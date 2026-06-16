import faiss
import numpy as np
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from tools.base import BaseTool

_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    """Returns the globally shared SentenceTransformer instance (lazily loaded)."""
    global _embedding_model
    if _embedding_model is None:
        # Load the BGE Small model
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model

class ToolSelector:
    """Uses FAISS and BGE Small to classify user queries to registered tools."""
    def __init__(self, tools: List[BaseTool]):
        self.tools = tools
        self.mappings: List[Tuple[str, BaseTool]] = []
        
        # 1. Map all example queries to their corresponding tool
        for tool in self.tools:
            for query in tool.example_queries:
                self.mappings.append((query, tool))
                
        if not self.mappings:
            raise ValueError("No example queries registered for tool selection.")
            
        # 2. Embed all example queries
        model = get_embedding_model()
        example_queries = [item[0] for item in self.mappings]
        embeddings = model.encode(example_queries, normalize_embeddings=True)
        
        # 3. Create FAISS Flat Inner Product index
        # Normalized vectors + Inner Product search = Cosine Similarity
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def find(self, query: str) -> Tuple[Optional[BaseTool], float]:
        """Finds the best-matching tool using cosine similarity search on query embeddings."""
        model = get_embedding_model()
        query_emb = model.encode([query], normalize_embeddings=True)
        
        # Search the top 1 match
        scores, indices = self.index.search(np.array(query_emb, dtype=np.float32), k=1)
        
        best_score = float(scores[0][0])
        best_idx = int(indices[0][0])
        
        if best_idx < 0 or best_idx >= len(self.mappings):
            return None, 0.0
            
        _, matched_tool = self.mappings[best_idx]
        return matched_tool, best_score
