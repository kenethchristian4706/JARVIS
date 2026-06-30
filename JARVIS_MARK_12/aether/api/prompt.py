"""
api/prompt.py

Interactive prompt coordination module for the Aether assistant.
Allows synchronous tool execution threads to prompt the React frontend for input 
over WebSockets and wait for responses, falling back to CLI console stdin.
"""

import uuid
import queue
import threading
import asyncio
import logging
import contextvars
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

_global_manager = None
_global_loop = None

class CurrentExecution:
    """
    Stores contextvars references to the EventManager and asyncio event loop
    handling the active client session, propagated across async tasks and threadpools.
    Also maintains global references as a fallback to guarantee thread-safe visibility.
    """
    _manager_var = contextvars.ContextVar('event_manager', default=None)
    _loop_var = contextvars.ContextVar('loop', default=None)
    
    @classmethod
    def set_context(cls, event_manager: Any, loop: asyncio.AbstractEventLoop):
        global _global_manager, _global_loop
        _global_manager = event_manager
        _global_loop = loop
        cls._manager_var.set(event_manager)
        cls._loop_var.set(loop)
        
    @classmethod
    def get_event_manager(cls) -> Optional[Any]:
        val = cls._manager_var.get()
        if val is not None:
            return val
        return _global_manager
        
    @classmethod
    def get_loop(cls) -> Optional[asyncio.AbstractEventLoop]:
        val = cls._loop_var.get()
        if val is not None:
            return val
        return _global_loop


# Global mapping of prompt_id -> response queue.Queue
active_prompts: Dict[str, queue.Queue] = {}
active_prompts_lock = threading.Lock()

def register_prompt(prompt_id: str, q: queue.Queue):
    with active_prompts_lock:
        active_prompts[prompt_id] = q

def resolve_prompt(prompt_id: str, value: str):
    """
    Resolves a pending prompt by pushing the client's choice to its response queue.
    """
    with active_prompts_lock:
        if prompt_id in active_prompts:
            active_prompts[prompt_id].put(value)
            del active_prompts[prompt_id]

def prompt_user_sync(title: str, options: List[str]) -> str:
    """
    Prompts the user for clarification or choice.
    If running under WebSocket, streams a prompt event and blocks until client input is returned.
    Otherwise falls back to command-line input.
    """
    manager = CurrentExecution.get_event_manager()
    loop = CurrentExecution.get_loop()
    
    if not manager or not loop:
        logger.info(f"prompt_user_sync: Event execution context is missing (manager={manager}, loop={loop}). Falling back to CLI console stdin.")
        # Synchronous fallback for local CLI runs
        print(f"\n{title}")
        for idx, opt in enumerate(options, 1):
            print(f"  {idx}. {opt}")
        try:
            return input("Please select: ").strip()
        except (KeyboardInterrupt, EOFError, Exception):
            return "cancel"
            
    prompt_id = str(uuid.uuid4())
    logger.info(f"prompt_user_sync: Dispatching user prompt '{prompt_id}' to frontend via WebSocket.")
    q = queue.Queue()
    register_prompt(prompt_id, q)

    
    # Broadcast prompt event over WebSocket
    async def emit_prompt():
        await manager.emit("user_prompt", {
            "prompt_id": prompt_id,
            "title": title,
            "options": options
        })
        
    asyncio.run_coroutine_threadsafe(emit_prompt(), loop)
    
    # Wait for client input (timeout after 3 minutes)
    try:
        response = q.get(timeout=180.0)
        return response
    except queue.Empty:
        logger.warning(f"User prompt '{prompt_id}' timed out after 180s.")
        return "cancel"
