"""
Pytest configuration and fixtures for Flask app tests
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


@pytest.fixture
def mock_api_response(monkeypatch):
    """Fixture to mock API responses"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        return MockResponse(200, {})
    
    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        return MockResponse(200, {})
    
    import requests
    monkeypatch.setattr(requests, 'get', mock_get)
    monkeypatch.setattr(requests, 'post', mock_post)

