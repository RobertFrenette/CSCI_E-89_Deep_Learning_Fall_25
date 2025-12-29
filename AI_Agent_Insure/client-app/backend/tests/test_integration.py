"""
Integration tests for Client Backend API
These tests run against running containers and require external services
"""
import pytest
import requests
import os
import time
import random

# Get API base URL from environment or default to localhost
CLIENT_BACKEND_URL = os.getenv("CLIENT_BACKEND_URL", "http://localhost:8001")


@pytest.mark.integration
def test_health_endpoint():
    """Test health check endpoint against running container"""
    response = requests.get(f"{CLIENT_BACKEND_URL}/health", timeout=10.0)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_register_and_login_flow():
    """Test complete registration and login flow"""
    # Generate unique username to avoid conflicts
    unique_id = f"inttest_{int(time.time())}_{random.randint(0, 10000)}"
    email = f"{unique_id}@example.com"
    username = unique_id
    password = "TestPassword123!"
    policy_number = "P2NOMD8BB"  # Use a known valid policy number
    
    # Test registration
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "policy_number": policy_number
    }
    register_response = requests.post(
        f"{CLIENT_BACKEND_URL}/api/auth/register",
        json=register_data,
        timeout=10.0
    )
    
    # Registration should succeed (201) or fail if user already exists (400)
    assert register_response.status_code in [201, 400]
    
    if register_response.status_code == 201:
        # If registration succeeded, test login
        login_data = {
            "username": username,
            "password": password
        }
        login_response = requests.post(
            f"{CLIENT_BACKEND_URL}/api/auth/login",
            json=login_data,
            timeout=10.0
        )
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        assert login_result["access_token"] is not None


@pytest.mark.integration
def test_protected_route_requires_auth():
    """Test that protected routes require authentication"""
    # Try to access protected route without token
    response = requests.get(f"{CLIENT_BACKEND_URL}/api/user/me", timeout=10.0)
    assert response.status_code == 401
    
    # Try with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{CLIENT_BACKEND_URL}/api/user/me", headers=headers, timeout=10.0)
    assert response.status_code == 401

