"""System configuration - optimize for 8GB RAM"""

import os
from pathlib import Path
from typing import Optional

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models_cache"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_documents"

# Create directories if not exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Model Configuration (8GB RAM optimized)
class ModelConfig:
    # Embedding Model - Lightweight, 384 dimensions
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # 33M params, ~100MB
    EMBEDDING_DIM = 384
    
    # LLM - Extremely lightweight for 8GB constraint
    LLM_MODEL = "microsoft/phi-2"  # Better quality/size ratio than Qwen 0.5B
    LLM_DEVICE = "cpu"  # Force CPU to save VRAM
    USE_4BIT_QUANTIZATION = True  # Critical for 8GB RAM
    LLM_MAX_TOKENS = 512
    LLM_BATCH_SIZE = 1
    LLM_TEMPERATURE = 0.3
    LLM_TOP_P = 0.9
    
    # Vision Model - Optional, can be disabled on low memory
    USE_VISION_MODEL = True  # Can disable if OOM
    VISION_MODEL = "llava-hf/llava-1.5-7b-hf"
    VISION_DEVICE = "cpu"
    USE_VISION_4BIT = True
    VISION_MAX_TOKENS = 256
    
    # HuggingFace Cache
    HF_CACHE_DIR = MODELS_DIR / "huggingface"
    os.environ["HF_HOME"] = str(HF_CACHE_DIR)
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN", "")

# Vector Store Configuration
class VectorStoreConfig:
    STORE_TYPE = "faiss"  # Fast, local
    INDEX_TYPE = "IndexFlatL2"  # Simple, effective for automotive
    METRIC = "l2"
    INDEX_FILE = DATA_DIR / "faiss_index.pkl"
    METADATA_FILE = DATA_DIR / "metadata.json"
    MAX_CHUNK_SIZE = 512  # Characters per chunk

# Ingestion Configuration
class IngestionConfig:
    # PDF Parsing
    PDF_PARSER = "pymupdf"  # Lightweight, no external deps
    EXTRACT_IMAGES = True
    IMAGE_DPI = 150  # Lower DPI = faster processing
    
    # Chunking Strategy
    CHUNK_SIZE = 300  # chars for text
    CHUNK_OVERLAP = 50  # chars overlap for context
    TABLE_CHUNK_SIZE = 500  # Larger for dense tables
    
    # Maximum file size
    MAX_FILE_SIZE_MB = 100
    
    # Supported types
    ALLOWED_EXTENSIONS = {".pdf"}

# API Configuration
class APIConfig:
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    RELOAD = os.getenv("RELOAD", "False").lower() == "true"
    WORKERS = 1  # Single worker for 8GB RAM
    
    # API Settings
    QUERY_TOP_K = 5  # Number of chunks to retrieve
    MAX_QUERY_LENGTH = 500
    
    # Timeouts (in seconds)
    INGESTION_TIMEOUT = 300
    QUERY_TIMEOUT = 120

# Logging Configuration
class LogConfig:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / "logs" / "app.log"
    LOG_DIR = BASE_DIR / "logs"

# Create log directory
LogConfig.LOG_DIR.mkdir(exist_ok=True)

# Consolidate configs
class Config:
    model = ModelConfig()
    vector_store = VectorStoreConfig()
    ingestion = IngestionConfig()
    api = APIConfig()
    logging = LogConfig()

# Export for convenience
config = Config()
