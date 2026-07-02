"""
tools/browser_tools.py

Implements handlers for browser operations delegating to the platform abstraction layer.
"""

from typing import Optional
from aether.platforms import platform

def search_web(query: str) -> str:
    """Searches Google for a given query in the default web browser."""
    return platform.browser.search_web(query)

def search_youtube(query: str) -> str:
    """Searches YouTube for a given query in the default web browser."""
    return platform.browser.search_youtube(query)

def open_url(url: str) -> str:
    """Opens a URL in the default web browser."""
    return platform.browser.open_url(url)

def download_file(url: str, destination: Optional[str] = None) -> str:
    """Downloads a file from a URL to the local destination directory."""
    return platform.browser.download_file(url, destination)

def open_new_tab(url: str) -> str:
    """Opens a new tab in the default web browser with the given URL."""
    return platform.browser.open_new_tab(url)

def close_tab() -> str:
    """Closes the active tab."""
    return platform.browser.close_tab()

def list_tabs() -> str:
    """Lists the open browser tabs."""
    return platform.browser.list_tabs()

def switch_tab(tab: str) -> str:
    """Switches to the specified browser tab."""
    return platform.browser.switch_tab(tab)
