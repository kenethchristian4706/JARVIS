"""
platform/windows/notification_tools.py

Windows implementation of NotificationAPI.
"""

import logging
from aether.platforms.common.interfaces import NotificationAPI

logger = logging.getLogger(__name__)

class WindowsNotificationAPI(NotificationAPI):
    def send_notification(self, title: str, message: str) -> str:
        logger.info(f"Sending Windows notification - Title: {title}, Message: {message}")
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Aether"
            )
            return f"Notification '{title}' sent."
        except Exception as e:
            logger.warning(f"Could not send native notification: {e}")
            return f"Notification logged: [{title}] {message}"
