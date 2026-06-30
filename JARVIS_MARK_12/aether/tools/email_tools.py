import logging
from typing import Dict, Any, List, Optional

from aether.email.email_manager import email_manager
from aether.email.exceptions import EmailError

logger = logging.getLogger(__name__)

def check_connection() -> Optional[Dict[str, Any]]:
    """Verify if an email account is currently connected in EmailManager.
    
    If not, returns the standardized Aether response indicating that login/connection
    is required to be handled in the frontend application Settings.
    """
    if not email_manager.is_connected():
        logger.info("Email tool invoked but account is not connected.")
        return {
            "success": False,
            "error": "EMAIL_NOT_CONNECTED",
            "requires_login": True,
            "message": "No email account is connected. Please connect your email account in Settings."
        }
    return None

def send_email(
    recipient: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    confirmed: bool = False
) -> Dict[str, Any]:
    """
    Send an email using SMTP.
    
    Args:
        recipient (str): Recipient email address.
        subject (str): Subject line of the email.
        body (str): Body content of the email.
        cc (str, optional): Carbon copy email address(es).
        bcc (str, optional): Blind carbon copy email address(es).
        attachments (list, optional): List of local file paths to attach.
        confirmed (bool): Confirmation flag from the user.
    """
    conn_check = check_connection()
    if conn_check:
        return conn_check

    # Confirmation requirement
    if not confirmed:
        logger.info("Email sending requires safety confirmation. Returning preview data.")
        return {
            "success": False,
            "requires_confirmation": True,
            "message": "You're about to send an email.",
            "data": {
                "recipient": recipient,
                "cc": cc,
                "bcc": bcc,
                "subject": subject,
                "body": body,
                "attachments": attachments
            }
        }

    try:
        email_manager.send_email(
            recipients=recipient,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            attachments=attachments
        )
        return {
            "success": True,
            "message": f"Email sent successfully to {recipient}."
        }
    except EmailError as e:
        return {
            "success": False,
            "message": f"Failed to send email: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while sending email: {e}"
        }

def list_emails(limit: int = 10, unread_only: bool = False) -> Dict[str, Any]:
    """
    List summaries of recent emails from the inbox.
    
    Args:
        limit (int, optional): Maximum number of emails to list. Defaults to 10.
        unread_only (bool, optional): If True, filters to unread emails only.
    """
    conn_check = check_connection()
    if conn_check:
        return conn_check

    try:
        emails = email_manager.list_emails(limit=limit, unread_only=unread_only)
        email_dicts = []
        for e in emails:
            email_dicts.append({
                "id": e.id,
                "sender": e.sender,
                "subject": e.subject,
                "date": e.date,
                "unread": e.unread,
                "has_attachments": e.has_attachments
            })
        
        if not email_dicts:
            msg = "No unread emails found." if unread_only else "No emails found in inbox."
        else:
            filter_text = "unread " if unread_only else ""
            lines = [f"### Recent {filter_text.capitalize()}Emails ({len(email_dicts)})"]
            for e in email_dicts:
                unread_badge = " **[UNREAD]**" if e["unread"] else ""
                attachment_badge = " 📎" if e["has_attachments"] else ""
                lines.append(f"- **[ID: {e['id']}]** From: {e['sender']} | Subject: **{e['subject']}** | {e['date']}{unread_badge}{attachment_badge}")
            msg = "\n".join(lines)

        return {
            "success": True,
            "message": msg,
            "data": {
                "emails": email_dicts
            }
        }
    except EmailError as e:
        return {
            "success": False,
            "message": f"Failed to list emails: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while listing emails: {e}"
        }

def read_email(email_id: str) -> Dict[str, Any]:
    """
    Read the content details of a selected email.
    
    Args:
        email_id (str): Email unique identifier, inbox sequence number, or 'latest'.
    """
    conn_check = check_connection()
    if conn_check:
        return conn_check

    try:
        details = email_manager.read_email(email_id)
        recipients_str = ", ".join(details.recipients) if details.recipients else "None"
        attachments_str = ", ".join(details.attachments) if details.attachments else "None"
        body_content = details.body.strip() if details.body else "*(Empty Body)*"
        
        lines = [
            f"### Email Details (ID: {details.id})",
            f"- **From:** {details.sender}",
            f"- **To:** {recipients_str}",
            f"- **Subject:** **{details.subject}**",
            f"- **Date:** {details.date}",
            f"- **Attachments:** {attachments_str}",
            "",
            "### Body",
            body_content
        ]
        msg = "\n".join(lines)

        return {
            "success": True,
            "message": msg,
            "data": {
                "id": details.id,
                "sender": details.sender,
                "recipients": details.recipients,
                "subject": details.subject,
                "date": details.date,
                "body": details.body,
                "attachments": details.attachments
            }
        }
    except EmailError as e:
        return {
            "success": False,
            "message": f"Failed to read email {email_id}: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while reading email: {e}"
        }
