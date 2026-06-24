"""
planner/validator.py

Validates the structure and parameter schemas of generated execution plans.
"""

import logging
from typing import Tuple, List
from aether.registry.tools import TOOLS
from aether.planner.models import ExecutionPlan
from aether.validation.schema_validator import validate_parameters

logger = logging.getLogger(__name__)

def validate_plan(plan: ExecutionPlan, candidate_tools: List[str]) -> Tuple[bool, str]:
    """
    Validates tool names, candidate tools membership, and parameter schema validity.
    Uses existing validation modules where possible.
    
    Returns:
        (success: bool, error_message: str)
    """
    if not plan.actions:
        return False, "Plan does not contain any actions."

    for idx, action in enumerate(plan.actions):
        tool_name = action.tool
        
        # 1. Tool exists
        if tool_name not in TOOLS:
            err = f"Action {idx+1}: Tool '{tool_name}' is not registered."
            logger.warning(err)
            return False, err
            
        # 2. Tool belongs to candidate tools
        if tool_name not in candidate_tools:
            err = f"Action {idx+1}: Tool '{tool_name}' is not in candidate tools list."
            logger.warning(err)
            return False, err
            
        # 3. Parameters are valid (using existing schema validation system)
        success, validated_params, error = validate_parameters(tool_name, action.parameters)
        if not success:
            err = f"Action {idx+1} ({tool_name}) parameters invalid: {error}"
            logger.warning(err)
            return False, err
            
        # Update action parameters with default values populated by schema validator
        action.parameters = validated_params
            
    return True, ""
