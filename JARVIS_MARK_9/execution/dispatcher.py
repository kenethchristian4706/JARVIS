"""
execution/dispatcher.py

Routes tool names to their execution handlers, validates input parameters,
standardizes returned values, and logs execution details.
"""

import logging
from typing import Callable, Any

# Import all tool handlers
from tools.file_tools import (
    search_file, open_file, create_file, delete_file, rename_file,
    move_file, copy_file, create_folder, delete_folder, rename_folder,
    append_to_file, read_file_content, recent_files, files_by_extension,
    files_by_date, semantic_file_search
)
from tools.app_tools import (
    open_app, close_app, switch_to_app, list_running_apps, list_installed_apps
)
from tools.system_tools import (
    set_volume, increase_volume, decrease_volume, mute_volume, unmute_volume,
    set_brightness, increase_brightness, decrease_brightness,
    take_screenshot, copy_to_clipboard, read_clipboard, clear_clipboard,
    shutdown_system, restart_system, sleep_system, lock_system, logout_user,
    open_notepad_and_write, open_website, google_search, youtube_search,
    website_search, download_file, extract_text_from_image, close_browser,
    open_new_tab, switch_tab, close_tab, fill_form, submit_form,
    click_element, type_text, scroll_page, upload_file, browser_agent
)

logger = logging.getLogger(__name__)

# Dispatcher registry mapping all 56 tool names to their execution handler functions
DISPATCH_TABLE: dict[str, Callable] = {
    # Application Management
    "open_app": open_app,
    "close_app": close_app,
    "switch_to_app": switch_to_app,
    "list_running_apps": list_running_apps,
    "list_installed_apps": list_installed_apps,
    
    # System Control
    "shutdown_system": shutdown_system,
    "restart_system": restart_system,
    "sleep_system": sleep_system,
    "lock_system": lock_system,
    "logout_user": logout_user,
    
    # Audio Volume
    "set_volume": set_volume,
    "increase_volume": increase_volume,
    "decrease_volume": decrease_volume,
    "mute_volume": mute_volume,
    "unmute_volume": unmute_volume,
    
    # Brightness Settings
    "set_brightness": set_brightness,
    "increase_brightness": increase_brightness,
    "decrease_brightness": decrease_brightness,
    
    # Clipboard Actions
    "copy_to_clipboard": copy_to_clipboard,
    "read_clipboard": read_clipboard,
    "clear_clipboard": clear_clipboard,
    
    # File Management
    "search_file": search_file,
    "open_file": open_file,
    "create_file": create_file,
    "delete_file": delete_file,
    "rename_file": rename_file,
    "move_file": move_file,
    "copy_file": copy_file,
    
    # Folder Management
    "create_folder": create_folder,
    "delete_folder": delete_folder,
    "rename_folder": rename_folder,
    
    # File Content Editing
    "open_notepad_and_write": open_notepad_and_write,
    "append_to_file": append_to_file,
    "read_file_content": read_file_content,
    
    # Screenshot / OCR
    "take_screenshot": take_screenshot,
    "extract_text_from_image": extract_text_from_image,
    
    # Advanced Search Filters
    "semantic_file_search": semantic_file_search,
    "recent_files": recent_files,
    "files_by_extension": files_by_extension,
    "files_by_date": files_by_date,
    
    # Web Browser Operations
    "open_website": open_website,
    "close_browser": close_browser,
    "open_new_tab": open_new_tab,
    "switch_tab": switch_tab,
    "close_tab": close_tab,
    
    # Search Engine Queries
    "google_search": google_search,
    "youtube_search": youtube_search,
    "website_search": website_search,
    
    # Web Browser Page Interactions
    "fill_form": fill_form,
    "submit_form": submit_form,
    "click_element": click_element,
    "type_text": type_text,
    "scroll_page": scroll_page,
    
    # File Transfer Actions
    "download_file": download_file,
    "upload_file": upload_file,
    
    # Autonomous Browser Automation
    "browser_agent": browser_agent
}

def dispatch(tool_name: str, parameters: dict) -> dict:
    """
    Routes the given tool_name and validated parameters dictionary to the matching handler.
    Standardizes output response formatting and captures processing runtime errors.
    """
    handler = DISPATCH_TABLE.get(tool_name)
    
    if handler is None:
        logger.error(f"No handler registered for tool: {tool_name}")
        return {
            "success": False,
            "tool": tool_name,
            "output": None,
            "error": f"No handler registered for tool: {tool_name}"
        }
        
    try:
        logger.info(f"Dispatching tool '{tool_name}' with parameters {parameters}...")
        result = handler(**parameters)
        return {
            "success": True,
            "tool": tool_name,
            "output": result,
            "error": None
        }
    except TypeError as e:
        # Wrong parameters passed (e.g. validator and handler schema mismatch)
        logger.error(f"Parameter mismatch error in dispatch for '{tool_name}': {e}")
        return {
            "success": False,
            "tool": tool_name,
            "output": None,
            "error": f"Parameter mismatch error: {e}"
        }
    except Exception as e:
        logger.error(f"Execution failed in handler for '{tool_name}': {e}")
        return {
            "success": False,
            "tool": tool_name,
            "output": None,
            "error": f"Execution error: {e}"
        }
