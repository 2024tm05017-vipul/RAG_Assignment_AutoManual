"""Domain-specific constants for Automotive Quality Control"""

# Automotive Technical Specifications
AUTOMOTIVE_SPECS = {
    "engine_types": ["V4", "V6", "V8", "I4", "Diesel", "Turbocharged"],
    "temperature_units": ["°C", "°F", "K"],
    "pressure_units": ["PSI", "bar", "kPa", "MPa"],
    "torque_units": ["Nm", "ft-lb", "kg-cm"],
    "volume_units": ["mL", "L", "cc"],
}

# Common Automotive Quality Parameters
QUALITY_PARAMETERS = [
    "torque_specification",
    "temperature_limit",
    "pressure_range",
    "fluid_capacity",
    "tolerance_level",
    "service_interval",
    "safety_limit",
    "diagnostic_code",
]

# RAG System Prompts
RAG_PROMPT_TEMPLATE = """You are an expert automotive quality control consultant with deep knowledge of service manuals and specifications.

Based on the following retrieved documents from an official service manual, answer the question precisely and concisely.

RETRIEVED CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer ONLY using information from the retrieved context
2. If the answer requires a specification, include exact values with units
3. Always cite the source (page number, section) at the end
4. If information is not in the retrieved context, say "Not found in available documentation"
5. For safety-critical specifications, emphasize they must be verified in official documentation

ANSWER:"""

# Image Analysis Prompt
IMAGE_ANALYSIS_PROMPT = """Analyze this automotive engineering diagram/image and provide a concise technical summary.

Include:
1. Main components shown
2. Key assembly sequence (if applicable)
3. Any performance specifications visible
4. Safety considerations

Keep summary to 100-150 words. Use technical automotive terminology."""

# Health Check Response
DEFAULT_HEALTH_RESPONSE = {
    "status": "healthy",
    "models_ready": True,
    "indexed_documents": 0,
    "documents": [],
    "total_chunks": 0,
    "index_size_mb": 0.0,
    "uptime_seconds": 0,
    "available_endpoints": ["/ingest", "/query", "/health", "/docs"]
}

# Error Messages
ERROR_MESSAGES = {
    "no_documents": "No documents indexed. Please upload a PDF via POST /ingest first.",
    "invalid_file": "Invalid file format. Only PDF files are supported.",
    "empty_query": "Query cannot be empty.",
    "llm_error": "Error generating response from LLM. Check logs.",
    "retrieval_error": "Error retrieving documents from index.",
    "ingestion_error": "Error processing PDF during ingestion.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "ingest_success": "{filename} successfully indexed with {total_chunks} chunks",
    "query_success": "Query completed successfully",
    "health_ok": "System healthy and ready",
}
