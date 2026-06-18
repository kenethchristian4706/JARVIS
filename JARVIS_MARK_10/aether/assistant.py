"""
assistant.py

Orchestrates the hierarchical AI pipeline for Aether:
1. Intent Selection (Unified Category + Tool Selection in a single LLM request)
2. Parameter Extraction (Rule-based or fallback to LLM)
3. Special Folder Resolution
4. Missing Parameters Clarification Prompting
5. Validation (Pydantic schema constraints + existence checks)
6. Safety & Confirmation Gates
7. Execution
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

# Pipeline steps
from aether.llm.intent_selector import select_intent
from aether.llm.parameter_extractor import extract_parameters
from aether.validation.schema_validator import validate_parameters
from aether.validation.safety_checker import needs_safety_confirmation, ask_user_confirmation
from aether.executor.executor import execute_tool

logger = logging.getLogger(__name__)

SPECIAL_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
    "music": Path.home() / "Music"
}

def resolve_special_folders(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves colloquial special folder names to absolute paths for specified tools."""
    target_tools = {"list_directory", "create_file", "create_folder", "move_file", "copy_file", "extract_archive", "take_screenshot"}
    if tool_name not in target_tools:
        return parameters
        
    resolved = {}
    for k, v in parameters.items():
        if isinstance(v, str):
            val_lower = v.lower().strip()
            if val_lower in SPECIAL_FOLDERS:
                resolved[k] = str(SPECIAL_FOLDERS[val_lower].resolve())
            else:
                resolved[k] = v
        else:
            resolved[k] = v
    return resolved

def handle_missing_parameters(tool_name: str, parameters: Dict[str, Any], metrics: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Prompts the user via console input for missing parameters instead of failing."""
    
    # 1. create_file location clarification
    if tool_name == "create_file":
        filename = parameters.get("filename")
        if not filename:
            filename = input("Enter name of the file to create: ").strip()
            if not filename:
                return parameters, False
            parameters["filename"] = filename
            metrics["clarification"] = "Required"
            
        location = parameters.get("location")
        if not location:
            # Check for existing duplicate files first
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 0", (filename,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                print(f"\nA file named '{filename}' already exists:")
                for idx, r in enumerate(rows, 1):
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    print(f"  {idx}. {r['absolute_path']}{suffix}")
                print("\nWhat would you like to do?")
                print("  1. Open Existing")
                print("  2. Create Another")
                print("  3. Cancel")
                
                while True:
                    choice = input("Enter selection (1-3): ").strip()
                    if choice == '1':
                        import os
                        from pathlib import Path
                        from aether.tools.file_tools import resolve_filename
                        if len(rows) == 1:
                            dest = Path(rows[0]["absolute_path"])
                        else:
                            dest = resolve_filename(filename, is_directory=False)
                        os.startfile(str(dest))
                        parameters["location"] = f"_ALREADY_OPENED_:{dest}"
                        return parameters, True
                    elif choice == '2':
                        break
                    elif choice == '3':
                        return parameters, False
                    print("Invalid selection. Please enter 1, 2, or 3.")
            
            metrics["clarification"] = "Required"
            print(f"\nWhere would you like me to create {filename}?")
            print("  1. Desktop")
            print("  2. Documents")
            print("  3. Downloads")
            print("  4. Current Directory")
            print("  5. Custom Path")
            while True:
                choice = input("Enter choice (1-5): ").strip()
                if choice == '1':
                    parameters["location"] = str(SPECIAL_FOLDERS["desktop"]) + "?create_another=true"
                    break
                elif choice == '2':
                    parameters["location"] = str(SPECIAL_FOLDERS["documents"]) + "?create_another=true"
                    break
                elif choice == '3':
                    parameters["location"] = str(SPECIAL_FOLDERS["downloads"]) + "?create_another=true"
                    break
                elif choice == '4':
                    parameters["location"] = os.getcwd() + "?create_another=true"
                    break
                elif choice == '5':
                    cust = input("Enter custom path: ").strip()
                    if cust:
                        parameters["location"] = cust + "?create_another=true"
                        break
                print("Invalid choice. Please enter 1-5.")

    # 2. create_folder location clarification
    elif tool_name == "create_folder":
        folder_name = parameters.get("folder_name")
        if not folder_name:
            folder_name = input("Enter name of the folder to create: ").strip()
            if not folder_name:
                return parameters, False
            parameters["folder_name"] = folder_name
            metrics["clarification"] = "Required"
            
        location = parameters.get("location")
        if not location:
            # Check for existing duplicate folders first
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 1", (folder_name,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                print(f"\nA folder named '{folder_name}' already exists:")
                for idx, r in enumerate(rows, 1):
                    loc = r["relative_location"]
                    suffix = f" ({loc})" if loc else ""
                    print(f"  {idx}. {r['absolute_path']}{suffix}")
                print("\nWhat would you like to do?")
                print("  1. Open Existing")
                print("  2. Create Another")
                print("  3. Cancel")
                
                while True:
                    choice = input("Enter selection (1-3): ").strip()
                    if choice == '1':
                        import os
                        from pathlib import Path
                        from aether.tools.file_tools import resolve_filename
                        if len(rows) == 1:
                            dest = Path(rows[0]["absolute_path"])
                        else:
                            dest = resolve_filename(folder_name, is_directory=True)
                        os.startfile(str(dest))
                        parameters["location"] = f"_ALREADY_OPENED_:{dest}"
                        return parameters, True
                    elif choice == '2':
                        break
                    elif choice == '3':
                        return parameters, False
                    print("Invalid selection. Please enter 1, 2, or 3.")
            
            metrics["clarification"] = "Required"
            print(f"\nWhere would you like me to create folder '{folder_name}'?")
            print("  1. Desktop")
            print("  2. Documents")
            print("  3. Downloads")
            print("  4. Current Directory")
            print("  5. Custom Path")
            while True:
                choice = input("Enter choice (1-5): ").strip()
                if choice == '1':
                    parameters["location"] = str(SPECIAL_FOLDERS["desktop"]) + "?create_another=true"
                    break
                elif choice == '2':
                    parameters["location"] = str(SPECIAL_FOLDERS["documents"]) + "?create_another=true"
                    break
                elif choice == '3':
                    parameters["location"] = str(SPECIAL_FOLDERS["downloads"]) + "?create_another=true"
                    break
                elif choice == '4':
                    parameters["location"] = os.getcwd() + "?create_another=true"
                    break
                elif choice == '5':
                    cust = input("Enter custom path: ").strip()
                    if cust:
                        parameters["location"] = cust + "?create_another=true"
                        break
                print("Invalid choice. Please enter 1-5.")

    # 3. move_file destination clarification
    elif tool_name == "move_file":
        source = parameters.get("source")
        if not source:
            source = input("Enter source file/folder to move: ").strip()
            if not source:
                return parameters, False
            parameters["source"] = source
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = input(f"Where would you like to move {source}? ").strip()
            if not dest:
                return parameters, False
            parameters["destination"] = dest

    # 4. copy_file destination clarification
    elif tool_name == "copy_file":
        source = parameters.get("source")
        if not source:
            source = input("Enter source file to copy: ").strip()
            if not source:
                return parameters, False
            parameters["source"] = source
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = input(f"Where would you like to copy {source}? ").strip()
            if not dest:
                return parameters, False
            parameters["destination"] = dest

    # 5. extract_archive destination clarification
    elif tool_name == "extract_archive":
        archive = parameters.get("archive")
        if not archive:
            archive = input("Enter zip archive path: ").strip()
            if not archive:
                return parameters, False
            parameters["archive"] = archive
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = input(f"Where should I extract {archive}? ").strip()
            if not dest:
                return parameters, False
            parameters["destination"] = dest

    # 6. download_file destination clarification
    elif tool_name == "download_file":
        url = parameters.get("url")
        if not url:
            url = input("Enter URL to download from: ").strip()
            if not url:
                return parameters, False
            parameters["url"] = url
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = input("Where would you like me to save it? ").strip()
            if not dest:
                return parameters, False
            parameters["destination"] = dest

    # 7. append_file clarification
    elif tool_name == "append_file":
        filename = parameters.get("filename")
        if not filename:
            metrics["clarification"] = "Required"
            filename = input("Enter the file name to append to: ").strip()
            if not filename:
                return parameters, False
            parameters["filename"] = filename
            
        content = parameters.get("content")
        if not content:
            metrics["clarification"] = "Required"
            content = input("Enter the content to append: ").strip()
            if not content:
                return parameters, False
            parameters["content"] = content

    # 8. read_file_content clarification
    elif tool_name == "read_file_content":
        file_path = parameters.get("file_path")
        if not file_path:
            metrics["clarification"] = "Required"
            supported_extensions = {".txt", ".md", ".py", ".json", ".csv", ".log"}
            cwd = Path(os.getcwd())
            files_in_cwd = []
            try:
                for item in cwd.iterdir():
                    if item.is_file() and item.suffix.lower() in supported_extensions:
                        files_in_cwd.append(item)
            except Exception:
                pass

            if files_in_cwd:
                print("\nSelect a file to read:")
                for idx, file in enumerate(files_in_cwd, 1):
                    print(f"  {idx}. {file.name}")
                print(f"  {len(files_in_cwd) + 1}. Custom Path")

                while True:
                    choice = input(f"Enter choice (1-{len(files_in_cwd) + 1}): ").strip()
                    if not choice:
                        return parameters, False
                    try:
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(files_in_cwd):
                            parameters["file_path"] = str(files_in_cwd[choice_idx].resolve())
                            break
                        elif choice_idx == len(files_in_cwd):
                            cust = input("Enter custom file path: ").strip()
                            if cust:
                                parameters["file_path"] = cust
                                break
                            else:
                                return parameters, False
                    except ValueError:
                        parameters["file_path"] = choice
                        break
                    print(f"Invalid choice. Please enter 1-{len(files_in_cwd) + 1} or type a filename.")
            else:
                file_path = input("Enter the file path to read: ").strip()
                if not file_path:
                    return parameters, False
                parameters["file_path"] = file_path

    return parameters, True

def run_query(query: str) -> Dict[str, Any]:
    """
    Executes a natural language query through the Aether assistant pipeline.
    Tracks performance metrics for each stage.
    """
    total_start = time.perf_counter()
    metrics = {
        "intent_time": 0.0,
        "param_time": 0.0,
        "param_source": "LLM",
        "clarification": "None",
        "fallback": "None",
        "validation_time": 0.0,
        "execution_time": 0.0,
        "execution_status": "Executed",
        "total_time": 0.0
    }
    steps = {}
    
    # Initialize fallback tracker
    import aether.tools.file_tools as ft
    ft.FALLBACK_SEARCH_TRIGGERED = False
    
    # Clean up trailing punctuation from query
    query = query.strip()
    if query.endswith(".") and not query.endswith("..") and len(query) > 1:
        query = query[:-1].strip()
    query = query.rstrip("?!").strip()
    
    try:
        # Step 1: Intent Selection
        intent_start = time.perf_counter()
        category, tool = select_intent(query)
        metrics["intent_time"] = time.perf_counter() - intent_start
        steps["category"] = category
        steps["tool"] = tool
        
        # Step 2: Parameter Extraction
        param_start = time.perf_counter()
        metrics["param_source"] = "LLM"
        parameters = extract_parameters(tool, query)
        metrics["param_time"] = time.perf_counter() - param_start
        
        # Clean up trailing sentence punctuation and colloquial words (file, folder, app, etc.)
        cleanable_keys = {"filename", "folder_name", "source", "destination", "archive", "app_name", "path"}
        colloquial_suffixes = [" file", " folder", " directory", " app", " application"]
        for k, v in parameters.items():
            if k in cleanable_keys and isinstance(v, str):
                val_clean = v.strip()
                val_lower = val_clean.lower()
                for suffix in colloquial_suffixes:
                    if val_lower.endswith(suffix):
                        val_clean = val_clean[:-len(suffix)].strip()
                        val_lower = val_clean.lower()
                if val_clean.endswith(".") and not val_clean.endswith("..") and len(val_clean) > 1:
                    val_clean = val_clean.rstrip(".")
                val_clean = val_clean.rstrip("?!")
                parameters[k] = val_clean.strip()

        # Resolve file extensions from query context if omitted in parameter extraction (e.g. for create_file)
        if tool == "create_file" and "filename" in parameters:
            filename = parameters["filename"]
            if filename and not Path(filename).suffix:
                import re
                common_exts = ["ipynb", "txt", "py", "json", "csv", "log", "pdf", "docx", "xlsx", "zip", "png", "jpg", "html", "css", "js", "md"]
                extension_aliases = {
                    "python": "py",
                    "text": "txt",
                    "markdown": "md",
                    "notebook": "ipynb",
                    "jupyter": "ipynb",
                    "excel": "xlsx",
                    "word": "docx"
                }
                found_ext = None
                for ext in common_exts:
                    pattern = r"(?:\." + ext + r"\b|\b" + ext + r"\b\s*ext|\bext\w*\s*" + ext + r"\b)"
                    if re.search(pattern, query, re.IGNORECASE):
                        found_ext = "." + ext
                        break
                if not found_ext:
                    for alias, ext in extension_aliases.items():
                        if re.search(r"\b" + alias + r"\b", query, re.IGNORECASE):
                            found_ext = "." + ext
                            break
                if found_ext:
                    parameters["filename"] = filename + found_ext
                    logger.info(f"Auto-appended extension '{found_ext}' to filename '{filename}' based on query context.")
        
        # Step 2.5: Special Folder Resolution & Clarification Workflows
        parameters = resolve_special_folders(tool, parameters)
        parameters, p_success = handle_missing_parameters(tool, parameters, metrics)
        if not p_success:
            metrics["validation_time"] = 0.0
            metrics["total_time"] = time.perf_counter() - total_start
            metrics["clarification"] = "Aborted"
            metrics["execution_status"] = "Deferred"
            return {
                "success": False,
                "error": "Required parameter was omitted by user.",
                "steps": steps,
                "output": "Operation aborted: Missing required parameter.",
                "metrics": metrics
            }
        
        # Resolve folders again in case user input matches special folders (e.g. desktop)
        parameters = resolve_special_folders(tool, parameters)
        
        # Update fallback search flag from file tools
        if ft.FALLBACK_SEARCH_TRIGGERED:
            metrics["fallback"] = "Attempted"
            
        # Step 3: Schema Validation
        val_start = time.perf_counter()
        success, validated_params, error = validate_parameters(tool, parameters)
        
        if not success:
            logger.warning(f"Parameter validation failed: {error}. Retrying extraction once...")
            if metrics["param_source"] == "LLM":
                parameters = extract_parameters(tool, query)
                parameters = resolve_special_folders(tool, parameters)
                parameters, _ = handle_missing_parameters(tool, parameters, metrics)
                success, validated_params, error = validate_parameters(tool, parameters)
            
            if not success:
                metrics["validation_time"] = time.perf_counter() - val_start
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Failed"
                return {
                    "success": False,
                    "error": f"Parameter validation failed: {error}",
                    "steps": steps,
                    "output": "",
                    "metrics": metrics
                }
                
        metrics["validation_time"] = time.perf_counter() - val_start
        steps["parameters"] = validated_params
        
        # Step 4: Safety Check Gate
        if needs_safety_confirmation(tool):
            confirmed = ask_user_confirmation(tool, validated_params)
            if not confirmed:
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Deferred"
                return {
                    "success": False,
                    "error": "Safety Confirmation Denied",
                    "steps": steps,
                    "output": "Operation cancelled: Safety confirmation was not granted.",
                    "metrics": metrics
                }
            if tool == "send_email":
                validated_params["confirmed"] = True

                
        # Step 5: Execute Tool
        exec_start = time.perf_counter()
        exec_success, exec_output = execute_tool(tool, validated_params)
        metrics["execution_time"] = time.perf_counter() - exec_start
        
        # Check for fallback and execution status
        if ft.FALLBACK_SEARCH_TRIGGERED:
            metrics["fallback"] = "Succeeded" if exec_success else "Failed"
        if exec_success and "(Deferred creation)" in str(exec_output):
            metrics["execution_status"] = "Deferred"
        else:
            metrics["execution_status"] = "Executed" if exec_success else "Failed"
            
        metrics["total_time"] = time.perf_counter() - total_start
        return {
            "success": exec_success,
            "error": None if exec_success else exec_output,
            "steps": steps,
            "output": exec_output,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.exception(f"Exception occurred in assistant pipeline: {e}")
        metrics["total_time"] = time.perf_counter() - total_start
        metrics["execution_status"] = "Failed"
        return {
            "success": False,
            "error": str(e),
            "steps": steps,
            "output": f"Pipeline error: {e}",
            "metrics": metrics
        }
