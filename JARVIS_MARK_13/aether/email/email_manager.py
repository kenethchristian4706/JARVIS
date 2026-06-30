import logging
from typing import Dict, Any, List, Optional

from aether.email.exceptions import EmailNotConnectedError, EmailConnectionError
from aether.email.credential_store import save_credentials, get_credentials, delete_credentials
from aether.email.smtp_client import validate_smtp, send_smtp_email
from aether.email.imap_client import validate_imap, get_imap_client, list_imap_emails, read_imap_email
from aether.email.models import EmailSummary, EmailDetails

logger = logging.getLogger(__name__)

class EmailManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmailManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._email = None
        self._password = None
        self._initialized = True

    def connect(self, email: str, password: str) -> None:
        """Validate SMTP and IMAP, then save credentials in secure keyring."""
        logger.info(f"Initiating connection validation for {email}")
        
        # 1. Validate both SMTP and IMAP
        validate_smtp(email, password)
        validate_imap(email, password)
        
        # 2. Save credentials securely
        save_credentials(email, password)
        
        # 3. Store in memory
        self._email = email
        self._password = password
        logger.info(f"Successfully connected to email: {email}")

    def disconnect(self) -> None:
        """Clear memory and remove credentials from keyring."""
        logger.info("Disconnecting email account...")
        delete_credentials()
        self._email = None
        self._password = None
        logger.info("Email account disconnected.")

    def reconnect(self) -> bool:
        """Load credentials from keyring and verify connection status on startup."""
        logger.info("Attempting automatic email reconnection...")
        email, password = get_credentials()
        if not email or not password:
            logger.info("No saved credentials found in keyring. Remaining disconnected.")
            return False
        
        try:
            validate_smtp(email, password)
            validate_imap(email, password)
            self._email = email
            self._password = password
            logger.info(f"Automatically reconnected to email account: {email}")
            return True
        except Exception as e:
            logger.warning(f"Automatic reconnection failed (credentials might be invalid or network offline): {e}")
            # Keep credentials in keyring so they can reconnect when network returns, but do not log in memory
            return False

    def is_connected(self) -> bool:
        """Check if an email account is currently connected in memory."""
        return self._email is not None and self._password is not None

    def get_email_address(self) -> str | None:
        """Get the connected email address."""
        return self._email

    def send_email(
        self,
        recipients: List[str] | str,
        subject: str,
        body: str,
        cc: List[str] | str | None = None,
        bcc: List[str] | str | None = None,
        attachments: List[str] = None
    ) -> None:
        """Send an email using SMTP."""
        if not self.is_connected():
            raise EmailNotConnectedError("Email account is not connected.")
        send_smtp_email(
            email=self._email,
            password=self._password,
            recipients=recipients,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            attachments=attachments
        )

    def list_emails(self, limit: int = 10, unread_only: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[EmailSummary]:
        """Fetch summaries of recent emails from IMAP."""
        if not self.is_connected():
            raise EmailNotConnectedError("Email account is not connected.")
        
        try:
            mail = get_imap_client(self._email, self._password)
            with mail:
                return list_imap_emails(mail, limit, unread_only, filters)
        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            raise EmailConnectionError(f"Failed to retrieve emails from server: {e}")

    def read_email(
        self, 
        email_id: str = "latest", 
        sender: Optional[str] = None, 
        date: Optional[str] = None
    ) -> EmailDetails:
        """Fetch details of a specific email from IMAP."""
        if not self.is_connected():
            raise EmailNotConnectedError("Email account is not connected.")
        
        try:
            mail = get_imap_client(self._email, self._password)
            with mail:
                return read_imap_email(mail, email_id, sender, date)
        except Exception as e:
            logger.error(f"Error reading email {email_id}: {e}")
            raise EmailConnectionError(f"Failed to read email details: {e}")

    def status(self) -> Dict[str, Any]:
        """Return the current connection status dictionary."""
        if self.is_connected():
            return {
                "connected": True,
                "email": self._email
            }
        return {
            "connected": False
        }

# Global singleton instance
email_manager = EmailManager()
