"""
planner/context.py

Implements ExecutionContext and reference resolution for sequential actions.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ExecutionContext:
    """
    Stores runtime variables/objects created during the execution of actions.
    """
    def __init__(self):
        self.variables: Dict[str, Any] = {}

    def store(self, name: str, value: Any) -> None:
        """Stores a variable in the execution context."""
        self.variables[name] = value

    def get(self, name: str) -> Any:
        """Retrieves a variable from the execution context."""
        return self.variables.get(name)


def resolve_parameters(parameters: Any, execution_context: ExecutionContext) -> Any:
    """
    Recursively resolves symbolic references (strings starting with '$')
    using the given execution_context.
    
    If the resolved value is a dictionary and contains a 'path' key,
    it returns only the value of the 'path' key.
    """
    if isinstance(parameters, str):
        if parameters.startswith("$"):
            var_name = parameters[1:]
            val = execution_context.get(var_name)
            if val is None:
                raise ValueError(f"Unknown reference: '{parameters}'")
            
            resolved_val = val
            # Resolve rules: if the resolved object is a dictionary and has a 'path' key,
            # inject only the path.
            if isinstance(val, dict) and "path" in val:
                resolved_val = val["path"]
            
            logger.info(f"Resolved reference '{parameters}' -> '{resolved_val}'")
            return resolved_val
        return parameters
    elif isinstance(parameters, list):
        return [resolve_parameters(item, execution_context) for item in parameters]
    elif isinstance(parameters, dict):
        return {k: resolve_parameters(v, execution_context) for k, v in parameters.items()}
    else:
        return parameters
