"""Embeddings module - HuggingFace sentence transformers"""

import logging
import numpy as np
from typing import List, Union
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    """BGE embeddings for semantic search"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Args:
            model_name: HuggingFace model identifier
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        
        self.model_name = model_name
        
        # Use CPU to save VRAM
        self.device = "cpu"
        logger.info(f"Loading embedder on {self.device}")
        
        self.model = SentenceTransformer(model_name, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Embedder loaded: {model_name}, dim={self.embedding_dim}")
    
    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text to embeddings.
        
        Args:
            text: Single string or list of strings
            
        Returns:
            Array of embeddings (single or batch)
        """
        # Ensure text is a string or list
        if isinstance(text, str):
            embeddings = self.model.encode([text])
        else:
            embeddings = self.model.encode(text, batch_size=32)
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        
        return embeddings.astype('float32')
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim
