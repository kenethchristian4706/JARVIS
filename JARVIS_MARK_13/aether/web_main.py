"""
web_main.py

FastAPI app entrypoint for Aether's desktop UI connection.
Manages the lifecycle of LLM sidecar servers, background file indexer, and the uvicorn web server.
"""

import sys
import os
import logging
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Resolve project path to import aether package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aether.config import LOG_FILE
from aether.llm.model import start_server, stop_server
from aether.api.websocket import router as ws_router

app = FastAPI(
    title="Aether Assistant API",
    description="FastAPI WebSocket and REST API for Aether offline desktop assistant.",
    version="1.0"
)

# Allow CORS for local frontend development (offline utility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)

# Include email REST routes
from aether.email.connection import router as email_router
app.include_router(email_router)

# Include GGUF models selection REST routes
from aether.api.models import router as models_router
app.include_router(models_router)

def setup_logging():
    """Sets up file and console log handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aether.tools.indexer").setLevel(logging.WARNING)

def main():
    setup_logging()
    logger = logging.getLogger("aether_web")
    
    print("\n" + "="*60)
    print("      AETHER WEB INTERFACE BACKEND (V1)")
    print("="*60)
    print("Initializing sidecars and indexer. Please wait...")

    # Boot local models
    if not start_server():
        print("\n[Error] Failed to initialize local LLM sidecar server. Exiting.")
        sys.exit(1)

    # Boot indexing daemon
    from aether.tools.indexer import start_background_refresh
    start_background_refresh()

    # Reconnect saved email account from keyring
    from aether.email.email_manager import email_manager
    email_manager.reconnect()

    print("\nSystem ready! Web API Server is running on http://127.0.0.1:8000")
    print("WebSocket Endpoint: ws://127.0.0.1:8000/ws")
    print("="*60 + "\n")

    try:
        # Run uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        print("Stopping sidecars and indexer...")
        stop_server()
        print("Shutdown completed successfully!")

if __name__ == "__main__":
    main()
