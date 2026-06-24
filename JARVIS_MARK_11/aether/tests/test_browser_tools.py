"""
tests/test_browser_tools.py

Unit tests for Aether's browser tools focusing on URL domain expansion.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.tools.browser_tools import open_url, open_new_tab

@patch("webbrowser.open")
def test_open_url_domain_expansion(mock_web_open):
    # 1. Test name without scheme or dot is expanded to .com and https
    result = open_url("youtube")
    assert "https://youtube.com" in result
    mock_web_open.assert_called_once_with("https://youtube.com")
    mock_web_open.reset_mock()

    # 2. Test name with dot is not expanded with .com, just https prepended
    result = open_url("google.com")
    assert "https://google.com" in result
    mock_web_open.assert_called_once_with("https://google.com")
    mock_web_open.reset_mock()

    # 3. Test name with scheme is not touched at all
    result = open_url("http://myintranet")
    assert "http://myintranet" in result
    mock_web_open.assert_called_once_with("http://myintranet")
    mock_web_open.reset_mock()

    # 4. Test localhost is not expanded to localhost.com
    result = open_url("localhost")
    assert "https://localhost" in result
    mock_web_open.assert_called_once_with("https://localhost")
    mock_web_open.reset_mock()


@patch("webbrowser.open_new_tab")
def test_open_new_tab_domain_expansion(mock_web_open_new):
    # 1. Test name without scheme or dot is expanded
    result = open_new_tab("wikipedia")
    assert "https://wikipedia.com" in result
    mock_web_open_new.assert_called_once_with("https://wikipedia.com")
    mock_web_open_new.reset_mock()

    # 2. Test name with dot is not expanded
    result = open_new_tab("wikipedia.org")
    assert "https://wikipedia.org" in result
    mock_web_open_new.assert_called_once_with("https://wikipedia.org")
    mock_web_open_new.reset_mock()
