"""
indexing/watchdog_service.py

Implements a watchdog daemon to watch user-authorized folders and update
the SQLite index incrementally when files are created, deleted, renamed, or modified.
"""

import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from database.db_manager import get_db_connection
from indexing.file_indexer import index_file, deindex_file

class FileIndexHandler(FileSystemEventHandler):
    """
    Event handler linking filesystem changes to SQLite indexers.
    """
    def on_created(self, event):
        if not event.is_directory:
            index_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            deindex_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            index_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            deindex_file(event.src_path)
            index_file(event.dest_path)

class WatchdogService:
    def __init__(self):
        self.observer = None
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """
        Starts the watchdog observer in a background thread.
        Monitors all authorized directories in folder_permissions.
        """
        if self.observer is not None:
            return
            
        self.observer = Observer()
        handler = FileIndexHandler()
        
        # Load authorized folder roots from database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT folder_path, access_level FROM folder_permissions")
            rows = cursor.fetchall()
            
        watch_count = 0
        for row in rows:
            path = row["folder_path"]
            level = row["access_level"]
            if level != "none" and os.path.exists(path):
                self.observer.schedule(handler, path=path, recursive=True)
                watch_count += 1
                
        if watch_count == 0:
            print("[Watchdog] No authorized folders to monitor.")
            self.observer = None
            return

        print(f"[Watchdog] Starting service monitoring {watch_count} directories recursively...")
        self.observer.start()

    def stop(self):
        """
        Stops the watchdog service observer.
        """
        if self.observer:
            print("[Watchdog] Stopping service...")
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("[Watchdog] Stopped successfully.")
            
if __name__ == "__main__":
    # Test script runs watchdog locally
    service = WatchdogService()
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
