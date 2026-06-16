"""
indexing/file_indexer.py

Handles indexing files from approved directories into a SQLite database,
looking up files by name, and maintaining file metadata records.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# List of directories to completely skip during indexing and filesystem watchdog events
SYSTEM_IGNORE_DIRS = {
    # Windows system folders
    "windows", "system volume information", "$recycle.bin", "recovery", "boot", "msocache", "documents and settings",
    # Program files / applications
    "program files", "program files (x86)", "programdata",
    # App data & heavy caches
    "appdata", "application data", "local settings", "temp", "tmp",
    # Developer / dependency noise
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "build", "dist",
    # Specific environment / package folders
    ".gradle", ".npm", ".nuget", ".cache", "site-packages", "virtualenv", "env", ".env",
    # Drivers and logs
    "drivers", "perflogs", "database"
}

def create_index(db_path: str) -> None:
    """
    Creates the file_index table if it does not already exist.
    """
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_index (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name     TEXT NOT NULL,
                absolute_path TEXT NOT NULL UNIQUE,
                extension     TEXT,
                parent_folder TEXT,
                size          INTEGER,
                modified_time DATETIME,
                have_access   INTEGER NOT NULL DEFAULT 1,
                indexed_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

def index_folder(folder_path: str, db_path: str, have_access: int = 1) -> int:
    """
    Walks the folder recursively. For each file found, extracts metadata,
    and inserts/replaces it in the file_index SQLite table.
    Skips hidden files and system directories/caches.
    """
    folder = Path(folder_path).resolve()
    if not folder.exists() or not folder.is_dir():
        logger.warning(f"Folder does not exist or is not a directory: {folder_path}")
        return 0
        
    db_file = Path(db_path)
    count = 0
    
    # We walk using a recursive helper or Path.rglob, but rglob can be slow or raise permission errors.
    # A custom stack walk using Path works best.
    stack = [folder]
    
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        
        # Register the folder itself to establish access permission record even if empty
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO file_index 
                (file_name, absolute_path, extension, parent_folder, size, modified_time, have_access)
                VALUES (?, ?, NULL, ?, 0, ?, ?)
            """, (folder.name, str(folder), str(folder.parent), datetime.now().isoformat(), have_access))
        except Exception:
            pass
        
        while stack:
            current_dir = stack.pop()
            try:
                for child in current_dir.iterdir():
                    # Skip hidden directories and ignore directories
                    name_lower = child.name.lower()
                    if child.name.startswith(".") or name_lower in SYSTEM_IGNORE_DIRS:
                        continue
                        
                    if child.is_dir():
                        stack.append(child)
                    elif child.is_file():
                        # Skip database and log/system files to prevent infinite watchdog feedback loop
                        ext_lower = child.suffix.lower()
                        if ext_lower in (".log", ".log1", ".log2", ".dat") or "aether.db" in name_lower:
                            continue
                        
                        file_name = child.name
                        abs_path = str(child.resolve())
                        ext = child.suffix.lower() if child.suffix else ""
                        parent_folder = str(child.parent.resolve())
                        
                        try:
                            stat = child.stat()
                            size = stat.st_size
                            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        except (FileNotFoundError, PermissionError):
                            # File deleted mid-walk or restricted permissions
                            continue
                            
                        cursor.execute("""
                            INSERT OR REPLACE INTO file_index 
                            (file_name, absolute_path, extension, parent_folder, size, modified_time, have_access)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (file_name, abs_path, ext, parent_folder, size, modified_time, have_access))
                        count += 1
            except (PermissionError, FileNotFoundError):
                # Restrained directory access
                continue
                
        conn.commit()
        
    logger.info(f"Indexed {count} files in folder '{folder_path}' (have_access={have_access})")
    return count

def setup_index(approved_folders: list[str], db_path: str) -> None:
    """
    Sets up the database index and populates it with files from approved folders.
    """
    create_index(db_path)
    for folder in approved_folders:
        print(f"Indexing: {folder} ... ", end="", flush=True)
        count = index_folder(folder, db_path, have_access=1)
        print(f"{count} files indexed.")

def lookup_file(query_term: str, db_path: str) -> dict | None:
    """
    Looks up a file name using a pattern match. Returns the first matched file's
    absolute path and access level.
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return None
        
    with sqlite3.connect(str(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT absolute_path, have_access FROM file_index WHERE LOWER(file_name) LIKE ? LIMIT 1",
            (f"%{query_term.lower()}%",)
        )
        row = cursor.fetchone()
        if row:
            return {"absolute_path": row["absolute_path"], "have_access": row["have_access"]}
    return None

def lookup_file_multi(query_term: str, db_path: str, limit: int = 5) -> list[dict]:
    """
    Searches for multiple matches and returns their name, absolute path, and access level.
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return []
        
    with sqlite3.connect(str(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_name, absolute_path, have_access FROM file_index WHERE LOWER(file_name) LIKE ? LIMIT ?",
            (f"%{query_term.lower()}%", limit)
        )
        return [{"file_name": row["file_name"], "absolute_path": row["absolute_path"], "have_access": row["have_access"]} 
                for row in cursor.fetchall()]

def remove_file_from_index(absolute_path: str, db_path: str) -> None:
    """
    Removes a file from the SQLite index by path.
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return
        
    norm_path = str(Path(absolute_path).resolve())
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_index WHERE absolute_path = ?", (norm_path,))
        conn.commit()
    logger.debug(f"Removed from index: {absolute_path}")

def update_file_in_index(old_path: str, new_path: str, db_path: str) -> None:
    """
    Updates the file path and metadata when a file is renamed or moved.
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return
        
    old_resolved = str(Path(old_path).resolve())
    new_resolved_path = Path(new_path).resolve()
    new_resolved = str(new_resolved_path)
    file_name = new_resolved_path.name
    parent_folder = str(new_resolved_path.parent.resolve())
    ext = new_resolved_path.suffix.lower() if new_resolved_path.suffix else ""
    
    try:
        stat = new_resolved_path.stat()
        size = stat.st_size
        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
    except (FileNotFoundError, OSError):
        size = 0
        modified_time = datetime.now().isoformat()
        
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.cursor()
        # Retrieve old permission level or default to 1
        cursor.execute("SELECT have_access FROM file_index WHERE absolute_path = ?", (old_resolved,))
        row = cursor.fetchone()
        have_access = row[0] if row else 1
        
        cursor.execute("""
            INSERT OR REPLACE INTO file_index 
            (file_name, absolute_path, extension, parent_folder, size, modified_time, have_access)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_name, new_resolved, ext, parent_folder, size, modified_time, have_access))
        
        if old_resolved != new_resolved:
            cursor.execute("DELETE FROM file_index WHERE absolute_path = ?", (old_resolved,))
            
        conn.commit()
    logger.debug(f"Updated index path: '{old_path}' -> '{new_path}'")
