"""
Smoke tests for basic endpoint functionality
These tests run during Docker build without requiring real databases
Tests basic app setup and endpoint availability
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio  
async def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/user/me")
        
        assert response.status_code == 401


@pytest.mark.asyncio  
async def test_docs_available():
    """Test that API docs are available"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
        
        assert response.status_code == 200


@pytest.mark.asyncio  
async def test_openapi_schema():
    """Test that OpenAPI schema is available"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]

