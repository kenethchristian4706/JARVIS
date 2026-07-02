"""
platform/windows/window_manager.py

Windows implementation of WindowAPI.
Manages window positioning, sizing, focusing, and listing using pygetwindow and win32gui.
"""

import logging
from typing import List
import pygetwindow as gw
import win32gui

from aether.platforms.common.interfaces import WindowAPI

logger = logging.getLogger(__name__)

class WindowsWindowAPI(WindowAPI):
    def move_window(self, title: str, x: int, y: int) -> str:
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return f"No window found matching title '{title}'."
            w = windows[0]
            w.moveTo(x, y)
            return f"Moved window '{w.title}' to ({x}, {y})."
        except Exception as e:
            logger.error(f"Error moving window: {e}")
            return f"Failed to move window '{title}': {e}"

    def resize_window(self, title: str, width: int, height: int) -> str:
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return f"No window found matching title '{title}'."
            w = windows[0]
            w.resizeTo(width, height)
            return f"Resized window '{w.title}' to {width}x{height}."
        except Exception as e:
            logger.error(f"Error resizing window: {e}")
            return f"Failed to resize window '{title}': {e}"

    def focus_window(self, title: str) -> str:
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return f"No window found matching title '{title}'."
            w = windows[0]
            w.activate()
            return f"Focused window '{w.title}'."
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return f"Failed to focus window '{title}': {e}"

    def close_window(self, title: str) -> str:
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return f"No window found matching title '{title}'."
            w = windows[0]
            w.close()
            return f"Closed window '{w.title}'."
        except Exception as e:
            logger.error(f"Error closing window: {e}")
            return f"Failed to close window '{title}': {e}"

    def list_windows(self) -> List[str]:
        try:
            windows = gw.getAllWindows()
            return [w.title for w in windows if w.title]
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return []

    def get_active_window(self) -> str:
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return title or ""
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return ""
