"""
execution/dispatcher.py

Routes tool names to execution handlers, performs access permission verification,
enforces safety check prompts, executes actions, and writes to audit_logs.
"""

import json
from datetime import datetime
from database.db_manager import get_db_connection
from permissions.access_manager import verify_and_authorize
from permissions.safety_manager import verify_safety

# Import all tool handlers
import tools.app_handlers as app
import tools.system_handlers as sys_ctrl
import tools.file_handlers as files

# Dispatcher registry mapping tool_name to handler function
HANDLER_REGISTRY = {
    # Apps
    "open_app": lambda params: app.open_app(params["app_name"]),
    "close_app": lambda params: app.close_app(params["app_name"]),
    "list_installed_apps": lambda params: app.list_installed_apps(),
    
    # Audio
    "set_volume": lambda params: sys_ctrl.set_volume(params["volume"]),
    "increase_volume": lambda params: sys_ctrl.increase_volume(),
    "decrease_volume": lambda params: sys_ctrl.decrease_volume(),
    "mute_volume": lambda params: sys_ctrl.mute_volume(),
    "unmute_volume": lambda params: sys_ctrl.unmute_volume(),
    
    # Brightness
    "set_brightness": lambda params: sys_ctrl.set_brightness(params["brightness"]),
    "increase_brightness": lambda params: sys_ctrl.increase_brightness(),
    "decrease_brightness": lambda params: sys_ctrl.decrease_brightness(),
    
    # System Control
    "shutdown_system": lambda params: sys_ctrl.shutdown_system(),
    "take_screenshot": lambda params: sys_ctrl.take_screenshot(),
    
    # Files
    "search_file": lambda params: files.search_file(params["filename"]),
    "open_file": lambda params: files.open_file(params["filename"]),
    "create_file": lambda params: files.create_file(params["filename"]),
    "delete_file": lambda params: files.delete_file(params["filename"]),
    "rename_file": lambda params: files.rename_file(params["filename"], params["new_name"]),
    "move_file": lambda params: files.move_file(params["source"], params["destination"]),
    "copy_file": lambda params: files.copy_file(params["source"], params["destination"]),
    "append_to_file": lambda params: files.append_to_file(params["filename"], params["text"]),
    "read_file_content": lambda params: files.read_file_content(params["filename"]),
    
    # Folders
    "create_folder": lambda params: files.create_folder(params["folder_name"]),
    "delete_folder": lambda params: files.delete_folder(params["folder_name"]),
    "rename_folder": lambda params: files.rename_folder(params["folder_name"], params["new_name"]),
    
    # Notepad
    "open_notepad_and_write": lambda params: files.open_notepad_and_write(params.get("app_name", "notepad"), params["text"])
}

def log_to_audit(query: str, tool_name: str, parameters: dict, status: str, error_msg: str = None):
    """
    Saves the execution trace into SQLite audit_logs table.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (timestamp, user_query, selected_tool, parameters, execution_status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                query,
                tool_name,
                json.dumps(parameters),
                status,
                error_msg
            ))
            conn.commit()
    except Exception as e:
        print(f"[Dispatcher] Error writing to audit log: {e}")

def dispatch_and_execute(query: str, tool_name: str, parameters: dict) -> dict:
    """
    Orchestrates validation checks, folder permission checks, safety confirmation checks,
    invokes the target handler, and logs trace results.
    """
    if tool_name not in HANDLER_REGISTRY:
        log_to_audit(query, tool_name, parameters, "error", f"Tool '{tool_name}' not supported by dispatcher.")
        return {"status": "error", "message": f"Tool '{tool_name}' has no execution handler."}

    # 1. Enforce Folder/File Permission Checks
    permission_checked = True
    
    if tool_name in ["open_file", "search_file", "read_file_content"]:
        permission_checked = verify_and_authorize(parameters["filename"], "read")
        
    elif tool_name in ["create_file", "append_to_file", "rename_file", "create_folder", "rename_folder"]:
        permission_checked = verify_and_authorize(parameters.get("filename") or parameters.get("folder_name"), "read_write")
        
    elif tool_name in ["move_file", "copy_file"]:
        # Verify permissions on source (read) and destination (read_write)
        permission_checked = verify_and_authorize(parameters["source"], "read") and \
                             verify_and_authorize(parameters["destination"], "read_write")
                             
    elif tool_name in ["delete_file", "delete_folder"]:
        permission_checked = verify_and_authorize(parameters.get("filename") or parameters.get("folder_name"), "full_control")

    if not permission_checked:
        log_to_audit(query, tool_name, parameters, "error", "Blocked by permissions layer.")
        return {"status": "error", "message": f"Execution blocked: Access permission denied for the folder path."}

    # 2. Enforce Safety risk confirmation checks
    if not verify_safety(tool_name, parameters):
        log_to_audit(query, tool_name, parameters, "error", "Execution cancelled by user safety check.")
        return {"status": "error", "message": "Execution cancelled: High-risk action was not confirmed."}

    # 3. Trigger Handler execution
    handler = HANDLER_REGISTRY[tool_name]
    try:
        result = handler(parameters)
        status = result.get("status", "success")
        error_msg = result.get("message") if status == "error" else None
        
        log_to_audit(query, tool_name, parameters, status, error_msg)
        return result
    except Exception as e:
        error_msg = str(e)
        log_to_audit(query, tool_name, parameters, "error", error_msg)
        return {"status": "error", "message": f"Unexpected execution crash: {e}"}
