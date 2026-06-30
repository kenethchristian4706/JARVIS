import unittest
from unittest.mock import patch, MagicMock
import datetime

from aether.email.exceptions import EmailNotConnectedError
from aether.email.email_summary import EmailSummaryService, clean_email_body, build_summary_prompt
from aether.email.email_manager import email_manager

class TestEmailSummary(unittest.TestCase):

    def test_clean_email_body_html(self):
        html_body = "<html><body><p>Hello World</p></body></html>"
        cleaned = clean_email_body(html_body)
        self.assertEqual(cleaned, "Hello World")

    def test_clean_email_body_reply_chain(self):
        body = "This is the actual message.\n\nOn Tue, Jun 30, 2026 at 11:00 AM User wrote:\n> Hello back!"
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "This is the actual message.")

    def test_clean_email_body_signature(self):
        body = "Here is the report details.\n\nBest regards,\nJohn Doe\nManager"
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "Here is the report details.")

    def test_clean_email_body_excessive_whitespace(self):
        body = "   Hello    \n\n\n\nWorld   "
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "Hello\n\nWorld")

    @patch("aether.email.email_summary.generate_completion")
    @patch("aether.email.email_manager.email_manager.read_email")
    @patch("aether.email.email_manager.email_manager.list_emails")
    @patch("aether.email.email_manager.email_manager.is_connected")
    def test_summarize_today_success(self, mock_is_connected, mock_list_emails, mock_read_email, mock_generate):
        mock_is_connected.return_value = True
        
        # Mock email list
        class DummySummary:
            def __init__(self, uid, sender, subject, date):
                self.id = uid
                self.sender = sender
                self.subject = subject
                self.date = date
                self.unread = True
                self.has_attachments = False
                
        mock_emails = [
            DummySummary("1", "Alice", "Meeting Update", "Today"),
            DummySummary("2", "Bob", "Project Status", "Today")
        ]
        # Attach total_count
        from aether.email.imap_client import EmailList
        mock_list_emails.return_value = EmailList(mock_emails, 2)
        
        # Mock read_email
        class DummyDetails:
            def __init__(self, uid, sender, subject, body):
                self.id = uid
                self.sender = sender
                self.recipients = ["me@test.com"]
                self.subject = subject
                self.date = "Today"
                self.body = body
                self.attachments = []
                
        mock_read_email.side_effect = lambda uid: {
            "1": DummyDetails("1", "Alice", "Meeting Update", "We need to reschedule the sync."),
            "2": DummyDetails("2", "Bob", "Project Status", "Everything is green.\n\nBest regards,\nBob")
        }[uid]
        
        mock_generate.return_value = "Email Summary — Today\n• Alice\nRescheduling sync.\n• Bob\nEverything is green."
        
        # Call summarize
        filters = {"date_type": "today"}
        summary = EmailSummaryService.summarize(filters)
        
        self.assertIn("Email Summary — Today", summary)
        self.assertIn("Alice", summary)
        self.assertIn("Bob", summary)
        
        mock_list_emails.assert_called_once()
        self.assertEqual(mock_read_email.call_count, 2)
        mock_generate.assert_called_once()

    @patch("aether.email.email_manager.email_manager.is_connected")
    def test_summarize_not_connected(self, mock_is_connected):
        mock_is_connected.return_value = False
        with self.assertRaises(EmailNotConnectedError):
            EmailSummaryService.summarize({"date_type": "today"})

    @patch("aether.email.email_manager.email_manager.list_emails")
    @patch("aether.email.email_manager.email_manager.is_connected")
    def test_summarize_no_emails_found(self, mock_is_connected, mock_list_emails):
        mock_is_connected.return_value = True
        mock_list_emails.return_value = []
        
        with self.assertRaises(ValueError) as ctx:
            EmailSummaryService.summarize({"date_type": "today"})
        self.assertEqual(str(ctx.exception), "No emails were found for the selected date.")

if __name__ == "__main__":
    unittest.main()
