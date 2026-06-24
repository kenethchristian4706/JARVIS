"""
planner/tool_collector.py

Collects all candidate tools belonging to the specified intents using existing registry metadata.
"""

from typing import List
from aether.registry.tools import TOOLS

# Map user intents to registry category names
INTENT_TO_CATEGORY = {
    "application_management": "application_management",
    "file_system": "file_operations",
    "file_operations": "file_operations",
    "browser_operations": "browser_operations",
    "system_control": "system_control"
}

def collect_candidate_tools(intents: List[str]) -> List[str]:
    """
    Given a list of intents, returns a list of all tools belonging to those intents.
    Uses existing registry metadata from aether.registry.tools.
    
    Args:
        intents: List of intent/category names.
        
    Returns:
        List of matching tool name strings.
    """
    categories = set()
    for intent in intents:
        cat = INTENT_TO_CATEGORY.get(intent)
        if cat:
            categories.add(cat)
            
    candidate_tools = []
    for tool_name, tool_info in TOOLS.items():
        if tool_info.get("category") in categories:
            candidate_tools.append(tool_name)
            
    return sorted(candidate_tools)
