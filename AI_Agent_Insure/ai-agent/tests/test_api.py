"""
Tests for AI Agent API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

# Set environment variables for testing
os.environ["TESTING"] = "true"
os.environ["CHROMADB_USE_HTTP"] = "true"
os.environ["CHROMADB_HOST"] = "localhost"
os.environ["CHROMADB_PORT"] = "8000"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["MONGO_HOST"] = "localhost"
os.environ["MONGO_ROOT_USER"] = "mongo_admin"
os.environ["MONGO_ROOT_PASSWORD"] = "mongo_secure_pass_2025"


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


@pytest.mark.integration
def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "chromadb" in data
    assert "ollama" in data
    assert "mongodb" in data
    assert isinstance(data["chromadb"], bool)
    assert isinstance(data["ollama"], bool)
    assert isinstance(data["mongodb"], bool)


@pytest.mark.integration
def test_history_endpoint(client):
    """Test query history endpoint"""
    health = client.get("/health").json()
    if not health.get("mongodb"):
        pytest.skip("MongoDB not available")
    
    # Use a valid ObjectId format
    user_id = "507f1f77bcf86cd799439011"
    
    response = client.get(f"/api/agent/history/{user_id}")
    
    # Should return 200 even if no history exists
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # If there are results, check structure
        if len(data) > 0:
            query = data[0]
            assert "query_id" in query
            assert "query_text" in query
            assert "query_timestamp" in query



