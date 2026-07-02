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
        "Purpose": "Send an email message using SMTP server configurations. Requires confirmation.",
        "Arguments": "recipient (str, required), subject (str, required), body (str, required), confirmed (bool, optional)",
        "Keywords": ["email", "send", "mail", "message"],
        "Aliases": ["send mail"],
        "Dependencies": "none"
    },
    "list_emails": {
        "Purpose": "List or retrieve a list of recent email messages from the inbox.",
        "Arguments": "limit (int, optional), unread_only (bool, optional)",
        "Keywords": ["emails", "inbox", "list", "messages", "get emails", "check mail"],
        "Aliases": ["list inbox", "check emails"],
        "Dependencies": "none"
    },
    "read_email": {
        "Purpose": "Read or retrieve full details of a specific email by its ID/UID, or by searching sender, date, or query.",
        "Arguments": "email_id (str, optional), sender (str, optional), date (str, optional)",
        "Keywords": ["read email", "open email", "view email", "email content"],
        "Aliases": ["read mail", "open mail"],
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
    "create_word": {
        "Purpose": "Create a new Microsoft Word document (.docx).",
        "Arguments": "filename (str, required), directory (str, optional), content (str, optional), overwrite (bool, optional)",
        "Keywords": ["create word", "make docx", "write docx", "new document"],
        "Aliases": ["create report", "create proposal"],
        "Dependencies": "none"
    },
    "read_word": {
        "Purpose": "Read plain text from a Microsoft Word document (.docx).",
        "Arguments": "file_path (str, required)",
        "Keywords": ["read word", "open word", "docx text", "extract docx"],
        "Aliases": ["read report", "view word document"],
        "Dependencies": "none"
    },
    "edit_word": {
        "Purpose": "Modify (append or replace text in) a Microsoft Word document (.docx).",
        "Arguments": "file_path (str, required), operation (str, required), text (str, optional), old_text (str, optional), new_text (str, optional)",
        "Keywords": ["edit word", "modify docx", "append word", "replace word text"],
        "Aliases": ["append to document", "replace text in report"],
        "Dependencies": "none"
    },
    "create_excel": {
        "Purpose": "Create a new Excel workbook (.xlsx).",
        "Arguments": "filename (str, required), directory (str, optional), sheet_name (str, optional), overwrite (bool, optional)",
        "Keywords": ["create excel", "make xlsx", "new spreadsheet", "new workbook"],
        "Aliases": ["create sheet", "create excel file"],
        "Dependencies": "none"
    },
    "read_excel": {
        "Purpose": "Read worksheet content from an Excel workbook (.xlsx).",
        "Arguments": "file_path (str, required), sheet_name (str, optional), cell_range (str, optional)",
        "Keywords": ["read excel", "open excel", "xlsx values", "view sheet"],
        "Aliases": ["read worksheet", "read table from excel"],
        "Dependencies": "none"
    },
    "write_excel": {
        "Purpose": "Write a value to a cell in an Excel workbook (.xlsx).",
        "Arguments": "file_path (str, required), sheet_name (str, required), cell (str, required), value (any, required)",
        "Keywords": ["write excel", "update cell", "set excel cell", "write xlsx"],
        "Aliases": ["update sheet cell", "write value to workbook"],
        "Dependencies": "none"
    }
}
