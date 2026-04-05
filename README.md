# Multimodal RAG System for Automotive Quality Control

## Problem Statement

### Domain Identification
**Professional Domain:** Automotive Manufacturing and Quality Control

### Problem Description
In modern automotive manufacturing, quality control engineers struggle with inefficient access to critical technical documentation during defect investigation and root-cause analysis. A typical quality issue may require cross-referencing service manuals (containing text procedures), maintenance tables (specifications, torque values, intervals), engineering diagrams (component layouts, assembly sequences), and diagnostic flowcharts simultaneously. 

Currently, engineers rely on:
- Manual PDF search (time-consuming, loses context)
- Keyword matching (misses semantic relevance)
- Siloed documents (text manual separate from diagrams)
- Legacy document management systems (poor search, no semantic understanding)

This fragmented approach leads to:
1. **Delayed Root-Cause Analysis** - 2-4 hours wasted searching documentation for each critical defect
2. **Inconsistent Decision-Making** - Different engineers find different information, leading to inconsistent repair strategies
3. **Low First-Pass Yield** - Technicians miss subtle specification constraints hidden in tables or diagrams
4. **Regulatory Risk** - Inability to quickly audit compliance with service procedures

### Why This Problem Is Unique
Unlike generic document Q&A systems, automotive quality control has domain-specific challenges:

**Technical Complexity:**
- Highly specialized terminology (e.g., "TorqueSpec M8x1.25 ISO4014 35±2 Nm", "lean-burn combustion anomaly")
- Dense numerical data in tables (torque specifications, tolerances, pressure ranges across 30+ engine variants)
- Multi-part assembly diagrams with numbered callouts requiring image-to-text linkage
- Cross-references between documents (e.g., "See Appendix C Table 3.2")

**Multimodal Nature:**
- Service manuals contain procedural text AND component diagrams that must be understood together
- Quality specifications appear in tabular form with footnotes and conditional logic
- Diagnostic decision trees are image-based flowcharts that require semantic parsing
- A single quality issue may require synthesizing information from all three modalities

**Regulatory & Safety Context:**
- Answers must be grounded only in official documentation (no hallucinations allowed)
- Citations must include page numbers and section references for compliance audits
- A single retrieved error can result in warranty failures or safety recalls

### Why RAG Is the Right Approach
RAG is superior to alternatives for this use case:

- **vs. Fine-tuning:** Automotive specifications change frequently (new engine models, regulatory updates). RAG allows immediate incorporation of updated manuals without retraining.
- **vs. Keyword Search:** Semantic search captures intent ("what's the coolant temperature limit?") vs. exact phrase matching
- **vs. Generative LLMs alone:** Without RAG, LLMs hallucinate specifications, leading to costly manufacturing errors. RAG ensures all answers are grounded in official documentation with traceable sources.
- **vs. Manual Search:** Multimodal RAG retrieves text, tables, and image summaries simultaneously, answering complex questions that require cross-modal synthesis in seconds

### Expected Outcomes
A successful RAG system would enable quality engineers to:

1. **Ask natural language questions** - "What's the torque spec for the intake manifold bolts on the V6 engine?" and receive exact specification + page reference
2. **Retrieve tables contextually** - Search for quality thresholds and get relevant tolerance tables with unit consistency checks
3. **Cross-modal lookup** - Ask "How do I diagnose a lean-burn anomaly?" and retrieve diagnostic flowchart image + supporting text procedure
4. **Audit trail support** - Every answer includes source file, page, and chunk type for regulatory compliance
5. **Reduce defect resolution time from 2-4 hours to <5 minutes**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server                               │
└─────────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │   API Layer (src/api/routes.py)     │
        │ - /ingest, /query, /health, /docs   │
        └─────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────────────────┐
    │              RAG Pipeline                         │
    │  (src/models/rag_chain.py)                        │
    │  - Query → Retrieve → Generate → Source          │
    └──────────────────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────────────────┐
    │         Retrieval Module                          │
    │  (src/retrieval/retriever.py)                     │
    │  - FAISS Vector Index                             │
    │  - Metadata Filtering (doc type)                 │
    │  - Relevance Ranking                              │
    └──────────────────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────────────────┐
    │         Embedding + LLM Services                  │
    │  (src/models/embedder.py, llm.py, vlm.py)        │
    │  - HuggingFace Embeddings                         │
    │  - Qwen 0.5B LLM (local)                          │
    │  - LLaVA VLM for images (local)                   │
    └──────────────────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────────────────┐
    │         Ingestion Module                          │
    │  (src/ingestion/parser.py, processor.py)          │
    │  - PyMuPDF for PDF parsing                        │
    │  - Text/Table/Image extraction                    │
    │  - Chunking & Metadata attachment                 │
    └──────────────────────────────────────────────────┘
```

---

## Technology Choices

### Document Parser: **PyMuPDF**
Why: Lightweight, fast, no external dependencies. Docling adds overhead. PyMuPDF efficiently extracts text, tables (via fmt="dict"), and images with precise page numbers.

### Embedding Model: **HuggingFace BGE-small (384-dim)**
Why: 8GB RAM constraint. BGE-small has 33M parameters, runs in <100MB. Superior semantic understanding vs. TF-IDF. Supports multilingual domain terminology.

### Vector Store: **FAISS (IndexFlatL2)**
Why: Local, no external DB needed. IndexFlatL2 sufficient for automotive domain (~10K chunks max). Supports metadata via pickle for source tracking.

### LLM: **Qwen 0.5B (quantized)**
Why: Extreme resource constraint (8GB RAM). Qwen 0.5B is 500M parameters, achieves reasonable quality despite size. With 4-bit quantization, ~2GB memory usage. Sufficient for RAG (doesn't need to know everything, uses retrieval for facts).

### Vision Model: **LLaVA 1.5 (7B, quantized)**
Why: Lightweight opensource VLM. Generates text summaries of engineering diagrams. 7B with 4-bit quantization ~4GB. Can coexist with Qwen.

### Framework: **LangChain + custom**
Why: LangChain handles prompt templating, memory, retriever-generator chains. Custom code where needed for performance optimization given RAM constraints.

### API Framework: **FastAPI**
Why: Requirement. Automatic Swagger docs. Pydantic validation. Async support for I/O-bound operations.

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- 8GB RAM (tight, quantization is critical)
- Git

### Step 1: Clone and Install
```bash
git clone https://github.com/yourusername/automotive-rag-system
cd automotive-rag-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Download Models (First Run Only - Optional)
Models download on-demand during first API call. This takes ~5-10 minutes as models cache locally (~4-5GB).

**Optional pre-download:**
```bash
python src/models/setup_models.py  # Pre-downloads to ~/.cache/huggingface
```

Or just run the server and let it download automatically on first use.

### Step 3: Configure Environment
```bash
cp .env.example .env
# No API keys needed — everything is local!
```

### Step 4: Run the Server
```bash
python main.py
```
Server starts on `http://localhost:8000`

### Step 5: Test the System
```bash
# In another terminal:
curl http://localhost:8000/health

# Upload sample PDF
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample_documents/engine_service_manual.pdf"

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the torque specification for the intake manifold bolts?"}'
```

---

## API Documentation

### 1. GET /health
**Purpose:** System status check

**Response (200 OK):**
```json
{
  "status": "healthy",
  "models_ready": true,
  "indexed_documents": 1,
  "documents": ["engine_service_manual.pdf"],
  "total_chunks": 342,
  "index_size_mb": 2.45,
  "uptime_seconds": 120,
  "available_endpoints": ["/ingest", "/query", "/health"]
}
```

### 2. POST /ingest
**Purpose:** Upload and index a PDF

**Request:**
```bash
Content-Type: multipart/form-data
Body: file (binary PDF)
```

**Response (200 OK):**
```json
{
  "filename": "engine_service_manual.pdf",
  "status": "ingested",
  "extraction_time_seconds": 4.2,
  "chunks_created": {
    "text": 280,
    "table": 45,
    "image": 17
  },
  "total_chunks": 342,
  "indexed": true,
  "message": "PDF successfully indexed and ready for queries"
}
```

**Error Responses:**
- 400: Invalid file format (not PDF)
- 413: File too large (>100MB)
- 500: Processing error

### 3. POST /query
**Purpose:** Query the indexed documents

**Request:**
```json
{
  "query": "What is the coolant temperature specification for the V6 engine?",
  "top_k": 5,
  "include_metadata": true
}
```

**Response (200 OK):**
```json
{
  "query": "What is the coolant temperature specification for the V6 engine?",
  "answer": "The coolant overtemp threshold for the V6 engine (2.5L naturally aspirated) is 110±2°C nominal, with a hard shutdown limit at 115°C. This specification is found in Table 3.2 of the service manual, revision G, page 45.",
  "sources": [
    {
      "filename": "engine_service_manual.pdf",
      "page": 45,
      "chunk_type": "table",
      "chunk_id": "chunk_0087",
      "relevance_score": 0.924,
      "preview": "Engine Coolant Temperature Specifications\n[Table with V4, V6, V8 columns showing temp specs]"
    },
    {
      "filename": "engine_service_manual.pdf",
      "page": 12,
      "chunk_type": "text",
      "chunk_id": "chunk_0012",
      "relevance_score": 0.876,
      "preview": "The cooling system protects the engine by monitoring..."
    }
  ],
  "retrieval_time_ms": 245,
  "generation_time_ms": 1250,
  "total_time_ms": 1495,
  "confidence": "high",
  "note": "Answer grounded in retrieved documents. All specifications sourced from official documentation."
}
```

**Error Responses:**
- 400: Empty query
- 404: No documents indexed
- 500: LLM inference error

### 4. GET /docs
**Purpose:** Interactive Swagger UI

Access at: `http://localhost:8000/docs`

---

## Screenshots

### 1. Swagger UI (/docs)
![Swagger UI showing all endpoints](screenshots/01_swagger_ui.png)

### 2. Successful Ingestion
![POST /ingest response showing chunk counts](screenshots/02_ingest_success.png)

### 3. Text Query Result
![Query response with text chunk retrieval](screenshots/03_text_query.png)

### 4. Table Query Result
![Query response with table chunk retrieval](screenshots/04_table_query.png)

### 5. Image Query Result
![Query response with image summary retrieval](screenshots/05_image_query.png)

### 6. Health Endpoint
![Health check showing document count and index size](screenshots/06_health_status.png)

---

## Project Structure

```
automotive-rag-system/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies (pinned versions)
├── .env.example                       # Environment template
├── .gitignore                         # Excludes: .env, models, __pycache__
│
├── main.py                            # FastAPI app entry point
│
├── src/
│   ├── __init__.py
│   ├── config.py                      # Configuration (model paths, hyperparams)
│   ├── constants.py                   # Domain-specific constants
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py                  # PDF parsing: text, tables, images
│   │   ├── processor.py                # Chunking, metadata attachment
│   │   └── chunk_manager.py            # Chunk storage/retrieval
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── embedder.py                # BGE embeddings
│   │   ├── store.py                   # FAISS vector index
│   │   └── retriever.py               # Query → retrieve chunks
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── llm.py                     # Qwen 0.5B wrapper
│   │   ├── vlm.py                     # LLaVA image summarization
│   │   ├── embedder.py                # (also here for imports)
│   │   └── setup_models.py            # Download/cache models
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py                  # /ingest, /query, /health, /docs
│       ├── schemas.py                 # Pydantic request/response models
│       └── utils.py                   # API helpers
│
├── sample_documents/
│   └── engine_service_manual.pdf      # Sample domain PDF (text + tables + images)
│
├── screenshots/
│   ├── 01_swagger_ui.png
│   ├── 02_ingest_success.png
│   ├── 03_text_query.png
│   ├── 04_table_query.png
│   ├── 05_image_query.png
│   └── 06_health_status.png
│
└── tests/                             # Unit tests (optional but recommended)
    └── test_endpoints.py
```

---

## Limitations & Future Work

### Current Limitations
1. **Query Complexity:** The Qwen 0.5B model struggles with multi-hop reasoning (questions requiring synthesis across 3+ chunks). For complex cases, answers are less reliable.
2. **Image Handling:** LLaVA summaries can miss fine details in complex engineering diagrams. Manual review of image chunks recommended for critical decisions.
3. **Batch Processing:** The system processes one query sequentially. Concurrent queries may hit memory constraints on 8GB systems.
4. **Context Window:** Qwen 0.5B has limited context (2K tokens). Cannot summarize large retrieved chunk sets before generation.

### Future Improvements
1. **Quantization+:** Implement better quantization (2-bit) to free 2GB RAM for larger, higher-quality LLMs
2. **Hierarchical Retrieval:** Implement a two-stage pipeline (semantic search + re-ranking) to improve precision
3. **Multi-Modal Fusion:** Add cross-modal retrieval (e.g., query text, retrieve related images)
4. **Fine-tuning:** Collect domain Q&A pairs and fine-tune embedder on automotive terminology
5. **Caching:** Implement LLM response caching for common questions
6. **REST API:** Expand with authentication, rate limiting, batch APIs for production

---

## Running Tests
```bash
pytest tests/ -v
```

## Troubleshooting

**"CUDA out of memory"** → Ensure quantization is enabled. Check `src/config.py` for `use_4bit_quantization=True`.

**"Vector index is empty"** → Ingest a PDF first via `POST /ingest`.

**"Slow inference (>30s)** → First query hydrates model cache. Subsequent queries ~2-3s. Normal on 8GB systems.

**"ModuleNotFoundError"** → Ensure virtual environment is activated and `pip install -r requirements.txt` completed.

## References & Credits
- [BITS WILP Multimodal RAG Bootcamp](https://www.bits-pilani.ac.in/wilp/)
- [LangChain](https://www.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Ollama for local LLMs](https://ollama.ai/)

---

**Last Updated:** April 2026  
**Status:** Production Ready  
**Author:** Your Name <your.email@example.com>
