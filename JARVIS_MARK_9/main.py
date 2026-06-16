"""
main.py

Main interactive console interface for the Aether MVP Offline AI Desktop Assistant.
Handles database bootstrap, folder indexing, sidecar LLM server management,
incremental file watchers, and the main user interaction query pipeline.
"""

import os
import sys
import time
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

import config
from ai.preprocessor import preprocess, is_file_related
from ai.tool_selector.selector import select_tool
from ai.parameter_extractor.extractor import start_sidecar_server, stop_sidecar_server, extract_parameters
from safety.safety_manager import check_safety, get_risk_level
from execution.dispatcher import dispatch
from indexing.file_indexer import create_index, setup_index, lookup_file_multi
from indexing.watchdog_service import start_watchdog

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "aether.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
# Suppress heavy logging from dependencies
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger("aether")

def get_all_drives() -> list[str]:
    """
    Returns all logical drive roots on Windows, e.g. ['C:\\', 'D:\\'].
    Only retrieves valid fixed, removable, or network drives.
    """
    import string
    import ctypes
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    drives = []
    for letter in string.ascii_uppercase:
        if bitmask & (1 << (ord(letter) - 65)):
            drive_path = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            if drive_type in (2, 3, 4):  # Removable, Fixed, Remote
                drives.append(drive_path)
    if not drives:
        drives = ["C:\\"]
    return drives

def resolve_common_folders(name: str) -> str:
    """
    Resolves common named directories to absolute Windows user paths.
    """
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
    common_paths = {
        "desktop": str(Path(user_profile) / "Desktop"),
        "documents": str(Path(user_profile) / "Documents"),
        "downloads": str(Path(user_profile) / "Downloads"),
        "pictures": str(Path(user_profile) / "Pictures"),
        "music": str(Path(user_profile) / "Music"),
        "videos": str(Path(user_profile) / "Videos")
    }
    
    clean_name = name.strip().lower()
    if clean_name in common_paths:
        return os.path.normpath(common_paths[clean_name])
    return os.path.normpath(os.path.abspath(name.strip()))

def get_approved_folders() -> list[str]:
    """
    Queries the file_index table to find previously authorized directories.
    """
    folders = []
    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        return folders
        
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            # Extension is NULL for registered folders
            cursor.execute("SELECT absolute_path FROM file_index WHERE extension IS NULL AND have_access = 1")
            folders = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error querying approved folders: {e}")
    return folders

def run_setup_wizard() -> list[str]:
    """
    Guides the user through authorizing folders for file operations on first run.
    """
    print("\n" + "=" * 60)
    print("AETHER FIRST-TIME SETUP: FOLDER AUTHORIZATION")
    print("=" * 60)
    print("Aether runs completely offline and needs permission to access files.")
    print("Please specify which directories Aether is authorized to read/write.")
    print("Common options: Documents, Desktop, Downloads, or enter custom paths.")
    print("=" * 60)
    
    try:
        folders_input = input("Enter directories (comma-separated, e.g. Documents, Downloads): ").strip()
    except (KeyboardInterrupt, EOFError):
        folders_input = "Downloads"
        
    folders = [f.strip() for f in folders_input.split(",") if f.strip()]
    if not folders:
        folders = ["Downloads"]
        
    resolved_folders = []
    print("\n[Setup] Indexing authorized directories recursively...")
    for folder in folders:
        abs_path = resolve_common_folders(folder)
        path_obj = Path(abs_path)
        if not path_obj.exists():
            print(f"[Setup] Folder '{abs_path}' does not exist. Creating it...")
            path_obj.mkdir(parents=True, exist_ok=True)
        resolved_folders.append(abs_path)
        
    # Setup database schemas and run indexer
    setup_index(resolved_folders, str(config.DB_PATH))
    print("[Setup] Authorized folders indexed successfully!")
    return resolved_folders

def main_loop():
    print("\n" + "=" * 60)
    print("      AETHER OFFLINE AI DESKTOP ASSISTANT - ACTIVE")
    print("      (Type 'exit', 'quit', or 'help' to interact)")
    print("=" * 60)
    
    # 1. Initialize databases and folder list
    create_index(str(config.DB_PATH))
    
    if getattr(config, "ALL_PC_ACCESS", False):
        approved_folders = get_all_drives()
        print(f"[Aether] All-PC Access Mode Active. Detected Drives: {approved_folders}")
        # Insert them into the database to register access permission
        try:
            with sqlite3.connect(str(config.DB_PATH)) as conn:
                cursor = conn.cursor()
                for drive in approved_folders:
                    cursor.execute("""
                        INSERT OR REPLACE INTO file_index 
                        (file_name, absolute_path, extension, parent_folder, size, modified_time, have_access)
                        VALUES (?, ?, NULL, ?, 0, ?, 1)
                    """, (drive, drive, drive, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error registering drives in database: {e}")
            
        print(f"[Aether] Re-indexing authorized directories: {approved_folders}")
        setup_index(approved_folders, str(config.DB_PATH))
    else:
        approved_folders = get_approved_folders()
        if not approved_folders:
            approved_folders = run_setup_wizard()
        else:
            print(f"[Aether] Re-indexing authorized directories: {approved_folders}")
            setup_index(approved_folders, str(config.DB_PATH))
        
    # 2. Start watchdog monitors
    print("[Aether] Launching incremental filesystem watchdogs...")
    watchdog = start_watchdog(approved_folders, str(config.DB_PATH))
    
    # 3. Start sidecar server
    print("[Aether] Bootstrapping background LLM server...")
    if not start_sidecar_server():
        print("[Aether] ERROR: Failed to start background LLM server. Shutting down.", file=sys.stderr)
        watchdog.stop()
        watchdog.join()
        return
        
    print("\n[Aether] Ready for requests!")
    print("-" * 60)
    
    try:
        while True:
            try:
                query = input("\nAether > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Aether] Shutdown request received.")
                break
                
            if not query:
                continue
                
            if query.lower() in ["exit", "quit", "bye"]:
                break
                
            if query.lower() == "help":
                print("Aether supports OS control commands, such as:")
                print(" - 'open chrome' / 'close spotify'")
                print(" - 'set volume to 40' / 'mute volume'")
                print(" - 'create folder Work' / 'create file todo.txt'")
                print(" - 'move report.pdf to Downloads'")
                print(" - 'capture screen' / 'shutdown computer'")
                print(" - 'google search offline AI'")
                print(" - 'download file from http://example.com/test.zip'")
                continue
                
            # Pipeline Step 1: Preprocessing
            logger.debug(f"Raw query: {query}")
            processed_query = preprocess(query)
            logger.debug(f"Preprocessed: {processed_query}")
            
            # Pipeline Step 2: File Index Check (if file-related)
            if is_file_related(processed_query):
                print("[Aether] File-related keywords detected. Performing SQLite index check...")
                # Search database index for keywords mentioned in the query
                query_words = [w for w in processed_query.split() if len(w) > 3]
                matches = []
                for word in query_words:
                    matches.extend(lookup_file_multi(word, str(config.DB_PATH), limit=2))
                
                if matches:
                    print(f"  [SQLite Index Check] Found {len(matches)} potential matching file paths:")
                    for m in matches:
                        print(f"    - {m['file_name']} (Access: {'Allowed' if m['have_access'] == 1 else 'Denied'})")
                else:
                    print("  [SQLite Index Check] No files currently matching query terms in index.")
            
            # Pipeline Step 3: Tool Selector (FAISS semantic matching)
            print("[Aether] Selecting tool...")
            try:
                select_res = select_tool(processed_query)
            except Exception as e:
                print(f"[Aether] Selection Error: {e}")
                continue
                
            tool_name = select_res["selected_tool"]
            score = select_res["score"]
            
            # Enforce confidence threshold check (0.40 as recommended)
            if score < 0.40 or not tool_name:
                print(f"[Aether] Clarification: I am not confident about which tool to execute (Score: {score:.2f}). Could you rephrase your request?")
                continue
                
            print(f"[Aether] Matched Tool: '{tool_name}' (Confidence: {score:.2f})")
            
            # Pipeline Step 4: Parameter Extractor (LLM sidecar prompt)
            print("[Aether] Extracting arguments...")
            extract_res = extract_parameters(tool_name, processed_query)
            
            if not extract_res["success"]:
                print(f"[Aether] Extraction Error: {extract_res['error']}")
                continue
                
            parameters = extract_res["parameters"]
            print(f"[Aether] Extracted Parameters: {parameters}")
            
            # Pipeline Step 5: Safety Check (Risk classification & gate)
            if not check_safety(tool_name, parameters):
                print("[Aether] Execution cancelled: High-risk action was not confirmed.")
                continue
                
            # Pipeline Step 6 & 7: Executor (Dispatcher) and Response
            print("[Aether] Dispatching command...")
            exec_res = dispatch(tool_name, parameters)
            
            if exec_res["success"]:
                output = exec_res["output"]
                print("\n" + "=" * 50)
                print("  ✅ EXECUTION SUCCESS")
                print("=" * 50)
                if isinstance(output, list):
                    for item in output:
                        print(f"  - {item}")
                elif output is not None:
                    print(f"  {output}")
                else:
                    print("  Action complete.")
                print("=" * 50)
            else:
                print("\n" + "=" * 50)
                print("  ❌ EXECUTION FAILURE")
                print("=" * 50)
                print(f"  Error: {exec_res['error']}")
                print("=" * 50)
                
    finally:
        # Graceful cleanup
        print("\n[Aether] Commencing cleanup...")
        if watchdog:
            print("[Aether] Stopping filesystem watchdogs...")
            watchdog.stop()
            watchdog.join()
        print("[Aether] Terminating background LLM server...")
        stop_sidecar_server()
        print("[Aether] Shutdown completed successfully. Goodbye!")

if __name__ == "__main__":
    main_loop()
