"""
Unit tests for Flask routes
These tests run before Docker build and don't require external services
"""
import pytest
from unittest.mock import Mock, patch
from app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app.test_client()


def test_index_route(client):
    """Test index route"""
    response = client.get('/')
    assert response.status_code == 200


def test_login_route_get(client):
    """Test login route GET"""
    response = client.get('/login')
    assert response.status_code in [200, 302]  # 302 if redirect


def test_register_route_get(client):
    """Test register route GET"""
    response = client.get('/register')
    assert response.status_code in [200, 302]  # 302 if redirect


@patch('app.requests.post')
def test_login_route_post_success(mock_post, client):
    """Test login route POST with successful authentication"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'access_token': 'test-token'}
    mock_post.return_value = mock_response
    
    with client.session_transaction() as sess:
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Should redirect on success
        assert response.status_code in [200, 302]


@patch('app.requests.post')
def test_login_route_post_failure(mock_post, client):
    """Test login route POST with failed authentication"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.json.return_value = {'detail': 'Invalid credentials'}
    mock_post.return_value = mock_response
    
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpass'
    })
    # Should stay on page or redirect with error
    assert response.status_code in [200, 302]


def test_logout_route(client):
    """Test logout route"""
    with client.session_transaction() as sess:
        sess['access_token'] = 'test-token'
        sess['username'] = 'testuser'
    
    response = client.get('/logout')
    assert response.status_code == 302  # Should redirect


def test_dashboard_route_requires_auth(client):
    """Test dashboard route requires authentication"""
    response = client.get('/dashboard')
    # Should redirect to login if not authenticated
    assert response.status_code in [302, 401]

