"""
llm/query_normalizer.py

Preprocessing layer for normalizing user queries before routing/planning.
Preserves quoted strings, paths, URLs, emails, and filenames using temporary placeholders
while correcting common typos and normalizing whitespace.
"""

import re
from typing import Dict

# Patterns that must not be altered by spelling correction
PRESERVE_PATTERNS = [
    # Quotes
    r'"[^"]*"',
    r"'[^']*'",
    # Emails
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    # URLs
    r'\bhttps?://[^\s]+',
    r'\bwww\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    # Absolute paths (Windows/Unix)
    r'\b[a-zA-Z]:[/\\](?:[^\\\s\/:*?"<>|]+[/\\])*[^\\\s\/:*?"<>|]+',
    # Relative/Home paths
    r'(?:~|\.|\.\.)[/\\][a-zA-Z0-9._/\\-]+',
    # Filenames with extensions
    r'\b[a-zA-Z0-9_\-]+\.(?:pdf|csv|txt|docx|xlsx|zip|png|jpg|log|py|json|ipynb|md|lnk|exe|bat|sh)\b'
]

# Typo dictionary for correction
TYPO_MAP: Dict[str, str] = {
    "opne": "open",
    "extantion": "extension",
    "chorme": "chrome",
    "vscdoe": "vscode",
    "calclator": "calculator",
    "calcualtor": "calculator",
    "spotfy": "spotify",
    "scrneshot": "screenshot",
    "screenshoot": "screenshot",
    "brwoser": "browser",
    "documnet": "document",
    "documnets": "documents",
    "cretae": "create",
    "delte": "delete",
    "renam": "rename",
    "coyp": "copy"
}

def normalize_query(query: str) -> str:
    """
    Normalizes whitespace and corrects spelling typos in the query
    while strictly preserving quoted strings, paths, URLs, emails, and filenames.
    """
    if not query:
        return ""

    placeholders = []

    # Helper function to cache preserved strings
    def cache_placeholder(match):
        matched_str = match.group(0)
        idx = len(placeholders)
        placeholders.append(matched_str)
        return f"__PLACEHOLDER_{idx}__"

    temp_query = query
    # Replace all matching preservation patterns with placeholders
    for pattern in PRESERVE_PATTERNS:
        temp_query = re.sub(pattern, cache_placeholder, temp_query)

    # Whitespace normalization
    temp_query = re.sub(r'\s+', ' ', temp_query).strip()

    # Spelling correction on word boundaries
    words = []
    # Split keeping non-alphanumeric chars to preserve exact punctuation
    for token in re.split(r'(\W+)', temp_query):
        token_lower = token.lower()
        if token_lower in TYPO_MAP:
            corrected = TYPO_MAP[token_lower]
            # Match original case structure
            if token.istitle():
                corrected = corrected.title()
            elif token.isupper():
                corrected = corrected.upper()
            words.append(corrected)
        else:
            words.append(token)

    temp_query = "".join(words)

    # Restore preserved strings
    for idx, original_val in enumerate(placeholders):
        temp_query = temp_query.replace(f"__PLACEHOLDER_{idx}__", original_val)

    return temp_query
