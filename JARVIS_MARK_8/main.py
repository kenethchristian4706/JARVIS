"""
main.py

Main interactive console interface for the Aether MVP Offline AI Desktop Assistant.
Bootstraps indices, starts background watchdogs, launches the llama-server sidecar,
and handles the query processing loop.
"""

import os
import sys
import time
from database.db_manager import init_db, get_db_connection
from indexing.file_indexer import index_folder_recursive
from indexing.app_indexer import index_installed_applications
from indexing.watchdog_service import WatchdogService
from ai.tool_selector import ToolSelector
from ai.parameter_extractor import ParameterExtractor
from execution.dispatcher import dispatch_and_execute

def resolve_common_folders(name: str) -> str:
    """
    Resolves common named directories to absolute Windows user paths.
    """
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
    common_paths = {
        "desktop": os.path.join(user_profile, "Desktop"),
        "documents": os.path.join(user_profile, "Documents"),
        "downloads": os.path.join(user_profile, "Downloads"),
        "pictures": os.path.join(user_profile, "Pictures"),
        "music": os.path.join(user_profile, "Music"),
        "videos": os.path.join(user_profile, "Videos")
    }
    
    clean_name = name.strip().lower()
    if clean_name in common_paths:
        return os.path.normpath(common_paths[clean_name])
    return os.path.normpath(os.path.abspath(name.strip()))

def run_first_time_setup():
    """
    Checks if database permissions are empty and guides the user through folder authorization.
    Also indexes registry applications on first launch.
    """
    # 1. Initialize databases
    init_db()
    
    # Check if we have authorized folders
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM folder_permissions")
        has_permissions = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM installed_apps")
        has_apps = cursor.fetchone()[0] > 0

    # 2. Run App Indexer if empty
    if not has_apps:
        print("\n[Setup] No apps indexed. Scanning Registry and Start Menu Shortcuts...")
        index_installed_applications()

    # 3. Prompt user for folders to access
    if not has_permissions:
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
            
        print("\n[Setup] Indexing authorized directories recursively...")
        for folder in folders:
            abs_path = resolve_common_folders(folder)
            if not os.path.exists(abs_path):
                print(f"[Setup] Folder '{abs_path}' does not exist. Creating it...")
                os.makedirs(abs_path, exist_ok=True)
            index_folder_recursive(abs_path, "full_control")
            
        print("[Setup] Authorized folders indexed successfully!")

def main_loop():
    print("\n" + "=" * 60)
    print("      AETHER OFFLINE AI DESKTOP ASSISTANT - ACTIVE")
    print("      (Type 'exit', 'quit', or 'help' to interact)")
    print("=" * 60)
    
    # 1. Initialize selectors and extractors
    print("[Aether] Initializing Tool Selection Engine (FAISS)...")
    selector = ToolSelector()
    
    print("[Aether] Initializing Parameter Extraction Engine (Sidecar)...")
    extractor = ParameterExtractor()
    
    # Ensure sidecar starts up immediately
    print("[Aether] Bootstrapping background LLM server...")
    if not extractor.start_sidecar_server():
        print("[Aether] ERROR: Failed to start background LLM server. Shutting down.", file=sys.stderr)
        return
        
    # 2. Start watchdog monitors
    print("[Aether] Launching incremental filesystem watchdogs...")
    watchdog = WatchdogService()
    watchdog.start()
    
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
                print(" - 'capture my screen' / 'shutdown computer'")
                continue

            print("[Aether] Selecting tool...")
            select_res = selector.select_tool(query)
            
            if select_res["requires_clarification"] or not select_res["selected_tool"]:
                print("[Aether] Clarification: I am not confident about which tool to execute. Could you rephrase your request?")
                continue
                
            tool_name = select_res["selected_tool"]
            confidence = select_res["score"]
            print(f"[Aether] Matched Tool: '{tool_name}' (Confidence: {confidence:.2f})")
            
            print("[Aether] Extracting arguments...")
            extract_res = extractor.extract_parameters(tool_name, query)
            
            if not extract_res["success"]:
                print(f"[Aether] Extraction Error: {extract_res['error']}")
                continue
                
            parameters = extract_res["parameters"]
            print(f"[Aether] Extracted Parameters: {parameters}")
            
            print("[Aether] Dispatching command...")
            exec_res = dispatch_and_execute(query, tool_name, parameters)
            
            # Print execution outcome
            status = exec_res.get("status", "success")
            msg = exec_res.get("message", "Execution complete.")
            if status == "success":
                print(f"\n[SUCCESS] {msg}")
            else:
                print(f"\n[FAILURE] {msg}")
                
    finally:
        # Cleanup and shutdown gracefully
        print("\n[Aether] Commencing cleanup...")
        if watchdog:
            watchdog.stop()
        if extractor:
            extractor.stop_sidecar_server()
        print("[Aether] Shutdown completed successfully. Goodbye!")

if __name__ == "__main__":
    # Ensure Windows path logic runs cleanly
    run_first_time_setup()
    main_loop()
