"""
llm/planner.py

Builds the planner prompt, calls the LLM, and returns the parsed ExecutionPlan.
"""

import os
import logging
from typing import List
from aether.llm.grammar import repair_and_parse_json
from aether.planner.models import ExecutionPlan

logger = logging.getLogger(__name__)

def get_tool_definitions(candidate_tools: List[str]) -> str:
    """Formats candidate tool schemas and descriptions for the LLM prompt."""
    from aether.registry.tools import TOOLS
    
    defs = []
    for tool_name in candidate_tools:
        if tool_name not in TOOLS:
            continue
        info = TOOLS[tool_name]
        desc = info["description"]
        schema_cls = info["schema_class"]
        schema_json = schema_cls.schema()
        properties = schema_json.get("properties", {})
        required = schema_json.get("required", [])
        
        props_str = []
        for prop_name, prop_info in properties.items():
            req_label = "required" if prop_name in required else "optional"
            prop_type = prop_info.get("type", "string")
            prop_desc = prop_info.get("description", "")
            props_str.append(f"  - {prop_name} ({prop_type}, {req_label}): {prop_desc}")
            
        props_formatted = "\n".join(props_str) if props_str else "  None"
        defs.append(f"Tool: {tool_name}\nDescription: {desc}\nParameters:\n{props_formatted}")
    return "\n\n".join(defs)

def generate_plan(query: str, candidate_tools: List[str]) -> ExecutionPlan:
    """
    Generates a complete ExecutionPlan from the user query using the candidate tools.
    Enforces a strict JSON schema completion structure on the local LLM sidecar.
    """
    from aether.llm.model import generate_completion

    # 1. Load prompt template
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "planner_prompt.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    tool_defs = get_tool_definitions(candidate_tools)
    prompt = prompt_tmpl.replace("{candidate_tools}", tool_defs).replace("{query}", query)
    
    # Enforce simplified schema constraint to speed up llama.cpp grammar compilation
    schema_dict = {
        "type": "object",
        "properties": {
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "tool": {"type": "string"},
                        "parameters": {"type": "object"}
                    },
                    "required": ["tool"]
                }
            }
        },
        "required": ["actions"]
    }
    
    logger.info("Running Planner LLM...")
    raw_response = generate_completion(prompt, json_schema=schema_dict, max_tokens=512)
    
    try:
        parsed = repair_and_parse_json(raw_response)
        plan = ExecutionPlan(**parsed)
        logger.info(f"Generated ExecutionPlan: {plan}")
        return plan
    except Exception as e:
        logger.error(f"Planner LLM failed to parse plan: {e}. Raw response: {raw_response}")
        raise
