"""
indexing/watchdog_service.py

Uses the watchdog library to monitor approved folders for filesystem events
and keep the SQLite file index up to date.
"""

import time
import logging
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from indexing.file_indexer import remove_file_from_index, update_file_in_index, SYSTEM_IGNORE_DIRS

logger = logging.getLogger(__name__)

# Shared thread lock for database access
_db_lock = threading.Lock()

class AetherFileHandler(FileSystemEventHandler):
    def __init__(self, db_path: str, have_access: int = 1):
        super().__init__()
        self.db_path = db_path
        self.have_access = have_access
        
    def _should_skip(self, path_str: str) -> bool:
        path = Path(path_str)
        name_lower = path.name.lower()
        # Skip database and log files to prevent infinite watchdog feedback loop
        if path.suffix.lower() in (".log", ".log1", ".log2", ".dat") or "aether.db" in name_lower:
            return True
        # Skip hidden files/folders and system/cache directories recursively
        for part in path.parts:
            part_lower = part.lower()
            if part.startswith(".") or part_lower in SYSTEM_IGNORE_DIRS:
                return True
        return False

    def on_created(self, event):
        if event.is_directory or self._should_skip(event.src_path):
            return
            
        logger.debug(f"File created: {event.src_path}")
        path = Path(event.src_path).resolve()
        file_name = path.name
        abs_path = str(path)
        ext = path.suffix.lower() if path.suffix else ""
        parent_folder = str(path.parent.resolve())
        
        # Safely get file metadata
        try:
            stat = path.stat()
            size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except (FileNotFoundError, PermissionError):
            return
            
        with _db_lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO file_index 
                        (file_name, absolute_path, extension, parent_folder, size, modified_time, have_access)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (file_name, abs_path, ext, parent_folder, size, modified_time, self.have_access))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error indexing created file {abs_path}: {e}")

    def on_deleted(self, event):
        if event.is_directory or self._should_skip(event.src_path):
            return
            
        logger.debug(f"File deleted: {event.src_path}")
        with _db_lock:
            try:
                remove_file_from_index(event.src_path, self.db_path)
            except Exception as e:
                logger.error(f"Error deindexing deleted file {event.src_path}: {e}")

    def on_moved(self, event):
        # Handle both files and directories for moves/renames
        if self._should_skip(event.src_path) or self._should_skip(event.dest_path):
            return
            
        logger.debug(f"Moved: '{event.src_path}' to '{event.dest_path}'")
        with _db_lock:
            try:
                if event.is_directory:
                    # If directory, recursively update all indexed paths inside it
                    # Find all entries starting with old directory path
                    src_dir = str(Path(event.src_path).resolve())
                    dest_dir = str(Path(event.dest_path).resolve())
                    
                    with sqlite3.connect(self.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute("SELECT absolute_path FROM file_index WHERE absolute_path LIKE ?", (f"{src_dir}%",))
                        rows = cursor.fetchall()
                        for row in rows:
                            old_file_path = row["absolute_path"]
                            new_file_path = old_file_path.replace(src_dir, dest_dir, 1)
                            update_file_in_index(old_file_path, new_file_path, self.db_path)
                else:
                    update_file_in_index(event.src_path, event.dest_path, self.db_path)
            except Exception as e:
                logger.error(f"Error handling move from {event.src_path} to {event.dest_path}: {e}")

    def on_modified(self, event):
        if event.is_directory or self._should_skip(event.src_path):
            return
            
        logger.debug(f"File modified: {event.src_path}")
        path = Path(event.src_path).resolve()
        
        with _db_lock:
            try:
                # Read modified size and time
                stat = path.stat()
                size = stat.st_size
                modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE file_index 
                        SET size = ?, modified_time = ?
                        WHERE absolute_path = ?
                    """, (size, modified_time, str(path)))
                    conn.commit()
            except FileNotFoundError:
                # File deleted shortly after modification
                remove_file_from_index(event.src_path, self.db_path)
            except PermissionError:
                # Locked files (temporary locks)
                pass
            except Exception as e:
                logger.error(f"Error modifying file index {event.src_path}: {e}")

def start_watchdog(approved_folders: list[str], db_path: str) -> Observer:
    """
    Creates observers and registers events recursively.
    """
    logger.info("Initializing Watchdog observer service...")
    observer = Observer()
    
    for folder in approved_folders:
        folder_path = Path(folder).resolve()
        if folder_path.exists() and folder_path.is_dir():
            handler = AetherFileHandler(db_path, have_access=1)
            observer.schedule(handler, path=str(folder_path), recursive=True)
            logger.info(f"Watchdog monitoring folder: {folder_path}")
            
    observer.start()
    return observer

if __name__ == "__main__":
    # Test watchdog service locally
    logging.basicConfig(level=logging.INFO)
    test_db = "../database/aether.db"
    test_folder = "C:/Users/lenovo/dev/ather/JARVIS_MARK_6/JARVIS_MARK_9/tests_watchdog"
    Path(test_folder).mkdir(parents=True, exist_ok=True)
    
    # Run test
    obs = start_watchdog([test_folder], test_db)
    print(f"Watchdog running. Create/edit files in {test_folder} to test.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
