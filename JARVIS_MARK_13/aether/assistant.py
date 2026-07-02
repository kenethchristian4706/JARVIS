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
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from aether.platforms import platform

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
from aether.api.events import EventManager
from aether.api.prompt import prompt_user_sync

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
    """Prompts the user via prompt_user_sync for missing parameters instead of failing."""
    
    # 1. create_file location clarification
    if tool_name == "create_file":
        filename = parameters.get("filename")
        if not filename:
            filename = prompt_user_sync("Enter name of the file to create:", [])
            if not filename:
                return parameters, False
            parameters["filename"] = filename
            metrics["clarification"] = "Required"
            
        location = parameters.get("location")
        is_resolved = location and (location.startswith("_USE_EXISTING_:") or location.startswith("_ALREADY_OPENED_:") or "?create_another=true" in location)
        if not is_resolved:
            # Check for existing duplicate files first
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 0", (filename,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                title = f"A file named '{filename}' already exists. What would you like to do?"
                options = ["Choose Existing", "Open Existing", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options)
                try:
                    choice_int = int(choice)
                except ValueError:
                    choice_int = -1
                    for idx_opt, opt in enumerate(options, 1):
                        if choice.lower() in opt.lower():
                            choice_int = idx_opt
                            break
                
                if choice_int == 1 or (isinstance(choice, str) and "choose" in choice.lower()):
                    options_sub = []
                    for r in rows:
                        loc = r["relative_location"]
                        suffix = f" ({loc})" if loc else ""
                        options_sub.append(f"{r['absolute_path']}{suffix}")
                    choice_sub = prompt_user_sync("Select which existing file to use:", options_sub)
                    try:
                        choice_idx = int(choice_sub) - 1
                    except ValueError:
                        choice_idx = -1
                        for idx_opt, opt in enumerate(options_sub, 1):
                            if choice_sub.lower() in opt.lower():
                                choice_idx = idx_opt - 1
                                break
                    if 0 <= choice_idx < len(rows):
                        dest = rows[choice_idx]["absolute_path"]
                        parameters["location"] = f"_USE_EXISTING_:{dest}"
                        return parameters, True
                    else:
                        return parameters, False
                        
                elif choice_int == 2 or (isinstance(choice, str) and "open" in choice.lower()):
                    options_sub = []
                    for r in rows:
                        loc = r["relative_location"]
                        suffix = f" ({loc})" if loc else ""
                        options_sub.append(f"{r['absolute_path']}{suffix}")
                    choice_sub = prompt_user_sync("Select which existing file to open:", options_sub)
                    try:
                        choice_idx = int(choice_sub) - 1
                    except ValueError:
                        choice_idx = -1
                        for idx_opt, opt in enumerate(options_sub, 1):
                            if choice_sub.lower() in opt.lower():
                                choice_idx = idx_opt - 1
                                break
                    if 0 <= choice_idx < len(rows):
                        dest = rows[choice_idx]["absolute_path"]
                        platform.file.open_file(str(dest))
                        parameters["location"] = f"_ALREADY_OPENED_:{dest}"
                        return parameters, True
                    else:
                        return parameters, False
                        
                elif choice_int == 3 or (isinstance(choice, str) and "create another" in choice.lower()):
                    pass
                else:
                    return parameters, False
            
            metrics["clarification"] = "Required"
            title = f"Where would you like me to create file '{filename}'?"
            options = ["Desktop", "Documents", "Downloads", "Current Directory", "Custom Path"]
            choice = prompt_user_sync(title, options)
            if choice in ('1', 'Desktop'):
                parameters["location"] = str(SPECIAL_FOLDERS["desktop"]) + "?create_another=true"
            elif choice in ('2', 'Documents'):
                parameters["location"] = str(SPECIAL_FOLDERS["documents"]) + "?create_another=true"
            elif choice in ('3', 'Downloads'):
                parameters["location"] = str(SPECIAL_FOLDERS["downloads"]) + "?create_another=true"
            elif choice in ('4', 'Current Directory'):
                parameters["location"] = os.getcwd() + "?create_another=true"
            elif choice in ('5', 'Custom Path'):
                custom_choice = prompt_user_sync("Enter the custom folder path to create the file in:", [])
                if not custom_choice or custom_choice.lower() in ('cancel', 'c'):
                    return parameters, False
                parameters["location"] = custom_choice.strip() + "?create_another=true"
            elif choice:
                val = choice.strip()
                if val.lower() in ('cancel', 'c'):
                    return parameters, False
                parameters["location"] = val + "?create_another=true"
            else:
                return parameters, False

    # 2. create_folder location clarification
    elif tool_name == "create_folder":
        folder_name = parameters.get("folder_name")
        if not folder_name:
            folder_name = prompt_user_sync("Enter name of the folder to create:", [])
            if not folder_name:
                return parameters, False
            parameters["folder_name"] = folder_name
            metrics["clarification"] = "Required"
            
        location = parameters.get("location")
        is_resolved = location and (location.startswith("_USE_EXISTING_:") or location.startswith("_ALREADY_OPENED_:") or "?create_another=true" in location)
        if not is_resolved:
            # Check for existing duplicate folders first
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 1", (folder_name,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                title = f"A folder named '{folder_name}' already exists. What would you like to do?"
                options = ["Choose Existing", "Open Existing", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options)
                try:
                    choice_int = int(choice)
                except ValueError:
                    choice_int = -1
                    for idx_opt, opt in enumerate(options, 1):
                        if choice.lower() in opt.lower():
                            choice_int = idx_opt
                            break
                
                if choice_int == 1 or (isinstance(choice, str) and "choose" in choice.lower()):
                    options_sub = []
                    for r in rows:
                        loc = r["relative_location"]
                        suffix = f" ({loc})" if loc else ""
                        options_sub.append(f"{r['absolute_path']}{suffix}")
                    choice_sub = prompt_user_sync("Select which existing folder to use:", options_sub)
                    try:
                        choice_idx = int(choice_sub) - 1
                    except ValueError:
                        choice_idx = -1
                        for idx_opt, opt in enumerate(options_sub, 1):
                            if choice_sub.lower() in opt.lower():
                                choice_idx = idx_opt - 1
                                break
                    if 0 <= choice_idx < len(rows):
                        dest = rows[choice_idx]["absolute_path"]
                        parameters["location"] = f"_USE_EXISTING_:{dest}"
                        return parameters, True
                    else:
                        return parameters, False
                        
                elif choice_int == 2 or (isinstance(choice, str) and "open" in choice.lower()):
                    options_sub = []
                    for r in rows:
                        loc = r["relative_location"]
                        suffix = f" ({loc})" if loc else ""
                        options_sub.append(f"{r['absolute_path']}{suffix}")
                    choice_sub = prompt_user_sync("Select which existing folder to open:", options_sub)
                    try:
                        choice_idx = int(choice_sub) - 1
                    except ValueError:
                        choice_idx = -1
                        for idx_opt, opt in enumerate(options_sub, 1):
                            if choice_sub.lower() in opt.lower():
                                choice_idx = idx_opt - 1
                                break
                    if 0 <= choice_idx < len(rows):
                        dest = rows[choice_idx]["absolute_path"]
                        platform.file.open_file(str(dest))
                        parameters["location"] = f"_ALREADY_OPENED_:{dest}"
                        return parameters, True
                    else:
                        return parameters, False
                        
                elif choice_int == 3 or (isinstance(choice, str) and "create another" in choice.lower()):
                    pass
                else:
                    return parameters, False
            
            metrics["clarification"] = "Required"
            title = f"Where would you like me to create folder '{folder_name}'?"
            options = ["Desktop", "Documents", "Downloads", "Current Directory", "Custom Path"]
            choice = prompt_user_sync(title, options)
            if choice in ('1', 'Desktop'):
                parameters["location"] = str(SPECIAL_FOLDERS["desktop"]) + "?create_another=true"
            elif choice in ('2', 'Documents'):
                parameters["location"] = str(SPECIAL_FOLDERS["documents"]) + "?create_another=true"
            elif choice in ('3', 'Downloads'):
                parameters["location"] = str(SPECIAL_FOLDERS["downloads"]) + "?create_another=true"
            elif choice in ('4', 'Current Directory'):
                parameters["location"] = os.getcwd() + "?create_another=true"
            elif choice in ('5', 'Custom Path'):
                custom_choice = prompt_user_sync("Enter the custom folder path to create the folder in:", [])
                if not custom_choice or custom_choice.lower() in ('cancel', 'c'):
                    return parameters, False
                parameters["location"] = custom_choice.strip() + "?create_another=true"
            elif choice:
                val = choice.strip()
                if val.lower() in ('cancel', 'c'):
                    return parameters, False
                parameters["location"] = val + "?create_another=true"
            else:
                return parameters, False

    # 3. move_file destination clarification
    elif tool_name == "move_file":
        source = parameters.get("source")
        if not source:
            source = prompt_user_sync("Enter source file/folder to move:", [])
            if not source:
                return parameters, False
            parameters["source"] = source
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = prompt_user_sync(f"Where would you like to move '{source}'?", ["Desktop", "Documents", "Downloads"])
            if not dest or dest.lower() in ('cancel', 'c'):
                return parameters, False
            parameters["destination"] = dest

    # 4. copy_file destination clarification
    elif tool_name == "copy_file":
        source = parameters.get("source")
        if not source:
            source = prompt_user_sync("Enter source file to copy:", [])
            if not source:
                return parameters, False
            parameters["source"] = source
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = prompt_user_sync(f"Where would you like to copy '{source}'?", ["Desktop", "Documents", "Downloads"])
            if not dest or dest.lower() in ('cancel', 'c'):
                return parameters, False
            parameters["destination"] = dest

    # 5. extract_archive destination clarification
    elif tool_name == "extract_archive":
        archive = parameters.get("archive")
        if not archive:
            archive = prompt_user_sync("Enter zip archive path:", [])
            if not archive:
                return parameters, False
            parameters["archive"] = archive
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = prompt_user_sync(f"Where should I extract '{archive}'?", ["Desktop", "Documents", "Downloads"])
            if not dest or dest.lower() in ('cancel', 'c'):
                return parameters, False
            parameters["destination"] = dest

    # 6. download_file destination clarification
    elif tool_name == "download_file":
        url = parameters.get("url")
        if not url:
            url = prompt_user_sync("Enter URL to download from:", [])
            if not url:
                return parameters, False
            parameters["url"] = url
            
        dest = parameters.get("destination")
        if not dest:
            metrics["clarification"] = "Required"
            dest = prompt_user_sync("Where would you like me to save it?", ["Desktop", "Documents", "Downloads"])
            if not dest or dest.lower() in ('cancel', 'c'):
                return parameters, False
            parameters["destination"] = dest

    # 6.5. write_file clarification
    elif tool_name == "write_file":
        path_val = parameters.get("path")
        if not path_val:
            metrics["clarification"] = "Required"
            path_val = prompt_user_sync("Enter name of the file to write:", [])
            if not path_val:
                return parameters, False
            parameters["path"] = path_val
            
        p = Path(parameters["path"])
        if not p.is_absolute() and len(p.parts) <= 1:
            metrics["clarification"] = "Required"
            filename = p.name
            title = f"Where would you like me to save file '{filename}'?"
            options = ["Desktop", "Documents", "Downloads", "Current Directory", "Custom Path"]
            choice = prompt_user_sync(title, options)
            
            dest_dir = None
            if choice in ('1', 'Desktop'):
                dest_dir = SPECIAL_FOLDERS["desktop"]
            elif choice in ('2', 'Documents'):
                dest_dir = SPECIAL_FOLDERS["documents"]
            elif choice in ('3', 'Downloads'):
                dest_dir = SPECIAL_FOLDERS["downloads"]
            elif choice in ('4', 'Current Directory'):
                dest_dir = Path(os.getcwd())
            elif choice in ('5', 'Custom Path'):
                custom_choice = prompt_user_sync("Enter the custom folder path to save the file in:", [])
                if not custom_choice or custom_choice.lower() in ('cancel', 'c'):
                    return parameters, False
                dest_dir = Path(custom_choice.strip())
            elif choice:
                val = choice.strip()
                if val.lower() in ('cancel', 'c'):
                    return parameters, False
                dest_dir = Path(val)
            else:
                return parameters, False
                
            if dest_dir:
                parameters["path"] = str((dest_dir / filename).resolve())
                
        content = parameters.get("content")
        if content is None:
            metrics["clarification"] = "Required"
            content = prompt_user_sync("Enter the content to write to the file:", [])
            if content is None:
                return parameters, False
            parameters["content"] = content

    # 7. append_file clarification
    elif tool_name == "append_file":
        filename = parameters.get("filename")
        if not filename:
            metrics["clarification"] = "Required"
            filename = prompt_user_sync("Enter the file name to append to:", [])
            if not filename:
                return parameters, False
            parameters["filename"] = filename
            
        content = parameters.get("content")
        if not content:
            metrics["clarification"] = "Required"
            content = prompt_user_sync("Enter the content to append:", [])
            if not content:
                return parameters, False
            parameters["content"] = content

    # 8. read_file_content clarification
    elif tool_name == "read_file_content":
        file_path = parameters.get("file_path") or parameters.get("filename") or parameters.get("path")
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
                options = [file.name for file in files_in_cwd] + ["Custom Path"]
                choice = prompt_user_sync("Select a file to read:", options)
                if not choice:
                    return parameters, False
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(files_in_cwd):
                        parameters["file_path"] = str(files_in_cwd[choice_idx].resolve())
                    elif choice_idx == len(files_in_cwd):
                        cust = prompt_user_sync("Enter custom file path:", [])
                        if cust:
                            parameters["file_path"] = cust
                        else:
                            return parameters, False
                except ValueError:
                    parameters["file_path"] = choice
            else:
                file_path_input = prompt_user_sync("Enter the file path to read:", [])
                if not file_path_input:
                    return parameters, False
                parameters["file_path"] = file_path_input
        else:
            parameters["file_path"] = file_path

    # 9. compress_files output clarification
    elif tool_name == "compress_files":
        sources = parameters.get("sources")
        if not sources:
            s_singular = parameters.get("source")
            if s_singular:
                sources = [s_singular]
                parameters["sources"] = sources
            else:
                sources_str = prompt_user_sync("Enter comma-separated files or folders to compress:", [])
                if not sources_str:
                    return parameters, False
                sources = [s.strip() for s in sources_str.split(",")]
                parameters["sources"] = sources
                
        output = parameters.get("output")
        if not output or not Path(output).is_absolute():
            metrics["clarification"] = "Required"
            default_name = "Archive.zip"
            if output and not Path(output).is_dir():
                default_name = Path(output).name
            elif sources:
                try:
                    first_src = Path(sources[0]).name
                    default_name = f"{first_src}.zip" if first_src else "Archive.zip"
                except Exception:
                    pass
            
            title = f"Where would you like to save the compressed archive '{default_name}'?"
            options = ["Desktop", "Documents", "Downloads", "Current Directory", "Custom Path"]
            choice = prompt_user_sync(title, options)
            if choice in ('1', 'Desktop'):
                parameters["output"] = str(SPECIAL_FOLDERS["desktop"] / default_name)
            elif choice in ('2', 'Documents'):
                parameters["output"] = str(SPECIAL_FOLDERS["documents"] / default_name)
            elif choice in ('3', 'Downloads'):
                parameters["output"] = str(SPECIAL_FOLDERS["downloads"] / default_name)
            elif choice in ('4', 'Current Directory'):
                parameters["output"] = str(Path(os.getcwd()) / default_name)
            elif choice in ('5', 'Custom Path') or choice:
                val = choice.strip()
                if val.lower() in ('cancel', 'c'):
                    return parameters, False
                try:
                    p_val = Path(val)
                    if p_val.is_dir() or not p_val.suffix:
                        parameters["output"] = str(p_val / default_name)
                    else:
                        parameters["output"] = val
                except Exception:
                    parameters["output"] = val
            else:
                return parameters, False

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
            mapped["file_path"] = v
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

def get_step_description(tool: str, args: dict) -> str:
    """Provides a human-friendly sentence describing what a step/tool call will do."""
    if not args:
        args = {}
    if tool == "open_app":
        return f"Open {args.get('app_name', 'application')}"
    elif tool == "close_app":
        return f"Close {args.get('app_name', 'application')}"
    elif tool == "switch_to_app":
        return f"Switch to {args.get('app_name', 'application')}"
    elif tool == "move_file":
        return f"Move '{args.get('source', '')}' to '{args.get('destination', '')}'"
    elif tool == "copy_file":
        return f"Copy '{args.get('source', '')}' to '{args.get('destination', '')}'"
    elif tool == "rename_file":
        return f"Rename '{args.get('source', '')}' to '{args.get('new_name', '')}'"
    elif tool == "delete_file":
        return f"Delete file at '{args.get('path', '')}'"
    elif tool == "search_files":
        return f"Search files for '{args.get('query', '')}'"
    elif tool == "open_file":
        return f"Open file '{args.get('path', '')}'"
    elif tool == "create_file":
        return f"Create file '{args.get('filename', args.get('path', ''))}' in '{args.get('location', '')}'"
    elif tool == "create_folder":
        return f"Create folder '{args.get('folder_name', '')}' in '{args.get('location', '')}'"
    elif tool == "delete_folder":
        return f"Delete folder '{args.get('folder_name', '')}'"
    elif tool == "list_directory":
        return f"List contents of '{args.get('path', '')}'"
    elif tool == "compress_files":
        return f"Compress sources into '{args.get('output', '')}'"
    elif tool == "extract_archive":
        return f"Extract '{args.get('archive', '')}' to '{args.get('destination', '')}'"
    elif tool == "file_info":
        return f"Get details for '{args.get('path', '')}'"
    elif tool == "append_file":
        return f"Append text to '{args.get('filename', args.get('path', ''))}'"
    elif tool == "write_file":
        return f"Write text to '{args.get('path', '')}'"
    elif tool == "duplicate_file":
        return f"Duplicate file '{args.get('source_path', args.get('source', ''))}'"
    elif tool == "search_web":
        return f"Search web for '{args.get('query', '')}'"
    elif tool == "search_youtube":
        return f"Search YouTube for '{args.get('query', '')}'"
    elif tool == "open_url":
        return f"Open URL {args.get('url', '')}"
    elif tool == "download_file":
        return f"Download from '{args.get('url', '')}'"
    elif tool == "open_new_tab":
        return f"Open new browser tab at '{args.get('url', '')}'"
    elif tool == "close_tab":
        return "Close current browser tab"
    elif tool == "list_tabs":
        return "List active browser tabs"
    elif tool == "switch_tab":
        return f"Switch to browser tab {args.get('tab', '')}"
    elif tool == "shutdown_pc":
        return "Shut down PC"
    elif tool == "restart_pc":
        return "Restart PC"
    elif tool == "sleep_pc":
        return "Put PC to sleep"
    elif tool == "lock_pc":
        return "Lock PC screen"
    elif tool == "set_volume":
        return f"Set volume to {args.get('level', 0)}%"
    elif tool == "mute_volume":
        return "Mute audio volume"
    elif tool == "unmute_volume":
        return "Unmute audio volume"
    elif tool == "set_brightness":
        return f"Set brightness to {args.get('level', 0)}%"
    elif tool == "take_screenshot":
        return "Capture screen screenshot"
    elif tool == "extract_text_from_image":
        return f"Extract text from image '{args.get('path', '')}'"
    elif tool == "open_notepad_and_write":
        return "Open Notepad and type text"
    elif tool == "read_file_content":
        return f"Read contents of '{args.get('file_path', args.get('path', ''))}'"
    elif tool == "clear_clipboard":
        return "Clear clipboard contents"
    elif tool == "get_clipboard":
        return "Get current clipboard text"
    elif tool == "set_clipboard":
        return "Set clipboard text content"
    elif tool == "send_email":
        return f"Send email to '{args.get('recipient', '')}'"
    elif tool == "list_emails":
        return f"Retrieve recent emails (limit={args.get('limit', 10)})"
    elif tool == "read_email":
        return f"Read email with ID '{args.get('email_id', 'latest')}'"
    elif tool == "create_word":
        return f"Create Word document '{args.get('filename', '')}'"
    elif tool == "read_word":
        return f"Read Word document '{args.get('file_path', '')}'"
    elif tool == "edit_word":
        return f"Edit Word document '{args.get('file_path', '')}' ({args.get('operation', '')})"
    elif tool == "create_excel":
        return f"Create Excel workbook '{args.get('filename', '')}'"
    elif tool == "read_excel":
        return f"Read Excel sheet '{args.get('sheet_name', '')}' in '{args.get('file_path', '')}'"
    elif tool == "write_excel":
        return f"Write value to cell {args.get('cell', '')} in '{args.get('file_path', '')}'"
    elif tool == "cpu_usage":
        return "Check CPU usage"
    elif tool == "ram_usage":
        return "Check RAM memory usage"
    elif tool == "disk_usage":
        return "Check disk storage usage"
    elif tool == "battery_status":
        return "Check battery status"
    elif tool == "network_status":
        return "Check network connection status"
    elif tool == "list_processes":
        return f"List top processes sorted by {args.get('sort_by', 'cpu')}"
    elif tool == "get_screen_resolution":
        return "Check screen display resolution"
    return f"Execute {tool}"

async def process_query(query: str, events: Optional[EventManager] = None) -> Dict[str, Any]:
    """
    Executes a natural language query through the hierarchical Aether assistant pipeline,
    dispatching live progress updates to an EventManager.
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
        if events:
            await events.emit_thinking("Analyzing query...")
        
        # Preprocessing: Query Normalizer
        normalized_query = normalize_query(query)
        logger.info(f"Normalized Query: {normalized_query}")
        steps_log["normalized_query"] = normalized_query
        
        # Step 1: Router Stage (Qwen2.5-3B)
        if events:
            await events.emit_thinking("Selecting appropriate tool categories...")
        cat_start = time.perf_counter()
        router_output = await asyncio.to_thread(select_categories, normalized_query)
        metrics["intent_time"] = time.perf_counter() - cat_start
        logger.info(f"Router Output: {router_output}")
        steps_log["router_output"] = router_output
        
        categories = router_output.get("categories", [])
        intent = router_output.get("intent", "unknown")
        complexity = router_output.get("complexity", "single_step")
        
        if intent == "email_summary":
            if events:
                await events.emit_thinking("Generating email summary...")
            from aether.email.email_summary import EmailSummaryService
            summary_start = time.perf_counter()
            try:
                summary_result = await asyncio.to_thread(
                    EmailSummaryService.summarize,
                    router_output.get("filters", {})
                )
                metrics["execution_time"] = time.perf_counter() - summary_start
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Executed"
                if events:
                    await events.emit_final(summary_result)
                return {
                    "success": True,
                    "error": None,
                    "steps": steps_log,
                    "output": summary_result,
                    "metrics": metrics
                }
            except Exception as e:
                metrics["execution_time"] = time.perf_counter() - summary_start
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Failed"
                
                from aether.email.exceptions import EmailNotConnectedError, EmailConnectionError
                err_msg = str(e)
                if isinstance(e, EmailNotConnectedError):
                    err_msg = "No email account is connected.\nPlease connect your email in Settings."
                elif isinstance(e, EmailConnectionError):
                    err_msg = "Unable to retrieve emails."
                elif "No emails were found" in str(e):
                    err_msg = "No emails were found for the selected date."
                elif "Unable to generate summary" in str(e):
                    err_msg = "Unable to generate summary."
                
                if events:
                    await events.emit_error(err_msg)
                return {
                    "success": False,
                    "error": err_msg,
                    "steps": steps_log,
                    "output": err_msg,
                    "metrics": metrics
                }

        # Step 2: Deterministic Python Category Engine
        logger.info(f"Expanded Categories: {categories}")
        candidate_tools = CategoryEngine.get_candidate_tools(normalized_query, categories)
        logger.info(f"Candidate Tools: {candidate_tools}")
        steps_log["candidate_tools"] = candidate_tools
        
        # Step 3: Planner Stage (Qwen3-7B-Instruct)
        if events:
            await events.emit_thinking("Formulating tool execution plan...")
        planner_start = time.perf_counter()
        planned_steps = await asyncio.to_thread(plan_actions, query, normalized_query, candidate_tools)
        metrics["param_time"] = time.perf_counter() - planner_start
        logger.info(f"Planner Output: {planned_steps}")
        steps_log["planner_output"] = planned_steps
        
        # Step 4: Python Rule Validator (Non-LLM)
        val_start = time.perf_counter()
        is_valid, validation_errors = await asyncio.to_thread(validate_plan_steps, planned_steps)
        metrics["validation_time"] = time.perf_counter() - val_start
        logger.info(f"Validation Result: Valid={is_valid}, Errors={validation_errors}")
        steps_log["validation_result"] = {
            "success": is_valid,
            "errors": validation_errors
        }

        
        if not is_valid:
            metrics["total_time"] = time.perf_counter() - total_start
            metrics["execution_status"] = "Failed"
            if events:
                await events.emit_error(f"Rule validation failed: {validation_errors}")
            return {
                "success": False,
                "error": f"Rule validation failed: {validation_errors}",
                "steps": steps_log,
                "output": "Plan validation failed.",
                "metrics": metrics
            }

        # Emit visual plan step list
        if events:
            steps_desc = [get_step_description(s.get("tool"), s.get("arguments", {})) for s in planned_steps]
            await events.emit_plan(steps_desc)
            
        # Step 5: Execute actions sequentially (delegating tasks to a background thread to prevent loop blocking)
        execution_outputs = []
        exec_start_total = time.perf_counter()
        
        for step in planned_steps:
            tool = step["tool"]
            arguments = step["arguments"]
            step_desc = get_step_description(tool, arguments)
            
            if events:
                await events.emit_step_start(step_desc)
                await events.emit_tool_start(tool)
            
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
            
            # Execute clarifications inside threadpool to keep main ASGI loop alive
            mapped_params, p_success = await asyncio.to_thread(handle_missing_parameters, tool, mapped_params, metrics)
            # Clean up/remove old propagation (now done post-execution)
            pass
                                            
            if not p_success:
                metrics["execution_time"] = time.perf_counter() - exec_start_total
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["clarification"] = "Aborted"
                metrics["execution_status"] = "Deferred"
                if events:
                    await events.emit_tool_complete(tool, False)
                    await events.emit_step_complete(step_desc, False)
                    await events.emit_error("Required parameter was omitted by user.")
                return {
                    "success": False,
                    "error": "Required parameter was omitted by user.",
                    "steps": steps_log,
                    "output": "Operation aborted: Missing required parameter.",
                    "metrics": metrics
                }
                
            mapped_params = resolve_special_folders(tool, mapped_params)
            
            if needs_safety_confirmation(tool):
                # Execute confirmations inside threadpool
                confirmed = await asyncio.to_thread(ask_user_confirmation, tool, mapped_params)
                if not confirmed:
                    metrics["execution_time"] = time.perf_counter() - exec_start_total
                    metrics["total_time"] = time.perf_counter() - total_start
                    metrics["execution_status"] = "Deferred"
                    if events:
                        await events.emit_tool_complete(tool, False)
                        await events.emit_step_complete(step_desc, False)
                        await events.emit_error("Safety Confirmation Denied")
                    return {
                        "success": False,
                        "error": "Safety Confirmation Denied",
                        "steps": steps_log,
                        "output": "Operation cancelled: Safety confirmation was not granted.",
                        "metrics": metrics
                    }
                if tool == "send_email":
                    mapped_params["confirmed"] = True
                    
            # Execute tool inside threadpool
            exec_success, exec_output = await asyncio.to_thread(execute_tool, tool, mapped_params)
            if events:
                await events.emit_tool_complete(tool, exec_success)
                await events.emit_step_complete(step_desc, exec_success)
                
            if exec_success and (tool in ("create_file", "create_folder")):
                import re
                match = re.search(r"'([^']+)'", exec_output)
                if match:
                    selected_path = match.group(1)
                    name_key = "filename" if tool == "create_file" else "folder_name"
                    name_val = mapped_params.get(name_key)
                    if name_val:
                        # Propagate selected_path to subsequent steps in planned_steps
                        for subsequent_step in planned_steps[planned_steps.index(step) + 1:]:
                            sub_args = subsequent_step.get("arguments", {})
                            for sub_k, sub_v in sub_args.items():
                                if isinstance(sub_v, str):
                                    if sub_v == name_val:
                                        sub_args[sub_k] = selected_path
                                    elif sub_v.replace("\\", "/").startswith(name_val + "/"):
                                        rel_part = sub_v[len(name_val):].lstrip("/\\")
                                        sub_args[sub_k] = str(Path(selected_path) / rel_part)
                                elif isinstance(sub_v, list):
                                    for idx_v, item in enumerate(sub_v):
                                        if isinstance(item, str):
                                            if item == name_val:
                                                sub_v[idx_v] = selected_path
                                            elif item.replace("\\", "/").startswith(name_val + "/"):
                                                rel_part = item[len(name_val):].lstrip("/\\")
                                                sub_v[idx_v] = str(Path(selected_path) / rel_part)
                
            if not exec_success:
                metrics["execution_time"] = time.perf_counter() - exec_start_total
                metrics["total_time"] = time.perf_counter() - total_start
                metrics["execution_status"] = "Failed"
                
                error_code = None
                if "EMAIL_NOT_CONNECTED" in exec_output:
                    error_code = "EMAIL_NOT_CONNECTED"
                    
                if events:
                    await events.emit_error(f"Failed executing {tool}: {exec_output}", error_code=error_code)
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
        if events:
            await events.emit_final(combined_output)
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
        if events:
            await events.emit_error(str(e))
        return {
            "success": False,
            "error": str(e),
            "steps": steps_log,
            "output": f"Pipeline error: {e}",
            "metrics": metrics
        }

def run_query(query: str) -> Dict[str, Any]:
    """Sync wrapper for process_query to preserve backward compatibility for CLI."""
    return asyncio.run(process_query(query))
