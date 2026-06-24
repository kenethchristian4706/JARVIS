"""
llm/grammar.py

JSON response cleaning and repair helper utilities.
"""

import re
import json
import logging
import json_repair

logger = logging.getLogger(__name__)

def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown formatting block markers and leading/trailing whitespace
    from the raw model response.
    """
    text = raw_text.strip()
    
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
        
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text.strip()

def repair_and_parse_json(text: str) -> dict:
    """
    Robust JSON parsing pipeline:
    1. Standard json.loads
    2. Fallback to json_repair
    3. Regex matching of first {...} block + json_repair
    
    Returns parsed dictionary or raises ValueError.
    """
    cleaned = clean_json_response(text)
    
    # 1. Direct JSON parse
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
        
    # 2. json-repair fallback
    try:
        parsed = json_repair.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
        
    # 3. Regex match first block candidate
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            try:
                parsed = json_repair.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
                
    raise ValueError(f"Failed to parse text as a valid JSON dictionary: '{text}'")
