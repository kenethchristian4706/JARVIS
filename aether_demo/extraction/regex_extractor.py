import re
from typing import Optional

def extract_app_name(query: str) -> Optional[str]:
    """Extracts an app name from queries like 'open chrome', 'launch spotify', etc."""
    # Matches verbs like open, launch, start, run followed by the app name
    pattern = r"\b(?:open|launch|start|run)\s+([a-zA-Z0-9_\-\.\s]+)"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        # Clean up leading/trailing whitespace
        return match.group(1).strip()
    return None

def extract_volume_level(query: str) -> Optional[int]:
    """Extracts volume level (0-100) from queries. Returns None if not matched."""
    # Special cases
    if re.search(r"\b(?:mute|silence|turn off sound|sound off)\b", query, re.IGNORECASE):
        return 0
    
    # Try to extract numbers
    pattern = r"\b(?:to|up to|at|set|volume)\s+(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        return max(0, min(100, val))
    
    # Simple fallback: find any number in the query
    numbers = re.findall(r"\b\d+\b", query)
    if numbers:
        val = int(numbers[0])
        return max(0, min(100, val))
        
    return None

def extract_file_type(query: str) -> Optional[str]:
    """Extracts file type/extension keyword from queries like 'search for PDF files'."""
    # Map common terms to extensions
    mapping = {
        r"\bpdf[s]?\b": "pdf",
        r"\b(?:presentation[s]?|powerpoint[s]?|pptx)\b": "pptx",
        r"\b(?:text[s]?|txt|note[s]?)\b": "txt",
        r"\b(?:spreadsheet[s]?|excel|xlsx)\b": "xlsx",
        r"\b(?:word|docx|doc)\b": "docx",
        r"\b(?:image[s]?|photo[s]?|jpg|png|jpeg)\b": "jpg",
        r"\b(?:json|config)\b": "json",
        r"\b(?:markdown|md|readme)\b": "md"
    }
    
    for pattern, extension in mapping.items():
        if re.search(pattern, query, re.IGNORECASE):
            return extension
            
    # Fallback to checking for literal extensions like ".txt" or "txt"
    match = re.search(r"\b([a-zA-Z0-9]+)\s+file[s]?\b", query, re.IGNORECASE)
    if match:
        potential_ext = match.group(1).lower()
        if potential_ext in ["pdf", "pptx", "txt", "xlsx", "docx", "jpg", "json", "md"]:
            return potential_ext

    return None
