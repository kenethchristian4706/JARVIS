"""
platform/windows/clipboard_tools.py

Windows implementation of ClipboardAPI using pyperclip.
"""

import logging
import pyperclip
from aether.platforms.common.interfaces import ClipboardAPI

logger = logging.getLogger(__name__)

class WindowsClipboardAPI(ClipboardAPI):
    def clear_clipboard(self) -> dict:
        try:
            logger.info("Clearing Windows clipboard.")
            pyperclip.copy("")
            # Verification check
            if pyperclip.paste() == "":
                return {
                    "success": True,
                    "message": "Clipboard cleared successfully."
                }
            return {
                "success": False,
                "message": "Clipboard was not cleared successfully."
            }
        except Exception as e:
            logger.error(f"Error while clearing clipboard: {e}")
            return {
                "success": False,
                "message": f"Failed to clear clipboard: {str(e)}"
            }

    def get_clipboard(self) -> dict:
        try:
            logger.info("Retrieving Windows clipboard content.")
            content = pyperclip.paste()
            return {
                "success": True,
                "message": "Successfully retrieved clipboard content.",
                "data": {
                    "content": content
                }
            }
        except Exception as e:
            logger.error(f"Error while retrieving clipboard content: {e}")
            return {
                "success": False,
                "message": f"Failed to retrieve clipboard content: {str(e)}"
            }

    def set_clipboard(self, text: str) -> dict:
        try:
            logger.info("Setting Windows clipboard content.")
            pyperclip.copy(text)
            if pyperclip.paste() == text:
                return {
                    "success": True,
                    "message": "Text copied to clipboard successfully."
                }
            return {
                "success": False,
                "message": "Failed to copy text to clipboard."
            }
        except Exception as e:
            logger.error(f"Error while copying text to clipboard: {e}")
            return {
                "success": False,
                "message": f"Failed to copy text to clipboard: {str(e)}"
            }
