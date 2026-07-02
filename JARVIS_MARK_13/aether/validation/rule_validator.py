"""
validation/rule_validator.py

Deterministic Python rule validator for Planner steps.
Checks tool existence, required arguments, type safety, missing parameters,
and duplicate steps. Bypasses LLM.
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from aether.registry.tools import TOOLS
from aether.validation.schema_validator import validate_parameters

logger = logging.getLogger(__name__)

def map_arguments_to_schema_fields(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically maps simplified/aliased argument names from the Planner output
    to the formal schema property names expected by the tool's Pydantic model.
    Only allows parameters defined in the schema class, pruning unknown parameters.
    """
    if tool_name not in TOOLS:
        return arguments

    schema_class = TOOLS[tool_name]["schema_class"]
    fields = getattr(schema_class, "model_fields", None) or getattr(schema_class, "__fields__", {})
    allowed_params = set(fields.keys())

    mapped = {}
    for k, v in arguments.items():
        if k in allowed_params:
            mapped[k] = v
        elif k == "path" and "file_path" in allowed_params:
            mapped["file_path"] = v
        elif k == "path" and "directory_path" in allowed_params:
            mapped["directory_path"] = v
        elif k == "path" and "image_path" in allowed_params:
            mapped["image_path"] = v
        elif k == "path" and "save_path" in allowed_params:
            mapped["save_path"] = v
        elif k == "path" and "folder_name" in allowed_params:
            mapped["folder_name"] = v
        elif k == "source" and "source_path" in allowed_params:
            mapped["source_path"] = v
        elif k == "destination" and "destination_path" in allowed_params:
            mapped["destination_path"] = v
        elif k == "destination" and "save_path" in allowed_params:
            mapped["save_path"] = v
        elif k == "destination" and "new_name" in allowed_params:
            mapped["new_name"] = v
        elif k == "archive" and "archive_path" in allowed_params:
            mapped["archive_path"] = v
        elif k == "text" and "clipboard_text" in allowed_params:
            mapped["clipboard_text"] = v
        elif k == "text" and "text" in allowed_params:
            mapped["text"] = v
        elif k == "clipboard_text" and "text" in allowed_params:
            mapped["text"] = v
        elif k == "sources" and "source_paths" in allowed_params:
            mapped["source_paths"] = v
        elif k == "output" and "output_path" in allowed_params:
            mapped["output_path"] = v
        elif k == "location" and "location" in allowed_params:
            mapped["location"] = v
        elif k == "location" and "file_path" in allowed_params:
            mapped["file_path"] = v
        elif k == "location" and "directory_path" in allowed_params:
            mapped["directory_path"] = v
        elif k == "filename" and "file_path" in allowed_params:
            mapped["file_path"] = v
            
    return mapped

def propagate_missing_path_parameters(steps: List[Dict[str, Any]]) -> None:
    """
    Sequentially propagates missing path-like parameters (path, source, destination, archive)
    and application parameters (app_name) from preceding steps in the plan to subsequent
    steps that require them. This corrects omissions from the LLM when executing multi-step plans.
    """
    path_fields = {
        "file_path": "path",
        "directory_path": "path",
        "image_path": "path",
        "save_path": "path",
        "source_path": "source",
        "destination_path": "destination",
        "archive_path": "archive",
        "app_name": "app_name"
    }

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        tool_name = step.get("tool")
        if not tool_name or tool_name not in TOOLS:
            continue
            
        arguments = step.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
            step["arguments"] = arguments

        schema_class = TOOLS[tool_name]["schema_class"]
        fields = getattr(schema_class, "model_fields", None) or getattr(schema_class, "__fields__", {})

        for field_name, simplified_name in path_fields.items():
            if field_name in fields:
                # If this parameter (or its mapped name) is not supplied
                if simplified_name not in arguments and field_name not in arguments:
                    # Search backwards for any path-like or app_name argument
                    found_val = None
                    for prev_idx in range(i - 1, -1, -1):
                        prev_step = steps[prev_idx]
                        if not isinstance(prev_step, dict):
                            continue
                        prev_args = prev_step.get("arguments", {})
                        if not isinstance(prev_args, dict):
                            continue
                        # Look for any path-like keys or app_name in the previous step
                        for k in ["path", "source", "destination", "archive", "file_path", "source_path", "destination_path", "archive_path", "app_name"]:
                            if k in prev_args and prev_args[k]:
                                found_val = prev_args[k]
                                break
                        if found_val:
                            break
                    if found_val:
                        arguments[simplified_name] = found_val
                        logger.info(f"Auto-propagated missing parameter '{simplified_name}' = '{found_val}' from a previous step to step {i} ({tool_name})")

def validate_plan_steps(steps: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validates a list of planned steps against schemas and python business rules.
    Checks: tool existence, required arguments, parameter types, duplicate steps, and missing parameters.
    
    Returns:
        (is_valid: bool, list_of_errors: List[str])
    """
    errors = []
    if not isinstance(steps, list):
        errors.append("Plan steps must be a list of step items.")
        return False, errors

    # Auto-repair specific tool mispredictions/omissions
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        tool_name = step.get("tool")
        arguments = step.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
            step["arguments"] = arguments
            
        if tool_name == "open_notepad_and_write":
            text = arguments.get("text")
            if text is None or (isinstance(text, str) and not text.strip()):
                step["tool"] = "open_app"
                step["arguments"] = {"app_name": "notepad"}
                logger.info(f"Auto-repaired step {idx}: downgraded open_notepad_and_write without text to open_app notepad.")
        elif tool_name == "create_word":
            if "filename" not in arguments and "file_path" not in arguments:
                content = arguments.get("content")
                if content:
                    content_str = str(content).strip()
                    if (content_str.lower().endswith((".docx", ".doc")) or 
                        " " not in content_str or 
                        len(content_str) < 15):
                        arguments["filename"] = content_str
                        if content_str.lower().endswith((".docx", ".doc")):
                            arguments.pop("content", None)
                    else:
                        arguments["filename"] = "document.docx"
                else:
                    arguments["filename"] = "document.docx"
                logger.info(f"Auto-repaired step {idx}: added missing filename parameter for create_word.")
        elif tool_name == "create_excel":
            if "filename" not in arguments and "file_path" not in arguments:
                sheet_name = arguments.get("sheet_name")
                if sheet_name and (str(sheet_name).lower().endswith(".xlsx") or " " not in str(sheet_name)):
                    arguments["filename"] = sheet_name
                else:
                    arguments["filename"] = "workbook.xlsx"
                logger.info(f"Auto-repaired step {idx}: added missing filename parameter for create_excel.")

    # Auto-repair and propagate missing parameters before validation
    propagate_missing_path_parameters(steps)

    seen_steps: List[Tuple[str, str]] = []

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"Step {idx} is not a valid JSON object.")
            continue

        tool_name = step.get("tool")
        arguments = step.get("arguments", {})

        if not tool_name:
            errors.append(f"Step {idx} is missing the 'tool' field.")
            continue

        # 1. Check tool existence & unsupported tools
        if tool_name not in TOOLS:
            errors.append(f"Step {idx}: Tool '{tool_name}' is not registered or unsupported.")
            continue

        # Map to expected schema parameter names
        mapped_args = map_arguments_to_schema_fields(tool_name, arguments)

        # 2. Check required arguments, types, and missing parameters
        success, _, err_msg = validate_parameters(tool_name, mapped_args)
        if not success:
            errors.append(f"Step {idx} ({tool_name}) parameter validation failed: {err_msg}")

        # 3. Check duplicate steps
        step_fingerprint = (tool_name, json.dumps(mapped_args, sort_keys=True))
        if step_fingerprint in seen_steps:
            errors.append(f"Step {idx} ({tool_name}) is a duplicate of a previous step in the plan.")
        else:
            seen_steps.append(step_fingerprint)

    return len(errors) == 0, errors
