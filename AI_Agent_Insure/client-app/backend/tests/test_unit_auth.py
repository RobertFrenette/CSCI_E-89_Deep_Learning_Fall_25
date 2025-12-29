"""
Unit tests for authentication module
These tests run before Docker build and don't require external services
"""
import pytest
from unittest.mock import Mock, patch
from app.auth import create_access_token, verify_password, get_password_hash
from datetime import timedelta


def test_create_access_token():
    """Test access token creation"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expires():
    """Test access token creation with custom expiration"""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=expires_delta)
    
    assert token is not None
    assert isinstance(token, str)


def test_verify_password():
    """Test password verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_get_password_hash():
    """Test password hashing"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed is not None
    assert isinstance(hashed, str)
    assert hashed != password
    assert len(hashed) > 0

