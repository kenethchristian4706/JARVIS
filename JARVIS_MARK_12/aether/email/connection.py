import logging
from fastapi import APIRouter, HTTPException, Query

from aether.email.email_manager import email_manager
from aether.email.models import ConnectRequest
from aether.email.exceptions import EmailError
from aether.email.smtp_client import validate_smtp
from aether.email.imap_client import validate_imap

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["Email"])

@router.post("/connect")
def connect_email(req: ConnectRequest, validate_only: bool = Query(False)):
    """Connect an email account, validate credentials, and store them securely."""
    try:
        if validate_only:
            logger.info("Validation-only connect requested.")
            validate_smtp(req.email, req.password)
            validate_imap(req.email, req.password)
            return {"success": True}
        else:
            email_manager.connect(req.email, req.password)
            return {"success": True}
    except EmailError as e:
        logger.warning(f"Email error in connect: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected exception in connect: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@router.post("/test")
def test_email(req: ConnectRequest):
    """Validate credentials without saving them."""
    try:
        logger.info("Test connection requested.")
        validate_smtp(req.email, req.password)
        validate_imap(req.email, req.password)
        return {"success": True}
    except EmailError as e:
        logger.warning(f"Email error in test: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected exception in test: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@router.get("/status")
def get_email_status():
    """Retrieve connection status of the email account."""
    return email_manager.status()

@router.post("/disconnect")
def disconnect_email():
    """Disconnect email account, clearing memory state and deleting stored credentials."""
    try:
        email_manager.disconnect()
        return {"success": True}
    except Exception as e:
        logger.exception(f"Unexpected exception in disconnect: {e}")
        raise HTTPException(status_code=500, detail=str(e))
