"""
selector.py

This module implements the select_tool function. It loads the offline model,
index, and metadata, prepends the query instruction prefix, and uses FAISS to find
the top 3 matching tools using cosine similarity.
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Module-level cached resources to avoid reloading on every function call
_model = None
_index = None
_metadata = None

def _initialize_resources():
    """Load model, index, and metadata from the local offline data folder."""
    global _model, _index, _metadata
    
    if _model is not None:
        return
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    
    local_model_path = os.path.join(data_dir, 'model')
    index_path = os.path.join(data_dir, 'faiss.index')
    metadata_path = os.path.join(data_dir, 'tool_metadata.json')
    
    # Check if index files exist
    if not (os.path.exists(local_model_path) and os.path.exists(index_path) and os.path.exists(metadata_path)):
        raise FileNotFoundError(
            "Index files or local model not found. Please run 'build_index.py' first to generate them."
        )
        
    # Load SentenceTransformer model offline
    _model = SentenceTransformer(local_model_path)
    
    # Load FAISS index
    _index = faiss.read_index(index_path)
    
    # Load metadata mapping
    with open(metadata_path, 'r', encoding='utf-8') as f:
        _metadata = json.load(f)

def select_tool(query: str) -> dict:
    """
    Selects the most suitable tool for a given query using offline semantic search.
    
    Parameters:
        query (str): The natural language query.
        
    Returns:
        dict: A dictionary containing the selected tool, score, and top 3 matches.
    """
    # Initialize resources lazily
    _initialize_resources()
    
    # 1. Format the query with the BGE prefix for asymmetric retrieval
    # BGE models require this prefix on queries to align them with document embeddings.
    instruction_prefix = "Represent this sentence for searching relevant passages: "
    formatted_query = f"{instruction_prefix}{query}"
    
    # 2. Generate the embedding
    query_embedding = _model.encode([formatted_query])
    query_embedding = np.array(query_embedding).astype('float32')
    
    # 3. L2-Normalize the query embedding for Cosine Similarity
    norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
    norm = np.where(norm == 0, 1e-10, norm)
    normalized_query_embedding = query_embedding / norm
    
    # 4. Search the FAISS index (retrieve top 3 results)
    k = min(3, len(_metadata))
    scores, indices = _index.search(normalized_query_embedding, k)
    
    # 5. Format the results
    top_matches = []
    for score, idx in zip(scores[0], indices[0]):
        # index could be -1 if FAISS doesn't have enough entries (not expected here)
        if idx != -1:
            tool_name = _metadata[idx]
            top_matches.append({
                "tool": tool_name,
                "score": round(float(score), 4)
            })
            
    # Default outputs if no matches are found
    if not top_matches:
        return {
            "selected_tool": None,
            "score": 0.0,
            "top_matches": []
        }
        
    return {
        "selected_tool": top_matches[0]["tool"],
        "score": top_matches[0]["score"],
        "top_matches": top_matches
    }
