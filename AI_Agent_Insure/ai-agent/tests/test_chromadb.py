"""
Tests for ChromaDB vector store operations
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chromadb_client import ChromaDBClient
from src.vector_search import VectorSearch


@pytest.fixture
def chromadb_client():
    """Create a ChromaDB client for testing"""
    client = ChromaDBClient()
    yield client
    # Cleanup: delete test collection if it exists
    try:
        client.delete_collection("test_collection")
    except:
        pass


@pytest.fixture
def test_documents():
    """Sample documents for testing"""
    return [
        "AI Agent Insurance provides coverage for autonomous AI systems.",
        "RAG systems use vector databases to store embeddings.",
        "ChromaDB is a vector database for AI applications.",
        "Insurance policies protect against AI-related risks.",
        "Vector search enables semantic similarity matching."
    ]


@pytest.fixture
def test_metadata():
    """Sample metadata for testing"""
    return [
        {"source": "test1.pdf", "category": "insurance"},
        {"source": "test2.pdf", "category": "technology"},
        {"source": "test3.pdf", "category": "technology"},
        {"source": "test4.pdf", "category": "insurance"},
        {"source": "test5.pdf", "category": "technology"}
    ]


class TestChromaDBClient:
    """Tests for ChromaDBClient"""
    
    def test_check_health(self, chromadb_client):
        """Test health check"""
        assert chromadb_client.check_health() is True
    
    def test_get_or_create_collection(self, chromadb_client):
        """Test collection creation"""
        collection = chromadb_client.get_or_create_collection("test_collection")
        assert collection is not None
    
    def test_add_documents(self, chromadb_client, test_documents, test_metadata):
        """Test adding documents to collection"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        count = chromadb_client.get_collection_count("test_collection")
        assert count == len(test_documents)
    
    def test_query(self, chromadb_client, test_documents, test_metadata):
        """Test querying the vector store"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        results = chromadb_client.query(
            collection_name="test_collection",
            query_texts=["What is AI insurance?"],
            n_results=3
        )
        
        assert results is not None
        assert "ids" in results
        assert len(results["ids"][0]) > 0
    
    def test_get_collection_count(self, chromadb_client, test_documents, test_metadata):
        """Test getting collection count"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        count = chromadb_client.get_collection_count("test_collection")
        assert count == len(test_documents)
    
    def test_list_collections(self, chromadb_client):
        """Test listing collections"""
        # Create a test collection
        chromadb_client.get_or_create_collection("test_list_collection")
        
        collections = chromadb_client.list_collections()
        assert "test_list_collection" in collections or "test_collection" in collections


class TestVectorSearch:
    """Tests for vector search"""
    
    def test_search(self, chromadb_client, test_documents, test_metadata):
        """Test similarity search"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        search = VectorSearch(chromadb_client)
        results = search.search(
            query="AI insurance coverage",
            collection_name="test_collection",
            n_results=3
        )
        
        assert len(results) > 0
        assert all("document" in r for r in results)
        assert all("metadata" in r for r in results)
    
    def test_search_with_filter(self, chromadb_client, test_documents, test_metadata):
        """Test search with metadata filter"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        search = VectorSearch(chromadb_client)
        results = search.search(
            query="technology",
            collection_name="test_collection",
            n_results=5,
            metadata_filter={"category": "technology"}
        )
        
        assert len(results) > 0
        # All results should have category=technology
        assert all(r["metadata"].get("category") == "technology" for r in results)
    
    def test_get_collection_stats(self, chromadb_client, test_documents, test_metadata):
        """Test getting collection statistics"""
        ids = [f"doc_{i}" for i in range(len(test_documents))]
        
        chromadb_client.add_documents(
            collection_name="test_collection",
            documents=test_documents,
            metadatas=test_metadata,
            ids=ids
        )
        
        search = VectorSearch(chromadb_client)
        stats = search.get_collection_stats("test_collection")
        
        assert stats["collection_name"] == "test_collection"
        assert stats["document_count"] == len(test_documents)
        assert stats["unique_sources"] > 0

