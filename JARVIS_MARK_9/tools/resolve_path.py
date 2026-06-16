"""
tools/resolve_path.py

Provides middleware for resolving and validating file/folder paths across all
Aether file tools using File Resolution Logic v2. Supports CWD, custom paths,
Downloads, and entire-system stack-walk searches.
"""

import os
import re
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List

import config

logger = logging.getLogger(__name__)

def get_all_drives() -> List[str]:
    """
    Returns all logical drive roots on Windows, e.g. ['C:\\', 'D:\\'].
    """
    import string
    import ctypes
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    drives = []
    for letter in string.ascii_uppercase:
        if bitmask & (1 << (ord(letter) - 65)):
            drive_path = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            if drive_type in (2, 3, 4):  # Removable, Fixed, Remote
                drives.append(drive_path)
    if not drives:
        drives = ["C:\\"]
    return drives

def is_path(value: str) -> bool:
    """
    Determine whether the value is a file path.
    """
    return (
        os.path.isabs(value)
        or "\\" in value
        or "/" in value
        or value.startswith(".")
        or value.startswith("~")
    )

def search_directory_for_file(search_dir: str, filename: str) -> List[Path]:
    """
    Recursively scans the directory for files or folders matching name.
    """
    matches = []
    try:
        for p in Path(search_dir).rglob("*"):
            if p.name.lower() == filename.lower():
                matches.append(p.resolve())
    except Exception as e:
        logger.error(f"Error scanning directory {search_dir}: {e}")
    return matches

def search_entire_system(filename: str) -> List[Path]:
    """
    Searches all logical drives for matching files/folders, skipping standard ignore dirs.
    """
    from indexing.file_indexer import SYSTEM_IGNORE_DIRS
    drives = get_all_drives()
    matches = []
    for drive in drives:
        stack = [Path(drive)]
        while stack:
            current_dir = stack.pop()
            try:
                for child in current_dir.iterdir():
                    name_lower = child.name.lower()
                    if child.name.startswith(".") or name_lower in SYSTEM_IGNORE_DIRS:
                        continue
                    if child.is_dir():
                        stack.append(child)
                    elif child.is_file():
                        if name_lower == filename.lower():
                            matches.append(child.resolve())
            except (PermissionError, FileNotFoundError):
                continue
    return matches

def ask_search_directory_v2(filename: str) -> List[Path]:
    """
    Prompts the user for a search location, performs the search, and returns matches.
    """
    print(f"\nI couldn't find \"{filename}\" in the file index.\n")
    print("Would you like me to search:\n")
    print("1. Current directory")
    print("2. Custom folder path")
    print("3. Downloads folder")
    print("4. Entire system (may take longer)")
    print("5. Cancel")
    
    try:
        choice = input("\nChoice: ").strip()
    except (KeyboardInterrupt, EOFError):
        return []
        
    if choice == "1":
        cwd = os.getcwd()
        print(f"Searching directory: {cwd}...")
        return search_directory_for_file(cwd, filename)
    elif choice == "2":
        try:
            custom_path = input("Please provide the folder path: ").strip()
            path_obj = Path(custom_path).resolve()
            if path_obj.exists() and path_obj.is_dir():
                print(f"Searching directory: {path_obj}...")
                return search_directory_for_file(str(path_obj), filename)
            else:
                print(f"Folder '{custom_path}' does not exist or is not a directory.")
                return []
        except Exception as e:
            logger.error(f"Error checking custom path: {e}")
            return []
    elif choice == "3":
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
        downloads = str((Path(user_profile) / "Downloads").resolve())
        print(f"Searching directory: {downloads}...")
        return search_directory_for_file(downloads, filename)
    elif choice == "4":
        print("Searching entire system...")
        return search_entire_system(filename)
    else:
        return []

def confirm_single_match(path: str) -> Optional[str]:
    """
    Asks the user to confirm a single matched file path.
    """
    print(f"\nI found this file:\n\n{path}\n")
    print("Is this the correct file?\n")
    print("1. Yes")
    print("2. Search elsewhere")
    print("3. Cancel")
    
    try:
        choice = input("\nChoice: ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
        
    if choice in ["1", "yes", "y", "Yes"]:
        return path
    elif choice in ["2", "Search elsewhere", "search"]:
        return "search_elsewhere"
    else:
        return None

def resolve_multiple_matches(filename: str, candidates: List[Path]) -> Optional[str]:
    """
    Handles prompting the user to select among multiple candidate paths.
    """
    while True:
        print(f"\nI found multiple files named \"{filename}\":\n")
        for idx, cand in enumerate(candidates, start=1):
            print(f"{idx}. {cand}")
            
        print("\nSelect a file:\n")
        print("- Enter the number")
        print("- Enter the full path")
        print("- Type \"Search\" to search elsewhere")
        print("- Type \"Cancel\"")
        
        try:
            choice = input("\nChoice: ").strip()
        except (KeyboardInterrupt, EOFError):
            return None
            
        if choice.lower() in ["cancel", "c"]:
            return None
            
        if choice.lower() in ["search", "s"]:
            return "search_elsewhere"
            
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                return str(candidates[idx - 1])
                
        # Check if they entered a full path matching one of the candidates
        for cand in candidates:
            if str(cand).lower() == choice.lower() or Path(choice).resolve() == cand:
                return str(cand)
                
        print("\nInvalid selection. Please try again.")

def repair_windows_path(filename: str) -> str:
    """
    Repairs missing colons and double-slashes in Windows drive letter paths.
    e.g., "c\\\\users\\..." -> "c:\\users\\..."
          "c\\users\\..."   -> "c:\\users\\..."
          "c/users/..."     -> "c:/users/..."
    """
    import re
    # Clean multiple consecutive backslashes/slashes right after the drive letter
    # e.g., c\\\\users -> c\users
    cleaned = re.sub(r'^([a-zA-Z])([/\\s]+)', r'\1\\', filename)
    # Match drive letter followed by slashes
    match = re.match(r'^([a-zA-Z])([/\\].*)', cleaned)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    return filename

def resolve_file_path(
    filename: str,
    user_provided_path: Optional[str] = None
) -> Optional[str]:
    """
    Resolves the correct file path before executing an operation using File Resolution Logic v2.

    Returns:
        Resolved absolute path or None if cancelled.
    """
    filename = repair_windows_path(filename)
    if user_provided_path:
        user_provided_path = repair_windows_path(user_provided_path)
        
    path_to_check = user_provided_path or filename
    
    # 1. Check if User Provided a Full Path
    if user_provided_path or is_path(filename):
        resolved_path = str(Path(path_to_check).resolve())
        if os.path.exists(resolved_path):
            print(f"\nResolved file:\n\n{resolved_path}\n")
            return resolved_path
        else:
            print(f"\nThe specified path does not exist:\n\n{resolved_path}\n")
            print("Would you like to:")
            print("1. Provide another path")
            print("2. Search by filename instead")
            print("3. Cancel")
            
            try:
                choice = input("\nChoice: ").strip()
            except (KeyboardInterrupt, EOFError):
                return None
                
            if choice == "1":
                try:
                    new_path = input("\nPlease enter the file path: ").strip()
                    return resolve_file_path(new_path)
                except (KeyboardInterrupt, EOFError):
                    return None
            elif choice == "2":
                filename_only = Path(resolved_path).name
                return resolve_file_path(filename_only)
            else:
                return None

    # 2. If Only Filename Is Given
    cleaned_fn = filename.strip()
    prefix_pattern = re.compile(r'^(file|folder|document|directory|path)\s+', re.IGNORECASE)
    clean_name = prefix_pattern.sub('', cleaned_fn)
    base_name = Path(clean_name).name.lower()
    
    candidates = []
    try:
        with sqlite3.connect(str(config.DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT absolute_path FROM file_index WHERE LOWER(file_name) = ? AND have_access = 1",
                (base_name,)
            )
            candidates = [Path(row[0]).resolve() for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error querying file index: {e}")
        
    resolved = None
    
    # If no matches in SQLite File Index
    if not candidates:
        dir_matches = ask_search_directory_v2(clean_name)
        if not dir_matches:
            print(f"\nFile \"{clean_name}\" was not found.\n\nOperation cancelled.")
            return None
        candidates = dir_matches
        
    # If exactly one match found
    if len(candidates) == 1:
        ans = confirm_single_match(str(candidates[0]))
        if ans == "search_elsewhere":
            dir_matches = ask_search_directory_v2(clean_name)
            if not dir_matches:
                print(f"\nFile \"{clean_name}\" was not found.\n\nOperation cancelled.")
                return None
            candidates = dir_matches
            if len(candidates) == 1:
                ans2 = confirm_single_match(str(candidates[0]))
                if ans2 == "search_elsewhere" or ans2 is None:
                    print(f"\nFile \"{clean_name}\" was not found.\n\nOperation cancelled.")
                    return None
                resolved = ans2
            else:
                resolved = resolve_multiple_matches(clean_name, candidates)
        else:
            resolved = ans
            
    # If multiple matches found
    elif len(candidates) > 1:
        ans = resolve_multiple_matches(clean_name, candidates)
        if ans == "search_elsewhere":
            dir_matches = ask_search_directory_v2(clean_name)
            if not dir_matches:
                print(f"\nFile \"{clean_name}\" was not found.\n\nOperation cancelled.")
                return None
            candidates = dir_matches
            if len(candidates) == 1:
                ans2 = confirm_single_match(str(candidates[0]))
                if ans2 == "search_elsewhere" or ans2 is None:
                    print(f"\nFile \"{clean_name}\" was not found.\n\nOperation cancelled.")
                    return None
                resolved = ans2
            else:
                resolved = resolve_multiple_matches(clean_name, candidates)
        else:
            resolved = ans
            
    if resolved:
        print(f"\nResolved file:\n\n{resolved}\n")
        return resolved
        
    return None
