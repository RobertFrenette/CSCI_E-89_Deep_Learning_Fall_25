"""
Unit tests for Flask routes
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
from app import app as flask_app


def test_index_redirects_to_login_when_not_authenticated(client):
    """Test that index redirects to login when user is not logged in"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location


def test_index_redirects_to_dashboard_when_authenticated(client):
    """Test that index redirects to dashboard when user is logged in"""
    with client.session_transaction() as sess:
        sess['access_token'] = 'test-token'
        sess['username'] = 'testuser'
    
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.location


def test_login_page_loads(client):
    """Test that login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Welcome Back' in response.data
    assert b'Sign in to your account' in response.data


def test_login_with_valid_credentials(client):
    """Test successful login"""
    with patch('app.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test-token',
            'token_type': 'bearer'
        }
        mock_post.return_value = mock_response
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert '/dashboard' in response.location
        with client.session_transaction() as sess:
            assert sess['access_token'] == 'test-token'
            assert sess['username'] == 'testuser'


def test_login_with_invalid_credentials(client):
    """Test login with invalid credentials"""
    with patch('app.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'detail': 'Incorrect username or password'
        }
        mock_post.return_value = mock_response
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200
        assert b'Incorrect username or password' in response.data


def test_register_page_loads(client):
    """Test that register page loads successfully"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data


def test_register_success(client):
    """Test successful registration"""
    with patch('app.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            '_id': '123'
        }
        mock_post.return_value = mock_response
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'policy_number': 'POL123'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert '/login' in response.location


def test_register_validation_error(client):
    """Test registration with validation error"""
    with patch('app.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'detail': 'Email and policy number do not match our records'
        }
        mock_post.return_value = mock_response
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'invalid@example.com',
            'password': 'testpass123',
            'policy_number': 'INVALID'
        })
        
        assert response.status_code == 200
        assert b'Email and policy number do not match' in response.data


def test_logout_clears_session(client):
    """Test that logout clears session"""
    with client.session_transaction() as sess:
        sess['access_token'] = 'test-token'
        sess['username'] = 'testuser'
    
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location
    
    with client.session_transaction() as sess:
        assert 'access_token' not in sess
        assert 'username' not in sess


def test_dashboard_requires_login(client):
    """Test that dashboard requires authentication"""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


def test_dashboard_loads_when_authenticated(client):
    """Test that dashboard loads when user is authenticated"""
    with patch('app.requests.get') as mock_get:
        # Mock user profile response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            'username': 'testuser',
            'email': 'test@example.com',
            '_id': '123'
        }
        
        # Mock policies response
        policies_response = MagicMock()
        policies_response.status_code = 200
        policies_response.json.return_value = []
        
        mock_get.side_effect = [user_response, policies_response]
        
        with client.session_transaction() as sess:
            sess['access_token'] = 'test-token'
            sess['username'] = 'testuser'
        
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Welcome' in response.data


def test_policies_requires_login(client):
    """Test that policies page requires authentication"""
    response = client.get('/policies', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


def test_profile_requires_login(client):
    """Test that profile page requires authentication"""
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


def test_claims_requires_login(client):
    """Test that claims page requires authentication"""
    response = client.get('/claims', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

