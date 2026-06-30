"""
tools/email_tools.py

Implements email operations (sending, listing, reading) for the Aether assistant
using the central EmailManager (Email Connection Configuration).
"""

import logging
from typing import List, Dict, Any, Optional

from aether.email.email_manager import email_manager

logger = logging.getLogger(__name__)

def send_email(
    recipient: str,
    subject: str,
    body: str,
    confirmed: bool = False
) -> dict:
    """
    Send an email using the connected EmailManager account.
    """
    logger.info(f"send_email tool triggered. Recipient: {recipient}, Subject: {subject}, Confirmed: {confirmed}")
    
    if not email_manager.is_connected():
        logger.warning("Attempted to send email but email account is not connected.")
        return {
            "success": False,
            "message": "Email account is not connected. Please connect it in settings. [EMAIL_NOT_CONNECTED]"
        }
        
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

    try:
        email_manager.send_email(
            recipients=[recipient],
            subject=subject,
            body=body
        )
        return {
            "success": True,
            "message": f"Email sent successfully to {recipient}"
        }
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")
        return {
            "success": False,
            "message": f"Failed to send email: {e}"
        }

def list_emails(limit: int = 10, unread_only: bool = False) -> dict:
    """
    Retrieve summaries of recent emails from the inbox.
    """
    logger.info(f"list_emails tool triggered. Limit: {limit}, Unread only: {unread_only}")
    
    if not email_manager.is_connected():
        return {
            "success": False,
            "message": "Email account is not connected. Please connect it in settings. [EMAIL_NOT_CONNECTED]"
        }
        
    try:
        emails = email_manager.list_emails(limit=limit, unread_only=unread_only)
        emails_list = []
        for e in emails:
            emails_list.append({
                "id": e.id,
                "sender": e.sender,
                "subject": e.subject,
                "date": e.date,
                "unread": e.unread,
                "has_attachments": e.has_attachments
            })
        return {
            "success": True,
            "message": f"Successfully retrieved {len(emails_list)} emails.",
            "data": {
                "emails": emails_list
            }
        }
    except Exception as e:
        logger.exception(f"Failed to list emails: {e}")
        return {
            "success": False,
            "message": f"Failed to list emails: {e}"
        }

def read_email(
    email_id: str = "latest", 
    sender: Optional[str] = None, 
    date: Optional[str] = None
) -> dict:
    """
    Retrieve full details of a specific email by its ID/UID, or by searching sender/date/query.
    """
    logger.info(f"read_email tool triggered. Email ID: {email_id}, Sender: {sender}, Date: {date}")
    
    if not email_manager.is_connected():
        return {
            "success": False,
            "message": "Email account is not connected. Please connect it in settings. [EMAIL_NOT_CONNECTED]"
        }
        
    try:
        details = email_manager.read_email(email_id=email_id, sender=sender, date=date)
        return {
            "success": True,
            "message": f"Successfully retrieved email details for ID: {details.id}",
            "data": {
                "email": {
                    "id": details.id,
                    "sender": details.sender,
                    "recipients": details.recipients,
                    "subject": details.subject,
                    "date": details.date,
                    "body": details.body,
                    "attachments": details.attachments
                }
            }
        }
    except Exception as e:
        logger.exception(f"Failed to read email {email_id} (sender={sender}, date={date}): {e}")
        return {
            "success": False,
            "message": f"Failed to read email details: {e}"
        }
