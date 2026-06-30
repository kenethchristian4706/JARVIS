"""
llm/category_selector.py

Lightweight category selector stage. Classifies user natural language query
into relevant tool categories using sidecar grammar constraints.
"""

import os
import json
import logging
from typing import Dict, Any
from aether.llm.model import generate_completion
from aether.llm.grammar import repair_and_parse_json
from aether.registry.micro_categories import MICRO_CATEGORIES
import aether.config as config

logger = logging.getLogger(__name__)

def select_categories(query: str) -> Dict[str, Any]:
    """
    Identifies intent, complexity, and categories matching the user's query.
    Queries the Router sidecar on the ROUTER_PORT (12345).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "category_prompt.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    prompt = prompt_tmpl.replace("{query}", query)
    
    # Define categories schema constraint
    router_schema = {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string"
            },
            "complexity": {
                "type": "string",
                "enum": ["single_step", "multi_step"]
            },
            "categories": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": MICRO_CATEGORIES + ["Email"]
                }
            },
            "filters": {
                "type": "object",
                "properties": {
                    "date_type": {
                        "type": "string",
                        "enum": ["today", "yesterday", "specific"]
                    },
                    "date": {
                        "type": "string"
                    }
                },
                "required": ["date_type"]
            }
        },
        "required": ["intent", "complexity", "categories"]
    }
    
    logger.info(f"Running LLM Router stage on port {config.ROUTER_PORT}...")
    raw_response = generate_completion(
        prompt,
        json_schema=router_schema,
        max_tokens=100,
        port=config.ROUTER_PORT
    )
    
    try:
        parsed = repair_and_parse_json(raw_response)
        return parsed
    except Exception as e:
        logger.error(f"Router stage failed: {e}. Raw response: {raw_response}")
        return {"intent": "unknown", "complexity": "single_step", "categories": []}
