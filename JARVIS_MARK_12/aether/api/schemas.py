"""
api/schemas.py

Pydantic validation schemas for the Aether WebSocket API.
"""

from pydantic import BaseModel

class UserMessage(BaseModel):
    type: str
    message: str
