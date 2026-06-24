"""
tools/file_tools.py

Implements handlers for local file and folder operations utilizing SQLite indexing:
move_file, copy_file, rename_file, delete_file, search_files, open_file,
create_folder, delete_folder, compress_files, extract_archive, list_directory, file_info.
"""

import os
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
    print(f"\nFound multiple matching entries for '{name_or_path}':")
    for idx, row in enumerate(rows, 1):
        loc = row["relative_location"]
        suffix = f" ({loc})" if loc else ""
        print(f"  {idx}. {row['absolute_path']}{suffix}")
        
    try:
        choice = input(f"Please select a number (1-{len(rows)}) or type 'cancel': ").strip()
        if choice.lower() == 'cancel':
            raise ValueError("Operation cancelled by user.")
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(rows):
            return Path(rows[choice_idx]["absolute_path"])
        else:
            raise ValueError(f"Invalid selection: {choice}")
    except (KeyboardInterrupt, EOFError, ValueError) as e:
        logger.warning(f"Ambiguity resolution aborted or invalid: {e}")
        raise ValueError(f"Ambiguity Resolution Failed: {e}")

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

def create_folder(folder_name: str, location: Optional[str] = None) -> dict:
    """Creates a new folder/directory recursively after checking duplicate names."""
    if location and location.startswith("_ALREADY_OPENED_:"):
        dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
        return {
            "success": True,
            "message": f"Successfully opened existing folder at '{dest_path}' (Deferred creation).",
            "path": str(dest_path)
        }

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
            print(f"\nA folder or file named '{folder_name}' already exists:")
            for idx, r in enumerate(rows, 1):
                loc = r["relative_location"]
                suffix = f" ({loc})" if loc else ""
                print(f"  {idx}. {r['absolute_path']}{suffix}")
            print("\nWhat would you like to do?")
            print("  1. Open Existing")
            print("  2. Create Another")
            print("  3. Cancel")
            
            while True:
                choice = input("Enter selection (1-3): ").strip()
                if choice == '1':
                    # Open existing
                    if len(rows) == 1:
                        dest = Path(rows[0]["absolute_path"])
                    else:
                        dest = resolve_filename(folder_name, is_directory=True)
                    os.startfile(str(dest))
                    return {
                        "success": True,
                        "message": f"Successfully opened existing folder at '{dest}' (Deferred creation).",
                        "path": str(dest)
                    }
                elif choice == '2':
                    break
                elif choice == '3':
                    raise ValueError("Operation cancelled by user.")
                print("Invalid selection. Please enter 1, 2, or 3.")

    if target.exists():
        if target.is_dir():
            return {
                "success": True,
                "message": f"Folder '{target}' already exists.",
                "path": str(target)
            }
        else:
            raise FileExistsError(f"A file already exists at '{target}'.")
            
    target.mkdir(parents=True, exist_ok=True)
    add_to_index(target)
    return {
        "success": True,
        "message": f"Successfully created folder at '{target}'",
        "path": str(target)
    }

def create_file(filename: str, location: Optional[str] = None) -> dict:
    """Creates a new file after checking duplicate names."""
    if location and location.startswith("_ALREADY_OPENED_:"):
        dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
        return {
            "success": True,
            "message": f"Successfully opened existing file at '{dest_path}' (Deferred creation).",
            "path": str(dest_path)
        }

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
            print(f"\nA file or folder named '{filename}' already exists:")
            for idx, r in enumerate(rows, 1):
                loc = r["relative_location"]
                suffix = f" ({loc})" if loc else ""
                print(f"  {idx}. {r['absolute_path']}{suffix}")
            print("\nWhat would you like to do?")
            print("  1. Open Existing")
            print("  2. Create Another")
            print("  3. Cancel")
            
            while True:
                choice = input("Enter selection (1-3): ").strip()
                if choice == '1':
                    # Open existing
                    if len(rows) == 1:
                        dest = Path(rows[0]["absolute_path"])
                    else:
                        dest = resolve_filename(filename, is_directory=False)
                    os.startfile(str(dest))
                    return {
                        "success": True,
                        "message": f"Successfully opened existing file at '{dest}' (Deferred creation).",
                        "path": str(dest)
                    }
                elif choice == '2':
                    break
                elif choice == '3':
                    raise ValueError("Operation cancelled by user.")
                print("Invalid selection. Please enter 1, 2, or 3.")

    if target.exists():
        if target.is_file():
            return {
                "success": True,
                "message": f"File '{target}' already exists.",
                "path": str(target)
            }
        else:
            raise FileExistsError(f"A directory already exists at '{target}'.")
            
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
    add_to_index(target)
    return {
        "success": True,
        "message": f"Successfully created file at '{target}'",
        "path": str(target)
    }

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

