"""
platform/mac/screenshot_tools.py

macOS implementation of ScreenshotAPI using native screencapture utility.
"""

import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from aether.platforms.common.interfaces import ScreenshotAPI
from aether.platforms.common.paths import PlatformPaths

logger = logging.getLogger(__name__)

class MacScreenshotAPI(ScreenshotAPI):
    def take_screenshot(self, save_path: Optional[str] = None) -> dict:
        try:
            logger.info("Taking screenshot on macOS.")
            if save_path:
                from aether.tools.file_tools import resolve_path
                p = resolve_path(save_path)
                if p.suffix == "" or p.is_dir() or save_path.endswith("/") or save_path.endswith("\\"):
                    p.mkdir(parents=True, exist_ok=True)
                    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    final_path = p / filename
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    final_path = p
            else:
                default_dir = PlatformPaths.get_pictures() / "Aether" / "Screenshots"
                default_dir.mkdir(parents=True, exist_ok=True)
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                final_path = default_dir / filename

            # Use native macOS screencapture tool (-x suppresses sound)
            subprocess.run(["screencapture", "-x", str(final_path)], check=True)
            
            saved_path_str = final_path.as_posix()
            logger.info(f"Screenshot saved successfully at: {saved_path_str}")
            return {
                "success": True,
                "message": "Screenshot saved successfully.",
                "data": {
                    "path": saved_path_str
                }
            }
        except Exception as e:
            logger.error(f"Error during screenshot capture on macOS: {e}")
            return {
                "success": False,
                "message": f"Failed to capture screenshot: {str(e)}"
            }
