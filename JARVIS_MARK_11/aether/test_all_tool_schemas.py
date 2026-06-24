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

print("Starting/checking server...")
if not start_server():
    print("Failed to start server")
    sys.exit(1)

failed_tools = []

for tool_name, tool_info in TOOLS.items():
    schema_class = tool_info["schema_class"]
    if hasattr(schema_class, "model_json_schema"):
        schema_dict = schema_class.model_json_schema()
    else:
        schema_dict = schema_class.schema()
        
    payload = {
        "prompt": f"Arguments for {tool_name}",
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "n_predict": 50,
        "json_schema": schema_dict
    }
    
    req = urllib.request.Request(
        f"{config.BASE_URL}/completion",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10.0) as response:
            pass # Success
    except urllib.error.HTTPError as e:
        print(f"FAIL: Tool '{tool_name}' failed with HTTP {e.code}: {e.reason}")
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            print("Error body:", json.dumps(err_body, indent=2))
        except Exception:
            pass
        failed_tools.append((tool_name, e.code))
    except Exception as e:
        print(f"FAIL: Tool '{tool_name}' error: {e}")
        failed_tools.append((tool_name, str(e)))

print("\n--- Summary ---")
print(f"Tested {len(TOOLS)} tools.")
if failed_tools:
    print(f"Failed tools count: {len(failed_tools)}")
    for name, err in failed_tools:
        print(f" - {name}: {err}")
else:
    print("All tool schemas passed successfully!")
