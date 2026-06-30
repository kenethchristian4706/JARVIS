"""
api/events.py

EventManager to emit real-time assistant and executor execution events to the websocket.
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

class EventManager:
    """
    Manages and dispatches assistant execution pipeline events to active WebSocket sessions.
    """
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.callback = callback

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Helper to format and dispatch event payloads."""
        payload = {"type": event_type.lower(), **data}
        logger.info(f"Emitting event: {payload}")
        if self.callback:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(payload)
                else:
                    self.callback(payload)
            except Exception as e:
                logger.error(f"Error calling event dispatch: {e}")

    async def emit_thinking(self, message: str):
        await self.emit("thinking", {"message": message})

    async def emit_plan(self, steps: List[str]):
        await self.emit("plan", {"steps": steps})

    async def emit_step_start(self, step: str):
        await self.emit("step_start", {"step": step})

    async def emit_step_complete(self, step: str, success: bool):
        await self.emit("step_complete", {"step": step, "success": success})

    async def emit_tool_start(self, tool: str):
        await self.emit("tool_start", {"tool": tool})

    async def emit_tool_complete(self, tool: str, success: bool):
        await self.emit("tool_complete", {"tool": tool, "success": success})

    async def emit_error(self, message: str, error_code: Optional[str] = None):
        data = {"message": message}
        if error_code:
            data["error_code"] = error_code
        await self.emit("error", data)

    async def emit_final(self, message: str):
        await self.emit("final_response", {"message": message})
