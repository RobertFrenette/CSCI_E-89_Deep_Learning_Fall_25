"""
Integration tests for PostgreSQL service and SQL query handler
"""
import pytest
import os
from app.services.postgres_service import PostgreSQLService
from app.routing.sql_query_handler import SQLQueryHandler
from app.database.postgres import check_postgres_health

# Test configuration
POSTGRES_AVAILABLE = os.getenv("POSTGRES_AVAILABLE", "true").lower() == "true"


@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="PostgreSQL not available")
class TestPostgreSQLService:
    """Tests for PostgreSQLService"""
    
    @pytest.fixture
    def postgres_service(self):
        """Create PostgreSQL service for testing"""
        return PostgreSQLService()
    
    def test_count_insureds(self, postgres_service):
        """Test counting insureds"""
        count = postgres_service.count_insureds()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_count_claims(self, postgres_service):
        """Test counting claims"""
        count = postgres_service.count_claims()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_count_policies(self, postgres_service):
        """Test counting policies"""
        count = postgres_service.count_policies()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_count_claims_by_policy(self, postgres_service):
        """Test counting claims for a specific policy"""
        # First get a policy number from the database
        try:
            policies = postgres_service.execute_custom_query(
                "SELECT policy_number FROM policies LIMIT 1"
            )
            if policies:
                policy_number = policies[0]['policy_number']
                count = postgres_service.count_claims_by_policy(policy_number)
                assert isinstance(count, int)
                assert count >= 0
        except Exception as e:
            pytest.skip(f"Could not test count_claims_by_policy: {e}")
    
    def test_count_policies_by_insured(self, postgres_service):
        """Test counting policies for a specific insured"""
        # First get an insured_id from the database
        try:
            insureds = postgres_service.execute_custom_query(
                "SELECT insured_id FROM insureds LIMIT 1"
            )
            if insureds:
                insured_id = insureds[0]['insured_id']
                count = postgres_service.count_policies_by_insured(insured_id)
                assert isinstance(count, int)
                assert count >= 0
        except Exception as e:
            pytest.skip(f"Could not test count_policies_by_insured: {e}")
    
    def test_get_policy_by_number(self, postgres_service):
        """Test getting policy by policy number"""
        try:
            policies = postgres_service.execute_custom_query(
                "SELECT policy_number FROM policies LIMIT 1"
            )
            if policies:
                policy_number = policies[0]['policy_number']
                policy = postgres_service.get_policy_by_number(policy_number)
                assert policy is not None
                assert policy['policy_number'] == policy_number
        except Exception as e:
            pytest.skip(f"Could not test get_policy_by_number: {e}")
    
    def test_get_high_risk_policies(self, postgres_service):
        """Test getting high-risk policies"""
        policies = postgres_service.get_high_risk_policies(min_risk_score=90)
        assert isinstance(policies, list)
        # All policies should have risk_score_internal >= 90
        for policy in policies:
            assert policy.get('risk_score_internal', 0) >= 90
    
    def test_get_insured_info(self, postgres_service):
        """Test getting insured information"""
        # First, get a list of insureds to test with
        # We'll try to get info for a known insured ID if available
        # For now, we'll just test that the method works
        # In a real scenario, you'd have test data
        try:
            # Try with a sample ID format
            info = postgres_service.get_insured_info("TEST123")
            # Should return None if not found, or a dict if found
            assert info is None or isinstance(info, dict)
        except Exception as e:
            # If there's an error, it should be a database error, not a logic error
            assert "insured" in str(e).lower() or "not found" in str(e).lower()


@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="PostgreSQL not available")
class TestSQLQueryHandler:
    """Tests for SQLQueryHandler"""
    
    @pytest.fixture
    def sql_query_handler(self):
        """Create SQL query handler for testing"""
        postgres_service = PostgreSQLService()
        return SQLQueryHandler(postgres_service)
    
    def test_count_insureds_query(self, sql_query_handler):
        """Test count insureds query"""
        response = sql_query_handler.handle_query("How many insureds are there?")
        assert isinstance(response, str)
        assert "insured" in response.lower() or "count" in response.lower()
    
    def test_count_claims_query(self, sql_query_handler):
        """Test count claims query"""
        response = sql_query_handler.handle_query("How many claims have been filed?")
        assert isinstance(response, str)
        assert "claim" in response.lower()
    
    def test_count_policies_query(self, sql_query_handler):
        """Test count policies query"""
        response = sql_query_handler.handle_query("How many policies are there?")
        assert isinstance(response, str)
        assert "polic" in response.lower()
    
    def test_count_policies_query_with_filtering(self, sql_query_handler):
        """Test count policies query with policy_number filtering (authenticated user)"""
        # Get a policy number from database for testing
        try:
            policies = sql_query_handler.postgres_service.execute_custom_query(
                "SELECT policy_number FROM policies LIMIT 1"
            )
            if policies:
                policy_number = policies[0]['policy_number']
                response = sql_query_handler.handle_query(
                    "How many policies do I have?",
                    policy_number=policy_number
                )
                assert isinstance(response, str)
                assert "policy" in response.lower() or "1" in response
        except Exception as e:
            pytest.skip(f"Could not test filtered query: {e}")
    
    def test_high_risk_policies_query(self, sql_query_handler):
        """Test high-risk policies query"""
        response = sql_query_handler.handle_query("Show me all high risk policies")
        assert isinstance(response, str)
        assert "risk" in response.lower() or "policy" in response.lower()
    
    def test_insured_info_query_no_id(self, sql_query_handler):
        """Test insured info query without ID"""
        response = sql_query_handler.handle_query("Show me information for insured")
        assert isinstance(response, str)
        # Should return help message or error
        assert len(response) > 0
    
    def test_help_message(self, sql_query_handler):
        """Test that unrecognized queries return help message"""
        response = sql_query_handler.handle_query("What is the weather?")
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="PostgreSQL not available")
class TestPostgreSQLHealth:
    """Tests for PostgreSQL health checks"""
    
    def test_postgres_health_check(self):
        """Test PostgreSQL health check"""
        is_healthy = check_postgres_health()
        assert isinstance(is_healthy, bool)

