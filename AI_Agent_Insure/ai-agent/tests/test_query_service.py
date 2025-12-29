"""
Tests for QueryService integration
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.services.query_service import QueryService
from app.services.postgres_service import PostgreSQLService
from src.rag_engine import RAGEngine


class TestQueryService:
    """Tests for QueryService"""
    
    @pytest.fixture
    def mock_postgres_service(self):
        """Create mock PostgreSQL service"""
        service = Mock(spec=PostgreSQLService)
        return service
    
    @pytest.fixture
    def mock_rag_engine(self):
        """Create mock RAG engine"""
        engine = Mock(spec=RAGEngine)
        engine.query.return_value = {
            "answer": "Test answer from RAG",
            "sources": ["test_doc.pdf"],
            "model": "llama3.1",
            "retrieved_docs": 3,
            "context_length": 500
        }
        return engine
    
    @pytest.fixture
    def query_service_with_postgres(self, mock_postgres_service, mock_rag_engine):
        """Create QueryService with PostgreSQL"""
        return QueryService(
            postgres_service=mock_postgres_service,
            rag_engine=mock_rag_engine
        )
    
    @pytest.fixture
    def query_service_without_postgres(self, mock_rag_engine):
        """Create QueryService without PostgreSQL"""
        return QueryService(
            postgres_service=None,
            rag_engine=mock_rag_engine
        )
    
    @pytest.mark.asyncio
    async def test_sql_query_routing(self, query_service_with_postgres):
        """Test that SQL queries are routed correctly"""
        # Mock SQL query handler response
        from app.routing.sql_query_handler import SQLQueryHandler
        mock_handler = Mock(spec=SQLQueryHandler)
        mock_handler.handle_query.return_value = "There are 100 insureds in the database."
        query_service_with_postgres.sql_query_handler = mock_handler
        
        result = await query_service_with_postgres.process_query("How many insureds are there?", user_id="admin")
        
        assert result["query_type"] == "sql"
        assert "insured" in result["answer"].lower()
        mock_handler.handle_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_query_routing(self, query_service_with_postgres):
        """Test that RAG queries are routed correctly"""
        result = await query_service_with_postgres.process_query("What is AI Agent Insure?")
        
        assert result["query_type"] == "rag"
        assert "answer" in result
        query_service_with_postgres.rag_engine.query.assert_called()
    
    @pytest.mark.asyncio
    async def test_sql_unavailable_fallback(self, query_service_without_postgres):
        """Test that SQL queries fallback gracefully when PostgreSQL is unavailable"""
        result = await query_service_without_postgres.process_query("How many insureds are there?")
        
        # Should still process, but indicate SQL is unavailable
        assert "query_type" in result
        # May route to RAG as fallback or return error message
    
    @pytest.mark.asyncio
    async def test_hybrid_query_processing(self, query_service_with_postgres):
        """Test hybrid query processing"""
        # Mock SQL handler
        from app.routing.sql_query_handler import SQLQueryHandler
        mock_handler = Mock(spec=SQLQueryHandler)
        mock_handler.handle_query.return_value = "Database info: 100 insureds"
        query_service_with_postgres.sql_query_handler = mock_handler
        
        # Test a query that might route to hybrid (admin only)
        result = await query_service_with_postgres.process_query(
            "What is the company's policy on high risk insureds?",
            user_id="admin"
        )
        
        # Should process successfully
        assert "answer" in result
        assert "query_type" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, query_service_with_postgres):
        """Test error handling in query processing"""
        # Make RAG engine raise an error
        query_service_with_postgres.rag_engine.query.side_effect = Exception("Test error")
        
        result = await query_service_with_postgres.process_query("Test query")
        
        assert result["query_type"] == "error" or "error" in result
        assert "answer" in result
    
    @pytest.mark.asyncio
    async def test_admin_user_access(self, query_service_with_postgres):
        """Test that admin user can access all query types"""
        # Mock SQL query handler
        from app.routing.sql_query_handler import SQLQueryHandler
        mock_handler = Mock(spec=SQLQueryHandler)
        mock_handler.handle_query.return_value = "There are 100 insureds."
        query_service_with_postgres.sql_query_handler = mock_handler
        
        # Admin should be able to query SQL
        result = await query_service_with_postgres.process_query(
            "How many insureds are there?",
            user_id="admin"
        )
        
        assert result["query_type"] == "sql"
        mock_handler.handle_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_guest_user_restricted(self, query_service_with_postgres):
        """Test that guest users are restricted to RAG queries"""
        # Mock SQL query handler
        from app.routing.sql_query_handler import SQLQueryHandler
        mock_handler = Mock(spec=SQLQueryHandler)
        query_service_with_postgres.sql_query_handler = mock_handler
        
        # Guest user attempting SQL query should be redirected to RAG
        result = await query_service_with_postgres.process_query(
            "How many insureds are there?",
            user_id="guest"
        )
        
        # Should be redirected to RAG, not SQL
        assert result["query_type"] == "rag"
        # SQL handler should not be called
        mock_handler.handle_query.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticated_user_with_policy(self, query_service_with_postgres):
        """Test that authenticated users can query SQL filtered to their policy"""
        # Mock MongoDB service to return account info
        from app.services.mongodb_service import MongoDBService
        mock_mongo = Mock(spec=MongoDBService)
        mock_mongo.get_account_info_from_username.return_value = {
            "insured_id": "INS001",
            "policy_number": "POL123"
        }
        query_service_with_postgres.mongodb_service = mock_mongo
        
        # Mock SQL query handler
        from app.routing.sql_query_handler import SQLQueryHandler
        mock_handler = Mock(spec=SQLQueryHandler)
        mock_handler.handle_query.return_value = "Your policy information..."
        query_service_with_postgres.sql_query_handler = mock_handler
        
        # Authenticated user should be able to query SQL (filtered to their policy)
        result = await query_service_with_postgres.process_query(
            "What is my policy status?",
            user_id="testuser"
        )
        
        # Should process SQL query with policy_number filtering
        assert result["query_type"] == "sql"
        # Verify handler was called (with optional policy_number parameter)
        mock_handler.handle_query.assert_called()
        # Check that it was called with the query and optionally policy_number
        call_args = mock_handler.handle_query.call_args
        assert call_args is not None
        # The call should include the query and optionally policy_number/insured_id
        assert len(call_args[0]) >= 1  # At least the query string

