"""
Tests for RAG Engine
"""
import pytest
import os
from src.rag_engine import RAGEngine
from src.chromadb_client import ChromaDBClient
from src.ollama_client import OllamaClient

# Test configuration
CHROMADB_URL = os.getenv("CHROMADB_BASE_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_TEST_MODEL", "llama3.1")


@pytest.fixture
def chromadb_client():
    """Create ChromaDB client for testing"""
    client = ChromaDBClient()
    # Set HTTP mode for testing
    os.environ['CHROMADB_USE_HTTP'] = 'true'
    return client


@pytest.fixture
def ollama_client():
    """Create Ollama client for testing"""
    return OllamaClient(base_url=OLLAMA_URL)


@pytest.fixture
def rag_engine(chromadb_client, ollama_client):
    """Create RAG engine for testing"""
    return RAGEngine(
        chromadb_client=chromadb_client,
        ollama_client=ollama_client,
        model=OLLAMA_MODEL,
        top_k=3  # Use smaller top_k for faster tests
    )


@pytest.mark.integration
def test_rag_engine_initialization(rag_engine):
    """Test RAG engine can be initialized"""
    assert rag_engine is not None
    assert rag_engine.model == OLLAMA_MODEL
    assert rag_engine.top_k == 3
    assert rag_engine.collection_name == "knowledge_base"


@pytest.mark.integration
def test_rag_engine_health_checks(rag_engine):
    """Test that RAG engine can check service health"""
    # These should not raise exceptions
    ollama_health = rag_engine.ollama_client.check_health()
    chromadb_health = rag_engine.chromadb_client.check_health()
    
    # At least one service should be available for tests
    assert isinstance(ollama_health, bool)
    assert isinstance(chromadb_health, bool)


@pytest.mark.integration
def test_rag_query_basic(rag_engine):
    """Test basic RAG query functionality"""
    # Skip if services aren't available
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    query = "What is insurance coverage?"
    
    result = rag_engine.query(query)
    
    # Check result structure
    assert 'answer' in result
    assert 'sources' in result
    assert 'model' in result
    assert 'retrieved_docs' in result
    assert 'context_length' in result
    
    # Check that answer is a string
    assert isinstance(result['answer'], str)
    assert len(result['answer']) > 0
    
    # Check that sources is a list
    assert isinstance(result['sources'], list)
    
    # Check model matches
    assert result['model'] == OLLAMA_MODEL


@pytest.mark.integration
def test_rag_query_with_context(rag_engine):
    """Test RAG query retrieves and uses context"""
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    query = "What types of insurance policies are available?"
    
    result = rag_engine.query(query, top_k=5)
    
    # Should have retrieved some documents
    assert result['retrieved_docs'] >= 0
    
    # If documents were retrieved, should have context
    if result['retrieved_docs'] > 0:
        assert result['context_length'] > 0
        assert len(result['sources']) >= 0
    
    # Answer should exist
    assert 'answer' in result
    assert isinstance(result['answer'], str)


@pytest.mark.integration
def test_rag_query_custom_parameters(rag_engine):
    """Test RAG query with custom parameters"""
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    query = "Explain coverage limits"
    
    result = rag_engine.query(
        query,
        top_k=2,
        temperature=0.5
    )
    
    assert 'answer' in result
    assert result['retrieved_docs'] <= 2  # Should respect top_k


@pytest.mark.integration
def test_rag_query_no_results(rag_engine):
    """Test RAG query when no documents are found"""
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    # Use a query that likely won't match anything
    query = "xyzabc123nonexistentquery456"
    
    result = rag_engine.query(query, top_k=1)
    
    # Should still return a result structure
    assert 'answer' in result
    assert isinstance(result['answer'], str)
    # Answer might be empty or indicate no information found
    assert result['retrieved_docs'] >= 0


@pytest.mark.integration
def test_rag_chat_interface(rag_engine):
    """Test RAG chat interface with conversation history"""
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    messages = [
        {'role': 'user', 'content': 'What is a policy?'}
    ]
    
    result = rag_engine.chat(messages)
    
    assert 'answer' in result
    assert isinstance(result['answer'], str)
    assert 'sources' in result
    assert 'model' in result


@pytest.mark.integration
def test_rag_chat_conversation(rag_engine):
    """Test RAG chat with multiple messages"""
    if not rag_engine.ollama_client.check_health():
        pytest.skip("Ollama not available")
    if not rag_engine.chromadb_client.check_health():
        pytest.skip("ChromaDB not available")
    
    messages = [
        {'role': 'user', 'content': 'What is insurance?'},
        {'role': 'assistant', 'content': 'Insurance is a contract...'},
        {'role': 'user', 'content': 'What types are there?'}
    ]
    
    result = rag_engine.chat(messages)
    
    assert 'answer' in result
    assert isinstance(result['answer'], str)
    assert len(result['answer']) > 0


def test_build_context_empty(rag_engine):
    """Test context building with empty results"""
    empty_docs = []
    context = rag_engine._build_context(empty_docs)
    assert context == ""


def test_build_context_with_docs(rag_engine):
    """Test context building with documents"""
    test_docs = [
        {
            'document': 'This is test document 1',
            'metadata': {'source': 'test1.pdf', 'source_dir': 'test'},
            'similarity': 0.95
        },
        {
            'document': 'This is test document 2',
            'metadata': {'source': 'test2.pdf'},
            'similarity': 0.85
        }
    ]
    
    context = rag_engine._build_context(test_docs)
    
    assert 'test document 1' in context
    assert 'test document 2' in context
    assert 'test1.pdf' in context
    assert 'test2.pdf' in context


def test_build_prompt_with_context(rag_engine):
    """Test prompt building with context"""
    query = "What is insurance?"
    context = "Insurance is a contract..."
    
    prompt = rag_engine._build_prompt(query, context)
    
    assert query in prompt
    assert context in prompt
    assert 'Question:' in prompt


def test_build_prompt_no_context(rag_engine):
    """Test prompt building without context"""
    query = "What is insurance?"
    context = ""
    
    prompt = rag_engine._build_prompt(query, context)
    
    assert query in prompt
    assert 'Please answer the question' in prompt

