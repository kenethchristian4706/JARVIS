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
    "send_email",
    "write_file",
    "duplicate_file"
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
    elif tool_name == "write_file":
        return parameters.get("path") or "unspecified file"
    elif tool_name == "duplicate_file":
        return parameters.get("source") or parameters.get("source_path") or "unspecified file"
    return str(parameters)

def ask_user_confirmation(tool_name: str, parameters: Dict[str, Any]) -> bool:
    """
    Prompts the user to confirm execution of high-risk actions.
    If connected to a WebSocket session, uses the visual frontend popup.
    Otherwise falls back to command-line input.
    """
    target = get_confirmation_target(tool_name, parameters)
    
    if tool_name == "delete_file":
        prompt_msg = f"Are you sure you want to delete file '{target}'?"
    elif tool_name == "delete_folder":
        prompt_msg = f"Are you sure you want to delete folder '{target}'?"
    elif tool_name == "shutdown_pc":
        prompt_msg = "Are you sure you want to shut down the computer?"
    elif tool_name == "restart_pc":
        prompt_msg = "Are you sure you want to restart the computer?"
    elif tool_name == "sleep_pc":
        prompt_msg = "Are you sure you want to put the computer to sleep?"
    elif tool_name == "send_email":
        prompt_msg = f"Are you sure you want to send this email to {parameters.get('recipient')}?"
    elif tool_name == "write_file":
        from pathlib import Path
        from aether.tools.file_tools import resolve_path
        try:
            resolved_path = resolve_path(target)
            exists = resolved_path.exists()
        except Exception:
            exists = False
            
        if exists:
            prompt_msg = f"File '{target}' already exists. Are you sure you want to OVERWRITE its contents?"
        else:
            prompt_msg = f"Are you sure you want to create and write content to file '{target}'?"
    elif tool_name == "duplicate_file":
        dst = parameters.get("destination") or parameters.get("destination_path")
        dst_str = f" to '{dst}'" if dst else ""
        prompt_msg = f"Are you sure you want to duplicate file '{target}'{dst_str}?"
    else:
        prompt_msg = f"Are you sure you want to execute {tool_name}?"

    from aether.api.prompt import prompt_user_sync
    title = f"[WARNING] High-Risk System Operation Requested\nAction: {tool_name}\nTarget: {target}\n\n{prompt_msg}"
    options = ["Yes, confirm action", "No, cancel action"]
    
    choice = prompt_user_sync(title, options)
    confirmed = choice.lower() in ("yes", "y", "confirm", "1", "yes, confirm action")
    logger.info(f"User confirmation for {tool_name} (target: {target}): {confirmed}")
    return confirmed
