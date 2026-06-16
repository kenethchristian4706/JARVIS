"""
ai/parameter_extractor/schemas.py

Defines Pydantic v2 validation schemas for all 56 Aether tools, and registers
them in the global TOOL_REGISTRY mapping tool names to schemas and validators.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# --- APPLICATION TOOLS ---
class OpenApp(BaseModel):
    app_name: str = Field(description="Name of the app to open. e.g. 'chrome', 'vs code', 'spotify'.")

class CloseApp(BaseModel):
    app_name: str = Field(description="Name of the running app to close.")

class SwitchToApp(BaseModel):
    app_name: str = Field(description="Name of the running app to switch focus to.")

class ListRunningApps(BaseModel):
    pass

class ListInstalledApps(BaseModel):
    pass

# --- SYSTEM CONTROL ---
class ShutdownSystem(BaseModel):
    pass

class RestartSystem(BaseModel):
    pass

class SleepSystem(BaseModel):
    pass

class LockSystem(BaseModel):
    pass

class LogoutUser(BaseModel):
    pass

# --- AUDIO ---
class SetVolume(BaseModel):
    volume: int = Field(ge=0, le=100, description="Target volume 0-100.")

class IncreaseVolume(BaseModel):
    amount: Optional[int] = Field(default=10, ge=1, le=100, description="Amount to increase by. Default 10.")

class DecreaseVolume(BaseModel):
    amount: Optional[int] = Field(default=10, ge=1, le=100, description="Amount to decrease by. Default 10.")

class MuteVolume(BaseModel):
    pass

class UnmuteVolume(BaseModel):
    pass

# --- BRIGHTNESS ---
class SetBrightness(BaseModel):
    brightness: int = Field(ge=0, le=100, description="Target brightness 0-100.")

class IncreaseBrightness(BaseModel):
    amount: Optional[int] = Field(default=10, ge=1, le=100, description="Amount to increase by. Default 10.")

class DecreaseBrightness(BaseModel):
    amount: Optional[int] = Field(default=10, ge=1, le=100, description="Amount to decrease by. Default 10.")

# --- CLIPBOARD ---
class CopyToClipboard(BaseModel):
    text: str = Field(description="Text content to copy to the clipboard.")

class ReadClipboard(BaseModel):
    pass

class ClearClipboard(BaseModel):
    pass

# --- FILE MANAGEMENT ---
class SearchFile(BaseModel):
    query: str = Field(description="Filename or keyword to search for in the file index.")

class OpenFile(BaseModel):
    filename: str = Field(description="Name or path of the file to open.")

class CreateFile(BaseModel):
    filename: str = Field(description="Name or path of the file to create, including directory if specified by the user (e.g. 'downloads/system.log' or 'notes.txt').")
    content: Optional[str] = Field(default=None, description="Optional initial content for the file.")

class DeleteFile(BaseModel):
    filename: str = Field(description="Name or path of the file to delete.")

class RenameFile(BaseModel):
    source: str = Field(description="Current filename or path.")
    destination: str = Field(description="New filename.")

class MoveFile(BaseModel):
    source: str = Field(description="Source filename or path.")
    destination: str = Field(description="Destination folder path.")

class CopyFile(BaseModel):
    source: str = Field(description="Source filename or path.")
    destination: str = Field(description="Destination folder path.")

# --- FOLDER MANAGEMENT ---
class CreateFolder(BaseModel):
    folder_name: str = Field(description="Name or path of the folder to create, including parent directory if specified (e.g. 'downloads/work').")

class DeleteFolder(BaseModel):
    folder_name: str = Field(description="Name or path of the folder to delete.")

class RenameFolder(BaseModel):
    source: str = Field(description="Current folder name or path.")
    destination: str = Field(description="New folder name.")

# --- FILE CONTENT ---
class OpenNotepadAndWrite(BaseModel):
    app_name: str = Field(default="notepad", description="Text editor app. Usually 'notepad'.")
    text: str = Field(description="Text content to type into the editor.")

class AppendToFile(BaseModel):
    filename: str = Field(description="Name or path of the file to append to, including directory prefix if specified (e.g. 'downloads/notes.txt').")
    text: str = Field(description="Text to append to the end of the file.")

class ReadFileContent(BaseModel):
    filename: str = Field(description="Name or path of the file to read, including directory prefix if specified (e.g. 'downloads/notes.txt').")

# --- SCREENSHOT / OCR ---
class TakeScreenshot(BaseModel):
    filename: Optional[str] = Field(default=None, description="Optional filename to save the screenshot. Auto-generated if not provided.")

class ExtractTextFromImage(BaseModel):
    filename: str = Field(description="Path or name of the image file to extract text from.")

# --- ADVANCED SEARCH ---
class SemanticFileSearch(BaseModel):
    query: str = Field(description="Semantic description of what to search for. e.g. 'AI project files'.")

class RecentFiles(BaseModel):
    hours: Optional[int] = Field(default=24, ge=1, description="How many hours back to look. Default 24.")

class FilesByExtension(BaseModel):
    extension: str = Field(description="File extension without dot. e.g. 'pdf', 'txt', 'py'.")

class FilesByDate(BaseModel):
    date_description: str = Field(description="Natural language date. e.g. 'yesterday', 'last week', '2026-01-01'.")

# --- BROWSER ---
class OpenWebsite(BaseModel):
    url: str = Field(description="Full URL or domain to open. e.g. 'https://google.com' or 'github.com'.")

class CloseBrowser(BaseModel):
    pass

class OpenNewTab(BaseModel):
    pass

class SwitchTab(BaseModel):
    tab_identifier: str = Field(description="Tab number, URL fragment, or title keyword. e.g. '2', 'github', 'youtube'.")

class CloseTab(BaseModel):
    tab_identifier: Optional[str] = Field(default=None, description="Tab to close. Closes current tab if not specified.")

# --- WEB SEARCH ---
class GoogleSearch(BaseModel):
    query: str = Field(description="Search query to look up on Google.")

class YoutubeSearch(BaseModel):
    query: str = Field(description="Search query to look up on YouTube.")

class WebsiteSearch(BaseModel):
    site: str = Field(description="Domain to search within. e.g. 'wikipedia.org', 'stackoverflow.com'.")
    query: str = Field(description="Search query to look up within that site.")

# --- WEB INTERACTION ---
class FillForm(BaseModel):
    field_identifier: str = Field(description="Field name, label, or id to fill. e.g. 'email', 'username'.")
    value: str = Field(description="Value to enter into the field.")

class SubmitForm(BaseModel):
    pass

class ClickElement(BaseModel):
    element_identifier: str = Field(description="Element to click: button text, id, label. e.g. 'login button', 'submit'.")

class TypeText(BaseModel):
    text: str = Field(description="Text to type into the currently focused input.")

class ScrollPage(BaseModel):
    direction: str = Field(description="Direction: 'up', 'down', 'top', 'bottom'.")
    amount: Optional[int] = Field(default=300, description="Pixels to scroll. Default 300.")

# --- FILE TRANSFER ---
class DownloadFile(BaseModel):
    url: str = Field(description="URL of the file to download.")
    destination: Optional[str] = Field(default=None, description="Optional local save path.")

class UploadFile(BaseModel):
    filename: str = Field(description="Local file path to upload.")
    field_identifier: Optional[str] = Field(default=None, description="Upload field identifier if needed.")

# --- BROWSER AGENT ---
class BrowserAgent(BaseModel):
    task: str = Field(description="Full description of the multi-step web task to complete.")


# --- TOOL REGISTRY ---
# Map tool names to their descriptions, JSON schemas, and validators
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "open_app": {
        "description": "Open or launch a local application on the computer.",
        "json_schema": OpenApp.model_json_schema(),
        "validator": OpenApp
    },
    "close_app": {
        "description": "Terminate or close a running application.",
        "json_schema": CloseApp.model_json_schema(),
        "validator": CloseApp
    },
    "switch_to_app": {
        "description": "Switch window focus to a running application.",
        "json_schema": SwitchToApp.model_json_schema(),
        "validator": SwitchToApp
    },
    "list_running_apps": {
        "description": "List all active processes or running application windows.",
        "json_schema": {},
        "validator": ListRunningApps
    },
    "list_installed_apps": {
        "description": "List all software applications installed on the system.",
        "json_schema": {},
        "validator": ListInstalledApps
    },
    "shutdown_system": {
        "description": "Shut down the computer system completely.",
        "json_schema": {},
        "validator": ShutdownSystem
    },
    "restart_system": {
        "description": "Reboot or restart the computer system.",
        "json_schema": {},
        "validator": RestartSystem
    },
    "sleep_system": {
        "description": "Put the computer system into sleep mode.",
        "json_schema": {},
        "validator": SleepSystem
    },
    "lock_system": {
        "description": "Lock the Windows user session.",
        "json_schema": {},
        "validator": LockSystem
    },
    "logout_user": {
        "description": "Log out the current user session.",
        "json_schema": {},
        "validator": LogoutUser
    },
    "set_volume": {
        "description": "Set system master volume to a specific level (0-100).",
        "json_schema": SetVolume.model_json_schema(),
        "validator": SetVolume
    },
    "increase_volume": {
        "description": "Increase system master volume.",
        "json_schema": IncreaseVolume.model_json_schema(),
        "validator": IncreaseVolume
    },
    "decrease_volume": {
        "description": "Decrease system master volume.",
        "json_schema": DecreaseVolume.model_json_schema(),
        "validator": DecreaseVolume
    },
    "mute_volume": {
        "description": "Mute system audio output.",
        "json_schema": {},
        "validator": MuteVolume
    },
    "unmute_volume": {
        "description": "Unmute system audio output.",
        "json_schema": {},
        "validator": UnmuteVolume
    },
    "set_brightness": {
        "description": "Set screen brightness to a specific level (0-100).",
        "json_schema": SetBrightness.model_json_schema(),
        "validator": SetBrightness
    },
    "increase_brightness": {
        "description": "Increase display screen brightness.",
        "json_schema": IncreaseBrightness.model_json_schema(),
        "validator": IncreaseBrightness
    },
    "decrease_brightness": {
        "description": "Decrease display screen brightness.",
        "json_schema": DecreaseBrightness.model_json_schema(),
        "validator": DecreaseBrightness
    },
    "copy_to_clipboard": {
        "description": "Copy specified text to the system clipboard.",
        "json_schema": CopyToClipboard.model_json_schema(),
        "validator": CopyToClipboard
    },
    "read_clipboard": {
        "description": "Retrieve and display text currently stored on the system clipboard.",
        "json_schema": {},
        "validator": ReadClipboard
    },
    "clear_clipboard": {
        "description": "Clear all contents from the system clipboard.",
        "json_schema": {},
        "validator": ClearClipboard
    },
    "search_file": {
        "description": "Search for a file by name keyword in the database index.",
        "json_schema": SearchFile.model_json_schema(),
        "validator": SearchFile
    },
    "open_file": {
        "description": "Open an existing file using its default associated application.",
        "json_schema": OpenFile.model_json_schema(),
        "validator": OpenFile
    },
    "create_file": {
        "description": "Create a new blank or initialized file.",
        "json_schema": CreateFile.model_json_schema(),
        "validator": CreateFile
    },
    "delete_file": {
        "description": "Permanently delete an existing file from the filesystem. HIGH RISK.",
        "json_schema": DeleteFile.model_json_schema(),
        "validator": DeleteFile
    },
    "rename_file": {
        "description": "Rename an existing file.",
        "json_schema": RenameFile.model_json_schema(),
        "validator": RenameFile
    },
    "move_file": {
        "description": "Move a file from its current path to a target folder directory.",
        "json_schema": MoveFile.model_json_schema(),
        "validator": MoveFile
    },
    "copy_file": {
        "description": "Copy a file to a target folder directory.",
        "json_schema": CopyFile.model_json_schema(),
        "validator": CopyFile
    },
    "create_folder": {
        "description": "Create a new empty folder directory.",
        "json_schema": CreateFolder.model_json_schema(),
        "validator": CreateFolder
    },
    "delete_folder": {
        "description": "Permanently delete a folder directory and its contents. HIGH RISK.",
        "json_schema": DeleteFolder.model_json_schema(),
        "validator": DeleteFolder
    },
    "rename_folder": {
        "description": "Rename a folder directory.",
        "json_schema": RenameFolder.model_json_schema(),
        "validator": RenameFolder
    },
    "open_notepad_and_write": {
        "description": "Open Notepad and type specified text content.",
        "json_schema": OpenNotepadAndWrite.model_json_schema(),
        "validator": OpenNotepadAndWrite
    },
    "append_to_file": {
        "description": "Append text content to the end of a file.",
        "json_schema": AppendToFile.model_json_schema(),
        "validator": AppendToFile
    },
    "read_file_content": {
        "description": "Read and return all text contents of a file.",
        "json_schema": ReadFileContent.model_json_schema(),
        "validator": ReadFileContent
    },
    "take_screenshot": {
        "description": "Capture a screenshot image of the computer screen.",
        "json_schema": TakeScreenshot.model_json_schema(),
        "validator": TakeScreenshot
    },
    "extract_text_from_image": {
        "description": "Perform OCR to extract text from a local image file.",
        "json_schema": ExtractTextFromImage.model_json_schema(),
        "validator": ExtractTextFromImage
    },
    "semantic_file_search": {
        "description": "Perform semantic search for documents based on meaning or concepts.",
        "json_schema": SemanticFileSearch.model_json_schema(),
        "validator": SemanticFileSearch
    },
    "recent_files": {
        "description": "List recently modified files within a specific timeframe.",
        "json_schema": RecentFiles.model_json_schema(),
        "validator": RecentFiles
    },
    "files_by_extension": {
        "description": "Filter and find files matching a specific file extension.",
        "json_schema": FilesByExtension.model_json_schema(),
        "validator": FilesByExtension
    },
    "files_by_date": {
        "description": "Find files modified on or around a specific date description.",
        "json_schema": FilesByDate.model_json_schema(),
        "validator": FilesByDate
    },
    "open_website": {
        "description": "Open a website URL in the web browser.",
        "json_schema": OpenWebsite.model_json_schema(),
        "validator": OpenWebsite
    },
    "close_browser": {
        "description": "Close the active web browser application.",
        "json_schema": {},
        "validator": CloseBrowser
    },
    "open_new_tab": {
        "description": "Open a new blank tab in the active browser window.",
        "json_schema": {},
        "validator": OpenNewTab
    },
    "switch_tab": {
        "description": "Switch active tab in the browser using an identifier.",
        "json_schema": SwitchTab.model_json_schema(),
        "validator": SwitchTab
    },
    "close_tab": {
        "description": "Close a specific tab or the current tab in the browser.",
        "json_schema": CloseTab.model_json_schema(),
        "validator": CloseTab
    },
    "google_search": {
        "description": "Search the web using Google Search.",
        "json_schema": GoogleSearch.model_json_schema(),
        "validator": GoogleSearch
    },
    "youtube_search": {
        "description": "Search for videos on YouTube.",
        "json_schema": YoutubeSearch.model_json_schema(),
        "validator": YoutubeSearch
    },
    "website_search": {
        "description": "Search for terms inside a specific site domain.",
        "json_schema": WebsiteSearch.model_json_schema(),
        "validator": WebsiteSearch
    },
    "fill_form": {
        "description": "Fill a form input field in the browser web page.",
        "json_schema": FillForm.model_json_schema(),
        "validator": FillForm
    },
    "submit_form": {
        "description": "Submit the currently active browser form.",
        "json_schema": {},
        "validator": SubmitForm
    },
    "click_element": {
        "description": "Click a specific HTML element on the browser web page.",
        "json_schema": ClickElement.model_json_schema(),
        "validator": ClickElement
    },
    "type_text": {
        "description": "Type text into the focused browser element.",
        "json_schema": TypeText.model_json_schema(),
        "validator": TypeText
    },
    "scroll_page": {
        "description": "Scroll the browser web page in a specified direction.",
        "json_schema": ScrollPage.model_json_schema(),
        "validator": ScrollPage
    },
    "download_file": {
        "description": "Download a file from a URL to the local filesystem.",
        "json_schema": DownloadFile.model_json_schema(),
        "validator": DownloadFile
    },
    "upload_file": {
        "description": "Upload a local file to a web form or server endpoint.",
        "json_schema": UploadFile.model_json_schema(),
        "validator": UploadFile
    },
    "browser_agent": {
        "description": "Launch a multi-step autonomous browser agent task.",
        "json_schema": BrowserAgent.model_json_schema(),
        "validator": BrowserAgent
    }
}
