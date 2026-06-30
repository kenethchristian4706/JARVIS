"""
tools/file_tools.py

Implements handlers for local file and folder operations utilizing SQLite indexing:
move_file, copy_file, rename_file, delete_file, search_files, open_file,
create_folder, delete_folder, compress_files, extract_archive, list_directory, file_info.
"""

import os
import time
import shutil
import logging
import zipfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import send2trash
import pytesseract
from PIL import Image

from aether.tools.indexer import add_to_index, remove_from_index, get_db_connection, compute_relative_location

logger = logging.getLogger(__name__)

FALLBACK_SEARCH_TRIGGERED = False

def get_user_directories() -> list[Path]:
    """Returns a list of common user directories to search or resolve relative paths in."""
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    return [
        Path(user_profile) / "Desktop",
        Path(user_profile) / "Downloads",
        Path(user_profile) / "Documents",
        Path(user_profile) / "Pictures",
        Path(user_profile) / "Videos",
        Path(user_profile) / "Music",
        Path(os.getcwd())
    ]

def resolve_path(target_path: str) -> Path:
    """
    Resolves a string path.
    If it is absolute, returns it.
    If it is relative, checks if it exists in current directory or scans common user folders.
    If not found anywhere, returns path relative to current directory.
    """
    path = Path(target_path)
    if path.is_absolute():
        return path

    # Check if exists in CWD
    resolved = path.resolve()
    if resolved.exists():
        return resolved

    # Search in common user directories
    for parent_dir in get_user_directories():
        candidate = parent_dir / target_path
        if candidate.exists():
            return candidate.resolve()
            
    # Default fallback to CWD
    return resolved

def find_all_files_on_disk(name_or_path: str, is_directory: Optional[bool] = None) -> List[Path]:
    """Performs a full filesystem walk to find all matching files or folders across all logical drives."""
    p = Path(name_or_path)
    filename = p.name
    rel_parent = p.parent
    
    from aether.tools.indexer import get_indexed_paths, EXCLUDED_DIRS
    drives = get_indexed_paths()
    EXCLUDED_DIRS_LOWER = {d.lower() for d in EXCLUDED_DIRS}
    
    matches = []
    for d in drives:
        try:
            for root, dirs, files_list in os.walk(d):
                # Prune excluded directories case-insensitively and skip dot/dollar system dirs
                dirs[:] = [name for name in dirs if name.lower() not in EXCLUDED_DIRS_LOWER and not name.startswith(".") and not name.startswith("$")]
                
                # Check directories
                if is_directory is not False:
                    for folder_name in dirs:
                        if folder_name.lower() == filename.lower():
                            candidate = Path(root) / folder_name
                            resolved = candidate.resolve()
                            if len(rel_parent.parts) > 0:
                                if rel_parent.name.lower() in str(resolved.parent).lower():
                                    if resolved not in matches:
                                        matches.append(resolved)
                            else:
                                if resolved not in matches:
                                    matches.append(resolved)
                                
                # Check files
                if is_directory is not True:
                    for file_name in files_list:
                        if file_name.lower() == filename.lower():
                            candidate = Path(root) / file_name
                            resolved = candidate.resolve()
                            if len(rel_parent.parts) > 0:
                                if rel_parent.name.lower() in str(resolved.parent).lower():
                                    if resolved not in matches:
                                        matches.append(resolved)
                            else:
                                if resolved not in matches:
                                    matches.append(resolved)
        except Exception:
            pass
    return matches

def find_file_on_disk(name_or_path: str, is_directory: Optional[bool] = None) -> Optional[Path]:
    """Performs a full filesystem walk to find the first file or folder across all logical drives."""
    matches = find_all_files_on_disk(name_or_path, is_directory)
    return matches[0] if matches else None

def resolve_filename(name_or_path: str, is_directory: Optional[bool] = None) -> Path:
    """
    Queries the index database to locate files or directories matching a filename query.
    If not found in index, queries standard folders, and performs full filesystem fallback search.
    If multiple matches are found, prompts the user to select one.
    """
    p = Path(name_or_path)
    if p.is_absolute():
        return p

    filename = p.name
    rel_parent = p.parent
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ?"
    params = [filename]
    if is_directory is not None:
        query += " AND is_directory = ?"
        params.append(1 if is_directory else 0)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Filter by parent folder structures if the query specifies them
    if len(rel_parent.parts) > 0:
        filtered_rows = []
        for r in rows:
            rel_loc = r["relative_location"]
            if rel_loc and (rel_parent.name in rel_loc or Path(rel_loc).is_relative_to(rel_parent)):
                filtered_rows.append(r)
        if filtered_rows:
            rows = filtered_rows
            
    if not rows:
        # Fallback 1: Check standard folders in case index database is not fully built yet
        fallback_matches = []
        for d in get_user_directories():
            candidate = d / name_or_path
            if candidate.exists():
                if is_directory is True and not candidate.is_dir():
                    continue
                if is_directory is False and not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if resolved not in fallback_matches:
                    fallback_matches.append(resolved)
                    
        # Fallback 2: Perform full filesystem search (Requirement 8)
        if not fallback_matches:
            global FALLBACK_SEARCH_TRIGGERED
            FALLBACK_SEARCH_TRIGGERED = True
            logger.info(f"File '{name_or_path}' not found in index or standard directories. Initiating fallback full disk search...")
            fallback_matches = find_all_files_on_disk(name_or_path, is_directory)
            
        if not fallback_matches:
            raise FileNotFoundError(f"I couldn't find that file anywhere on this computer.")
            
        # Add found matches to index
        for match in fallback_matches:
            try:
                add_to_index(match)
            except Exception:
                pass
                
        if len(fallback_matches) == 1:
            return fallback_matches[0]
            
        # If multiple fallback matches found, convert to rows representation to prompt the user below
        rows = [{"absolute_path": str(m), "relative_location": compute_relative_location(m)} for m in fallback_matches]

    if len(rows) == 1:
        return Path(rows[0]["absolute_path"])
        
    # Ambiguity Resolution: ask user to choose
    from aether.api.prompt import prompt_user_sync
    title = f"Multiple entries found for '{name_or_path}'. Which one would you like to use?"
    options = []
    for r in rows:
        loc = r["relative_location"]
        suffix = f" ({loc})" if loc else ""
        options.append(f"{r['absolute_path']}{suffix}")
    options.append("Cancel")
    
    choice = prompt_user_sync(title, options)
    
    if not choice or choice.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
        raise ValueError("Ambiguity Resolution Cancelled.")
        
    try:
        # Check if selection is an index number (e.g. console input "1")
        choice_idx = int(choice) - 1
    except ValueError:
        # Check if selection matches one of the option strings (e.g. frontend click)
        choice_idx = -1
        for idx_opt, opt in enumerate(options[:-1]):  # Exclude "Cancel" option
            if choice.lower() in opt.lower():
                choice_idx = idx_opt
                break
                
    if 0 <= choice_idx < len(rows):
        return Path(rows[choice_idx]["absolute_path"])
    else:
        raise ValueError("Invalid selection or operation cancelled.")

def move_file(source: str, destination: Optional[str] = None) -> str:
    """Moves a file or folder from source path to destination folder or path."""
    src = resolve_filename(source)
    if not src.exists():
        raise FileNotFoundError(f"Source path '{source}' not found (resolved: '{src}').")
        
    if not destination:
        print(f"\nWhere would you like me to move '{src.name}'?")
        print("Examples:\n* Documents\n* Downloads\n* Desktop\n* Custom path")
        destination = input("Enter destination: ").strip()
        if not destination:
                    raise ValueError("Destination is required to move a file.")
            
    dst = resolve_path(destination)
    if dst.is_dir():
        dst_final = dst / src.name
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst_final = dst

    shutil.move(str(src), str(dst_final))
    
    # Update index immediately
    remove_from_index(src)
    add_to_index(dst_final)
    return f"Successfully moved '{src.name}' from '{src}' to '{dst_final}'"

def copy_file(source: str, destination: Optional[str] = None) -> str:
    """Copies a file from source path to destination folder or path."""
    src = resolve_filename(source)
    if not src.exists():
        raise FileNotFoundError(f"Source file '{source}' not found (resolved: '{src}').")
        
    if src.is_dir():
        raise IsADirectoryError("Copy file tool only supports files.")

    if not destination:
        print(f"\nWhere would you like me to copy '{src.name}'?")
        print("Examples:\n* Documents\n* Downloads\n* Desktop\n* Custom path")
        destination = input("Enter destination: ").strip()
        if not destination:
            raise ValueError("Destination is required to copy a file.")
            
    dst = resolve_path(destination)
    if dst.is_dir():
        dst_final = dst / src.name
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst_final = dst

    shutil.copy2(str(src), str(dst_final))
    
    # Update index immediately
    add_to_index(dst_final)
    return f"Successfully copied '{src.name}' to '{dst_final}'"

def rename_file(source: str, new_name: str) -> str:
    """Renames a file or folder at a given path to a new filename."""
    target = resolve_filename(source)
    if not target.exists():
        raise FileNotFoundError(f"Target '{source}' not found (resolved: '{target}').")
        
    if "/" in new_name or "\\" in new_name:
        raise ValueError("new_name parameter must be a filename, not a full path. Use move_file for moving.")
        
    # Preserve original extension if new_name has no suffix and target is a file with a suffix
    if target.is_file() and target.suffix and not Path(new_name).suffix:
        new_name = new_name + target.suffix

    dest = target.parent / new_name
    target.rename(dest)
    
    # Update index immediately
    remove_from_index(target)
    add_to_index(dest)
    return f"Successfully renamed '{target.name}' to '{new_name}' (path: '{dest}')"

def delete_file(filename: str) -> str:
    """Deletes a file (moves it to the Recycle Bin using send2trash)."""
    target = resolve_filename(filename, is_directory=False)
    if not target.exists():
        raise FileNotFoundError(f"File '{filename}' not found (resolved: '{target}').")
        
    send2trash.send2trash(str(target))
    
    # Update index immediately
    remove_from_index(target)
    return f"Successfully deleted '{target.name}' (moved to Recycle Bin)."

def search_files(query: str) -> str:
    """Searches SQLite index database for files matching the query substring."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT absolute_path
        FROM indexed_files
        WHERE filename LIKE ? OR relative_location LIKE ?
        LIMIT 15
    """, (f"%{query}%", f"%{query}%"))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        lines = []
        for r in rows:
            lines.append(f"- {r['absolute_path']}")
        return "Found matching files:\n" + "\n".join(lines)
    else:
        return f"No files found matching query '{query}'."

def open_file(filename: str) -> str:
    """Opens a file using its default registered OS application."""
    target = resolve_filename(filename, is_directory=False)
    if not target.exists():
        raise FileNotFoundError(f"File '{filename}' not found (resolved: '{target}').")
        
    os.startfile(str(target))
    return f"Successfully opened file '{target.name}' in its default viewer."

def create_folder(folder_name: str, location: Optional[str] = None) -> str:
    """Creates a new folder/directory recursively after checking duplicate names."""
    if location and location.startswith("_ALREADY_OPENED_:"):
        dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
        return f"Successfully opened existing folder at '{dest_path}' (Deferred creation)."

    create_another = False
    if location and "?create_another=true" in location:
        location = location.replace("?create_another=true", "")
        create_another = True

    if not location:
        location = os.getcwd()
    target_dir = resolve_path(location)
    target = target_dir / folder_name
    
    if not create_another:
        # Duplicate detection check using SQLite index (Requirement 5)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ?", (folder_name,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            from aether.api.prompt import prompt_user_sync
            title = f"A folder or file named '{folder_name}' already exists. What would you like to do?"
            options = ["Choose Existing", "Open Existing", "Create Another", "Cancel"]
            choice = prompt_user_sync(title, options)
            
            try:
                choice_int = int(choice)
            except ValueError:
                choice_int = -1
                for idx_opt, opt in enumerate(options, 1):
                    if choice.lower() in opt.lower():
                        choice_int = idx_opt
                        break
            
            if choice_int == 1 or (isinstance(choice, str) and "choose" in choice.lower()):
                options_sub = []
                for r in rows:
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    options_sub.append(f"{r['absolute_path']}{suffix}")
                choice_sub = prompt_user_sync("Select which existing folder to use:", options_sub)
                try:
                    choice_idx = int(choice_sub) - 1
                except ValueError:
                    choice_idx = -1
                    for idx_opt, opt in enumerate(options_sub, 1):
                        if choice_sub.lower() in opt.lower():
                            choice_idx = idx_opt - 1
                            break
                if 0 <= choice_idx < len(rows):
                    dest = Path(rows[choice_idx]["absolute_path"])
                    return f"Successfully selected existing folder at '{dest}' for further tasks."
                else:
                    raise ValueError("Operation cancelled by user.")
                    
            elif choice_int == 2 or (isinstance(choice, str) and "open" in choice.lower()):
                options_sub = []
                for r in rows:
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    options_sub.append(f"{r['absolute_path']}{suffix}")
                choice_sub = prompt_user_sync("Select which existing folder to open:", options_sub)
                try:
                    choice_idx = int(choice_sub) - 1
                except ValueError:
                    choice_idx = -1
                    for idx_opt, opt in enumerate(options_sub, 1):
                        if choice_sub.lower() in opt.lower():
                            choice_idx = idx_opt - 1
                            break
                if 0 <= choice_idx < len(rows):
                    dest = Path(rows[choice_idx]["absolute_path"])
                    os.startfile(str(dest))
                    return f"Successfully opened existing folder at '{dest}' (Deferred creation)."
                else:
                    raise ValueError("Operation cancelled by user.")
                    
            elif choice_int == 3 or (isinstance(choice, str) and "create another" in choice.lower()):
                pass
            else:
                raise ValueError("Operation cancelled by user.")

    if target.exists():
        if target.is_dir():
            return f"Folder '{target}' already exists."
        else:
            raise FileExistsError(f"A file already exists at '{target}'.")
            
    target.mkdir(parents=True, exist_ok=True)
    add_to_index(target)
    return f"Successfully created folder at '{target}'"

def create_file(filename: str, location: Optional[str] = None) -> str:
    """Creates a new file after checking duplicate names."""
    if location and location.startswith("_ALREADY_OPENED_:"):
        dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
        return f"Successfully opened existing file at '{dest_path}' (Deferred creation)."

    create_another = False
    if location and "?create_another=true" in location:
        location = location.replace("?create_another=true", "")
        create_another = True

    if not location:
        location = os.getcwd()
    target_dir = resolve_path(location)
    target = target_dir / filename
    
    if not create_another:
        # Duplicate detection check using SQLite index (Requirement 5)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ?", (filename,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            from aether.api.prompt import prompt_user_sync
            title = f"A file or folder named '{filename}' already exists. What would you like to do?"
            options = ["Choose Existing", "Open Existing", "Create Another", "Cancel"]
            choice = prompt_user_sync(title, options)
            
            try:
                choice_int = int(choice)
            except ValueError:
                choice_int = -1
                for idx_opt, opt in enumerate(options, 1):
                    if choice.lower() in opt.lower():
                        choice_int = idx_opt
                        break
            
            if choice_int == 1 or (isinstance(choice, str) and "choose" in choice.lower()):
                options_sub = []
                for r in rows:
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    options_sub.append(f"{r['absolute_path']}{suffix}")
                choice_sub = prompt_user_sync("Select which existing file to use:", options_sub)
                try:
                    choice_idx = int(choice_sub) - 1
                except ValueError:
                    choice_idx = -1
                    for idx_opt, opt in enumerate(options_sub, 1):
                        if choice_sub.lower() in opt.lower():
                            choice_idx = idx_opt - 1
                            break
                if 0 <= choice_idx < len(rows):
                    dest = Path(rows[choice_idx]["absolute_path"])
                    return f"Successfully selected existing file at '{dest}' for further tasks."
                else:
                    raise ValueError("Operation cancelled by user.")
                    
            elif choice_int == 2 or (isinstance(choice, str) and "open" in choice.lower()):
                options_sub = []
                for r in rows:
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    options_sub.append(f"{r['absolute_path']}{suffix}")
                choice_sub = prompt_user_sync("Select which existing file to open:", options_sub)
                try:
                    choice_idx = int(choice_sub) - 1
                except ValueError:
                    choice_idx = -1
                    for idx_opt, opt in enumerate(options_sub, 1):
                        if choice_sub.lower() in opt.lower():
                            choice_idx = idx_opt - 1
                            break
                if 0 <= choice_idx < len(rows):
                    dest = Path(rows[choice_idx]["absolute_path"])
                    os.startfile(str(dest))
                    return f"Successfully opened existing file at '{dest}' (Deferred creation)."
                else:
                    raise ValueError("Operation cancelled by user.")
                    
            elif choice_int == 3 or (isinstance(choice, str) and "create another" in choice.lower()):
                pass
            else:
                raise ValueError("Operation cancelled by user.")

    if target.exists():
        if target.is_file():
            return f"File '{target}' already exists."
        else:
            raise FileExistsError(f"A directory already exists at '{target}'.")
            
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
    add_to_index(target)
    return f"Successfully created file at '{target}'"

def delete_folder(folder_name: str) -> str:
    """Deletes a folder recursively (moves it to the Recycle Bin using send2trash)."""
    target = resolve_filename(folder_name, is_directory=True)
    if not target.exists():
        raise FileNotFoundError(f"Folder '{folder_name}' not found (resolved: '{target}').")
        
    send2trash.send2trash(str(target))
    
    # Update index immediately
    remove_from_index(target)
    return f"Successfully deleted folder '{target.name}' and its contents (moved to Recycle Bin)."

def compress_files(sources: List[str], output: str) -> str:
    """Compresses a list of files/folders into a zip archive."""
    out_archive = resolve_path(output)
    if not out_archive.name.lower().endswith(".zip"):
        out_archive = out_archive.with_suffix(".zip")
        
    out_archive.parent.mkdir(parents=True, exist_ok=True)
    
    resolved_sources = []
    for p_str in sources:
        try:
            p = resolve_filename(p_str)
            if p.exists():
                resolved_sources.append(p)
        except Exception as e:
            logger.warning(f"File/folder '{p_str}' skipped for compression: {e}")
            
    if not resolved_sources:
        raise FileNotFoundError("None of the sources to compress were found.")

    with zipfile.ZipFile(out_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for p in resolved_sources:
            if p.is_file():
                zipf.write(p, p.name)
            elif p.is_dir():
                for root, _, files in os.walk(p):
                    for file in files:
                        file_path = Path(root) / file
                        archive_name = file_path.relative_to(p.parent)
                        zipf.write(file_path, archive_name)
                        
    # Update index immediately
    add_to_index(out_archive)
    return f"Successfully compressed files into '{out_archive}'"

def extract_archive(archive: str, destination: Optional[str] = None) -> str:
    """Extracts a zip archive to the destination directory."""
    arc_path = resolve_filename(archive)
    if not arc_path.exists():
        raise FileNotFoundError(f"Archive file '{archive}' not found (resolved: '{arc_path}').")
        
    if not destination:
        print(f"\nWhere would you like me to extract '{arc_path.name}'?")
        print("Examples:\n* Documents\n* Downloads\n* Desktop\n* Custom path")
        destination = input("Enter destination: ").strip()
        if not destination:
            raise ValueError("Destination is required to extract an archive.")
            
    dst = resolve_path(destination)
    dst.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(arc_path, 'r') as zipf:
        zipf.extractall(dst)
        
    # Update index immediately
    add_to_index(dst)
    return f"Successfully extracted archive '{arc_path.name}' into '{dst}'"

def list_directory(path: Optional[str] = None) -> str:
    """List the files and directories inside a specified path (falls back to CWD if not specified)."""
    if not path:
        print("\nSpecify the directory path to list (or press Enter to list current working directory):")
        path = input("Enter path: ").strip()
        if not path:
            path = os.getcwd()
            
    target = resolve_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Directory '{path}' not found (resolved: '{target}').")
    if not target.is_dir():
        raise NotADirectoryError(f"Path '{path}' is not a directory.")
        
    items = list(target.iterdir())
    if not items:
        return f"Directory '{target}' is empty."
        
    lines = [f"Contents of '{target}':"]
    for item in items:
        prefix = "[DIR] " if item.is_dir() else "[FILE]"
        lines.append(f"  {prefix} {item.name}")
    return "\n".join(lines)

def file_info(filename: str) -> str:
    """Gets metadata for a specific file matching name query (size, extension, modified date)."""
    target = resolve_filename(filename, is_directory=False)
    if not target.exists():
        raise FileNotFoundError(f"File '{filename}' not found (resolved: '{target}').")
        
    stat = target.stat()
    size_bytes = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    ext = target.suffix
    
    if size_bytes < 1024:
        size_str = f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.2f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
        
    return (
        f"File Metadata for '{target.name}':\n"
        f"  Absolute Path : {target}\n"
        f"  Size          : {size_str}\n"
        f"  Extension     : {ext}\n"
        f"  Modified Date : {mtime}"
    )

def append_file(filename: str, content: str) -> str:
    """Appends content to a file. Resolves filename first."""
    target = resolve_filename(filename, is_directory=False)
    if not target.exists():
        raise FileNotFoundError(f"File '{filename}' not found (resolved: '{target}').")
    
    with open(target, "a", encoding="utf-8") as f:
        f.write("\n" + content)
    
    # Update index immediately
    add_to_index(target)
    return f"Successfully appended content to '{target.name}'"


# Try to configure pytesseract Windows binary path if not in standard PATH
TESSERACT_CMD_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
]
for candidate in TESSERACT_CMD_CANDIDATES:
    if os.path.exists(candidate):
        pytesseract.pytesseract.tesseract_cmd = candidate
        break

def extract_text_from_image(image_path: str) -> dict:
    """
    Extract text from an image using OCR (pytesseract).
    Validates image existence and format, removes excessive whitespace, and returns text.
    """
    try:
        logger.info(f"Starting extract_text_from_image for path: {image_path}")
        p = resolve_filename(image_path, is_directory=False)
        if not p.exists():
            logger.error(f"Image file not found: {image_path} (resolved: '{p}')")
            return {
                "success": False,
                "message": f"Image file not found at '{image_path}' (resolved: '{p}')."
            }
        if not p.is_file():
            logger.error(f"Path is not a file: {image_path} (resolved: '{p}')")
            return {
                "success": False,
                "message": f"Path '{image_path}' is not a file (resolved: '{p}')."
            }

        # Verify image format using Pillow
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as img_err:
            logger.error(f"Unsupported or corrupt image file: {img_err}")
            return {
                "success": False,
                "message": f"Unsupported or corrupt image format: {str(img_err)}"
            }

        # Perform OCR
        # We need to re-open because verify() closes the file pointer or makes it un-readable
        with Image.open(p) as img:
            extracted_text = pytesseract.image_to_string(img)

        # Remove excessive whitespace
        cleaned_text = " ".join(extracted_text.split()).strip()
        
        logger.info("OCR text extraction completed successfully.")
        return {
            "success": True,
            "message": "Text extracted successfully.",
            "data": {
                "text": cleaned_text
            }
        }
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract OCR binary not found.")
        return {
            "success": False,
            "message": "Tesseract OCR engine is not installed or not found in system path. Please install Tesseract-OCR."
        }
    except FileNotFoundError as e:
        logger.error(f"Image file not found: {image_path} (error: {e})")
        return {
            "success": False,
            "message": f"Image file not found at '{image_path}'."
        }
    except Exception as e:
        logger.error(f"OCR extraction failed with exception: {e}")
        return {
            "success": False,
            "message": f"OCR extraction failed: {str(e)}"
        }

def read_file_content(file_path: str) -> dict:
    """
    Read text content from supported files (.txt, .md, .py, .json, .csv, .log).
    Safely detects encoding and limits output to the first 10,000 characters.
    """
    supported_extensions = {".txt", ".md", ".py", ".json", ".csv", ".log"}
    try:
        logger.info(f"Starting read_file_content for path: {file_path}")
        p = resolve_filename(file_path, is_directory=False)
        if p.suffix.lower() not in supported_extensions:
            logger.error(f"Unsupported file format requested: {p.suffix}")
            return {
                "success": False,
                "message": f"Unsupported file format '{p.suffix}'. Supported formats: {', '.join(supported_extensions)}"
            }

        if not p.exists():
            logger.error(f"File not found: {file_path} (resolved: '{p}')")
            return {
                "success": False,
                "message": f"File not found at '{file_path}' (resolved: '{p}')."
            }
        if not p.is_file():
            logger.error(f"Path is not a file: {file_path} (resolved: '{p}')")
            return {
                "success": False,
                "message": f"Path '{file_path}' is not a file (resolved: '{p}')."
            }

        size_bytes = p.stat().st_size

        # Safe encoding detection and reading
        content = ""
        detected_encoding = None
        encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "utf-16"]
        
        for enc in encodings_to_try:
            try:
                with open(p, "r", encoding=enc) as f:
                    # Read slightly more than 10,000 to know context
                    content = f.read(10005)
                detected_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if detected_encoding is None:
            logger.error(f"Failed to decode file {file_path} with standard encodings.")
            return {
                "success": False,
                "message": "Failed to decode file with standard encodings."
            }

        logger.info(f"File successfully read using encoding: {detected_encoding}")
        return {
            "success": True,
            "message": "File read successfully.",
            "data": {
                "content": content[:10000],
                "size_bytes": size_bytes,
                "encoding": detected_encoding
            }
        }
    except PermissionError:
        logger.error(f"Permission denied accessing path: {file_path}")
        return {
            "success": False,
            "message": f"Permission denied accessing '{file_path}'."
        }
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path} (error: {e})")
        return {
            "success": False,
            "message": f"File not found at '{file_path}'."
        }
    except Exception as e:
        logger.error(f"Error reading file content: {e}")
        return {
            "success": False,
            "message": f"Failed to read file: {str(e)}"
        }


def write_file(path: str, content: str, encoding: str = "utf-8", create_parent: bool = False) -> dict:
    """
    Create a new text file or completely overwrite an existing text file.
    Does not append text. Supports only text extensions.
    """
    start_time = time.time()
    logger.info(f"Starting write_file for path='{path}', encoding='{encoding}', create_parent={create_parent}")
    
    # 1. Supported Text Extensions Validation
    supported_extensions = {
        ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml", ".ini", ".log",
        ".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h", ".sql",
        ".sh", ".bat", ".ps1"
    }
    
    try:
        resolved_path = resolve_path(path)
        suffix = resolved_path.suffix.lower()
        
        if suffix not in supported_extensions:
            logger.error(f"write_file failed: Unsupported file extension '{suffix}'.")
            return {
                "success": False,
                "message": f"Unsupported extension '{suffix}'. Only text files are supported."
            }
            
        # 2. Check Parent Folder Existence
        parent = resolved_path.parent
        if not parent.exists():
            if create_parent:
                parent.mkdir(parents=True, exist_ok=True)
            else:
                logger.error(f"write_file failed: Parent directory '{parent}' does not exist.")
                return {
                    "success": False,
                    "message": f"Parent directory '{parent}' does not exist and create_parent is set to False."
                }
                
        # 3. Check Overwritten status
        overwritten = resolved_path.exists()
        
        # 4. Perform Write
        # Check encoding by trying to encode the content first
        encoded_content = content.encode(encoding)
        bytes_written = len(encoded_content)
        
        with open(resolved_path, "w", encoding=encoding) as f:
            f.write(content)
            
        add_to_index(resolved_path)
        
        duration = time.time() - start_time
        logger.info(f"write_file completed in {duration:.4f}s. Bytes written: {bytes_written}, overwritten: {overwritten}")
        
        return {
            "success": True,
            "message": f"File successfully written to '{resolved_path}'",
            "data": {
                "path": str(resolved_path),
                "bytes_written": bytes_written,
                "encoding": encoding,
                "overwritten": overwritten,
                "success": True
            }
        }
        
    except LookupError:
        logger.error(f"write_file failed: Invalid or unsupported encoding: '{encoding}'")
        return {
            "success": False,
            "message": f"Invalid or unsupported encoding: '{encoding}'."
        }
    except PermissionError:
        logger.error(f"write_file failed: Permission denied accessing '{path}'")
        return {
            "success": False,
            "message": f"Permission denied: you don't have access to write to '{path}'."
        }
    except Exception as e:
        logger.error(f"write_file failed with exception: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to write file '{path}': {str(e)}"
        }


def duplicate_file(source: str, destination: Optional[str] = None, overwrite: bool = False) -> dict:
    """
    Create a duplicate copy of an existing file.
    Preserves metadata using shutil.copy2().
    """
    start_time = time.time()
    logger.info(f"Starting duplicate_file: source='{source}', destination='{destination}', overwrite={overwrite}")
    
    try:
        # 1. Resolve source
        src = resolve_filename(source, is_directory=False)
        if not src.exists():
            logger.error(f"duplicate_file failed: Source '{source}' not found.")
            return {
                "success": False,
                "message": f"Source file '{source}' not found."
            }
        if not src.is_file():
            logger.error(f"duplicate_file failed: Source '{source}' is not a file.")
            return {
                "success": False,
                "message": f"Source path '{source}' is not a file."
            }
            
        # 2. Determine destination
        if not destination:
            # Auto-generate copy filename
            parent = src.parent
            stem = src.stem
            suffix = src.suffix
            
            candidate_name = f"{stem} - Copy{suffix}"
            dst = parent / candidate_name
            counter = 2
            while dst.exists():
                candidate_name = f"{stem} - Copy ({counter}){suffix}"
                dst = parent / candidate_name
                counter += 1
            generated_filename = dst.name
        else:
            dst = resolve_path(destination)
            if dst.is_dir():
                dst = dst / src.name
            generated_filename = None
            
        # 3. Overwrite check
        if dst.exists():
            if not overwrite:
                logger.error(f"duplicate_file failed: Destination '{dst}' already exists and overwrite is False.")
                return {
                    "success": False,
                    "message": f"Destination file '{dst}' already exists and overwrite is set to False."
                }
                
        # Ensure destination parent folder exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # 4. Perform duplicate
        shutil.copy2(str(src), str(dst))
        add_to_index(dst)
        
        size = dst.stat().st_size
        duration = time.time() - start_time
        logger.info(f"duplicate_file completed in {duration:.4f}s. Source: '{src}', Destination: '{dst}'")
        
        return {
            "success": True,
            "message": f"Successfully duplicated '{src.name}' to '{dst}'",
            "data": {
                "source": str(src),
                "destination": str(dst),
                "size": size,
                "success": True
            }
        }
        
    except PermissionError:
        logger.error(f"duplicate_file failed: Permission denied.")
        return {
            "success": False,
            "message": "Permission denied accessing source or destination path."
        }
    except Exception as e:
        logger.error(f"duplicate_file failed with exception: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to duplicate file: {str(e)}"
        }


