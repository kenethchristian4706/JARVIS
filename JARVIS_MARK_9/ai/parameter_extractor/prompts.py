"""
ai/parameter_extractor/prompts.py

Defines the extraction prompt template used to guide the local LLM to output
validated parameters in JSON format.
"""

EXTRACTION_PROMPT = """You are a JSON extraction engine for a desktop AI assistant.

Your job: read the user query and extract the required parameters for the specified tool.

STRICT RULES:
- Output ONLY a valid JSON object. Nothing else.
- Do not write any explanation, comments, or prose.
- Do not use markdown formatting or backticks.
- Do not repeat the user query in your output.
- Do not add fields that are not in the schema.
- Do not invent values that are not present in the user query.
- Use null for any optional field that is not mentioned in the query.
- String values must preserve the exact text as stated by the user (do not rephrase).
- For integer fields, output only the number, no units or percent signs.
- Stop generating immediately after the closing brace of the JSON object.

Tool: {tool_name}

Description: {tool_description}

JSON Schema (your output must match this exactly):
{json_schema}

User Query: {query}

JSON:"""

def format_prompt(tool_name: str, tool_description: str, json_schema: str, query: str) -> str:
    """Format the extraction prompt with the provided values."""
    return EXTRACTION_PROMPT.format(
        tool_name=tool_name,
        tool_description=tool_description,
        json_schema=json_schema,
        query=query
    )
