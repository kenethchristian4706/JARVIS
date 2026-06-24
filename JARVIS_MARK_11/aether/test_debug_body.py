import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aether.config as config
from aether.llm.model import start_server

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

# Pass OpenAI-style response_format with type "json_schema"
payload = {
    "prompt": "Open chrome",
    "temperature": 0.0,
    "top_p": 1.0,
    "stream": False,
    "n_predict": 50,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "intent_schema",
            "schema": intent_schema
        }
    }
}

start_server()

url = f"{config.BASE_URL}/completion"
headers = {"Content-Type": "application/json"}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10.0) as response:
        print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print("Response body:")
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Other error:", e)
