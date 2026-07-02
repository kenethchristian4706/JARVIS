"""
platform/common/platform_factory.py

Dynamically loads the appropriate platform implementation depending on the host OS.
"""

import sys
import logging
import platform as sys_platform

logger = logging.getLogger(__name__)

class Platform:
    """Convenient container holding references to all APIs for the current platform."""
    def __init__(self, app, browser, file, window, clipboard, screenshot, notification, power, system, permissions, path):
        self.app = app
        self.browser = browser
        self.file = file
        self.window = window
        self.clipboard = clipboard
        self.screenshot = screenshot
        self.notification = notification
        self.power = power
        self.system = system
        self.permissions = permissions
        self.path = path


_cached_platform_instance = None

def get_platform_instance() -> Platform:
    """Returns the singleton instance of the current Platform container."""
    global _cached_platform_instance
    if _cached_platform_instance is not None:
        return _cached_platform_instance

    system_name = sys_platform.system()
    logger.info(f"Detecting system platform: {system_name}")

    if system_name == "Windows":
        from aether.platforms.windows import WindowsPlatform
        _cached_platform_instance = WindowsPlatform()
    elif system_name in ("Darwin", "Mac"):
        from aether.platforms.mac import MacPlatform
        _cached_platform_instance = MacPlatform()
    else:
        # Fallback to Windows or a mock platform for testing/fallback
        logger.warning(f"Unsupported platform {system_name}. Falling back to Windows implementation for compatibility.")
        from aether.platforms.windows import WindowsPlatform
        _cached_platform_instance = WindowsPlatform()

    return _cached_platform_instance
