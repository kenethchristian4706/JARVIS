"""
ai/parameter_extractor/extractor.py

Manages the llama-server.exe background process and uses it to extract structured
parameters from queries using Qwen2.5 with grammar-constrained decoding.
"""

import os
import re
import sys
import json
import time
import logging
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from pathlib import Path

import json_repair

import config
from ai.parameter_extractor.schemas import TOOL_REGISTRY
from ai.parameter_extractor.prompts import format_prompt

logger = logging.getLogger(__name__)

# Module-level sidecar process tracker
_server_process: Optional[subprocess.Popen] = None

def start_sidecar_server(timeout_seconds: int = 45) -> bool:
    """
    Launches llama-server.exe as a background subprocess and polls until it is ready.
    """
    global _server_process
    
    if _server_process is not None:
        if _server_process.poll() is None:
            return True
        else:
            _server_process = None
            
    llama_path = Path(config.LLAMA_SERVER_PATH)
    model_path = Path(config.MODEL_PATH)
    
    if not llama_path.exists():
        logger.error(f"llama-server.exe not found at path: {llama_path}")
        return False
        
    if not model_path.exists():
        logger.error(f"GGUF model file not found at path: {model_path}")
        return False
        
    logger.info(f"Starting background sidecar llama-server.exe using model: {model_path}")
    
    cmd = [
        str(llama_path),
        "-m", str(model_path),
        "--host", config.HOST,
        "--port", str(config.PORT),
        "-c", "2048",
        "-ngl", "0"
    ]
    
    try:
        # Create without window shell on Windows
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
    except Exception as e:
        logger.error(f"Failed to start llama-server process: {e}")
        return False
        
    # Poll endpoint
    health_url = f"{config.BASE_URL}/health"
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if _server_process.poll() is not None:
            logger.error(f"Server process terminated unexpectedly with exit code {_server_process.returncode}")
            _server_process = None
            return False
            
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                        logger.info("llama-server sidecar is ready and running.")
                        return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionResetError):
            time.sleep(1.0)
            
    logger.error("Timeout waiting for llama-server to report ready.")
    stop_sidecar_server()
    return False

def stop_sidecar_server() -> None:
    """
    Terminates the active llama-server sidecar process.
    """
    global _server_process
    if _server_process is None:
        return
        
    logger.info("Stopping sidecar llama-server...")
    try:
        _server_process.terminate()
        try:
            _server_process.wait(timeout=3.0)
            logger.info("llama-server stopped gracefully.")
        except subprocess.TimeoutExpired:
            logger.warning("Force killing llama-server...")
            _server_process.kill()
            _server_process.wait()
            logger.info("llama-server terminated.")
    except Exception as e:
        logger.error(f"Error terminating server process: {e}")
    finally:
        _server_process = None

def clean_json_response(raw_text: str) -> str:
    """
    Cleans markdown formatting and whitespace blocks from the JSON string.
    """
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text.strip()

def extract_parameters(tool_name: str, query: str) -> dict:
    """
    Extracts structured parameters from the user query matching the tool schema.
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "parameters": {},
            "raw_response": "",
            "error": f"Tool '{tool_name}' is not in the registry.",
            "was_repaired": False,
            "grammar_used": False
        }
        
    tool_info = TOOL_REGISTRY[tool_name]
    schema = tool_info["json_schema"]
    validator = tool_info["validator"]
    
    # Bypass logic for empty/no-parameter schemas
    if not schema:
        return {
            "success": True,
            "parameters": {},
            "raw_response": "",
            "error": None,
            "was_repaired": False,
            "grammar_used": False
        }
        
    # Start the sidecar server if it is not currently active
    if not start_sidecar_server():
        return {
            "success": False,
            "parameters": {},
            "raw_response": "",
            "error": "Failed to launch or connect to local llama-server.",
            "was_repaired": False,
            "grammar_used": False
        }
        
    # Format the structured prompt
    schema_str = json.dumps(schema)
    prompt = format_prompt(tool_name, tool_info["description"], schema_str, query)
    
    # Prepare API completion request payload
    url = f"{config.BASE_URL}/completion"
    payload = {
        "prompt": prompt,
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "n_predict": 128,
        "stop": ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"],
        "json_schema": schema
    }
    
    # Request completion
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            raw_text = res_data.get("content", "").strip()
    except Exception as e:
        return {
            "success": False,
            "parameters": {},
            "raw_response": "",
            "error": f"HTTP completion query failed: {e}",
            "was_repaired": False,
            "grammar_used": True
        }
        
    cleaned = clean_json_response(raw_text)
    parsed_json = None
    was_repaired = False
    
    # Stage A: Direct JSON load
    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError:
        # Stage B: json-repair fallback
        try:
            parsed = json_repair.loads(cleaned)
            if isinstance(parsed, dict):
                parsed_json = parsed
                was_repaired = True
        except Exception:
            pass
            
    # Stage C: Regex extract + parse fallback
    if parsed_json is None or not isinstance(parsed_json, dict):
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            inner_content = match.group(0)
            try:
                parsed_json = json.loads(inner_content)
                was_repaired = True
            except json.JSONDecodeError:
                try:
                    parsed = json_repair.loads(inner_content)
                    if isinstance(parsed, dict):
                        parsed_json = parsed
                        was_repaired = True
                except Exception:
                    pass
                    
    if parsed_json is None or not isinstance(parsed_json, dict):
        return {
            "success": False,
            "parameters": {},
            "raw_response": raw_text,
            "error": "Failed to parse model output into a valid JSON dictionary.",
            "was_repaired": was_repaired,
            "grammar_used": True
        }
        
    # Pydantic validator validation check
    try:
        validated = validator(**parsed_json)
        return {
            "success": True,
            "parameters": validated.model_dump(),
            "raw_response": raw_text,
            "error": None,
            "was_repaired": was_repaired,
            "grammar_used": True
        }
    except Exception as e:
        # Return what was partially parsed so caller can inspect
        return {
            "success": False,
            "parameters": parsed_json,
            "raw_response": raw_text,
            "error": f"Pydantic schema validation error: {e}",
            "was_repaired": was_repaired,
            "grammar_used": True
        }
