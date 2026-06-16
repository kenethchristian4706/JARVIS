"""
permissions/safety_manager.py

Categorizes tool actions by safety risk level and handles user confirmation
prompts for high-risk, potentially destructive system commands.
"""

from typing import Dict

# Risk levels map
RISK_LEVELS: Dict[str, str] = {
    # Low Risk
    "open_app": "low",
    "close_app": "low",
    "list_installed_apps": "low",
    "set_volume": "low",
    "increase_volume": "low",
    "decrease_volume": "low",
    "mute_volume": "low",
    "unmute_volume": "low",
    "set_brightness": "low",
    "increase_brightness": "low",
    "decrease_brightness": "low",
    "search_file": "low",
    "open_file": "low",
    "read_file_content": "low",
    "take_screenshot": "low",
    
    # Medium Risk
    "create_file": "medium",
    "rename_file": "medium",
    "move_file": "medium",
    "copy_file": "medium",
    "create_folder": "medium",
    "rename_folder": "medium",
    "open_notepad_and_write": "medium",
    "append_to_file": "medium",
    
    # High Risk
    "delete_file": "high",
    "delete_folder": "high",
    "shutdown_system": "high"
}

def get_tool_risk_level(tool_name: str) -> str:
    """
    Returns the risk level: 'low', 'medium', or 'high'.
    Defaults to 'medium' for safety.
    """
    return RISK_LEVELS.get(tool_name, "medium")

def request_execution_confirmation(tool_name: str, parameters: dict) -> bool:
    """
    Prompts the user to confirm execution of high-risk actions.
    """
    print("\n" + "=" * 60)
    print("WARNING: HIGH RISK ACTION CONFIRMATION REQUIRED")
    print("=" * 60)
    print(f"Tool Action: {tool_name}")
    print(f"Parameters:  {parameters}")
    print("-" * 60)
    print("Executing this action could modify or delete systems/files permanently.")
    print("=" * 60)
    
    try:
        confirm = input("Confirm execution? [yes/no]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        confirm = "no"
        
    if confirm in ["y", "yes"]:
        print("[Safety] User confirmed execution.")
        return True
    else:
        print("[Safety] Execution cancelled by user.")
        return False

def verify_safety(tool_name: str, parameters: dict) -> bool:
    """
    Verifies action safety. Returns True if execution is safe to proceed, False otherwise.
    """
    risk = get_tool_risk_level(tool_name)
    if risk == "high":
        return request_execution_confirmation(tool_name, parameters)
    return True
