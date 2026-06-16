import os
import faiss
import numpy as np
from typing import List, Dict, Any
from config import DEMO_DIR

# Shared memory structures for the semantic file index
_file_index = None  # FAISS Index
_filepaths: List[str] = []  # List of filepaths corresponding to index IDs

def get_embedding_model():
    """Import and return the shared embedding model from tool_selector."""
    from tool_selector import get_embedding_model as shared_model_getter
    return shared_model_getter()

def rebuild_file_index():
    """Scans the demo directory, embeds all file names, and builds the FAISS index."""
    global _file_index, _filepaths
    
    # 1. Collect all files in DEMO_DIR
    _filepaths = []
    if os.path.exists(DEMO_DIR):
        for root, _, files in os.walk(DEMO_DIR):
            for file in files:
                _filepaths.append(os.path.join(root, file))
                
    if not _filepaths:
        _file_index = None
        return
        
    # 2. Get filenames + extensions for embedding
    filenames = [os.path.basename(f) for f in _filepaths]
    
    # 3. Embed all filenames
    model = get_embedding_model()
    embeddings = model.encode(filenames, normalize_embeddings=True)
    
    # 4. Build FAISS Flat Inner Product index (for Cosine Similarity)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    
    _file_index = index

def search_semantic(query_str: str, file_type: str = None) -> List[Dict[str, Any]]:
    """Searches the semantic index of filenames using cosine similarity."""
    global _file_index, _filepaths
    
    if _file_index is None or not _filepaths:
        # Build if it wasn't built yet
        rebuild_file_index()
        if _file_index is None or not _filepaths:
            return []
            
    # Embed search query
    model = get_embedding_model()
    query_emb = model.encode([query_str], normalize_embeddings=True)
    
    # Query FAISS
    k = min(10, len(_filepaths))
    if k == 0:
        return []
        
    scores, indices = _file_index.search(np.array(query_emb, dtype=np.float32), k=k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_filepaths):
            continue
            
        filepath = _filepaths[idx]
        filename = os.path.basename(filepath)
        
        # Verify file still exists physically
        if not os.path.exists(filepath):
            continue
            
        # Filter by file type if specified
        if file_type:
            _, ext = os.path.splitext(filename)
            if ext.lower().lstrip(".") != file_type.lower().lstrip("."):
                continue
                
        results.append({
            "filepath": filepath,
            "filename": filename,
            "score": float(score)
        })
        
    return results
