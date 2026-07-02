"""
platform/windows/power_tools.py

Windows implementation of PowerAPI.
"""

import os
import logging
from aether.platforms.common.interfaces import PowerAPI

logger = logging.getLogger(__name__)

class WindowsPowerAPI(PowerAPI):
    def shutdown_pc(self) -> str:
        logger.info("Triggering Windows shutdown.")
        os.system("shutdown /s /t 1")
        return "Shutdown command triggered successfully."

    def restart_pc(self) -> str:
        logger.info("Triggering Windows restart.")
        os.system("shutdown /r /t 1")
        return "Restart command triggered successfully."

    def sleep_pc(self) -> str:
        logger.info("Triggering Windows sleep.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "System put to sleep successfully."

    def lock_pc(self) -> str:
        logger.info("Triggering Windows session lock.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "System session locked successfully."
