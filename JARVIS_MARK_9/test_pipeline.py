"""
test_pipeline.py

Automated test harness for verifying Aether POC pipeline end-to-end.
Does not require interactive input, making it suitable for automated run environments.
"""

import os
import sys
import time
from pathlib import Path

# Add the project directory to python module path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import config
from ai.preprocessor import preprocess, is_file_related
from ai.tool_selector.selector import select_tool
from ai.parameter_extractor.extractor import start_sidecar_server, stop_sidecar_server, extract_parameters
from safety.safety_manager import get_risk_level
from execution.dispatcher import dispatch
from indexing.file_indexer import create_index, setup_index, lookup_file_multi
from indexing.watchdog_service import start_watchdog

def run_test():
    print("=== AETHER POC PIPELINE VERIFICATION RUNNER ===")
    
    db_path = str(config.DB_PATH)
    create_index(db_path)
    
    # Check if ALL_PC_ACCESS is configured
    if getattr(config, "ALL_PC_ACCESS", False):
        from main import get_all_drives
        approved_folders = get_all_drives()
    else:
        downloads = str(Path(os.environ.get("USERPROFILE", "C:/Users/Default")) / "Downloads")
        approved_folders = [downloads]
        
    print(f"Initializing SQLite index for: {approved_folders}")
    setup_index(approved_folders, db_path)
    
    # Start filesystem watcher daemon
    print("Starting watchdog observer...")
    watchdog = start_watchdog(approved_folders, db_path)
    
    # Launch local Qwen2.5 LLM server
    print("Starting local llama-server sidecar...")
    if not start_sidecar_server():
        print("ERROR: Failed to launch local LLM sidecar server.")
        watchdog.stop()
        watchdog.join()
        return
        
    try:
        # Predefined test queries representing low, medium, and high risk profiles
        queries = [
            "open chrome browser",
            "set volume to 65",
            "create folder Work",
            "append text hello world to notes.txt",
            "delete file budget_old.xlsx"
        ]
        
        for q in queries:
            print("\n" + "=" * 60)
            print(f"QUERY UNDER TEST: '{q}'")
            print("=" * 60)
            
            # Step 1: Query Pre-processing
            pq = preprocess(q)
            print(f"1. Preprocessed: '{pq}'")
            
            # Step 2: SQLite Index lookup
            if is_file_related(pq):
                print("2. SQLite Lookup:")
                matches = lookup_file_multi(pq, db_path, limit=2)
                if matches:
                    for m in matches:
                        print(f"   - {m['file_name']} (Access: {'Allowed' if m['have_access'] == 1 else 'Denied'})")
                else:
                    print("   - No matching files in index.")
            else:
                print("2. SQLite Lookup: Skipped (Non-file query)")
                
            # Step 3: FAISS Semantic Selection
            sel = select_tool(pq)
            tool = sel["selected_tool"]
            score = sel["score"]
            print(f"3. Matched Tool: '{tool}' (Confidence: {score:.2f})")
            
            if not tool or score < 0.40:
                print("   Skipped: Score below threshold (0.40).")
                continue
                
            # Step 4: Parameter Extraction via llama-server
            print("4. Parameter Extraction:")
            ext = extract_parameters(tool, pq)
            if not ext["success"]:
                print(f"   Extraction failed: {ext['error']}")
                continue
            params = ext["parameters"]
            print(f"   Extracted arguments: {params}")
            
            # Step 5: Safety Classification
            level = get_risk_level(tool)
            print(f"5. Safety check: Risk category is {level.upper()}.")
            
            # Step 6: Command Dispatching
            # Note: Skip manual CLI input prompt for automated tests
            if level == "high":
                print("   [Test Mode] Auto-confirming high risk action.")
                
            print("6. Dispatching Execution:")
            res = dispatch(tool, params)
            print(f"   Status: {'SUCCESS' if res['success'] else 'FAILURE'}")
            print(f"   Output: {res['output']}")
            print(f"   Error: {res['error']}")
            
    finally:
        # Gracefully release system hooks
        print("\nReleasing system resources...")
        if watchdog:
            watchdog.stop()
            watchdog.join()
        stop_sidecar_server()
        print("Verification completed.")

if __name__ == "__main__":
    run_test()
