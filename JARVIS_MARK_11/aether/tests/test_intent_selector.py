"""
tests/test_intent_selector.py

Unit tests for Aether's intent selection correction logic.
"""

import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.llm.intent_selector import select_intent

@patch("aether.llm.intent_selector.generate_completion")
def test_select_intent_notepad_corrections(mock_generate):
    # Mock LLM to return open_notepad_and_write intent
    mock_generate.return_value = '{"category": "system_control", "tool": "open_notepad_and_write"}'
    
    # Mock reading the prompt template to avoid filesystem dependency in unit test
    mock_prompt_content = "Query: {query}"
    with patch("builtins.open", mock_open(read_data=mock_prompt_content)):
        # 1. Simple commands should be corrected to open_app
        cat, tool = select_intent("open notepad")
        assert cat == "application_management"
        assert tool == "open_app"

        cat, tool = select_intent("launch notepad")
        assert cat == "application_management"
        assert tool == "open_app"

        cat, tool = select_intent("please start notepad")
        assert cat == "application_management"
        assert tool == "open_app"

        cat, tool = select_intent("run notepad.exe")
        assert cat == "application_management"
        assert tool == "open_app"

        # 2. Command with text to write should NOT be corrected
        cat, tool = select_intent("open notepad and write Hello")
        assert cat == "system_control"
        assert tool == "open_notepad_and_write"


def test_select_intent_open_app_vs_file_corrections():
    # 1. open_app misclassified as open_file should be corrected
    # Mock LLM to return open_file
    with patch("aether.llm.intent_selector.generate_completion", return_value='{"category": "file_operations", "tool": "open_file"}') as mock_gen:
        mock_prompt_content = "Query: {query}"
        with patch("builtins.open", mock_open(read_data=mock_prompt_content)):
            cat, tool = select_intent("open Chrome")
            assert cat == "application_management"
            assert tool == "open_app"

    # 2. open_file misclassified as open_app should be corrected
    # Mock LLM to return open_app
    with patch("aether.llm.intent_selector.generate_completion", return_value='{"category": "application_management", "tool": "open_app"}') as mock_gen:
        mock_prompt_content = "Query: {query}"
        with patch("builtins.open", mock_open(read_data=mock_prompt_content)):
            cat, tool = select_intent("open notes.txt")
            assert cat == "file_operations"
            assert tool == "open_file"

