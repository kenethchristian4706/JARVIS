"""
api/models.py

FastAPI APIRouter for GGUF model selection, discovery, configuration, and dynamic server reload/rollback.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aether.models.scanner import scan_gguf_models
from aether.models.manager import load_models_config, save_models_config
from aether.llm.model import reload_sidecar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])

class ModelSelectRequest(BaseModel):
    model: str

@router.get("")
async def get_models():
    """
    Returns the currently active router and planner models,
    as well as a list of all discovered GGUF files.
    """
    try:
        cfg = load_models_config()
        available = scan_gguf_models()
        available_names = [m["name"] for m in available]
        
        return {
            "router_model": cfg["router_model"],
            "planner_model": cfg["planner_model"],
            "available_models": available_names
        }
    except Exception as e:
        logger.error(f"Error fetching models status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/router")
async def select_router_model(req: ModelSelectRequest):
    """
    Changes the Router LLM model. Restarts only the router sidecar.
    Rolls back if model loading fails.
    """
    new_model = req.model.strip()
    available = scan_gguf_models()
    available_names = [m["name"] for m in available]
    
    if new_model not in available_names or not new_model.lower().endswith(".gguf"):
        raise HTTPException(status_code=400, detail="Model not found or invalid format.")
        
    cfg = load_models_config()
    old_model = cfg["router_model"]
    
    if old_model == new_model:
        return {"success": True, "message": "Router model is already active."}
        
    logger.info(f"Switching Router model from '{old_model}' to '{new_model}'")
    
    try:
        # Save config first
        save_models_config(new_model, cfg["planner_model"])
        
        # Try reloading the sidecar
        success = reload_sidecar("router", new_model)
        if not success:
            logger.error(f"Failed to reload sidecar with model '{new_model}'. Rolling back to '{old_model}'...")
            save_models_config(old_model, cfg["planner_model"])
            reload_sidecar("router", old_model)
            raise HTTPException(status_code=500, detail="Unable to load selected model. Rolled back.")
            
        return {"success": True, "message": "Router model updated."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching router model: {e}")
        save_models_config(old_model, cfg["planner_model"])
        reload_sidecar("router", old_model)
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}. Rolled back.")

@router.post("/planner")
async def select_planner_model(req: ModelSelectRequest):
    """
    Changes the Planner LLM model. Restarts only the planner sidecar.
    Rolls back if model loading fails.
    """
    new_model = req.model.strip()
    available = scan_gguf_models()
    available_names = [m["name"] for m in available]
    
    if new_model not in available_names or not new_model.lower().endswith(".gguf"):
        raise HTTPException(status_code=400, detail="Model not found or invalid format.")
        
    cfg = load_models_config()
    old_model = cfg["planner_model"]
    
    if old_model == new_model:
        return {"success": True, "message": "Planner model is already active."}
        
    logger.info(f"Switching Planner model from '{old_model}' to '{new_model}'")
    
    try:
        # Save config first
        save_models_config(cfg["router_model"], new_model)
        
        # Try reloading the sidecar
        success = reload_sidecar("planner", new_model)
        if not success:
            logger.error(f"Failed to reload planner sidecar with model '{new_model}'. Rolling back to '{old_model}'...")
            save_models_config(cfg["router_model"], old_model)
            reload_sidecar("planner", old_model)
            raise HTTPException(status_code=500, detail="Unable to load selected model. Rolled back.")
            
        return {"success": True, "message": "Planner model updated."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching planner model: {e}")
        save_models_config(cfg["router_model"], old_model)
        reload_sidecar("planner", old_model)
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}. Rolled back.")

@router.post("/refresh")
async def refresh_models():
    """
    Rescans the models folder and returns the current active and available GGUF list.
    """
    try:
        cfg = load_models_config()
        available = scan_gguf_models()
        available_names = [m["name"] for m in available]
        
        return {
            "router_model": cfg["router_model"],
            "planner_model": cfg["planner_model"],
            "available_models": available_names
        }
    except Exception as e:
        logger.error(f"Failed to refresh model scanning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open")
async def open_models_folder():
    """
    Opens the GGUF models folder using the active platform file explorer.
    """
    try:
        from aether.platforms import platform
        from aether.models.scanner import get_gguf_dir
        gguf_dir = get_gguf_dir()
        platform.file.open_file(str(gguf_dir))
        return {"success": True, "message": "Opened models folder."}
    except Exception as e:
        logger.error(f"Failed to open models folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))
