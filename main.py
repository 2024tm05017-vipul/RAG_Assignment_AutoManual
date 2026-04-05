"""Main FastAPI application entry point"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.ingestion.parser import PDFParser
from src.ingestion.processor import ChunkProcessor
from src.models.embedder import Embedder
from src.models.llm import LLMWrapper
from src.models.vlm import VisionLanguageModel
from src.retrieval.store import FAISSVectorStore
from src.retrieval.retriever import Retriever
from src.api.routes import router, system

# Setup logging
logging.basicConfig(
    level=config.logging.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize models on startup, cleanup on shutdown"""
    logger.info("=" * 60)
    logger.info("STARTING AUTOMOTIVE RAG SYSTEM")
    logger.info(f"Config: {config.api.HOST}:{config.api.PORT}")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        logger.info("Initializing document parser...")
        system.parser = PDFParser(dpi=config.ingestion.IMAGE_DPI)
        
        logger.info("Initializing chunk processor...")
        system.processor = ChunkProcessor(
            text_chunk_size=config.ingestion.CHUNK_SIZE,
            text_overlap=config.ingestion.CHUNK_OVERLAP,
            table_chunk_size=config.ingestion.TABLE_CHUNK_SIZE
        )
        
        logger.info("Loading embedder...")
        system.embedder = Embedder(config.model.EMBEDDING_MODEL)
        
        logger.info("Initializing vector store...")
        system.vector_store = FAISSVectorStore(
            embedding_dim=config.model.EMBEDDING_DIM,
            index_file=str(config.vector_store.INDEX_FILE)
        )
        
        # Try to load existing index
        if config.vector_store.INDEX_FILE.exists():
            logger.info("Loading existing index...")
            system.vector_store.load(str(config.vector_store.INDEX_FILE))
        
        logger.info("Initializing retriever...")
        system.retriever = Retriever(system.vector_store, system.embedder)
        
        logger.info("Loading LLM...")
        system.llm = LLMWrapper(
            model_name=config.model.LLM_MODEL,
            use_4bit=config.model.USE_4BIT_QUANTIZATION,
            max_tokens=config.model.LLM_MAX_TOKENS,
            temperature=config.model.LLM_TEMPERATURE
        )
        
        # Load VLM if enabled
        if config.model.USE_VISION_MODEL:
            try:
                logger.info("Loading Vision Language Model...")
                system.vlm = VisionLanguageModel(
                    model_name=config.model.VISION_MODEL,
                    use_4bit=config.model.USE_VISION_4BIT
                )
            except Exception as e:
                logger.warning(f"VLM loading failed: {e}. Image processing will be skipped.")
                system.vlm = None
        
        logger.info("=" * 60)
        logger.info("✓ ALL SYSTEMS INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    yield  # Application runs here
    
    # Cleanup
    logger.info("Shutting down system...")
    if system.vector_store:
        try:
            system.vector_store.save()
            logger.info("Index saved successfully")
        except Exception as e:
            logger.error(f"Error saving index: {e}")


# Create FastAPI app
app = FastAPI(
    title="Automotive Quality Control RAG System",
    description="Multimodal Retrieval-Augmented Generation for automotive service manuals",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, tags=["RAG API"])


@app.get("/")
async def root():
    """Root endpoint - serve documentation"""
    return {
        "message": "Automotive Quality Control RAG System",
        "docs": "Visit /docs for Swagger UI",
        "endpoints": {
            "/health": "GET - System health check",
            "/ingest": "POST - Upload and index PDF",
            "/query": "POST - Query indexed documents",
            "/docs": "GET - Swagger UI"
        }
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint"""
    return FileResponse("favicon.ico", status_code=404)


if __name__ == "__main__":
    logger.info(f"Starting server on {config.api.HOST}:{config.api.PORT}")
    
    uvicorn.run(
        "main:app",
        host=config.api.HOST,
        port=config.api.PORT,
        reload=config.api.RELOAD,
        workers=config.api.WORKERS,
        log_level=config.logging.LOG_LEVEL.lower()
    )
