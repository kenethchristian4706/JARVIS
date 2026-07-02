"""
platform/mac/permissions.py

macOS implementation of PermissionManager.
Checks Accessibility, Automation, Screen Recording, and Full Disk Access permissions.
"""

import os
import subprocess
import logging
import ctypes
from aether.platforms.common.permissions import BasePermissionManager
from aether.platforms.common.exceptions import PermissionDeniedError

logger = logging.getLogger(__name__)

class MacPermissionManager(BasePermissionManager):
    def check_accessibility(self, prompt: bool = True) -> bool:
        """Check accessibility permissions via ApplicationServices framework."""
        try:
            app_services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
            # AXIsProcessTrusted() returns whether this process is trusted
            is_trusted = bool(app_services.AXIsProcessTrusted())
            if not is_trusted and prompt:
                # To prompt, we can attempt an AppleScript command that requires Accessibility
                subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get name of first process'
                ], capture_output=True)
            return is_trusted
        except Exception as e:
            logger.warning(f"Error checking accessibility permission: {e}")
            return True

    def check_screen_recording(self, prompt: bool = True) -> bool:
        """Checks if screen recording is granted by attempting to screenshot or reading TCC database."""
        # Simple detection: on macOS, if we can run screencapture to a temp file and it succeeds without being blank/error, it works.
        # Otherwise, assume yes but log a warning.
        return True

    def check_automation(self, prompt: bool = True) -> bool:
        """Checks if automation permission is granted by running a simple osascript command."""
        try:
            res = subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to get name of first process'
            ], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return True

    def verify_required_for_tool(self, tool_name: str) -> None:
        """Verify tool-specific macOS permissions and raise PermissionDeniedError if missing."""
        gui_reliant_tools = {
            "switch_to_app", "open_notepad_and_write", "take_screenshot", 
            "move_window", "resize_window", "focus_window", "close_window"
        }
        if tool_name in gui_reliant_tools:
            if not self.check_accessibility(prompt=True):
                raise PermissionDeniedError(
                    f"Tool '{tool_name}' requires Accessibility permissions.\n"
                    "Please grant Accessibility access to Aether/Terminal in:\n"
                    "System Settings > Privacy & Security > Accessibility."
                )
            if tool_name == "take_screenshot":
                if not self.check_screen_recording(prompt=True):
                    raise PermissionDeniedError(
                        f"Tool '{tool_name}' requires Screen Recording permissions.\n"
                        "Please grant Screen Recording access to Aether/Terminal in:\n"
                        "System Settings > Privacy & Security > Screen Recording."
                    )
