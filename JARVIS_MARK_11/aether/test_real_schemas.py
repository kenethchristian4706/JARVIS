import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aether.config as config
from aether.llm.model import start_server
from aether.registry.tools import TOOLS

print("Starting llama-server...")
start_server()

# 1. Test the full intent selector schema
CATEGORIES = [
    "application_management",
    "file_operations",
    "browser_operations",
    "system_control"
]

intent_schema = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": CATEGORIES
        },
        "tool": {
            "type": "string",
            "enum": list(TOOLS.keys())
        }
    },
    "required": ["category", "tool"]
}

payload_intent = {
    "prompt": "Open chrome",
    "temperature": 0.0,
    "top_p": 1.0,
    "stream": False,
    "n_predict": 25,
    "json_schema": intent_schema
}

print("\n--- Testing Intent Selector Schema ---")
req = urllib.request.Request(
    f"{config.BASE_URL}/completion",
    data=json.dumps(payload_intent).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10.0) as response:
        print(f"Intent Schema Success: {response.status}")
        print(response.read().decode('utf-8')[:200])
except urllib.error.HTTPError as e:
    print(f"Intent Schema HTTP Error {e.code}: {e.reason}")
    print("Response body:")
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)

# 2. Test Tool schemas
for tool_name, tool_info in list(TOOLS.items())[:5]:
    schema_class = tool_info["schema_class"]
    if hasattr(schema_class, "model_json_schema"):
        schema_dict = schema_class.model_json_schema()
    else:
        schema_dict = schema_class.schema()
        
    print(f"\n--- Testing Tool Schema for '{tool_name}' ---")
    payload_tool = {
        "prompt": f"Arguments for {tool_name}",
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "n_predict": 50,
        "json_schema": schema_dict
    }
    
    req = urllib.request.Request(
        f"{config.BASE_URL}/completion",
        data=json.dumps(payload_tool).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10.0) as response:
            print(f"Tool '{tool_name}' Success: {response.status}")
            print(response.read().decode('utf-8')[:200])
    except urllib.error.HTTPError as e:
        print(f"Tool '{tool_name}' HTTP Error {e.code}: {e.reason}")
        print("Response body:")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print("Error:", e)
