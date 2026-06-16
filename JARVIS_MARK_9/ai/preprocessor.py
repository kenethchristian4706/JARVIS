"""
ai/preprocessor.py

Normalizes raw user input for Aether's tool selection pipeline.
Performs typo correction, alias normalization, and punctuation removal.
"""

import re

# Typo correction mapping
TYPO_MAPPING = {
    "chorme": "chrome",
    "chorma": "chrome",
    "vscde": "vscode",
    "notpad": "notepad",
    "noteapd": "notepad",
    "sptoify": "spotify",
    "discrod": "discord",
    "calcultor": "calculator",
    "opne": "open"
}

# Alias normalization mapping
ALIAS_MAPPING = {
    "vscode": "vs code",
    "vs-code": "vs code",
    "chrome browser": "chrome",
    "google chrome": "chrome",
    "ms word": "microsoft word",
    "ms excel": "microsoft excel",
    "ms powerpoint": "microsoft powerpoint",
    "win explorer": "windows explorer",
    "file explorer": "windows explorer"
}

# File-related keywords for lookup check
FILE_KEYWORDS = [
    "file", "folder", "document", "doc", "pdf", "txt", "docx", "xlsx",
    "pptx", "png", "jpg", "jpeg", "zip", "csv", "json", "py", "mp3", "mp4",
    "move", "copy", "delete", "rename", "create", "open", "find", "search",
    "read", "write", "append", "where is", "locate"
]

def preprocess(query: str) -> str:
    """
    Cleans and normalizes raw user queries.
    """
    if not query:
        return ""
        
    # 1. Strip leading/trailing whitespace
    text = query.strip()
    
    # 2. Convert to lowercase
    text = text.lower()
    
    # 3. Remove characters that are not letters, digits, spaces, dots, slashes, underscores, parentheses, or dashes
    # Note: Keep dots, forward/backward slashes, underscores, spaces, parentheses, and dashes.
    text = re.sub(r"[^\w\s\./\\_\(\)\-]", "", text)
    
    # 4. Apply typo correction for common app names
    words = text.split()
    corrected_words = [TYPO_MAPPING.get(w, w) for w in words]
    text = " ".join(corrected_words)
    
    # 5. Apply alias normalization using exact mapping
    # Sort keys by length descending to avoid partial matches replacing incorrectly
    for alias, replacement in sorted(ALIAS_MAPPING.items(), key=lambda x: len(x[0]), reverse=True):
        # Use word boundaries or literal replacements where appropriate
        pattern = r"\b" + re.escape(alias) + r"\b"
        text = re.sub(pattern, replacement, text)
        
    # 6. Collapse multiple spaces into one
    text = re.sub(r"\s+", " ", text).strip()
    
    # 7. Return the cleaned string
    return text

def is_file_related(query: str) -> bool:
    """
    Returns True if the query likely involves a file operation.
    """
    cleaned_query = query.lower()
    for keyword in FILE_KEYWORDS:
        if keyword in cleaned_query:
            return True
    return False

if __name__ == "__main__":
    test_queries = [
        "opne chorme!!!",
        "Can you launch vscode?",
        "Move report.pdf to Downloads",
        "Delete the folder Work",
        "read noteapd contents"
    ]
    
    print("Preprocessor Test Outputs:")
    print("=" * 40)
    for q in test_queries:
        processed = preprocess(q)
        file_related = is_file_related(q)
        print(f"Original:   '{q}'")
        print(f"Normalized: '{processed}'")
        print(f"File-related: {file_related}")
        print("-" * 40)
