"""
tools/indexer.py

Manages SQLite-based file indexing for all logical drives.
Provides real-time updates using watchdog and initial background full walk.
"""

import os
import sqlite3
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

# Resolve DB path relative to the config / script directory
DB_PATH = (Path(__file__).parent.parent / "database.db").resolve()

# Folders to exclude from indexing
EXCLUDED_DIRS = {
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "AppData",
    "$Recycle.Bin",
    "System Volume Information",
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".cargo",
    ".rustup",
    ".gradle",
    ".conda",
    "logs",
    ".gemini"
}

# File extensions that are considered operable/openable by the user
OPERABLE_EXTENSIONS = {
    # Documents
    ".txt", ".pdf", ".csv", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".md", ".rtf", ".odt", ".ods", ".odp",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
    # Audio & Video
    ".mp3", ".wav", ".mp4", ".mkv", ".avi", ".mov", ".flac",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz",
    # Code & Configs
    ".py", ".ipynb", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".ini", ".conf",
    # Executables & Shortcuts
    ".exe", ".lnk", ".bat", ".cmd", ".ps1"
}

_observer = None

def get_db_connection():
    """Returns a SQLite connection to the index database."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception as e:
        logger.debug(f"Failed to set WAL mode: {e}")
    conn.row_factory = sqlite3.Row
    return conn

_db_initialized = False

def init_db():
    """Initializes the database schema if it does not exist."""
    global _db_initialized
    if _db_initialized:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            extension TEXT,
            relative_location TEXT,
            absolute_path TEXT UNIQUE,
            modified_time DATETIME,
            is_directory BOOLEAN
        )
    """)
    conn.commit()
    conn.close()
    _db_initialized = True
    logger.info("SQLite index database initialized.")

def get_indexed_paths() -> List[Path]:
    """Resolves and returns the list of active logical drive paths to index."""
    from aether.platforms import platform
    if os.environ.get("AETHER_TESTING") == "1":
        return platform.path.get_user_directories()
        
    try:
        return platform.file.get_indexed_paths()
    except Exception as e:
        logger.error(f"Error resolving logical drives: {e}")
        # Fallback to user home if drive discovery fails
        return [Path.home()]

def compute_relative_location(path: Path) -> str:
    """
    Computes the parent folder path relative to the user profile or home, or drive root.
    E.g. C:/Users/name/Documents/work/file.txt -> Documents/work
         D:/work/file.txt -> work
    """
    try:
        user_home = Path.home()
        parent = path.parent.resolve()
        if parent == user_home:
            return ""
        if parent.is_relative_to(user_home):
            return str(parent.relative_to(user_home)).replace("\\", "/")
            
        # Fallback to drive-relative path
        drive = parent.drive
        if drive:
            drive_root = Path(drive + "/")
            if parent == drive_root:
                return ""
            if parent.is_relative_to(drive_root):
                return str(parent.relative_to(drive_root)).replace("\\", "/")
    except Exception:
        pass
    return str(path.parent.name)

def is_excluded_path(path: Path) -> bool:
    """Checks if a path contains any folder from EXCLUDED_DIRS or is the DB itself."""
    try:
        # Check folders
        lower_parts = {p.lower() for p in path.parts}
        for d in EXCLUDED_DIRS:
            if d.lower() in lower_parts:
                return True
        
        # Check if the path is the database file or one of its temporary files (journal, wal, shm)
        resolved_path = path.resolve()
        resolved_path_str = str(resolved_path).lower()
        db_path_str = str(DB_PATH).lower()
        if resolved_path_str == db_path_str or resolved_path_str.startswith(db_path_str + "-"):
            return True
    except Exception:
        pass
    return False

def index_all():
    """
    Performs a full walk of all accessible drives, updates the index,
    and removes files that no longer exist on disk.
    """
    init_db()
    logger.info("Starting full file indexing walk...")
    indexed_paths = get_indexed_paths()
    db_paths_on_disk = set()

    conn = get_db_connection()
    cursor = conn.cursor()

    EXCLUDED_DIRS_LOWER = {d.lower() for d in EXCLUDED_DIRS}

    write_counter = 0
    for base_dir in indexed_paths:
        logger.info(f"Indexing drive: {base_dir}")
        try:
            for root, dirs, files in os.walk(base_dir):
                # Prune excluded directories in-place case-insensitively and skip dot/dollar system dirs
                dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS_LOWER and not d.startswith(".") and not d.startswith("$")]
                
                # Scan files
                for file_name in files:
                    full_path = Path(root) / file_name
                    if is_excluded_path(full_path):
                        continue
                    if full_path.suffix.lower() not in OPERABLE_EXTENSIONS:
                        continue
                    try:
                        abs_path_str = str(full_path.resolve())
                        db_paths_on_disk.add(abs_path_str)
                        
                        stat = full_path.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        ext = full_path.suffix
                        rel_loc = compute_relative_location(full_path)
                        
                        cursor.execute("""
                            INSERT INTO indexed_files (filename, extension, relative_location, absolute_path, modified_time, is_directory)
                            VALUES (?, ?, ?, ?, ?, 0)
                            ON CONFLICT(absolute_path) DO UPDATE SET
                                filename = excluded.filename,
                                extension = excluded.extension,
                                relative_location = excluded.relative_location,
                                modified_time = excluded.modified_time
                        """, (file_name, ext, rel_loc, abs_path_str, mtime))
                        write_counter += 1
                        if write_counter % 500 == 0:
                            conn.commit()
                    except Exception:
                        pass

                # Scan directories
                for dir_name in dirs:
                    full_path = Path(root) / dir_name
                    try:
                        abs_path_str = str(full_path.resolve())
                        db_paths_on_disk.add(abs_path_str)
                        
                        stat = full_path.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        rel_loc = compute_relative_location(full_path)
                        
                        cursor.execute("""
                            INSERT INTO indexed_files (filename, extension, relative_location, absolute_path, modified_time, is_directory)
                            VALUES (?, ?, ?, ?, ?, 1)
                            ON CONFLICT(absolute_path) DO UPDATE SET
                                filename = excluded.filename,
                                extension = excluded.extension,
                                relative_location = excluded.relative_location,
                                modified_time = excluded.modified_time
                        """, (dir_name, "", rel_loc, abs_path_str, mtime))
                        write_counter += 1
                        if write_counter % 500 == 0:
                            conn.commit()
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error scanning location {base_dir}: {e}")

    conn.commit()

    # Clean up stale paths in the DB
    cursor.execute("SELECT absolute_path FROM indexed_files")
    rows = cursor.fetchall()
    stale_paths = []
    for row in rows:
        path_str = row["absolute_path"]
        if path_str not in db_paths_on_disk:
            stale_paths.append(path_str)

    if stale_paths:
        logger.info(f"Removing {len(stale_paths)} stale entries from index database.")
        cursor.executemany("DELETE FROM indexed_files WHERE absolute_path = ?", [(p,) for p in stale_paths])
        conn.commit()

    conn.close()
    logger.info("File indexing finished.")

def add_to_index(path: Path, is_directory: Optional[bool] = None):
    """Adds or updates a single file/directory in the SQLite database index."""
    if is_excluded_path(path):
        return
        
    if is_directory is None:
        try:
            is_dir = path.is_dir()
        except Exception:
            is_dir = False
    else:
        is_dir = is_directory

    if not is_dir and path.suffix.lower() not in OPERABLE_EXTENSIONS:
        return

    init_db()
    try:
        abs_path = path.resolve()
        abs_path_str = str(abs_path)
        stat = abs_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        filename = abs_path.name
        ext = "" if is_dir else abs_path.suffix
        rel_loc = compute_relative_location(abs_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO indexed_files (filename, extension, relative_location, absolute_path, modified_time, is_directory)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(absolute_path) DO UPDATE SET
                filename = excluded.filename,
                extension = excluded.extension,
                relative_location = excluded.relative_location,
                modified_time = excluded.modified_time,
                is_directory = excluded.is_directory
        """, (filename, ext, rel_loc, abs_path_str, mtime, 1 if is_dir else 0))
        conn.commit()
        conn.close()
        logger.debug(f"Index added/updated: {abs_path_str}")
    except Exception as e:
        logger.debug(f"Error adding {path} to index: {e}")

def remove_from_index(path: Path, is_directory: Optional[bool] = None):
    """Removes a file/directory from the index database (including children if folder)."""
    if is_excluded_path(path):
        return
        
    if is_directory is None:
        try:
            is_dir = path.is_dir()
        except Exception:
            is_dir = False
    else:
        is_dir = is_directory

    if not is_dir and path.suffix.lower() not in OPERABLE_EXTENSIONS:
        return

    init_db()
    try:
        abs_path_str = str(path.resolve())
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM indexed_files WHERE absolute_path = ?", (abs_path_str,))
        cursor.execute("DELETE FROM indexed_files WHERE absolute_path LIKE ?", (abs_path_str + "/%",))
        cursor.execute("DELETE FROM indexed_files WHERE absolute_path LIKE ?", (abs_path_str + "\\%",))
        
        conn.commit()
        conn.close()
        logger.debug(f"Index removed: {abs_path_str}")
    except Exception as e:
        logger.debug(f"Error removing {path} from index: {e}")

class IndexEventHandler(FileSystemEventHandler):
    """Handles real-time file system events to update the index database."""
    def on_created(self, event):
        path = Path(event.src_path)
        add_to_index(path, is_directory=event.is_directory)

    def on_deleted(self, event):
        path = Path(event.src_path)
        remove_from_index(path, is_directory=event.is_directory)

    def on_modified(self, event):
        # Only index file modifications; directory modification signals can be noisy
        if not event.is_directory:
            path = Path(event.src_path)
            add_to_index(path, is_directory=False)

    def on_moved(self, event):
        old_path = Path(event.src_path)
        new_path = Path(event.dest_path)
        remove_from_index(old_path, is_directory=event.is_directory)
        add_to_index(new_path, is_directory=event.is_directory)

def start_watchdog_observer():
    """Starts recursive watchdog monitoring across all indexed logical drives."""
    observer = Observer()
    handler = IndexEventHandler()
    
    drives = get_indexed_paths()
    for d in drives:
        try:
            observer.schedule(handler, str(d), recursive=True)
            logger.info(f"Watchdog monitoring scheduled for drive: {d}")
        except Exception as e:
            logger.warning(f"Watchdog could not monitor drive {d}: {e}")
            
    observer.start()
    return observer

def start_background_refresh():
    """Starts watchdog monitoring and runs the initial index_all scan synchronously."""
    global _observer
    # 1. Initialize watchdog observer
    try:
        _observer = start_watchdog_observer()
    except Exception as e:
        logger.error(f"Failed to start watchdog observer: {e}")
        
    # 2. Run full scan synchronously
    print("Building search index. Please wait...")
    try:
        index_all()
    except Exception as e:
        logger.error(f"Error during initial full index walk: {e}")
    print("Search index built successfully!")
