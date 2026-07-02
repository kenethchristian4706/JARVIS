"""
models/scanner.py

Scans the models/gguf folder recursively for GGUF model files.
"""

from pathlib import Path
from typing import List, Dict

# Resolve the models/gguf folder relative to this file
GGUF_DIR = (Path(__file__).parent / "gguf").resolve()

def scan_gguf_models() -> List[Dict[str, str]]:
    """
    Recursively scans the local 'gguf/' folder for *.gguf files.
    Creates the directory if it does not exist.
    """
    if not GGUF_DIR.exists():
        GGUF_DIR.mkdir(parents=True, exist_ok=True)
        
    models = []
    # Recursively find all *.gguf files using rglob
    for path in GGUF_DIR.rglob("*.gguf"):
        if path.is_file():
            models.append({
                "name": path.name,
                "path": str(path.resolve())
            })
            
    # Sort models by name for consistency
    models.sort(key=lambda x: x["name"].lower())
    return models

def get_gguf_dir() -> Path:
    """Returns the absolute Path of the GGUF model directory."""
    if not GGUF_DIR.exists():
        GGUF_DIR.mkdir(parents=True, exist_ok=True)
    return GGUF_DIR
