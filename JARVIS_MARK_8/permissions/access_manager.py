"""
permissions/access_manager.py

Enforces file-system access authorization levels. Checks if a file path is permitted,
prompts the user interactively on permission denials, and tracks session-only overrides.
"""

import os
from indexing.file_indexer import get_folder_permission, add_folder_permission, index_folder_recursive

# In-memory store for session-only ("Allow Once") permissions
# Maps normalized folder_path -> access_level
_session_permissions = {}

def check_permission(file_path: str, required_level: str) -> bool:
    """
    Checks if access to file_path is authorized for the required access level.
    Levels: 'read', 'read_write', 'full_control'
    """
    norm_path = os.path.normpath(os.path.abspath(file_path))
    
    # 1. Determine parent folder directory
    if os.path.isdir(norm_path):
        target_dir = norm_path
    else:
        target_dir = os.path.dirname(norm_path)
        
    # Check hierarchy for session permissions
    current = target_dir
    session_level = "none"
    while True:
        if current in _session_permissions:
            session_level = _session_permissions[current]
            break
        parent = os.path.dirname(current)
        if parent == current:
            if current in _session_permissions:
                session_level = _session_permissions[current]
            break
        current = parent
        
    # 2. Get database permissions
    db_level = get_folder_permission(target_dir)
    
    # Select the highest authorization between session and DB
    permission_hierarchy = {"none": 0, "read": 1, "read_write": 2, "full_control": 3}
    active_level = db_level
    if permission_hierarchy[session_level] > permission_hierarchy[db_level]:
        active_level = session_level
        
    # 3. Verify access match
    req_score = permission_hierarchy.get(required_level, 9)
    act_score = permission_hierarchy.get(active_level, 0)
    
    return act_score >= req_score

def request_user_authorization(file_path: str, required_level: str) -> bool:
    """
    Prompts the user interactively on the console to grant permission to a directory.
    Options: Allow Once (session), Always Allow (SQLite persist), Deny.
    """
    norm_path = os.path.normpath(os.path.abspath(file_path))
    if os.path.isdir(norm_path):
        target_dir = norm_path
    else:
        target_dir = os.path.dirname(norm_path)
        
    print("\n" + "!" * 60)
    print("PERMISSION ACCESS REQUEST REQUIRED")
    print("!" * 60)
    print(f"Aether is attempting to perform an action requiring '{required_level}' access.")
    print(f"Target Directory: {target_dir}")
    print("-" * 60)
    print("Choose authorization level:")
    print("  [1] Allow Once (this session only)")
    print("  [2] Always Allow (persisted to SQLite config)")
    print("  [3] Deny Access")
    print("!" * 60)
    
    try:
        choice = input("Enter choice [1-3]: ").strip()
    except (KeyboardInterrupt, EOFError):
        choice = "3"
        
    if choice == "1":
        _session_permissions[target_dir] = required_level
        print(f"[Permissions] Granted session-only '{required_level}' access to: {target_dir}")
        return True
    elif choice == "2":
        add_folder_permission(target_dir, required_level)
        # Recursively index the folder contents as background helper
        print(f"[Permissions] Persisting '{required_level}' access. Indexing files...")
        index_folder_recursive(target_dir, required_level)
        return True
    else:
        print(f"[Permissions] Access Denied for directory: {target_dir}")
        return False

def verify_and_authorize(file_path: str, required_level: str) -> bool:
    """
    Enforces authorization check, triggering interactive prompt if unauthorized.
    Returns True if allowed, False if blocked.
    """
    if check_permission(file_path, required_level):
        return True
        
    # Request authorization from the user
    return request_user_authorization(file_path, required_level)
