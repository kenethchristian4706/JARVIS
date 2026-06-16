"""
tools/app_handlers.py

Implements execution handlers for application management:
open_app, close_app, list_installed_apps.
"""

import os
import subprocess
import psutil
from indexing.app_indexer import get_executable_by_name, list_indexed_apps

def open_app(app_name: str) -> dict:
    """
    Launches an application executable.
    """
    exe_path = get_executable_by_name(app_name)
    
    if not exe_path:
        # Fallback to shell start (which may trigger default handler or system PATH lookup)
        try:
            # os.startfile is Windows specific and robust for protocol/shortcuts
            os.startfile(app_name)
            return {"status": "success", "message": f"Triggered OS startfile fallback for '{app_name}'."}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Application '{app_name}' not found in index and command execution failed: {e}"
            }

    try:
        # Launch process in background detached
        subprocess.Popen([exe_path], close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
        return {"status": "success", "message": f"Successfully launched {app_name} from: {exe_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute application process: {e}"}

def close_app(app_name: str) -> dict:
    """
    Terminates running instances of an application.
    """
    clean_name = app_name.lower().strip()
    terminated_count = 0
    errors = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name']
            if proc_name and (clean_name in proc_name.lower() or proc_name.lower() in clean_name):
                proc.terminate()
                terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            errors.append(str(e))
            
    if terminated_count > 0:
        return {"status": "success", "message": f"Terminated {terminated_count} running process instances matching '{app_name}'."}
    else:
        msg = f"No active processes found matching '{app_name}'."
        if errors:
            msg += f" Encountered permission locks: {', '.join(errors[:2])}"
        return {"status": "error", "message": msg}

def list_installed_apps() -> dict:
    """
    Lists all indexed desktop applications.
    """
    apps = list_indexed_apps()
    app_names = [row["app_name"] for row in apps]
    return {
        "status": "success",
        "message": f"Found {len(app_names)} indexed applications.",
        "data": app_names
    }
