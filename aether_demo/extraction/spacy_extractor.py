import re
from typing import Optional, List, Tuple
import spacy

_nlp = None

def get_nlp():
    """Lazily loads the spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Attempt to download model inline if it fails to load
            import subprocess
            import sys
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

def extract_filename_candidates(query: str) -> List[str]:
    """Extracts potential filename or folder candidates using spaCy and regex."""
    nlp = get_nlp()
    doc = nlp(query)
    
    candidates = []
    
    # 1. Regex search for tokens with extensions (e.g., old_report.pdf)
    ext_pattern = r"\b[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+\b"
    for match in re.finditer(ext_pattern, query):
        candidates.append(match.group(0))
        
    # 2. Extract noun chunks or adjacent nouns/proper nouns
    for chunk in doc.noun_chunks:
        # Clean chunk text (remove determiners like 'a', 'the', 'my', 'this', 'that')
        clean_tokens = [t.text for t in chunk if t.dep_ != "det" and t.text.lower() not in ("file", "files", "folder", "folders", "directory", "archive")]
        clean_text = " ".join(clean_tokens).strip()
        if clean_text and clean_text not in candidates:
            candidates.append(clean_text)
              
    # 3. Individual nouns and proper nouns
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and token.text not in candidates:
            # Don't add if it's a utility keyword
            if token.text.lower() not in ("file", "files", "folder", "folders", "directory", "archive", "document", "documents", "presentation"):
                candidates.append(token.text)
                  
    # Clean and deduplicate keeping order
    seen = set()
    deduped = []
    for c in candidates:
        c_clean = c.strip().strip("'\"").strip()
        if c_clean and c_clean.lower() not in seen:
            seen.add(c_clean.lower())
            deduped.append(c_clean)
            
    return deduped

def extract_move_targets(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts source and destination files/paths for move commands using NLP and text splitting."""
    nlp = get_nlp()
    doc = nlp(query)
    
    to_token_idx = -1
    for i, token in enumerate(doc):
        if token.text.lower() in ("to", "into"):
            to_token_idx = i
            break
            
    if to_token_idx != -1:
        # Extract source candidates from the left part
        left_text = " ".join([t.text for t in doc[:to_token_idx]])
        # Remove verbs like "move", "transfer"
        left_clean = re.sub(r"\b(?:move|transfer|shift|send|put)\b", "", left_text, flags=re.IGNORECASE).strip()
        
        # Extract destination candidates from the right part
        right_text = " ".join([t.text for t in doc[to_token_idx+1:]])
        right_clean = re.sub(r"\b(?:the|folder|directory|archive)\b", "", right_text, flags=re.IGNORECASE).strip()
        
        # Clean source filename: it could be a word with an extension
        src_match = re.search(r"\b[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+\b", left_clean)
        if src_match:
            source = src_match.group(0)
        else:
            # Fallback to noun chunks on left
            left_candidates = extract_filename_candidates(left_clean)
            source = left_candidates[0] if left_candidates else left_clean
            
        dest_candidates = extract_filename_candidates(right_clean)
        dest = dest_candidates[0] if dest_candidates else right_clean
        
        return source, dest
        
    return None, None

def extract_create_file_params(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts filename and content parameters from file creation requests."""
    filename = None
    content = None
    
    # Try splitting by content keywords
    content_split = re.split(r"\b(?:with content|containing|with the content of|with text)\b", query, maxsplit=1, flags=re.IGNORECASE)
    
    name_part = content_split[0]
    if len(content_split) > 1:
        content = content_split[1].strip().strip("'\"")
        
    # Look for names with extensions first
    ext_match = re.search(r"\b[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+\b", name_part)
    if ext_match:
        filename = ext_match.group(0)
    else:
        # Look for named/called X
        match = re.search(r"\b(?:named|called|file|titled)\s+([a-zA-Z0-9_\-]+)", name_part, re.IGNORECASE)
        if match:
            filename = match.group(1)
        else:
            # Fallback to noun chunks or last words after "create"/"make"
            nlp = get_nlp()
            doc = nlp(name_part)
            # Find verbs like create, make
            action_idx = -1
            for i, token in enumerate(doc):
                if token.text.lower() in ("create", "make", "write", "new"):
                    action_idx = i
            
            after_action = [t.text for t in doc[action_idx+1:] if t.text.lower() not in ("a", "an", "new", "file", "text", "called", "named")]
            if after_action:
                filename = after_action[0] # Take the first noun / word
                
    if filename:
        filename = filename.strip().strip("'\"")
    return filename, content
