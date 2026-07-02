"""
platform/mac/app_tools.py

macOS implementation of ApplicationAPI.
"""

import os
import subprocess
import logging
import psutil
from pathlib import Path

from aether.platforms.common.interfaces import ApplicationAPI
from aether.platforms.common.aliases import resolve_alias
from aether.platforms.common.exceptions import AppNotFoundError

logger = logging.getLogger(__name__)

class MacApplicationAPI(ApplicationAPI):
    def __init__(self):
        self._installed_apps_cache = {}

    def scan_installed_applications(self) -> dict[str, str]:
        if self._installed_apps_cache:
            return self._installed_apps_cache
        
        apps = {}
        search_dirs = [Path("/Applications"), Path("/System/Applications"), Path.home() / "Applications"]
        for directory in search_dirs:
            if directory.exists():
                try:
                    for item in directory.iterdir():
                        if item.name.lower().endswith(".app"):
                            apps[item.stem.lower().strip()] = str(item.resolve())
                except Exception as e:
                    logger.warning(f"Error scanning directory {directory}: {e}")
        self._installed_apps_cache = apps
        return apps

    def open_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "mac")
        apps = self.scan_installed_applications()
        clean_name = resolved_name.lower().strip()
        app_path = apps.get(clean_name)
        
        if not app_path:
            for k, v in apps.items():
                if clean_name in k or k in clean_name:
                    app_path = v
                    resolved_name = k.title()
                    break
        
        try:
            if app_path:
                subprocess.run(["open", app_path], check=True)
                return f"Successfully opened '{resolved_name}' from path '{app_path}'"
            else:
                subprocess.run(["open", "-a", resolved_name], check=True)
                return f"Successfully launched '{resolved_name}' via macOS open command."
        except Exception as e:
            raise AppNotFoundError(f"Could not open application '{app_name}' or resolved '{resolved_name}'. Reason: {e}")

    def close_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "mac")
        try:
            cmd = f'tell application "{resolved_name}" to quit'
            res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Successfully closed '{resolved_name}'."
        except Exception:
            pass
            
        clean_name = resolved_name.lower().strip()
        terminated_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name']
                if name and (clean_name in name.lower() or app_name.lower() in name.lower()):
                    proc.terminate()
                    terminated_count += 1
            except Exception:
                pass
        if terminated_count > 0:
            return f"Successfully closed {terminated_count} running instance(s) of '{resolved_name}'."
        raise AppNotFoundError(f"No running processes found matching '{app_name}' or '{resolved_name}'.")

    def switch_to_app(self, app_name: str) -> str:
        resolved_name = resolve_alias(app_name, "mac")
        try:
            cmd = f'tell application "{resolved_name}" to activate'
            res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Switched focus to '{resolved_name}'."
        except Exception as e:
            logger.warning(f"Error bringing app to focus: {e}")
        return f"Application '{resolved_name}' is not currently running or cannot be focused."

    def list_running_apps(self) -> list[str]:
        running = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and not name.startswith("sys") and not name.startswith("com."):
                    running.add(name.replace(".app", "").title())
            except Exception:
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
        resolved = resolve_alias(app_name, "mac")
        if resolved.lower().strip() in apps:
            return True
        return False
