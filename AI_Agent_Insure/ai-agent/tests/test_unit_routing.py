"""
Unit tests for query routing logic
These tests run before Docker build and don't require external services
"""
import pytest
from app.routing.query_router import detect_query_type
from app.routing.constants import SQL_INDICATORS, RAG_INDICATORS, MONGO_INDICATORS


def test_detect_query_type_sql_prefix():
    """Test SQL prefix detection"""
    query_type, cleaned = detect_query_type("DB: How many insureds?")
    assert query_type == "sql"
    assert cleaned == "How many insureds?"


def test_detect_query_type_sql_indicators():
    """Test SQL query detection via indicators"""
    query_type, _ = detect_query_type("How many insureds are there in the database?")
    assert query_type == "sql"


def test_detect_query_type_rag_indicators():
    """Test RAG query detection via indicators"""
    query_type, _ = detect_query_type("What is AI Agent Insure?")
    assert query_type == "rag"


def test_detect_query_type_mongo_indicators():
    """Test MongoDB query detection via indicators"""
    query_type, _ = detect_query_type("How many registered users are there?")
    assert query_type == "mongo"


def test_detect_query_type_hybrid():
    """Test hybrid query detection"""
    query_type, _ = detect_query_type("Show me high risk policies and what coverage they have")
    # Should detect both SQL and RAG indicators
    assert query_type in ["hybrid", "sql", "rag"]


def test_detect_query_type_default_rag():
    """Test default routing to RAG for ambiguous queries"""
    query_type, _ = detect_query_type("Tell me about insurance")
    assert query_type == "rag"


def test_detect_query_type_case_insensitive():
    """Test case insensitive detection"""
    query_type1, _ = detect_query_type("HOW MANY INSUREDS?")
    query_type2, _ = detect_query_type("how many insureds?")
    assert query_type1 == query_type2


def test_detect_query_type_cleaned_output():
    """Test that cleaned query removes prefix"""
    query_type, cleaned = detect_query_type("database: count policies")
    assert query_type == "sql"
    assert "database:" not in cleaned.lower()
    assert "count policies" in cleaned.lower()

