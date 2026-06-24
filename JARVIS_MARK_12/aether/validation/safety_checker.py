"""
validation/safety_checker.py

Identifies high-risk tools and prompts the user for explicit confirmation before execution.
"""

import sys
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

HIGH_RISK_TOOLS = {
    "delete_file",
    "delete_folder",
    "shutdown_pc",
    "restart_pc",
    "sleep_pc",
    "send_email"
}

def needs_safety_confirmation(tool_name: str) -> bool:
    """Checks if the given tool is categorized as high-risk."""
    return tool_name in HIGH_RISK_TOOLS

def get_confirmation_target(tool_name: str, parameters: Dict[str, Any]) -> str:
    """Gets a user-friendly description of the target of the action."""
    if tool_name == "delete_file":
        return parameters.get("filename") or "unspecified file"
    elif tool_name == "delete_folder":
        return parameters.get("folder_name") or "unspecified folder"
    elif tool_name in ("shutdown_pc", "restart_pc", "sleep_pc"):
        return "the operating system"
    elif tool_name == "send_email":
        return f"email to {parameters.get('recipient')} (Subject: {parameters.get('subject')})"
    return str(parameters)

def ask_user_confirmation(tool_name: str, parameters: Dict[str, Any]) -> bool:
    """
    Prompts the user via stdin console to confirm execution of high-risk actions.
    
    Returns True if confirmed, False otherwise.
    """
    target = get_confirmation_target(tool_name, parameters)
    
    if tool_name == "delete_file":
        prompt_msg = f"Are you sure you want to delete {target}?\nType yes to continue: "
    elif tool_name == "delete_folder":
        prompt_msg = f"Are you sure you want to delete folder {target}?\nType yes to continue: "
    elif tool_name == "shutdown_pc":
        prompt_msg = "Are you sure you want to shut down the computer?\nType yes to continue: "
    elif tool_name == "restart_pc":
        prompt_msg = "Are you sure you want to restart the computer?\nType yes to continue: "
    elif tool_name == "sleep_pc":
        prompt_msg = "Are you sure you want to put the computer to sleep?\nType yes to continue: "
    elif tool_name == "send_email":
        prompt_msg = f"Are you sure you want to send this email to {parameters.get('recipient')}?\nType yes to continue: "
    else:
        prompt_msg = f"Are you sure you want to execute {tool_name}?\nType yes to continue: "

        
    print()
    print("=" * 60)
    print("  [WARNING] HIGH-RISK SYSTEM OPERATION REQUESTED")
    print("=" * 60)
    print(f"  Action : {tool_name}")
    print(f"  Target : {target}")
    print("-" * 60)
    print("  This action can alter system state or permanently delete files.")
    print("=" * 60)
    
    try:
        confirm = input(prompt_msg).strip()
        confirmed = confirm.lower() in ("yes", "y", "confirm")
        logger.info(f"User confirmation for {tool_name} (target: {target}): {confirmed}")
        return confirmed
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled (input interrupted).")
        logger.warning("User confirmation prompt interrupted.")
        return False
