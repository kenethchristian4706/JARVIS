"""
llm/parameter_extractor.py

Extracts tool parameters from user queries using the local LLM.
Bypasses LLM inference completely if the tool schema has no fields.
"""

import os
import json
import logging
from typing import Dict, Any
from aether.registry.tools import TOOLS
from aether.llm.model import generate_completion
from aether.llm.grammar import repair_and_parse_json

logger = logging.getLogger(__name__)

def extract_parameters(tool_name: str, query: str) -> Dict[str, Any]:
    """
    Extracts parameters from the query matching the tool's Pydantic schema.
    If the schema is empty, LLM inference is bypassed.
    """
    if tool_name not in TOOLS:
        raise ValueError(f"Tool '{tool_name}' is not registered.")
        
    tool_info = TOOLS[tool_name]
    schema_class = tool_info["schema_class"]
    
    # Check if the schema has fields (properties)
    # Pydantic V2 uses model_fields, V1 uses __fields__
    fields = getattr(schema_class, "model_fields", None) or getattr(schema_class, "__fields__", {})
    if not fields:
        logger.info(f"Bypassing LLM inference for parameter-free tool '{tool_name}'")
        return {}
        
    # Generate JSON schema dict
    # Pydantic V2 uses model_json_schema, V1 uses schema
    if hasattr(schema_class, "model_json_schema"):
        schema_dict = schema_class.model_json_schema()
    else:
        schema_dict = schema_class.schema()
    
    # Load prompt template
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "parameter_prompt.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    prompt = (
        prompt_tmpl.replace("{tool_name}", tool_name)
        .replace("{tool_description}", tool_info["description"])
        .replace("{json_schema}", json.dumps(schema_dict))
        .replace("{query}", query)
    )
    
    logger.info(f"Running LLM Parameter Extraction stage for tool '{tool_name}'...")
    raw_response = generate_completion(prompt, json_schema=schema_dict, max_tokens=128)
    
    try:
        # Parse the JSON response
        params = repair_and_parse_json(raw_response)
        return params
    except Exception as e:
        logger.error(f"Parameter Extraction failed: {e}. Raw response: {raw_response}")
        raise
