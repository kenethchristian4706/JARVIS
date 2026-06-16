"""
config.py

Global configuration constants for the Aether MVP desktop assistant.
Resolves local model paths, database paths, and llama-server.exe paths.
"""

import os
from pathlib import Path

# Base directory for Aether workspace
ATHER_DIR = Path("C:/Users/lenovo/dev/ather")

# Enable full access to all local drives on the PC
ALL_PC_ACCESS = True

# Path to the precompiled llama-server sidecar executable
LLAMA_SERVER_PATH = ATHER_DIR / "aether-main/runtime/windows-x64/llama-server.exe"

# Llama server connection details
HOST = "127.0.0.1"
PORT = 12345
BASE_URL = f"http://{HOST}:{PORT}"

# Local model filenames
MODEL_NAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
FALLBACK_MODEL_NAME = "qwen2.5-3b-instruct-q2_k.gguf"

# Search paths for the model GGUF file
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
    MODEL_PATH = preferred_model_path_1

# SQLite database file path (resolved dynamically relative to config file location)
DB_PATH = Path(__file__).parent / "database" / "aether.db"
