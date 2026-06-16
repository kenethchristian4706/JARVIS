import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import DEMO_DIR
from file_index.sqlite_index import reindex_all as sqlite_reindex
from file_index.faiss_index import rebuild_file_index as faiss_reindex

class AetherFolderHandler(FileSystemEventHandler):
    """Event handler that triggers SQLite and FAISS re-indexing on file changes."""
    def on_any_event(self, event):
        # We only care about file events (creation, deletion, moves, modifications)
        if event.is_directory:
            # We can still re-index if directories change to capture additions,
            # but let's filter out temp lock files or database modifications
            if event.event_type == 'modified':
                return
                
        # Skip hidden files and directory operations that are temporary
        src_path = getattr(event, 'src_path', '')
        if src_path and (os.path.basename(src_path).startswith('.') or '.aether_file_index' in src_path):
            return
            
        # Re-index both sqlite and FAISS representation
        try:
            sqlite_reindex()
            faiss_reindex()
        except Exception as e:
            # Prevent watcher thread from dying on temporary read-access locks
            pass

def start_watcher() -> Observer:
    """Starts the watchdog observer to monitor DEMO_DIR."""
    # Ensure directory exists first
    os.makedirs(DEMO_DIR, exist_ok=True)
    
    event_handler = AetherFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, path=DEMO_DIR, recursive=True)
    observer.start()
    return observer
