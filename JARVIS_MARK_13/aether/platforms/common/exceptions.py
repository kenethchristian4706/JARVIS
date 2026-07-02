"""
platform/common/exceptions.py

Defines common platform exceptions for the Aether assistant.
These abstract away raw OS/system-level errors into Aether-defined exceptions.
"""

class AetherPlatformError(Exception):
    """Base exception for all Aether platform-level issues."""
    pass

class PermissionDeniedError(AetherPlatformError):
    """Raised when the platform layer detects that required OS permissions are missing."""
    pass

class AppNotFoundError(AetherPlatformError):
    """Raised when an application is not installed or cannot be found on the system."""
    pass

class ProcessError(AetherPlatformError):
    """Raised when a process operation (kill, launch) fails."""
    pass

class DeviceError(AetherPlatformError):
    """Raised when a hardware device (audio speakers, monitor brightness control) is unavailable."""
    pass
