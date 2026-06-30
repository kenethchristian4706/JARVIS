"""
tools/email_tools.py

Implements the send_email tool for the Aether assistant.
Allows sending emails using SMTP configurations defined in environment variables.
Supports a confirmation workflow before actually sending.
"""

import os
import smtplib
import ssl
import logging
import socket
from email.message import EmailMessage
from typing import Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback load_dotenv to handle environments where python-dotenv installation is unavailable.
    def load_dotenv(dotenv_path=None) -> None:
        """
        Fallback implementation of load_dotenv that parses a standard .env file
        and loads key-value pairs into os.environ.
        """
        from pathlib import Path
        if dotenv_path is None:
            # Look for .env in current directory and parent directories
            dotenv_path = Path(os.getcwd()) / ".env"
            if not dotenv_path.exists():
                dotenv_path = Path(__file__).resolve().parent.parent / ".env"
        else:
            dotenv_path = Path(dotenv_path)

        if dotenv_path.exists() and dotenv_path.is_file():
            try:
                with open(dotenv_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            os.environ[key] = val
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to read fallback .env: {e}")

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def send_email(
    recipient: str,
    subject: str,
    body: str,
    confirmed: bool = False
) -> dict:
    """
    Send an email using SMTP.
    
    To secure credentials, Gmail App Passwords (or equivalent application-specific
    passwords) should be configured in the .env file instead of normal email passwords.
    
    Args:
        recipient (str): Recipient email address.
        subject (str): Subject line of the email.
        body (str): Body content of the email.
        confirmed (bool): Confirmation flag. If False, returns the email summary for confirmation.
        
    Returns:
        dict: Standardized JSON-like response dict with 'success', 'message', and optional metadata.
    """
    logger.info(f"send_email tool triggered. Recipient: {recipient}, Subject: {subject}, Confirmed: {confirmed}")
    
    # 1. Read SMTP configuration from environment variables.
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port_str = os.getenv("SMTP_PORT")
    
    # 2. Validate email credentials/configurations exist.
    if not email_address or not email_password or not smtp_server or not smtp_port_str:
        logger.error("Email credentials or server configuration not fully set in environment variables.")
        return {
            "success": False,
            "message": "Invalid email credentials."
        }
        
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        logger.error(f"Invalid SMTP_PORT configured: {smtp_port_str}")
        return {
            "success": False,
            "message": "Unable to connect to email server."
        }

    # 3. Confirmation Requirement
    if not confirmed:
        logger.info("Email sending requires confirmation. Returning preview data.")
        return {
            "success": False,
            "requires_confirmation": True,
            "message": "You're about to send an email.",
            "data": {
                "recipient": recipient,
                "subject": subject,
                "body": body
            }
        }

    # 4. Create EmailMessage
    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    # 5. Connect and send email
    try:
        context = ssl.create_default_context()
        logger.info(f"Connecting to SMTP server {smtp_server}:{smtp_port} using TLS...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            
            logger.info("Authenticating with SMTP server...")
            server.login(email_address, email_password)
            
            logger.info("Sending the email...")
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {recipient}")
        return {
            "success": True,
            "message": f"Email sent successfully to {recipient}"
        }
        
    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(f"Authentication failure: {auth_err}")
        return {
            "success": False,
            "message": "Invalid email credentials."
        }
    except (smtplib.SMTPConnectError, TimeoutError, ConnectionError, socket.gaierror) as conn_err:
        logger.exception(f"Connection error occurred: {conn_err}")
        return {
            "success": False,
            "message": "Unable to connect to email server."
        }
    except Exception as e:
        logger.exception(f"Unexpected exception occurred while sending email: {e}")
        return {
            "success": False,
            "message": f"Failed to send email: {e}"
        }
