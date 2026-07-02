"""
tests/common/test_platform.py

Verifies that the platform abstraction layer loaded by the factory
correctly implements all defined abstract base class interfaces.
"""

from aether.platforms import platform
from aether.platforms.common.interfaces import (
    ApplicationAPI, BrowserAPI, FileAPI, WindowAPI,
    ClipboardAPI, ScreenshotAPI, NotificationAPI, PowerAPI, SystemAPI
)

def test_platform_implements_interfaces():
    """Asserts that all components of the platform singleton inherit from their interface ABCs."""
    assert isinstance(platform.app, ApplicationAPI)
    assert isinstance(platform.browser, BrowserAPI)
    assert isinstance(platform.file, FileAPI)
    assert isinstance(platform.window, WindowAPI)
    assert isinstance(platform.clipboard, ClipboardAPI)
    assert isinstance(platform.screenshot, ScreenshotAPI)
    assert isinstance(platform.notification, NotificationAPI)
    assert isinstance(platform.power, PowerAPI)
    assert isinstance(platform.system, SystemAPI)

def test_platform_methods_exist():
    """Validates that key API methods are callable on the platform instance components."""
    assert hasattr(platform.app, "open_app")
    assert hasattr(platform.app, "close_app")
    assert hasattr(platform.file, "create_file")
    assert hasattr(platform.system, "set_volume")
    assert hasattr(platform.power, "sleep_pc")
