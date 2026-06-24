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

    # Extract configuration variables with fallbacks
    context_size = getattr(config, "CONTEXT_SIZE", 2048)
    gpu_layers = getattr(config, "GPU_LAYERS", 0)
    threads = getattr(config, "THREADS", 4)
    batch_size = getattr(config, "BATCH_SIZE", 512)
    enable_flash_attention = getattr(config, "ENABLE_FLASH_ATTENTION", False)

    # Validate configuration values
    if not isinstance(context_size, int) or context_size <= 0:
        raise ValueError(f"Invalid CONTEXT_SIZE: {context_size}. Must be a positive integer.")
    if not isinstance(gpu_layers, int) or gpu_layers < 0:
        raise ValueError(f"Invalid GPU_LAYERS: {gpu_layers}. Must be a non-negative integer.")
    if not isinstance(threads, int) or threads <= 0:
        raise ValueError(f"Invalid THREADS: {threads}. Must be a positive integer.")
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"Invalid BATCH_SIZE: {batch_size}. Must be a positive integer.")

    fa_str = "Enabled" if enable_flash_attention else "Disabled"
    logger.info(
        f"Starting llama-server\n"
        f"Model: {model_path}\n"
        f"Context: {context_size}\n"
        f"Threads: {threads}\n"
        f"Batch Size: {batch_size}\n"
        f"GPU Layers: {gpu_layers}\n"
        f"Flash Attention: {fa_str}"
    )

    # Construct the start command with performance optimization:
    # -c: Context size (defines context window limit for prompt/completion context buffer)
    # -ngl: GPU layers (defines number of model layers to offload to GPU; 0 indicates pure CPU inference)
    # -t: Threads (defines count of CPU threads allocated for token generation)
    # -b: Batch size (defines batch prompt processing chunk size)
    cmd = [
        llama_path,
        "-m", model_path,
        "--host", config.HOST,
        "--port", str(config.PORT),
        "-c", str(context_size),
        "-ngl", str(gpu_layers),
        "-t", str(threads),
        "-b", str(batch_size),
    ]

    # -fa: Flash Attention (improves latency/throughput during attention matrix calculations)
    if enable_flash_attention:
        cmd.append("-fa")

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
    max_tokens: Optional[int] = None
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
    
    # Use configuration defaults for max_tokens, temperature, and top_p
    effective_max_tokens = max_tokens if max_tokens is not None else getattr(config, "MAX_TOKENS", 128)
    temperature = getattr(config, "TEMPERATURE", 0.0)
    top_p = getattr(config, "TOP_P", 1.0)

    # Ensure strict type safety for numeric values in payload
    try:
        effective_max_tokens = int(effective_max_tokens)
    except (ValueError, TypeError):
        effective_max_tokens = 128

    try:
        temperature = float(temperature)
    except (ValueError, TypeError):
        temperature = 0.0

    try:
        top_p = float(top_p)
    except (ValueError, TypeError):
        top_p = 1.0

    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
        "n_predict": effective_max_tokens,
        "stop": stop_sequences
    }
    
    if json_schema:
        payload["json_schema"] = json_schema

    # Filter out None/null values
    payload = {k: v for k, v in payload.items() if v is not None}

    logger.info(f"Sending completion request to endpoint: {url}")
    logger.info(f"Payload:\n{json.dumps(payload, indent=2)}")

    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("content", "").strip()
    except urllib.error.HTTPError as e:
        try:
            err_body_raw = e.read().decode('utf-8')
            try:
                err_json = json.loads(err_body_raw)
                err_body = json.dumps(err_json, indent=2)
            except Exception:
                err_body = err_body_raw
        except Exception:
            err_body = "Could not read error response body."
            
        detailed_error = (
            f"\n------------------------------------\n"
            f"HTTP {e.code}: {e.reason}\n"
            f"{err_body}\n"
            f"------------------------------------"
        )
        logger.error(f"HTTP completion request failed: {detailed_error}")
        raise RuntimeError(f"Failed to query LLM sidecar server: HTTP Error {e.code}: {e.reason}\n{detailed_error}")
    except Exception as e:
        logger.error(f"HTTP completion request failed: {e}")
        raise RuntimeError(f"Failed to query LLM sidecar server: {e}")
