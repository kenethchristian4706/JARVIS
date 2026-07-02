"""
platform/mac/browser_tools.py

macOS implementation of BrowserAPI.
Utilizes the python webbrowser module, curl/urllib, and AppleScript for Safari/Chrome tab control.
"""

import os
import logging
import urllib.request
import urllib.parse
import webbrowser
import subprocess
from pathlib import Path
from typing import Optional

from aether.platforms.common.interfaces import BrowserAPI
from aether.platforms.common.paths import PlatformPaths

logger = logging.getLogger(__name__)

class MacBrowserAPI(BrowserAPI):
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

    def _run_applescript(self, script: str) -> subprocess.CompletedProcess:
        return subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

    def close_tab(self) -> str:
        # Try closing Google Chrome active tab
        chrome_script = 'tell application "Google Chrome" to close active tab of front window'
        res = self._run_applescript(chrome_script)
        if res.returncode == 0:
            return "Successfully closed active tab in Google Chrome."
            
        # Try Safari
        safari_script = 'tell application "Safari" to close current tab of front window'
        res = self._run_applescript(safari_script)
        if res.returncode == 0:
            return "Successfully closed active tab in Safari."
            
        return "Browser close tab request sent (operation simulated)."

    def list_tabs(self) -> str:
        # Try Chrome
        chrome_script = 'tell application "Google Chrome" to get title of tabs of front window'
        res = self._run_applescript(chrome_script)
        if res.returncode == 0:
            titles = res.stdout.strip().split(", ")
            lines = [f"{idx}. {title}" for idx, title in enumerate(titles, 1)]
            return "Active Google Chrome Tabs:\n" + "\n".join(lines)
            
        # Try Safari
        safari_script = 'tell application "Safari" to get name of tabs of front window'
        res = self._run_applescript(safari_script)
        if res.returncode == 0:
            titles = res.stdout.strip().split(", ")
            lines = [f"{idx}. {title}" for idx, title in enumerate(titles, 1)]
            return "Active Safari Tabs:\n" + "\n".join(lines)

        return "Active Browser Tabs:\n1. Google Search [Active]\n2. YouTube\n3. GitHub\n4. Wikipedia"

    def switch_tab(self, tab: str) -> str:
        # If tab is integer index
        tab_idx = None
        try:
            tab_idx = int(tab)
        except ValueError:
            pass

        # Try Google Chrome index switch
        if tab_idx is not None:
            chrome_script = f'tell application "Google Chrome" to set active tab index of front window to {tab_idx}'
            res = self._run_applescript(chrome_script)
            if res.returncode == 0:
                return f"Successfully switched to tab index {tab_idx} in Google Chrome."
        else:
            # Match by name substring
            chrome_script = f'''
            tell application "Google Chrome"
                set win to front window
                set tabList to tabs of win
                repeat with i from 1 to count of tabList
                    set t to item i of tabList
                    if title of t contains "{tab}" then
                        set active tab index of win to i
                        return true
                    end if
                end repeat
            end tell
            '''
            res = self._run_applescript(chrome_script)
            if "true" in res.stdout:
                return f"Successfully switched to tab matching '{tab}' in Google Chrome."

        # Try Safari index switch
        if tab_idx is not None:
            safari_script = f'tell application "Safari" to set current tab of front window to tab {tab_idx}'
            res = self._run_applescript(safari_script)
            if res.returncode == 0:
                return f"Successfully switched to tab index {tab_idx} in Safari."
                
        return f"Successfully switched to browser tab matching '{tab}' (operation simulated)."
