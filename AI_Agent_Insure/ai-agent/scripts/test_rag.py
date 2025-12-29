#!/usr/bin/env python3
"""
Test script for RAG Engine
Tests the complete RAG pipeline end-to-end
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_engine import RAGEngine
from src.chromadb_client import ChromaDBClient
from src.ollama_client import OllamaClient

# Configuration
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Set HTTP mode for ChromaDB
os.environ['CHROMADB_USE_HTTP'] = 'true'


def test_services():
    """Test that required services are available"""
    print("🔍 Checking services...")
    
    # Check ChromaDB
    chromadb_client = ChromaDBClient()
    if chromadb_client.check_health():
        print("✅ ChromaDB is accessible")
    else:
        print("❌ ChromaDB is not accessible")
        return False
    
    # Check Ollama
    ollama_client = OllamaClient(base_url=OLLAMA_BASE_URL)
    if ollama_client.check_health():
        print("✅ Ollama is accessible")
        models = ollama_client.list_models()
        if models:
            print(f"   Available models: {', '.join(models)}")
        else:
            print("   ⚠️  No models found in Ollama")
    else:
        print("❌ Ollama is not accessible")
        return False
    
    return True


def test_rag_query(rag_engine, query: str):
    """Test a single RAG query"""
    print(f"\n📝 Query: {query}")
    print("⏳ Processing...")
    
    try:
        result = rag_engine.query(query, top_k=5)
        
        print(f"\n✅ Answer ({len(result['answer'])} chars):")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)
        
        print(f"\n📊 Metadata:")
        print(f"   - Model: {result['model']}")
        print(f"   - Retrieved documents: {result['retrieved_docs']}")
        print(f"   - Context length: {result['context_length']} chars")
        
        if result['sources']:
            print(f"   - Sources: {', '.join(result['sources'][:3])}")
            if len(result['sources']) > 3:
                print(f"     ... and {len(result['sources']) - 3} more")
        
        if 'error' in result:
            print(f"   ⚠️  Error: {result['error']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("=" * 80)
    print("RAG Engine Test Script")
    print("=" * 80)
    
    # Check services
    if not test_services():
        print("\n❌ Service checks failed. Please ensure ChromaDB and Ollama are running.")
        sys.exit(1)
    
    # Initialize RAG engine
    print("\n🚀 Initializing RAG Engine...")
    try:
        chromadb_client = ChromaDBClient()
        ollama_client = OllamaClient(base_url=OLLAMA_BASE_URL)
        rag_engine = RAGEngine(
            chromadb_client=chromadb_client,
            ollama_client=ollama_client,
            model=MODEL,
            top_k=5
        )
        print("✅ RAG Engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize RAG Engine: {e}")
        sys.exit(1)
    
    # Test queries
    test_queries = [
        "What is insurance coverage?",
        "What types of insurance policies are available?",
        "How do I file a claim?",
        "What is the claims process?",
    ]
    
    print(f"\n🧪 Running {len(test_queries)} test queries...")
    print("=" * 80)
    
    success_count = 0
    for query in test_queries:
        if test_rag_query(rag_engine, query):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"📊 Test Summary: {success_count}/{len(test_queries)} queries succeeded")
    print("=" * 80)
    
    if success_count == len(test_queries):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

