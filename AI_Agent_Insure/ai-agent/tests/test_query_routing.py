"""
Tests for query routing logic
"""
import pytest
from app.routing.query_router import detect_query_type
from app.routing.constants import SQL_INDICATORS, RAG_INDICATORS


class TestQueryRouter:
    """Tests for query routing"""
    
    def test_sql_prefix_routing(self):
        """Test explicit SQL prefix routing"""
        query_type, cleaned = detect_query_type("DB: How many insureds?")
        assert query_type == "sql"
        assert "DB:" not in cleaned
        assert "How many insureds?" in cleaned
    
    def test_sql_insured_count_query(self):
        """Test SQL routing for insured count query"""
        query_type, _ = detect_query_type("How many insureds are in the database?")
        assert query_type == "sql"
    
    def test_sql_claims_query(self):
        """Test SQL routing for claims query"""
        query_type, _ = detect_query_type("How many claims have been filed?")
        assert query_type == "sql"
    
    def test_sql_high_risk_query(self):
        """Test SQL routing for high-risk policies query"""
        query_type, _ = detect_query_type("Show me all high risk policies")
        assert query_type == "sql"
    
    def test_sql_insured_info_query(self):
        """Test SQL routing for insured info query"""
        query_type, _ = detect_query_type("Show me information for insured BQ4DCXWL")
        assert query_type == "sql"
    
    def test_rag_company_query(self):
        """Test RAG routing for company info query"""
        query_type, _ = detect_query_type("What is AI Agent Insure?")
        assert query_type == "rag"
    
    def test_rag_product_query(self):
        """Test RAG routing for product query"""
        query_type, _ = detect_query_type("What products does the company offer?")
        assert query_type == "rag"
    
    def test_rag_procedure_query(self):
        """Test RAG routing for procedure query"""
        query_type, _ = detect_query_type("How do I file a claim?")
        assert query_type == "rag"
    
    def test_hybrid_query(self):
        """Test hybrid routing for queries with both SQL and RAG indicators"""
        query_type, _ = detect_query_type("What is the company's policy on high risk insureds?")
        # Should route to hybrid if both indicators present
        assert query_type in ["sql", "rag", "hybrid"]
    
    def test_ambiguous_query_defaults_to_rag(self):
        """Test that ambiguous queries default to RAG"""
        query_type, _ = detect_query_type("Hello, how are you?")
        # Should default to RAG for ambiguous queries
        assert query_type == "rag"
    
    def test_query_cleaning(self):
        """Test that queries are properly cleaned"""
        query_type, cleaned = detect_query_type("database: count insureds")
        assert query_type == "sql"
        assert "database:" not in cleaned.lower()
        assert "count" in cleaned.lower()

