"""
models/manager.py

Manages model configuration loading, updating, and validation.
Performs fallback checking against scanned GGUF files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from aether.models.scanner import scan_gguf_models

logger = logging.getLogger(__name__)

# Path to config.json in the same folder as this file
CONFIG_PATH = (Path(__file__).parent / "config.json").resolve()

# Fallback defaults if no models are scanned
DEFAULT_ROUTER = "qwen2.5-3b-instruct-q4_k_m.gguf"
DEFAULT_PLANNER = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"

def load_models_config() -> Dict[str, str]:
    """
    Loads, scans, and verifies selected models from config.json.
    Falls back to the first available GGUF if configured models are missing.
    Never crashes.
    """
    config_data = {
        "router_model": DEFAULT_ROUTER,
        "planner_model": DEFAULT_PLANNER
    }
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    config_data["router_model"] = loaded.get("router_model") or DEFAULT_ROUTER
                    config_data["planner_model"] = loaded.get("planner_model") or DEFAULT_PLANNER
        except Exception as e:
            logger.error(f"Error loading models config.json: {e}")
            
    # Scan the gguf folder
    available = scan_gguf_models()
    available_names = [m["name"] for m in available]
    
    updated = False
    if available_names:
        # Check if selected router model exists on disk
        if config_data["router_model"] not in available_names:
            old_model = config_data["router_model"]
            config_data["router_model"] = available_names[0]
            logger.warning(f"Router model '{old_model}' not found. Falling back to '{config_data['router_model']}'")
            updated = True
            
        # Check if selected planner model exists on disk
        if config_data["planner_model"] not in available_names:
            old_model = config_data["planner_model"]
            # Fallback to the coder model if available, or first model
            coder_fallback = next((m for m in available_names if "coder" in m.lower()), available_names[0])
            config_data["planner_model"] = coder_fallback
            logger.warning(f"Planner model '{old_model}' not found. Falling back to '{config_data['planner_model']}'")
            updated = True
            
    if updated or not CONFIG_PATH.exists():
        save_models_config(config_data["router_model"], config_data["planner_model"])
        
    return config_data

def save_models_config(router_model: str, planner_model: str) -> None:
    """Saves the router and planner configuration to config.json."""
    config_data = {
        "router_model": router_model,
        "planner_model": planner_model
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        logger.info(f"Saved model config to {CONFIG_PATH}: {config_data}")
    except Exception as e:
        logger.error(f"Failed to write models config.json: {e}")

def resolve_model_path(model_name: str) -> Path:
    """
    Resolves the model name to a path. Searches:
    1. aether/models/gguf/
    2. User Downloads directory (cross-platform fallback)
    3. aether-main/models/
    """
    # 1. Models/gguf/ folder
    gguf_path = (Path(__file__).parent / "gguf" / model_name).resolve()
    if gguf_path.exists():
        return gguf_path
        
    # 2. Downloads folder
    downloads_path = Path.home() / "Downloads" / model_name
    if downloads_path.exists():
        return downloads_path
        
    # 3. Aether main models folder
    root_dir = (Path(__file__).parent.parent.parent).resolve()
    alt_path = root_dir / "aether-main" / "models" / model_name
    if alt_path.exists():
        return alt_path
        
    # Default to the gguf folder
    return gguf_path
