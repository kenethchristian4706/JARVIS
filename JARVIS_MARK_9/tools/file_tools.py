"""
tools/file_tools.py

Implement execution handlers for local file and directory management.
Validates path authorization against approved directories before executing.
"""

import os
import shutil
import logging
import sqlite3
from pathlib import Path
from typing import Optional

import config
from indexing.file_indexer import lookup_file, lookup_file_multi
from tools.resolve_path import resolve_file_path

logger = logging.getLogger(__name__)

def _has_access(path: Path, db_path: str = str(config.DB_PATH)) -> bool:
    """
    Checks if a resolved path lies within any approved directories stored in the database.
    """
    if getattr(config, "ALL_PC_ACCESS", False):
        return True
        
    try:
        resolved_path = path.resolve()
        resolved_str = str(resolved_path).lower()
        
        # Connect to retrieve approved directories (have_access = 1)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path FROM file_index WHERE have_access = 1")
            approved_paths = [Path(row[0]).resolve() for row in cursor.fetchall()]
            
        for approved in approved_paths:
            approved_str = str(approved).lower()
            # If our path is child or starts with the approved path prefix
            if resolved_str.startswith(approved_str):
                return True
    except Exception as e:
        logger.error(f"Error checking access level for {path}: {e}")
    return False

def repair_windows_path(filename: str) -> str:
    r"""
    Repairs missing colons in Windows drive letter paths, e.g. c\users\... -> c:\users\...
    """
    import re
    match = re.match(r'^([a-zA-Z])([/\\].*)', filename)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    return filename

def _resolve_path(filename: str, db_path: str = str(config.DB_PATH), is_create: bool = False) -> Path:
    """
    Resolves a file path using DB lookup for simple filenames.
    Validates folder permission checks before returning.
    Supports resolving common directory prefixes, Windows drive paths repair,
    and prompts user if multiple matching file paths are found in the index.
    """
    import re
    cleaned_fn = filename.strip()
    
    # Check if the original name exists in the index or filesystem
    original_exists = False
    try:
        if Path(cleaned_fn).exists():
            original_exists = True
        else:
            base_name = Path(cleaned_fn).name.lower()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM file_index WHERE LOWER(file_name) = ? AND have_access = 1 LIMIT 1",
                    (base_name,)
                )
                if cursor.fetchone():
                    original_exists = True
    except Exception:
        pass

    # If it doesn't exist, check for noise prefix like "file ", "folder ", etc.
    if not original_exists:
        prefix_pattern = re.compile(r'^(file|folder|document|directory|path)\s+', re.IGNORECASE)
        filename = prefix_pattern.sub('', cleaned_fn)
    else:
        filename = cleaned_fn

    # 1. Repair Windows drive path if malformed (e.g. c\users\... -> c:\users\...)
    filename = repair_windows_path(filename)
    
    # 2. Check if filename starts with a common folder prefix (e.g. downloads/file.txt)
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
    common_paths = {
        "desktop": str(Path(user_profile) / "Desktop"),
        "documents": str(Path(user_profile) / "Documents"),
        "downloads": str(Path(user_profile) / "Downloads"),
        "pictures": str(Path(user_profile) / "Pictures"),
        "music": str(Path(user_profile) / "Music"),
        "videos": str(Path(user_profile) / "Videos")
    }
    
    normalized_fn = filename.replace("\\", "/")
    for alias, abs_dir in common_paths.items():
        if normalized_fn.lower().startswith(alias + "/"):
            filename = str(Path(abs_dir) / filename[len(alias)+1:])
            break
        elif normalized_fn.lower() == alias:
            filename = abs_dir
            break
            
    path = Path(filename)
    
    # 3. Resolve relative path
    if not path.is_absolute():
        # First, search index for matching file paths
        base_name = path.name.lower()
        candidates = []
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT absolute_path FROM file_index WHERE LOWER(file_name) = ? AND have_access = 1",
                    (base_name,)
                )
                candidates = [Path(row[0]).resolve() for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error querying file index for resolve: {e}")
            
        # If filename contains subfolders (e.g. "jarvis_mark_9/notes.txt"), filter candidates
        search_suffix = filename.replace("\\", "/").lower()
        if "/" in search_suffix or "\\" in filename:
            filtered = []
            for cand in candidates:
                cand_str = str(cand).replace("\\", "/").lower()
                if cand_str.endswith(search_suffix):
                    filtered.append(cand)
            candidates = filtered
            
        # Process lookup match
        resolved_path = None
        if candidates:
            if len(candidates) == 1:
                resolved_path = candidates[0]
            else:
                # Duplicates found! Prompt user on the console.
                print(f"\n[Aether] Multiple file matches found for '{filename}':")
                for idx, cand in enumerate(candidates, start=1):
                    print(f"  [{idx}] {cand}")
                print(f"  [{len(candidates) + 1}] Use current working directory fallback")
                print(f"  [{len(candidates) + 2}] Cancel operation")
                
                try:
                    choice_str = input(f"Select file index choice [1-{len(candidates)+2}]: ").strip()
                    choice = int(choice_str)
                except (ValueError, KeyboardInterrupt, EOFError):
                    choice = len(candidates) + 2
                    
                if 1 <= choice <= len(candidates):
                    resolved_path = candidates[choice - 1]
                elif choice == len(candidates) + 1:
                    resolved_path = None
                else:
                    raise PermissionError("Operation cancelled by user due to ambiguous file path choice.")
                    
        if resolved_path:
            path = resolved_path
        else:
            # Fallback to current working directory
            cwd_path = Path(os.path.abspath(filename))
            if _has_access(cwd_path, db_path):
                path = cwd_path
            else:
                # CWD fallback not authorized, resolve relative to the first approved folder in DB.
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT absolute_path FROM file_index WHERE extension IS NULL AND have_access = 1 LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        path = Path(row[0]) / filename
                    else:
                        cursor.execute("SELECT absolute_path FROM file_index WHERE have_access = 1 LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            first_path = Path(row[0])
                            if first_path.is_dir():
                                path = first_path / filename
                            else:
                                path = first_path.parent / filename
                        else:
                            path = cwd_path
                            
    resolved = path.resolve()
    
    # Enforce have_access validation
    if not _has_access(resolved, db_path):
        raise PermissionError(f"Access Denied: Path '{resolved}' is outside of authorized folders.")
        
    return resolved

# --- Handlers ---

def search_file(query: str) -> list[dict]:
    """
    Search index for matching file names.
    """
    results = lookup_file_multi(query, str(config.DB_PATH))
    # Filter to return only authorized matches
    return [r for r in results if r["have_access"] == 1]

def open_file(filename: str) -> str:
    """
    Opens a file using the OS default launcher.
    """
    resolved = resolve_file_path(filename)
    if not resolved:
        return "Operation cancelled."
    path = Path(resolved)
    os.startfile(str(path))
    return f"Successfully opened file: {path}"

def ask_create_directory(name: str, is_folder: bool = False) -> Optional[Path]:
    """
    Asks the user where to create the new file or folder.
    """
    type_name = "folder" if is_folder else "file"
    print(f"\nWhere would you like to create {type_name} \"{name}\"?\n")
    print("1. Current directory")
    print("2. Custom folder path")
    print("3. Downloads folder")
    print("4. Cancel")
    
    try:
        choice = input("\nChoice: ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
        
    if choice == "1":
        return Path(os.getcwd()) / name
    elif choice == "2":
        try:
            custom_path = input("Please provide the folder path: ").strip()
            path_obj = Path(custom_path).resolve()
            if path_obj.exists() and path_obj.is_dir():
                return path_obj / name
            else:
                print(f"Folder '{custom_path}' does not exist or is not a directory.")
                return None
        except Exception:
            return None
    elif choice == "3":
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
        downloads = Path(user_profile) / "Downloads"
        return downloads.resolve() / name
    else:
        return None

def create_file(filename: str, content: Optional[str] = None) -> str:
    """
    Creates a new blank or initialized file.
    """
    from tools.resolve_path import is_path
    
    import re
    cleaned_fn = filename.strip()
    prefix_pattern = re.compile(r'^(file|folder|document|directory|path)\s+', re.IGNORECASE)
    clean_name = prefix_pattern.sub('', cleaned_fn)
    
    if is_path(clean_name):
        path = Path(clean_name).resolve()
    else:
        path = ask_create_directory(clean_name, is_folder=False)
        if not path:
            return "Operation cancelled."
            
    if not _has_access(path):
        raise PermissionError(f"Access Denied: Path '{path}' is outside of authorized folders.")
        
    print(f"\nResolved file:\n\n{path}\n")
        
    # Check overwrite safety gate
    if path.exists() and path.is_file():
        print("\n⚠️ This action cannot be undone.\n")
        print(f"Overwrite:\n\n{path}\n")
        print("Type:")
        print("- Yes")
        print("- No")
        try:
            confirm = input().strip()
        except (KeyboardInterrupt, EOFError):
            return "Operation cancelled."
        if confirm != "Yes":
            return "Operation cancelled."
            
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            if content:
                f.write(content)
        return f"Created file: {path}"
    except Exception as e:
        return f"Failed to create file: {e}"

def delete_file(filename: str) -> str:
    """
    Deletes an existing file. HIGH RISK.
    """
    resolved = resolve_file_path(filename)
    if not resolved:
        return "Operation cancelled."
        
    path = Path(resolved)
    print("\n⚠️ This action cannot be undone.\n")
    print(f"Delete:\n\n{path}\n")
    print("Type:")
    print("- Yes")
    print("- No")
    try:
        confirm = input().strip()
    except (KeyboardInterrupt, EOFError):
        return "Operation cancelled."
        
    if confirm != "Yes":
        return "Operation cancelled."
        
    if path.is_dir():
        raise IsADirectoryError(f"Target is a directory: {path}")
        
    path.unlink()
    return f"Deleted file: {path}"

def rename_file(source: str, destination: str) -> str:
    """
    Renames a file in its parent folder.
    """
    src_resolved = resolve_file_path(source)
    if not src_resolved:
        return "Operation cancelled."
        
    src_path = Path(src_resolved)
    dest_path = src_path.parent / destination
    dest_resolved = dest_path.resolve()
    
    if not _has_access(dest_resolved):
        raise PermissionError(f"Access Denied: Rename target '{dest_resolved}' is outside of authorized folders.")
        
    if dest_resolved.exists():
        print("\n⚠️ This action cannot be undone.\n")
        print(f"Overwrite:\n\n{dest_resolved}\n")
        print("Type:")
        print("- Yes")
        print("- No")
        try:
            confirm = input().strip()
        except (KeyboardInterrupt, EOFError):
            return "Operation cancelled."
        if confirm != "Yes":
            return "Operation cancelled."
            
    src_path.rename(dest_resolved)
    return f"Renamed file '{src_path.name}' to '{destination}' at {dest_resolved}"

def move_file(source: str, destination: str) -> str:
    """
    Moves a file to a destination folder.
    """
    src_resolved = resolve_file_path(source)
    if not src_resolved:
        return "Operation cancelled."
        
    src_path = Path(src_resolved)
    dest_resolved = _resolve_path(destination, is_create=True)
    dest_resolved.mkdir(parents=True, exist_ok=True)
    
    target_path = dest_resolved / src_path.name
    if target_path.exists():
        print("\n⚠️ This action cannot be undone.\n")
        print(f"Overwrite:\n\n{target_path}\n")
        print("Type:")
        print("- Yes")
        print("- No")
        try:
            confirm = input().strip()
        except (KeyboardInterrupt, EOFError):
            return "Operation cancelled."
        if confirm != "Yes":
            return "Operation cancelled."
            
    shutil.move(str(src_path), str(target_path))
    return f"Moved file from '{src_path}' to '{target_path}'"

def copy_file(source: str, destination: str) -> str:
    """
    Copies a file to a destination folder.
    """
    src_resolved = resolve_file_path(source)
    if not src_resolved:
        return "Operation cancelled."
        
    src_path = Path(src_resolved)
    dest_resolved = _resolve_path(destination, is_create=True)
    dest_resolved.mkdir(parents=True, exist_ok=True)
    
    target_path = dest_resolved / src_path.name
    if target_path.exists():
        print("\n⚠️ This action cannot be undone.\n")
        print(f"Overwrite:\n\n{target_path}\n")
        print("Type:")
        print("- Yes")
        print("- No")
        try:
            confirm = input().strip()
        except (KeyboardInterrupt, EOFError):
            return "Operation cancelled."
        if confirm != "Yes":
            return "Operation cancelled."
            
    shutil.copy2(str(src_path), str(target_path))
    return f"Copied file from '{src_path}' to '{target_path}'"

def create_folder(folder_name: str) -> str:
    """
    Creates a new folder.
    """
    from tools.resolve_path import is_path
    
    import re
    cleaned_fn = folder_name.strip()
    prefix_pattern = re.compile(r'^(file|folder|document|directory|path)\s+', re.IGNORECASE)
    clean_name = prefix_pattern.sub('', cleaned_fn)
    
    if is_path(clean_name):
        path = Path(clean_name).resolve()
    else:
        path = ask_create_directory(clean_name, is_folder=True)
        if not path:
            return "Operation cancelled."
            
    if not _has_access(path):
        raise PermissionError(f"Access Denied: Path '{path}' is outside of authorized folders.")
        
    print(f"\nResolved file:\n\n{path}\n")
        
    if path.exists():
        if path.is_dir():
            return f"Folder already exists: {path}"
        else:
            return f"Failed to create folder: A file already exists at {path}"
            
    try:
        path.mkdir(parents=True, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Failed to create folder: {e}"

def delete_folder(folder_name: str) -> str:
    """
    Deletes an existing folder recursively. HIGH RISK.
    """
    resolved = resolve_file_path(folder_name)
    if not resolved:
        return "Operation cancelled."
        
    path = Path(resolved)
    print("\n⚠️ This action cannot be undone.\n")
    print(f"Delete:\n\n{path}\n")
    print("Type:")
    print("- Yes")
    print("- No")
    try:
        confirm = input().strip()
    except (KeyboardInterrupt, EOFError):
        return "Operation cancelled."
        
    if confirm != "Yes":
        return "Operation cancelled."
        
    if not path.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {path}")
        
    shutil.rmtree(str(path))
    return f"Deleted folder: {path}"

def rename_folder(source: str, destination: str) -> str:
    """
    Renames a folder in its parent folder.
    """
    src_resolved = resolve_file_path(source)
    if not src_resolved:
        return "Operation cancelled."
        
    src_path = Path(src_resolved)
    if not src_path.is_dir():
        raise NotADirectoryError(f"Source is not a directory: {src_path}")
        
    dest_path = src_path.parent / destination
    dest_resolved = dest_path.resolve()
    
    if not _has_access(dest_resolved):
        raise PermissionError(f"Access Denied: Rename target '{dest_resolved}' is outside of authorized folders.")
        
    if dest_resolved.exists():
        print("\n⚠️ This action cannot be undone.\n")
        print(f"Overwrite:\n\n{dest_resolved}\n")
        print("Type:")
        print("- Yes")
        print("- No")
        try:
            confirm = input().strip()
        except (KeyboardInterrupt, EOFError):
            return "Operation cancelled."
        if confirm != "Yes":
            return "Operation cancelled."
            
    src_path.rename(dest_resolved)
    return f"Renamed folder '{src_path.name}' to '{destination}' at {dest_resolved}"

def append_to_file(filename: str, text: str) -> str:
    """
    Appends text to the end of a file.
    """
    resolved = resolve_file_path(filename)
    if not resolved:
        return "Operation cancelled."
        
    path = Path(resolved)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + text)
        
    return f"Appended text to: {path}"

def read_file_content(filename: str) -> str:
    """
    Reads and returns the contents of a text file.
    """
    resolved = resolve_file_path(filename)
    if not resolved:
        return "Operation cancelled."
        
    path = Path(resolved)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    return content

# --- Advanced Search Handlers ---

def semantic_file_search(query: str) -> list[dict]:
    """
    Performs semantic search. For the offline POC database, queries the index by matching names.
    """
    return lookup_file_multi(query, str(config.DB_PATH))

def recent_files(hours: Optional[int] = 24) -> list[dict]:
    """
    Lists files modified within the last N hours.
    """
    from datetime import datetime, timedelta
    val_hours = hours if hours is not None else 24
    cutoff = (datetime.now() - timedelta(hours=val_hours)).isoformat()
    
    with sqlite3.connect(str(config.DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_name, absolute_path, have_access 
            FROM file_index 
            WHERE modified_time >= ? AND have_access = 1
        """, (cutoff,))
        return [dict(row) for row in cursor.fetchall()]

def files_by_extension(extension: str) -> list[dict]:
    """
    Lists files matching a specific extension (dot is optional).
    """
    ext = extension.lower().strip()
    if not ext.startswith("."):
        ext = f".{ext}"
        
    with sqlite3.connect(str(config.DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_name, absolute_path, have_access 
            FROM file_index 
            WHERE LOWER(extension) = ? AND have_access = 1
        """, (ext,))
        return [dict(row) for row in cursor.fetchall()]

def files_by_date(date_description: str) -> list[dict]:
    """
    Lists files modified around or after a natural language date description.
    """
    from datetime import datetime, timedelta
    clean_desc = date_description.lower().strip()
    now = datetime.now()
    
    if "today" in clean_desc:
        start_date = datetime(now.year, now.month, now.day)
    elif "yesterday" in clean_desc:
        yest = now - timedelta(days=1)
        start_date = datetime(yest.year, yest.month, yest.day)
    else:
        try:
            # Try parsing YYYY-MM-DD
            start_date = datetime.strptime(clean_desc, "%Y-%m-%d")
        except ValueError:
            # Fallback to last 7 days
            start_date = now - timedelta(days=7)
            
    start_str = start_date.isoformat()
    
    with sqlite3.connect(str(config.DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_name, absolute_path, have_access 
            FROM file_index 
            WHERE modified_time >= ? AND have_access = 1
        """, (start_str,))
        return [dict(row) for row in cursor.fetchall()]

