"""
tools/system_tools.py

Implements handlers for system control:
shutdown_pc, restart_pc, sleep_pc, lock_pc, set_volume, mute_volume, set_brightness.
"""

import os
import logging
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pyautogui
import pyperclip
import pygetwindow as gw

logger = logging.getLogger(__name__)

def _get_volume_interface() -> Optional[POINTER(IAudioEndpointVolume)]:
    """Retrieves the Windows audio volume interface."""
    try:
        comtypes.CoInitialize()
    except Exception:
        pass
    try:
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, "Activate"):
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        elif hasattr(devices, "EndpointVolume"):
            return devices.EndpointVolume
        return None
    except Exception as e:
        logger.error(f"Error accessing audio endpoint: {e}")
        return None

def shutdown_pc() -> str:
    """Powers down the computer immediately."""
    os.system("shutdown /s /t 1")
    return "Shutdown command triggered successfully."

def restart_pc() -> str:
    """Restarts the computer immediately."""
    os.system("shutdown /r /t 1")
    return "Restart command triggered successfully."

def sleep_pc() -> str:
    """Places the computer into sleep/suspend mode."""
    # Rundll32 power command
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "System put to sleep successfully."

def lock_pc() -> str:
    """Locks the Windows user session workstation."""
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "System session locked successfully."

def set_volume(level: int) -> str:
    """Sets the system master volume to a value in 0-100."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    # Scale from [0, 100] to float [0.0, 1.0]
    scalar = float(level) / 100.0
    vol.SetMasterVolumeLevelScalar(scalar, None)
    return f"Master volume set to {level}%."

def mute_volume() -> str:
    """Mutes the master system volume."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    vol.SetMute(1, None)
    return "Master system audio muted successfully."

def unmute_volume() -> str:
    """Unmutes the master system volume."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    vol.SetMute(0, None)
    return "Master system audio unmuted successfully."

def set_brightness(level: int) -> str:
    """Sets display screen brightness to a value in 0-100."""
    try:
        sbc.set_brightness(level)
        return f"Display brightness set to {level}%."
    except Exception as e:
        # Desktop external monitors might fail software adjustment
        raise OSError(f"Failed to adjust monitor brightness: {e}")

def take_screenshot(save_path: str | None = None) -> dict:
    """
    Capture the entire screen and save it as a PNG image.
    If save_path is not provided, saves to ~/Pictures/Aether/Screenshots/
    with an automatically generated filename.
    """
    try:
        logger.info("Starting take_screenshot tool execution.")
        if save_path:
            from aether.tools.file_tools import resolve_path
            p = resolve_path(save_path)
            # If no extension or is an existing directory or ends with slash, treat as directory
            if p.suffix == "" or p.is_dir() or save_path.endswith("/") or save_path.endswith("\\"):
                p.mkdir(parents=True, exist_ok=True)
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                final_path = p / filename
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                final_path = p
        else:
            default_dir = Path.home() / "Pictures" / "Aether" / "Screenshots"
            default_dir.mkdir(parents=True, exist_ok=True)
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            final_path = default_dir / filename

        # Take screenshot and save it
        screenshot = pyautogui.screenshot()
        screenshot.save(str(final_path))
        
        saved_path_str = final_path.as_posix()
        logger.info(f"Screenshot saved successfully at: {saved_path_str}")
        return {
            "success": True,
            "message": "Screenshot saved successfully.",
            "data": {
                "path": saved_path_str
            }
        }
    except Exception as e:
        logger.error(f"Error during screenshot capture: {e}")
        return {
            "success": False,
            "message": f"Failed to capture screenshot: {str(e)}"
        }

def open_notepad_and_write(text: str) -> dict:
    """
    Launch Windows Notepad, wait until active, and write the provided text preserving line breaks.
    """
    try:
        logger.info("Starting open_notepad_and_write tool execution.")
        # Launch Notepad
        subprocess.Popen(["notepad.exe"])
        
        # Wait for Notepad window to become active
        notepad_window = None
        for _ in range(10):  # Wait up to 5 seconds
            windows = gw.getWindowsWithTitle("Notepad")
            if windows:
                notepad_window = windows[0]
                break
            time.sleep(0.5)
            
        if not notepad_window:
            logger.error("Notepad window did not open within the timeout.")
            return {
                "success": False,
                "message": "Notepad failed to open in a timely manner."
            }
            
        # Activate the window using Win32 API SetForegroundWindow and ThreadInput attachment
        try:
            hwnd = notepad_window._hWnd
            import win32gui
            import win32con
            import win32process
            
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            
            fore_hwnd = win32gui.GetForegroundWindow()
            if fore_hwnd != hwnd:
                fore_thread = win32process.GetWindowThreadProcessId(fore_hwnd)[0]
                target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
                if fore_thread != target_thread:
                    try:
                        win32process.AttachThreadInput(fore_thread, target_thread, True)
                        win32gui.SetForegroundWindow(hwnd)
                        win32process.AttachThreadInput(fore_thread, target_thread, False)
                    except Exception:
                        pass
                else:
                    win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
            time.sleep(0.5)  # Let activation complete
        except Exception as e:
            logger.warning(f"Failed to activate Notepad window using Win32 helper: {e}")
            # Fallback to pygetwindow activate
            try:
                notepad_window.activate()
                time.sleep(0.5)
            except Exception as e2:
                logger.warning(f"Fallback activation also failed: {e2}")
            
        # Write the text using pyautogui
        pyautogui.write(text)
        logger.info("Successfully wrote text to Notepad.")
        return {
            "success": True,
            "message": "Notepad opened and text inserted."
        }
    except Exception as e:
        logger.error(f"Error during notepad write operation: {e}")
        return {
            "success": False,
            "message": f"Failed to open Notepad and write text: {str(e)}"
        }

def clear_clipboard() -> dict:
    """
    Clear the Windows clipboard and verify it was cleared successfully.
    """
    try:
        logger.info("Starting clear_clipboard tool execution.")
        pyperclip.copy("")
        # Verify it was cleared
        clipboard_content = pyperclip.paste()
        if clipboard_content == "":
            logger.info("Clipboard cleared successfully.")
            return {
                "success": True,
                "message": "Clipboard cleared successfully."
            }
            
        logger.error(f"Clipboard verification failed. Found: {repr(clipboard_content)}")
        return {
            "success": False,
            "message": "Clipboard was not cleared successfully."
        }
    except Exception as e:
        logger.error(f"Error while clearing clipboard: {e}")
        return {
            "success": False,
            "message": f"Failed to clear clipboard: {str(e)}"
        }

def get_clipboard() -> dict:
    """
    Retrieve the current text content of the Windows clipboard.
    """
    try:
        logger.info("Starting get_clipboard tool execution.")
        content = pyperclip.paste()
        return {
            "success": True,
            "message": "Successfully retrieved clipboard content.",
            "data": {
                "content": content
            }
        }
    except Exception as e:
        logger.error(f"Error while retrieving clipboard content: {e}")
        return {
            "success": False,
            "message": f"Failed to retrieve clipboard content: {str(e)}"
        }

def set_clipboard(text: str) -> dict:
    """
    Copy specified text to the Windows clipboard.
    """
    try:
        logger.info(f"Starting set_clipboard tool execution for text: {text}")
        pyperclip.copy(text)
        # Verify it was copied
        clipboard_content = pyperclip.paste()
        if clipboard_content == text:
            logger.info("Text copied to clipboard successfully.")
            return {
                "success": True,
                "message": "Text copied to clipboard successfully."
            }
        else:
            logger.error("Clipboard verification failed.")
            return {
                "success": False,
                "message": "Failed to copy text to clipboard."
            }
    except Exception as e:
        logger.error(f"Error while copying text to clipboard: {e}")
        return {
            "success": False,
            "message": f"Failed to copy text to clipboard: {str(e)}"
        }

def increase_volume() -> str:
    """
    Increase the master playback volume by a default step of 10%.
    """
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current_scalar = vol.GetMasterVolumeLevelScalar()
    current_level = int(round(current_scalar * 100))
    new_level = min(100, current_level + 10)
    vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
    return f"Master volume set to {new_level}%."

def decrease_volume() -> str:
    """
    Decrease the master playback volume by a default step of 10%.
    """
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current_scalar = vol.GetMasterVolumeLevelScalar()
    current_level = int(round(current_scalar * 100))
    new_level = max(0, current_level - 10)
    vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
    return f"Master volume set to {new_level}%."

def increase_brightness() -> str:
    """
    Increase the display screen brightness by a default step of 10%.
    """
    try:
        brightness_list = sbc.get_brightness()
        if isinstance(brightness_list, list) and len(brightness_list) > 0:
            current = brightness_list[0]
        elif isinstance(brightness_list, int):
            current = brightness_list
        else:
            current = 50
        
        new_level = min(100, current + 10)
        sbc.set_brightness(new_level)
        return f"Display brightness set to {new_level}%."
    except Exception as e:
        raise OSError(f"Failed to adjust monitor brightness: {e}")

def decrease_brightness() -> str:
    """
    Decrease the display screen brightness by a default step of 10%.
    """
    try:
        brightness_list = sbc.get_brightness()
        if isinstance(brightness_list, list) and len(brightness_list) > 0:
            current = brightness_list[0]
        elif isinstance(brightness_list, int):
            current = brightness_list
        else:
            current = 50
        
        new_level = max(0, current - 10)
        sbc.set_brightness(new_level)
        return f"Display brightness set to {new_level}%."
    except Exception as e:
        raise OSError(f"Failed to adjust monitor brightness: {e}")
