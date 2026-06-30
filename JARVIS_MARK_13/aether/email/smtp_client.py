import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Union, Tuple

from aether.email.exceptions import EmailAuthenticationError, EmailConnectionError, EmailSendError

logger = logging.getLogger(__name__)

def resolve_smtp_config(email: str) -> Tuple[str, int]:
    """Auto-detect SMTP host and port based on email domain."""
    domain = email.split("@")[-1].lower().strip()
    if domain in ("gmail.com", "googlemail.com"):
        return "smtp.gmail.com", 465
    elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com", "office365.com"):
        return "smtp.office365.com", 587
    elif domain in ("yahoo.com", "ymail.com"):
        return "smtp.mail.yahoo.com", 465
    elif domain in ("icloud.com", "me.com", "mac.com"):
        return "smtp.mail.me.com", 587
    else:
        return f"smtp.{domain}", 587

def validate_smtp(email: str, password: str) -> bool:
    """Validate credentials against the SMTP server without saving them."""
    host, port = resolve_smtp_config(email)
    logger.info(f"Validating SMTP connection to {host}:{port} for {email}")
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        with server:
            server.login(email, password)
        logger.info("SMTP validation succeeded.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Auth failed: {e}")
        error_msg = e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else e.smtp_error
        raise EmailAuthenticationError(f"SMTP authentication failed: {error_msg}")
    except Exception as e:
        logger.error(f"SMTP Connection failed: {e}")
        raise EmailConnectionError(f"Failed to connect or log in to SMTP server {host}:{port}: {e}")

def send_smtp_email(
    email: str,
    password: str,
    recipients: Union[List[str], str],
    subject: str,
    body: str,
    cc: Union[List[str], str, None] = None,
    bcc: Union[List[str], str, None] = None,
    attachments: List[str] = None
) -> None:
    """Format and send an email via SMTP."""
    # Resolve lists
    if isinstance(recipients, str):
        to_list = [r.strip() for r in recipients.split(",") if r.strip()]
    else:
        to_list = recipients

    cc_list = []
    if cc:
        if isinstance(cc, str):
            cc_list = [r.strip() for r in cc.split(",") if r.strip()]
        else:
            cc_list = cc

    bcc_list = []
    if bcc:
        if isinstance(bcc, str):
            bcc_list = [r.strip() for r in bcc.split(",") if r.strip()]
        else:
            bcc_list = bcc

    if not to_list:
        raise EmailSendError("No recipients provided.")

    host, port = resolve_smtp_config(email)
    
    # Construct email message
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = ", ".join(to_list)
    if cc_list:
        msg['Cc'] = ", ".join(cc_list)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Attach files
    if attachments:
        for filepath in attachments:
            if not os.path.exists(filepath):
                raise EmailSendError(f"Attachment file not found: {filepath}")
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)
            except Exception as e:
                raise EmailSendError(f"Failed to attach file '{filename}': {e}")
                
    # Send
    all_recipients = to_list + cc_list + bcc_list
    logger.info(f"Sending SMTP email to {len(all_recipients)} addresses via {host}:{port}")
    
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        with server:
            server.login(email, password)
            server.sendmail(email, all_recipients, msg.as_string())
        logger.info("SMTP email sent successfully.")
    except smtplib.SMTPResponseException as e:
        logger.error(f"SMTP response error during send: {e}")
        error_msg = e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else e.smtp_error
        raise EmailSendError(f"SMTP error: {error_msg}")
    except Exception as e:
        logger.error(f"SMTP exception during send: {e}")
        raise EmailSendError(f"Failed to send email: {e}")
