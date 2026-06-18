"""
llm/model.py

Manages the background subprocess for llama-server.exe and handles HTTP POST requests
to get completions from the local Qwen2.5-3B model.
"""

import os
import sys
import json
import time
import logging
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

import aether.config as config

logger = logging.getLogger(__name__)

# Active background sidecar process
_server_process: Optional[subprocess.Popen] = None

def start_server(timeout_seconds: int = 45) -> bool:
    """
    Launches llama-server.exe in the background and waits for it to become ready.
    """
    global _server_process
    
    if _server_process is not None:
        if _server_process.poll() is None:
            return True
        else:
            _server_process = None

    llama_path = os.path.normpath(config.LLAMA_SERVER_PATH)
    model_path = os.path.normpath(config.MODEL_PATH)
    
    if not os.path.exists(llama_path):
        logger.error(f"llama-server.exe sidecar not found at: {llama_path}")
        return False
        
    if not os.path.exists(model_path):
        logger.error(f"GGUF model file not found at: {model_path}")
        return False

    logger.info(f"Starting llama-server.exe sidecar. Port: {config.PORT}")
    logger.info(f"Using model: {model_path}")

    # Build startup command
    # -ngl 0 disables GPU offloading for CPU compatibility
    cmd = [
        llama_path,
        "-m", model_path,
        "--host", config.HOST,
        "--port", str(config.PORT),
        "-c", "2048",
        "-ngl", "0"
    ]

    try:
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
        logger.error(f"Error starting llama-server process: {e}")
        return False

    # Poll server health endpoint until it is listening
    health_url = f"{config.BASE_URL}/health"
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if _server_process.poll() is not None:
            _, stderr_content = _server_process.communicate()
            logger.error(f"llama-server process exited prematurely (code {_server_process.returncode}).")
            logger.error(f"Stderr logs:\n{stderr_content}")
            _server_process = None
            return False
            
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                        logger.info(f"llama-server sidecar is ready at {config.BASE_URL}")
                        return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionResetError):
            time.sleep(1.0)
            
    logger.error("Timeout waiting for llama-server.exe sidecar to start.")
    stop_server()
    return False

def stop_server() -> None:
    """
    Stops the background llama-server.exe process.
    """
    global _server_process
    if _server_process is None:
        return
        
    logger.info("Stopping sidecar server...")
    try:
        _server_process.terminate()
        try:
            _server_process.wait(timeout=3.0)
            logger.info("Server stopped gracefully.")
        except subprocess.TimeoutExpired:
            logger.warning("Server did not stop. Force killing...")
            _server_process.kill()
            _server_process.wait()
            logger.info("Server killed.")
    except Exception as e:
        logger.error(f"Error stopping sidecar server: {e}")
    finally:
        _server_process = None

def generate_completion(
    prompt: str,
    json_schema: Optional[Dict[str, Any]] = None,
    stop_sequences: Optional[list[str]] = None,
    max_tokens: int = 128
) -> str:
    """
    Queries the sidecar server completion endpoint.
    Forces JSON output grammar if json_schema is provided.
    """
    if stop_sequences is None:
        stop_sequences = ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"]

    if not start_server():
        raise RuntimeError("LLM sidecar server is not running and failed to start.")

    url = f"{config.BASE_URL}/completion"
    
    payload = {
        "prompt": prompt,
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "n_predict": max_tokens,
        "stop": stop_sequences
    }
    
    if json_schema:
        payload["json_schema"] = json_schema

    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("content", "").strip()
    except Exception as e:
        logger.error(f"HTTP completion request failed: {e}")
        raise RuntimeError(f"Failed to query LLM sidecar server: {e}")
