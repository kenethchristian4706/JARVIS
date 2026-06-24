"""
tests/test_planner.py

Unit and integration tests for the refined planner architecture.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.assistant import is_multi_action, run_query
from aether.llm.intent_selector import select_intents
from aether.planner.tool_collector import collect_candidate_tools
from aether.llm.planner import generate_plan
from aether.planner.validator import validate_plan
from aether.planner.plan_executor import execute_plan

def test_is_multi_action():
    # Multi-actions
    assert is_multi_action("Open Chrome and VS Code")
    assert is_multi_action("Create folder AI-Agent and create main.py")
    assert is_multi_action("Search YouTube for LangGraph and set volume to 50%")
    assert is_multi_action("Open Chrome, create test.py and send email")
    
    # Single action
    assert not is_multi_action("Open Chrome")
    assert not is_multi_action("Create test.py")
    assert not is_multi_action("Increase volume to 50%")

@patch("aether.llm.model.generate_completion")
def test_select_intents(mock_gen):
    mock_gen.return_value = '{"intents": ["application_management", "file_system", "system_control"]}'
    intents = select_intents("Open Chrome, create test.py and set volume to 50%")
    assert "application_management" in intents
    assert "file_system" in intents
    assert "system_control" in intents

def test_tool_collector():
    candidates = collect_candidate_tools(["application_management", "file_system"])
    assert "open_app" in candidates
    assert "create_file" in candidates

@patch("aether.llm.model.generate_completion")
def test_planner_and_validator(mock_gen):
    # Test Case 1: Open Chrome and VS Code
    mock_gen.return_value = '{"actions": [{"tool": "open_app", "parameters": {"app_name": "chrome"}}, {"tool": "open_app", "parameters": {"app_name": "vscode"}}]}'
    plan = generate_plan("Open Chrome and VS Code", ["open_app"])
    assert len(plan.actions) == 2
    assert plan.actions[0].tool == "open_app"
    
    is_valid, err = validate_plan(plan, ["open_app"])
    assert is_valid
    assert err == ""

@patch("aether.executor.executor.execute_tool")
def test_plan_executor(mock_exec):
    mock_exec.return_value = (True, "Success")
    from aether.planner.models import ExecutionPlan, Action
    plan = ExecutionPlan(
        actions=[
            Action(tool="open_app", parameters={"app_name": "chrome"}),
            Action(tool="create_file", parameters={"filename": "unique_nonexistent_file_xyz_123.py", "location": "desktop"})
        ]
    )
    success, output = execute_plan(plan)
    assert success
    assert mock_exec.call_count == 2

@patch("aether.llm.model.generate_completion")
@patch("aether.executor.executor.execute_tool")
def test_run_query_e2e_multi_action(mock_execute, mock_generate):
    mock_generate.side_effect = [
        '{"intents": ["application_management", "file_system"]}',
        '{"actions": [{"tool": "open_app", "parameters": {"app_name": "chrome"}}, {"tool": "create_file", "parameters": {"filename": "unique_nonexistent_file_xyz_123.py", "location": "desktop"}}]}'
    ]
    mock_execute.return_value = (True, "Success")
    
    res = run_query("Open Chrome and create test.py")
    assert res["success"]
    assert "plan" in res["steps"]
    assert len(res["steps"]["plan"]["actions"]) == 2

@patch("aether.assistant.select_intent")
@patch("aether.assistant.extract_parameters")
@patch("aether.assistant.execute_tool")
def test_run_query_e2e_single_action(mock_execute, mock_extract, mock_select):
    mock_select.return_value = ("application_management", "open_app")
    mock_extract.return_value = {"app_name": "chrome"}
    mock_execute.return_value = (True, "Success")
    
    res = run_query("Open Chrome")
    assert res["success"]
    assert res["steps"]["category"] == "application_management"
    assert res["steps"]["tool"] == "open_app"
