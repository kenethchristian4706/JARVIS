"""
registry/tools.py

Registers all tools with their category, descriptions, Pydantic schemas,
and wraps them in a centralized Tool Registry.
"""

from typing import Dict, Any, List, Optional
import aether.registry.schemas as schemas
from aether.registry.categories import CATEGORIES

class ToolMetadata:
    def __init__(self, name: str, category: str, description: str, parameters: Optional[List[str]] = None, aliases: Optional[List[str]] = None, schema_class: Any = None):
        self.name = name
        self.category = category
        self.description = description
        self.aliases = aliases or []
        self.schema_class = schema_class
        self._parameters = parameters

    @property
    def parameters(self) -> List[str]:
        if self._parameters is not None:
            return self._parameters
        if not self.schema_class:
            return []
        fields = getattr(self.schema_class, "model_fields", None) or getattr(self.schema_class, "__fields__", {})
        return list(fields.keys())

    def __repr__(self) -> str:
        return f"ToolMetadata(name='{self.name}', category='{self.category}', parameters={self.parameters})"

# Define the central TOOLS schema mapping
TOOLS = {
    # --- applications ---
    "open_app": {
        "category": "applications",
        "description": "Launch a desktop application by name (e.g. Chrome, Notepad, Spotify).",
        "schema_class": schemas.OpenAppSchema
    },
    "close_app": {
        "category": "applications",
        "description": "Close all running instances of a desktop application by name.",
        "schema_class": schemas.CloseAppSchema
    },
    "list_installed_apps": {
        "category": "applications",
        "description": "List all indexed installed desktop applications available on the system.",
        "schema_class": schemas.ListInstalledAppsSchema
    },

    # --- windows ---
    "switch_to_app": {
        "category": "windows",
        "description": "Switch focus to an already running desktop application window by name.",
        "schema_class": schemas.SwitchToAppSchema
    },

    # --- process ---
    "list_running_apps": {
        "category": "process",
        "description": "List all active application processes currently running on the system.",
        "schema_class": schemas.ListRunningAppsSchema
    },

    # --- filesystem ---
    "move_file": {
        "category": "filesystem",
        "description": "Move a file from a source path to a destination path.",
        "schema_class": schemas.MoveFileSchema
    },
    "copy_file": {
        "category": "filesystem",
        "description": "Copy a file from a source path to a destination folder or file path.",
        "schema_class": schemas.CopyFileSchema
    },
    "rename_file": {
        "category": "filesystem",
        "description": "Rename a file or folder at a given path to a new name.",
        "schema_class": schemas.RenameFileSchema
    },
    "delete_file": {
        "category": "filesystem",
        "description": "Delete a file from the local file system. This action requires safety confirmation.",
        "schema_class": schemas.DeleteFileSchema
    },
    "search_files": {
        "category": "filesystem",
        "description": "Search for files matching a query or pattern.",
        "schema_class": schemas.SearchFilesSchema
    },
    "open_file": {
        "category": "filesystem",
        "description": "Open a file using its default registered system application.",
        "schema_class": schemas.OpenFileSchema
    },
    "create_folder": {
        "category": "filesystem",
        "description": "Create a new folder or directory at the specified path.",
        "schema_class": schemas.CreateFolderSchema
    },
    "create_file": {
        "category": "filesystem",
        "description": "Create a new blank file at the specified path.",
        "schema_class": schemas.CreateFileSchema
    },
    "delete_folder": {
        "category": "filesystem",
        "description": "Delete a folder and all its contents recursively. This action requires safety confirmation.",
        "schema_class": schemas.DeleteFolderSchema
    },
    "list_directory": {
        "category": "filesystem",
        "description": "List the files and directories inside a specified path.",
        "schema_class": schemas.ListDirectorySchema
    },
    "file_info": {
        "category": "filesystem",
        "description": "Get file metadata like size, extension, and modified date by path.",
        "schema_class": schemas.FileInfoSchema
    },
    "append_file": {
        "category": "filesystem",
        "description": "Write or append text content to a file.",
        "schema_class": schemas.AppendFileSchema
    },
    "read_file_content": {
        "category": "filesystem",
        "description": "Read text content from supported files (.txt, .md, .py, .json, .csv, .log).",
        "schema_class": schemas.ReadFileContentSchema
    },

    # --- compression ---
    "compress_files": {
        "category": "compression",
        "description": "Compress a list of file and folder paths into a zip archive.",
        "schema_class": schemas.CompressFilesSchema
    },
    "extract_archive": {
        "category": "compression",
        "description": "Extract a zip archive into a destination folder.",
        "schema_class": schemas.ExtractArchiveSchema
    },

    # --- browser ---
    "search_web": {
        "category": "browser",
        "description": "Search Google for a query in the default web browser.",
        "schema_class": schemas.SearchWebSchema
    },
    "search_youtube": {
        "category": "browser",
        "description": "Search YouTube for a query in the default web browser.",
        "schema_class": schemas.SearchYoutubeSchema
    },
    "open_url": {
        "category": "browser",
        "description": "Open a specific URL website in the web browser.",
        "schema_class": schemas.OpenUrlSchema
    },
    "open_new_tab": {
        "category": "browser",
        "description": "Open a new tab in the web browser with an optional URL.",
        "schema_class": schemas.OpenNewTabSchema
    },
    "close_tab": {
        "category": "browser",
        "description": "Close the active browser tab.",
        "schema_class": schemas.CloseTabSchema
    },
    "list_tabs": {
        "category": "browser",
        "description": "List all active open tabs in the browser.",
        "schema_class": schemas.ListTabsSchema
    },
    "switch_tab": {
        "category": "browser",
        "description": "Switch focus to a specific browser tab by title or index.",
        "schema_class": schemas.SwitchTabSchema
    },

    # --- network ---
    "download_file": {
        "category": "network",
        "description": "Download a file from a URL to a local destination directory.",
        "schema_class": schemas.DownloadFileSchema
    },

    # --- email ---
    "send_email": {
        "category": "email",
        "description": "Send an email using SMTP server configurations. This action requires safety confirmation.",
        "schema_class": schemas.SendEmailSchema
    },
    "list_emails": {
        "category": "email",
        "description": "Retrieve summaries of recent emails using IMAP.",
        "schema_class": schemas.ListEmailsSchema
    },
    "read_email": {
        "category": "email",
        "description": "Retrieve details of a specific email (body, sender, recipients, attachments) by its ID using IMAP.",
        "schema_class": schemas.ReadEmailSchema
    },

    # --- power ---
    "shutdown_pc": {
        "category": "power",
        "description": "Shut down the computer. This action requires safety confirmation.",
        "schema_class": schemas.ShutdownPcSchema
    },
    "restart_pc": {
        "category": "power",
        "description": "Restart the computer. This action requires safety confirmation.",
        "schema_class": schemas.RestartPcSchema
    },
    "sleep_pc": {
        "category": "power",
        "description": "Put the computer into sleep/suspend mode.",
        "schema_class": schemas.SleepPcSchema
    },
    "lock_pc": {
        "category": "power",
        "description": "Lock the Windows session/workstation.",
        "schema_class": schemas.LockPcSchema
    },

    # --- media ---
    "set_volume": {
        "category": "media",
        "description": "Set the master audio playback volume between 0 and 100 percent.",
        "schema_class": schemas.SetVolumeSchema
    },
    "mute_volume": {
        "category": "media",
        "description": "Mute the master audio playback volume.",
        "schema_class": schemas.MuteVolumeSchema
    },
    "unmute_volume": {
        "category": "media",
        "description": "Unmute the master audio playback volume.",
        "schema_class": schemas.UnmuteVolumeSchema
    },
    "increase_volume": {
        "category": "media",
        "description": "Increase the master system audio volume by a default step of 10%.",
        "schema_class": schemas.IncreaseVolumeSchema
    },
    "decrease_volume": {
        "category": "media",
        "description": "Decrease the master system audio volume by a default step of 10%.",
        "schema_class": schemas.DecreaseVolumeSchema
    },
    "take_screenshot": {
        "category": "media",
        "description": "Capture the entire screen and save it as a PNG image.",
        "schema_class": schemas.TakeScreenshotSchema
    },

    # --- system ---
    "set_brightness": {
        "category": "system",
        "description": "Set the display brightness between 0 and 100 percent.",
        "schema_class": schemas.SetBrightnessSchema
    },
    "increase_brightness": {
        "category": "system",
        "description": "Increase the display screen brightness by a default step of 10%.",
        "schema_class": schemas.IncreaseBrightnessSchema
    },
    "decrease_brightness": {
        "category": "system",
        "description": "Decrease the display screen brightness by a default step of 10%.",
        "schema_class": schemas.DecreaseBrightnessSchema
    },

    # --- ocr ---
    "extract_text_from_image": {
        "category": "ocr",
        "description": "Extract text from an image using OCR.",
        "schema_class": schemas.ExtractTextFromImageSchema
    },

    # --- text ---
    "open_notepad_and_write": {
        "category": "text",
        "description": "Launch Windows Notepad and populate it with text.",
        "schema_class": schemas.OpenNotepadAndWriteSchema
    },

    # --- clipboard ---
    "clear_clipboard": {
        "category": "clipboard",
        "description": "Clear the Windows clipboard.",
        "schema_class": schemas.ClearClipboardSchema
    },
    "get_clipboard": {
        "category": "clipboard",
        "description": "Retrieve the current text content of the Windows clipboard.",
        "schema_class": schemas.GetClipboardSchema
    },
    "set_clipboard": {
        "category": "clipboard",
        "description": "Copy specified text to the Windows clipboard.",
        "schema_class": schemas.SetClipboardSchema
    },
    "create_word": {
        "category": "documents",
        "description": "Create a new Microsoft Word document (.docx).",
        "schema_class": schemas.CreateWordSchema
    },
    "read_word": {
        "category": "documents",
        "description": "Read plain text from a Microsoft Word document (.docx).",
        "schema_class": schemas.ReadWordSchema
    },
    "edit_word": {
        "category": "documents",
        "description": "Modify (append or replace text in) a Microsoft Word document (.docx).",
        "schema_class": schemas.EditWordSchema
    },
    "create_excel": {
        "category": "documents",
        "description": "Create a new Excel workbook (.xlsx).",
        "schema_class": schemas.CreateExcelSchema
    },
    "read_excel": {
        "category": "documents",
        "description": "Read worksheet content from an Excel workbook (.xlsx).",
        "schema_class": schemas.ReadExcelSchema
    },
    "write_excel": {
        "category": "documents",
        "description": "Write a value to a cell in an Excel workbook (.xlsx).",
        "schema_class": schemas.WriteExcelSchema
    }
}

# Construct the registry list of ToolMetadata objects
_registry_tools: Dict[str, ToolMetadata] = {}
for name, info in TOOLS.items():
    _registry_tools[name] = ToolMetadata(
        name=name,
        category=info["category"],
        description=info["description"],
        schema_class=info["schema_class"]
    )

def get_tool(name: str) -> Optional[ToolMetadata]:
    """Retrieve metadata for a specific tool by name."""
    return _registry_tools.get(name)

def get_tools_by_category(category: str) -> List[ToolMetadata]:
    """Retrieve all tools belonging to a specific category."""
    return [t for t in _registry_tools.values() if t.category == category]

def list_tools() -> List[ToolMetadata]:
    """Retrieve all registered tools."""
    return list(_registry_tools.values())

def list_categories() -> List[str]:
    """Retrieve all registered categories."""
    return list(CATEGORIES.keys())
