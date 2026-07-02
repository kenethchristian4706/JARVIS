"""
tools/app_tools.py

Implements handlers for application management delegating to the platform abstraction layer.
"""

from aether.platforms import platform

def open_app(app_name: str) -> str:
    """Launches an application by name."""
    return platform.app.open_app(app_name)

def close_app(app_name: str) -> str:
    """Closes all active process instances of a given application by name."""
    return platform.app.close_app(app_name)

def switch_to_app(app_name: str) -> str:
    """Brings the application window to foreground focus."""
    return platform.app.switch_to_app(app_name)

def list_running_apps() -> list[str]:
    """Lists unique names of currently running application processes."""
    return platform.app.list_running_apps()

def list_installed_apps() -> list[str]:
    """Lists names of all scanned/installed applications on the system."""
    return platform.app.list_installed_apps()
