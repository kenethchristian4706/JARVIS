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

# Llama server connection details
HOST = "127.0.0.1"
PORT = 12345
BASE_URL = f"http://{HOST}:{PORT}"

# Preferred model name (Q4_K_M)
MODEL_NAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
# Fallback model name (Q2_K)
FALLBACK_MODEL_NAME = "qwen2.5-3b-instruct-q2_k.gguf"

# Model paths
preferred_model_path_1 = Path("C:/Users/lenovo/Downloads") / MODEL_NAME
preferred_model_path_2 = ATHER_DIR / "aether-main/models" / MODEL_NAME
fallback_model_path = ATHER_DIR / "aether-main/models" / FALLBACK_MODEL_NAME

# Resolve active model path
if preferred_model_path_1.exists():
    MODEL_PATH = preferred_model_path_1
elif preferred_model_path_2.exists():
    MODEL_PATH = preferred_model_path_2
elif fallback_model_path.exists():
    MODEL_PATH = fallback_model_path
else:
    MODEL_PATH = preferred_model_path_1  # Default fallback if none exists

# Directory for logs
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "aether.log"

# Inference Optimization Configuration
CONTEXT_SIZE = 2048
GPU_LAYERS = 0
THREADS = os.cpu_count() or 4
BATCH_SIZE = 512
TEMPERATURE = 0.0
TOP_P = 0.9
MAX_TOKENS = 256
ENABLE_FLASH_ATTENTION = False
