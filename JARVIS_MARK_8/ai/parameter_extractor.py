"""
ai/parameter_extractor.py

Implements parameter extraction by managing a llama-server.exe sidecar process,
submitting structured prompts with JSON schemas, cleaning raw LLM outputs,
and validating parameters.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
import re
import json_repair
from typing import Dict, Any, Optional

import config
from ai.prompts import EXTRACTION_PROMPT
from validation.schemas import TOOL_REGISTRY

class ParameterExtractor:
    def __init__(self):
        self._server_process: Optional[subprocess.Popen] = None
        
    def start_sidecar_server(self, timeout_seconds: int = 45) -> bool:
        """
        Launches llama-server.exe in the background and waits for it to become ready.
        """
        if self._server_process is not None:
            if self._server_process.poll() is None:
                return True
            else:
                self._server_process = None

        if not os.path.exists(config.LLAMA_SERVER_PATH):
            print(f"[Sidecar] ERROR: llama-server.exe not found at {config.LLAMA_SERVER_PATH}", file=sys.stderr)
            return False

        if not os.path.exists(config.MODEL_PATH):
            print(f"[Sidecar] ERROR: Model file not found at {config.MODEL_PATH}", file=sys.stderr)
            return False

        print(f"[Sidecar] Starting sidecar server: {config.LLAMA_SERVER_PATH}")
        print(f"[Sidecar] Model: {config.MODEL_PATH}")
        print(f"[Sidecar] Endpoint: {config.BASE_URL}")

        # Launch command
        cmd = [
            config.LLAMA_SERVER_PATH,
            "-m", config.MODEL_PATH,
            "--host", config.HOST,
            "--port", str(config.PORT),
            "-c", "2048",
            "-ngl", "0"
        ]

        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except Exception as e:
            print(f"[Sidecar] Error launching server process: {e}", file=sys.stderr)
            return False

        # Wait for initialization
        health_url = f"{config.BASE_URL}/health"
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if self._server_process.poll() is not None:
                _, stderr_content = self._server_process.communicate()
                print(f"[Sidecar] Server process exited with code {self._server_process.returncode}.", file=sys.stderr)
                self._server_process = None
                return False
                
            try:
                with urllib.request.urlopen(health_url, timeout=1.0) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        if data.get("status") == "ok" or data.get("slots_idle", 0) > 0:
                            print(f"[Sidecar] Server is ready at {config.BASE_URL}")
                            return True
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionResetError):
                time.sleep(1.0)
                
        print("[Sidecar] Timeout waiting for server to respond.", file=sys.stderr)
        self.stop_sidecar_server()
        return False

    def stop_sidecar_server(self):
        """
        Terminates the background sidecar server.
        """
        if self._server_process is None:
            return
            
        print("[Sidecar] Stopping sidecar server...")
        try:
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=3.0)
                print("[Sidecar] Stopped gracefully.")
            except subprocess.TimeoutExpired:
                print("[Sidecar] Force killing server process...")
                self._server_process.kill()
                self._server_process.wait()
                print("[Sidecar] Force killed.")
        except Exception as e:
            print(f"[Sidecar] Error stopping sidecar: {e}", file=sys.stderr)
        finally:
            self._server_process = None

    def clean_json_response(self, raw_text: str) -> str:
        """
        Strips markdown wrappers and trims spaces.
        """
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
            
        if text.endswith("```"):
            text = text[:-3].strip()
            
        return text

    def extract_parameters(self, tool_name: str, query: str) -> dict:
        """
        Queries the sidecar server with grammar constraints to extract parameters.
        """
        if tool_name not in TOOL_REGISTRY:
            return {"success": False, "parameters": {}, "error": f"Tool '{tool_name}' unregistered."}

        tool_info = TOOL_REGISTRY[tool_name]
        schema = tool_info["json_schema"]
        validator = tool_info["validator"]

        # Bypassed if schema is empty
        if not schema:
            return {
                "success": True,
                "parameters": {},
                "raw_response": "",
                "error": None,
                "was_repaired": False
            }

        # Start server if not running
        if not self.start_sidecar_server():
            return {"success": False, "parameters": {}, "error": "Sidecar llama-server failed to launch."}

        json_schema_str = json.dumps(schema)
        prompt = EXTRACTION_PROMPT.format(
            tool_name=tool_name,
            tool_description=tool_info["description"],
            json_schema=json_schema_str,
            query=query
        )

        url = f"{config.BASE_URL}/completion"
        payload = {
            "prompt": prompt,
            "temperature": 0.0,
            "top_p": 1.0,
            "stream": False,
            "n_predict": 128,
            "stop": ["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"],
            "json_schema": schema
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20.0) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                raw_text = res_data.get("content", "").strip()
        except Exception as e:
            return {"success": False, "parameters": {}, "error": f"Completion request failed: {e}"}

        cleaned = self.clean_json_response(raw_text)
        parsed_json = None
        was_repaired = False

        # Try direct parse
        try:
            parsed_json = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback repair
            try:
                parsed_json = json_repair.loads(cleaned)
                if isinstance(parsed_json, dict):
                    was_repaired = True
            except Exception:
                pass

        # Regex fallback
        if parsed_json is None or not isinstance(parsed_json, dict):
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                try:
                    parsed_json = json.loads(match.group(0))
                    was_repaired = True
                except json.JSONDecodeError:
                    try:
                        parsed_json = json_repair.loads(match.group(0))
                        if isinstance(parsed_json, dict):
                            was_repaired = True
                    except Exception:
                        pass

        if parsed_json is None or not isinstance(parsed_json, dict):
            return {
                "success": False,
                "parameters": {},
                "raw_response": raw_text,
                "error": "Failed to parse model output into a valid JSON object."
            }

        # Pydantic validation
        try:
            validated = validator(**parsed_json)
            return {
                "success": True,
                "parameters": validated.model_dump(),
                "raw_response": raw_text,
                "error": None,
                "was_repaired": was_repaired
            }
        except Exception as e:
            return {
                "success": False,
                "parameters": parsed_json,
                "raw_response": raw_text,
                "error": f"Schema validation failed: {e}"
            }
