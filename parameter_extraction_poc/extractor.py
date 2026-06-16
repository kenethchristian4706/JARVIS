"""
extractor.py

Implements parameter extraction by managing a llama-server.exe sidecar process,
submitting structured prompts, cleaning raw text responses, and validating outputs
against tool-specific Pydantic schemas.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple

import config
from prompts import EXTRACTION_PROMPT
from schemas import TOOL_REGISTRY

# Keep track of the sidecar process
_server_process: Optional[subprocess.Popen] = None

def start_sidecar_server(timeout_seconds: int = 45) -> bool:
    """
    Launches llama-server.exe in the background and waits for it to become ready.
    """
    global _server_process
    
    if _server_process is not None:
        # Check if the process is still running
        if _server_process.poll() is None:
            print("[Sidecar] llama-server is already running.")
            return True
        else:
            _server_process = None

    print(f"[Sidecar] Launching sidecar server: {config.LLAMA_SERVER_PATH}")
    print(f"[Sidecar] Using model: {config.MODEL_PATH}")
    print(f"[Sidecar] Port: {config.PORT}")

    # Build startup command
    # -ngl 0 disables GPU offloading for maximum CPU compatibility.
    # -c 2048 sets the context window size.
    cmd = [
        config.LLAMA_SERVER_PATH,
        "-m", config.MODEL_PATH,
        "--host", config.HOST,
        "--port", str(config.PORT),
        "-c", "2048",
        "-ngl", "0"
    ]

    try:
        # Redirect outputs to stdout/stderr or null to prevent clogging the console
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Creation flags to run cleanly in background on Windows
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception as e:
        print(f"[Sidecar] Error launching server process: {e}", file=sys.stderr)
        return False

    # Poll server health endpoint until it is listening
    health_url = f"{config.BASE_URL}/health"
    start_time = time.time()
    
    print("[Sidecar] Waiting for server to initialize model and bind to port...")
    while time.time() - start_time < timeout_seconds:
        # Quick check if process has died early
        if _server_process.poll() is not None:
            _, stderr_content = _server_process.communicate()
            print(f"[Sidecar] Server process exited prematurely with code {_server_process.returncode}.", file=sys.stderr)
            print(f"[Sidecar] Error logs:\n{stderr_content}", file=sys.stderr)
            _server_process = None
            return False
            
        try:
            # Attempt to read the health endpoint
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                        print(f"[Sidecar] Server ready! Bound to {config.BASE_URL}")
                        return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionResetError):
            # Server not listening yet, wait and retry
            time.sleep(1.0)
            
    # Timeout reached
    print("[Sidecar] Timeout waiting for llama-server to start.", file=sys.stderr)
    stop_sidecar_server()
    return False

def stop_sidecar_server():
    """
    Stops the background llama-server.exe process.
    """
    global _server_process
    if _server_process is None:
        return
        
    print("[Sidecar] Stopping sidecar server...")
    try:
        # Graceful shutdown first (terminate)
        _server_process.terminate()
        # Wait up to 3 seconds for cleanup
        try:
            _server_process.wait(timeout=3.0)
            print("[Sidecar] Server stopped gracefully.")
        except subprocess.TimeoutExpired:
            # Force kill if still running
            print("[Sidecar] Server did not stop. Killing process...")
            _server_process.kill()
            _server_process.wait()
            print("[Sidecar] Server killed.")
    except Exception as e:
        print(f"[Sidecar] Error while stopping server: {e}", file=sys.stderr)
    finally:
        _server_process = None

def clean_json_response(raw_text: str) -> str:
    """
    Cleans the model output by removing markdown code block markers and leading/trailing whitespace.
    """
    text = raw_text.strip()
    
    # Strip markdown formatting if the model wrapped JSON in backticks
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
        
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text

import re
import json_repair

def extract_parameters(tool_name: str, query: str) -> Dict[str, Any]:
    """
    Uses the local LLM sidecar to extract tool parameters, validates them,
    and returns a structured dict of the results.
    
    If the schema is empty, LLM inference is bypassed completely.
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "parameters": {},
            "raw_response": "",
            "error": f"Tool '{tool_name}' is not registered in the schema catalog.",
            "was_repaired": False,
            "grammar_used": False
        }

    tool_info = TOOL_REGISTRY[tool_name]
    description = tool_info["description"]
    schema_dict = tool_info["json_schema"]
    validator = tool_info["validator"]

    # 1. Skip extraction for empty schemas
    if not schema_dict:
        return {
            "success": True,
            "parameters": {},
            "raw_response": "",
            "error": None,
            "was_repaired": False,
            "grammar_used": False
        }

    # Convert schema to JSON string for the prompt
    json_schema_str = json.dumps(schema_dict)

    # 2. Format the extraction prompt
    prompt = EXTRACTION_PROMPT.format(
        tool_name=tool_name,
        tool_description=description,
        json_schema=json_schema_str,
        query=query
    )

    # 3. Make completion call to llama-server API
    url = f"{config.BASE_URL}/completion"
    
    # Configure deterministic inference, grammar constraints, and stop sequences
    payload = {
        "prompt": prompt,
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "n_predict": 64,  # Max tokens
        "stop": ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"],
        "json_schema": schema_dict  # Force response to follow schema using grammar
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    raw_response_text = ""
    try:
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            raw_response_text = res_data.get("content", "").strip()
    except Exception as e:
        return {
            "success": False,
            "parameters": {},
            "raw_response": "",
            "error": f"API request failed: {e}",
            "was_repaired": False,
            "grammar_used": True
        }

    # 4. Clean and parse JSON using robust parsing pipeline
    cleaned_text = clean_json_response(raw_response_text)
    parsed_json = None
    was_repaired = False
    parsing_error = None

    # Step A: Direct JSON parse
    try:
        parsed_json = json.loads(cleaned_text)
    except json.JSONDecodeError as e_a:
        parsing_error = e_a
        
        # Step B: Fallback JSON repair
        try:
            parsed_json = json_repair.loads(cleaned_text)
            if isinstance(parsed_json, dict):
                was_repaired = True
                parsing_error = None
        except Exception as e_b:
            parsing_error = e_b

    # Step C: Final Fallback regex extraction of first JSON object
    if parsed_json is None or not isinstance(parsed_json, dict):
        match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
        if match:
            json_candidate = match.group(0)
            # Try parsing direct regex block
            try:
                parsed_json = json.loads(json_candidate)
                was_repaired = True
                parsing_error = None
            except json.JSONDecodeError:
                # Try repairing regex block
                try:
                    parsed_json = json_repair.loads(json_candidate)
                    if isinstance(parsed_json, dict):
                        was_repaired = True
                        parsing_error = None
                except Exception as e_c:
                    parsing_error = e_c

    # If parsing failed entirely
    if parsed_json is None or not isinstance(parsed_json, dict):
        return {
            "success": False,
            "parameters": {},
            "raw_response": raw_response_text,
            "error": f"JSON syntax error: {parsing_error}",
            "was_repaired": was_repaired,
            "grammar_used": True
        }

    # 5. Validate parsed arguments with Pydantic
    try:
        # Create Pydantic instance and convert back to dictionary
        validated_model = validator(**parsed_json)
        validated_params = validated_model.model_dump()
        return {
            "success": True,
            "parameters": validated_params,
            "raw_response": raw_response_text,
            "error": None,
            "was_repaired": was_repaired,
            "grammar_used": True
        }
    except Exception as e:
        return {
            "success": False,
            "parameters": parsed_json,  # Return parsed JSON to help diagnose
            "raw_response": raw_response_text,
            "error": f"Schema validation error: {e}",
            "was_repaired": was_repaired,
            "grammar_used": True
        }
