"""
platform/mac/__init__.py

macOS-specific platform initialization.
Instantiates implementation classes for each of Aether's APIs.
"""

from aether.platforms.common.platform_factory import Platform
from aether.platforms.common.paths import PlatformPaths
from aether.platforms.mac.permissions import MacPermissionManager
from aether.platforms.mac.app_tools import MacApplicationAPI
from aether.platforms.mac.browser_tools import MacBrowserAPI
from aether.platforms.mac.file_tools import MacFileAPI
from aether.platforms.mac.window_manager import MacWindowAPI
from aether.platforms.mac.clipboard_tools import MacClipboardAPI
from aether.platforms.mac.screenshot_tools import MacScreenshotAPI
from aether.platforms.mac.notification_tools import MacNotificationAPI
from aether.platforms.mac.power_tools import MacPowerAPI
from aether.platforms.mac.system_tools import MacSystemAPI

class MacPlatform(Platform):
    def __init__(self):
        super().__init__(
            app=MacApplicationAPI(),
            browser=MacBrowserAPI(),
            file=MacFileAPI(),
            window=MacWindowAPI(),
            clipboard=MacClipboardAPI(),
            screenshot=MacScreenshotAPI(),
            notification=MacNotificationAPI(),
            power=MacPowerAPI(),
            system=MacSystemAPI(),
            permissions=MacPermissionManager(),
            path=PlatformPaths
        )
