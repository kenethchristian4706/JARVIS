"""
tools/app_tools.py

Implements handlers for application management:
open_app, close_app, switch_to_app, list_running_apps, list_installed_apps.
"""

import os
import subprocess
import logging
import psutil
from pathlib import Path
import pygetwindow as gw
import win32gui
import win32process
import win32con

from aether.validation.validators import scan_installed_applications
from aether.tools.app_aliases import resolve_app_name

logger = logging.getLogger(__name__)

def get_hwnds_for_pid(pid: int) -> list[int]:
    """Enumerate all visible/enabled HWNDs for a given PID."""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
            if win_pid == pid:
                hwnds.append(hwnd)
        return True
    hwnds = []
    try:
        win32gui.EnumWindows(callback, hwnds)
    except Exception as e:
        logger.warning(f"Error enumerating windows: {e}")
    return hwnds

def open_app(app_name: str) -> str:
    """Launches an application by name, searching local system paths with alias resolution."""
    resolved_name = resolve_app_name(app_name)
    apps = scan_installed_applications()
    clean_name = resolved_name.lower().strip()
    
    exe_path = apps.get(clean_name)
    if not exe_path:
        # Substring matching
        for k, v in apps.items():
            if clean_name in k or k in clean_name:
                exe_path = v
                break
                
    if exe_path:
        try:
            # Launch using os.startfile for shortcut links (.lnk), subprocess for others
            if exe_path.lower().endswith(".lnk"):
                os.startfile(exe_path)
            else:
                subprocess.Popen([exe_path], close_fds=True, creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
            return f"Successfully opened '{resolved_name}' from path '{exe_path}'"
        except Exception as e:
            logger.error(f"Error launching '{exe_path}': {e}")
            
    # Fallback: let OS shell launch it
    try:
        if resolved_name.lower().endswith(".lnk"):
            os.startfile(resolved_name)
        else:
            os.startfile(resolved_name)
        return f"Successfully launched '{resolved_name}' via Windows OS shell."
    except Exception:
        try:
            os.startfile(app_name)
            return f"Successfully launched '{app_name}' via Windows OS shell."
        except Exception as e:
            # Fallback to opening the app's website if not found locally
            try:
                web_mappings = {
                    "spotify": "https://www.spotify.com",
                    "chrome": "https://www.google.com/chrome",
                    "firefox": "https://www.mozilla.org/firefox",
                    "edge": "https://www.microsoft.com/edge",
                    "vscode": "https://code.visualstudio.com",
                    "vs code": "https://code.visualstudio.com",
                    "visual studio code": "https://code.visualstudio.com",
                    "discord": "https://discord.com",
                    "slack": "https://slack.com",
                    "notion": "https://www.figma.com" if "figma" in clean_name else "https://www.notion.so",
                    "zoom": "https://zoom.us",
                    "whatsapp": "https://www.whatsapp.com",
                    "telegram": "https://telegram.org",
                    "skype": "https://www.skype.com",
                    "steam": "https://store.steampowered.com",
                    "excel": "https://www.office.com",
                    "word": "https://www.office.com",
                    "powerpoint": "https://www.office.com",
                    "teams": "https://www.microsoft.com/microsoft-teams",
                    "obs": "https://obsproject.com",
                    "vlc": "https://www.videolan.org/vlc",
                    "github": "https://github.com",
                    "figma": "https://www.figma.com",
                    "canva": "https://www.canva.com",
                }
                
                target_url = None
                for k, url in web_mappings.items():
                    if k in clean_name or clean_name in k:
                        target_url = url
                        break
                
                if not target_url:
                    import urllib.parse
                    query = urllib.parse.quote(f"{app_name} website")
                    target_url = f"https://www.google.com/search?q={query}"
                
                import webbrowser
                webbrowser.open(target_url)
                return f"Application '{app_name}' was not found on your system. Opened its website instead: {target_url}"
            except Exception as web_err:
                raise FileNotFoundError(f"Could not open application '{app_name}' or resolved '{resolved_name}' and failed to open fallback website. Reason: {e}, Web error: {web_err}")

def close_app(app_name: str) -> str:
    """Closes all active process instances of a given application by name, using alias matching."""
    resolved_name = resolve_app_name(app_name)
    clean_name = resolved_name.lower().strip()
    orig_clean = app_name.lower().strip()
    terminated_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if name:
                proc_clean = name.lower().replace(".exe", "")
                # Match against normalized/resolved name and original query name
                if (clean_name in proc_clean or proc_clean in clean_name or
                    orig_clean in proc_clean or proc_clean in orig_clean):
                    proc.terminate()
                    terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if terminated_count > 0:
        return f"Successfully closed {terminated_count} running instance(s) of '{resolved_name}'."
    else:
        raise ProcessLookupError(f"No running processes found matching '{app_name}' or '{resolved_name}'.")

def switch_to_app(app_name: str) -> str:
    """Brings the application window to foreground focus with alias support."""
    resolved_name = resolve_app_name(app_name)
    clean_name = resolved_name.lower().strip()
    orig_clean = app_name.lower().strip()
    
    # Method 1: Find process PID, then matching HWND and restore/focus
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if name:
                proc_clean = name.lower().replace(".exe", "")
                if (clean_name in proc_clean or proc_clean in clean_name or
                    orig_clean in proc_clean or proc_clean in orig_clean):
                    pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    activated = False
    activated_title = ""
    for pid in pids:
        hwnds = get_hwnds_for_pid(pid)
        for hwnd in hwnds:
            title = win32gui.GetWindowText(hwnd)
            if title:
                try:
                    # Restore if minimized
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    # Bring window to foreground
                    win32gui.SetForegroundWindow(hwnd)
                    activated = True
                    activated_title = title
                    break
                except Exception as e:
                    logger.warning(f"Failed to SetForegroundWindow for hwnd {hwnd}: {e}")
        if activated:
            break
            
    if activated:
        return f"Switched focus to window '{activated_title}'."

    # Method 2: Fallback using pygetwindow title searching
    try:
        windows = gw.getAllWindows()
        for w in windows:
            title_lower = w.title.lower()
            matches = [
                "google chrome" in title_lower if "chrome" in clean_name or "chrome" in orig_clean else False,
                "visual studio code" in title_lower if "code" in clean_name or "code" in orig_clean else False,
                "discord" in title_lower if "discord" in clean_name or "discord" in orig_clean else False,
                "notepad" in title_lower if "notepad" in clean_name or "notepad" in orig_clean else False,
                clean_name in title_lower,
                orig_clean in title_lower
            ]
            if any(matches) and w.title:
                w.activate()
                return f"Switched focus to window '{w.title}'."
    except Exception as e:
        logger.warning(f"Error bringing window to focus: {e}")
        
    return (
        "Application is not currently running.\n"
        "Would you like me to open it instead?"
    )

def list_running_apps() -> list[str]:
    """Lists unique names of currently running application processes."""
    running = set()
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name']
            if name and name.lower().endswith(".exe"):
                # Capitalize base name
                running.add(Path(name).stem.title())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(list(running))

def list_installed_apps() -> list[str]:
    """Lists names of all scanned/installed applications on the system."""
    apps = scan_installed_applications()
    return sorted(list({name.title() for name in apps.keys()}))
