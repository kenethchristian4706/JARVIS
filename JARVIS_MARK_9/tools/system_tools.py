"""
tools/system_tools.py

Implement execution handlers for system operations:
audio, brightness, clipboard, screenshot, system control, browser web search,
and file download utility handlers.
"""

import os
import time
import logging
import tempfile
import webbrowser
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional
from ctypes import cast, POINTER

import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pyautogui
import win32clipboard

import config

logger = logging.getLogger(__name__)

# --- AUDIO AUDIO UTILITIES ---

def _get_volume_interface() -> Optional[POINTER(IAudioEndpointVolume)]:
    """
    Retrieves the Windows master audio endpoint volume controller.
    """
    try:
        # Initialize COM libraries in current thread context
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
        else:
            logger.error("Audio device did not expose Activate or EndpointVolume.")
            return None
    except Exception as e:
        logger.error(f"Error accessing system audio devices: {e}")
        return None

def set_volume(volume: int) -> str:
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    vol.SetMasterVolumeLevelScalar(volume / 100.0, None)
    return f"System volume set to {volume}%"

def increase_volume(amount: Optional[int] = 10) -> str:
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current = vol.GetMasterVolumeLevelScalar()
    new_vol = min(1.0, current + (amount / 100.0))
    vol.SetMasterVolumeLevelScalar(new_vol, None)
    return f"Increased volume to {int(new_vol * 100)}%"

def decrease_volume(amount: Optional[int] = 10) -> str:
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current = vol.GetMasterVolumeLevelScalar()
    new_vol = max(0.0, current - (amount / 100.0))
    vol.SetMasterVolumeLevelScalar(new_vol, None)
    return f"Decreased volume to {int(new_vol * 100)}%"

def mute_volume() -> str:
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    vol.SetMute(1, None)
    return "Muted system audio."

def unmute_volume() -> str:
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    vol.SetMute(0, None)
    return "Unmuted system audio."

# --- BRIGHTNESS CONTROLS ---

def set_brightness(brightness: int) -> str:
    try:
        sbc.set_brightness(brightness)
        return f"Display brightness adjusted to {brightness}%"
    except Exception as e:
        # Deskop monitors may not support display control
        raise OSError(f"Failed to adjust screen brightness: {e}")

def increase_brightness(amount: Optional[int] = 10) -> str:
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            current = current[0]
        new_val = min(100, current + amount)
        sbc.set_brightness(new_val)
        return f"Increased screen brightness to {new_val}%"
    except Exception as e:
        raise OSError(f"Failed to adjust screen brightness: {e}")

def decrease_brightness(amount: Optional[int] = 10) -> str:
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            current = current[0]
        new_val = max(0, current - amount)
        sbc.set_brightness(new_val)
        return f"Decreased screen brightness to {new_val}%"
    except Exception as e:
        raise OSError(f"Failed to adjust screen brightness: {e}")

# --- SYSTEM MANAGEMENT ---

def shutdown_system() -> str:
    os.system("shutdown /s /t 1")
    return "Shutdown command executed successfully."

def restart_system() -> str:
    os.system("shutdown /r /t 1")
    return "Reboot command executed successfully."

def sleep_system() -> str:
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "System placed in sleep/suspend mode."

def lock_system() -> str:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Windows session locked."

def logout_user() -> str:
    os.system("shutdown /l")
    return "Logged out current Windows user session."

# --- CLIPBOARD MANAGEMENT ---

def copy_to_clipboard(text: str) -> str:
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return f"Copied to clipboard: '{text[:30]}...'"

def read_clipboard() -> str:
    win32clipboard.OpenClipboard()
    try:
        data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return f"Clipboard text: {data}"

def clear_clipboard() -> str:
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
    finally:
        win32clipboard.CloseClipboard()
    return "Cleared clipboard contents."

# --- SCREENSHOT & NOTEPAD WRITE ---

def take_screenshot(filename: Optional[str] = None) -> str:
    # Resolve screenshot path
    if filename:
        # Access check handled by imports
        from tools.file_tools import _resolve_path
        save_path = _resolve_path(filename)
        if not save_path.suffix:
            save_path = save_path.with_suffix(".png")
    else:
        # Default screenshots directory in Aether home
        screenshots_dir = Path(__file__).parent.parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        save_path = screenshots_dir / f"screenshot_{int(time.time())}.png"
        
    screenshot = pyautogui.screenshot()
    screenshot.save(str(save_path))
    return f"Screenshot saved successfully at: {save_path}"

def open_notepad_and_write(app_name: str = "notepad", text: str = "") -> str:
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / "aether_notepad_write.txt"
    
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text)
        
    subprocess.Popen([app_name + ".exe" if not app_name.endswith(".exe") else app_name, str(temp_file)])
    return f"Opened Notepad containing text details."

def extract_text_from_image(filename: str) -> str:
    # Safe OCR stub
    from tools.file_tools import _resolve_path
    path = _resolve_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Image not found at path: {path}")
        
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return f"Extracted Text:\n{text.strip()}"
    except ImportError:
        return f"[OCR Simulation] Found image '{path.name}'. Pytesseract is not installed; simulated text returned: 'Mock OCR content from image.'"

# --- WEB BROWSER SEARCH & INTERACTIONS ---

def open_website(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened website: {url}"

def google_search(query: str) -> str:
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searched Google for: '{query}'"

def youtube_search(query: str) -> str:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searched YouTube for: '{query}'"

def website_search(site: str, query: str) -> str:
    url = f"https://www.google.com/search?q=site%3A{site}+{urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searched inside '{site}' for '{query}'"

# --- Web interactions & agents stubs ---

def close_browser() -> str:
    return "Closed active web browser window (simulated)."

def open_new_tab() -> str:
    webbrowser.open("about:blank")
    return "Opened new browser tab."

def switch_tab(tab_identifier: str) -> str:
    return f"Switched tab focus to browser identifier: {tab_identifier} (simulated)."

def close_tab(tab_identifier: Optional[str] = None) -> str:
    return f"Closed tab identifier: {tab_identifier or 'active'} (simulated)."

def fill_form(field_identifier: str, value: str) -> str:
    return f"Filled form field '{field_identifier}' with value '{value}' (simulated)."

def submit_form() -> str:
    return "Submitted browser web form (simulated)."

def click_element(element_identifier: str) -> str:
    return f"Clicked web element: '{element_identifier}' (simulated)."

def type_text(text: str) -> str:
    return f"Typed text string in browser element: '{text}' (simulated)."

def scroll_page(direction: str, amount: Optional[int] = 300) -> str:
    return f"Scrolled web page {direction} by {amount} pixels (simulated)."

# --- File downloads ---

def download_file(url: str, destination: Optional[str] = None) -> str:
    if destination:
        from tools.file_tools import _resolve_path
        dest_path = _resolve_path(destination)
    else:
        # Default user Downloads folder fallback
        dest_path = Path(os.environ.get("USERPROFILE", "C:/Users/Default")) / "Downloads"
        
    dest_path.mkdir(parents=True, exist_ok=True)
    filename = Path(urllib.parse.urlparse(url).path).name or "downloaded_file"
    target = dest_path / filename
    
    # Check access permission on target file destination
    from tools.file_tools import _has_access
    if not _has_access(target):
        raise PermissionError(f"Access Denied: Cannot save download to '{target}'. Unauthorized folder.")
        
    logger.info(f"Downloading from '{url}' to '{target}'...")
    urllib.request.urlretrieve(url, str(target))
    return f"Successfully downloaded file to: {target}"

def upload_file(filename: str, field_identifier: Optional[str] = None) -> str:
    from tools.file_tools import _resolve_path
    path = _resolve_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return f"Uploaded file '{path}' to browser field '{field_identifier or 'default'}' (simulated)."

def browser_agent(task: str) -> str:
    return f"Browser agent successfully started task: '{task}' (simulated)."
