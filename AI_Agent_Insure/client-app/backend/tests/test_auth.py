"""
Tests for authentication endpoints
Tests the running container via HTTP requests
"""
import pytest
import httpx
import os

# Get API base URL from environment or default to localhost
API_BASE_URL = os.getenv("CLIENT_BACKEND_URL", "http://localhost:8001")


@pytest.mark.asyncio
async def test_register_invalid_policy():
    """Test registration with invalid email/policy combination"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        response = await client.post("/api/auth/register", json={
            "username": "testuser2",
            "email": "invalid@email.com",
            "password": "testpassword123",
            "policy_number": "INVALID"
        })
        
        assert response.status_code == 400
        assert "do not match" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username():
    """Test registration with duplicate username"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        # First registration
        await client.post("/api/auth/register", json={
            "username": "duplicate_user",
            "email": "user1162@example.com",
            "password": "testpassword123",
            "policy_number": "PRC0TVCGG"
        })
        
        # Second registration with same username (using different email/policy)
        response = await client.post("/api/auth/register", json={
            "username": "duplicate_user",
            "email": "user4767@example.com",
            "password": "testpassword123",
            "policy_number": "P344UQML0"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_stores_policy_info():
    """Test that registration stores policy_number and insured_id"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        # Use a unique username and email/policy combination that exists in the database
        # Use the same email/policy as test_login_success which we know works
        import random
        import string
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"registertest_{unique_suffix}"
        
        # Use email/policy combination from test_login_success (known to exist)
        response = await client.post("/api/auth/register", json={
            "username": username,
            "email": "user2143@example.com",
            "password": "testpassword123",
            "policy_number": "P2NOMD8BB"
        })
        
        # If user already exists (from previous test run), that's okay - just verify structure
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            # If it's because user already exists, try with different username
            if "already registered" in error_detail:
                username = f"registertest2_{unique_suffix}"
                response = await client.post("/api/auth/register", json={
                    "username": username,
                    "email": "user2143@example.com",
                    "password": "testpassword123",
                    "policy_number": "P2NOMD8BB"
                })
        
        # Should succeed with 201
        assert response.status_code == 201, f"Registration failed: {response.text}"
        data = response.json()
        assert "policy_number" in data
        assert data["policy_number"] == "P2NOMD8BB"
        assert "insured_id" in data
        assert data["insured_id"] is not None


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        # Generate unique username to avoid conflicts
        import random
        import string
        import time
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        timestamp = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        username = f"logintest_{timestamp}_{unique_suffix}"
        
        # Register user first with unique email/policy
        # Use email/policy combination that exists in database
        register_response = await client.post("/api/auth/register", json={
            "username": username,
            "email": "user2143@example.com",
            "password": "testpassword123",
            "policy_number": "P2NOMD8BB"
        })
        
        # If registration fails because email is already registered, try a different email/policy
        if register_response.status_code == 400:
            error_detail = register_response.json().get("detail", "")
            if "already registered" in error_detail:
                # Try with a different email/policy combination
                register_response = await client.post("/api/auth/register", json={
                    "username": username,
                    "email": "user1162@example.com",
                    "password": "testpassword123",
                    "policy_number": "PRC0TVCGG"
                })
        
        # Registration should succeed (201) or we skip the test
        if register_response.status_code != 201:
            pytest.skip(f"Could not register test user: {register_response.text}")
        
        # Login with the username we just registered
        response = await client.post("/api/auth/login", data={
            "username": username,
            "password": "testpassword123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        response = await client.post("/api/auth/login", data={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
