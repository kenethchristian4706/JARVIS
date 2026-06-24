import sys
import json
import urllib.request
import urllib.error
import logging
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Setup logging to stdout
logging.basicConfig(level=logging.INFO)

import aether.config as config
from aether.llm.model import generate_completion
from aether.registry.tools import TOOLS

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

# 1. Load prompt template
base_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(base_dir, "prompts", "intent_prompt.txt")

with open(prompt_path, "r", encoding="utf-8") as f:
    prompt_tmpl = f.read()
    
prompt = prompt_tmpl.replace("{query}", "open notepad")

print("Calling generate_completion with real prompt and logging error body...")
try:
    # We will modify our local urlopen call by catching HTTPError and reading body:
    url = f"{config.BASE_URL}/completion"
    effective_max_tokens = 25
    temperature = getattr(config, "TEMPERATURE", 0.0)
    top_p = getattr(config, "TOP_P", 1.0)
    stop_sequences = ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"]
    
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
        "n_predict": effective_max_tokens,
        "stop": stop_sequences,
        "json_schema": intent_schema
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=90.0) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        print("Success response:", res_data.get("content", "").strip())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print("------------------------------------")
    print(e.read().decode('utf-8'))
    print("------------------------------------")
except Exception as e:
    print("Failed with exception:", e)
