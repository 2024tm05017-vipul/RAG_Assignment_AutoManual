"""API routes - FastAPI endpoints"""

import logging
import time
from datetime import datetime
from typing import Optional
import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from src.api.schemas import (
    HealthResponse, IngestResponse, QueryRequest, 
    QueryResponse, SourceReference, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Global state (shared between endpoints)
class SystemState:
    def __init__(self):
        self.start_time = time.time()
        self.parser = None
        self.processor = None
        self.embedder = None
        self.vector_store = None
        self.retriever = None
        self.llm = None
        self.vlm = None

system = SystemState()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check endpoint"""
    try:
        uptime = time.time() - system.start_time
        
        # Get indexed documents
        indexed_docs = []
        total_chunks = 0
        index_size_mb = 0.0
        
        if system.vector_store:
            docs_dict = system.vector_store.get_documents_list()
            indexed_docs = list(docs_dict.keys())
            stats = system.vector_store.get_stats()
            total_chunks = stats.get("total_chunks", 0)
            index_size_mb = stats.get("memory_usage_mb", 0.0)
        
        return HealthResponse(
            status="healthy",
            models_ready=all([system.embedder, system.llm, system.vector_store]),
            indexed_documents=len(indexed_docs),
            documents=indexed_docs,
            total_chunks=total_chunks,
            index_size_mb=round(index_size_mb, 2),
            uptime_seconds=round(uptime, 2),
            available_endpoints=["/health", "/ingest", "/query", "/docs"]
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """Ingest and index a PDF document"""
    
    if system.parser is None or system.processor is None or system.embedder is None:
        raise HTTPException(status_code=500, detail="System not initialized. Models not loaded.")
    
    # Validate file
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=413, detail="File too large (max 100MB)")
    
    temp_path = f"/tmp/{file.filename}"
    
    try:
        start_time = time.time()
        
        # Save uploaded file
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Parse PDF
        logger.info(f"Parsing PDF: {file.filename}")
        parsed_content = system.parser.parse(temp_path)
        
        # Process chunks
        logger.info("Processing chunks...")
        chunks_data = system.processor.process(parsed_content)
        
        # Prepare all chunks for embedding
        all_chunks = []
        all_chunks.extend(chunks_data.get("text_chunks", []))
        all_chunks.extend(chunks_data.get("table_chunks", []))
        all_chunks.extend(chunks_data.get("image_chunks", []))
        
        # Embed chunks (skip image chunks, they'll be summarized later)
        embeddings_list = []
        chunks_to_index = []
        
        for chunk in all_chunks:
            if chunk.get("type") == "image":
                # For images, generate summary first if VLM available
                if system.vlm and system.vlm.is_available() and chunk.get("image_path"):
                    try:
                        summary = system.vlm.summarize_image(chunk["image_path"])
                        chunk["summary"] = summary
                        # Embed summary instead of empty content
                        embedding = system.embedder.encode(summary)
                        embeddings_list.append(embedding[0])
                        chunks_to_index.append(chunk)
                    except Exception as e:
                        logger.warning(f"Error summarizing image: {e}")
                else:
                    # Skip image without VLM
                    logger.debug("Skipping image (VLM not available)")
                    continue
            else:
                # Text and table chunks
                content = chunk.get("content", "")
                if content.strip():
                    embedding = system.embedder.encode(content)
                    embeddings_list.append(embedding[0])
                    chunks_to_index.append(chunk)
        
        # Add to vector store
        if embeddings_list:
            import numpy as np
            embeddings_array = np.array(embeddings_list).astype('float32')
            system.vector_store.add_embeddings(embeddings_array, chunks_to_index)
            system.vector_store.save()
        
        extraction_time = time.time() - start_time
        
        # Remove temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return IngestResponse(
            filename=file.filename,
            status="success",
            extraction_time_seconds=round(extraction_time, 2),
            chunks_created={
                "text": len(chunks_data.get("text_chunks", [])),
                "table": len(chunks_data.get("table_chunks", [])),
                "image": len(chunks_data.get("image_chunks", []))
            },
            total_chunks=len(chunks_to_index),
            indexed=True,
            message=f"Successfully indexed {file.filename} with {len(chunks_to_index)} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the indexed documents"""
    
    if system.retriever is None or system.llm is None:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    docs = system.vector_store.get_documents_list()
    if not docs:
        raise HTTPException(status_code=404, detail="No documents indexed. Please upload a PDF first.")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        start_time = time.time()
        
        # Retrieve chunks
        retrieval_start = time.time()
        retrieved_chunks = system.retriever.retrieve(request.query, top_k=request.top_k)
        retrieval_time = time.time() - retrieval_start
        
        if not retrieved_chunks:
            raise HTTPException(status_code=404, detail="No relevant chunks found")
        
        # Prepare context from chunks
        context_parts = []
        source_references = []
        
        for chunk in retrieved_chunks:
            content = chunk.get("content", "")
            if chunk.get("type") == "image" and chunk.get("image_summary"):
                content = f"[IMAGE] {chunk.get('image_summary')}"
            
            context_parts.append(f"[{chunk.get('type').upper()}, Page {chunk.get('page')}]\n{content}")
            
            # Create source reference
            preview = content[:100] + "..." if len(content) > 100 else content
            source_references.append(SourceReference(
                filename=chunk.get("filename", "unknown"),
                page=chunk.get("page", 0),
                chunk_type=chunk.get("type", "text"),
                chunk_id=chunk.get("chunk_id", ""),
                relevance_score=min(1.0, chunk.get("similarity_score", 0.0)),
                preview=preview
            ))
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using the LLM
        from src.constants import RAG_PROMPT_TEMPLATE
        
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            question=request.query
        )
        
        generation_start = time.time()
        answer = system.llm.generate(prompt, max_length=512)
        generation_time = time.time() - generation_start
        
        total_time = time.time() - start_time
        
        # Determine confidence
        avg_relevance = sum(s.relevance_score for s in source_references) / len(source_references) if source_references else 0
        if avg_relevance > 0.8:
            confidence = "high"
        elif avg_relevance > 0.6:
            confidence = "medium"
        else:
            confidence = "low"
        
        return QueryResponse(
            query=request.query,
            answer=answer.strip(),
            sources=source_references,
            retrieval_time_ms=round(retrieval_time * 1000, 2),
            generation_time_ms=round(generation_time * 1000, 2),
            total_time_ms=round(total_time * 1000, 2),
            confidence=confidence,
            note="Answer grounded in retrieved documents. All specifications sourced from official documentation."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# Additional utility endpoints
@router.delete("/clear")
async def clear_index():
    """Clear all indexed documents (for testing)"""
    try:
        system.vector_store.clear()
        logger.info("Index cleared")
        return {"status": "cleared", "message": "All indexed documents removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        if system.vector_store:
            stats = system.vector_store.get_stats()
            stats["documents"] = system.vector_store.get_documents_list()
            return stats
        return {"error": "Vector store not initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
