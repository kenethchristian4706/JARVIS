"""
registry/schemas.py

Defines the Pydantic schemas and validation models for all Aether tools.
These are used by the LLM parameter extraction stage and the validation layer.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any

# --- Application Management Schemas ---

class OpenAppSchema(BaseModel):
    app_name: str = Field(description="Name of the application to open/launch.")

class CloseAppSchema(BaseModel):
    app_name: str = Field(description="Name of the application to close/terminate.")

class SwitchToAppSchema(BaseModel):
    app_name: str = Field(description="Name of the application window to bring to the foreground.")

class ListRunningAppsSchema(BaseModel):
    pass

class ListInstalledAppsSchema(BaseModel):
    pass


# --- File Operations Schemas ---

class MoveFileSchema(BaseModel):
    source_path: str = Field(description="Path of the source file to move.")
    destination_path: Optional[str] = Field(None, description="Path of the destination folder or file.")

class CopyFileSchema(BaseModel):
    source_path: str = Field(description="Path of the source file to copy.")
    destination_path: Optional[str] = Field(None, description="Path of the destination folder or file.")

class RenameFileSchema(BaseModel):
    source_path: str = Field(description="Current filename or path to rename.")
    new_name: str = Field(description="New filename (base name only).")

class DeleteFileSchema(BaseModel):
    file_path: str = Field(description="Path of the file to delete.")

class SearchFilesSchema(BaseModel):
    query: str = Field(description="Filename query or pattern to search for.")

class OpenFileSchema(BaseModel):
    file_path: str = Field(description="Path of the file to open.")

class CreateFileSchema(BaseModel):
    file_path: str = Field(description="Path of the file to create.")
    location: Optional[str] = Field(None, description="Location folder/directory where the file should be created.")

class CreateFolderSchema(BaseModel):
    folder_name: str = Field(description="Name of the folder to create.")
    location: Optional[str] = Field(None, description="Location folder/directory where the folder should be created.")

class DeleteFolderSchema(BaseModel):
    folder_name: str = Field(description="Name of the folder to delete.")

class ListDirectorySchema(BaseModel):
    directory_path: Optional[str] = Field(None, description="Path of the directory to list.")

class CompressFilesSchema(BaseModel):
    source_paths: List[str] = Field(description="List of paths of files or folders to compress.")
    output_path: str = Field(description="Path of the output zip file to create.")

class ExtractArchiveSchema(BaseModel):
    archive_path: str = Field(description="Path of the zip archive to extract.")
    destination_path: Optional[str] = Field(None, description="Path of the destination folder to extract into.")

class FileInfoSchema(BaseModel):
    file_path: str = Field(description="Path of the file to check information for.")

class AppendFileSchema(BaseModel):
    file_path: str = Field(description="Path of the file to append to.")
    content: str = Field(description="Text content to append to the file.")


# --- Browser Operations Schemas ---

class SearchWebSchema(BaseModel):
    query: str = Field(description="Text query to search Google for.")

class SearchYoutubeSchema(BaseModel):
    query: str = Field(description="Text query to search YouTube for.")

class OpenUrlSchema(BaseModel):
    url: str = Field(description="URL to open in the browser.")

class DownloadFileSchema(BaseModel):
    url: str = Field(description="URL of the file to download.")
    destination_path: Optional[str] = Field(None, description="Path of the destination directory to save the download.")

class OpenNewTabSchema(BaseModel):
    url: str = Field(description="URL to open in the new browser tab.")

class CloseTabSchema(BaseModel):
    pass

class ListTabsSchema(BaseModel):
    pass

class SwitchTabSchema(BaseModel):
    tab: str = Field(description="Tab title or index to switch to.")


# --- System Control Schemas ---

class ShutdownPcSchema(BaseModel):
    pass

class RestartPcSchema(BaseModel):
    pass

class SleepPcSchema(BaseModel):
    pass

class LockPcSchema(BaseModel):
    pass

class SetVolumeSchema(BaseModel):
    level: int = Field(description="Volume level to set, between 0 and 100.", ge=0, le=100)

class MuteVolumeSchema(BaseModel):
    pass

class UnmuteVolumeSchema(BaseModel):
    pass

class SetBrightnessSchema(BaseModel):
    level: int = Field(description="Brightness level to set, between 0 and 100.", ge=0, le=100)


# --- Phase 1 Additional Schemas ---

class TakeScreenshotSchema(BaseModel):
    save_path: Optional[str] = Field(None, description="Optional custom folder path or file path to save the screenshot as a PNG. Defaults to Pictures directory.")

class ExtractTextFromImageSchema(BaseModel):
    image_path: str = Field(description="Path of the image to extract text from.")

class OpenNotepadAndWriteSchema(BaseModel):
    text: str = Field(description="Text to write into the launched Notepad window.")

class ReadFileContentSchema(BaseModel):
    file_path: str = Field(description="Path of the file to read content from.")

class ClearClipboardSchema(BaseModel):
    pass

class GetClipboardSchema(BaseModel):
    pass

class SetClipboardSchema(BaseModel):
    clipboard_text: str = Field(description="Text to copy/write to the Windows clipboard.")

class IncreaseVolumeSchema(BaseModel):
    pass

class DecreaseVolumeSchema(BaseModel):
    pass

class IncreaseBrightnessSchema(BaseModel):
    pass

class DecreaseBrightnessSchema(BaseModel):
    pass


# --- browser_operations additional schemas ---

class SendEmailSchema(BaseModel):
    recipient: str = Field(description="Recipient email address.")
    subject: str = Field(description="Subject line of the email.")
    body: str = Field(description="Body content of the email.")
    confirmed: Optional[bool] = Field(False, description="Whether the user confirmed sending the email.")

class ListEmailsSchema(BaseModel):
    limit: Optional[int] = Field(10, description="The maximum number of emails to retrieve (default: 10).")
    unread_only: Optional[bool] = Field(False, description="If True, retrieve only unread emails (default: False).")

class ReadEmailSchema(BaseModel):
    email_id: Optional[str] = Field("latest", description="The ID/UID of the email to read, or 'latest' to read the most recent email.")
    sender: Optional[str] = Field(None, description="Optional sender name or email address to search for and read.")
    date: Optional[str] = Field(None, description="Optional date (e.g. 'yesterday', '2026-06-28') to search for and read.")


# --- Document Operations Schemas ---

class CreateWordSchema(BaseModel):
    filename: str = Field(description="The name of the Word document file to create.")
    directory: Optional[str] = Field(None, description="Optional directory path where the document should be created.")
    content: Optional[str] = Field(None, description="Optional text content to populate in the first paragraph.")
    overwrite: Optional[bool] = Field(False, description="Whether to overwrite if file already exists.")

class ReadWordSchema(BaseModel):
    file_path: str = Field(description="The name or path of the Word document file to read.")

class EditWordSchema(BaseModel):
    file_path: str = Field(description="The name or path of the Word document file to edit.")
    operation: str = Field(description="The editing operation to perform: 'append' or 'replace'.")
    text: Optional[str] = Field(None, description="Text to append (only used for 'append' operation).")
    old_text: Optional[str] = Field(None, description="The text to find and replace (only used for 'replace' operation).")
    new_text: Optional[str] = Field(None, description="The replacement text (only used for 'replace' operation).")

class CreateExcelSchema(BaseModel):
    filename: str = Field(description="The name of the Excel workbook file to create.")
    directory: Optional[str] = Field(None, description="Optional directory path where the workbook should be created.")
    sheet_name: Optional[str] = Field("Sheet1", description="Optional name of the worksheet to create.")
    overwrite: Optional[bool] = Field(False, description="Whether to overwrite if file already exists.")

class ReadExcelSchema(BaseModel):
    file_path: str = Field(description="The name or path of the Excel workbook file to read.")
    sheet_name: Optional[str] = Field(None, description="Optional name of the sheet to read.")
    cell_range: Optional[str] = Field(None, description="Optional cell range to read (e.g. 'A1:C10').")

class WriteExcelSchema(BaseModel):
    file_path: str = Field(description="The name or path of the Excel workbook file to write.")
    sheet_name: str = Field("Sheet1", description="The name of the sheet to update.")
    cell: str = Field(description="The target cell coordinate (e.g. 'A1').")
    value: Any = Field(description="The value to write into the cell.")

