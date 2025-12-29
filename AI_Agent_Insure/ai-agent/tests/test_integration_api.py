"""
Integration tests for AI Agent API endpoints
These tests run against running containers and test component integration.
"""
import pytest
import httpx
import os

# Get API base URL from environment or default to localhost
API_BASE_URL = os.getenv("AI_AGENT_URL", "http://localhost:8002")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check endpoint against running container"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "chromadb" in data
        assert "ollama" in data
        assert "mongodb" in data

