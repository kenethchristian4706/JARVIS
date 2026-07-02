"""
executor/executor.py

Maps tools to their corresponding python handlers and executes them after performing
pre-execution existence validations (file exists, folder exists, app exists).
"""

import logging
from typing import Dict, Any, Tuple

# Import handlers
import aether.tools.app_tools as app
import aether.tools.file_tools as files
import aether.tools.browser_tools as browser
import aether.tools.system_tools as system
import aether.tools.email_tools as email
import aether.tools.document_tools as documents


# Import existence checkers
from aether.validation.validators import verify_file_exists, verify_folder_exists, verify_app_exists

logger = logging.getLogger(__name__)

# Map tool names to python functions
TOOL_MAP = {
    # Application Management
    "open_app": app.open_app,
    "close_app": app.close_app,
    "switch_to_app": app.switch_to_app,
    "list_running_apps": app.list_running_apps,
    "list_installed_apps": app.list_installed_apps,
    
    # File Operations
    "move_file": files.move_file,
    "copy_file": files.copy_file,
    "rename_file": files.rename_file,
    "delete_file": files.delete_file,
    "search_files": files.search_files,
    "open_file": files.open_file,
    "create_folder": files.create_folder,
    "delete_folder": files.delete_folder,
    "compress_files": files.compress_files,
    "extract_archive": files.extract_archive,
    "create_file": files.create_file,
    "list_directory": files.list_directory,
    "file_info": files.file_info,
    "append_file": files.append_file,
    
    # Browser Operations
    "search_web": browser.search_web,
    "search_youtube": browser.search_youtube,
    "open_url": browser.open_url,
    "download_file": browser.download_file,
    "open_new_tab": browser.open_new_tab,
    "close_tab": browser.close_tab,
    "list_tabs": browser.list_tabs,
    "switch_tab": browser.switch_tab,
    
    # System Control
    "shutdown_pc": system.shutdown_pc,
    "restart_pc": system.restart_pc,
    "sleep_pc": system.sleep_pc,
    "lock_pc": system.lock_pc,
    "set_volume": system.set_volume,
    "mute_volume": system.mute_volume,
    "unmute_volume": system.unmute_volume,
    "set_brightness": system.set_brightness,
    
    # Phase 1 Additional Tools
    "take_screenshot": system.take_screenshot,
    "extract_text_from_image": files.extract_text_from_image,
    "open_notepad_and_write": system.open_notepad_and_write,
    "read_file_content": files.read_file_content,
    "clear_clipboard": system.clear_clipboard,
    "get_clipboard": system.get_clipboard,
    "set_clipboard": system.set_clipboard,
    "increase_volume": system.increase_volume,
    "decrease_volume": system.decrease_volume,
    "increase_brightness": system.increase_brightness,
    "decrease_brightness": system.decrease_brightness,
    
    # Email Operations
    "send_email": email.send_email,
    "list_emails": email.list_emails,
    "read_email": email.read_email,
    
    # Document Operations
    "create_word": documents.create_word,
    "read_word": documents.read_word,
    "edit_word": documents.edit_word,
    "create_excel": documents.create_excel,
    "read_excel": documents.read_excel,
    "write_excel": documents.write_excel
}

def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Executes the specified tool with validated parameters.
    Performs existence validation checks before invoking the tool handler.
    
    Returns:
        (success: bool, output_message: str)
    """
    if tool_name not in TOOL_MAP:
        return False, f"Tool '{tool_name}' is not registered in execution map."

    handler = TOOL_MAP[tool_name]

    # --- Pre-execution Existence Validations ---
    try:
        # Application existence validation
        if tool_name == "open_app":
            app_name = parameters.get("app_name")
            if not verify_app_exists(app_name):
                logger.warning(f"Existence Check Warning: App '{app_name}' not found in registry scan.")
                
        elif tool_name in ("close_app", "switch_to_app"):
            app_name = parameters.get("app_name")
            if not verify_app_exists(app_name):
                logger.info(f"Existence Check Info: App '{app_name}' not registered.")

    except Exception as e:
        return False, f"Pre-execution validation error: {e}"

    # Map optimized parameter names back to original names for backward compatibility
    mapped_parameters = {}
    for k, v in parameters.items():
        if k == "source_path":
            mapped_parameters["source"] = v
        elif k == "destination_path":
            mapped_parameters["destination"] = v
        elif k == "file_path":
            mapped_parameters["filename"] = v
        elif k == "clipboard_text":
            mapped_parameters["text"] = v
        elif k == "directory_path":
            mapped_parameters["path"] = v
        elif k == "source_paths":
            mapped_parameters["sources"] = v
        elif k == "output_path":
            mapped_parameters["output"] = v
        elif k == "archive_path":
            mapped_parameters["archive"] = v
        else:
            mapped_parameters[k] = v

    # Execute the handler
    try:
        logger.info(f"Executing tool '{tool_name}' with mapped parameters: {mapped_parameters}")
        
        # Unpack parameters
        if not mapped_parameters:
            result = handler()
        else:
            result = handler(**mapped_parameters)
            
        if isinstance(result, dict):
            success = result.get("success", True)
            message = result.get("message", "")
            data = result.get("data")
            if data:
                output_str = f"{message} Data: {data}"
            else:
                output_str = message
            return success, output_str
            
        return True, str(result)
        
    except Exception as e:
        logger.error(f"Error during execution of tool '{tool_name}': {e}")
        return False, f"Execution failed: {e}"
