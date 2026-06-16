import os
import sys

# Add current folder to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import DEMO_DIR, DUMMY_FILES
from tool_selector import ToolSelector
from file_index.sqlite_index import reindex_all as sqlite_reindex
from file_index.faiss_index import rebuild_file_index as faiss_reindex
from file_index.watcher import start_watcher

# Import tools
from tools.open_app import OpenAppTool
from tools.search_files import SearchFilesTool
from tools.delete_file import DeleteFileTool
from tools.set_volume import SetVolumeTool
from tools.get_system_info import GetSystemInfoTool
from tools.create_file import CreateFileTool
from tools.move_file import MoveFileTool

def main():
    # 1. Print startup message
    print("Aether starting...")
    
    # 2. Load spaCy model
    print("Loading NLP parsing model (spaCy)...")
    from extraction.spacy_extractor import get_nlp
    get_nlp()
    
    # 3. Load BGE Small embedding model
    print("Loading semantic embedding model (BGE Small)...")
    from tool_selector import get_embedding_model
    get_embedding_model()
    
    # 4. Register all 7 tools
    print("Registering tools...")
    tools_list = [
        OpenAppTool(),
        SearchFilesTool(),
        DeleteFileTool(),
        SetVolumeTool(),
        GetSystemInfoTool(),
        CreateFileTool(),
        MoveFileTool()
    ]
    
    # 5. Embed all tool example queries and build tool selector FAISS index
    print("Building tool semantic index...")
    tool_selector = ToolSelector(tools_list)
    
    # 6. Create ~/Desktop/AetherDemo/ if not exists
    print(f"Provisioning demo directory: {DEMO_DIR}")
    os.makedirs(DEMO_DIR, exist_ok=True)
    
    # 7. Populate with dummy files if empty
    # We check if folder has files (excluding hidden ones)
    existing_files = [f for f in os.listdir(DEMO_DIR) if not f.startswith(".")]
    if not existing_files:
        print("Populating demo folder with dummy files...")
        for filename, content in DUMMY_FILES.items():
            filepath = os.path.join(DEMO_DIR, filename)
            try:
                # Open with encoding for text, write contents
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"Error creating dummy file {filename}: {e}")
                
    # 8. Build SQLite FTS5 index from demo folder
    print("Indexing files in SQLite FTS5 index...")
    sqlite_reindex()
    
    # 9. Build FAISS semantic file index from demo folder
    print("Indexing files in semantic FAISS index...")
    faiss_reindex()
    
    # 10. Start Watchdog observer on demo folder
    print("Starting filesystem monitoring...")
    watcher_observer = start_watcher()
    
    # 11. Print ready message
    print("\nReady. Type your command (or 'quit' to exit):")
    
    # CLI loop
    while True:
        try:
            # Print prompt and read user input
            query = input("> ").strip()
            
            # On empty input: re-prompt
            if not query:
                continue
                
            # On exit commands: cleanup and exit
            if query.lower() in ("quit", "exit"):
                print("Shutting down filesystem watcher...")
                watcher_observer.stop()
                watcher_observer.join()
                print("Goodbye!")
                break
                
            # Query similarity match
            matched_tool, score = tool_selector.find(query)
            
            # Check confidence threshold (0.35)
            if score < 0.35:
                print("I didn't understand that. Try: 'open chrome', 'find my resume', 'check CPU usage'")
            else:
                # Run matched tool (orchestrates extraction -> validation -> confirmation -> execution)
                result = matched_tool.run(query)
                print(result)
                
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nShutting down filesystem watcher...")
            watcher_observer.stop()
            watcher_observer.join()
            print("Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
