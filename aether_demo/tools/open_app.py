import os
import sys
import subprocess
from typing import Literal
from tools.base import BaseTool, BaseSchema
from extraction.regex_extractor import extract_app_name

class OpenAppSchema(BaseSchema):
    app_name: str

class OpenAppTool(BaseTool):
    name = "open_app"
    description = "Opens a specified desktop application (e.g. Chrome, Spotify, Terminal)."
    example_queries = ["open chrome", "launch spotify", "start terminal", "open notepad", "launch notepad"]
    schema_class = OpenAppSchema
    safety_level: Literal["auto", "confirm"] = "auto"

    def extract(self, query: str) -> dict:
        app_name = extract_app_name(query)
        if not app_name:
            # Ambiguity handling: Ask one clarifying question
            print("I couldn't identify the application name in your request.")
            app_name = input("Which application would you like to open? ").strip()
            if not app_name:
                raise ValueError("Application name is required.")
        return {"app_name": app_name}

    def execute(self, params: OpenAppSchema) -> str:
        app_name = params.app_name
        
        if sys.platform == "win32":
            aliases = {
                "chrome": "chrome.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "cmd": "cmd.exe",
                "terminal": "cmd.exe",
                "explorer": "explorer.exe",
                "spotify": "spotify.exe"
            }
            app_to_run = aliases.get(app_name.lower(), app_name)
            try:
                os.startfile(app_to_run)
            except FileNotFoundError:
                # Try running via cmd shell
                subprocess.Popen(f"start {app_to_run}", shell=True)
        elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
        else:  # Linux / other
            subprocess.Popen(["xdg-open", app_name])
            
        return f"Opened {app_name}."
