"""
tests/test_phase1_tools.py

Unit tests for Phase 1 Aether tools using pytest and unittest.mock.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add project root to python path to resolve aether packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.tools.system_tools import (
    take_screenshot, open_notepad_and_write, clear_clipboard,
    get_clipboard, set_clipboard, increase_volume, decrease_volume,
    increase_brightness, decrease_brightness
)
from aether.tools.file_tools import extract_text_from_image, read_file_content, rename_file


# --- take_screenshot tests ---

@patch("pyautogui.screenshot")
def test_take_screenshot_default_path(mock_screenshot, tmp_path):
    # Mock default home directory to avoid writing to user's actual Pictures folder
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    
    with patch("pathlib.Path.home", return_value=mock_home):
        result = take_screenshot()
        
        assert result["success"] is True
        assert "Screenshot saved successfully." in result["message"]
        saved_path = Path(result["data"]["path"])
        
        # Verify default directory structure
        assert saved_path.parent == mock_home / "Pictures" / "Aether" / "Screenshots"
        assert saved_path.suffix == ".png"
        assert saved_path.name.startswith("screenshot_")
        mock_screenshot.return_value.save.assert_called_once()

@patch("pyautogui.screenshot")
def test_take_screenshot_custom_path(mock_screenshot, tmp_path):
    custom_dir = tmp_path / "custom_dir"
    custom_dir.mkdir()
    custom_file = custom_dir / "my_screenshot.png"
    
    result = take_screenshot(save_path=str(custom_file))
    
    assert result["success"] is True
    assert Path(result["data"]["path"]) == custom_file
    mock_screenshot.return_value.save.assert_called_once_with(str(custom_file))


# --- extract_text_from_image tests ---

@patch("PIL.Image.open")
@patch("pytesseract.image_to_string")
def test_extract_text_from_image_success(mock_ocr, mock_image_open, tmp_path):
    # Create dummy image file
    img_path = tmp_path / "test.png"
    img_path.touch()
    
    mock_ocr.return_value = "   Hello   World   \n  Line 2   "
    
    result = extract_text_from_image(str(img_path))
    
    assert result["success"] is True
    # Extra whitespace stripped and merged
    assert result["data"]["text"] == "Hello World Line 2"
    mock_ocr.assert_called_once()

def test_extract_text_from_image_missing_file():
    result = extract_text_from_image("non_existent_file.png")
    assert result["success"] is False
    assert "not found" in result["message"]

def test_extract_text_from_image_corrupt_file(tmp_path):
    corrupt_file = tmp_path / "corrupt.png"
    corrupt_file.write_text("not an image")
    
    result = extract_text_from_image(str(corrupt_file))
    
    assert result["success"] is False
    assert "Unsupported or corrupt" in result["message"]


# --- open_notepad_and_write tests ---

@patch("subprocess.Popen")
@patch("pygetwindow.getWindowsWithTitle")
@patch("pyautogui.write")
def test_open_notepad_and_write_success(mock_write, mock_get_windows, mock_popen):
    # Mock window retrieval
    mock_window = MagicMock()
    mock_get_windows.return_value = [mock_window]
    
    result = open_notepad_and_write("Hello from tests!")
    
    assert result["success"] is True
    assert "Notepad opened and text inserted." in result["message"]
    mock_popen.assert_called_once_with(["notepad.exe"])
    mock_window.activate.assert_called_once()
    mock_write.assert_called_once_with("Hello from tests!")

@patch("subprocess.Popen")
@patch("pygetwindow.getWindowsWithTitle")
def test_open_notepad_and_write_timeout(mock_get_windows, mock_popen):
    # No windows found
    mock_get_windows.return_value = []
    
    result = open_notepad_and_write("Hello!")
    
    assert result["success"] is False
    assert "failed to open in a timely manner" in result["message"]


# --- read_file_content tests ---

def test_read_file_content_success(tmp_path):
    text_file = tmp_path / "sample.txt"
    text_file.write_text("Hello line 1\nHello line 2", encoding="utf-8")
    
    result = read_file_content(str(text_file))
    
    assert result["success"] is True
    assert result["data"]["content"] == "Hello line 1\nHello line 2"
    assert result["data"]["size_bytes"] == os.path.getsize(str(text_file))
    assert result["data"]["encoding"] == "utf-8"

def test_read_file_content_limit(tmp_path):
    large_file = tmp_path / "large.txt"
    large_content = "A" * 15000
    large_file.write_text(large_content, encoding="utf-8")
    
    result = read_file_content(str(large_file))
    
    assert result["success"] is True
    assert len(result["data"]["content"]) == 10000
    assert result["data"]["size_bytes"] == 15000

def test_read_file_content_unsupported_format(tmp_path):
    unsupported = tmp_path / "image.png"
    unsupported.touch()
    
    result = read_file_content(str(unsupported))
    
    assert result["success"] is False
    assert "Unsupported file format" in result["message"]

def test_read_file_content_missing_file():
    result = read_file_content("non_existent_file.txt")
    assert result["success"] is False
    assert "not found" in result["message"]


# --- clear_clipboard tests ---

@patch("pyperclip.copy")
@patch("pyperclip.paste")
def test_clear_clipboard_success(mock_paste, mock_copy):
    mock_paste.return_value = ""
    
    result = clear_clipboard()
    
    assert result["success"] is True
    assert "Clipboard cleared successfully." in result["message"]
    mock_copy.assert_called_once_with("")
    mock_paste.assert_called_once()

@patch("pyperclip.copy")
@patch("pyperclip.paste")
def test_clear_clipboard_verification_failure(mock_paste, mock_copy):
    # Mock paste returning non-empty value after copy
    mock_paste.return_value = "clipboard content"
    
    result = clear_clipboard()
    
    assert result["success"] is False
    assert "was not cleared" in result["message"]


# --- get_clipboard / set_clipboard tests ---

@patch("pyperclip.paste")
def test_get_clipboard_success(mock_paste):
    mock_paste.return_value = "hello test clipboard"
    result = get_clipboard()
    assert result["success"] is True
    assert result["data"]["content"] == "hello test clipboard"
    mock_paste.assert_called_once()

@patch("pyperclip.copy")
@patch("pyperclip.paste")
def test_set_clipboard_success(mock_paste, mock_copy):
    mock_paste.return_value = "hello copied content"
    result = set_clipboard("hello copied content")
    assert result["success"] is True
    mock_copy.assert_called_once_with("hello copied content")

@patch("pyperclip.copy")
@patch("pyperclip.paste")
def test_set_clipboard_failure(mock_paste, mock_copy):
    mock_paste.return_value = "different content"
    result = set_clipboard("hello copied content")
    assert result["success"] is False
    assert "Failed to copy" in result["message"]


# --- volume / brightness step adjustments tests ---

@patch("aether.tools.system_tools._get_volume_interface")
def test_increase_volume(mock_get_vol):
    mock_vol = MagicMock()
    mock_vol.GetMasterVolumeLevelScalar.return_value = 0.5 # 50%
    mock_get_vol.return_value = mock_vol
    
    result = increase_volume()
    assert "Master volume set to 60%" in result
    mock_vol.SetMasterVolumeLevelScalar.assert_called_once_with(0.6, None)

@patch("aether.tools.system_tools._get_volume_interface")
def test_decrease_volume(mock_get_vol):
    mock_vol = MagicMock()
    mock_vol.GetMasterVolumeLevelScalar.return_value = 0.5 # 50%
    mock_get_vol.return_value = mock_vol
    
    result = decrease_volume()
    assert "Master volume set to 40%" in result
    mock_vol.SetMasterVolumeLevelScalar.assert_called_once_with(0.4, None)

@patch("screen_brightness_control.get_brightness")
@patch("screen_brightness_control.set_brightness")
def test_increase_brightness(mock_set_brightness, mock_get_brightness):
    mock_get_brightness.return_value = [50]
    
    result = increase_brightness()
    assert "Display brightness set to 60%" in result
    mock_set_brightness.assert_called_once_with(60)

@patch("screen_brightness_control.get_brightness")
@patch("screen_brightness_control.set_brightness")
def test_decrease_brightness(mock_set_brightness, mock_get_brightness):
    mock_get_brightness.return_value = [50]
    
    result = decrease_brightness()
    assert "Display brightness set to 40%" in result
    mock_set_brightness.assert_called_once_with(40)


# --- rename_file extension preservation tests ---

@patch("aether.tools.file_tools.resolve_filename")
@patch("pathlib.Path.rename")
def test_rename_file_preserves_extension(mock_rename, mock_resolve_filename):
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.suffix = ".ipynb"
    mock_path.parent = Path("C:/test_dir")
    mock_path.name = "demo.ipynb"
    mock_resolve_filename.return_value = mock_path
    
    result = rename_file("demo.ipynb", "demo_1")
    
    assert "Successfully renamed 'demo.ipynb' to 'demo_1.ipynb'" in result
    mock_path.rename.assert_called_once_with(Path("C:/test_dir/demo_1.ipynb"))
