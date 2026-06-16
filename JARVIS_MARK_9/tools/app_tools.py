"""
tools/app_tools.py

Implement handlers for application management:
open_app, close_app, switch_to_app, list_running_apps, list_installed_apps.
"""

import os
import logging
import subprocess
import psutil
import winreg
import win32com.client
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache of installed apps to speed up search
_installed_apps_cache = {}

def _resolve_shortcut(lnk_path: Path) -> str:
    """
    Extracts the target executable path from a .lnk shortcut.
    """
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(lnk_path))
        target = shortcut.TargetPath
        if target and Path(target).exists() and target.lower().endswith(".exe"):
            return str(Path(target).resolve())
    except Exception:
        pass
    return ""

def _scan_installed_applications() -> dict[str, str]:
    """
    Scans Windows registry, Start Menu, and system paths to index apps (name -> exe_path).
    """
    global _installed_apps_cache
    if _installed_apps_cache:
        return _installed_apps_cache
        
    apps = {}
    
    # 1. Registry scans for Uninstall path
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    for hive, subkey in registry_keys:
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)
                for i in range(num_subkeys):
                    try:
                        name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, name) as sub:
                            try:
                                display_name, _ = winreg.QueryValueEx(sub, "DisplayName")
                                install_loc, _ = winreg.QueryValueEx(sub, "InstallLocation")
                                if display_name and install_loc and Path(install_loc).exists():
                                    # Search for executable
                                    for file in Path(install_loc).iterdir():
                                        if file.name.lower().endswith(".exe") and "uninstall" not in file.name.lower():
                                            apps[display_name.lower().strip()] = str(file.resolve())
                                            break
                            except (FileNotFoundError, OSError):
                                pass
                    except Exception:
                        pass
        except Exception:
            pass
            
    # 2. Start Menu Shortcuts scan
    paths_to_scan = [
        Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs"
    ]
    for base_path in paths_to_scan:
        if base_path.exists():
            for child in base_path.rglob("*.lnk"):
                target = _resolve_shortcut(child)
                if target:
                    apps[child.stem.lower().strip()] = target
                    
    # 3. System built-ins
    system32 = Path("C:/Windows/System32")
    builtins = {
        "notepad": system32 / "notepad.exe",
        "calculator": system32 / "calc.exe",
        "command prompt": system32 / "cmd.exe",
        "powershell": system32 / "WindowsPowerShell/v1.0/powershell.exe",
        "paint": system32 / "mspaint.exe",
        "wordpad": Path("C:/Program Files/Windows NT/Accessories/wordpad.exe")
    }
    for name, path in builtins.items():
        if path.exists():
            apps[name] = str(path.resolve())
            
    # Add alias equivalents
    aliases = {
        "chrome": "google chrome",
        "vscode": "visual studio code",
        "vs code": "visual studio code",
        "calc": "calculator",
        "explorer": "windows explorer",
        "file explorer": "windows explorer"
    }
    for alias, full_name in aliases.items():
        for key, path in list(apps.items()):
            if key == full_name or full_name in key:
                apps[alias] = path
                
    _installed_apps_cache = apps
    return apps

# --- Handlers ---

def open_app(app_name: str) -> str:
    """
    Launches an application by name.
    """
    apps = _scan_installed_applications()
    clean_name = app_name.lower().strip()
    
    # Try direct lookup
    exe_path = apps.get(clean_name)
    
    # Try substring match
    if not exe_path:
        for name, path in apps.items():
            if clean_name in name or name in clean_name:
                exe_path = path
                break
                
    if exe_path:
        # Open using detached process to prevent locking Aether terminal
        subprocess.Popen([exe_path], close_fds=True, creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
        return f"Successfully launched {app_name} from '{exe_path}'"
    else:
        # Fallback to os.startfile which lets Windows resolve it via PATH/registered protocols
        try:
            os.startfile(app_name)
            return f"Opened application '{app_name}' via OS shell launcher."
        except Exception as e:
            raise FileNotFoundError(f"Could not find application executable or shell path for '{app_name}'. Error: {e}")

def close_app(app_name: str) -> str:
    """
    Closes all active process instances of an application.
    """
    clean_name = app_name.lower().strip()
    terminated_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if name and (clean_name in name.lower() or name.lower() in clean_name):
                proc.terminate()
                terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if terminated_count > 0:
        return f"Closed {terminated_count} running instances of '{app_name}'."
    else:
        raise ProcessLookupError(f"No running processes found matching '{app_name}'.")

def switch_to_app(app_name: str) -> str:
    """
    Brings the application window to foreground focus.
    """
    clean_name = app_name.lower().strip()
    shell = win32com.client.Dispatch("WScript.Shell")
    
    # Try activating by name directly
    activated = shell.AppActivate(clean_name)
    
    # If failed, find exact window name using active processes
    if not activated:
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and clean_name in name.lower():
                    # Strip .exe extension for activation title match
                    stem = Path(name).stem
                    if shell.AppActivate(stem):
                        activated = True
                        break
            except Exception:
                pass
                
    if activated:
        return f"Switched window focus to '{app_name}'."
    else:
        raise ProcessLookupError(f"Failed to focus on window matching '{app_name}'. Is it running?")

def list_running_apps() -> list[str]:
    """
    Lists all unique names of running application processes.
    """
    running = set()
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name']
            if name and name.lower().endswith(".exe"):
                # Clean name (e.g. Chrome.exe -> Chrome)
                running.add(Path(name).stem)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(list(running))

def list_installed_apps() -> list[str]:
    """
    Lists names of all indexed installed applications.
    """
    apps = _scan_installed_applications()
    # Return formatted list of unique application titles capitalized
    return sorted([name.title() for name in apps.keys()])
