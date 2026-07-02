"""
platform/windows/system_tools.py

Windows implementation of SystemAPI.
Controls audio master levels (pycaw), display brightness (screen_brightness_control),
Notepad window activation and writing automation.
"""

import os
import time
import logging
import subprocess
from typing import Optional
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pyautogui
import pygetwindow as gw

from aether.platforms.common.interfaces import SystemAPI

logger = logging.getLogger(__name__)

class WindowsSystemAPI(SystemAPI):
    def _get_volume_interface(self) -> Optional[POINTER(IAudioEndpointVolume)]:
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
            logger.error(f"Error accessing Windows audio endpoint: {e}")
            return None

    def set_volume(self, level: int) -> str:
        vol = self._get_volume_interface()
        if not vol:
            raise OSError("Audio control device is unavailable.")
        scalar = float(level) / 100.0
        vol.SetMasterVolumeLevelScalar(scalar, None)
        return f"Master volume set to {level}%."

    def mute_volume(self) -> str:
        vol = self._get_volume_interface()
        if not vol:
            raise OSError("Audio control device is unavailable.")
        vol.SetMute(1, None)
        return "Master system audio muted successfully."

    def unmute_volume(self) -> str:
        vol = self._get_volume_interface()
        if not vol:
            raise OSError("Audio control device is unavailable.")
        vol.SetMute(0, None)
        return "Master system audio unmuted successfully."

    def increase_volume(self) -> str:
        vol = self._get_volume_interface()
        if not vol:
            raise OSError("Audio control device is unavailable.")
        current_scalar = vol.GetMasterVolumeLevelScalar()
        current_level = int(round(current_scalar * 100))
        new_level = min(100, current_level + 10)
        vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
        return f"Master volume set to {new_level}%."

    def decrease_volume(self) -> str:
        vol = self._get_volume_interface()
        if not vol:
            raise OSError("Audio control device is unavailable.")
        current_scalar = vol.GetMasterVolumeLevelScalar()
        current_level = int(round(current_scalar * 100))
        new_level = max(0, current_level - 10)
        vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
        return f"Master volume set to {new_level}%."

    def set_brightness(self, level: int) -> str:
        try:
            sbc.set_brightness(level)
            return f"Display brightness set to {level}%."
        except Exception as e:
            raise OSError(f"Failed to adjust monitor brightness: {e}")

    def increase_brightness(self) -> str:
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

    def decrease_brightness(self) -> str:
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

    def open_notepad_and_write(self, text: str) -> dict:
        try:
            logger.info("Starting open_notepad_and_write tool execution on Windows.")
            subprocess.Popen(["notepad.exe"])
            
            notepad_window = None
            for _ in range(10):
                windows = gw.getWindowsWithTitle("Notepad")
                if windows:
                    notepad_window = windows[0]
                    break
                time.sleep(0.5)
                
            if not notepad_window:
                return {
                    "success": False,
                    "message": "Notepad failed to open in a timely manner."
                }
                
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
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Failed to activate Notepad window using Win32 helper: {e}")
                try:
                    notepad_window.activate()
                    time.sleep(0.5)
                except Exception as e2:
                    logger.warning(f"Fallback activation also failed: {e2}")
                
            pyautogui.write(text)
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
