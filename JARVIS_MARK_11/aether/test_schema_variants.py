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

# Variant 1: Original top-level json_schema
payload_v1 = {
    "prompt": "Open chrome",
    "temperature": 0.0,
    "top_p": 1.0,
    "stream": False,
    "n_predict": 50,
    "json_schema": intent_schema
}

# Variant 2: OpenAI-style response_format with top-level response_format
payload_v2 = {
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

# Variant 3: json_schema as nested under schema key
payload_v3 = {
    "prompt": "Open chrome",
    "temperature": 0.0,
    "top_p": 1.0,
    "stream": False,
    "n_predict": 50,
    "json_schema": {
        "schema": intent_schema
    }
}

# Variant 4: json_schema as a serialized JSON string
payload_v4 = {
    "prompt": "Open chrome",
    "temperature": 0.0,
    "top_p": 1.0,
    "stream": False,
    "n_predict": 50,
    "json_schema": json.dumps(intent_schema)
}

# Variant 5: openai response_format but on /v1/chat/completions
# Let's test completion variants first.

variants = {
    "v1 (top-level json_schema)": (f"{config.BASE_URL}/completion", payload_v1),
    "v2 (response_format /completion)": (f"{config.BASE_URL}/completion", payload_v2),
    "v3 (nested json_schema/schema)": (f"{config.BASE_URL}/completion", payload_v3),
    "v4 (serialized json_schema string)": (f"{config.BASE_URL}/completion", payload_v4),
}

print("Starting llama-server sidecar...")
if not start_server():
    print("Failed to start server!")
    sys.exit(1)

for name, (url, payload) in variants.items():
    print(f"\n--- Testing variant: {name} ---")
    print("URL:", url)
    print("Payload:", json.dumps(payload, indent=2))
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10.0) as response:
            body = response.read().decode('utf-8')
            print(f"STATUS: {response.status}")
            print("RESPONSE BODY:")
            try:
                print(json.dumps(json.loads(body), indent=2))
            except Exception:
                print(body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print("RESPONSE BODY:")
        try:
            print(json.dumps(json.loads(e.read().decode('utf-8')), indent=2))
        except Exception as ex:
            print("Failed parsing error body:", ex)
    except Exception as e:
        print("Error:", e)
