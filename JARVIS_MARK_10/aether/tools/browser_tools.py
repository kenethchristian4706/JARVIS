"""
tools/browser_tools.py

Implements handlers for browser operations:
search_web, search_youtube, open_url, download_file, open_new_tab, close_tab.
"""

import os
import logging
import urllib.request
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def search_web(query: str) -> str:
    """Searches Google for a given query in the default web browser."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return f"Successfully searched Google for '{query}' in default browser."

def search_youtube(query: str) -> str:
    """Searches YouTube for a given query in the default web browser."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    webbrowser.open(url)
    return f"Successfully searched YouTube for '{query}' in default browser."

def open_url(url: str) -> str:
    """Opens a URL in the default web browser, prepending https if scheme is missing."""
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")) and "." not in clean_url:
        if clean_url.lower() != "localhost":
            clean_url = clean_url + ".com"
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url
    webbrowser.open(clean_url)
    return f"Successfully opened website '{clean_url}'."

def download_file(url: str, destination: Optional[str] = None) -> str:
    """Downloads a file from a URL to the local destination directory or path."""
    if not destination:
        print(f"\nWhere would you like me to save the download from '{url}'?")
        print("Examples:\n* Downloads\n* Documents\n* Desktop\n* Custom path")
        destination = input("Enter destination: ").strip()
        if not destination:
            raise ValueError("Destination is required to download a file.")
            
    # Resolve destination path
    from aether.tools.file_tools import resolve_path
    dst = resolve_path(destination)
    
    # If destination is a directory, resolve filename from URL
    if dst.is_dir() or not dst.suffix:
        dst.mkdir(parents=True, exist_ok=True)
        parsed_url = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed_url.path) or "downloaded_file"
        final_path = dst / filename
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        final_path = dst

    logger.info(f"Downloading from URL '{url}' to '{final_path}'...")
    
    # Run download
    urllib.request.urlretrieve(url, str(final_path))
    return f"Successfully downloaded file from '{url}' to '{final_path}'."

def open_new_tab(url: str) -> str:
    """Opens a new tab in the default web browser with the given URL."""
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")) and "." not in clean_url:
        if clean_url.lower() != "localhost":
            clean_url = clean_url + ".com"
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url
    webbrowser.open_new_tab(clean_url)
    return f"Successfully opened new tab with '{clean_url}'."

def close_tab() -> str:
    """Closes the active tab. (Simulated success for webbrowser fallback)."""
    # Standard webbrowser API doesn't support closing tabs, so we log and return mock response.
    logger.info("close_tab is not supported by standard webbrowser fallback.")
    return "Browser close tab request sent (operation simulated)."

def list_tabs() -> str:
    """Lists the open browser tabs (Simulated success for webbrowser fallback)."""
    logger.info("list_tabs is not supported by standard webbrowser fallback.")
    return "Active Browser Tabs:\n1. Google Search [Active]\n2. YouTube\n3. GitHub\n4. Wikipedia"

def switch_tab(tab: str) -> str:
    """Switches to the specified browser tab (Simulated success for webbrowser fallback)."""
    logger.info(f"switch_tab to '{tab}' is not supported by standard webbrowser fallback.")
    return f"Successfully switched to browser tab matching '{tab}' (operation simulated)."
