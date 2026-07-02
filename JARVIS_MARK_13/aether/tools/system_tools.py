"""
tools/system_tools.py

Implements handlers for system control delegating to the platform abstraction layer.
"""

from typing import Optional
from aether.platforms import platform

def shutdown_pc() -> str:
    """Powers down the computer immediately."""
    return platform.power.shutdown_pc()

def restart_pc() -> str:
    """Restarts the computer immediately."""
    return platform.power.restart_pc()

def sleep_pc() -> str:
    """Places the computer into sleep/suspend mode."""
    return platform.power.sleep_pc()

def lock_pc() -> str:
    """Locks the user session workstation."""
    return platform.power.lock_pc()

def set_volume(level: int) -> str:
    """Sets the system master volume to a value in 0-100."""
    return platform.system.set_volume(level)

def mute_volume() -> str:
    """Mutes the master system volume."""
    return platform.system.mute_volume()

def unmute_volume() -> str:
    """Unmutes the master system volume."""
    return platform.system.unmute_volume()

def increase_volume() -> str:
    """Increase the master playback volume by a default step of 10%."""
    return platform.system.increase_volume()

def decrease_volume() -> str:
    """Decrease the master playback volume by a default step of 10%."""
    return platform.system.decrease_volume()

def set_brightness(level: int) -> str:
    """Sets display screen brightness to a value in 0-100."""
    return platform.system.set_brightness(level)

def increase_brightness() -> str:
    """Increase the display screen brightness by a default step of 10%."""
    return platform.system.increase_brightness()

def decrease_brightness() -> str:
    """Decrease the display screen brightness by a default step of 10%."""
    return platform.system.decrease_brightness()

def take_screenshot(save_path: Optional[str] = None) -> dict:
    """Capture the entire screen and save it as a PNG image."""
    return platform.screenshot.take_screenshot(save_path)

def open_notepad_and_write(text: str) -> dict:
    """Launch Notepad/TextEdit, wait until active, and write the provided text."""
    return platform.system.open_notepad_and_write(text)

def clear_clipboard() -> dict:
    """Clear the clipboard."""
    return platform.clipboard.clear_clipboard()

def get_clipboard() -> dict:
    """Retrieve the current text content of the clipboard."""
    return platform.clipboard.get_clipboard()

def set_clipboard(text: str) -> dict:
    """Copy specified text to the clipboard."""
    return platform.clipboard.set_clipboard(text)
