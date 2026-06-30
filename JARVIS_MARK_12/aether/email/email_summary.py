"""
email/email_summary.py

Service layer for the Email Summary Workflow. 
Bypasses the Action Planner and Executor, communicating directly with the email backend and the Planner LLM.
"""

import logging
import datetime
import re
import time
from typing import Dict, Any, List

import aether.config as config
from aether.email.email_manager import email_manager
from aether.email.exceptions import EmailNotConnectedError, EmailConnectionError
from aether.llm.model import generate_completion

logger = logging.getLogger(__name__)

class EmailSummaryService:
    """
    Service to retrieve, clean, and summarize emails for a given date filter.
    """
    
    @staticmethod
    def summarize(filters: Dict[str, Any]) -> str:
        """
        Retrieves emails for the filtered date, cleans their contents, 
        and queries the Planner LLM to generate a summary.
        """
        logger.info("Email Summary Started")
        start_time = time.perf_counter()
        
        # 1. Parse date filters
        date_type = filters.get("date_type", "today")
        date_str = filters.get("date")
        
        logger.info(f"Date Filter: {date_type} (value: {date_str})")
        
        MONTHS_SHORT = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        
        MONTH_NAMES = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        def to_imap_date(d: datetime.date) -> str:
            return f"{d.day:02d}-{MONTHS_SHORT[d.month]}-{d.year}"
            
        now = datetime.date.today()
        
        if date_type == "today":
            target_date = now
            date_label = "Today"
        elif date_type == "yesterday":
            target_date = now - datetime.timedelta(days=1)
            date_label = "Yesterday"
        elif date_type == "specific" and date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                date_label = f"{MONTH_NAMES[target_date.month]} {target_date.day}, {target_date.year}"
            except ValueError:
                logger.warning(f"Invalid specific date format: {date_str}. Defaulting to today.")
                target_date = now
                date_label = "Today"
        else:
            target_date = now
            date_label = "Today"
            
        imap_date_filter = f"ON {to_imap_date(target_date)}"
        
        # 2. Verify connection
        if not email_manager.is_connected():
            logger.error("Email Summary Failed: Email account is not connected")
            raise EmailNotConnectedError("Email account is not connected. Please connect your email in Settings.")
            
        # 3. Retrieve emails
        max_emails = getattr(config, "MAX_SUMMARIZED_EMAILS", 10)
        try:
            emails = email_manager.list_emails(limit=max_emails, date_filter=imap_date_filter)
        except EmailConnectionError as e:
            logger.exception("Email Summary Failed: IMAP connection error")
            raise RuntimeError("Unable to retrieve emails.") from e
        except Exception as e:
            logger.exception("Email Summary Failed: Unexpected error while retrieving emails")
            raise RuntimeError("Unable to retrieve emails.") from e
            
        total_count = getattr(emails, "total_count", len(emails))
        logger.info(f"Emails Retrieved: {len(emails)} (Total matching date: {total_count})")
        
        if not emails:
            logger.info("Email Summary: No emails found for date")
            raise ValueError("No emails were found for the selected date.")
            
        # 4. Read and clean email bodies
        emails_data = []
        for e in emails:
            try:
                details = email_manager.read_email(e.id)
                cleaned_body = clean_email_body(details.body)
                emails_data.append({
                    "sender": details.sender,
                    "subject": details.subject,
                    "date": details.date,
                    "body": cleaned_body
                })
            except Exception as ex:
                logger.warning(f"Failed to read email body for ID {e.id}: {ex}")
                # Append with empty body if read fails
                emails_data.append({
                    "sender": e.sender,
                    "subject": e.subject,
                    "date": e.date,
                    "body": "*(Could not retrieve email body)*"
                })
                
        logger.info(f"Emails Summarized: {len(emails_data)}")
        
        # 5. Build prompt
        prompt = build_summary_prompt(emails_data, date_label)
        logger.info(f"LLM Prompt Length: {len(prompt)} characters")
        
        # 6. Call LLM
        try:
            summary = generate_completion(
                prompt=prompt,
                json_schema=None,
                max_tokens=350,
                port=config.PLANNER_PORT,
                temperature=0.2,
                top_p=0.9
            )
        except Exception as e:
            logger.exception("Email Summary Failed: LLM generation error")
            raise RuntimeError("Unable to generate summary.") from e
            
        if not summary or not summary.strip():
            logger.error("Email Summary Failed: Empty response from LLM")
            raise RuntimeError("Unable to generate summary.")
            
        # Append total count info if there are more emails than MAX_SUMMARIZED_EMAILS
        if total_count > max_emails:
            extra_msg = f"\n\n*(Note: Showing summary for the latest {max_emails} of {total_count} emails received on this day.)*"
            summary += extra_msg
            
        execution_time = time.perf_counter() - start_time
        logger.info(f"Summary Generated Successfully in {execution_time:.2f}s")
        logger.info(f"Execution Time: {execution_time:.4f}s")
        
        return summary

def clean_email_body(text: str) -> str:
    """
    Cleans email body by removing HTML tags, reply chains, signatures, 
    excessive blank lines, and whitespace.
    """
    if not text:
        return ""
        
    # 1. Remove HTML tags if any residual exist
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 2. Remove reply chains
    reply_markers = [
        r'(?m)^On\s+.*\s+wrote:\s*$',
        r'(?m)^-+\s*Original Message\s*-+$',
        r'(?m)^_+\s*$',
        r'(?m)^From:\s+.*$',
        r'(?m)^Sent:\s+.*$',
        r'(?m)^To:\s+.*$',
    ]
    for marker in reply_markers:
        parts = re.split(marker, text, maxsplit=1)
        if parts:
            text = parts[0]
            
    # 3. Basic signature removal
    sig_markers = [
        r'(?m)^--\s*$',
        r'(?m)^Regards,\s*$',
        r'(?m)^Sincerely,\s*$',
        r'(?m)^Thanks,\s*$',
        r'(?m)^Best regards,\s*$',
    ]
    for marker in sig_markers:
        parts = re.split(marker, text, maxsplit=1)
        if parts:
            text = parts[0]
            
    # 4. Remove trailing/leading whitespace on each line, and remove excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    return text.strip()

def build_summary_prompt(emails_data: List[Dict[str, Any]], date_label: str) -> str:
    """
    Builds the system and user prompt for the Planner LLM.
    """
    max_words = getattr(config, "SUMMARY_MAX_WORDS", 250)
    
    prompt_lines = [
        "<|im_start|>system",
        "You are a helpful assistant that summarizes emails.",
        "Generate a summary of the provided emails in this exact format:",
        "",
        f"Email Summary — {date_label}",
        "",
        "• <SenderName1>",
        "<SubjectLine1>",
        "<One sentence summary of the email>",
        "",
        "• <SenderName2>",
        "<SubjectLine2>",
        "<One sentence summary of the email>",
        "",
        "Overall Summary",
        "",
        "<A brief paragraph summarizing the emails, e.g. 'You received X emails. Y require action.'>",
        "",
        "Action Items",
        "",
        "• <Action item 1>",
        "• <Action item 2>",
        "",
        f"Keep the entire response under {max_words} words. Do not include any extra introductory or concluding text outside of this format.",
        "<|im_end|>",
        "<|im_start|>user",
        "Here are the emails to summarize:"
    ]
    
    for i, email in enumerate(emails_data, 1):
        prompt_lines.extend([
            f"Email {i}",
            f"From:\n{email['sender']}",
            f"Subject:\n{email['subject']}",
            f"Body:\n{email['body']}",
            "----------------"
        ])
        
    prompt_lines.extend([
        "<|im_end|>",
        "<|im_start|>assistant",
        ""
    ])
    return "\n".join(prompt_lines)
