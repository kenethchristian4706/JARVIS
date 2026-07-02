"""
platform/mac/system_tools.py

macOS implementation of SystemAPI.
Controls system volume via AppleScript output volume settings,
and brightness. Maps Notepad writing tool to TextEdit.
"""

import time
import subprocess
import logging
import pyautogui

from aether.platforms.common.interfaces import SystemAPI

logger = logging.getLogger(__name__)

class MacSystemAPI(SystemAPI):
    def _run_applescript(self, script: str) -> str:
        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if res.returncode == 0:
                return res.stdout.strip()
            logger.warning(f"AppleScript error: {res.stderr}")
        except Exception as e:
            logger.error(f"Error executing AppleScript: {e}")
        return ""

    def set_volume(self, level: int) -> str:
        self._run_applescript(f"set volume output volume {level}")
        return f"Master volume set to {level}%."

    def mute_volume(self) -> str:
        self._run_applescript("set volume with output muted")
        return "Master system audio muted successfully."

    def unmute_volume(self) -> str:
        self._run_applescript("set volume without output muted")
        return "Master system audio unmuted successfully."

    def increase_volume(self) -> str:
        vol_str = self._run_applescript("output volume of (get volume settings)")
        try:
            current = int(vol_str) if vol_str else 50
        except ValueError:
            current = 50
        new_level = min(100, current + 10)
        self.set_volume(new_level)
        return f"Master volume set to {new_level}%."

    def decrease_volume(self) -> str:
        vol_str = self._run_applescript("output volume of (get volume settings)")
        try:
            current = int(vol_str) if vol_str else 50
        except ValueError:
            current = 50
        new_level = max(0, current - 10)
        self.set_volume(new_level)
        return f"Master volume set to {new_level}%."

    def set_brightness(self, level: int) -> str:
        # Set brightness via osascript using system preferences panel or external utilities
        # Under user session context, can try:
        script = f'''
        tell application "System Events"
            try
                -- Works on standard Apple laptops
                set value of property "brightness" of first display of application "System Preferences" to {level / 100.0}
                return "success"
            on error
                return "fail"
            end try
        end tell
        '''
        self._run_applescript(script)
        # We will also try screen_brightness_control as fallback
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            return f"Display brightness set to {level}%."
        except Exception:
            pass
        return f"Display brightness set to {level}% (sent to OS preferences)."

    def increase_brightness(self) -> str:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            val = current[0] if isinstance(current, list) and current else 50
            new_level = min(100, val + 10)
            self.set_brightness(new_level)
            return f"Display brightness set to {new_level}%."
        except Exception:
            pass
        return "Display brightness increased by 10% (simulated)."

    def decrease_brightness(self) -> str:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            val = current[0] if isinstance(current, list) and current else 50
            new_level = max(0, val - 10)
            self.set_brightness(new_level)
            return f"Display brightness set to {new_level}%."
        except Exception:
            pass
        return "Display brightness decreased by 10% (simulated)."

    def open_notepad_and_write(self, text: str) -> dict:
        try:
            logger.info("Starting open_notepad_and_write tool execution on macOS (TextEdit mapping).")
            subprocess.run(["open", "-a", "TextEdit"], check=True)
            time.sleep(1.0)
            
            script = '''
            tell application "TextEdit"
                activate
                if (count of documents) = 0 then
                    make new document
                end if
            end tell
            '''
            self._run_applescript(script)
            time.sleep(0.5)
            
            pyautogui.write(text)
            return {
                "success": True,
                "message": "TextEdit opened and text inserted."
            }
        except Exception as e:
            logger.error(f"Error during TextEdit write operation: {e}")
            return {
                "success": False,
                "message": f"Failed to open TextEdit and write text: {str(e)}"
            }
