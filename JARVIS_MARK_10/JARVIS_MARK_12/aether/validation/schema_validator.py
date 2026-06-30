"""
validation/schema_validator.py

Performs Pydantic schema validation on extracted parameters.
Checks existence, unknown parameters, required fields, types, and constraints.
"""

import logging
from typing import Dict, Any, Tuple
from aether.registry.tools import TOOLS

logger = logging.getLogger(__name__)

def validate_parameters(tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validates a dictionary of parameters against the Pydantic schema class registered for the tool.
    
    Returns:
        (success: bool, validated_parameters_dict: Dict, error_message: str)
    """
    if tool_name not in TOOLS:
        return False, {}, f"Tool '{tool_name}' is not registered."

    tool_info = TOOLS[tool_name]
    schema_class = tool_info["schema_class"]

    # 1. Verify unknown parameters
    fields = getattr(schema_class, "model_fields", None) or getattr(schema_class, "__fields__", {})
    allowed_params = set(fields.keys())
    provided_params = set(parameters.keys())
    
    unknown_params = provided_params - allowed_params
    if unknown_params:
        return False, parameters, f"Tool '{tool_name}' received unknown parameters: {list(unknown_params)}. Allowed parameters are: {list(allowed_params)}"

    try:
        # Pydantic validation: validates types, required fields, and constraints (including enums)
        instance = schema_class(**parameters)
        # Support both Pydantic V1 (.dict()) and V2 (.model_dump())
        dump_fn = getattr(instance, "model_dump", None) or getattr(instance, "dict", None)
        return True, dump_fn() if dump_fn else parameters, ""
    except Exception as e:
        logger.warning(f"Schema validation failed for tool '{tool_name}' with parameters {parameters}: {e}")
        return False, parameters, str(e)
