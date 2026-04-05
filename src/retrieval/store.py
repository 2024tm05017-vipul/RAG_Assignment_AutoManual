"""FAISS Vector Store - Local vector index"""

import logging
import pickle
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
try:
    import faiss
except ImportError:
    faiss = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """Local FAISS vector store optimized for 8GB RAM"""
    
    def __init__(self, embedding_dim: int = 384, index_file: str = None):
        """
        Args:
            embedding_dim: Dimension of embeddings
            index_file: Path to save/load index
        """
        if faiss is None:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
        
        self.embedding_dim = embedding_dim
        self.index_file = Path(index_file) if index_file else Path("faiss_index.pkl")
        self.index = faiss.IndexFlatL2(embedding_dim)  # L2 distance
        self.chunks_store = []  # Store chunk metadata
        self.id_counter = 0
    
    def add_embeddings(self, embeddings: np.ndarray, chunks: List[Dict]) -> int:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: Array of shape (n_chunks, embedding_dim)
            chunks: List of chunk dictionaries with metadata
            
        Returns:
            Number of chunks added
        """
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Embeddings and chunks must have same length")
        
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_dim}, got {embeddings.shape[1]}")
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Add to FAISS
        self.index.add(embeddings)
        
        # Store chunk metadata
        for i, chunk in enumerate(chunks):
            chunk["vector_id"] = self.id_counter + i
            self.chunks_store.append(chunk)
        
        self.id_counter += len(chunks)
        
        logger.info(f"Added {len(chunks)} chunks to index. Total: {self.id_counter}")
        return len(chunks)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple]:
        """
        Search for nearest neighbors.
        
        Args:
            query_embedding: Single embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (distance, chunk_dict) tuples
        """
        if self.id_counter == 0:
            return []
        
        # Ensure query is float32
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # FAISS search
        distances, indices = self.index.search(query_embedding, min(top_k, self.id_counter))
        
        # Pair distances with chunks
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.chunks_store):
                chunk = self.chunks_store[idx].copy()
                chunk["distance"] = float(dist)
                # Convert distance to similarity score (0-1, higher is better)
                chunk["similarity_score"] = 1.0 / (1.0 + float(dist))
                results.append((float(dist), chunk))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            "total_chunks": self.id_counter,
            "embedding_dim": self.embedding_dim,
            "index_type": "IndexFlatL2",
            "memory_usage_mb": (self.index.ntotal * self.embedding_dim * 4) / (1024 * 1024)  # float32
        }
    
    def save(self, filepath: str = None):
        """Save index to disk"""
        filepath = Path(filepath or self.index_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'index': self.index,
                'chunks_store': self.chunks_store,
                'id_counter': self.id_counter,
                'embedding_dim': self.embedding_dim
            }, f)
        
        logger.info(f"Index saved to {filepath}")
    
    def load(self, filepath: str = None):
        """Load index from disk"""
        filepath = Path(filepath or self.index_file)
        
        if not filepath.exists():
            logger.warning(f"Index file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.index = data['index']
                self.chunks_store = data['chunks_store']
                self.id_counter = data['id_counter']
                self.embedding_dim = data['embedding_dim']
            
            logger.info(f"Index loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def clear(self):
        """Clear all indexed data"""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunks_store = []
        self.id_counter = 0
        logger.info("Index cleared")
    
    def get_documents_list(self) -> Dict[str, Dict]:
        """Get list of indexed documents with counts"""
        docs = {}
        
        for chunk in self.chunks_store:
            filename = chunk.get("filename", "unknown")
            if filename not in docs:
                docs[filename] = {
                    "count": 0,
                    "pages": set(),
                    "types": []
                }
            
            docs[filename]["count"] += 1
            docs[filename]["pages"].add(chunk.get("page", 0))
            if chunk.get("type") not in docs[filename]["types"]:
                docs[filename]["types"].append(chunk.get("type"))
        
        # Convert sets to lists for JSON serialization
        for filename in docs:
            docs[filename]["pages"] = sorted(list(docs[filename]["pages"]))
        
        return docs
