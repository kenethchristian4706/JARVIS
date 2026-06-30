import unittest
from unittest.mock import patch, MagicMock
import imaplib
import smtplib

from aether.email.exceptions import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailNotConnectedError,
    EmailSendError
)
from aether.email.credential_store import (
    save_credentials,
    get_credentials,
    delete_credentials
)
from aether.email.smtp_client import (
    resolve_smtp_config,
    validate_smtp,
    send_smtp_email
)
from aether.email.imap_client import (
    resolve_imap_config,
    validate_imap,
    list_imap_emails,
    read_imap_email,
    html_to_text
)
from aether.email.email_manager import email_manager, EmailManager
from aether.tools.email_tools import send_email, list_emails, read_email

class TestEmailModule(unittest.TestCase):

    def setUp(self):
        # Clear singleton cache
        email_manager._email = None
        email_manager._password = None

    # --- Credential Store Tests ---
    @patch("keyring.set_password")
    @patch("keyring.get_password")
    def test_save_and_get_credentials(self, mock_get, mock_set):
        mock_get.side_effect = lambda s, u: "user@gmail.com" if s == "aether_email" else "app_password"
        
        save_credentials("user@gmail.com", "app_password")
        self.assertEqual(mock_set.call_count, 2)
        
        email, password = get_credentials()
        self.assertEqual(email, "user@gmail.com")
        self.assertEqual(password, "app_password")

    @patch("keyring.get_password")
    @patch("keyring.delete_password")
    def test_delete_credentials(self, mock_delete, mock_get):
        mock_get.side_effect = lambda s, u: "user@gmail.com" if s == "aether_email" else None
        delete_credentials()
        self.assertTrue(mock_delete.called)

    # --- SMTP Client Config and Validation Tests ---
    def test_resolve_smtp_config(self):
        self.assertEqual(resolve_smtp_config("user@gmail.com"), ("smtp.gmail.com", 465))
        self.assertEqual(resolve_smtp_config("user@outlook.com"), ("smtp.office365.com", 587))
        self.assertEqual(resolve_smtp_config("user@unknown.net"), ("smtp.unknown.net", 587))

    @patch("smtplib.SMTP_SSL")
    def test_validate_smtp_ssl_success(self, mock_smtp):
        instance = mock_smtp.return_value
        self.assertTrue(validate_smtp("user@gmail.com", "pass"))
        instance.login.assert_called_with("user@gmail.com", "pass")

    @patch("smtplib.SMTP")
    def test_validate_smtp_tls_success(self, mock_smtp):
        instance = mock_smtp.return_value
        self.assertTrue(validate_smtp("user@outlook.com", "pass"))
        instance.login.assert_called_with("user@outlook.com", "pass")

    @patch("smtplib.SMTP_SSL")
    def test_validate_smtp_auth_error(self, mock_smtp):
        mock_smtp.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        with self.assertRaises(EmailAuthenticationError):
            validate_smtp("user@gmail.com", "bad_pass")

    # --- IMAP Client Config and Validation Tests ---
    def test_resolve_imap_config(self):
        self.assertEqual(resolve_imap_config("user@gmail.com"), ("imap.gmail.com", 993))
        self.assertEqual(resolve_imap_config("user@outlook.com"), ("outlook.office365.com", 993))
        self.assertEqual(resolve_imap_config("user@unknown.net"), ("imap.unknown.net", 993))

    @patch("imaplib.IMAP4_SSL")
    def test_validate_imap_success(self, mock_imap):
        instance = mock_imap.return_value
        self.assertTrue(validate_imap("user@gmail.com", "pass"))
        instance.login.assert_called_with("user@gmail.com", "pass")

    @patch("imaplib.IMAP4_SSL")
    def test_validate_imap_auth_error(self, mock_imap):
        mock_imap.return_value.login.side_effect = imaplib.IMAP4.error("Login failed")
        with self.assertRaises(EmailAuthenticationError):
            validate_imap("user@gmail.com", "bad_pass")

    # --- HTML to Text Parser Tests ---
    def test_html_to_text(self):
        html = "<html><body><h1>Hello</h1><p>This is a <br/> test email.</p></body></html>"
        text = html_to_text(html)
        self.assertIn("Hello", text)
        self.assertIn("This is a", text)
        self.assertIn("test email.", text)
        self.assertNotIn("<html>", text)
        self.assertNotIn("<br/>", text)

    # --- EmailManager Singleton Tests ---
    def test_email_manager_singleton(self):
        manager1 = EmailManager()
        manager2 = EmailManager()
        self.assertIs(manager1, manager2)

    @patch("aether.email.email_manager.validate_smtp")
    @patch("aether.email.email_manager.validate_imap")
    @patch("aether.email.email_manager.save_credentials")
    def test_email_manager_connect(self, mock_save, mock_imap, mock_smtp):
        email_manager.connect("user@gmail.com", "password")
        self.assertTrue(email_manager.is_connected())
        self.assertEqual(email_manager.get_email_address(), "user@gmail.com")
        mock_smtp.assert_called_once()
        mock_imap.assert_called_once()
        mock_save.assert_called_once()

    # --- AI Tools (Tools Interface) Disconnected State Tests ---
    def test_tools_disconnected_error(self):
        # Tools should immediately return EMAIL_NOT_CONNECTED error if account not connected
        res_send = send_email("recipient@test.com", "subject", "body")
        res_list = list_emails()
        res_read = read_email("latest")

        for res in (res_send, res_list, res_read):
            self.assertFalse(res["success"])
            self.assertEqual(res["error"], "EMAIL_NOT_CONNECTED")
            self.assertTrue(res["requires_login"])

    # --- Tool Execution Success Paths with Mock Session ---
    @patch("aether.email.email_manager.validate_smtp")
    @patch("aether.email.email_manager.validate_imap")
    @patch("aether.email.email_manager.save_credentials")
    @patch("aether.email.email_manager.send_smtp_email")
    def test_tool_send_email_flow(self, mock_send_smtp, mock_save, mock_imap, mock_smtp):
        email_manager.connect("user@gmail.com", "password")
        
        # Test confirmation requirement
        res_preview = send_email("recipient@test.com", "Hello Subject", "Hello Body", confirmed=False)
        self.assertFalse(res_preview["success"])
        self.assertTrue(res_preview["requires_confirmation"])
        self.assertEqual(res_preview["data"]["recipient"], "recipient@test.com")
        
        # Test send when confirmed
        res_sent = send_email("recipient@test.com", "Hello Subject", "Hello Body", confirmed=True)
        self.assertTrue(res_sent["success"])
        mock_send_smtp.assert_called_once()

    @patch("aether.email.email_manager.validate_smtp")
    @patch("aether.email.email_manager.validate_imap")
    @patch("aether.email.email_manager.save_credentials")
    @patch("aether.email.email_manager.get_imap_client")
    @patch("aether.email.email_manager.list_imap_emails")
    def test_tool_list_emails_flow(self, mock_list, mock_get_imap, mock_save, mock_imap, mock_smtp):
        email_manager.connect("user@gmail.com", "password")
        mock_list.return_value = []
        
        res = list_emails(limit=5)
        self.assertTrue(res["success"])
        self.assertIn("emails", res["data"])
        mock_list.assert_called_once()

    @patch("aether.email.email_manager.validate_smtp")
    @patch("aether.email.email_manager.validate_imap")
    @patch("aether.email.email_manager.save_credentials")
    @patch("aether.email.email_manager.get_imap_client")
    @patch("aether.email.email_manager.read_imap_email")
    def test_tool_read_email_flow(self, mock_read, mock_get_imap, mock_save, mock_imap, mock_smtp):
        email_manager.connect("user@gmail.com", "password")
        
        # Mock EmailDetails return value
        class DummyDetails:
            id = "123"
            sender = "from@test.com"
            recipients = ["user@gmail.com"]
            subject = "Hello"
            date = "Today"
            body = "Body Content"
            attachments = []
        mock_read.return_value = DummyDetails()
        
        res = read_email("123")
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["id"], "123")
        self.assertEqual(res["data"]["body"], "Body Content")
        mock_read.assert_called_once()

if __name__ == "__main__":
    unittest.main()
