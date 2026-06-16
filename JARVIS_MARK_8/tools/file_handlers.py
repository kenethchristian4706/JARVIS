"""
tools/file_handlers.py

Implements execution handlers for file and folder management tools,
as well as Notepad helper routines.
Resolves simple file names to absolute paths using the SQLite index.
"""

import os
import shutil
import tempfile
import subprocess
from indexing.file_indexer import query_files_by_name

def resolve_file_path(filename: str, search_if_not_found: bool = True) -> str:
    """
    Resolves a file path. If it's a simple filename, queries the database
    to find its absolute path.
    """
    if os.path.isabs(filename):
        return os.path.normpath(filename)
        
    # Check current directory
    local_path = os.path.abspath(filename)
    if os.path.exists(local_path):
        return os.path.normpath(local_path)
        
    if search_if_not_found:
        matches = query_files_by_name(filename)
        if matches:
            # Return first exact or best match
            return os.path.normpath(matches[0]["absolute_path"])
            
    return os.path.normpath(local_path)

def search_file(filename: str) -> dict:
    matches = query_files_by_name(filename)
    results = [dict(row) for row in matches]
    return {
        "status": "success",
        "message": f"Found {len(results)} matches for '{filename}'.",
        "data": results
    }

def open_file(filename: str) -> dict:
    path = resolve_file_path(filename)
    if not os.path.exists(path):
        return {"status": "error", "message": f"File not found: {path}"}
    try:
        os.startfile(path)
        return {"status": "success", "message": f"Opened file: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to open file: {e}"}

def create_file(filename: str) -> dict:
    path = resolve_file_path(filename, search_if_not_found=False)
    try:
        # Create directory tree if missing
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            pass
        return {"status": "success", "message": f"Created file: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create file: {e}"}

def delete_file(filename: str) -> dict:
    path = resolve_file_path(filename)
    if not os.path.exists(path):
        return {"status": "error", "message": f"File does not exist: {path}"}
    try:
        os.remove(path)
        return {"status": "success", "message": f"Deleted file: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete file: {e}"}

def rename_file(filename: str, new_name: str) -> dict:
    path = resolve_file_path(filename)
    if not os.path.exists(path):
        return {"status": "error", "message": f"File not found: {path}"}
    try:
        parent = os.path.dirname(path)
        new_path = os.path.join(parent, new_name)
        os.rename(path, new_path)
        return {"status": "success", "message": f"Renamed file '{path}' to '{new_name}'."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rename file: {e}"}

def move_file(source: str, destination: str) -> dict:
    src_path = resolve_file_path(source)
    dest_path = resolve_file_path(destination, search_if_not_found=False)
    
    if not os.path.exists(src_path):
        return {"status": "error", "message": f"Source file not found: {src_path}"}
        
    try:
        # If destination is a folder, make sure it exists
        if not os.path.splitext(dest_path)[1]: # Is directory path
            os.makedirs(dest_path, exist_ok=True)
            
        shutil.move(src_path, dest_path)
        return {"status": "success", "message": f"Moved file from '{src_path}' to '{dest_path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move file: {e}"}

def copy_file(source: str, destination: str) -> dict:
    src_path = resolve_file_path(source)
    dest_path = resolve_file_path(destination, search_if_not_found=False)
    
    if not os.path.exists(src_path):
        return {"status": "error", "message": f"Source file not found: {src_path}"}
        
    try:
        if not os.path.splitext(dest_path)[1]: # Is directory path
            os.makedirs(dest_path, exist_ok=True)
            
        shutil.copy2(src_path, dest_path)
        return {"status": "success", "message": f"Copied file from '{src_path}' to '{dest_path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy file: {e}"}

def create_folder(folder_name: str) -> dict:
    path = resolve_file_path(folder_name, search_if_not_found=False)
    try:
        os.makedirs(path, exist_ok=True)
        return {"status": "success", "message": f"Created folder: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create folder: {e}"}

def delete_folder(folder_name: str) -> dict:
    path = resolve_file_path(folder_name)
    if not os.path.exists(path) or not os.path.isdir(path):
        return {"status": "error", "message": f"Folder not found: {path}"}
    try:
        shutil.rmtree(path)
        return {"status": "success", "message": f"Deleted folder: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete folder: {e}"}

def rename_folder(folder_name: str, new_name: str) -> dict:
    path = resolve_file_path(folder_name)
    if not os.path.exists(path) or not os.path.isdir(path):
        return {"status": "error", "message": f"Folder not found: {path}"}
    try:
        parent = os.path.dirname(path)
        new_path = os.path.join(parent, new_name)
        os.rename(path, new_path)
        return {"status": "success", "message": f"Renamed folder '{path}' to '{new_name}'."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rename folder: {e}"}

def open_notepad_and_write(app_name: str, text: str) -> dict:
    """
    Creates a temporary file with the specified text and opens it in Notepad.
    """
    try:
        # Create a temp file to hold text
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "aether_notepad_temp.txt")
        
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        subprocess.Popen(["notepad.exe", temp_path])
        return {
            "status": "success",
            "message": f"Opened Notepad containing the text: '{text[:20]}...'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to open Notepad: {e}"}

def append_to_file(filename: str, text: str) -> dict:
    path = resolve_file_path(filename)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + text)
        return {"status": "success", "message": f"Appended text to: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to append to file: {e}"}

def read_file_content(filename: str) -> dict:
    path = resolve_file_path(filename)
    if not os.path.exists(path):
        return {"status": "error", "message": f"File not found: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "status": "success",
            "message": f"Read content from file: {path}",
            "data": {"content": content}
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file: {e}"}
