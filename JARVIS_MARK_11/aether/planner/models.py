"""
planner/models.py

Defines Pydantic models for the planner.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Action(BaseModel):
    id: Optional[str] = Field(None, description="Optional ID to identify resources created during execution.")
    tool: str = Field(description="Name of the tool to execute.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool.")

class ExecutionPlan(BaseModel):
    actions: List[Action] = Field(default_factory=list, description="Sequence of actions to execute.")
