"""
config.py

Global configuration constants for the Aether assistant.
Resolves paths for llama-server.exe, the GGUF model files, and output logs.
"""

import os
from pathlib import Path

# Base workspace directory
ATHER_DIR = Path("C:/Users/lenovo/dev/ather")

# Sidecar server path
LLAMA_SERVER_PATH = ATHER_DIR / "aether-main/runtime/windows-x64/llama-server.exe"

# Router (3B) and Planner (7B) model configurations
from aether.models.manager import load_models_config, resolve_model_path
models_cfg = load_models_config()

ROUTER_MODEL_NAME = models_cfg["router_model"]
PLANNER_MODEL_NAME = models_cfg["planner_model"]

# Resolve model paths dynamically with fallback checks
ROUTER_MODEL_PATH = resolve_model_path(ROUTER_MODEL_NAME)
PLANNER_MODEL_PATH = resolve_model_path(PLANNER_MODEL_NAME)

# Backward compatibility constants
MODEL_NAME = ROUTER_MODEL_NAME
MODEL_PATH = ROUTER_MODEL_PATH
PORT = 12345

# Llama server connection details
HOST = "127.0.0.1"
ROUTER_PORT = 12345
PLANNER_PORT = 12346

ROUTER_BASE_URL = f"http://{HOST}:{ROUTER_PORT}"
PLANNER_BASE_URL = f"http://{HOST}:{PLANNER_PORT}"

# Backward compatibility URL
BASE_URL = ROUTER_BASE_URL

# Timeout for completion requests in seconds
COMPLETION_TIMEOUT = 180.0

# Directory for logs
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "aether.log"

# Email summary configuration
MAX_SUMMARIZED_EMAILS = 10
SUMMARY_MAX_WORDS = 250

