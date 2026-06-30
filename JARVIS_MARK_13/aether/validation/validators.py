"""
validation/validators.py

Implements type validation and existence checks for files, folders, and applications.
"""

import os
import re
import logging
import urllib.parse
from pathlib import Path
import psutil
import winreg

logger = logging.getLogger(__name__)

# Cache of installed apps (lowercase name -> path)
_installed_apps_cache = {}

def validate_level(level: int) -> bool:
    """Validates volume or brightness levels to be within [0, 100]."""
    return isinstance(level, int) and 0 <= level <= 100

def validate_url(url: str) -> bool:
    """Validates if a string is a properly formatted URL."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def scan_installed_applications() -> dict[str, str]:
    """Scans registry and common folders to map installed applications."""
    global _installed_apps_cache
    if _installed_apps_cache:
        return _installed_apps_cache

    apps = {}

    # 1. Registry scans
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
                                if display_name and install_loc and os.path.exists(install_loc):
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

    # 2. Start Menu scan
    paths_to_scan = [
        Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs"
    ]
    for base_path in paths_to_scan:
        if base_path.exists():
            for child in base_path.rglob("*.lnk"):
                # Simplified shortcut target extraction using ctypes or ignoring for simplicity
                # If we don't have pywin32, we can just resolve it or store the name
                apps[child.stem.lower().strip()] = str(child.resolve())

    # 3. Standard Windows components
    system32 = Path("C:/Windows/System32")
    builtins = {
        "notepad": system32 / "notepad.exe",
        "calculator": system32 / "calc.exe",
        "command prompt": system32 / "cmd.exe",
        "cmd": system32 / "cmd.exe",
        "powershell": system32 / "WindowsPowerShell/v1.0/powershell.exe",
        "paint": system32 / "mspaint.exe",
        "wordpad": Path("C:/Program Files/Windows NT/Accessories/wordpad.exe"),
        "chrome": Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        "msedge": Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        "edge": Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        "explorer": Path("C:/Windows/explorer.exe"),
        "file explorer": Path("C:/Windows/explorer.exe")
    }
    for name, path in builtins.items():
        if path.exists():
            apps[name] = str(path.resolve())

    _installed_apps_cache = apps
    return apps

def verify_app_exists(app_name: str) -> bool:
    """Checks if an application name corresponds to an installed app or executable in PATH."""
    apps = scan_installed_applications()
    clean_name = app_name.lower().strip()
    if clean_name in apps:
        return True
    
    # Check substring matches
    for k in apps.keys():
        if clean_name in k or k in clean_name:
            return True

    # Check if executable is directly in the PATH environment variable
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for ext in ["", ".exe", ".bat", ".cmd"]:
        for d in path_dirs:
            if os.path.exists(os.path.join(d, app_name + ext)):
                return True

    # Check common system programs
    if app_name.lower() in ["chrome", "notepad", "spotify", "calc", "calculator", "explorer", "paint", "mspaint", "teams", "ms-teams", "ms-teams.exe", "whatsapp", "whatsapp.root", "whatsapp:"]:
        return True

    return False

def verify_file_exists(file_path: str) -> bool:
    """Verifies if a file exists at the given path."""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False

def verify_folder_exists(folder_path: str) -> bool:
    """Verifies if a folder/directory exists at the given path."""
    try:
        path = Path(folder_path)
        return path.exists() and path.is_dir()
    except Exception:
        return False
