"""
safety/safety_manager.py

Categorizes Aether tools into low, medium, and high risk levels.
Requires explicit user confirmation on high-risk actions before execution.
"""

import logging

logger = logging.getLogger(__name__)

# Map of tool names to their corresponding safety risk level categories
RISK_LEVELS: dict[str, list[str]] = {
    "low": [
        "open_app", "close_app", "switch_to_app", "list_running_apps", "list_installed_apps",
        "open_file", "search_file", "read_file_content", "semantic_file_search",
        "recent_files", "files_by_extension", "files_by_date",
        "take_screenshot", "extract_text_from_image",
        "read_clipboard", "copy_to_clipboard",
        "open_website", "open_new_tab", "switch_tab", "close_tab", "close_browser",
        "google_search", "youtube_search", "website_search",
        "set_volume", "increase_volume", "decrease_volume", "mute_volume", "unmute_volume",
        "set_brightness", "increase_brightness", "decrease_brightness",
        "scroll_page", "click_element", "type_text", "fill_form", "submit_form",
        "lock_system", "sleep_system", "logout_user"
    ],
    "medium": [
        "create_file", "create_folder",
        "rename_file", "rename_folder",
        "move_file", "copy_file",
        "append_to_file",
        "open_notepad_and_write",
        "clear_clipboard",
        "download_file", "upload_file",
        "browser_agent",
        "restart_system"
    ],
    "high": [
        "delete_file",
        "delete_folder",
        "shutdown_system"
    ]
}

def get_risk_level(tool_name: str) -> str:
    """
    Returns 'low', 'medium', or 'high'. Default 'medium' if unknown.
    """
    for level, tools in RISK_LEVELS.items():
        if tool_name in tools:
            return level
    return "medium"

def check_safety(tool_name: str, parameters: dict) -> bool:
    """
    Blocks high-risk actions with a console user confirmation prompt.
    Returns True if allowed to proceed, or False if aborted.
    """
    level = get_risk_level(tool_name)
    logger.debug(f"Safety check for tool '{tool_name}': Risk level is {level}.")
    
    if level != "high":
        return True
        
    # Gather target description for high risk display
    target = (
        parameters.get("filename") or
        parameters.get("folder_name") or
        parameters.get("source") or
        str(parameters)
    )
    
    print()
    print("=" * 50)
    print("  ⚠️  HIGH RISK ACTION — CONFIRMATION REQUIRED")
    print("=" * 50)
    print(f"  Tool   : {tool_name}")
    print(f"  Target : {target}")
    print("=" * 50)
    print("  This action CANNOT be undone.")
    print()
    
    try:
        answer = input("  Confirm? [y = yes / n = cancel]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        logger.warning("Confirmation input interrupted or canceled.")
        return False
        
    confirmed = (answer == "y")
    logger.debug(f"User confirmation response for {tool_name}: {confirmed}")
    return confirmed

def describe_risk(tool_name: str) -> str:
    """
    Return a human-readable risk description for logging.
    """
    level = get_risk_level(tool_name)
    descriptions = {
        "low":    "Safe operation, no confirmation needed.",
        "medium": "Reversible operation, executing without confirmation.",
        "high":   "Destructive operation, requires confirmation."
    }
    return descriptions.get(level, "Unknown risk level.")
