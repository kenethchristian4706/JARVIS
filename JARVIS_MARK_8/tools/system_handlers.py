"""
tools/system_handlers.py

Implements execution handlers for system controls:
volume adjustment (pycaw), brightness (screen_brightness_control),
taking screenshots (pyautogui), and system shutdown.
"""

import os
import time
from typing import Optional
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pyautogui

def _get_volume_control() -> Optional[POINTER(IAudioEndpointVolume)]:
    """
    Helper to fetch the master volume control interface.
    """
    try:
        comtypes.CoInitialize()
    except Exception:
        pass
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None

# --- Audio volume handlers ---

def set_volume(volume: int) -> dict:
    vol_ctrl = _get_volume_control()
    if not vol_ctrl:
        return {"status": "error", "message": "Failed to connect to system audio device control."}
    try:
        vol_ctrl.SetMasterVolumeLevelScalar(volume / 100.0, None)
        return {"status": "success", "message": f"System volume adjusted to {volume}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set volume: {e}"}

def increase_volume() -> dict:
    vol_ctrl = _get_volume_control()
    if not vol_ctrl:
        return {"status": "error", "message": "Failed to connect to system audio device control."}
    try:
        current = vol_ctrl.GetMasterVolumeLevelScalar()
        new_vol = min(1.0, current + 0.1) # Increase by 10%
        vol_ctrl.SetMasterVolumeLevelScalar(new_vol, None)
        return {"status": "success", "message": f"Volume increased to {int(new_vol * 100)}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to increase volume: {e}"}

def decrease_volume() -> dict:
    vol_ctrl = _get_volume_control()
    if not vol_ctrl:
        return {"status": "error", "message": "Failed to connect to system audio device control."}
    try:
        current = vol_ctrl.GetMasterVolumeLevelScalar()
        new_vol = max(0.0, current - 0.1) # Decrease by 10%
        vol_ctrl.SetMasterVolumeLevelScalar(new_vol, None)
        return {"status": "success", "message": f"Volume decreased to {int(new_vol * 100)}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to decrease volume: {e}"}

def mute_volume() -> dict:
    vol_ctrl = _get_volume_control()
    if not vol_ctrl:
        return {"status": "error", "message": "Failed to connect to system audio device control."}
    try:
        vol_ctrl.SetMute(1, None)
        return {"status": "success", "message": "Audio muted successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to mute audio: {e}"}

def unmute_volume() -> dict:
    vol_ctrl = _get_volume_control()
    if not vol_ctrl:
        return {"status": "error", "message": "Failed to connect to system audio device control."}
    try:
        vol_ctrl.SetMute(0, None)
        return {"status": "success", "message": "Audio unmuted successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to unmute audio: {e}"}

# --- Brightness handlers ---

def set_brightness(brightness: int) -> dict:
    try:
        sbc.set_brightness(brightness)
        return {"status": "success", "message": f"Screen brightness set to {brightness}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set brightness: {e}"}

def increase_brightness() -> dict:
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            current = current[0]
        new_b = min(100, current + 10)
        sbc.set_brightness(new_b)
        return {"status": "success", "message": f"Brightness increased to {new_b}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to increase brightness: {e}"}

def decrease_brightness() -> dict:
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            current = current[0]
        new_b = max(0, current - 10)
        sbc.set_brightness(new_b)
        return {"status": "success", "message": f"Brightness decreased to {new_b}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to decrease brightness: {e}"}

# --- Screenshot handler ---

def take_screenshot() -> dict:
    try:
        # Save to a local screenshots directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshot_dir = os.path.join(base_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filename = f"screenshot_{int(time.time())}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        return {
            "status": "success",
            "message": f"Screenshot saved successfully at: {filepath}",
            "data": {"filepath": filepath}
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to capture screenshot: {e}"}

# --- System Shutdown ---

def shutdown_system() -> dict:
    try:
        # Trigger standard Windows shutdown command
        os.system("shutdown /s /t 1")
        return {"status": "success", "message": "Shutdown signal sent successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute shutdown command: {e}"}
