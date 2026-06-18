"""
validation/schema_validator.py

Performs Pydantic schema validation on extracted parameters.
"""

import logging
from typing import Dict, Any, Tuple
from aether.registry.tools import TOOLS

logger = logging.getLogger(__name__)

def validate_parameters(tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validates a dictionary of parameters against the Pydantic schema class registered for the tool.
    
    Returns:
        (success, validated_parameters_dict, error_message)
    """
    if tool_name not in TOOLS:
        return False, {}, f"Tool '{tool_name}' is not registered."

    tool_info = TOOLS[tool_name]
    schema_class = tool_info["schema_class"]

    try:
        # Pydantic validation: validates types and constraints
        instance = schema_class(**parameters)
        # Support both Pydantic V1 (.dict()) and V2 (.model_dump())
        dump_fn = getattr(instance, "model_dump", None) or getattr(instance, "dict", None)
        return True, dump_fn() if dump_fn else parameters, ""
    except Exception as e:
        logger.warning(f"Schema validation failed for tool '{tool_name}' with parameters {parameters}: {e}")
        return False, parameters, str(e)
