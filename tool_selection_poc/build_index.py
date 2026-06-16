"""
build_index.py

This script formats the phase-1 tool catalog, generates embeddings using
BAAI/bge-small-en-v1.5, normalizes the embeddings, indexes them using FAISS IndexFlatIP,
and saves the index, metadata, and the model locally for complete offline operation.
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tools import TOOLS

def main():
    print("Initializing offline tool selection index construction...")
    
    # 1. Ensure directory structure exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    print(f"Directory verified: {data_dir}")

    # 2. Format the searchable text documents
    documents = []
    tool_names = []
    
    for tool in TOOLS:
        tool_name = tool["tool_name"]
        description = tool["description"]
        examples_str = "\n".join(f"- {ex}" for ex in tool["examples"])
        
        doc = f"Tool: {tool_name}\n\nDescription:\n{description}\n\nExamples:\n{examples_str}"
        documents.append(doc)
        tool_names.append(tool_name)
        
    print(f"Prepared {len(documents)} tool documents for indexing.")

    # 3. Load the model from local cache (offline mode)
    model_name = "BAAI/bge-small-en-v1.5"
    print(f"Loading embedding model from local cache: {model_name}...")
    model = SentenceTransformer(model_name, local_files_only=True)
    
    # Save the model locally for future offline execution
    local_model_path = os.path.join(data_dir, 'model')
    print(f"Saving model locally to: {local_model_path} for offline use...")
    model.save(local_model_path)

    # 4. Generate embeddings
    print("Generating tool embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # 5. L2-Normalize the embeddings for Cosine Similarity (needed for IndexFlatIP)
    print("Normalizing embeddings...")
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero, although it shouldn't happen for valid text embeddings
    norms = np.where(norms == 0, 1e-10, norms)
    normalized_embeddings = embeddings / norms

    # 6. Build FAISS Index (IndexFlatIP computes Inner Product, which equals Cosine Similarity on normalized vectors)
    dimension = normalized_embeddings.shape[1]
    print(f"Initializing FAISS IndexFlatIP (dimension={dimension})...")
    index = faiss.IndexFlatIP(dimension)
    index.add(normalized_embeddings)
    
    # 7. Persist files
    index_path = os.path.join(data_dir, 'faiss.index')
    metadata_path = os.path.join(data_dir, 'tool_metadata.json')
    
    print(f"Saving FAISS index to: {index_path}...")
    faiss.write_index(index, index_path)
    
    print(f"Saving tool metadata to: {metadata_path}...")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(tool_names, f, indent=2, ensure_ascii=False)
        
    print("Offline Tool Selection Index build completed successfully!")

if __name__ == "__main__":
    main()
