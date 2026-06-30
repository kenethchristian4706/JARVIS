"""
registry/tools_metadata.py

Defines simplified tool metadata for compact prompting of the Planner.
Eliminates large JSON schemas, utilizing concise argument descriptions instead.
"""

from typing import Dict, Any

TOOLS_METADATA: Dict[str, Dict[str, Any]] = {
    "open_app": {
        "Purpose": "Launch, open, or start a desktop application by name.",
        "Arguments": "app_name (str, required)",
        "Keywords": ["open", "launch", "start", "run"],
        "Aliases": ["start app", "open program"],
        "Dependencies": "none"
    },
    "close_app": {
        "Purpose": "Close, terminate, exit, or stop a running desktop application.",
        "Arguments": "app_name (str, required)",
        "Keywords": ["close", "stop", "terminate", "kill", "exit"],
        "Aliases": ["stop program", "terminate app"],
        "Dependencies": "none"
    },
    "list_installed_apps": {
        "Purpose": "List all indexed or installed desktop applications available on the system.",
        "Arguments": "none",
        "Keywords": ["list", "installed", "apps", "programs"],
        "Aliases": ["show apps", "what programs"],
        "Dependencies": "none"
    },
    "switch_to_app": {
        "Purpose": "Switch focus to or bring an already running desktop application window to the foreground.",
        "Arguments": "app_name (str, required)",
        "Keywords": ["focus", "switch", "activate", "front"],
        "Aliases": ["switch window", "bring to front"],
        "Dependencies": "none"
    },
    "list_running_apps": {
        "Purpose": "List all active application processes, windows, or programs currently running.",
        "Arguments": "none",
        "Keywords": ["running", "processes", "active", "tasks"],
        "Aliases": ["show running apps", "active processes"],
        "Dependencies": "none"
    },
    "move_file": {
        "Purpose": "Move or cut a file or folder from a source path to a destination path.",
        "Arguments": "source_path (str, required), destination_path (str, optional)",
        "Keywords": ["move", "cut", "transfer"],
        "Aliases": ["move folder", "transfer file"],
        "Dependencies": "none"
    },
    "copy_file": {
        "Purpose": "Copy, duplicate, or clone a file or folder from a source path to a destination folder or file path.",
        "Arguments": "source_path (str, required), destination_path (str, optional)",
        "Keywords": ["copy", "duplicate", "clone"],
        "Aliases": ["copy folder", "duplicate file"],
        "Dependencies": "none"
    },
    "rename_file": {
        "Purpose": "Rename a file or folder at a given path to a new base name.",
        "Arguments": "source_path (str, required), new_name (str, required)",
        "Keywords": ["rename", "change name"],
        "Aliases": ["change filename"],
        "Dependencies": "none"
    },
    "delete_file": {
        "Purpose": "Delete or remove a file from the local file system. Requires confirmation.",
        "Arguments": "file_path (str, required)",
        "Keywords": ["delete", "remove", "trash", "destroy"],
        "Aliases": ["remove file"],
        "Dependencies": "none"
    },
    "search_files": {
        "Purpose": "Search or find files and folders matching a query name or pattern.",
        "Arguments": "query (str, required)",
        "Keywords": ["search", "find", "locate"],
        "Aliases": ["find files", "search folders"],
        "Dependencies": "none"
    },
    "open_file": {
        "Purpose": "Open, view, or launch a file or document with its default registered system application.",
        "Arguments": "file_path (str, required)",
        "Keywords": ["open", "view", "launch", "read"],
        "Aliases": ["open pdf", "view document"],
        "Dependencies": "none"
    },
    "create_folder": {
        "Purpose": "Create or make a new empty folder or directory.",
        "Arguments": "folder_name (str, required), location (str, optional)",
        "Keywords": ["create", "make", "new", "generate"],
        "Aliases": ["make directory", "new folder"],
        "Dependencies": "none"
    },
    "create_file": {
        "Purpose": "Create or make a new empty text or program file at the specified path.",
        "Arguments": "file_path (str, required), location (str, optional)",
        "Keywords": ["create", "make", "new", "generate"],
        "Aliases": ["new file", "create blank file"],
        "Dependencies": "none"
    },
    "delete_folder": {
        "Purpose": "Delete a folder and all its contents recursively. Requires confirmation.",
        "Arguments": "folder_name (str, required)",
        "Keywords": ["delete", "remove", "trash"],
        "Aliases": ["remove directory"],
        "Dependencies": "none"
    },
    "list_directory": {
        "Purpose": "List files and subdirectories inside a specified path.",
        "Arguments": "directory_path (str, optional)",
        "Keywords": ["list", "dir", "ls", "contents"],
        "Aliases": ["show folder contents", "list files"],
        "Dependencies": "none"
    },
    "file_info": {
        "Purpose": "Get metadata properties of a file (like size, extension, modified date).",
        "Arguments": "file_path (str, required)",
        "Keywords": ["metadata", "info", "properties", "size"],
        "Aliases": ["file properties", "show size"],
        "Dependencies": "none"
    },
    "append_file": {
        "Purpose": "Write or append text content to a specified file.",
        "Arguments": "file_path (str, required), content (str, required)",
        "Keywords": ["write", "append", "add", "insert"],
        "Aliases": ["append text", "write content"],
        "Dependencies": "none"
    },
    "read_file_content": {
        "Purpose": "Read and retrieve text content of a supported text file.",
        "Arguments": "file_path (str, required)",
        "Keywords": ["read", "get", "view", "show"],
        "Aliases": ["read file", "get text"],
        "Dependencies": "none"
    },
    "write_file": {
        "Purpose": "Creates a new text file or completely replaces the contents of an existing text file. Never appends existing content.",
        "Arguments": "path (str, required), content (str, required), encoding (str, optional, defaults to 'utf-8'), create_parent (bool, optional, defaults to False)",
        "Keywords": ["write", "overwrite", "replace", "rewrite", "clear"],
        "Aliases": ["overwrite file", "replace file content", "rewrite file", "clear and write"],
        "Dependencies": "none"
    },
    "duplicate_file": {
        "Purpose": "Creates a duplicate copy of a file. Automatically generates a destination filename if one is not provided.",
        "Arguments": "source_path (str, required), destination_path (str, optional), overwrite (bool, optional, defaults to False)",
        "Keywords": ["duplicate", "clone", "make copy", "create another copy"],
        "Aliases": ["duplicate file", "clone file", "make copy of file"],
        "Dependencies": "none"
    },
    "compress_files": {
        "Purpose": "Compress a list of file or folder paths into a single zip archive.",
        "Arguments": "source_paths (List[str], required), output_path (str, required)",
        "Keywords": ["zip", "compress", "archive"],
        "Aliases": ["zip files"],
        "Dependencies": "none"
    },
    "extract_archive": {
        "Purpose": "Extract a zip archive into a destination folder.",
        "Arguments": "archive_path (str, required), destination_path (str, optional)",
        "Keywords": ["unzip", "extract", "uncompress"],
        "Aliases": ["unzip folder"],
        "Dependencies": "none"
    },
    "search_web": {
        "Purpose": "Search Google in the default web browser.",
        "Arguments": "query (str, required)",
        "Keywords": ["search", "google", "lookup", "find"],
        "Aliases": ["search web", "google search"],
        "Dependencies": "none"
    },
    "search_youtube": {
        "Purpose": "Search YouTube in the default browser.",
        "Arguments": "query (str, required)",
        "Keywords": ["youtube", "video", "play", "search"],
        "Aliases": ["youtube search", "find video"],
        "Dependencies": "none"
    },
    "open_url": {
        "Purpose": "Open a specific URL website in the default browser.",
        "Arguments": "url (str, required)",
        "Keywords": ["open", "go to", "navigate", "website"],
        "Aliases": ["open site", "go to webpage"],
        "Dependencies": "none"
    },
    "open_new_tab": {
        "Purpose": "Open a new tab in the browser with an optional URL.",
        "Arguments": "url (str, optional)",
        "Keywords": ["new tab", "tab open"],
        "Aliases": ["open tab"],
        "Dependencies": "none"
    },
    "close_tab": {
        "Purpose": "Close the active browser tab.",
        "Arguments": "none",
        "Keywords": ["close tab", "exit tab"],
        "Aliases": ["close active tab"],
        "Dependencies": "none"
    },
    "list_tabs": {
        "Purpose": "List all active open tabs in the browser.",
        "Arguments": "none",
        "Keywords": ["list tabs", "show tabs"],
        "Aliases": ["what tabs"],
        "Dependencies": "none"
    },
    "switch_tab": {
        "Purpose": "Switch browser tab focus by title or index.",
        "Arguments": "tab (str, required)",
        "Keywords": ["switch", "go to", "change"],
        "Aliases": ["go to tab", "select tab"],
        "Dependencies": "none"
    },
    "download_file": {
        "Purpose": "Download a file from a URL to a local destination folder.",
        "Arguments": "url (str, required), destination_path (str, optional)",
        "Keywords": ["download", "fetch", "save"],
        "Aliases": ["download file"],
        "Dependencies": "none"
    },
    "send_email": {
        "Purpose": "Send an email using the connected account. Requires confirmation.",
        "Arguments": "recipient (str, required), subject (str, required), body (str, required), cc (str, optional), bcc (str, optional), attachments (List[str], optional), confirmed (bool, optional)",
        "Keywords": ["email", "send", "mail", "message"],
        "Aliases": ["send mail"],
        "Dependencies": "none"
    },
    "list_emails": {
        "Purpose": "List summaries of recent emails.",
        "Arguments": "limit (int, optional, defaults to 10), unread_only (bool, optional, defaults to False)",
        "Keywords": ["email", "list", "inbox", "mail", "messages"],
        "Aliases": ["list emails", "show inbox", "check mail"],
        "Dependencies": "none"
    },
    "read_email": {
        "Purpose": "Read the contents of a selected email.",
        "Arguments": "email_id (str, required)",
        "Keywords": ["email", "read", "view", "mail", "open"],
        "Aliases": ["read email", "view email", "open mail"],
        "Dependencies": "none"
    },
    "shutdown_pc": {
        "Purpose": "Shut down the computer. Requires confirmation.",
        "Arguments": "none",
        "Keywords": ["shutdown", "power off", "turn off"],
        "Aliases": ["turn off computer"],
        "Dependencies": "none"
    },
    "restart_pc": {
        "Purpose": "Restart the computer. Requires confirmation.",
        "Arguments": "none",
        "Keywords": ["restart", "reboot"],
        "Aliases": ["reboot system"],
        "Dependencies": "none"
    },
    "sleep_pc": {
        "Purpose": "Put the computer into sleep/suspend mode.",
        "Arguments": "none",
        "Keywords": ["sleep", "suspend"],
        "Aliases": ["standby mode"],
        "Dependencies": "none"
    },
    "lock_pc": {
        "Purpose": "Lock the Windows session/workstation.",
        "Arguments": "none",
        "Keywords": ["lock", "lock pc"],
        "Aliases": ["lock computer"],
        "Dependencies": "none"
    },
    "set_volume": {
        "Purpose": "Set the master audio playback volume percentage.",
        "Arguments": "level (int, required)",
        "Keywords": ["volume", "audio", "sound"],
        "Aliases": ["set volume"],
        "Dependencies": "none"
    },
    "mute_volume": {
        "Purpose": "Mute the master system audio volume.",
        "Arguments": "none",
        "Keywords": ["mute", "silence"],
        "Aliases": ["turn off sound"],
        "Dependencies": "none"
    },
    "unmute_volume": {
        "Purpose": "Unmute the master system audio volume.",
        "Arguments": "none",
        "Keywords": ["unmute", "sound on"],
        "Aliases": ["turn sound on"],
        "Dependencies": "none"
    },
    "increase_volume": {
        "Purpose": "Increase the master system audio volume by 10%.",
        "Arguments": "none",
        "Keywords": ["volume up", "louder"],
        "Aliases": ["increase volume"],
        "Dependencies": "none"
    },
    "decrease_volume": {
        "Purpose": "Decrease the master system audio volume by 10%.",
        "Arguments": "none",
        "Keywords": ["volume down", "quieter"],
        "Aliases": ["decrease volume"],
        "Dependencies": "none"
    },
    "take_screenshot": {
        "Purpose": "Capture the entire screen and save it as a PNG image.",
        "Arguments": "save_path (str, optional)",
        "Keywords": ["screenshot", "capture screen", "snapshot"],
        "Aliases": ["take screenshot"],
        "Dependencies": "none"
    },
    "set_brightness": {
        "Purpose": "Set the display brightness percentage.",
        "Arguments": "level (int, required)",
        "Keywords": ["brightness", "screen light", "display"],
        "Aliases": ["set brightness"],
        "Dependencies": "none"
    },
    "increase_brightness": {
        "Purpose": "Increase display screen brightness by 10%.",
        "Arguments": "none",
        "Keywords": ["brighter", "increase brightness"],
        "Aliases": ["make screen brighter"],
        "Dependencies": "none"
    },
    "decrease_brightness": {
        "Purpose": "Decrease display screen brightness by 10%.",
        "Arguments": "none",
        "Keywords": ["dim", "decrease brightness"],
        "Aliases": ["make screen dimmer"],
        "Dependencies": "none"
    },
    "extract_text_from_image": {
        "Purpose": "Extract text content from an image file using OCR.",
        "Arguments": "image_path (str, required)",
        "Keywords": ["ocr", "extract text", "read image"],
        "Aliases": ["ocr image"],
        "Dependencies": "none"
    },
    "open_notepad_and_write": {
        "Purpose": "Launch Windows Notepad and populate it with text.",
        "Arguments": "text (str, required)",
        "Keywords": ["notepad", "write", "type"],
        "Aliases": ["write to notepad"],
        "Dependencies": "none"
    },
    "clear_clipboard": {
        "Purpose": "Clear all text content from the system clipboard.",
        "Arguments": "none",
        "Keywords": ["clear clipboard", "empty clipboard"],
        "Aliases": ["reset clipboard"],
        "Dependencies": "none"
    },
    "get_clipboard": {
        "Purpose": "Retrieve the current text content of the system clipboard.",
        "Arguments": "none",
        "Keywords": ["get clipboard", "read clipboard", "paste"],
        "Aliases": ["show clipboard"],
        "Dependencies": "none"
    },
    "set_clipboard": {
        "Purpose": "Copy specified text to the system clipboard.",
        "Arguments": "clipboard_text (str, required)",
        "Keywords": ["copy", "clipboard write", "set clipboard"],
        "Aliases": ["copy to clipboard"],
        "Dependencies": "none"
    },
    "cpu_usage": {
        "Purpose": "Retrieve current CPU usage metrics (read-only system information).",
        "Arguments": "none",
        "Keywords": ["cpu", "processor", "cores", "utilization", "usage"],
        "Aliases": ["cpu percentage", "show cpu usage", "processor speed"],
        "Dependencies": "none"
    },
    "ram_usage": {
        "Purpose": "Retrieve current RAM memory usage metrics (read-only system information).",
        "Arguments": "none",
        "Keywords": ["ram", "memory", "usage", "available", "gb"],
        "Aliases": ["memory usage", "show memory", "free ram"],
        "Dependencies": "none"
    },
    "disk_usage": {
        "Purpose": "Retrieve storage and disk space information for all mounted drives (read-only system information).",
        "Arguments": "none",
        "Keywords": ["disk", "storage", "space", "drives", "hard drive"],
        "Aliases": ["disk space", "show storage", "free space"],
        "Dependencies": "none"
    },
    "battery_status": {
        "Purpose": "Retrieve current battery status, charging state, and remaining life (read-only system information).",
        "Arguments": "none",
        "Keywords": ["battery", "power", "charge", "plugged in", "remaining"],
        "Aliases": ["battery status", "show battery percentage", "power percentage"],
        "Dependencies": "none"
    },
    "network_status": {
        "Purpose": "Retrieve current network status, hostname, local IP, public IP, and upload/download traffic (read-only system information).",
        "Arguments": "none",
        "Keywords": ["network", "internet", "ip", "connection", "wifi", "ethernet"],
        "Aliases": ["network status", "what is my ip", "check internet connection"],
        "Dependencies": "none"
    },
    "list_processes": {
        "Purpose": "List running system processes with PID, name, CPU, and Memory usage (read-only system information).",
        "Arguments": "sort_by (str, optional, defaults to 'cpu'), limit (int, optional, defaults to 20)",
        "Keywords": ["processes", "tasks", "running", "cpu", "memory", "list"],
        "Aliases": ["show running tasks", "process list", "top processes"],
        "Dependencies": "none"
    },
    "get_screen_resolution": {
        "Purpose": "Retrieve the display resolution and bounds for all connected screens (read-only system information).",
        "Arguments": "none",
        "Keywords": ["resolution", "screen", "display", "monitor", "bounds", "size"],
        "Aliases": ["screen size", "monitor resolution", "show display resolution"],
        "Dependencies": "none"
    }
}
