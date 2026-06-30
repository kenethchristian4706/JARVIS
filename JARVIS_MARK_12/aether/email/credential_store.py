import keyring
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

SERVICE_NAME_EMAIL = "aether_email"
SERVICE_NAME_PASS = "aether_email_password"
USERNAME_EMAIL = "active_email"

def save_credentials(email: str, password: str) -> None:
    """Save email and app password in secure keyring."""
    try:
        logger.info(f"Saving credentials for email: {email}")
        keyring.set_password(SERVICE_NAME_EMAIL, USERNAME_EMAIL, email)
        keyring.set_password(SERVICE_NAME_PASS, email, password)
    except Exception as e:
        logger.error(f"Failed to save credentials in keyring: {e}")
        raise RuntimeError(f"Credential storage error: {e}")

def get_credentials() -> Tuple[str | None, str | None]:
    """Retrieve email and app password from secure keyring."""
    try:
        email = keyring.get_password(SERVICE_NAME_EMAIL, USERNAME_EMAIL)
        if not email:
            return None, None
        password = keyring.get_password(SERVICE_NAME_PASS, email)
        return email, password
    except Exception as e:
        logger.error(f"Failed to load credentials from keyring: {e}")
        return None, None

def delete_credentials() -> None:
    """Remove email credentials from keyring."""
    try:
        email = keyring.get_password(SERVICE_NAME_EMAIL, USERNAME_EMAIL)
        if email:
            try:
                keyring.delete_password(SERVICE_NAME_PASS, email)
            except keyring.errors.PasswordDeleteError:
                pass
        try:
            keyring.delete_password(SERVICE_NAME_EMAIL, USERNAME_EMAIL)
        except keyring.errors.PasswordDeleteError:
            pass
        logger.info("Credentials successfully deleted from keyring.")
    except Exception as e:
        logger.error(f"Error deleting credentials from keyring: {e}")
