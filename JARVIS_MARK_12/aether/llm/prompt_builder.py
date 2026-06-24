"""
llm/prompt_builder.py

Dynamically generates a compact planner prompt based on selected candidate tools.
"""

import os
from typing import List
from aether.registry.tools import ToolMetadata

class DynamicPromptBuilder:
    @staticmethod
    def build_prompt(query: str, candidate_tools: List[ToolMetadata]) -> str:
        """
        Builds a compact action planning prompt from candidate tools.
        
        Args:
            query: User's query string.
            candidate_tools: List of ToolMetadata for candidate tools.
            
        Returns:
            The compiled prompt string.
        """
        tools_str = ""
        for tool in candidate_tools:
            params_str = ", ".join(tool.parameters)
            tools_str += f"{tool.name}({params_str})\n{tool.description}\n\n"
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "planner_prompt.txt")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_tmpl = f.read()
            
        prompt = (
            prompt_tmpl.replace("{candidate_tools}", tools_str.strip())
            .replace("{query}", query)
        )
        return prompt
