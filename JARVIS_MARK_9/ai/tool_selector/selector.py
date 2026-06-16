"""
ai/tool_selector/selector.py

Given a user query, selects the closest matching tool from the FAISS index
using BGE sentence embeddings. Runs in < 50ms after resource loading.
"""

import json
import logging
import re
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Module-level resource cache
_model = None
_index = None
_metadata = None

def _initialize_resources() -> None:
    """
    Loads FAISS index, BGE model, and metadata from disk if not already cached.
    """
    global _model, _index, _metadata
    
    if _model is not None:
        return
        
    current_dir = Path(__file__).parent
    data_dir = current_dir / "data"
    model_path = data_dir / "model"
    index_path = data_dir / "faiss.index"
    metadata_path = data_dir / "tool_metadata.json"
    
    if not model_path.exists() or not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Run build_index.py first to compile offline resources.")
        
    logger.debug("Loading SentenceTransformer model from offline cache...")
    _model = SentenceTransformer(str(model_path), local_files_only=True)
    
    logger.debug("Loading FAISS index...")
    _index = faiss.read_index(str(index_path))
    
    logger.debug("Loading tool metadata...")
    with open(metadata_path, "r", encoding="utf-8") as f:
        _metadata = json.load(f)

def _check_rule_based_routing(query: str) -> str | None:
    """
    Checks if the preprocessed query matches an explicit, high-confidence rule
    to bypass semantic search and prevent false positives.
    """
    q = query.lower().strip()
    
    # 1. Open App vs Open Notepad and Write (Checked first to avoid URL/File overlap)
    if q in ["open notepad", "launch notepad", "start notepad", "run notepad", "please open notepad"]:
        return "open_app"
    if q.startswith("open notepad and write ") or q.startswith("open notepad to write ") or q.startswith("launch notepad and type ") or q.startswith("start notepad and type "):
        return "open_notepad_and_write"
        
    # 2. Search File vs Semantic File Search
    # If the user is asking where a file or document is, and does not specify conceptual keywords:
    search_keywords = ["where is", "find file", "locate file", "search for file", "where is the file", 
                       "where is document", "where is the document", "locate document", "find document",
                       "lookup file", "look up file", "find where", "locate the file", "locate the document",
                       "find my", "can you find", "can you find my", "where is my", "search for", "find"]
    semantic_keywords = ["semantic", "about", "discussing", "concerning", "related to", "concept", "meaning"]
    
    if any(q.startswith(kw) or f" {kw} " in f" {q} " for kw in search_keywords):
        if not any(sk in q for sk in semantic_keywords):
            return "search_file"
            
    # 3. Open Website (URL detection)
    # Match domain names, e.g. google.com, github.io, or URLs starting with http/https/www
    domain_pattern = r"^(https?://)?(www\.)?[a-z0-9\-]+(\.[a-z0-9\-]+)*\.[a-z]{2,6}(/.*)?$"
    common_file_exts = {"docx", "pdf", "txt", "py", "xlsx", "pptx", "png", "jpg", "jpeg", "zip", "rar", "csv", "log", "ipynb", "mp3", "mp4", "wav", "json", "md", "exe"}
    
    # Check if query starts with typical website navigation or open followed by a URL/domain
    nav_prefixes = ["go to ", "open website ", "open url ", "navigate to ", "open "]
    for prefix in nav_prefixes:
        if q.startswith(prefix):
            remainder = q[len(prefix):].strip()
            # If the remainder contains a dot and matches domain pattern, or starts with http
            if remainder.startswith("http") or remainder.startswith("www") or ("." in remainder and re.match(domain_pattern, remainder)):
                ext = remainder.split(".")[-1].split("/")[0].lower()
                if ext not in common_file_exts:
                    return "open_website"
            
    if re.match(domain_pattern, q):
        ext = q.split(".")[-1].split("/")[0].lower()
        if ext not in common_file_exts:
            return "open_website"
        
    # 4. Google Search / Youtube Search
    if q.startswith("google search ") or q.startswith("google for ") or q.startswith("search on google for "):
        return "google_search"
    if q.startswith("youtube search ") or q.startswith("search youtube for ") or q.startswith("search on youtube for "):
        return "youtube_search"
        
    # 5. Screenshot
    if q in ["screenshot", "take screenshot", "take a screenshot", "capture screen", "capture the screen"]:
        return "take_screenshot"
        
    # 6. Volume Mute/Unmute
    if q in ["mute", "mute volume", "mute sound", "silence volume", "silence speakers"]:
        return "mute_volume"
    if q in ["unmute", "unmute volume", "unmute sound", "restore volume", "restore sound"]:
        return "unmute_volume"
        
    # 7. System Power
    if q in ["reboot", "reboot computer", "reboot system", "restart computer", "restart system", "restart pc", "reboot pc"]:
        return "restart_system"
    if q in ["shutdown", "shutdown computer", "shutdown system", "turn off computer", "turn off pc", "power off pc", "power off computer"]:
        return "shutdown_system"
    if q in ["lock screen", "lock computer", "lock pc", "lock system", "lock windows"]:
        return "lock_system"
        
    # 8. Read File Content
    read_keywords = ["read file ", "read ", "cat ", "show content of ", "display content of ", "print content of ", "view content of "]
    for kw in read_keywords:
        if q.startswith(kw):
            remainder = q[len(kw):].strip().strip('"\'')
            # Route to read_file_content if it has a file extension or path separators
            if ("." in remainder and len(remainder.split(".")[-1]) in [2, 3, 4]) or "/" in remainder or "\\" in remainder:
                return "read_file_content"
                
    # 9. Open File vs Open App
    open_file_keywords = ["open file ", "open document ", "launch file ", "run file "]
    for kw in open_file_keywords:
        if q.startswith(kw):
            return "open_file"
            
    if q.startswith("open "):
        remainder = q[5:].strip().strip('"\'')
        if "." in remainder and len(remainder.split(".")[-1]) in [2, 3, 4] and not remainder.startswith("http") and not remainder.startswith("www"):
            return "open_file"

    # 10. Create File vs Create Folder
    if q.startswith("create file ") or q.startswith("make file ") or q.startswith("new file ") or q.startswith("generate file "):
        return "create_file"
    if q.startswith("create folder ") or q.startswith("make folder ") or q.startswith("new folder ") or q.startswith("create directory ") or q.startswith("make directory ") or q.startswith("new directory "):
        return "create_folder"

    # 11. Delete File vs Delete Folder
    if q.startswith("delete file ") or q.startswith("remove file ") or q.startswith("erase file ") or q.startswith("trash file "):
        return "delete_file"
    if q.startswith("delete folder ") or q.startswith("remove folder ") or q.startswith("delete directory ") or q.startswith("remove directory "):
        return "delete_folder"
    if q.startswith("delete ") or q.startswith("remove ") or q.startswith("erase ") or q.startswith("trash "):
        remainder = q.split(maxsplit=1)[1] if len(q.split()) > 1 else ""
        if remainder:
            if "folder" in remainder or "directory" in remainder:
                return "delete_folder"
            elif "." in remainder and len(remainder.split(".")[-1]) in [2, 3, 4]:
                return "delete_file"

    # 12. Rename File vs Rename Folder
    if q.startswith("rename ") and " to " in q:
        remainder = q[7:].split(" to ")[0].strip()
        if "folder" in remainder or "directory" in remainder:
            return "rename_folder"
        else:
            return "rename_file"

    # 13. Move File
    if q.startswith("move ") or q.startswith("transfer ") or q.startswith("shift "):
        if " to " in q or " in " in q or " into " in q:
            return "move_file"

    # 14. Copy File
    if q.startswith("copy ") or q.startswith("duplicate ") or q.startswith("clone "):
        if " to " in q or " in " in q or " into " in q:
            return "copy_file"

    # 15. Append to File
    if q.startswith("append ") or q.startswith("write "):
        if " to " in q:
            return "append_to_file"
        
    return None

def select_tool(query: str, top_k: int = 3) -> dict:
    """
    Queries the FAISS index to find the semantic match for the user query.
    """
    if not query:
        return {"selected_tool": None, "score": 0.0, "top_matches": []}
        
    # Check rule-based routing first
    routed_tool = _check_rule_based_routing(query)
    if routed_tool:
        return {
            "selected_tool": routed_tool,
            "score": 1.0,
            "top_matches": [{"tool": routed_tool, "score": 1.0}]
        }

    _initialize_resources()
    
    # Format query with the BGE instruction prefix
    formatted = "Represent this sentence for searching relevant passages: " + query
    
    # Generate BGE embedding
    embedding = _model.encode([formatted])
    embedding = np.array(embedding).astype("float32")
    
    # L2-normalize query embedding
    norm = np.linalg.norm(embedding, axis=1, keepdims=True)
    norm = np.where(norm == 0, 1e-10, norm)
    normalized = embedding / norm
    
    # Search index (query more than top_k to allow deduplication of multiple vectors per tool)
    search_k = min(top_k * 15, len(_metadata))
    scores, indices = _index.search(normalized, k=search_k)
    
    unique_tools = []
    seen = set()
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1 and idx < len(_metadata):
            tool_name = _metadata[idx]
            if tool_name not in seen:
                seen.add(tool_name)
                unique_tools.append({
                    "tool": tool_name,
                    "score": round(float(score), 4)
                })
                if len(unique_tools) >= top_k:
                    break
            
    if not unique_tools:
        return {"selected_tool": None, "score": 0.0, "top_matches": []}
        
    return {
        "selected_tool": unique_tools[0]["tool"],
        "score": unique_tools[0]["score"],
        "top_matches": unique_tools
    }
