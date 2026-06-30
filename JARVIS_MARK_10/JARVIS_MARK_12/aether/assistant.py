"""
assistant.py

Orchestrates the hierarchical AI pipeline for Aether:
1. Category Selection
2. Candidate Tool Retrieval
3. Action Planning with validation/repair loop
4. Sequential Execution
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List

# New pipeline steps
from aether.registry.tools import get_tools_by_category, list_tools
from aether.llm.category_selector import select_categories
from aether.llm.action_planner import plan_actions
from aether.llm.query_normalizer import normalize_query
from aether.llm.category_engine import CategoryEngine
from aether.validation.rule_validator import validate_plan_steps, map_arguments_to_schema_fields
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

def map_planner_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Maps optimized parameter names back to original names for backward compatibility."""
    mapped = {}
    for k, v in parameters.items():
        if k == "source_path":
            mapped["source"] = v
        elif k == "destination_path":
            mapped["destination"] = v
        elif k == "file_path":
            mapped["filename"] = v
        elif k == "clipboard_text":
            mapped["text"] = v
        elif k == "directory_path":
            mapped["path"] = v
        elif k == "source_paths":
            mapped["sources"] = v
        elif k == "output_path":
            mapped["output"] = v
        elif k == "archive_path":
            mapped["archive"] = v
        else:
            mapped[k] = v
    return mapped

def run_query(query: str) -> Dict[str, Any]:
    """
    Executes a natural language query through the hierarchical Aether assistant pipeline:
    User Query -> Query Normalizer -> Qwen2.5-3B Router -> Python Category Engine ->
    Qwen3-7B-Instruct Planner -> Rule Validator -> Executor.
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
    steps_log = {}
    
    # Initialize fallback tracker
    import aether.tools.file_tools as ft
    ft.FALLBACK_SEARCH_TRIGGERED = False
    
    # Clean up trailing punctuation from query
    query = query.strip()
    if query.endswith(".") and not query.endswith("..") and len(query) > 1:
        query = query[:-1].strip()
    query = query.rstrip("?!").strip()
    
    try:
        # Logging stage: User Query
        logger.info(f"User Query: {query}")
        
        # Preprocessing: Query Normalizer
        normalized_query = normalize_query(query)
        logger.info(f"Normalized Query: {normalized_query}")
        steps_log["normalized_query"] = normalized_query
        
        # Step 1: Router Stage (Qwen2.5-3B)
        cat_start = time.perf_counter()
        router_output = select_categories(normalized_query)
        metrics["intent_time"] = time.perf_counter() - cat_start
        logger.info(f"Router Output: {router_output}")
        steps_log["router_output"] = router_output
        
        categories = router_output.get("categories", [])
        intent = router_output.get("intent", "unknown")
        complexity = router_output.get("complexity", "single_step")
        
        # Step 2: Deterministic Python Category Engine
        logger.info(f"Expanded Categories: {categories}")
        candidate_tools = CategoryEngine.get_candidate_tools(normalized_query, categories)
        logger.info(f"Candidate Tools: {candidate_tools}")
        steps_log["candidate_tools"] = candidate_tools
        
        # Step 3: Planner Stage (Qwen3-7B-Instruct)
        planner_start = time.perf_counter()
        planned_steps = plan_actions(query, normalized_query, candidate_tools)
        metrics["param_time"] = time.perf_counter() - planner_start
        logger.info(f"Planner Output: {planned_steps}")
        steps_log["planner_output"] = planned_steps
        
        # Step 4: Python Rule Validator (Non-LLM)
        val_start = time.perf_counter()
        is_valid, validation_errors = validate_plan_steps(planned_steps)
        metrics["validation_time"] = time.perf_counter() - val_start
        logger.info(f"Validation Result: Valid={is_valid}, Errors={validation_errors}")
        steps_log["validation_result"] = {
            "success": is_valid,
            "errors": validation_errors
        }
        
        if not is_valid:
            metrics["total_time"] = time.perf_counter() - total_start
            metrics["execution_status"] = "Failed"
            return {
                "success": False,
                "error": f"Rule validation failed: {validation_errors}",
                "steps": steps_log,
                "output": "Plan validation failed.",
                "metrics": metrics
            }
            
        # Step 5: Execute actions sequentially
        execution_outputs = []
        exec_start_total = time.perf_counter()
        
        for step in planned_steps:
            tool = step["tool"]
            arguments = step["arguments"]
            
            # Map simplified parameters to schema-compliant fields
            mapped_schema_args = map_arguments_to_schema_fields(tool, arguments)
            
            # Map schema parameters for execution backward compatibility
            mapped_params = map_planner_parameters(mapped_schema_args)
            
            # Clean up trailing sentence punctuation and colloquial words
            cleanable_keys = {"filename", "folder_name", "source", "destination", "archive", "app_name", "path"}
            colloquial_suffixes = [" file", " folder", " directory", " app", " application"]
            for k, v in mapped_params.items():
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
                    mapped_params[k] = val_clean.strip()
                    
            # Resolve file extensions from query context if create_file
            if tool == "create_file" and "filename" in mapped_params:
                filename = mapped_params["filename"]
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
                        mapped_params["filename"] = filename + found_ext
                        logger.info(f"Auto-appended extension '{found_ext}' to filename '{filename}'.")
 
            # Resolve special folders and handle clarifications
            mapped_params = resolve_special_folders(tool, mapped_params)
            mapped_params, p_success = handle_missing_parameters(tool, mapped_params, metrics)
            if not p_success:
                metrics["execution_time"] = time.perf_counter() - exec_start_total
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["clarification"] = "Aborted"
                metrics["execution_status"] = "Deferred"
                return {
                    "success": False,
                    "error": "Required parameter was omitted by user.",
                    "steps": steps_log,
                    "output": "Operation aborted: Missing required parameter.",
                    "metrics": metrics
                }
                
            mapped_params = resolve_special_folders(tool, mapped_params)
            
            if needs_safety_confirmation(tool):
                confirmed = ask_user_confirmation(tool, mapped_params)
                if not confirmed:
                    metrics["execution_time"] = time.perf_counter() - exec_start_total
                    metrics["total_time"] = time.perf_counter() - total_start
                    metrics["execution_status"] = "Deferred"
                    return {
                        "success": False,
                        "error": "Safety Confirmation Denied",
                        "steps": steps_log,
                        "output": "Operation cancelled: Safety confirmation was not granted.",
                        "metrics": metrics
                    }
                if tool == "send_email":
                    mapped_params["confirmed"] = True
                    
            # Execute tool
            exec_success, exec_output = execute_tool(tool, mapped_params)
            if not exec_success:
                metrics["execution_time"] = time.perf_counter() - exec_start_total
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Failed"
                return {
                    "success": False,
                    "error": exec_output,
                    "steps": steps_log,
                    "output": f"Failed executing {tool}: {exec_output}",
                    "metrics": metrics
                }
            execution_outputs.append(exec_output)
            
        metrics["execution_time"] = time.perf_counter() - exec_start_total
        metrics["total_time"] = time.perf_counter() - total_start
        metrics["execution_status"] = "Executed"
        
        # Check fallback
        if ft.FALLBACK_SEARCH_TRIGGERED:
            metrics["fallback"] = "Succeeded"
            
        # Log diagnostics
        logger.info(f"=== AETHER DIAGNOSTICS ===")
        logger.info(f"User Query                 : {query}")
        logger.info(f"Normalized Query           : {normalized_query}")
        logger.info(f"Router Selected Categories : {categories}")
        logger.info(f"Retrieved Candidate Tools  : {candidate_tools}")
        logger.info(f"Router latency             : {metrics['intent_time']:.4f}s")
        logger.info(f"Action planner latency     : {metrics['param_time']:.4f}s")
        logger.info(f"Validator latency          : {metrics['validation_time']:.4f}s")
        logger.info(f"Execution latency          : {metrics['execution_time']:.4f}s")
        
        # Add detailed planner diagnostics from PlannedStepsList if present
        diagnostics = getattr(planned_steps, "diagnostics", {})
        if diagnostics:
            logger.info(f"Planner Prompt Tokens      : {diagnostics.get('Planner Prompt Tokens', 0)}")
            logger.info(f"Planner Completion Tokens  : {diagnostics.get('Planner Completion Tokens', 0)}")
            logger.info(f"Generation Time            : {diagnostics.get('Generation Time', '0.0000s')}")
            logger.info(f"Parsing Time               : {diagnostics.get('Parsing Time', '0.0000s')}")
            logger.info(f"Validation Time            : {metrics['validation_time']:.4f}s")
            logger.info(f"JSON Extraction Time       : {diagnostics.get('JSON Extraction Time', '0.0000s')}")
            logger.info(f"Fallback Triggered (Yes/No): {diagnostics.get('Fallback Triggered (Yes/No)', 'No')}")
            logger.info(f"Failure Reason             : {diagnostics.get('Failure Reason', 'None')}")
        logger.info(f"==========================")
        
        combined_output = " | ".join(str(o) for o in execution_outputs)
        logger.info(f"Execution Result: {combined_output}")
        steps_log["execution_result"] = combined_output
        return {
            "success": True,
            "error": None,
            "steps": steps_log,
            "output": combined_output,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.exception(f"Exception occurred in assistant pipeline: {e}")
        metrics["total_time"] = time.perf_counter() - total_start
        metrics["execution_status"] = "Failed"
        return {
            "success": False,
            "error": str(e),
            "steps": steps_log,
            "output": f"Pipeline error: {e}",
            "metrics": metrics
        }
