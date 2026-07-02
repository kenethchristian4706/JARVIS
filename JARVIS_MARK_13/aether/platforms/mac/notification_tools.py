"""
platform/mac/notification_tools.py

macOS implementation of NotificationAPI using AppleScript display notification.
"""

import subprocess
import logging
from aether.platforms.common.interfaces import NotificationAPI

logger = logging.getLogger(__name__)

class MacNotificationAPI(NotificationAPI):
    def send_notification(self, title: str, message: str) -> str:
        logger.info(f"Sending macOS notification - Title: {title}, Message: {message}")
        try:
            # Escape strings for AppleScript
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            subprocess.run(["osascript", "-e", script], check=True)
            return f"Notification '{title}' sent."
        except Exception as e:
            logger.warning(f"Could not send native macOS notification: {e}")
            return f"Notification logged: [{title}] {message}"
