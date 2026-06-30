"""
api/websocket.py

FastAPI WebSocket router handling connections, messages, and command routing for the assistant.
"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import List, Dict, Any

from aether.api.schemas import UserMessage
from aether.api.events import EventManager
from aether.assistant import process_query
import aether.llm.model as llm_model
import aether.config as config

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """
    Manages active WebSocket client connections and status broadcasting.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current LLM status as initial payload in a background task
        asyncio.create_task(self.send_llm_status(websocket))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to connection: {e}")

    async def send_llm_status(self, websocket: WebSocket):
        router_running, planner_running = await asyncio.gather(
            asyncio.to_thread(llm_model.is_sidecar_running, "router"),
            asyncio.to_thread(llm_model.is_sidecar_running, "planner")
        )
        status = {
            "type": "llm_status",
            "router_running": router_running,
            "planner_running": planner_running,
            "router_model": config.ROUTER_MODEL_NAME,
            "planner_model": config.PLANNER_MODEL_NAME,
            "router_port": config.ROUTER_PORT,
            "planner_port": config.PLANNER_PORT,
            "endpoint": f"http://{config.HOST}"
        }
        try:
            await websocket.send_json(status)
        except Exception as e:
            logger.error(f"Error sending LLM status: {e}")

manager = ConnectionManager()

@router.get("/")
async def root_health():
    return {
        "status": "online",
        "message": "Aether API Server is active. Access websocket endpoint at ws://127.0.0.1:8000/ws"
    }

@router.get("/ws")
async def ws_health():
    return {
        "status": "online",
        "message": "Please connect using a WebSocket client interface at ws://127.0.0.1:8000/ws"
    }

@router.websocket("/ws")

async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
    except Exception as e:
        logger.error(f"WebSocket handshake failed: {e}")
        return
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "user_message":
                query = data.get("message", "")
                if not query:
                    continue
                
                # Execute assistant process query in a background task to keep WS reactive
                asyncio.create_task(run_assistant_task(websocket, query))
                
            elif msg_type == "llm_status_request":
                await manager.send_llm_status(websocket)
                
            elif msg_type == "start_llm":
                logger.info("Received WS start_llm command")
                await asyncio.to_thread(llm_model.start_server)
                await manager.send_llm_status(websocket)
                
            elif msg_type == "stop_llm":
                logger.info("Received WS stop_llm command")
                await asyncio.to_thread(llm_model.stop_server)
                await manager.send_llm_status(websocket)
                
            elif msg_type == "prompt_response":
                prompt_id = data.get("prompt_id")
                selection = data.get("selection", "")
                logger.info(f"Received WS prompt_response: prompt_id={prompt_id}, selection={selection}")
                from aether.api.prompt import resolve_prompt
                resolve_prompt(prompt_id, selection)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket encounter error: {e}")

async def run_assistant_task(websocket: WebSocket, query: str):
    """
    Wraps the process_query execution inside an async callback EventManager to send live execution steps.
    """
    async def send_to_ws(event: dict):
        try:
            await websocket.send_json(event)
        except Exception as e:
            logger.error(f"Error forwarding event to WS: {e}")
            
    event_manager = EventManager(callback=send_to_ws)
    
    # Register event manager and current thread loop to handle user selections asynchronously
    from aether.api.prompt import CurrentExecution
    loop = asyncio.get_running_loop()
    CurrentExecution.set_context(event_manager, loop)
    
    try:
        await process_query(query, events=event_manager)
    except Exception as e:
        logger.exception(f"Error executing assistant process_query task: {e}")
        await event_manager.emit_error(str(e))

@router.get("/api/llm/status")
async def get_llm_status_api():
    router_running, planner_running = await asyncio.gather(
        asyncio.to_thread(llm_model.is_sidecar_running, "router"),
        asyncio.to_thread(llm_model.is_sidecar_running, "planner")
    )
    return {
        "router_running": router_running,
        "planner_running": planner_running,
        "router_model": config.ROUTER_MODEL_NAME,
        "planner_model": config.PLANNER_MODEL_NAME,
        "router_port": config.ROUTER_PORT,
        "planner_port": config.PLANNER_PORT,
        "endpoint": f"http://{config.HOST}"
    }

@router.post("/api/llm/start")
async def start_llm_api():
    await asyncio.to_thread(llm_model.start_server)
    router_running, planner_running = await asyncio.gather(
        asyncio.to_thread(llm_model.is_sidecar_running, "router"),
        asyncio.to_thread(llm_model.is_sidecar_running, "planner")
    )
    status_payload = {
        "type": "llm_status",
        "router_running": router_running,
        "planner_running": planner_running,
        "router_model": config.ROUTER_MODEL_NAME,
        "planner_model": config.PLANNER_MODEL_NAME,
        "router_port": config.ROUTER_PORT,
        "planner_port": config.PLANNER_PORT,
        "endpoint": f"http://{config.HOST}"
    }
    await manager.broadcast(status_payload)
    return {"success": True}

@router.post("/api/llm/stop")
async def stop_llm_api():
    await asyncio.to_thread(llm_model.stop_server)
    router_running, planner_running = await asyncio.gather(
        asyncio.to_thread(llm_model.is_sidecar_running, "router"),
        asyncio.to_thread(llm_model.is_sidecar_running, "planner")
    )
    status_payload = {
        "type": "llm_status",
        "router_running": router_running,
        "planner_running": planner_running,
        "router_model": config.ROUTER_MODEL_NAME,
        "planner_model": config.PLANNER_MODEL_NAME,
        "router_port": config.ROUTER_PORT,
        "planner_port": config.PLANNER_PORT,
        "endpoint": f"http://{config.HOST}"
    }
    await manager.broadcast(status_payload)
    return {"success": True}
