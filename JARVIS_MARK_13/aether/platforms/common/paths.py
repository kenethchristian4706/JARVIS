"""
platform/common/paths.py

Provides platform-independent path resolution for standard directories.
"""

import os
from pathlib import Path
from typing import List

class PlatformPaths:
    @staticmethod
    def get_home() -> Path:
        return Path.home()

    @staticmethod
    def get_desktop() -> Path:
        return Path.home() / "Desktop"

    @staticmethod
    def get_downloads() -> Path:
        return Path.home() / "Downloads"

    @staticmethod
    def get_documents() -> Path:
        return Path.home() / "Documents"

    @staticmethod
    def get_pictures() -> Path:
        return Path.home() / "Pictures"

    @staticmethod
    def get_videos() -> Path:
        return Path.home() / "Videos"

    @staticmethod
    def get_music() -> Path:
        return Path.home() / "Music"

    @staticmethod
    def get_temp() -> Path:
        # Standard temp dir path
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        if temp_dir:
            return Path(temp_dir)
        return Path("/tmp") if os.name != "nt" else Path.home() / "AppData/Local/Temp"

    @staticmethod
    def get_trash() -> Path:
        if os.name == "nt":
            # Windows Recycle Bin is not directly accessible as a normal folder path in python,
            # but we can return the virtual folder or handle send2trash.
            return Path.home() / "$Recycle.Bin"
        else:
            return Path.home() / ".Trash"

    @classmethod
    def get_user_directories(cls) -> List[Path]:
        """Returns standard directories list for search paths."""
        return [
            cls.get_desktop(),
            cls.get_downloads(),
            cls.get_documents(),
            cls.get_pictures(),
            cls.get_videos(),
            cls.get_music(),
            Path(os.getcwd())
        ]
