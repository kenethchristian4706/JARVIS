"""
schemas.py

Defines the JSON schemas and Pydantic validation models for Aether tools.
Generates standard JSON Schemas dynamically using Pydantic's model_json_schema().
"""

from typing import Dict, Any, Type
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# 1. Pydantic Models for Validation
# ----------------------------------------------------------------------

class OpenApp(BaseModel):
    app_name: str = Field(description="Name of the application to open (e.g., 'chrome', 'spotify').")

class OpenNotepadAndWrite(BaseModel):
    app_name: str = Field(description="Name of the notepad or text editor application. Usually 'notepad'.")
    text: str = Field(description="Text content to be written inside the notepad.")

class CreateFile(BaseModel):
    filename: str = Field(description="Name of the file to be created, including its extension (e.g., 'notes.txt').")

class MoveFile(BaseModel):
    source: str = Field(description="Source path or name of the file to move.")
    destination: str = Field(description="Destination path or folder where the file will be moved.")

class CreateFolder(BaseModel):
    folder_name: str = Field(description="Name of the new folder to create.")

class SetVolume(BaseModel):
    volume: int = Field(description="Target volume level as an integer percentage (e.g., 50).")

class ShutdownSystem(BaseModel):
    pass  # No arguments needed

# ----------------------------------------------------------------------
# 2. Tool Registry mapping tool names to schemas and descriptions
# ----------------------------------------------------------------------

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "open_app": {
        "description": "Open or launch an application installed on the computer.",
        "json_schema": OpenApp.model_json_schema(),
        "validator": OpenApp
    },
    "open_notepad_and_write": {
        "description": "Open Notepad and write specified text.",
        "json_schema": OpenNotepadAndWrite.model_json_schema(),
        "validator": OpenNotepadAndWrite
    },
    "create_file": {
        "description": "Create a new file.",
        "json_schema": CreateFile.model_json_schema(),
        "validator": CreateFile
    },
    "move_file": {
        "description": "Move a file from one location to another.",
        "json_schema": MoveFile.model_json_schema(),
        "validator": MoveFile
    },
    "create_folder": {
        "description": "Create a new folder.",
        "json_schema": CreateFolder.model_json_schema(),
        "validator": CreateFolder
    },
    "set_volume": {
        "description": "Adjust system volume.",
        "json_schema": SetVolume.model_json_schema(),
        "validator": SetVolume
    },
    "shutdown_system": {
        "description": "Shutdown the computer.",
        "json_schema": {},
        "validator": ShutdownSystem
    }
}
