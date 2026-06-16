"""
ai/tool_selector/build_index.py

One-time offline index builder. Generates L2-normalized embeddings using
BAAI/bge-small-en-v1.5 for all 56 tools and builds a FAISS IndexFlatIP.
"""

import os
import json
import shutil
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

from ai.tool_selector.tools import TOOLS

def main():
    # Resolve paths relative to this script
    current_dir = Path(__file__).parent
    data_dir = current_dir / "data"
    model_dir = data_dir / "model"
    index_path = data_dir / "faiss.index"
    metadata_path = data_dir / "tool_metadata.json"
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Model (local cache if exists, else copy from JARVIS_MARK_8, else download)
    print("Loading model...")
    source_model = Path("C:/Users/lenovo/dev/ather/JARVIS_MARK_6/JARVIS_MARK_8/ai/data/model")
    
    if model_dir.exists():
        print(f"Loading model from local path: {model_dir}")
        model = SentenceTransformer(str(model_dir), local_files_only=True)
    elif source_model.exists():
        print(f"Copying model from older cache: {source_model} to {model_dir}")
        shutil.copytree(str(source_model), str(model_dir))
        model = SentenceTransformer(str(model_dir), local_files_only=True)
    else:
        print("Local model not found. Downloading BAAI/bge-small-en-v1.5 from Hugging Face...")
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print(f"Saving model to local path: {model_dir}")
        model.save(str(model_dir))
        
    # 2. Format documents (indexing each description and example individually)
    print(f"Generating embeddings for {len(TOOLS)} tools and their examples...")
    documents = []
    tool_names = []
    
    for entry in TOOLS:
        tool_name = entry["tool_name"]
        description = entry["description"]
        examples = entry["examples"]
        
        # Add description document
        desc_doc = f"Tool: {tool_name}\nDescription: {description}"
        documents.append(desc_doc)
        tool_names.append(tool_name)
        
        # Add each individual example
        for ex in examples:
            documents.append(ex)
            tool_names.append(tool_name)
        
    # Generate BGE embeddings
    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")
    
    # 3. L2-normalize embeddings for cosine similarity
    print("Normalizing embeddings...")
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    normalized = embeddings / norms
    
    # 4. Build FAISS IndexFlatIP (dim=384 for bge-small)
    dimension = normalized.shape[1]
    print(f"Building FAISS index (dim={dimension})...")
    index = faiss.IndexFlatIP(dimension)
    index.add(normalized)
    
    # 5. Save output files
    print(f"Saving index to {index_path}")
    faiss.write_index(index, str(index_path))
    
    print(f"Saving metadata to {metadata_path}")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(tool_names, f, indent=2)
        
    print(f"Done. Index contains {index.ntotal} vectors.")

if __name__ == "__main__":
    main()
