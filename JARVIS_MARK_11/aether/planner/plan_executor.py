"""
planner/plan_executor.py

Sequentially executes actions in an ExecutionPlan, reusing existing validation, safety, and executor logic.
"""

import logging
from typing import Tuple
from aether.planner.models import ExecutionPlan

logger = logging.getLogger(__name__)

def execute_plan(plan: ExecutionPlan) -> Tuple[bool, str]:
    """
    Sequentially processes and executes each action in the ExecutionPlan.
    Reuses existing logic for folder resolution, clarification prompts,
    schema validation, safety gates, and tool execution.
    
    Returns:
        (success: bool, output_message: str)
    """
    from aether.assistant import resolve_special_folders, handle_missing_parameters
    from aether.validation.schema_validator import validate_parameters
    from aether.validation.safety_checker import needs_safety_confirmation, ask_user_confirmation
    from aether.executor.executor import execute_tool
    from aether.planner.context import ExecutionContext, resolve_parameters
    
    execution_context = ExecutionContext()
    outputs = []
    
    for idx, action in enumerate(plan.actions):
        tool_name = action.tool
        params = action.parameters
        
        # 0. Resolve symbolic references using the execution context
        try:
            params = resolve_parameters(params, execution_context)
        except ValueError as e:
            err_msg = f"Action {idx+1} ({tool_name}) reference resolution failed: {e}"
            logger.warning(err_msg)
            outputs.append(err_msg)
            return False, "\n".join(outputs)
        
        # 1. Special folder resolution & clarification workflows
        params = resolve_special_folders(tool_name, params)
        dummy_metrics = {"clarification": "None"}
        params, p_success = handle_missing_parameters(tool_name, params, dummy_metrics)
        if not p_success:
            err_msg = f"Action {idx+1} ({tool_name}) aborted: Required parameter omitted."
            logger.warning(err_msg)
            outputs.append(err_msg)
            return False, "\n".join(outputs)
            
        params = resolve_special_folders(tool_name, params)
        
        # 2. Schema validation
        success, validated_params, error = validate_parameters(tool_name, params)
        if not success:
            err_msg = f"Action {idx+1} ({tool_name}) validation failed: {error}"
            logger.warning(err_msg)
            outputs.append(err_msg)
            return False, "\n".join(outputs)
            
        # 3. Safety Check Gate
        if needs_safety_confirmation(tool_name):
            confirmed = ask_user_confirmation(tool_name, validated_params)
            if not confirmed:
                err_msg = f"Action {idx+1} ({tool_name}) cancelled: Safety confirmation was not granted."
                logger.warning(err_msg)
                outputs.append(err_msg)
                return False, "\n".join(outputs)
            if tool_name == "send_email":
                validated_params["confirmed"] = True
                
        # 4. Execute Tool
        logger.info(f"Executing action {idx+1}/{len(plan.actions)}: {tool_name}")
        exec_success, exec_output = execute_tool(tool_name, validated_params)
        outputs.append(exec_output)
        
        if not exec_success:
            logger.warning(f"Action {idx+1} ({tool_name}) execution failed. Stopping plan.")
            return False, "\n".join(outputs)
            
        # 5. Store output under symbolic ID if action has one
        if action.id:
            raw_res = getattr(exec_output, "raw_result", None)
            if raw_res is None:
                raw_res = exec_output
            execution_context.store(action.id, raw_res)
            logger.info(f"Stored variable [{action.id}] -> {raw_res}")
            
    return True, "\n".join(outputs)
