"""
registry/tools.py

Registers all 28 tools with their category, descriptions, and Pydantic schemas.
"""

import aether.registry.schemas as schemas

TOOLS = {
    # --- Application Management ---
    "open_app": {
        "category": "application_management",
        "description": "Open or launch a desktop application by name (e.g. Chrome, Notepad, Spotify).",
        "schema_class": schemas.OpenAppSchema
    },
    "close_app": {
        "category": "application_management",
        "description": "Close or terminate all running instances of a desktop application by name (e.g. close Chrome).",
        "schema_class": schemas.CloseAppSchema
    },
    "switch_to_app": {
        "category": "application_management",
        "description": "Switch focus to an already running desktop application window by name (e.g. focus Chrome, switch to Spotify).",
        "schema_class": schemas.SwitchToAppSchema
    },
    "list_running_apps": {
        "category": "application_management",
        "description": "List all active application processes currently running on the system.",
        "schema_class": schemas.ListRunningAppsSchema
    },
    "list_installed_apps": {
        "category": "application_management",
        "description": "List all indexed installed desktop applications available on the system.",
        "schema_class": schemas.ListInstalledAppsSchema
    },

    # --- File Operations ---
    "move_file": {
        "category": "file_operations",
        "description": "Move a file from a source path to a destination path.",
        "schema_class": schemas.MoveFileSchema
    },
    "copy_file": {
        "category": "file_operations",
        "description": "Copy a file from a source path to a destination folder or file path.",
        "schema_class": schemas.CopyFileSchema
    },
    "rename_file": {
        "category": "file_operations",
        "description": "Rename a file or folder at a given path to a new name.",
        "schema_class": schemas.RenameFileSchema
    },
    "delete_file": {
        "category": "file_operations",
        "description": "Delete a file from the local file system. This action requires safety confirmation.",
        "schema_class": schemas.DeleteFileSchema
    },
    "search_files": {
        "category": "file_operations",
        "description": "Search for files matching a natural language query or pattern.",
        "schema_class": schemas.SearchFilesSchema
    },
    "open_file": {
        "category": "file_operations",
        "description": "Open a file using its default registered system application (e.g. open notes.txt, view report.pdf).",
        "schema_class": schemas.OpenFileSchema
    },
    "create_folder": {
        "category": "file_operations",
        "description": "Create a new folder or directory at the specified path.",
        "schema_class": schemas.CreateFolderSchema
    },
    "create_file": {
        "category": "file_operations",
        "description": "Create a new blank file at the specified path.",
        "schema_class": schemas.CreateFileSchema
    },
    "delete_folder": {
        "category": "file_operations",
        "description": "Delete a folder and all its contents recursively. This action requires safety confirmation.",
        "schema_class": schemas.DeleteFolderSchema
    },
    "compress_files": {
        "category": "file_operations",
        "description": "Compress a list of file and folder paths into a zip archive.",
        "schema_class": schemas.CompressFilesSchema
    },
    "extract_archive": {
        "category": "file_operations",
        "description": "Extract a zip archive into a destination folder.",
        "schema_class": schemas.ExtractArchiveSchema
    },
    "list_directory": {
        "category": "file_operations",
        "description": "List the files and directories inside a specified path.",
        "schema_class": schemas.ListDirectorySchema
    },
    "file_info": {
        "category": "file_operations",
        "description": "Get file metadata like size, extension, and modified date by filename.",
        "schema_class": schemas.FileInfoSchema
    },
    "append_file": {
        "category": "file_operations",
        "description": "Append text content to an existing file.",
        "schema_class": schemas.AppendFileSchema
    },

    # --- Browser Operations ---
    "search_web": {
        "category": "browser_operations",
        "description": "Search Google for a query in the default web browser.",
        "schema_class": schemas.SearchWebSchema
    },
    "search_youtube": {
        "category": "browser_operations",
        "description": "Search YouTube for a query in the default web browser.",
        "schema_class": schemas.SearchYoutubeSchema
    },
    "open_url": {
        "category": "browser_operations",
        "description": "Open a specific URL website in the web browser.",
        "schema_class": schemas.OpenUrlSchema
    },
    "download_file": {
        "category": "browser_operations",
        "description": "Download a file from a URL to a local destination directory.",
        "schema_class": schemas.DownloadFileSchema
    },
    "open_new_tab": {
        "category": "browser_operations",
        "description": "Open a new tab in the web browser with an optional URL.",
        "schema_class": schemas.OpenNewTabSchema
    },
    "close_tab": {
        "category": "browser_operations",
        "description": "Close the active browser tab.",
        "schema_class": schemas.CloseTabSchema
    },
    "list_tabs": {
        "category": "browser_operations",
        "description": "List all active open tabs in the browser.",
        "schema_class": schemas.ListTabsSchema
    },
    "switch_tab": {
        "category": "browser_operations",
        "description": "Switch focus to a specific browser tab by title or index.",
        "schema_class": schemas.SwitchTabSchema
    },
    "send_email": {
        "category": "browser_operations",
        "description": "Send an email using SMTP server configurations.",
        "schema_class": schemas.SendEmailSchema
    },

    # --- System Control ---
    "shutdown_pc": {
        "category": "system_control",
        "description": "Shut down the computer. This action requires safety confirmation.",
        "schema_class": schemas.ShutdownPcSchema
    },
    "restart_pc": {
        "category": "system_control",
        "description": "Restart the computer. This action requires safety confirmation.",
        "schema_class": schemas.RestartPcSchema
    },
    "sleep_pc": {
        "category": "system_control",
        "description": "Put the computer into sleep/suspend mode.",
        "schema_class": schemas.SleepPcSchema
    },
    "lock_pc": {
        "category": "system_control",
        "description": "Lock the Windows session/workstation.",
        "schema_class": schemas.LockPcSchema
    },
    "set_volume": {
        "category": "system_control",
        "description": "Set the master audio playback volume to a level between 0 and 100 percent.",
        "schema_class": schemas.SetVolumeSchema
    },
    "mute_volume": {
        "category": "system_control",
        "description": "Mute the master audio playback volume.",
        "schema_class": schemas.MuteVolumeSchema
    },
    "unmute_volume": {
        "category": "system_control",
        "description": "Unmute the master audio playback volume.",
        "schema_class": schemas.UnmuteVolumeSchema
    },
    "set_brightness": {
        "category": "system_control",
        "description": "Set the display brightness to a level between 0 and 100 percent.",
        "schema_class": schemas.SetBrightnessSchema
    },
    "take_screenshot": {
        "category": "system_control",
        "description": "Capture the entire screen and save it as a PNG image.",
        "schema_class": schemas.TakeScreenshotSchema
    },
    "extract_text_from_image": {
        "category": "file_operations",
        "description": "Extract text from an image using OCR.",
        "schema_class": schemas.ExtractTextFromImageSchema
    },
    "open_notepad_and_write": {
        "category": "system_control",
        "description": "Launch Windows Notepad and populate it with text.",
        "schema_class": schemas.OpenNotepadAndWriteSchema
    },
    "read_file_content": {
        "category": "file_operations",
        "description": "Read text content from supported files (.txt, .md, .py, .json, .csv, .log).",
        "schema_class": schemas.ReadFileContentSchema
    },
    "clear_clipboard": {
        "category": "system_control",
        "description": "Clear the Windows clipboard.",
        "schema_class": schemas.ClearClipboardSchema
    },
    "get_clipboard": {
        "category": "system_control",
        "description": "Retrieve the current text content of the Windows clipboard.",
        "schema_class": schemas.GetClipboardSchema
    },
    "set_clipboard": {
        "category": "system_control",
        "description": "Copy specified text to the Windows clipboard.",
        "schema_class": schemas.SetClipboardSchema
    },
    "increase_volume": {
        "category": "system_control",
        "description": "Increase the master system audio volume by a default step of 10%.",
        "schema_class": schemas.IncreaseVolumeSchema
    },
    "decrease_volume": {
        "category": "system_control",
        "description": "Decrease the master system audio volume by a default step of 10%.",
        "schema_class": schemas.DecreaseVolumeSchema
    },
    "increase_brightness": {
        "category": "system_control",
        "description": "Increase the display screen brightness by a default step of 10%.",
        "schema_class": schemas.IncreaseBrightnessSchema
    },
    "decrease_brightness": {
        "category": "system_control",
        "description": "Decrease the display screen brightness by a default step of 10%.",
        "schema_class": schemas.DecreaseBrightnessSchema
    }
}
