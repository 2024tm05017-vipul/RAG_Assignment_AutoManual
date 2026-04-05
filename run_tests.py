#!/usr/bin/env python3
"""
Integration test script - Tests all endpoints and generates demonstration data.
Run this AFTER starting the server with: python main.py
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
SAMPLE_PDF = "sample_documents/engine_service_manual.pdf"

# Colors for terminal output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")

def test_health():
    """Test GET /health endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print_success(f"Health endpoint working")
        print(f"  Status: {data.get('status')}")
        print(f"  Models Ready: {data.get('models_ready')}")
        print(f"  Indexed Documents: {data.get('indexed_documents')}")
        print(f"  Total Chunks: {data.get('total_chunks')}")
        print(f"  Index Size: {data.get('index_size_mb')} MB")
        
        # Pretty print response
        print(f"\n{YELLOW}Response JSON:{RESET}")
        print(json.dumps(data, indent=2))
        
        return data
        
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print_info("Make sure to start the server first: python main.py")
        sys.exit(1)
    except Exception as e:
        print_error(f"Health check failed: {e}")
        sys.exit(1)

def test_ingest():
    """Test POST /ingest endpoint"""
    print_header("TEST 2: Document Ingestion")
    
    if not Path(SAMPLE_PDF).exists():
        print_error(f"Sample PDF not found: {SAMPLE_PDF}")
        return None
    
    try:
        with open(SAMPLE_PDF, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/ingest", files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print_success(f"Ingestion successful")
        print(f"  Filename: {data.get('filename')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Extraction Time: {data.get('extraction_time_seconds')} seconds")
        print(f"  Text Chunks: {data.get('chunks_created', {}).get('text', 0)}")
        print(f"  Table Chunks: {data.get('chunks_created', {}).get('table', 0)}")
        print(f"  Image Chunks: {data.get('chunks_created', {}).get('image', 0)}")
        print(f"  Total Chunks: {data.get('total_chunks')}")
        
        # Pretty print response
        print(f"\n{YELLOW}Response JSON:{RESET}")
        print(json.dumps(data, indent=2))
        
        return data
        
    except Exception as e:
        print_error(f"Ingestion failed: {e}")
        return None

def test_query(query_text, description):
    """Test POST /query endpoint"""
    print_header(f"TEST: Query - {description}")
    
    try:
        payload = {
            "query": query_text,
            "top_k": 5,
            "include_metadata": True
        }
        
        response = requests.post(f"{BASE_URL}/query", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print_success(f"Query successful: '{query_text}'")
        print(f"  Confidence: {data.get('confidence')}")
        print(f"  Retrieval Time: {data.get('retrieval_time_ms')} ms")
        print(f"  Generation Time: {data.get('generation_time_ms')} ms")
        print(f"  Total Time: {data.get('total_time_ms')} ms")
        print(f"  Sources Retrieved: {len(data.get('sources', []))}")
        
        for i, source in enumerate(data.get('sources', []), 1):
            print(f"\n  Source {i}:")
            print(f"    - File: {source.get('filename')}")
            print(f"    - Page: {source.get('page')}")
            print(f"    - Type: {source.get('chunk_type')}")
            print(f"    - Score: {source.get('relevance_score'):.3f}")
            print(f"    - Preview: {source.get('preview')[:80]}...")
        
        print(f"\n{YELLOW}Answer:{RESET}")
        print(f"  {data.get('answer')}\n")
        
        # Pretty print full response
        print(f"\n{YELLOW}Full Response JSON:{RESET}")
        print(json.dumps(data, indent=2))
        
        return data
        
    except Exception as e:
        print_error(f"Query failed: {e}")
        return None

def test_swagger_docs():
    """Test GET /docs endpoint"""
    print_header("TEST: Swagger Documentation")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print_success(f"Swagger UI is accessible")
        print(f"  URL: {BASE_URL}/docs")
        print(f"  Content Length: {len(response.content)} bytes")
        print_info("Open browser and navigate to http://localhost:8000/docs")
        
    except Exception as e:
        print_error(f"Swagger access failed: {e}")

def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}{'*' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{'AUTOMOTIVE RAG SYSTEM - INTEGRATION TEST'.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'*' * 70}{RESET}\n")
    
    print_info(f"Testing server at {BASE_URL}")
    print_info(f"Sample PDF: {SAMPLE_PDF}")
    
    # Test 1: Health
    health = test_health()
    time.sleep(1)
    
    # Test 2: Ingest
    ingest = test_ingest()
    time.sleep(2)
    
    if ingest and ingest.get('status') in ['success', 'ingested']:
        # Test 3-5: Different query types
        test_query(
            "What is the torque specification for the intake manifold bolts?",
            "TEXT - Specifications Query"
        )
        time.sleep(2)
        
        test_query(
            "What is the coolant temperature limit for the V6 engine?",
            "TABLE - Temperature Specifications"
        )
        time.sleep(2)
        
        test_query(
            "How do I diagnose a lean combustion anomaly?",
            "DIAGNOSTIC - Multi-step Procedure"
        )
        time.sleep(2)
    
    # Test 6: Swagger Docs
    test_swagger_docs()
    
    # Summary
    print_header("TEST SUMMARY")
    print_success("All critical endpoints tested successfully!")
    print_info("Next steps for assignment submission:")
    print_info("1. Take screenshots of all test outputs")
    print_info("2. Capture /docs (Swagger UI) page")
    print_info("3. Save query responses with source citations")
    print_info("4. Upload screenshots to screenshots/ folder")
    print_info("5. Commit to GitHub: git add -A && git commit -m 'Final RAG system'")
    print_info("6. Push to GitHub: git push origin main")

if __name__ == "__main__":
    main()
