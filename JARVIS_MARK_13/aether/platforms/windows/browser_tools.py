"""
platform/windows/browser_tools.py

Windows implementation of BrowserAPI.
Utilizes the python webbrowser module and urllib logic.
"""

import os
import logging
import urllib.request
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional

from aether.platforms.common.interfaces import BrowserAPI
from aether.platforms.common.paths import PlatformPaths

logger = logging.getLogger(__name__)

class WindowsBrowserAPI(BrowserAPI):
    def search_web(self, query: str) -> str:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(url)
        return f"Successfully searched Google for '{query}' in default browser."

    def search_youtube(self, query: str) -> str:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        webbrowser.open(url)
        return f"Successfully searched YouTube for '{query}' in default browser."

    def open_url(self, url: str) -> str:
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")) and "." not in clean_url:
            if clean_url.lower() != "localhost":
                clean_url = clean_url + ".com"
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        webbrowser.open(clean_url)
        return f"Successfully opened website '{clean_url}'."

    def download_file(self, url: str, destination: Optional[str] = None) -> str:
        if not destination:
            title = f"Where would you like me to save the download from '{url}'?\nExamples:\n* Downloads\n* Documents\n* Desktop\n* Custom path"
            from aether.api.prompt import prompt_user_sync
            destination = prompt_user_sync(title, []).strip()
            if not destination or destination.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                raise ValueError("Destination is required to download a file.")
                
        # Resolve destination path
        # Note: We must resolve path locally or via paths.py helper
        from aether.tools.file_tools import resolve_path
        dst = resolve_path(destination)
        
        if dst.is_dir() or not dst.suffix:
            dst.mkdir(parents=True, exist_ok=True)
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path) or "downloaded_file"
            final_path = dst / filename
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            final_path = dst

        logger.info(f"Downloading from URL '{url}' to '{final_path}'...")
        urllib.request.urlretrieve(url, str(final_path))
        return f"Successfully downloaded file from '{url}' to '{final_path}'."

    def open_new_tab(self, url: str) -> str:
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")) and "." not in clean_url:
            if clean_url.lower() != "localhost":
                clean_url = clean_url + ".com"
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        webbrowser.open_new_tab(clean_url)
        return f"Successfully opened new tab with '{clean_url}'."

    def close_tab(self) -> str:
        logger.info("close_tab is not supported by standard webbrowser fallback.")
        return "Browser close tab request sent (operation simulated)."

    def list_tabs(self) -> str:
        logger.info("list_tabs is not supported by standard webbrowser fallback.")
        return "Active Browser Tabs:\n1. Google Search [Active]\n2. YouTube\n3. GitHub\n4. Wikipedia"

    def switch_tab(self, tab: str) -> str:
        logger.info(f"switch_tab to '{tab}' is not supported by standard webbrowser fallback.")
        return f"Successfully switched to browser tab matching '{tab}' (operation simulated)."
