"""
llm/intent_selector.py

Unified intent selector stage. Identifies both the operational category and the target tool
in a single LLM request using grammar constraints.
"""

import os
import logging
from typing import Tuple, Optional
from aether.registry.tools import TOOLS
from aether.llm.model import generate_completion
from aether.llm.grammar import repair_and_parse_json

logger = logging.getLogger(__name__)

# Allowed categories
CATEGORIES = [
    "application_management",
    "file_operations",
    "browser_operations",
    "system_control"
]

def select_intent(query: str) -> Tuple[str, str]:
    """
    Identifies the category and tool matching the query.
    
    Returns:
        (category: str, tool: str)
    """
    # 1. Load prompt template
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "intent_prompt.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    prompt = prompt_tmpl.replace("{query}", query)
    
    # 2. Build dynamic grammar-constraining schema for Category + Tool
    intent_schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": CATEGORIES
            },
            "tool": {
                "type": "string",
                "enum": list(TOOLS.keys())
            }
        },
        "required": ["category", "tool"]
    }
    
    logger.info("Running LLM Intent Selection stage...")
    
    # Set deterministic configuration, temperature=0, top_p=1
    raw_response = generate_completion(prompt, json_schema=intent_schema, max_tokens=25)
    
    try:
        parsed = repair_and_parse_json(raw_response)
        category = parsed.get("category")
        tool = parsed.get("tool")
        
        # Verify validation matches
        if tool not in TOOLS:
            raise ValueError(f"Invalid tool returned: '{tool}'")
            
        # Correction for LLM misclassification of simple notepad launcher commands
        if tool == "open_notepad_and_write":
            import re
            cleaned_query = query.strip().lower()
            if re.match(r"^(?:please\s+)?(?:open|launch|start|run)\s+notepad(?:\.exe)?$", cleaned_query):
                tool = "open_app"
                category = "application_management"

        # Correction for LLM confusing open_app vs open_file
        if tool == "open_app":
            cleaned_query = query.strip().lower()
            if any(ext in cleaned_query for ext in [".txt", ".pdf", ".docx", ".xlsx", ".csv", ".zip", ".png", ".jpg", ".log", ".py", ".json", ".ipynb", ".md"]):
                tool = "open_file"
                category = "file_operations"
        elif tool == "open_file":
            cleaned_query = query.strip().lower()
            common_apps = ["chrome", "vscode", "vs code", "notepad", "calculator", "paint", "excel", "word", "powerpoint", "teams", "microsoft teams", "edge", "spotify", "explorer"]
            if any(app in cleaned_query for app in common_apps) and not any(ext in cleaned_query for ext in [".txt", ".pdf", ".docx", ".xlsx", ".csv", ".zip", ".png", ".jpg", ".log", ".py", ".json", ".ipynb", ".md"]):
                tool = "open_app"
                category = "application_management"

        expected_category = TOOLS[tool]["category"]
        if category != expected_category:
            logger.warning(f"Category mismatch: LLM returned '{category}' for tool '{tool}', correcting to '{expected_category}'.")
            category = expected_category
            
        return category, tool
        
    except Exception as e:
        logger.error(f"Intent Selection failed: {e}. Raw response: {raw_response}")
        raise
