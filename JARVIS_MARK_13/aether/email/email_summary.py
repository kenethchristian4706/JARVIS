import re
import time
import logging
import datetime
from typing import Dict, Any, List

import aether.config as config
from aether.email.email_manager import email_manager
from aether.email.exceptions import EmailNotConnectedError, EmailConnectionError
from aether.llm.model import generate_completion

logger = logging.getLogger(__name__)

def clean_email_body(text: str) -> str:
    """
    Cleans the email body by removing HTML, reply chains, signatures,
    excessive blank lines, and leading/trailing whitespace.
    """
    if not text:
        return ""
    
    # 1. Remove HTML tags if any remain
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 1.5. Replace URLs with [URL] to save tokens and avoid LLM confusion
    text = re.sub(r'https?://\S+', '[URL]', text)
    
    # 2. Split into lines and filter out reply chains and signatures
    reply_markers = [
        r'^-+\s*Original Message\s*-+',
        r'^On\s+.*\s+wrote:',
        r'^From:\s+',
        r'^To:\s+',
        r'^Sent:\s+',
        r'^Subject:\s+',
        r'^wrote:\s*$',
        r'^Sent from my'
    ]
    sig_markers = [
        r'^--\s*$',
        r'^best regards,?\s*$',
        r'^regards,?\s*$',
        r'^sincerely,?\s*$',
        r'^thanks,?\s*$',
        r'^thank you,?\s*$'
    ]
    
    cleaned_lines = []
    for line in text.splitlines():
        line_stripped = line.strip()
        # If we hit a reply chain or signature marker, truncate the body
        if any(re.match(marker, line_stripped, re.IGNORECASE) for marker in reply_markers + sig_markers):
            break
        # Skip quoted lines in reply chains
        if line_stripped.startswith('>'):
            continue
        cleaned_lines.append(line)
        
    text = "\n".join(cleaned_lines)
    
    # 3. Normalize spacing: replace multiple spaces with a single space, multiple newlines with at most double newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def build_summary_prompt(emails: List[Dict[str, Any]]) -> str:
    """
    Generates the prompt for the Planner LLM to summarize the emails.
    """
    prompt = (
        "<|im_start|>system\n"
        "You are the Email Summarizer for Aether, an offline AI desktop assistant.\n"
        "Analyze the provided emails and generate a concise summary and action items.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        "Summarize these emails.\n\n"
        "For each email provide:\n"
        "• Sender\n"
        "• Subject\n"
        "• One sentence summary\n\n"
        "Then provide:\n"
        "Overall Summary\n"
        "Action Items (Grouped by priority: prefix urgent tasks like due bills, deadlines, or important requests with [High Priority], and other tasks with [Standard Priority])\n\n"
        f"Keep response under {config.SUMMARY_MAX_WORDS} words.\n\n"
    )
    
    for i, email in enumerate(emails, 1):
        prompt += f"Email {i}\n\n"
        prompt += f"From:\n{email['sender']}\n\n"
        prompt += f"Subject:\n{email['subject']}\n\n"
        prompt += f"Body:\n{email['body']}\n\n"
        if i < len(emails):
            prompt += "----------------\n\n"
            
    prompt += "<|im_end|>\n<|im_start|>assistant\n"
    return prompt

class EmailSummaryService:
    @classmethod
    def summarize(cls, filters: Dict[str, Any]) -> str:
        """
        Retrieves, cleans, and generates a summary for emails based on the provided filters.
        """
        start_time = time.perf_counter()
        logger.info("Email Summary Started")
        
        # 1. Check if email is connected
        if not email_manager.is_connected():
            logger.warning("Email Summary Failed: Email not connected")
            raise EmailNotConnectedError("No email account is connected.")
        
        # Log Date Filter
        date_filter_val = filters.get("date_type", "unknown")
        if date_filter_val == "specific":
            date_filter_val = f"specific ({filters.get('date', 'unknown')})"
        logger.info(f"Date Filter: {date_filter_val}")
        
        # 2. Retrieve emails matching the filters (using a high limit to find total count)
        try:
            summaries = email_manager.list_emails(limit=100, filters=filters)
        except Exception as e:
            logger.error(f"Email Summary Failed: IMAP retrieval error: {e}")
            raise EmailConnectionError("Unable to retrieve emails.")
            
        total_count = len(summaries)
        logger.info(f"Emails Retrieved: {total_count}")
        
        # 3. Handle no emails found
        if total_count == 0:
            logger.info("Email Summary Completed: No emails found")
            raise ValueError("No emails were found for the selected date.")
            
        # 4. Limit to newest 10 (config.MAX_SUMMARIZED_EMAILS)
        newest_summaries = summaries[:config.MAX_SUMMARIZED_EMAILS]
        logger.info(f"Emails Summarized: {len(newest_summaries)}")
        
        num_emails = len(newest_summaries)
        # Calculate dynamic max body length to fit within 2048 token context and avoid CPU timeouts
        max_body_len = max(200, 1500 // num_emails)
        
        # 5. Read full email details and clean bodies
        emails_to_summarize = []
        for s in newest_summaries:
            try:
                details = email_manager.read_email(email_id=s.id)
                cleaned_body = clean_email_body(details.body)
                if len(cleaned_body) > max_body_len:
                    cleaned_body = cleaned_body[:max_body_len] + "... [truncated]"
                emails_to_summarize.append({
                    "sender": details.sender,
                    "subject": details.subject,
                    "date": details.date,
                    "body": cleaned_body
                })
            except Exception as e:
                logger.warning(f"Error reading email details for UID {s.id}: {e}")
                
        # If we failed to retrieve details for any email, make sure we still have something
        if not emails_to_summarize:
            raise EmailConnectionError("Unable to retrieve emails.")
            
        # 6. Build the LLM prompt
        prompt = build_summary_prompt(emails_to_summarize)
        logger.info(f"LLM Prompt Length: {len(prompt)}")
        
        # 7. Query the Planner LLM
        try:
            llm_summary = generate_completion(
                prompt=prompt,
                max_tokens=500,  # Increased from 300 to 500 to prevent cut-offs
                port=config.PLANNER_PORT,
                temperature=0.2,
                top_p=0.9
            )
        except Exception as e:
            logger.error(f"Email Summary Failed: LLM generation error: {e}")
            raise RuntimeError("Unable to generate summary.")
            
        if not llm_summary:
            logger.error("Email Summary Failed: LLM returned empty response")
            raise RuntimeError("Unable to generate summary.")
            
        # 8. Prepend the header
        date_type = filters.get("date_type", "today")
        if date_type == "today":
            header = "Email Summary — Today"
        elif date_type == "yesterday":
            header = "Email Summary — Yesterday"
        elif date_type == "specific" and "date" in filters:
            try:
                dt = datetime.datetime.strptime(filters["date"], "%Y-%m-%d")
                formatted_date = dt.strftime("%B %d, %Y")
                header = f"Email Summary — {formatted_date}"
            except Exception:
                header = f"Email Summary — {filters['date']}"
        else:
            header = "Email Summary"
            
        final_output = f"{header}\n\n{llm_summary}"
        
        logger.info("Summary Generated Successfully")
        execution_time = time.perf_counter() - start_time
        logger.info(f"Execution Time: {execution_time:.4f}s")
        
        return final_output
