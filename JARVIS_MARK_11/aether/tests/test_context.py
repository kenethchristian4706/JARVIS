"""
tests/test_context.py

Tests for ExecutionContext, reference resolution, and sequential multi-action
execution utilizing symbolic references.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.planner.models import Action, ExecutionPlan
from aether.planner.context import ExecutionContext, resolve_parameters
from aether.planner.plan_executor import execute_plan

def test_resolve_parameters_basic():
    ctx = ExecutionContext()
    ctx.store("file1", {"path": "C:\\notes.txt"})
    ctx.store("simple_var", "hello_world")
    
    # Resolve dict
    params = {"target": "$file1", "content": "test text", "val": "$simple_var"}
    resolved = resolve_parameters(params, ctx)
    assert resolved == {"target": "C:\\notes.txt", "content": "test text", "val": "hello_world"}

    # Resolve list
    list_params = ["$file1", "other_string", "$simple_var"]
    resolved_list = resolve_parameters(list_params, ctx)
    assert resolved_list == ["C:\\notes.txt", "other_string", "hello_world"]

    # Nested resolve
    nested = {
        "outer": {
            "inner": "$file1"
        },
        "items": ["$simple_var"]
    }
    resolved_nested = resolve_parameters(nested, ctx)
    assert resolved_nested == {
        "outer": {
            "inner": "C:\\notes.txt"
        },
        "items": ["hello_world"]
    }

def test_resolve_parameters_missing_variable():
    ctx = ExecutionContext()
    with pytest.raises(ValueError) as excinfo:
        resolve_parameters({"target": "$nonexistent"}, ctx)
    assert "Unknown reference" in str(excinfo.value)

@patch("builtins.input")
@patch("os.startfile")
@patch("pyautogui.screenshot")
@patch("urllib.request.urlretrieve")
def test_execution_plan_scenarios(mock_urlretrieve, mock_screenshot, mock_startfile, mock_input, tmp_path, monkeypatch):
    # Configure input mock to answer duplicate selection and location prompts automatically
    def mock_input_side_effect(prompt):
        prompt_lower = str(prompt).lower()
        if "selection" in prompt_lower:
            return "2"  # Create Another
        if "choice" in prompt_lower:
            return "4"  # Current Directory
        return ""
    mock_input.side_effect = mock_input_side_effect

    # Change current working directory to tmp_path to isolate file actions
    monkeypatch.chdir(tmp_path)
    
    # --- SCENARIO 1: Create notes.txt -> Write hello in it -> Open it ---
    plan1 = ExecutionPlan(
        actions=[
            Action(id="file1", tool="create_file", parameters={"filename": "notes_unique_123.txt"}),
            Action(tool="append_file", parameters={"filename": "$file1", "content": "hello"}),
            Action(tool="open_file", parameters={"filename": "$file1"})
        ]
    )
    
    success1, output1 = execute_plan(plan1)
    assert success1
    
    created_file = tmp_path / "notes_unique_123.txt"
    assert created_file.exists()
    assert created_file.read_text(encoding="utf-8").strip() == "hello"
    mock_startfile.assert_called_once_with(str(created_file.resolve()))
    
    mock_startfile.reset_mock()

    # --- SCENARIO 2: Create folder AI -> Create main.py inside it ---
    plan2 = ExecutionPlan(
        actions=[
            Action(id="folder1", tool="create_folder", parameters={"folder_name": "AI_unique_123"}),
            Action(tool="create_file", parameters={"filename": "main_unique_123.py", "location": "$folder1"})
        ]
    )
    
    success2, output2 = execute_plan(plan2)
    assert success2
    
    created_folder = tmp_path / "AI_unique_123"
    created_py = created_folder / "main_unique_123.py"
    assert created_folder.exists() and created_folder.is_dir()
    assert created_py.exists() and created_py.is_file()

    # --- SCENARIO 3: Take screenshot -> Open it ---
    # Setup mock for screenshot save operation
    def mock_save(path):
        Path(path).touch()
    mock_screenshot.return_value.save = mock_save
    
    plan3 = ExecutionPlan(
        actions=[
            Action(id="screenshot1", tool="take_screenshot", parameters={}),
            Action(tool="open_file", parameters={"filename": "$screenshot1"})
        ]
    )
    
    success3, output3 = execute_plan(plan3)
    assert success3
    mock_screenshot.assert_called_once()
    mock_startfile.assert_called_once()
    
    mock_startfile.reset_mock()

    # --- SCENARIO 4: Download a file -> Open it ---
    # Setup mock for urlretrieve download file creation
    def mock_retrieve(url, path):
        Path(path).touch()
    mock_urlretrieve.side_effect = mock_retrieve
    
    plan4 = ExecutionPlan(
        actions=[
            Action(id="downloaded1", tool="download_file", parameters={"url": "https://example.com/file_unique_123.zip", "destination": str(tmp_path)}),
            Action(tool="open_file", parameters={"filename": "$downloaded1"})
        ]
    )
    
    success4, output4 = execute_plan(plan4)
    assert success4
    mock_urlretrieve.assert_called_once()
    mock_startfile.assert_called_once()
    
    mock_startfile.reset_mock()

    # --- SCENARIO 5: Create folder Test -> Move notes.txt into it ---
    plan5 = ExecutionPlan(
        actions=[
            Action(id="folder2", tool="create_folder", parameters={"folder_name": "Test_unique_123"}),
            # notes_unique_123.txt was created in Scenario 1
            Action(tool="move_file", parameters={"source": "notes_unique_123.txt", "destination": "$folder2"})
        ]
    )
    
    success5, output5 = execute_plan(plan5)
    assert success5
    assert not (tmp_path / "notes_unique_123.txt").exists()
    assert (tmp_path / "Test_unique_123" / "notes_unique_123.txt").exists()

    # --- SCENARIO 6: Create folder AI -> Zip it ---
    plan6 = ExecutionPlan(
        actions=[
            Action(id="folder_zip", tool="create_folder", parameters={"folder_name": "AI_zip_dir"}),
            Action(tool="compress_files", parameters={"sources": ["$folder_zip"], "output": "AI_zip.zip"})
        ]
    )
    
    success6, output6 = execute_plan(plan6)
    assert success6
    assert (tmp_path / "AI_zip.zip").exists()
