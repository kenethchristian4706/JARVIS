import sys
import os
import subprocess
from typing import Literal
from tools.base import BaseTool, BaseSchema
from extraction.regex_extractor import extract_volume_level

class SetVolumeSchema(BaseSchema):
    level: int

class SetVolumeTool(BaseTool):
    name = "set_volume"
    description = "Sets the system audio volume (0-100)."
    example_queries = ["set volume to 50", "turn volume up to 80", "mute the sound"]
    schema_class = SetVolumeSchema
    safety_level: Literal["auto", "confirm"] = "auto"

    def extract(self, query: str) -> dict:
        level = extract_volume_level(query)
        if level is None:
            # Ambiguity handling: Ask one clarifying question
            print("I could not identify the target volume level in your request.")
            level_str = input("Please specify a volume level (0-100): ").strip()
            try:
                level = int(level_str)
                level = max(0, min(100, level))
            except ValueError:
                raise ValueError("Volume level must be an integer between 0 and 100.")
        return {"level": level}

    def execute(self, params: SetVolumeSchema) -> str:
        level = params.level
        
        if sys.platform == "win32":
            try:
                # Dynamically import comtypes and pycaw to avoid import crash if not installed
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                # Set volume scalar (0.0 to 1.0)
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            except Exception as e:
                print(f"Warning: Could not adjust Windows system volume. Please install 'pycaw' and 'comtypes'. (Error: {e})")
                return f"Volume set to {level}% (Simulated - pycaw not configured)."
        elif sys.platform == "darwin":  # macOS
            try:
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
            except Exception as e:
                return f"Error setting macOS volume: {e}"
        else:  # Linux
            try:
                subprocess.run(["amixer", "sset", "Master", f"{level}%"], check=True)
            except Exception as e:
                return f"Error setting Linux volume: {e}"
                
        return f"Volume set to {level}%."
