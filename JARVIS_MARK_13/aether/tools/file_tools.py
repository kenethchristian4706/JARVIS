"""
tools/file_tools.py

Implements handlers for local file and folder operations delegating to the platform abstraction layer.
"""

import logging
from pathlib import Path
from typing import List, Optional

from aether.platforms import platform
from aether.tools.file_search_service import FileSearchService, handle_file_suggestions
from aether.tools.indexer import get_db_connection

logger = logging.getLogger(__name__)

FALLBACK_SEARCH_TRIGGERED = False

def get_user_directories() -> List[Path]:
    """Returns a list of common user directories."""
    return platform.path.get_user_directories()

def resolve_path(target_path: str) -> Path:
    """Resolves a string path using platform resolver."""
    return platform.file.resolve_path(target_path)

def resolve_filename(name_or_path: str, is_directory: Optional[bool] = None) -> Path:
    """Resolves filename or path via platform search."""
    return platform.file.resolve_filename(name_or_path, is_directory)

def find_all_files_on_disk(name_or_path: str, is_directory: Optional[bool] = None) -> List[Path]:
    """Performs a full filesystem walk to find all matching files or folders."""
    return FileSearchService.find_all_files_on_disk(name_or_path, is_directory)

def find_file_on_disk(name_or_path: str, is_directory: Optional[bool] = None) -> Optional[Path]:
    """Finds first matching file/folder on disk."""
    matches = find_all_files_on_disk(name_or_path, is_directory)
    return matches[0] if matches else None

@handle_file_suggestions
def move_file(source: str, destination: Optional[str] = None) -> str:
    """Moves a file or folder from source path to destination folder or path."""
    return platform.file.move_file(source, destination)

@handle_file_suggestions
def copy_file(source: str, destination: Optional[str] = None) -> str:
    """Copies a file from source path to destination folder or path."""
    return platform.file.copy_file(source, destination)

@handle_file_suggestions
def rename_file(source: str, new_name: str) -> str:
    """Renames a file or folder at a given path to a new filename."""
    return platform.file.rename_file(source, new_name)

@handle_file_suggestions
def delete_file(filename: str) -> str:
    """Deletes a file (moves it to Trash/Recycle Bin)."""
    return platform.file.delete_file(filename)

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

@handle_file_suggestions
def open_file(filename: str) -> str:
    """Opens a file using its default registered OS application."""
    return platform.file.open_file(filename)

def create_folder(folder_name: str, location: Optional[str] = None) -> str:
    """Creates a new folder/directory recursively."""
    return platform.file.create_folder(folder_name, location)

def create_file(filename: str, location: Optional[str] = None) -> str:
    """Creates a new empty file."""
    return platform.file.create_file(filename, location)

@handle_file_suggestions
def delete_folder(folder_name: str) -> str:
    """Deletes a folder recursively (moves it to Trash/Recycle Bin)."""
    return platform.file.delete_folder(folder_name)

@handle_file_suggestions
def compress_files(sources: List[str], output: str) -> str:
    """Compresses a list of files/folders into a zip archive."""
    return platform.file.compress_files(sources, output)

@handle_file_suggestions
def extract_archive(archive: str, destination: Optional[str] = None) -> str:
    """Extracts a zip archive to the destination directory."""
    return platform.file.extract_archive(archive, destination)

@handle_file_suggestions
def list_directory(path: Optional[str] = None) -> str:
    """List the files and directories inside a specified path."""
    return platform.file.list_directory(path)

@handle_file_suggestions
def file_info(filename: str) -> str:
    """Gets metadata for a specific file (size, extension, modified date)."""
    return platform.file.file_info(filename)

@handle_file_suggestions
def append_file(filename: str, content: str) -> str:
    """Appends content to a file."""
    return platform.file.append_file(filename, content)

@handle_file_suggestions
def extract_text_from_image(image_path: str) -> dict:
    """Extract text from an image using OCR."""
    return platform.file.extract_text_from_image(image_path)

@handle_file_suggestions
def read_file_content(file_path: str) -> dict:
    """Read text content from supported files."""
    return platform.file.read_file_content(file_path)
