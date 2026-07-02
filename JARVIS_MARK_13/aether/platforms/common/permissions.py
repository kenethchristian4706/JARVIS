"""
platform/common/permissions.py

Interface and helper base class for OS-level permission management.
Ensures needed permissions are checked before executing GUI-reliant or disk-heavy tools.
"""

import logging
from aether.platforms.common.exceptions import PermissionDeniedError

logger = logging.getLogger(__name__)

class BasePermissionManager:
    def check_accessibility(self, prompt: bool = True) -> bool:
        """Check if Accessibility/TCC accessibility is granted."""
        return True

    def check_automation(self, prompt: bool = True) -> bool:
        """Check if Apple Events automation is granted."""
        return True

    def check_screen_recording(self, prompt: bool = True) -> bool:
        """Check if Screen Recording permission is granted."""
        return True

    def check_full_disk_access(self, prompt: bool = True) -> bool:
        """Check if Full Disk Access is granted."""
        return True

    def verify_required_for_tool(self, tool_name: str) -> None:
        """Verify tool-specific permissions, raising PermissionDeniedError on failure."""
        # By default (e.g. Windows), passes silently since OS doesn't block program actions.
        pass
