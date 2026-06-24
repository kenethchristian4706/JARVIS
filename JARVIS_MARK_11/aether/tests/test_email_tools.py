"""
tests/test_email_tools.py

Unit tests for Aether's send_email tool using pytest and unittest.mock.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import smtplib

# Add project root to python path to resolve aether packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aether.tools.email_tools import send_email

@pytest.fixture
def mock_env():
    """Fixture to inject required environment variables for SMTP configuration."""
    with patch.dict("os.environ", {
        "EMAIL_ADDRESS": "test_sender@example.com",
        "EMAIL_PASSWORD": "mock_app_password",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587"
    }):
        yield

def test_send_email_requires_confirmation(mock_env):
    """Test that send_email returns a confirmation preview when confirmed=False."""
    result = send_email(
        recipient="recipient@example.com",
        subject="Meeting Minutes",
        body="Here are the notes.",
        confirmed=False
    )
    
    assert result["success"] is False
    assert result.get("requires_confirmation") is True
    assert "You're about to send an email." in result["message"]
    assert result["data"]["recipient"] == "recipient@example.com"
    assert result["data"]["subject"] == "Meeting Minutes"
    assert result["data"]["body"] == "Here are the notes."

@patch("smtplib.SMTP")
def test_send_email_success(mock_smtp_class, mock_env):
    """Test that send_email successfully connects, authenticates, and dispatches the email when confirmed=True."""
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    result = send_email(
        recipient="recipient@example.com",
        subject="Meeting Minutes",
        body="Here are the notes.",
        confirmed=True
    )
    
    assert result["success"] is True
    assert "Email sent successfully to recipient@example.com" in result["message"]
    
    # Assert connection details
    mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
    
    # Assert flow: ehlo, starttls, ehlo, login, send_message
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("test_sender@example.com", "mock_app_password")
    mock_smtp_instance.send_message.assert_called_once()

def test_send_email_missing_credentials():
    """Test that send_email returns an authentication error when credentials are not configured in env."""
    with patch.dict("os.environ", {}, clear=True):
        result = send_email(
            recipient="recipient@example.com",
            subject="Test",
            body="Test body",
            confirmed=True
        )
        assert result["success"] is False
        assert "Invalid email credentials." in result["message"]

@patch("smtplib.SMTP")
def test_send_email_auth_failure(mock_smtp_class, mock_env):
    """Test that send_email returns specific error when SMTP login fails."""
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    result = send_email(
        recipient="recipient@example.com",
        subject="Test",
        body="Test body",
        confirmed=True
    )
    
    assert result["success"] is False
    assert "Invalid email credentials." in result["message"]

@patch("smtplib.SMTP")
@pytest.mark.parametrize("exception_type", [
    smtplib.SMTPConnectError(500, "Connect error"),
    TimeoutError("Connection timed out"),
    ConnectionError("Connection refused")
])
def test_send_email_connection_failures(mock_smtp_class, exception_type, mock_env):
    """Test that send_email returns a connection error when connecting to SMTP server fails."""
    mock_smtp_class.return_value.__enter__.side_effect = exception_type
    
    result = send_email(
        recipient="recipient@example.com",
        subject="Test",
        body="Test body",
        confirmed=True
    )
    
    assert result["success"] is False
    assert "Unable to connect to email server." in result["message"]

@patch("smtplib.SMTP")
def test_send_email_generic_exception(mock_smtp_class, mock_env):
    """Test that send_email catches unexpected exceptions and returns generic error message."""
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.send_message.side_effect = RuntimeError("Something went wrong")
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    result = send_email(
        recipient="recipient@example.com",
        subject="Test",
        body="Test body",
        confirmed=True
    )
    
    assert result["success"] is False
    assert "Failed to send email" in result["message"]
    assert "Something went wrong" in result["message"]
