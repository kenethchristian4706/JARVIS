"""
platform/mac/window_manager.py

macOS implementation of WindowAPI.
Utilizes AppleScript / System Events to list, focus, close, resize, and move application windows.
"""

import subprocess
import logging
from typing import List

from aether.platforms.common.interfaces import WindowAPI

logger = logging.getLogger(__name__)

class MacWindowAPI(WindowAPI):
    def _run_applescript(self, script: str) -> str:
        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if res.returncode == 0:
                return res.stdout.strip()
            logger.warning(f"AppleScript error: {res.stderr}")
        except Exception as e:
            logger.error(f"Error executing AppleScript: {e}")
        return ""

    def move_window(self, title: str, x: int, y: int) -> str:
        script = f'''
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                repeat with win in (every window of proc)
                    if name of win contains "{title}" then
                        set position of win to {{{x}, {y}}}
                        return "success"
                    end if
                end repeat
            end repeat
        end tell
        '''
        res = self._run_applescript(script)
        if "success" in res:
            return f"Moved window matching '{title}' to ({x}, {y})."
        return f"Could not find or move window matching '{title}'."

    def resize_window(self, title: str, width: int, height: int) -> str:
        script = f'''
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                repeat with win in (every window of proc)
                    if name of win contains "{title}" then
                        set size of win to {{{width}, {height}}}
                        return "success"
                    end if
                end repeat
            end repeat
        end tell
        '''
        res = self._run_applescript(script)
        if "success" in res:
            return f"Resized window matching '{title}' to {width}x{height}."
        return f"Could not find or resize window matching '{title}'."

    def focus_window(self, title: str) -> str:
        script = f'''
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                repeat with win in (every window of proc)
                    if name of win contains "{title}" then
                        set frontmost of proc to true
                        perform action "AXRaise" of win
                        return "success"
                    end if
                end repeat
            end repeat
        end tell
        '''
        res = self._run_applescript(script)
        if "success" in res:
            return f"Focused window matching '{title}'."
        return f"Could not find or focus window matching '{title}'."

    def close_window(self, title: str) -> str:
        script = f'''
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                repeat with win in (every window of proc)
                    if name of win contains "{title}" then
                        close win
                        return "success"
                    end if
                end repeat
            end repeat
        end tell
        '''
        res = self._run_applescript(script)
        if "success" in res:
            return f"Closed window matching '{title}'."
        return f"Could not find or close window matching '{title}'."

    def list_windows(self) -> List[str]:
        script = '''
        tell application "System Events"
            set winNames to {}
            repeat with proc in (every process whose visible is true)
                repeat with win in (every window of proc)
                    copy name of win to end of winNames
                end repeat
            end repeat
            return winNames
        end tell
        '''
        res = self._run_applescript(script)
        if res:
            # Parse AppleScript list output format (e.g. "Title 1, Title 2")
            return [t.strip() for t in res.split(", ") if t.strip()]
        return []

    def get_active_window(self) -> str:
        script = '''
        tell application "System Events"
            try
                set frontProc to first process whose frontmost is true
                if (count of windows of frontProc) > 0 then
                    return name of front window of frontProc
                else
                    return name of frontProc
                end if
            on error
                return ""
            end try
        end tell
        '''
        return self._run_applescript(script)
