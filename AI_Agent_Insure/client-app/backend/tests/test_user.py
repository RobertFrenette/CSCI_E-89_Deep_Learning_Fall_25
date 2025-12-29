"""
Tests for user endpoints
Tests the running container via HTTP requests
"""
import pytest
import httpx
import os

# Get API base URL from environment or default to localhost
API_BASE_URL = os.getenv("CLIENT_BACKEND_URL", "http://localhost:8001")


async def get_auth_token(client: httpx.AsyncClient):
    """Helper to get authentication token"""
    # Register and login with unique email/policy
    await client.post("/api/auth/register", json={
        "username": "policytest_unique",
        "email": "user4739@example.com",
        "password": "testpassword123",
        "policy_number": "PIE5AA9LM"
    })
    
    response = await client.post("/api/auth/login", data={
        "username": "policytest_unique",
        "password": "testpassword123"
    })
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_current_user():
    """Test getting current user profile"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        token = await get_auth_token(client)
        
        response = await client.get(
            "/api/user/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "policytest_unique"
        assert data["email"] == "user4739@example.com"
        # Verify policy_number and insured_id are included
        assert "policy_number" in data
        assert data["policy_number"] == "PIE5AA9LM"
        assert "insured_id" in data
        assert data["insured_id"] is not None


@pytest.mark.asyncio
async def test_get_user_policies():
    """Test getting user's policies"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        token = await get_auth_token(client)
        
        response = await client.get(
            "/api/user/policies",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        policies = response.json()
        assert isinstance(policies, list)
        assert len(policies) > 0
        
        # Check policy structure
        policy = policies[0]
        assert "policy_number" in policy
        assert "policy_type" in policy
        assert "premium_amount" in policy


@pytest.mark.asyncio
async def test_get_policy_details():
    """Test getting specific policy details"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        token = await get_auth_token(client)
        
        # Get user's policies first
        policies_response = await client.get(
            "/api/user/policies",
            headers={"Authorization": f"Bearer {token}"}
        )
        policies = policies_response.json()
        policy_number = policies[0]["policy_number"]
        
        # Get policy details
        response = await client.get(
            f"/api/user/policies/{policy_number}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["policy_number"] == policy_number
        assert "coverage_details" in data


@pytest.mark.asyncio
async def test_get_policy_unauthorized():
    """Test accessing someone else's policy"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        token = await get_auth_token(client)
        
        # Try to access a policy that doesn't belong to this user
        response = await client.get(
            "/api/user/policies/INVALID_POLICY",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test accessing protected endpoints without token"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        response = await client.get("/api/user/me")
        
        assert response.status_code == 401
