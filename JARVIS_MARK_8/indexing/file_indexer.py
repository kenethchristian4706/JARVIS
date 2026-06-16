"""
indexing/file_indexer.py

Handles recursive scanning of user-permitted folders, metadata indexing
into SQLite, permissions storage, and rapid lookup queries.
"""

import os
import sqlite3
from datetime import datetime
from database.db_manager import get_db_connection

def add_folder_permission(folder_path: str, access_level: str):
    """
    Saves folder authorization access level in SQLite.
    Access levels: 'none', 'read', 'read_write', 'full_control'
    """
    norm_path = os.path.normpath(folder_path)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO folder_permissions (folder_path, access_level) VALUES (?, ?)",
            (norm_path, access_level)
        )
        conn.commit()

def get_folder_permission(folder_path: str) -> str:
    """
    Retrieves the access level of a folder, checking parent folders recursively if not set explicitly.
    Defaults to 'none' if unauthorized.
    """
    norm_path = os.path.normpath(folder_path)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check parent hierarchy up to drive root
        current = norm_path
        while True:
            cursor.execute("SELECT access_level FROM folder_permissions WHERE folder_path = ?", (current,))
            row = cursor.fetchone()
            if row:
                return row["access_level"]
                
            parent = os.path.dirname(current)
            if parent == current: # Reached drive root (e.g. C:\)
                # Check drive root itself
                cursor.execute("SELECT access_level FROM folder_permissions WHERE folder_path = ?", (current,))
                row = cursor.fetchone()
                if row:
                    return row["access_level"]
                break
            current = parent
            
    return "none"

def index_file(file_path: str):
    """
    Extracts metadata for a single file and inserts/replaces it in the SQLite index.
    """
    norm_path = os.path.normpath(file_path)
    if not os.path.exists(norm_path):
        return
        
    try:
        stat = os.stat(norm_path)
        file_name = os.path.basename(norm_path)
        ext = os.path.splitext(file_name)[1].lower()
        parent_folder = os.path.dirname(norm_path)
        size = stat.st_size
        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Resolve access level based on parent folder permissions
        access_level = get_folder_permission(parent_folder)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO file_index 
                (file_name, absolute_path, extension, parent_folder, size, modified_time, access_level, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_name, norm_path, ext, parent_folder, size, modified_time, access_level, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        # Silently skip file read permission locks or systemic issues during indexing
        pass

def deindex_file(file_path: str):
    """
    Removes a file from the SQLite index.
    """
    norm_path = os.path.normpath(file_path)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_index WHERE absolute_path = ?", (norm_path,))
        conn.commit()

def index_folder_recursive(folder_path: str, access_level: str = "read"):
    """
    Adds folder permission and indexes all files inside recursively.
    """
    norm_path = os.path.normpath(folder_path)
    add_folder_permission(norm_path, access_level)
    
    print(f"[Indexer] Recursively scanning and indexing: {norm_path} (Access: {access_level})...")
    
    for root, _, files in os.walk(norm_path):
        for f in files:
            file_path = os.path.join(root, f)
            index_file(file_path)

def query_files_by_name(name_query: str) -> list:
    """
    Searches file_index for matching file names.
    Returns list of sqlite3.Row dict-like objects. Runs in sub-10ms.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Case insensitive lookup
        cursor.execute(
            "SELECT * FROM file_index WHERE file_name LIKE ? ORDER BY file_name ASC LIMIT 50",
            (f"%{name_query}%",)
        )
        return cursor.fetchall()
