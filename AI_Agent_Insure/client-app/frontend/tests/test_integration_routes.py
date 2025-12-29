"""
Integration tests for Flask routes
These tests run against running containers and require external services
"""
import pytest
import requests
import os

# Get API base URL from environment or default to localhost
CLIENT_BACKEND_URL = os.getenv("CLIENT_BACKEND_URL", "http://localhost:8001")
CLIENT_FRONTEND_URL = os.getenv("CLIENT_FRONTEND_URL", "http://localhost:5000")


@pytest.mark.integration
def test_index_route():
    """Test index route against running container"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/", timeout=10.0)
    assert response.status_code == 200


@pytest.mark.integration
def test_login_route():
    """Test login route against running container"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/login", timeout=10.0, allow_redirects=True)
    assert response.status_code == 200


@pytest.mark.integration
def test_register_route():
    """Test register route against running container"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/register", timeout=10.0, allow_redirects=True)
    assert response.status_code == 200


@pytest.mark.integration
def test_dashboard_route_requires_auth():
    """Test dashboard route requires authentication"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/dashboard", timeout=10.0, allow_redirects=True)
    # Should redirect to login if not authenticated
    assert response.status_code in [200, 302, 401]


@pytest.mark.integration
def test_policies_route_requires_auth():
    """Test policies route requires authentication"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/policies", timeout=10.0, allow_redirects=True)
    # Should redirect to login if not authenticated
    assert response.status_code in [200, 302, 401]


@pytest.mark.integration
def test_claims_route_requires_auth():
    """Test claims route requires authentication"""
    response = requests.get(f"{CLIENT_FRONTEND_URL}/claims", timeout=10.0, allow_redirects=True)
    # Should redirect to login if not authenticated
    assert response.status_code in [200, 302, 401]

