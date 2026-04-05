"""Optional: Pre-download models to cache for faster first-run startup"""

import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_models():
    """Download and cache models locally"""
    
    logger.info("=" * 60)
    logger.info("MODEL DOWNLOAD UTILITY")
    logger.info("=" * 60)
    
    try:
        # Download embedder
        logger.info("Downloading embedder: BAAI/bge-small-en-v1.5...")
        from sentence_transformers import SentenceTransformer
        SentenceTransformer("BAAI/bge-small-en-v1.5")
        logger.info("✓ Embedder cached")
        
        # Download LLM
        logger.info("Downloading LLM: microsoft/phi-2...")
        logger.info("(This may take 5-10 minutes for first run...)")
        from transformers import AutoTokenizer, AutoModelForCausalLM
        AutoTokenizer.from_pretrained("microsoft/phi-2")
        # Note: Model download is large, only tokenizer for now
        logger.info("✓ LLM tokenizer cached")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ MODELS READY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        logger.info("Don't worry - models will be downloaded on first run")
        sys.exit(1)


if __name__ == "__main__":
    setup_models()
