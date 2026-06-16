"""
config.py

Configuration file for the parameter extraction PoC.
References the precompiled llama-server.exe and Qwen 2.5 GGUF model files.
Now supports automatic fallback to Q2_K quantization if Q4_K_M is not found.
"""

import os

# Base directories
ATHER_DIR = "C:/Users/lenovo/dev/ather"

# Path to the precompiled llama-server sidecar executable
LLAMA_SERVER_PATH = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/runtime/windows-x64/llama-server.exe")
)

# Server connection configuration
HOST = "127.0.0.1"
PORT = 12345
BASE_URL = f"http://{HOST}:{PORT}"

# Preferred model name (Q4_K_M)
MODEL_NAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
# Fallback model name (Q2_K)
FALLBACK_MODEL_NAME = "qwen2.5-3b-instruct-q2_k.gguf"

# Define default and fallback paths
preferred_model_path_1 = os.path.normpath("C:/Users/lenovo/Downloads/qwen2.5-3b-instruct-q4_k_m.gguf")
preferred_model_path_2 = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/models", MODEL_NAME)
)
fallback_model_path = os.path.normpath(
    os.path.join(ATHER_DIR, "aether-main/models", FALLBACK_MODEL_NAME)
)

# Check and select the active model path
if os.path.exists(preferred_model_path_1):
    MODEL_PATH = preferred_model_path_1
    print(f"[Config] Using preferred model Q4_K_M (Downloads) at: {MODEL_PATH}")
elif os.path.exists(preferred_model_path_2):
    MODEL_PATH = preferred_model_path_2
    print(f"[Config] Using preferred model Q4_K_M (Aether) at: {MODEL_PATH}")
elif os.path.exists(fallback_model_path):
    MODEL_PATH = fallback_model_path
    print(f"[Config] Preferred model {MODEL_NAME} not found. Falling back to Q2_K at: {MODEL_PATH}")
else:
    MODEL_PATH = preferred_model_path_1
    print(f"[Config] WARNING: Neither model found. Defaulting to preferred path: {MODEL_PATH}")

# Validate files
if not os.path.exists(LLAMA_SERVER_PATH):
    print(f"[Config] WARNING: llama-server.exe sidecar not found at: {LLAMA_SERVER_PATH}")
