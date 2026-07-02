"""
platform/mac/power_tools.py

macOS implementation of PowerAPI using AppleScript System Events and shell commands.
"""

import subprocess
import logging
from aether.platforms.common.interfaces import PowerAPI

logger = logging.getLogger(__name__)

class MacPowerAPI(PowerAPI):
    def _run_applescript(self, script: str) -> None:
        try:
            subprocess.run(["osascript", "-e", script], check=True)
        except Exception as e:
            logger.error(f"Failed to execute power state AppleScript: {e}")

    def shutdown_pc(self) -> str:
        logger.info("Triggering macOS shutdown.")
        self._run_applescript('tell application "System Events" to shut down')
        return "Shutdown command triggered successfully."

    def restart_pc(self) -> str:
        logger.info("Triggering macOS restart.")
        self._run_applescript('tell application "System Events" to restart')
        return "Restart command triggered successfully."

    def sleep_pc(self) -> str:
        logger.info("Triggering macOS sleep.")
        self._run_applescript('tell application "System Events" to sleep')
        return "System put to sleep successfully."

    def lock_pc(self) -> str:
        logger.info("Triggering macOS screen lock.")
        # pmset displaysleepnow locks screen if passcode lock-on-sleep is enabled (standard Mac setting)
        try:
            subprocess.run(["pmset", "displaysleepnow"], check=True)
            return "System session locked successfully."
        except Exception:
            # Fallback to starting screensaver
            self._run_applescript('tell application "System Events" to start current screen saver')
            return "System session locked successfully (started screensaver)."
