"""
indexing/app_indexer.py

Scans the Windows Registry, Start Menu Shortcuts, and common install locations
to index all installed desktop applications and executable paths into SQLite.
"""

import os
import winreg
import sqlite3
import win32com.client
from database.db_manager import get_db_connection

def resolve_lnk_shortcut(lnk_path: str) -> str:
    """
    Uses WScript.Shell to extract the target absolute executable path from a .lnk shortcut.
    """
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.TargetPath
        if target and os.path.exists(target) and target.lower().endswith(".exe"):
            return os.path.normpath(target)
    except Exception:
        pass
    return ""

def scan_registry_uninstall(hive, subkey) -> list:
    """
    Scans a registry uninstall registry branch and returns list of (app_name, exe_path).
    """
    apps = []
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
                            
                            # Clean and verify path
                            if display_name and install_loc and os.path.exists(install_loc):
                                # Try to find main executable in location
                                for file in os.listdir(install_loc):
                                    if file.lower().endswith(".exe") and not "uninstall" in file.lower():
                                        exe_path = os.path.join(install_loc, file)
                                        apps.append((display_name, os.path.normpath(exe_path)))
                                        break
                        except (FileNotFoundError, OSError):
                            pass
                except Exception:
                    pass
    except Exception:
        pass
    return apps

def scan_start_menu_shortcuts() -> list:
    """
    Recursively scans the System and User Start Menu folders for executable shortcuts.
    """
    apps = []
    paths_to_scan = [
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs")
    ]
    
    for base_path in paths_to_scan:
        if not os.path.exists(base_path):
            continue
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith(".lnk"):
                    lnk_path = os.path.join(root, file)
                    target_exe = resolve_lnk_shortcut(lnk_path)
                    if target_exe:
                        app_name = os.path.splitext(file)[0]
                        apps.append((app_name, target_exe))
    return apps

def scan_common_install_directories() -> list:
    """
    Scans common Program Files and Local AppData Program install trees for executables.
    """
    apps = []
    roots = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")
    ]
    
    # List of common popular apps to look for
    common_app_names = ["chrome", "spotify", "discord", "vscode", "notepad++", "slack"]
    
    for r in roots:
        if not os.path.exists(r):
            continue
        for folder in os.listdir(r):
            folder_path = os.path.join(r, folder)
            if os.path.isdir(folder_path):
                # Check for executables inside directory matching folder name or common app names
                try:
                    for f in os.listdir(folder_path):
                        if f.lower().endswith(".exe") and not "uninstall" in f.lower():
                            if folder.lower() in f.lower() or any(app in f.lower() for app in common_app_names):
                                apps.append((folder, os.path.normpath(os.path.join(folder_path, f))))
                                break
                except OSError:
                    pass
    return apps

def index_installed_applications():
    """
    Gathers applications from registry, shortcuts, and folders, merging and indexing into SQLite.
    """
    print("[AppIndexer] Initializing application lookup scanning...")
    all_apps = {}
    
    # 1. Registry scans
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    for hive, subkey in registry_keys:
        for name, path in scan_registry_uninstall(hive, subkey):
            all_apps[path] = name
            
    # 2. Shortcuts scan
    for name, path in scan_start_menu_shortcuts():
        all_apps[path] = name
        
    # 3. Common directory scan
    for name, path in scan_common_install_directories():
        all_apps[path] = name
        
    # Include default system built-ins
    system_builtins = {
        os.path.normpath("C:\\Windows\\system32\\notepad.exe"): "Notepad",
        os.path.normpath("C:\\Windows\\system32\\calc.exe"): "Calculator",
        os.path.normpath("C:\\Windows\\system32\\cmd.exe"): "Command Prompt",
        os.path.normpath("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"): "PowerShell"
    }
    for path, name in system_builtins.items():
        if os.path.exists(path):
            all_apps[path] = name
            
    print(f"[AppIndexer] Found {len(all_apps)} unique application executables. Saving to SQLite...")
    
    # Save applications to database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for path, name in all_apps.items():
            # Generate common search alias lowercased
            alias = name.lower()
            cursor.execute("""
                INSERT OR REPLACE INTO installed_apps (app_name, executable_path, aliases)
                VALUES (?, ?, ?)
            """, (name, path, alias))
        conn.commit()
        
    print("[AppIndexer] Application indexing completed successfully.")

def get_executable_by_name(app_name: str) -> str:
    """
    Query registry for executable path by name lookup.
    """
    clean_name = app_name.lower().strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Direct name match or alias lookup
        cursor.execute(
            "SELECT executable_path FROM installed_apps WHERE LOWER(app_name) = ? OR aliases LIKE ?",
            (clean_name, f"%{clean_name}%")
        )
        row = cursor.fetchone()
        if row:
            return row["executable_path"]
    return ""

def list_indexed_apps() -> list:
    """
    Lists all indexed application names.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT app_name, executable_path FROM installed_apps ORDER BY app_name ASC")
        return cursor.fetchall()

if __name__ == "__main__":
    index_installed_applications()
