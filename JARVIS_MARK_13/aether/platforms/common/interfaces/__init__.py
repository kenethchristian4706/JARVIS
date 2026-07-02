"""
platform/common/interfaces/__init__.py

Defines the abstract base classes (ABCs) that serve as the common interfaces
for platform-specific modules in Aether. All platforms must implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ApplicationAPI(ABC):
    @abstractmethod
    def open_app(self, app_name: str) -> str:
        pass

    @abstractmethod
    def close_app(self, app_name: str) -> str:
        pass

    @abstractmethod
    def switch_to_app(self, app_name: str) -> str:
        pass

    @abstractmethod
    def list_running_apps(self) -> List[str]:
        pass

    @abstractmethod
    def list_installed_apps(self) -> List[str]:
        pass

    @abstractmethod
    def verify_app_exists(self, app_name: str) -> bool:
        pass


class BrowserAPI(ABC):
    @abstractmethod
    def search_web(self, query: str) -> str:
        pass

    @abstractmethod
    def search_youtube(self, query: str) -> str:
        pass

    @abstractmethod
    def open_url(self, url: str) -> str:
        pass

    @abstractmethod
    def download_file(self, url: str, destination: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def open_new_tab(self, url: str) -> str:
        pass

    @abstractmethod
    def close_tab(self) -> str:
        pass

    @abstractmethod
    def list_tabs(self) -> str:
        pass

    @abstractmethod
    def switch_tab(self, tab: str) -> str:
        pass


class FileAPI(ABC):
    @abstractmethod
    def move_file(self, source: str, destination: str) -> str:
        pass

    @abstractmethod
    def copy_file(self, source: str, destination: str) -> str:
        pass

    @abstractmethod
    def rename_file(self, source: str, new_name: str) -> str:
        pass

    @abstractmethod
    def delete_file(self, path: str) -> str:
        pass

    @abstractmethod
    def open_file(self, path: str) -> str:
        pass

    @abstractmethod
    def create_folder(self, folder_name: str, location: str) -> str:
        pass

    @abstractmethod
    def create_file(self, filename: str, location: str) -> str:
        pass

    @abstractmethod
    def delete_folder(self, folder_name: str) -> str:
        pass

    @abstractmethod
    def list_directory(self, path: str) -> str:
        pass

    @abstractmethod
    def file_info(self, path: str) -> str:
        pass

    @abstractmethod
    def append_file(self, filename: str, text: str) -> str:
        pass

    @abstractmethod
    def read_file_content(self, file_path: str) -> str:
        pass

    @abstractmethod
    def compress_files(self, sources: List[str], output: str) -> str:
        pass

    @abstractmethod
    def extract_archive(self, archive: str, destination: str) -> str:
        pass

    @abstractmethod
    def extract_text_from_image(self, path: str) -> dict:
        pass

    @abstractmethod
    def get_indexed_paths(self) -> List[Any]:
        pass


class WindowAPI(ABC):
    @abstractmethod
    def move_window(self, title: str, x: int, y: int) -> str:
        pass

    @abstractmethod
    def resize_window(self, title: str, width: int, height: int) -> str:
        pass

    @abstractmethod
    def focus_window(self, title: str) -> str:
        pass

    @abstractmethod
    def close_window(self, title: str) -> str:
        pass

    @abstractmethod
    def list_windows(self) -> List[str]:
        pass

    @abstractmethod
    def get_active_window(self) -> str:
        pass


class ClipboardAPI(ABC):
    @abstractmethod
    def clear_clipboard(self) -> dict:
        pass

    @abstractmethod
    def get_clipboard(self) -> dict:
        pass

    @abstractmethod
    def set_clipboard(self, text: str) -> dict:
        pass


class ScreenshotAPI(ABC):
    @abstractmethod
    def take_screenshot(self, save_path: Optional[str] = None) -> dict:
        pass


class NotificationAPI(ABC):
    @abstractmethod
    def send_notification(self, title: str, message: str) -> str:
        pass


class PowerAPI(ABC):
    @abstractmethod
    def shutdown_pc(self) -> str:
        pass

    @abstractmethod
    def restart_pc(self) -> str:
        pass

    @abstractmethod
    def sleep_pc(self) -> str:
        pass

    @abstractmethod
    def lock_pc(self) -> str:
        pass


class SystemAPI(ABC):
    @abstractmethod
    def set_volume(self, level: int) -> str:
        pass

    @abstractmethod
    def mute_volume(self) -> str:
        pass

    @abstractmethod
    def unmute_volume(self) -> str:
        pass

    @abstractmethod
    def increase_volume(self) -> str:
        pass

    @abstractmethod
    def decrease_volume(self) -> str:
        pass

    @abstractmethod
    def set_brightness(self, level: int) -> str:
        pass

    @abstractmethod
    def increase_brightness(self) -> str:
        pass

    @abstractmethod
    def decrease_brightness(self) -> str:
        pass

    @abstractmethod
    def open_notepad_and_write(self, text: str) -> dict:
        pass
