"""
platform/windows/app_tools.py

Windows implementation of ApplicationAPI.
Manages application registry scanning, process monitoring, window switching, etc.
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
import winreg

from aether.platforms.common.interfaces import ApplicationAPI
from aether.platforms.common.aliases import resolve_alias
from aether.platforms.common.exceptions import AppNotFoundError, ProcessError

logger = logging.getLogger(__name__)

class WindowsApplicationAPI(ApplicationAPI):
    def __init__(self):
        self._installed_apps_cache = {}

    def scan_installed_applications(self) -> dict[str, str]:
        """Scans registry and common folders to map installed applications."""
        if self._installed_apps_cache:
            return self._installed_apps_cache

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

        self._installed_apps_cache = apps
        return apps

    def open_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "windows")
        apps = self.scan_installed_applications()
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
                if exe_path.lower().endswith(".lnk"):
                    os.startfile(exe_path)
                else:
                    subprocess.Popen([exe_path], close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
                return f"Successfully opened '{resolved_name}' from path '{exe_path}'"
            except Exception as e:
                logger.error(f"Error launching '{exe_path}': {e}")
                
        # Fallback: let OS shell launch it
        try:
            os.startfile(resolved_name)
            return f"Successfully launched '{resolved_name}' via Windows OS shell."
        except Exception:
            try:
                os.startfile(app_name)
                return f"Successfully launched '{app_name}' via Windows OS shell."
            except Exception as e:
                raise AppNotFoundError(f"Could not open application '{app_name}' or resolved '{resolved_name}'. Reason: {e}")

    def close_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "windows")
        clean_name = resolved_name.lower().strip()
        orig_clean = app_name.lower().strip()
        terminated_count = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name']
                if name:
                    proc_clean = name.lower().replace(".exe", "")
                    if (clean_name in proc_clean or proc_clean in clean_name or
                        orig_clean in proc_clean or proc_clean in orig_clean):
                        proc.terminate()
                        terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if terminated_count > 0:
            return f"Successfully closed {terminated_count} running instance(s) of '{resolved_name}'."
        else:
            raise AppNotFoundError(f"No running processes found matching '{app_name}' or '{resolved_name}'.")

    def _get_hwnds_for_pid(self, pid: int) -> list[int]:
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

    def switch_to_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "windows")
        clean_name = resolved_name.lower().strip()
        orig_clean = app_name.lower().strip()
        
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
            hwnds = self._get_hwnds_for_pid(pid)
            for hwnd in hwnds:
                title = win32gui.GetWindowText(hwnd)
                if title:
                    try:
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
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

        # Fallback using pygetwindow title searching
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

    def list_running_apps(self) -> list[str]:
        running = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and name.lower().endswith(".exe"):
                    running.add(Path(name).stem.title())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(list(running))

    def list_installed_apps(self) -> list[str]:
        apps = self.scan_installed_applications()
        return sorted(list({name.title() for name in apps.keys()}))

    def verify_app_exists(self, app_name: str) -> bool:
        apps = self.scan_installed_applications()
        clean_name = app_name.lower().strip()
        if clean_name in apps:
            return True
            
        for k in apps.keys():
            if clean_name in k or k in clean_name:
                return True

        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for ext in ["", ".exe", ".bat", ".cmd"]:
            for d in path_dirs:
                if os.path.exists(os.path.join(d, app_name + ext)):
                    return True

        # Check common system programs aliases
        resolved = resolve_alias(app_name, "windows")
        if resolved.lower().strip() in apps:
            return True

        if app_name.lower() in ["chrome", "notepad", "spotify", "calc", "calculator", "explorer", "paint", "mspaint", "teams", "ms-teams", "ms-teams.exe", "whatsapp", "whatsapp.root", "whatsapp:"]:
            return True

        return False
