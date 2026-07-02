"""
llm/category_engine.py

Python Category Engine for deterministic candidate tool expansion, alias resolution,
dependency tracking, scoring, ranking, and truncation (5-15 tools max).
"""

import re
from typing import List, Dict, Set, Any
from aether.registry.micro_categories import MICRO_CATEGORY_TO_TOOLS
from aether.registry.tools_metadata import TOOLS_METADATA

# Default tools to use for padding if candidates list is too short
DEFAULT_PAD_TOOLS = [
    "open_app",
    "open_file",
    "search_files",
    "take_screenshot",
    "list_running_apps",
    "get_clipboard"
]

class CategoryEngine:
    @staticmethod
    def get_candidate_tools(query: str, categories: List[str]) -> List[str]:
        """
        Determines the candidate tools based on micro-categories, query keywords,
        and dependency expansion, ranks them, and returns between 5 and 15 tools.
        """
        query_lower = query.lower()
        candidate_sources: Dict[str, str] = {} # maps tool_name -> source ('direct', 'alias', 'dependency')

        # 1. Direct Category Mapping
        for cat in categories:
            if cat in MICRO_CATEGORY_TO_TOOLS:
                for tool in MICRO_CATEGORY_TO_TOOLS[cat]:
                    candidate_sources[tool] = "direct"

        # 2. Query Alias/Keyword Expansion
        alias_rules = {
            r"\b(open|launch|run|start)\b": ["open_app"],
            r"\b(close|stop|terminate|kill|exit)\b": ["close_app"],
            r"\b(delete|remove|trash|destroy)\b": ["delete_file", "delete_folder"],
            r"\b(search|find|locate)\b": ["search_files"],
            r"\b(write|type|note|notepad)\b": ["open_notepad_and_write"],
            r"\b(screenshot|capture|snap)\b": ["take_screenshot"],
            r"\b(copy|clipboard|clip)\b": ["set_clipboard", "get_clipboard", "clear_clipboard"],
            r"\b(doc|docx|word|report|letter|proposal)\b": ["create_word", "read_word", "edit_word"],
            r"\b(xls|xlsx|excel|sheet|spreadsheet|workbook|cell)\b": ["create_excel", "read_excel", "write_excel"]
        }

        for regex, tools in alias_rules.items():
            if re.search(regex, query_lower):
                for tool in tools:
                    # Keep 'direct' if it was already added directly
                    if tool not in candidate_sources:
                        candidate_sources[tool] = "alias"

        # 3. Dependency Expansion (Loop until no new tools are added)
        dependency_rules = {
            "append_file": ["create_file", "read_file_content"],
            "open_file": ["search_files"],
            "extract_archive": ["list_directory"],
            "compress_files": ["list_directory"],
            "send_email": ["get_clipboard"],
            "extract_text_from_image": ["read_file_content", "open_file"],
            "edit_word": ["read_word", "create_word"],
            "write_excel": ["read_excel", "create_excel"]
        }

        # Iteratively expand dependencies to capture transitive ones
        added_new = True
        while added_new:
            added_new = False
            current_candidates = list(candidate_sources.keys())
            for tool in current_candidates:
                if tool in dependency_rules:
                    for dep in dependency_rules[tool]:
                        if dep not in candidate_sources:
                            candidate_sources[dep] = "dependency"
                            added_new = True

        # Extract words from query for scoring
        query_words = set(re.findall(r"\w+", query_lower))

        # 4. Score and Rank ALL Candidate Tools
        scored_tools = []
        for tool_name, metadata in TOOLS_METADATA.items():
            score = 0
            
            # Base score from candidate source
            source = candidate_sources.get(tool_name)
            if source == "direct":
                score += 20
            elif source == "alias":
                score += 10
            elif source == "dependency":
                score += 5
                
            # Query word overlap score
            # Gather all text metadata for the tool
            metadata_text = (
                tool_name.lower().replace("_", " ") + " " +
                metadata.get("Purpose", "").lower() + " " +
                " ".join(metadata.get("Keywords", [])) + " " +
                " ".join(metadata.get("Aliases", []))
            )
            metadata_words = set(re.findall(r"\w+", metadata_text))
            
            # Calculate overlapping words
            overlap = query_words.intersection(metadata_words)
            score += len(overlap) * 2  # 2 points per matching word
            
            # If the tool name itself is in the query, add bonus
            if tool_name.replace("_", " ") in query_lower:
                score += 8
                
            # If any of the tool's keywords or name matches a query word exactly
            for kw in metadata.get("Keywords", []):
                if kw in query_words:
                    score += 3
            
            if score > 0 or tool_name in candidate_sources:
                scored_tools.append((tool_name, score))

        # Sort by score descending
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        ranked_tool_names = [t[0] for t in scored_tools]

        # 5. Truncate / Pad (ensure 5 to 15 tools)
        if len(ranked_tool_names) < 5:
            # Pad with default tools that are not already present
            for pad_tool in DEFAULT_PAD_TOOLS:
                if pad_tool not in ranked_tool_names:
                    ranked_tool_names.append(pad_tool)
                    if len(ranked_tool_names) >= 5:
                        break

        # Slice at 15
        final_candidates = ranked_tool_names[:15]
        return final_candidates
