class EmailError(Exception):
    """Base exception for email module errors."""
    pass

class EmailAuthenticationError(EmailError):
    """Raised when authentication fails with SMTP or IMAP servers."""
    pass

class EmailConnectionError(EmailError):
    """Raised when connection to SMTP or IMAP servers fails."""
    pass

class EmailNotConnectedError(EmailError):
    """Raised when trying to use email tools without a connected account."""
    pass

class EmailSendError(EmailError):
    """Raised when sending an email fails."""
    pass
