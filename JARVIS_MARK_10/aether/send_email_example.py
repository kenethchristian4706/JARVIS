"""
send_email_example.py

Demonstration script showing the usage of the send_email tool in Aether.
Shows both the confirmation-request response and a mock sending run.
"""

import os
from unittest.mock import patch
from aether.tools.email_tools import send_email

def main():
    print("==================================================")
    print("        Aether: send_email Tool Example Usage     ")
    print("==================================================")

    recipient = "john@example.com"
    subject = "Status Update"
    body = "Hi John,\n\nI am writing to let you know that the project is on track.\n\nBest,\nAssistant"

    # We mock the SMTP server and environment variables so this script can run out-of-the-box
    # without needing actual Gmail credentials configured.
    with patch.dict(os.environ, {
        "EMAIL_ADDRESS": "mock_sender@gmail.com",
        "EMAIL_PASSWORD": "mock_app_password_1234",
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587"
    }):
        print("\n--- 1. Calling send_email with confirmed=False (Default) ---")
        response_no_confirm = send_email(recipient=recipient, subject=subject, body=body, confirmed=False)
        print("Response JSON:")
        import json
        print(json.dumps(response_no_confirm, indent=4))

        print("\n--- 2. Calling send_email with confirmed=True (Mocking SMTP send) ---")
        with patch("smtplib.SMTP") as mock_smtp_class:
            # Configure mocked SMTP to succeed
            from unittest.mock import MagicMock
            mock_smtp_instance = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
            
            response_confirm = send_email(
                recipient=recipient,
                subject=subject,
                body=body,
                confirmed=True
            )
            print("Response JSON:")
            print(json.dumps(response_confirm, indent=4))


if __name__ == "__main__":
    main()
