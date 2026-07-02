"""
platform/windows/__init__.py

Windows-specific platform initialization.
Instantiates the implementation classes for each of Aether's APIs.
"""

from aether.platforms.common.platform_factory import Platform
from aether.platforms.common.paths import PlatformPaths
from aether.platforms.common.permissions import BasePermissionManager
from aether.platforms.windows.app_tools import WindowsApplicationAPI
from aether.platforms.windows.browser_tools import WindowsBrowserAPI
from aether.platforms.windows.file_tools import WindowsFileAPI
from aether.platforms.windows.window_manager import WindowsWindowAPI
from aether.platforms.windows.clipboard_tools import WindowsClipboardAPI
from aether.platforms.windows.screenshot_tools import WindowsScreenshotAPI
from aether.platforms.windows.notification_tools import WindowsNotificationAPI
from aether.platforms.windows.power_tools import WindowsPowerAPI
from aether.platforms.windows.system_tools import WindowsSystemAPI

class WindowsPlatform(Platform):
    def __init__(self):
        super().__init__(
            app=WindowsApplicationAPI(),
            browser=WindowsBrowserAPI(),
            file=WindowsFileAPI(),
            window=WindowsWindowAPI(),
            clipboard=WindowsClipboardAPI(),
            screenshot=WindowsScreenshotAPI(),
            notification=WindowsNotificationAPI(),
            power=WindowsPowerAPI(),
            system=WindowsSystemAPI(),
            permissions=BasePermissionManager(), # dummy check on Windows
            path=PlatformPaths
        )
