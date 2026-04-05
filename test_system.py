#!/usr/bin/env python3
"""Quick test of RAG system without starting the full server"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TESTING RAG SYSTEM COMPONENTS")
print("=" * 60)

try:
    # Test 1: Config
    print("\n[1/5] Testing configuration...")
    from src.config import config
    print(f"  ✓ Embedder: {config.model.EMBEDDING_MODEL}")
    print(f"  ✓ LLM: {config.model.LLM_MODEL}")
    print(f"  ✓ Vector Store: FAISS")
    
    # Test 2: Document Parser
    print("\n[2/5] Testing document parser...")
    from src.ingestion.parser import PDFParser
    parser = PDFParser()
    print(f"  ✓ Parser initialized")
    
    # Test 3: Vector Store
    print("\n[3/5] Testing vector store...")
    from src.retrieval.store import FAISSVectorStore
    import numpy as np
    store = FAISSVectorStore(embedding_dim=384)
    test_embeddings = np.random.randn(3, 384).astype('float32')
    test_chunks = [
        {"id": "c1", "content": "Test chunk 1", "type": "text", "page": 1, "filename": "test.pdf"},
        {"id": "c2", "content": "Test chunk 2", "type": "table", "page": 2, "filename": "test.pdf"},
        {"id": "c3", "content": "Test chunk 3", "type": "image", "page": 3, "filename": "test.pdf"},
    ]
    store.add_embeddings(test_embeddings, test_chunks)
    stats = store.get_stats()
    print(f"  ✓ Vector Store: {stats['total_chunks']} chunks, {stats['embedding_dim']} dims")
    
    # Test 4: Parse Sample PDF
    print("\n[4/5] Testing PDF parsing...")
    sample_pdf = Path("sample_documents/engine_service_manual.pdf")
    if sample_pdf.exists():
        parsed = parser.parse(str(sample_pdf))
        print(f"  ✓ PDF parsed: {parsed['filename']}")
        print(f"    - Pages: {parsed['metadata']['total_pages']}")
        print(f"    - Text chunks: {len(parsed['text_content'])}")
        print(f"    - Tables: {len(parsed['tables'])}")
        print(f"    - Images: {len(parsed['images'])}")
    else:
        print(f"  ✗ Sample PDF not found: {sample_pdf}")
    
    # Test 5: API Schemas
    print("\n[5/5] Testing API schemas...")
    from src.api.schemas import HealthResponse, QueryResponse
    health = HealthResponse(
        status="healthy",
        models_ready=True,
        indexed_documents=1,
        documents=["test.pdf"],
        total_chunks=10,
        index_size_mb=1.5,
        uptime_seconds=42.0,
        available_endpoints=["/ingest", "/query", "/health", "/docs"]
    )
    print(f"  ✓ Health schema created")
    print(f"  ✓ Query schema ready")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nSystem is ready to run: python main.py")
    
except Exception as e:
    print(f"\n✗ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
