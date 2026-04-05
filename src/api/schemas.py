"""API schemas - Pydantic models for FastAPI"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="System status")
    models_ready: bool = Field(..., description="Are models loaded")
    indexed_documents: int = Field(..., description="Number of indexed documents")
    documents: List[str] = Field(..., description="List of document filenames")
    total_chunks: int = Field(..., description="Total chunks in index")
    index_size_mb: float = Field(..., description="Index size in MB")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    available_endpoints: List[str] = Field(..., description="Available API endpoints")


class IngestRequest(BaseModel):
    """Ingest endpoint request"""
    pass  # File is handled by FastAPI file parameter


class IngestResponse(BaseModel):
    """Ingest endpoint response"""
    filename: str = Field(..., description="Uploaded filename")
    status: str = Field(..., description="Ingestion status")
    extraction_time_seconds: float = Field(..., description="Time to parse PDF")
    chunks_created: Dict[str, int] = Field(..., description="Chunks by type")
    total_chunks: int = Field(..., description="Total chunks created")
    indexed: bool = Field(..., description="Successfully indexed")
    message: str = Field(..., description="Status message")


class QueryRequest(BaseModel):
    """Query endpoint request"""
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    include_metadata: bool = Field(default=True, description="Include metadata in response")


class SourceReference(BaseModel):
    """Source reference for answer"""
    filename: str = Field(..., description="Document filename")
    page: int = Field(..., description="Page number")
    chunk_type: str = Field(..., description="Type of chunk (text/table/image)")
    chunk_id: str = Field(..., description="Unique chunk ID")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    preview: str = Field(..., description="Preview of retrieved content")


class QueryResponse(BaseModel):
    """Query endpoint response"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceReference] = Field(..., description="Source references")
    retrieval_time_ms: float = Field(..., description="Time to retrieve chunks")
    generation_time_ms: float = Field(..., description="Time to generate answer")
    total_time_ms: float = Field(..., description="Total processing time")
    confidence: str = Field(..., description="Confidence level (low/medium/high)")
    note: str = Field(..., description="Additional notes")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
