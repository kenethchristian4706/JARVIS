"""
config.py

Global configuration constants for the Aether MVP desktop assistant.
Resolves local model paths and llama-server.exe paths.
"""

import os

# Base directory for Aether
ATHER_DIR = "C:/Users/lenovo/dev/ather"

# Path to the precompiled llama-server sidecar executable
LLAMA_SERVER_PATH = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/runtime/windows-x64/llama-server.exe")
)

# Llama server connection details
HOST = "127.0.0.1"
PORT = 12345
BASE_URL = f"http://{HOST}:{PORT}"

# Preferred local model files
MODEL_NAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
FALLBACK_MODEL_NAME = "qwen2.5-3b-instruct-q2_k.gguf"

preferred_model_path_1 = os.path.normpath("C:/Users/lenovo/Downloads/qwen2.5-3b-instruct-q4_k_m.gguf")
preferred_model_path_2 = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/models", MODEL_NAME)
)
fallback_model_path = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/models", FALLBACK_MODEL_NAME)
)

# Resolve active model path
if os.path.exists(preferred_model_path_1):
    MODEL_PATH = preferred_model_path_1
elif os.path.exists(preferred_model_path_2):
    MODEL_PATH = preferred_model_path_2
elif os.path.exists(fallback_model_path):
    MODEL_PATH = fallback_model_path
else:
    MODEL_PATH = preferred_model_path_1

# SQLite database file path
DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "database/aether.db")
)
