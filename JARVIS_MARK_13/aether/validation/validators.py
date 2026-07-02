"""
validation/validators.py

Implements type validation and existence checks for files, folders, and applications.
"""

import os
import re
import logging
import urllib.parse
from pathlib import Path
import psutil
logger = logging.getLogger(__name__)

# Cache of installed apps (lowercase name -> path)
_installed_apps_cache = {}

def validate_level(level: int) -> bool:
    """Validates volume or brightness levels to be within [0, 100]."""
    return isinstance(level, int) and 0 <= level <= 100

def validate_url(url: str) -> bool:
    """Validates if a string is a properly formatted URL."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def scan_installed_applications() -> dict[str, str]:
    """Scans registry and common folders via platform to map installed applications."""
    from aether.platforms import platform
    return platform.app.scan_installed_applications()

def verify_app_exists(app_name: str) -> bool:
    """Checks if an application name corresponds to an installed app or executable in PATH."""
    from aether.platforms import platform
    return platform.app.verify_app_exists(app_name)

def verify_file_exists(file_path: str) -> bool:
    """Verifies if a file exists at the given path."""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False

def verify_folder_exists(folder_path: str) -> bool:
    """Verifies if a folder/directory exists at the given path."""
    try:
        path = Path(folder_path)
        return path.exists() and path.is_dir()
    except Exception:
        return False
