import imaplib
import email
import email.header
import re
import logging
from typing import List, Tuple, Dict, Any, Union, Optional

from aether.email.exceptions import EmailAuthenticationError, EmailConnectionError
from aether.email.models import EmailSummary, EmailDetails

logger = logging.getLogger(__name__)

def resolve_imap_config(email_addr: str) -> Tuple[str, int]:
    """Auto-detect IMAP host and port based on email domain."""
    domain = email_addr.split("@")[-1].lower().strip()
    if domain in ("gmail.com", "googlemail.com"):
        return "imap.gmail.com", 993
    elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com", "office365.com"):
        return "outlook.office365.com", 993
    elif domain in ("yahoo.com", "ymail.com"):
        return "imap.mail.yahoo.com", 993
    elif domain in ("icloud.com", "me.com", "mac.com"):
        return "imap.mail.me.com", 993
    else:
        return f"imap.{domain}", 993

def decode_header_val(header_val) -> str:
    """Decode RFC 2047 MIME encoded headers."""
    if not header_val:
        return ""
    try:
        decoded_parts = email.header.decode_header(header_val)
        parts = []
        for text, encoding in decoded_parts:
            if isinstance(text, bytes):
                parts.append(text.decode(encoding or 'utf-8', errors='ignore'))
            else:
                parts.append(text)
        return "".join(parts)
    except Exception:
        return str(header_val)

def html_to_text(html_content: str) -> str:
    """Convert HTML text to plain text using regex to strip tags and format lines."""
    if not html_content:
        return ""
    # Remove script and style elements
    text = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', ' ', html_content, flags=re.IGNORECASE)
    # Replace common block elements with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?(p|div|h[1-6]|li|tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace HTML entities
    entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&ndash;': '-', '&mdash;': '-'
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    # Normalize spacing
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def extract_body_and_attachments(msg) -> Tuple[str, List[str]]:
    """Extract plain text body (or converted HTML body) and attachment filenames."""
    plain_text = None
    html_text = None
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()
            
            if filename or "attachment" in content_disposition:
                if filename:
                    attachments.append(decode_header_val(filename))
                continue
                
            content_type = part.get_content_type()
            if content_type == "text/plain" and plain_text is None:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    plain_text = payload.decode(charset, errors='ignore')
                except Exception:
                    pass
            elif content_type == "text/html" and html_text is None:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_text = payload.decode(charset, errors='ignore')
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            body_str = payload.decode(charset, errors='ignore')
            if content_type == "text/html":
                html_text = body_str
            else:
                plain_text = body_str
        except Exception:
            pass

    body = ""
    if plain_text:
        body = plain_text
    elif html_text:
        body = html_to_text(html_text)
        
    return body.strip(), attachments

def validate_imap(email_addr: str, password: str) -> bool:
    """Validate credentials against the IMAP server without saving them."""
    host, port = resolve_imap_config(email_addr)
    logger.info(f"Validating IMAP connection to {host}:{port} for {email_addr}")
    try:
        mail = imaplib.IMAP4_SSL(host, port, timeout=10)
        with mail:
            mail.login(email_addr, password)
        logger.info("IMAP validation succeeded.")
        return True
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP Auth failed: {e}")
        raise EmailAuthenticationError(f"IMAP authentication failed: {e}")
    except Exception as e:
        logger.error(f"IMAP Connection failed: {e}")
        raise EmailConnectionError(f"Failed to connect or log in to IMAP server {host}:{port}: {e}")

def get_imap_client(email_addr: str, password: str) -> imaplib.IMAP4_SSL:
    """Connect and log in to the IMAP server, returning the authenticated instance."""
    host, port = resolve_imap_config(email_addr)
    try:
        mail = imaplib.IMAP4_SSL(host, port, timeout=15)
        mail.login(email_addr, password)
        return mail
    except imaplib.IMAP4.error as e:
        raise EmailAuthenticationError(f"IMAP authentication failed: {e}")
    except Exception as e:
        raise EmailConnectionError(f"Failed to connect to IMAP server {host}:{port}: {e}")

def list_imap_emails(
    mail: imaplib.IMAP4_SSL, 
    limit: int = 10, 
    unread_only: bool = False,
    filters: Optional[Dict[str, Any]] = None
) -> List[EmailSummary]:
    """Retrieve summaries of recent emails (newest first)."""
    import datetime
    mail.select("INBOX", readonly=True)
    
    search_criterion = "UNSEEN" if unread_only else "ALL"
    
    if filters and "date_type" in filters:
        date_type = filters["date_type"]
        target_date = None
        
        if date_type == "today":
            target_date = datetime.date.today()
        elif date_type == "yesterday":
            target_date = datetime.date.today() - datetime.timedelta(days=1)
        elif date_type == "specific" and "date" in filters:
            try:
                target_date = datetime.datetime.strptime(filters["date"], "%Y-%m-%d").date()
            except Exception as e:
                logger.error(f"Error parsing specific date filter '{filters['date']}': {e}")
                
        if target_date:
            # Locale-independent IMAP date formatting (DD-Mon-YYYY)
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            imap_date_str = f"{target_date.day:02d}-{months[target_date.month - 1]}-{target_date.year}"
            
            if unread_only:
                search_criterion = f"UNSEEN ON {imap_date_str}"
            else:
                search_criterion = f"ON {imap_date_str}"
                
    logger.info(f"IMAP search criterion: {search_criterion}")
    status, data = mail.uid('search', None, search_criterion)
    if status != 'OK' or not data or not data[0]:
        return []
        
    uids = data[0].split()
    uids.reverse()  # Newest first
    selected_uids = uids[:limit]
    
    summaries = []
    for uid_bytes in selected_uids:
        uid = uid_bytes.decode('utf-8')
        try:
            # Fetch only the header part for performance
            status, header_data = mail.uid('fetch', uid, '(BODY.PEEK[HEADER])')
            if status != 'OK' or not header_data or not header_data[0]:
                continue
                
            raw_header = header_data[0][1]
            msg = email.message_from_bytes(raw_header)
            
            subject = decode_header_val(msg.get("Subject", "(No Subject)"))
            sender = decode_header_val(msg.get("From", "(Unknown Sender)"))
            date = decode_header_val(msg.get("Date", ""))
            
            # Fetch flags to check if unread
            status, flag_data = mail.uid('fetch', uid, '(FLAGS)')
            unread = True
            if status == 'OK' and flag_data and flag_data[0]:
                flags_str = flag_data[0].decode('utf-8', errors='ignore')
                if '\\Seen' in flags_str:
                    unread = False
            
            # Check content type header for attachment hints
            content_type = str(msg.get("Content-Type", ""))
            has_attachments = "multipart/mixed" in content_type or "multipart/related" in content_type
            
            summaries.append(EmailSummary(
                id=uid,
                sender=sender,
                subject=subject,
                date=date,
                unread=unread,
                has_attachments=has_attachments
            ))
        except Exception as e:
            logger.warning(f"Error fetching header for email UID {uid}: {e}")
            
    return summaries

def read_imap_email(
    mail: imaplib.IMAP4_SSL, 
    email_id: str = "latest", 
    sender: Optional[str] = None, 
    date: Optional[str] = None
) -> EmailDetails:
    """Retrieve details for a specific email by UID, index, 'latest', or by searching sender/date/query."""
    mail.select("INBOX", readonly=False)  # select writeable to auto-mark as read if supported
    
    # Resolve target message UID or sequence number
    target_uid = None
    target_seq = None
    
    # Fetch all UIDs to resolve 'latest' or relative index
    status, search_data = mail.uid('search', None, 'ALL')
    all_uids = search_data[0].split() if (status == 'OK' and search_data and search_data[0]) else []
    
    # Determine if we need to perform a header search
    is_search = False
    search_query = None
    
    if sender or date:
        is_search = True
    elif email_id.lower() != "latest" and not email_id.isdigit():
        is_search = True
        search_query = email_id
        
    if is_search:
        # Search the last 50 emails (newest first)
        uids_to_search = all_uids[-50:]
        uids_to_search.reverse()
        
        for uid_bytes in uids_to_search:
            uid = uid_bytes.decode('utf-8')
            try:
                status, header_data = mail.uid('fetch', uid, '(BODY.PEEK[HEADER])')
                if status != 'OK' or not header_data or not header_data[0]:
                    continue
                raw_header = header_data[0][1]
                msg = email.message_from_bytes(raw_header)
                
                msg_sender = decode_header_val(msg.get("From", "")).lower()
                msg_subject = decode_header_val(msg.get("Subject", "")).lower()
                msg_date = decode_header_val(msg.get("Date", "")).lower()
                
                match = True
                if sender and sender.lower() not in msg_sender:
                    match = False
                if date and date.lower() not in msg_date:
                    match = False
                if search_query:
                    sq = search_query.lower()
                    if sq not in msg_sender and sq not in msg_subject and sq not in msg_date:
                        match = False
                        
                if match:
                    target_uid = uid
                    break
            except Exception as e:
                logger.warning(f"Error searching headers for email UID {uid}: {e}")
                
        if not target_uid:
            criteria = []
            if sender: criteria.append(f"sender='{sender}'")
            if date: criteria.append(f"date='{date}'")
            if search_query: criteria.append(f"query='{search_query}'")
            raise ValueError(f"No email found matching criteria: {', '.join(criteria)}")
            
    else:
        if email_id.lower() == "latest":
            if not all_uids:
                raise ValueError("Mailbox is empty.")
            target_uid = all_uids[-1].decode('utf-8')
        elif email_id.isdigit():
            # Check if the number corresponds to a direct UID
            uid_str = email_id
            if any(u.decode('utf-8') == uid_str for u in all_uids):
                target_uid = uid_str
            else:
                # Fallback: treat as sequence index (1-based index from newest)
                try:
                    idx = int(email_id)
                    if 1 <= idx <= len(all_uids):
                        target_uid = all_uids[-idx].decode('utf-8')
                    else:
                        # Treat as absolute server sequence number
                        target_seq = email_id
                except Exception:
                    target_seq = email_id
        else:
            raise ValueError(f"Invalid email identifier: {email_id}")

    # Fetch message
    raw_msg = None
    final_id = email_id
    if target_uid:
        status, data = mail.uid('fetch', target_uid, '(RFC822)')
        if status == 'OK' and data and data[0]:
            raw_msg = data[0][1]
            final_id = target_uid
            # Explicitly mark as read
            mail.uid('store', target_uid, '+FLAGS', '\\Seen')
    
    if not raw_msg and target_seq:
        status, data = mail.fetch(target_seq, '(RFC822)')
        if status == 'OK' and data and data[0]:
            raw_msg = data[0][1]
            final_id = target_seq
            # Explicitly mark as read
            mail.store(target_seq, '+FLAGS', '\\Seen')
            
    if not raw_msg:
        raise ValueError(f"Email not found for identifier: {email_id}")
        
    msg = email.message_from_bytes(raw_msg)
    
    sender_val = decode_header_val(msg.get("From", "(Unknown Sender)"))
    
    recipients_list = []
    to_header = msg.get("To", "")
    if to_header:
        recipients_list.extend([decode_header_val(r.strip()) for r in to_header.split(",") if r.strip()])
    cc_header = msg.get("Cc", "")
    if cc_header:
        recipients_list.extend([decode_header_val(r.strip()) for r in cc_header.split(",") if r.strip()])
        
    subject = decode_header_val(msg.get("Subject", "(No Subject)"))
    date_val = decode_header_val(msg.get("Date", ""))
    
    body, attachments = extract_body_and_attachments(msg)
    
    return EmailDetails(
        id=final_id,
        sender=sender_val,
        recipients=recipients_list,
        subject=subject,
        date=date_val,
        body=body,
        attachments=attachments
    )
