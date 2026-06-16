"""
validation/schemas.py

Defines standard Pydantic models for validation and registries for all Aether MVP tools.
Used by the validation layer and parameter extractor.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, conint

# --- App Management ---
class OpenAppSchema(BaseModel):
    app_name: str = Field(..., description="Name of the application to open (e.g., 'chrome', 'spotify').")

class CloseAppSchema(BaseModel):
    app_name: str = Field(..., description="Name of the application to close/terminate.")

class ListInstalledAppsSchema(BaseModel):
    pass

# --- Audio Settings ---
class SetVolumeSchema(BaseModel):
    volume: conint(ge=0, le=100) = Field(..., description="Target system volume percentage (0 to 100).")

class IncreaseVolumeSchema(BaseModel):
    pass

class DecreaseVolumeSchema(BaseModel):
    pass

class MuteVolumeSchema(BaseModel):
    pass

class UnmuteVolumeSchema(BaseModel):
    pass

# --- Display Brightness ---
class SetBrightnessSchema(BaseModel):
    brightness: conint(ge=0, le=100) = Field(..., description="Target display brightness percentage (0 to 100).")

class IncreaseBrightnessSchema(BaseModel):
    pass

class DecreaseBrightnessSchema(BaseModel):
    pass

# --- File Management ---
class SearchFileSchema(BaseModel):
    filename: str = Field(..., description="Name of the file to search for.")

class OpenFileSchema(BaseModel):
    filename: str = Field(..., description="Name or path of the file to open.")

class CreateFileSchema(BaseModel):
    filename: str = Field(..., description="Name of the new file to create.")

class DeleteFileSchema(BaseModel):
    filename: str = Field(..., description="Name or path of the file to delete.")

class RenameFileSchema(BaseModel):
    filename: str = Field(..., description="Current file name or path.")
    new_name: str = Field(..., description="New file name.")

class MoveFileSchema(BaseModel):
    source: str = Field(..., description="Path/name of the file to move.")
    destination: str = Field(..., description="Target directory or folder path.")

class CopyFileSchema(BaseModel):
    source: str = Field(..., description="Path/name of the file to copy.")
    destination: str = Field(..., description="Target directory or folder path.")

# --- Folder Management ---
class CreateFolderSchema(BaseModel):
    folder_name: str = Field(..., description="Name of the new folder to create.")

class DeleteFolderSchema(BaseModel):
    folder_name: str = Field(..., description="Name or path of the folder to delete.")

class RenameFolderSchema(BaseModel):
    folder_name: str = Field(..., description="Current folder name or path.")
    new_name: str = Field(..., description="New folder name.")

# --- Notepad Operations ---
class OpenNotepadAndWriteSchema(BaseModel):
    app_name: str = Field("notepad", description="Name of the text editor application.")
    text: str = Field(..., description="Text content to write.")

class AppendToFileSchema(BaseModel):
    filename: str = Field(..., description="Name or path of the file to write to.")
    text: str = Field(..., description="Text content to append.")

class ReadFileContentSchema(BaseModel):
    filename: str = Field(..., description="Name or path of the file to read.")

# --- Screenshot ---
class TakeScreenshotSchema(BaseModel):
    pass

# --- System Control ---
class ShutdownSystemSchema(BaseModel):
    pass

# Tool Schema registry mapping tool names to schemas
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "open_app": {
        "description": "Open or launch an application installed on the computer.",
        "json_schema": OpenAppSchema.model_json_schema(),
        "validator": OpenAppSchema
    },
    "close_app": {
        "description": "Close or terminate a running application.",
        "json_schema": CloseAppSchema.model_json_schema(),
        "validator": CloseAppSchema
    },
    "list_installed_apps": {
        "description": "List all applications installed on the computer.",
        "json_schema": {},
        "validator": ListInstalledAppsSchema
    },
    "set_volume": {
        "description": "Adjust system volume.",
        "json_schema": SetVolumeSchema.model_json_schema(),
        "validator": SetVolumeSchema
    },
    "increase_volume": {
        "description": "Increase the system volume.",
        "json_schema": {},
        "validator": IncreaseVolumeSchema
    },
    "decrease_volume": {
        "description": "Decrease the system volume.",
        "json_schema": {},
        "validator": DecreaseVolumeSchema
    },
    "mute_volume": {
        "description": "Mute system audio.",
        "json_schema": {},
        "validator": MuteVolumeSchema
    },
    "unmute_volume": {
        "description": "Unmute system audio.",
        "json_schema": {},
        "validator": UnmuteVolumeSchema
    },
    "set_brightness": {
        "description": "Adjust display brightness to percentage.",
        "json_schema": SetBrightnessSchema.model_json_schema(),
        "validator": SetBrightnessSchema
    },
    "increase_brightness": {
        "description": "Increase screen brightness.",
        "json_schema": {},
        "validator": IncreaseBrightnessSchema
    },
    "decrease_brightness": {
        "description": "Decrease screen brightness.",
        "json_schema": {},
        "validator": DecreaseBrightnessSchema
    },
    "search_file": {
        "description": "Search for files on the computer.",
        "json_schema": SearchFileSchema.model_json_schema(),
        "validator": SearchFileSchema
    },
    "open_file": {
        "description": "Open an existing file on the computer.",
        "json_schema": OpenFileSchema.model_json_schema(),
        "validator": OpenFileSchema
    },
    "create_file": {
        "description": "Create a new blank file.",
        "json_schema": CreateFileSchema.model_json_schema(),
        "validator": CreateFileSchema
    },
    "delete_file": {
        "description": "Delete or remove an existing file.",
        "json_schema": DeleteFileSchema.model_json_schema(),
        "validator": DeleteFileSchema
    },
    "rename_file": {
        "description": "Rename an existing file.",
        "json_schema": RenameFileSchema.model_json_schema(),
        "validator": RenameFileSchema
    },
    "move_file": {
        "description": "Move a file from one location to another.",
        "json_schema": MoveFileSchema.model_json_schema(),
        "validator": MoveFileSchema
    },
    "copy_file": {
        "description": "Copy a file to another location.",
        "json_schema": CopyFileSchema.model_json_schema(),
        "validator": CopyFileSchema
    },
    "create_folder": {
        "description": "Create a new folder.",
        "json_schema": CreateFolderSchema.model_json_schema(),
        "validator": CreateFolderSchema
    },
    "delete_folder": {
        "description": "Delete or remove an existing folder.",
        "json_schema": DeleteFolderSchema.model_json_schema(),
        "validator": DeleteFolderSchema
    },
    "rename_folder": {
        "description": "Rename an existing folder.",
        "json_schema": RenameFolderSchema.model_json_schema(),
        "validator": RenameFolderSchema
    },
    "open_notepad_and_write": {
        "description": "Open Notepad and write specified text.",
        "json_schema": OpenNotepadAndWriteSchema.model_json_schema(),
        "validator": OpenNotepadAndWriteSchema
    },
    "append_to_file": {
        "description": "Append text to the end of a file.",
        "json_schema": AppendToFileSchema.model_json_schema(),
        "validator": AppendToFileSchema
    },
    "read_file_content": {
        "description": "Read and return the text content of a file.",
        "json_schema": ReadFileContentSchema.model_json_schema(),
        "validator": ReadFileContentSchema
    },
    "take_screenshot": {
        "description": "Capture a screenshot of the screen.",
        "json_schema": {},
        "validator": TakeScreenshotSchema
    },
    "shutdown_system": {
        "description": "Shut down the computer.",
        "json_schema": {},
        "validator": ShutdownSystemSchema
    }
}
