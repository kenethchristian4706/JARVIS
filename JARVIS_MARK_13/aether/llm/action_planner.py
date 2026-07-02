"""
llm/action_planner.py

Action Planner stage. Synthesizes a list of tool calls to satisfy user query
using candidate tools and grammar-constrained JSON schemas.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Tuple, Optional
from aether.llm.model import generate_completion
from aether.llm.grammar import repair_and_parse_json, extract_first_json_object
from aether.registry.tools import TOOLS
import aether.config as config

logger = logging.getLogger(__name__)

class PlannedStepsList(list):
    def __init__(self, steps: list, diagnostics: dict):
        super().__init__(steps)
        self.diagnostics = diagnostics

TOOL_METADATA_SIMPLIFIED = {
    "open_app": {
        "Purpose": "Launch an installed desktop application.",
        "Arguments": "app_name",
        "Example_Query": "Open Chrome",
        "Example_Args": 'app_name="Chrome"'
    },
    "close_app": {
        "Purpose": "Close a running application.",
        "Arguments": "app_name",
        "Example_Query": "Close Notepad",
        "Example_Args": 'app_name="Notepad"'
    },
    "list_installed_apps": {
        "Purpose": "List all installed applications on the computer.",
        "Arguments": "none",
        "Example_Query": "show installed apps",
        "Example_Args": "{}"
    },
    "switch_to_app": {
        "Purpose": "Bring a running application window to the foreground.",
        "Arguments": "app_name",
        "Example_Query": "Switch to Chrome",
        "Example_Args": 'app_name="Chrome"'
    },
    "list_running_apps": {
        "Purpose": "List all currently running applications.",
        "Arguments": "none",
        "Example_Query": "what apps are running",
        "Example_Args": "{}"
    },
    "move_file": {
        "Purpose": "Move a file or folder from source to destination.",
        "Arguments": "source, destination",
        "Example_Query": "move doc.txt to Desktop",
        "Example_Args": 'source="doc.txt", destination="Desktop"'
    },
    "copy_file": {
        "Purpose": "Copy a file or folder to a destination.",
        "Arguments": "source, destination",
        "Example_Query": "copy report.pdf to Documents",
        "Example_Args": 'source="report.pdf", destination="Documents"'
    },
    "rename_file": {
        "Purpose": "Rename a file or folder.",
        "Arguments": "source, new_name",
        "Example_Query": "rename test.txt to test2.txt",
        "Example_Args": 'source="test.txt", new_name="test2.txt"'
    },
    "delete_file": {
        "Purpose": "Delete a file.",
        "Arguments": "path",
        "Example_Query": "delete report.pdf",
        "Example_Args": 'path="report.pdf"'
    },
    "search_files": {
        "Purpose": "Search for files matching a query.",
        "Arguments": "query",
        "Example_Query": "find report",
        "Example_Args": 'query="report"'
    },
    "open_file": {
        "Purpose": "Open a file in its default application.",
        "Arguments": "path",
        "Example_Query": "open document.docx",
        "Example_Args": 'path="document.docx"'
    },
    "create_file": {
        "Purpose": "Create a new empty file.",
        "Arguments": "path, location",
        "Example_Query": "create todo.txt on Desktop",
        "Example_Args": 'path="todo.txt", location="Desktop"'
    },
    "create_folder": {
        "Purpose": "Create a new folder.",
        "Arguments": "folder_name, location",
        "Example_Query": "create project folder",
        "Example_Args": 'folder_name="project", location=None'
    },
    "delete_folder": {
        "Purpose": "Delete a folder.",
        "Arguments": "folder_name",
        "Example_Query": "delete project folder",
        "Example_Args": 'folder_name="project"'
    },
    "list_directory": {
        "Purpose": "List contents of a directory.",
        "Arguments": "path",
        "Example_Query": "list Desktop files",
        "Example_Args": 'path="Desktop"'
    },
    "compress_files": {
        "Purpose": "Compress files/folders into a zip archive.",
        "Arguments": "sources, output",
        "Example_Query": "compress folder",
        "Example_Args": 'sources=["project"], output="project.zip"'
    },
    "extract_archive": {
        "Purpose": "Extract a zip archive.",
        "Arguments": "archive, destination",
        "Example_Query": "unzip archive.zip",
        "Example_Args": 'archive="archive.zip", destination=None'
    },
    "file_info": {
        "Purpose": "Get metadata properties of a file.",
        "Arguments": "path",
        "Example_Query": "info of notes.txt",
        "Example_Args": 'path="notes.txt"'
    },
    "append_file": {
        "Purpose": "Append text content to a file.",
        "Arguments": "path, content",
        "Example_Query": "append hello to log.txt",
        "Example_Args": 'path="log.txt", content="hello"'
    },
    "search_web": {
        "Purpose": "Search Google in the web browser.",
        "Arguments": "query",
        "Example_Query": "search weather",
        "Example_Args": 'query="weather"'
    },
    "search_youtube": {
        "Purpose": "Search YouTube for videos.",
        "Arguments": "query",
        "Example_Query": "search cooking on youtube",
        "Example_Args": 'query="cooking"'
    },
    "open_url": {
        "Purpose": "Open a URL in the browser.",
        "Arguments": "url",
        "Example_Query": "go to google.com",
        "Example_Args": 'url="https://google.com"'
    },
    "download_file": {
        "Purpose": "Download a file from a URL.",
        "Arguments": "url, destination",
        "Example_Query": "download file",
        "Example_Args": 'url="http://example.com/file", destination=None'
    },
    "open_new_tab": {
        "Purpose": "Open a new browser tab with a URL.",
        "Arguments": "url",
        "Example_Query": "open new tab",
        "Example_Args": 'url="https://github.com"'
    },
    "close_tab": {
        "Purpose": "Close the active browser tab.",
        "Arguments": "none",
        "Example_Query": "close current tab",
        "Example_Args": "{}"
    },
    "list_tabs": {
        "Purpose": "List all open browser tabs.",
        "Arguments": "none",
        "Example_Query": "list open tabs",
        "Example_Args": "{}"
    },
    "switch_tab": {
        "Purpose": "Switch to a browser tab.",
        "Arguments": "tab",
        "Example_Query": "switch to tab 2",
        "Example_Args": 'tab="2"'
    },
    "shutdown_pc": {
        "Purpose": "Shut down the PC.",
        "Arguments": "none",
        "Example_Query": "shutdown computer",
        "Example_Args": "{}"
    },
    "restart_pc": {
        "Purpose": "Restart the PC.",
        "Arguments": "none",
        "Example_Query": "reboot system",
        "Example_Args": "{}"
    },
    "sleep_pc": {
        "Purpose": "Put the PC to sleep.",
        "Arguments": "none",
        "Example_Query": "sleep computer",
        "Example_Args": "{}"
    },
    "lock_pc": {
        "Purpose": "Lock the PC.",
        "Arguments": "none",
        "Example_Query": "lock windows",
        "Example_Args": "{}"
    },
    "set_volume": {
        "Purpose": "Set system volume level.",
        "Arguments": "level",
        "Example_Query": "set volume to 50",
        "Example_Args": "level=50"
    },
    "mute_volume": {
        "Purpose": "Mute system volume.",
        "Arguments": "none",
        "Example_Query": "mute volume",
        "Example_Args": "{}"
    },
    "unmute_volume": {
        "Purpose": "Unmute system volume.",
        "Arguments": "none",
        "Example_Query": "unmute speaker",
        "Example_Args": "{}"
    },
    "set_brightness": {
        "Purpose": "Set screen brightness level.",
        "Arguments": "level",
        "Example_Query": "set brightness to 80",
        "Example_Args": "level=80"
    },
    "take_screenshot": {
        "Purpose": "Take a screenshot of the screen.",
        "Arguments": "path",
        "Example_Query": "take screenshot",
        "Example_Args": "path=None"
    },
    "extract_text_from_image": {
        "Purpose": "Extract text from an image using OCR.",
        "Arguments": "path",
        "Example_Query": "ocr image.png",
        "Example_Args": 'path="image.png"'
    },
    "open_notepad_and_write": {
        "Purpose": "Launch Notepad and write text into it.",
        "Arguments": "text",
        "Example_Query": "write hello in notepad",
        "Example_Args": 'text="hello"'
    },
    "read_file_content": {
        "Purpose": "Read text content of a file.",
        "Arguments": "path",
        "Example_Query": "read report.txt",
        "Example_Args": 'path="report.txt"'
    },
    "clear_clipboard": {
        "Purpose": "Clear system clipboard content.",
        "Arguments": "none",
        "Example_Query": "clear clipboard",
        "Example_Args": "{}"
    },
    "get_clipboard": {
        "Purpose": "Retrieve text content from system clipboard.",
        "Arguments": "none",
        "Example_Query": "get clipboard content",
        "Example_Args": "{}"
    },
    "set_clipboard": {
        "Purpose": "Copy text to system clipboard.",
        "Arguments": "clipboard_text",
        "Example_Query": "copy hello to clipboard",
        "Example_Args": 'clipboard_text="hello"'
    },
    "increase_volume": {
        "Purpose": "Increase system volume level.",
        "Arguments": "none",
        "Example_Query": "make volume louder",
        "Example_Args": "{}"
    },
    "decrease_volume": {
        "Purpose": "Decrease system volume level.",
        "Arguments": "none",
        "Example_Query": "lower volume",
        "Example_Args": "{}"
    },
    "increase_brightness": {
        "Purpose": "Increase screen brightness.",
        "Arguments": "none",
        "Example_Query": "make screen brighter",
        "Example_Args": "{}"
    },
    "decrease_brightness": {
        "Purpose": "Decrease screen brightness.",
        "Arguments": "none",
        "Example_Query": "dim screen",
        "Example_Args": "{}"
    },
    "send_email": {
        "Purpose": "Send an email with recipient, subject, and body.",
        "Arguments": "recipient, subject, body, confirmed",
        "Example_Query": "email john saying hello",
        "Example_Args": 'recipient="john@example.com", subject="Hello", body="hello", confirmed=False'
    },
    "list_emails": {
        "Purpose": "List or retrieve a list of recent email messages from the inbox.",
        "Arguments": "limit, unread_only",
        "Example_Query": "list my last 5 emails",
        "Example_Args": 'limit=5, unread_only=False'
    },
    "read_email": {
        "Purpose": "Read or retrieve full details of a specific email by its ID/UID, or by searching sender, date, or query.",
        "Arguments": "email_id (optional), sender (optional), date (optional)",
        "Example_Query": "read my latest email from John",
        "Example_Args": 'email_id="latest", sender="John"'
    },
    "create_word": {
        "Purpose": "Create a new Microsoft Word document (.docx).",
        "Arguments": "filename, directory, content, overwrite",
        "Example_Query": "Create report.docx containing Monthly report",
        "Example_Args": 'filename="report.docx", content="Monthly report", overwrite=False'
    },
    "read_word": {
        "Purpose": "Read plain text from a Word document.",
        "Arguments": "file_path",
        "Example_Query": "Read Meeting Notes.docx",
        "Example_Args": 'file_path="Meeting Notes.docx"'
    },
    "edit_word": {
        "Purpose": "Modify a Word document by appending or replacing text.",
        "Arguments": "file_path, operation, text, old_text, new_text",
        "Example_Query": "Replace 2024 with 2025 in report.docx",
        "Example_Args": 'file_path="report.docx", operation="replace", old_text="2024", new_text="2025"'
    },
    "create_excel": {
        "Purpose": "Create a new Excel workbook.",
        "Arguments": "filename, directory, sheet_name, overwrite",
        "Example_Query": "Create Sales workbook with Sheet1",
        "Example_Args": 'filename="Sales.xlsx", sheet_name="Sheet1", overwrite=False'
    },
    "read_excel": {
        "Purpose": "Read cells or entire worksheet values from an Excel workbook.",
        "Arguments": "file_path, sheet_name, cell_range",
        "Example_Query": "Read A1:C10 in sheet1 of Budget.xlsx",
        "Example_Args": 'file_path="Budget.xlsx", sheet_name="sheet1", cell_range="A1:C10"'
    },
    "write_excel": {
        "Purpose": "Write a value to a specific cell coordinate in an Excel workbook.",
        "Arguments": "file_path, sheet_name, cell, value",
        "Example_Query": "Write 500 into cell B4 of Budget.xlsx",
        "Example_Args": 'file_path="Budget.xlsx", sheet_name="Sheet1", cell="B4", value=500'
    }
}

TOOL_ARGUMENTS_MAP = {
    "open_app": ["app_name"],
    "create_word": ["filename", "directory", "content", "overwrite"],
    "read_word": ["file_path"],
    "edit_word": ["file_path", "operation", "text", "old_text", "new_text"],
    "create_excel": ["filename", "directory", "sheet_name", "overwrite"],
    "read_excel": ["file_path", "sheet_name", "cell_range"],
    "write_excel": ["file_path", "sheet_name", "cell", "value"],
    "close_app": ["app_name"],
    "list_installed_apps": [],
    "switch_to_app": ["app_name"],
    "list_running_apps": [],
    "move_file": ["source", "destination"],
    "copy_file": ["source", "destination"],
    "rename_file": ["source", "new_name"],
    "delete_file": ["path"],
    "search_files": ["query"],
    "open_file": ["path"],
    "create_file": ["path", "location"],
    "create_folder": ["folder_name", "location"],
    "delete_folder": ["folder_name"],
    "list_directory": ["path"],
    "compress_files": ["sources", "output"],
    "extract_archive": ["archive", "destination"],
    "file_info": ["path"],
    "append_file": ["path", "content"],
    "search_web": ["query"],
    "search_youtube": ["query"],
    "open_url": ["url"],
    "download_file": ["url", "destination"],
    "open_new_tab": ["url"],
    "close_tab": [],
    "list_tabs": [],
    "switch_tab": ["tab"],
    "shutdown_pc": [],
    "restart_pc": [],
    "sleep_pc": [],
    "lock_pc": [],
    "set_volume": ["level"],
    "mute_volume": [],
    "unmute_volume": [],
    "set_brightness": ["level"],
    "take_screenshot": ["path"],
    "extract_text_from_image": ["path"],
    "open_notepad_and_write": ["text"],
    "read_file_content": ["path"],
    "clear_clipboard": [],
    "get_clipboard": [],
    "set_clipboard": ["clipboard_text"],
    "increase_volume": [],
    "decrease_volume": [],
    "increase_brightness": [],
    "decrease_brightness": [],
    "send_email": ["recipient", "subject", "body", "confirmed"],
    "list_emails": ["limit", "unread_only"],
    "read_email": ["email_id", "sender", "date"]
}

def analyze_empty_plan(
    raw_response: str,
    extracted_json: str,
    parsed_plan: Optional[Dict[str, Any]],
    finish_reason: str,
    prompt: str
) -> str:
    """
    Analyzes and logs the specific reason why the planner returned an empty steps list.
    """
    if not raw_response.strip():
        return "Empty response from server (generation failed completely)"
        
    if "<think>" in raw_response and "</think>" not in raw_response:
        return "Generation stopped early inside <think> block (context truncation or max tokens limit)"
        
    if not extracted_json:
        return "Parser issue: No JSON object block found in the output string"
        
    if parsed_plan is None:
        return "Parser issue: Invalid JSON syntax (could not be repaired/parsed)"
        
    if isinstance(parsed_plan, dict) and "steps" in parsed_plan:
        steps = parsed_plan["steps"]
        if isinstance(steps, list) and len(steps) == 0:
            return "Planner decision: The planner explicitly decided that no candidate tool matches the user request"
            
    if finish_reason == "length":
        return "Generation stopped early due to max token limit (length)"
        
    return "Unknown reason (parsed steps list is empty)"

def safe_print(text: str):
    import sys
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        try:
            print(text.encode(encoding, errors='replace').decode(encoding))
        except Exception:
            print(text.encode('ascii', errors='replace').decode('ascii'))

def print_planner_diagnostics(
    prompt: str,
    raw_response: str,
    extracted_json: str,
    parsed_plan: Any,
    validation_result: str,
    fallback_triggered: str,
    failure_reason: str,
    req_metrics: Dict[str, Any],
    gen_time: float,
    finish_reason: str,
    port: int,
    original_query: str = "",
    normalized_query: str = ""
):
    """
    Outputs clean diagnostics for debug mode as requested in Step 8.
    """
    # Reconstruct the simulated chat messages
    system_part = prompt.split("<|im_start|>user")[0].replace("<|im_start|>system", "").replace("<|im_end|>", "").strip()
    user_part = prompt.split("<|im_start|>user")[-1].split("<|im_start|>assistant")[0].replace("<|im_end|>", "").strip() if "<|im_start|>user" in prompt else ""
    messages = [
        {"role": "system", "content": system_part},
        {"role": "user", "content": user_part if user_part else f"Original: {original_query}\nNormalized: {normalized_query}"}
    ]

    gen_params = {
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 350,
        "stop": ["<|im_end|>", "<|im_start|>", "\nUser:", "\nAssistant:"]
    }

    safe_print("\n============================================================")
    safe_print("=== PLANNER DEBUG DIAGNOSTICS ===")
    safe_print("============================================================")
    safe_print("Planner Prompt        :")
    safe_print(prompt.strip())
    safe_print("------------------------------------------------------------")
    safe_print("Planner Messages      :")
    safe_print(json.dumps(messages, indent=2))
    safe_print("------------------------------------------------------------")
    safe_print(f"Planner Tokens        : Prompt={req_metrics.get('tokens_evaluated', 0)}, Completion={req_metrics.get('tokens_predicted', 0)}")
    safe_print("------------------------------------------------------------")
    safe_print("Generation Parameters :")
    safe_print(json.dumps(gen_params, indent=2))
    safe_print("------------------------------------------------------------")
    safe_print(f"Generation Time       : {gen_time:.4f}s")
    safe_print(f"Finish Reason         : {finish_reason}")
    safe_print("------------------------------------------------------------")
    safe_print("Raw Response          :")
    safe_print(raw_response)
    safe_print("------------------------------------------------------------")
    safe_print("Extracted JSON        :")
    safe_print(extracted_json)
    safe_print("------------------------------------------------------------")
    safe_print("Parsed Plan           :")
    safe_print(json.dumps(parsed_plan, indent=2) if parsed_plan else "None")
    safe_print("------------------------------------------------------------")
    safe_print(f"Validation Result     : {validation_result}")
    safe_print(f"Fallback Triggered    : {fallback_triggered}")
    safe_print(f"Failure Reason        : {failure_reason}")
    safe_print("============================================================\n")


def analyze_empty_plan(
    raw_response: str,
    extracted_json: str,
    parsed_plan: Optional[Dict[str, Any]],
    finish_reason: str,
    prompt: str,
    candidate_tools: List[str]
) -> str:
    """
    Analyzes and logs the specific reason why the planner returned an empty steps list.
    """
    if not raw_response.strip():
        return "Empty response from server (generation failed completely)"
        
    if "<think>" in raw_response and "</think>" not in raw_response:
        return "context truncation (generation stopped early inside <think> block)"
        
    if not extracted_json:
        return "parser issue (No JSON object block found in the output string)"
        
    if parsed_plan is None:
        return "parser issue (Invalid JSON syntax, could not be repaired)"
        
    if finish_reason == "length":
        return "context truncation (generation stopped early due to max token limit)"
        
    if finish_reason not in ("stop", "stop_sequence"):
        return f"invalid finish reason ({finish_reason})"
        
    # Check if chat template tags are malformed or missing
    if "<|im_start|>" not in prompt or "<|im_end|>" not in prompt:
        return "wrong chat template"
        
    # Check if candidate tools list is empty or metadata is missing
    if not candidate_tools:
        return "missing metadata (no candidate tools provided to the planner)"
        
    # Check for empty plan decision
    if isinstance(parsed_plan, dict) and "steps" in parsed_plan:
        steps = parsed_plan["steps"]
        if isinstance(steps, list) and len(steps) == 0:
            return "planner believed no tool matched"
            
    return "prompt ambiguity (parsed steps list is empty)"


def is_arg_required(tool_name: str, arg_name: str) -> bool:
    if tool_name not in TOOLS:
        return False
    schema_class = TOOLS[tool_name].get("schema_class")
    if not schema_class:
        return False
        
    fields = getattr(schema_class, "model_fields", None) or getattr(schema_class, "__fields__", {})
    
    # 1. Check exact field name mapping first if it matches
    exact_field_name = arg_name
    if arg_name == "path" and "file_path" in fields:
        exact_field_name = "file_path"
    elif arg_name == "path" and "directory_path" in fields:
        exact_field_name = "directory_path"
    elif arg_name == "path" and "image_path" in fields:
        exact_field_name = "image_path"
    elif arg_name == "path" and "save_path" in fields:
        exact_field_name = "save_path"
    elif arg_name == "path" and "folder_name" in fields:
        exact_field_name = "folder_name"
    elif arg_name == "source" and "source_path" in fields:
        exact_field_name = "source_path"
    elif arg_name == "destination" and "destination_path" in fields:
        exact_field_name = "destination_path"
    elif arg_name == "destination" and "save_path" in fields:
        exact_field_name = "save_path"
    elif arg_name == "destination" and "new_name" in fields:
        exact_field_name = "new_name"
    elif arg_name == "archive" and "archive_path" in fields:
        exact_field_name = "archive_path"
    elif arg_name == "text" and "clipboard_text" in fields:
        exact_field_name = "clipboard_text"
    elif arg_name == "text" and "text" in fields:
        exact_field_name = "text"
    elif arg_name == "sources" and "source_paths" in fields:
        exact_field_name = "source_paths"
    elif arg_name == "output" and "output_path" in fields:
        exact_field_name = "output_path"
        
    if exact_field_name in fields:
        field = fields[exact_field_name]
        is_req_callable = getattr(field, "is_required", None)
        if callable(is_req_callable):
            return is_req_callable()
        required_attr = getattr(field, "required", None)
        if required_attr is not None:
            return required_attr
        return True
        
    # 2. Check fallback possible mappings list
    possible_fields = [arg_name]
    if arg_name == "path":
        possible_fields.extend(["file_path", "directory_path", "image_path", "save_path", "folder_name"])
    elif arg_name == "source":
        possible_fields.append("source_path")
    elif arg_name == "destination":
        possible_fields.extend(["destination_path", "save_path", "new_name"])
    elif arg_name == "archive":
        possible_fields.append("archive_path")
    elif arg_name == "text":
        possible_fields.extend(["clipboard_text", "text"])
    elif arg_name == "clipboard_text":
        possible_fields.append("text")
    elif arg_name == "sources":
        possible_fields.append("source_paths")
    elif arg_name == "output":
        possible_fields.append("output_path")
    elif arg_name == "location":
        possible_fields.extend(["location", "file_path", "directory_path"])
    elif arg_name == "filename":
        possible_fields.append("file_path")
        
    for field_name in possible_fields:
        if field_name in fields:
            field = fields[field_name]
            
            is_req_callable = getattr(field, "is_required", None)
            if callable(is_req_callable):
                if is_req_callable():
                    return True
                else:
                    continue
                    
            required_attr = getattr(field, "required", None)
            if required_attr is True:
                return True
                
    return False


def plan_actions(original_query: str, normalized_query: str, candidate_tools: List[str]) -> List[Dict[str, Any]]:
    """
    Plans actions sequentially to satisfy the query using only the candidate tools.
    Queries the Planner sidecar on the PLANNER_PORT (12346).
    """
    # 1. Format candidate tools with concise metadata
    tools_str = ""
    for tool_name in candidate_tools:
        if tool_name in TOOL_METADATA_SIMPLIFIED:
            meta = TOOL_METADATA_SIMPLIFIED[tool_name]
            tools_str += f"Tool\n{tool_name}\n"
            tools_str += f"Purpose\n{meta['Purpose']}\n"
            tools_str += f"Arguments\n{meta['Arguments']}\n"
            tools_str += f"Example\n{meta['Example_Query']}\n↓\n{meta['Example_Args']}\n\n"
            
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "planner_prompt.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    prompt = (
        prompt_tmpl.replace("{candidate_tools}", tools_str.strip())
        .replace("{original_query}", original_query)
        .replace("{normalized_query}", normalized_query)
    )
    
    # 2. Dynamic grammar constraint properties based on candidate tools using anyOf
    all_properties = {
        "app_name": {"type": "string"},
        "path": {"type": "string"},
        "location": {"type": "string"},
        "content": {"type": "string"},
        "source": {"type": "string"},
        "destination": {"type": "string"},
        "archive": {"type": "string"},
        "query": {"type": "string"},
        "url": {"type": "string"},
        "recipient": {"type": "string"},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "level": {"type": "integer"},
        "text": {"type": "string"},
        "clipboard_text": {"type": "string"},
        "sources": {
            "type": "array",
            "items": {"type": "string"}
        },
        "output": {"type": "string"},
        "tab": {"type": "string"},
        "folder_name": {"type": "string"},
        "new_name": {"type": "string"},
        "confirmed": {"type": "boolean"},
        "email_id": {"type": "string"},
        "sender": {"type": "string"},
        "date": {"type": "string"},
        "limit": {"type": "integer"},
        "unread_only": {"type": "boolean"}
    }
    
    any_of_items = []
    for tool_name in candidate_tools:
        if tool_name not in TOOL_ARGUMENTS_MAP:
            continue
        args_list = TOOL_ARGUMENTS_MAP[tool_name]
        arg_props = {arg: all_properties[arg] for arg in args_list if arg in all_properties}
        
        # Only mark strictly required parameters as required
        required_args = [arg for arg in args_list if is_arg_required(tool_name, arg)]
        
        any_of_items.append({
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "const": tool_name
                },
                "arguments": {
                    "type": "object",
                    "properties": arg_props,
                    "required": required_args,
                    "additionalProperties": False
                }
            },
            "required": ["tool", "arguments"],
            "additionalProperties": False
        })
        
    planner_schema = {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "anyOf": any_of_items
                } if any_of_items else {"type": "object"}
            }
        },
        "required": ["steps"],
        "additionalProperties": False
    }
    
    # 3. Request logic with retry-once for invalid JSON/timeout
    raw_response = ""
    res_metrics = {}
    finish_reason = "unknown"
    success = False
    attempts = 2
    port_to_use = config.PLANNER_PORT
    gen_time = 0.0
    
    for attempt in range(1, attempts + 1):
        t_start = time.perf_counter()
        try:
            logger.info(f"Running LLM Action Planner on port {port_to_use} (Attempt {attempt})...")
            raw_response, full_res = generate_completion(
                prompt,
                json_schema=planner_schema,
                max_tokens=350,
                port=port_to_use,
                return_full_response=True
            )
            gen_time = time.perf_counter() - t_start
            res_metrics = {
                "tokens_evaluated": full_res.get("tokens_evaluated", 0),
                "tokens_predicted": full_res.get("tokens_predicted", 0)
            }
            
            # Finish reason check
            if full_res.get("stopped_eos"):
                finish_reason = "stop"
            elif full_res.get("stopped_limit"):
                finish_reason = "length"
            elif full_res.get("stopped_word"):
                finish_reason = "stop_sequence"
            else:
                finish_reason = "unknown"
                
            t_ext_start = time.perf_counter()
            extracted_json = extract_first_json_object(raw_response)
            ext_time = time.perf_counter() - t_ext_start
            
            t_parse_start = time.perf_counter()
            parsed = None
            if extracted_json:
                try:
                    parsed = json.loads(extracted_json)
                except Exception:
                    try:
                        parsed = repair_and_parse_json(raw_response)
                    except Exception:
                        pass
            parse_time = time.perf_counter() - t_parse_start
            
            if parsed and isinstance(parsed, dict) and "steps" in parsed:
                success = True
                steps = parsed["steps"]
                
                # Cleanup optional "None" or "null" string arguments
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    args = step.get("arguments")
                    if not isinstance(args, dict):
                        continue
                    tool_name = step.get("tool")
                    for k, v in list(args.items()):
                        if isinstance(v, str) and v.strip().lower() in ("none", "null"):
                            if not is_arg_required(tool_name, k):
                                del args[k]

                # Print debug mode diagnostics
                print_planner_diagnostics(
                    prompt=prompt,
                    raw_response=raw_response,
                    extracted_json=extracted_json,
                    parsed_plan=parsed,
                    validation_result="Valid Plan Syntax" if steps else "Empty Plan Syntax",
                    fallback_triggered="No",
                    failure_reason="None" if steps else "Explicitly empty steps planned",
                    req_metrics=res_metrics,
                    gen_time=gen_time,
                    finish_reason=finish_reason,
                    port=port_to_use,
                    original_query=original_query,
                    normalized_query=normalized_query
                )
                
                if not steps:
                    empty_reason = analyze_empty_plan(raw_response, extracted_json, parsed, finish_reason, prompt, candidate_tools)
                    logger.warning(f"Planner decision analysis: {empty_reason}")
                
                diagnostics = {
                    "Planner Prompt Tokens": res_metrics.get("tokens_evaluated", 0),
                    "Planner Completion Tokens": res_metrics.get("tokens_predicted", 0),
                    "Generation Time": f"{gen_time:.4f}s",
                    "Parsing Time": f"{parse_time:.4f}s",
                    "Validation Time": "0.0000s",
                    "JSON Extraction Time": f"{ext_time:.4f}s",
                    "Fallback Triggered (Yes/No)": "No",
                    "Failure Reason": "None" if steps else f"Explicit empty steps planned: {analyze_empty_plan(raw_response, extracted_json, parsed, finish_reason, prompt, candidate_tools)}"
                }
                return PlannedStepsList(steps, diagnostics)
                
            # If parsed failed, raise to trigger retry/fallback
            raise ValueError("Parsed JSON format was invalid (missing 'steps' list)")
            
        except Exception as e:
            gen_time = time.perf_counter() - t_start
            err_msg = str(e)
            logger.warning(f"Action Planner failed on port {port_to_use} (Attempt {attempt}): {err_msg}")
            
            # Print debug diagnostics for the failure
            print_planner_diagnostics(
                prompt=prompt,
                raw_response=raw_response,
                extracted_json=extract_first_json_object(raw_response),
                parsed_plan=None,
                validation_result="Failed Syntax",
                fallback_triggered="Yes" if attempt == attempts else "No (retrying)",
                failure_reason=err_msg,
                req_metrics=res_metrics,
                gen_time=gen_time,
                finish_reason=finish_reason,
                port=port_to_use,
                original_query=original_query,
                normalized_query=normalized_query
            )
            
            if attempt == attempts:
                break
                
            # Sleep briefly before retry
            time.sleep(0.5)

    # 4. Fallback execution path
    if not success and config.PLANNER_PORT != config.ROUTER_PORT:
        port_to_use = config.ROUTER_PORT
        logger.info(f"Attempting fallback to ROUTER_PORT ({port_to_use}) using 3B model...")
        t_start = time.perf_counter()
        try:
            raw_response, full_res = generate_completion(
                prompt,
                json_schema=planner_schema,
                max_tokens=350,
                port=port_to_use,
                return_full_response=True
            )
            gen_time = time.perf_counter() - t_start
            res_metrics = {
                "tokens_evaluated": full_res.get("tokens_evaluated", 0),
                "tokens_predicted": full_res.get("tokens_predicted", 0)
            }
            if full_res.get("stopped_eos"):
                finish_reason = "stop"
            elif full_res.get("stopped_limit"):
                finish_reason = "length"
            else:
                finish_reason = "stop_sequence"
                
            t_ext_start = time.perf_counter()
            extracted_json = extract_first_json_object(raw_response)
            ext_time = time.perf_counter() - t_ext_start
            
            t_parse_start = time.perf_counter()
            parsed = repair_and_parse_json(raw_response)
            steps = parsed.get("steps", [])
            
            # Cleanup optional "None" or "null" string arguments
            for step in steps:
                if not isinstance(step, dict):
                    continue
                args = step.get("arguments")
                if not isinstance(args, dict):
                    continue
                tool_name = step.get("tool")
                for k, v in list(args.items()):
                    if isinstance(v, str) and v.strip().lower() in ("none", "null"):
                        if not is_arg_required(tool_name, k):
                            del args[k]
                            
            parse_time = time.perf_counter() - t_parse_start
            
            print_planner_diagnostics(
                prompt=prompt,
                raw_response=raw_response,
                extracted_json=extracted_json,
                parsed_plan=parsed,
                validation_result="Valid Plan Syntax" if steps else "Empty Plan Syntax",
                fallback_triggered="Yes (Succeeded)",
                failure_reason="None" if steps else "Explicitly empty steps planned",
                req_metrics=res_metrics,
                gen_time=gen_time,
                finish_reason=finish_reason,
                port=port_to_use,
                original_query=original_query,
                normalized_query=normalized_query
            )
            
            if steps:
                logger.info("Successfully resolved action plan using 3B model fallback!")
                diagnostics = {
                    "Planner Prompt Tokens": res_metrics.get("tokens_evaluated", 0),
                    "Planner Completion Tokens": res_metrics.get("tokens_predicted", 0),
                    "Generation Time": f"{gen_time:.4f}s",
                    "Parsing Time": f"{parse_time:.4f}s",
                    "Validation Time": "0.0000s",
                    "JSON Extraction Time": f"{ext_time:.4f}s",
                    "Fallback Triggered (Yes/No)": "Yes",
                    "Failure Reason": "None"
                }
                return PlannedStepsList(steps, diagnostics)
            else:
                empty_reason = analyze_empty_plan(raw_response, extracted_json, parsed, finish_reason, prompt, candidate_tools)
                logger.warning(f"Fallback Planner decision analysis: {empty_reason}")
                
        except Exception as e_fallback:
            gen_time = time.perf_counter() - t_start
            logger.error(f"Fallback Action Planner also failed: {e_fallback}")
            print_planner_diagnostics(
                prompt=prompt,
                raw_response="",
                extracted_json="",
                parsed_plan=None,
                validation_result="Failed Fallback Syntax",
                fallback_triggered="Yes (Failed)",
                failure_reason=str(e_fallback),
                req_metrics={},
                gen_time=gen_time,
                finish_reason="unknown",
                port=port_to_use,
                original_query=original_query,
                normalized_query=normalized_query
            )

    return PlannedStepsList([], {
        "Planner Prompt Tokens": 0,
        "Planner Completion Tokens": 0,
        "Generation Time": "0.0000s",
        "Parsing Time": "0.0000s",
        "Validation Time": "0.0000s",
        "JSON Extraction Time": "0.0000s",
        "Fallback Triggered (Yes/No)": "Yes",
        "Failure Reason": "Failed to resolve plan in all attempts"
    })
