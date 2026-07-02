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

# Active background sidecar processes
_router_process: Optional[subprocess.Popen] = None
_planner_process: Optional[subprocess.Popen] = None

_llm_server_enabled: bool = True

_router_stdout_file = None
_router_stderr_file = None
_planner_stdout_file = None
_planner_stderr_file = None

def start_sidecar(role: str, model_path: str, port: int, timeout_seconds: int = 45) -> bool:
    """
    Launches llama-server.exe sidecar for a specific role if not already running.
    """
    global _router_process, _planner_process
    global _router_stdout_file, _router_stderr_file, _planner_stdout_file, _planner_stderr_file

    # Check if a sidecar is already running on this port and responding to health checks
    health_url = f"http://{config.HOST}:{port}/health"
    try:
        with urllib.request.urlopen(health_url, timeout=0.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                    logger.info(f"llama-server sidecar ({role}) is already running at {health_url}. Reusing it.")
                    return True
    except Exception:
        pass

    current_proc = _router_process if role == "router" else _planner_process
    if current_proc is not None:
        if current_proc.poll() is None:
            return True
        else:
            if role == "router":
                _router_process = None
            else:
                _planner_process = None

    llama_path = os.path.normpath(config.LLAMA_SERVER_PATH)
    m_path = os.path.normpath(model_path)
    
    if not os.path.exists(llama_path):
        logger.error(f"llama-server.exe sidecar not found at: {llama_path}")
        return False
        
    if not os.path.exists(m_path):
        logger.error(f"GGUF model file not found at: {m_path}")
        return False

    logger.info(f"Starting llama-server.exe sidecar for {role.upper()}. Port: {port}")
    logger.info(f"Using model: {m_path}")

    # Build startup command
    # -ngl 0 disables GPU offloading for CPU compatibility
    cmd = [
        llama_path,
        "-m", m_path,
        "--host", config.HOST,
        "--port", str(port),
        "-c", "2048",
        "-ngl", "0",
        "-np", "1"
    ]

    try:
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        stdout_path = config.LOGS_DIR / f"llama_{role}_stdout.log"
        stderr_path = config.LOGS_DIR / f"llama_{role}_stderr.log"
        
        # Open in write mode to clean logs on startup
        out_f = open(stdout_path, "w", encoding="utf-8")
        err_f = open(stderr_path, "w", encoding="utf-8")
        
        if role == "router":
            _router_stdout_file = out_f
            _router_stderr_file = err_f
            _router_process = subprocess.Popen(
                cmd,
                stdout=out_f,
                stderr=err_f,
                text=True,
                creationflags=creationflags
            )
            proc = _router_process
        else:
            _planner_stdout_file = out_f
            _planner_stderr_file = err_f
            _planner_process = subprocess.Popen(
                cmd,
                stdout=out_f,
                stderr=err_f,
                text=True,
                creationflags=creationflags
            )
            proc = _planner_process
            
    except Exception as e:
        logger.error(f"Error starting llama-server process for {role}: {e}")
        return False

    # Poll server health endpoint until it is listening
    health_url = f"http://{config.HOST}:{port}/health"
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if proc.poll() is not None:
            logger.error(f"llama-server process for {role} exited prematurely (code {proc.returncode}).")
            # Log the captured stderr contents for troubleshooting
            try:
                stderr_path = config.LOGS_DIR / f"llama_{role}_stderr.log"
                if stderr_path.exists():
                    stderr_content = stderr_path.read_text(encoding="utf-8")
                    logger.error(f"Stderr logs:\n{stderr_content}")
            except Exception:
                pass
            
            # Clean up handles
            if role == "router":
                _router_process = None
                try: _router_stdout_file.close()
                except Exception: pass
                _router_stdout_file = None
                try: _router_stderr_file.close()
                except Exception: pass
                _router_stderr_file = None
            else:
                _planner_process = None
                try: _planner_stdout_file.close()
                except Exception: pass
                _planner_stdout_file = None
                try: _planner_stderr_file.close()
                except Exception: pass
                _planner_stderr_file = None
            return False
            
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                        logger.info(f"llama-server sidecar ({role}) is ready at http://{config.HOST}:{port}")
                        return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionResetError):
            time.sleep(1.0)
            
    logger.error(f"Timeout waiting for llama-server.exe sidecar ({role}) to start.")
    stop_sidecar(role)
    return False

def stop_sidecar(role: str) -> None:
    """
    Stops a specific background llama-server.exe process and closes log handles.
    Also kills any orphaned sidecar process running on the target port.
    """
    global _router_process, _planner_process
    global _router_stdout_file, _router_stderr_file, _planner_stdout_file, _planner_stderr_file
    
    proc = _router_process if role == "router" else _planner_process
    port = config.ROUTER_PORT if role == "router" else config.PLANNER_PORT

    if proc is not None:
        logger.info(f"Stopping sidecar server ({role})...")
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3.0)
                logger.info(f"Server ({role}) stopped gracefully.")
            except subprocess.TimeoutExpired:
                logger.warning(f"Server ({role}) did not stop. Force killing...")
                proc.kill()
                proc.wait()
                logger.info(f"Server ({role}) killed.")
        except Exception as e:
            logger.error(f"Error stopping sidecar server ({role}): {e}")
        finally:
            if role == "router":
                _router_process = None
                if _router_stdout_file:
                    try: _router_stdout_file.close()
                    except Exception: pass
                    _router_stdout_file = None
                if _router_stderr_file:
                    try: _router_stderr_file.close()
                    except Exception: pass
                    _router_stderr_file = None
            else:
                _planner_process = None
                if _planner_stdout_file:
                    try: _planner_stdout_file.close()
                    except Exception: pass
                    _planner_stdout_file = None
                if _planner_stderr_file:
                    try: _planner_stderr_file.close()
                    except Exception: pass
                    _planner_stderr_file = None

    # Kill any orphaned process still listening on that port
    try:
        import psutil
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                pid = conn.pid
                if pid:
                    try:
                        p = psutil.Process(pid)
                        if p.name().lower().startswith("llama-server"):
                            logger.info(f"Found orphaned sidecar {p.name()} (PID: {pid}) listening on port {port}. Terminating it.")
                            p.terminate()
                            try:
                                p.wait(timeout=3.0)
                            except psutil.TimeoutExpired:
                                p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
    except Exception as e:
        logger.error(f"Error checking/killing orphaned process on port {port}: {e}")


def start_server(timeout_seconds: int = 45) -> bool:
    """
    Launches both router (3B) and planner (7B) servers in the background and waits for them.
    """
    global _llm_server_enabled
    _llm_server_enabled = True
    success_router = start_sidecar("router", config.ROUTER_MODEL_PATH, config.ROUTER_PORT, timeout_seconds)
    success_planner = start_sidecar("planner", config.PLANNER_MODEL_PATH, config.PLANNER_PORT, timeout_seconds)
    return success_router and success_planner

def stop_server() -> None:
    """
    Stops both background sidecar processes.
    """
    global _llm_server_enabled
    _llm_server_enabled = False
    stop_sidecar("router")
    stop_sidecar("planner")

def is_sidecar_running(role: str) -> bool:
    """
    Checks if a sidecar is running, either by verifying our active process handle
    or by querying the health check URL to see if it's already active.
    """
    proc = _router_process if role == "router" else _planner_process
    if proc is not None and proc.poll() is None:
        return True

    port = config.ROUTER_PORT if role == "router" else config.PLANNER_PORT
    health_url = f"http://{config.HOST}:{port}/health"
    try:
        with urllib.request.urlopen(health_url, timeout=0.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                    return True
    except Exception:
        pass
    return False


def generate_completion(
    prompt: str,
    json_schema: Optional[Dict[str, Any]] = None,
    stop_sequences: Optional[list[str]] = None,
    max_tokens: int = 128,
    port: int = config.ROUTER_PORT,
    return_full_response: bool = False,
    temperature: float = 0.0,
    top_p: float = 1.0
) -> Any:
    """
    Queries the targeted sidecar server completion endpoint.
    Forces JSON output grammar if json_schema is provided.
    Enables special token parsing via "special": True.
    """
    if stop_sequences is None:
        # For planner or structured schemas, do not stop on double newlines
        if json_schema or port == config.PLANNER_PORT:
            stop_sequences = ["<|im_end|>", "<|im_start|>", "\nUser:", "\nAssistant:"]
        else:
            stop_sequences = ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"]

    role = "router" if port == config.ROUTER_PORT else "planner"
    model_path = config.ROUTER_MODEL_PATH if role == "router" else config.PLANNER_MODEL_PATH
    
    if not _llm_server_enabled:
        raise RuntimeError("Local LLM is stopped. Please start the Local LLM in the sidebar to process queries.")
        
    if not start_sidecar(role, model_path, port):
        raise RuntimeError(f"LLM sidecar server ({role}) is not running and failed to start.")

    url = f"http://{config.HOST}:{port}/completion"
    
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
        "n_predict": max_tokens,
        "stop": stop_sequences,
        "special": True
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
        timeout_val = getattr(config, "COMPLETION_TIMEOUT", 60.0)
        with urllib.request.urlopen(req, timeout=timeout_val) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            content = res_data.get("content", "").strip()
            if return_full_response:
                return content, res_data
            return content
    except Exception as e:
        logger.error(f"HTTP completion request failed on port {port}: {e}")
        raise RuntimeError(f"Failed to query LLM sidecar server on port {port}: {e}")

def reload_sidecar(role: str, new_model_name: str) -> bool:
    """
    Terminates the existing sidecar of the given role, updates config paths,
    and starts the new sidecar GGUF.
    """
    # 1. Stop active sidecar for the role
    stop_sidecar(role)
    
    # 2. Update config values
    import aether.config as config
    from pathlib import Path
    
    # Resolve path dynamically with fallback checks
    from aether.models.manager import resolve_model_path
    new_model_path = resolve_model_path(new_model_name)
    
    if role == "router":
        config.ROUTER_MODEL_NAME = new_model_name
        config.ROUTER_MODEL_PATH = new_model_path
        # backward compatibility
        config.MODEL_NAME = new_model_name
        config.MODEL_PATH = new_model_path
        
        # 3. Start sidecar again
        return start_sidecar("router", config.ROUTER_MODEL_PATH, config.ROUTER_PORT)
    else:
        config.PLANNER_MODEL_NAME = new_model_name
        config.PLANNER_MODEL_PATH = new_model_path
        
        # 3. Start sidecar again
        return start_sidecar("planner", config.PLANNER_MODEL_PATH, config.PLANNER_PORT)
