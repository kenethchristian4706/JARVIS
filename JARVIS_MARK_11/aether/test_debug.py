import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aether.config as config
from aether.llm.model import generate_completion

intent_schema = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["application_management", "file_operations", "browser_operations", "system_control"]
        },
        "tool": {
            "type": "string",
            "enum": ["open_app", "close_app"]
        }
    },
    "required": ["category", "tool"]
}

try:
    print("Testing generate_completion with json_schema...")
    res = generate_completion("Open chrome", json_schema=intent_schema, max_tokens=50)
    print("Success response:", res)
except Exception as e:
    print("Failed with exception:", e)
