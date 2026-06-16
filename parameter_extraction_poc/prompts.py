"""
prompts.py

Contains the prompt template for parameter extraction.
"""

EXTRACTION_PROMPT = """You are a JSON extraction engine.

Extract arguments for the selected tool.

Return ONLY a valid JSON object.

Rules:
- Output ONLY JSON.
- Do not explain anything.
- Do not use markdown.
- Do not provide examples.
- Do not repeat the user query.
- Do not generate conversations.
- Stop immediately after generating the JSON object.
- Use null for missing values.
- Follow the schema exactly.

Tool:
{tool_name}

Description:
{tool_description}

JSON Schema:
{json_schema}

User Query:
{query}

JSON:"""
