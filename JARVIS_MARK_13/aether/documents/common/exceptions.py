"""
documents/common/exceptions.py

Custom exceptions for Word and Excel document manipulation.
"""

class DocumentError(Exception):
    """Base class for all document-related exceptions."""
    pass

class DocumentCorruptedError(DocumentError):
    """Raised when a document format or structure is corrupted."""
    pass

class SheetNotFoundError(DocumentError):
    """Raised when a requested Excel worksheet is not found."""
    pass

class InvalidCellFormatError(DocumentError):
    """Raised when a cell range or coordinate format is invalid."""
    pass
