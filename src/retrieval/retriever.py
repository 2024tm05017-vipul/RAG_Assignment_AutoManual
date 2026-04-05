"""Retriever - Query the vector store"""

import logging
from typing import Dict, List, Optional
import numpy as np
from src.retrieval.store import FAISSVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve chunks from vector store based on query"""
    
    def __init__(self, vector_store: FAISSVectorStore, embedder):
        """
        Args:
            vector_store: FAISSVectorStore instance
            embedder: Embedder instance with encode() method
        """
        self.vector_store = vector_store
        self.embedder = embedder
    
    def retrieve(self, query: str, top_k: int = 5, 
                 chunk_type_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Natural language query
            top_k: Number of chunks to retrieve
            chunk_type_filter: Filter by chunk type ('text', 'table', 'image')
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        if not query.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            # Embed query
            query_embedding = self.embedder.encode(query)
            
            # Search vector store
            results = self.vector_store.search(query_embedding, top_k=top_k * 2)  # Get 2x to allow filtering
            
            # Apply filter if specified
            if chunk_type_filter:
                results = [
                    (dist, chunk) for dist, chunk in results 
                    if chunk.get("type") == chunk_type_filter
                ]
            
            # Return top_k
            final_results = []
            for dist, chunk in results[:top_k]:
                result = {
                    "chunk_id": chunk.get("id"),
                    "content": chunk.get("content"),
                    "type": chunk.get("type"),
                    "filename": chunk.get("filename"),
                    "page": chunk.get("page"),
                    "distance": dist,
                    "similarity_score": chunk.get("similarity_score", 0.0),
                }
                
                # Add image-specific fields
                if chunk.get("type") == "image":
                    result["image_path"] = chunk.get("image_path")
                    result["image_summary"] = chunk.get("summary")
                
                final_results.append(result)
            
            logger.info(f"Retrieved {len(final_results)} chunks for query: {query[:50]}...")
            return final_results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def retrieve_by_document(self, filename: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve chunks from a specific document.
        
        Args:
            filename: Document filename to query
            top_k: Number of chunks to return
            
        Returns:
            List of chunks from the document
        """
        results = []
        
        for chunk in self.vector_store.chunks_store[:top_k]:
            if chunk.get("filename") == filename:
                results.append({
                    "chunk_id": chunk.get("id"),
                    "content": chunk.get("content"),
                    "type": chunk.get("type"),
                    "page": chunk.get("page"),
                })
        
        return results
    
    def get_indexed_documents(self) -> Dict:
        """Get list of indexed documents"""
        return self.vector_store.get_documents_list()
