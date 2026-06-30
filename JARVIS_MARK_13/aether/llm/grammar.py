"""
llm/grammar.py

JSON response cleaning and repair helper utilities.
"""

import re
import json
import logging
import json_repair

logger = logging.getLogger(__name__)

def extract_first_json_object(text: str) -> str:
    """
    Finds and extracts the first valid JSON object {...} in the text by counting braces,
    automatically stripping any preceding/succeeding content or <think> blocks.
    """
    # 1. Strip closed <think> blocks completely
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    
    # 2. Handle unclosed <think> blocks
    if "<think>" in cleaned:
        # If there's a '{' after the "<think>" tag, start searching from that '{'
        think_idx = cleaned.find("<think>")
        json_start_after_think = cleaned.find("{", think_idx)
        if json_start_after_think != -1:
            cleaned = cleaned[json_start_after_think:]
        else:
            # If no '{' after "<think>", strip the partial <think> block
            cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL).strip()
            
    start_idx = cleaned.find("{")
    if start_idx == -1:
        return ""
        
    brace_count = 0
    in_quote = False
    escaped = False
    
    for i in range(start_idx, len(cleaned)):
        char = cleaned[i]
        if char == '\\' and not escaped:
            escaped = True
            continue
        if char == '"' and not escaped:
            in_quote = not in_quote
        elif not in_quote:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return cleaned[start_idx:i+1]
        escaped = False
        
    # If the braces did not close cleanly, return the candidate prefix
    # for json_repair to fix.
    return cleaned[start_idx:]

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
    1. Extract first JSON object block
    2. Try direct json.loads
    3. Fallback to json_repair on extracted block
    4. Fallback to json_repair on raw cleaned text
    
    Returns parsed dictionary or raises ValueError.
    """
    extracted = extract_first_json_object(text)
    if extracted:
        try:
            parsed = json.loads(extracted)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
            
        try:
            parsed = json_repair.loads(extracted)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    cleaned = clean_json_response(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
        
    try:
        parsed = json_repair.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
        
    raise ValueError(f"Failed to parse text as a valid JSON dictionary: '{text}'")
