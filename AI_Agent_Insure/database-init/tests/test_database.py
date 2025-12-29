"""
Database tests for AI Insurance Platform
Tests database connectivity, schema, and data integrity
"""

import os
from pathlib import Path
import pytest
import psycopg2
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'insurance_db'),
    'user': os.getenv('POSTGRES_USER', 'insure_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'insure_secure_pass_2025')
}


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for tests"""
    conn = psycopg2.connect(**DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def db_cursor(db_connection):
    """Create database cursor for tests"""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


class TestDatabaseConnection:
    """Test database connectivity"""
    
    def test_connection_successful(self, db_connection):
        """Test that database connection is successful"""
        assert db_connection is not None
        assert db_connection.closed == 0
    
    def test_database_version(self, db_cursor):
        """Test that database version can be retrieved"""
        db_cursor.execute("SELECT version();")
        version = db_cursor.fetchone()
        assert version is not None
        assert 'PostgreSQL' in version[0]


class TestDatabaseSchema:
    """Test database schema"""
    
    def test_all_tables_exist(self, db_cursor):
        """Test that all required tables exist"""
        expected_tables = [
            'insureds',
            'policies',
            'coverage_details',
            'ai_risk_profile',
            'claims_history'
        ]
        
        db_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in db_cursor.fetchall()]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
    
    def test_insureds_columns(self, db_cursor):
        """Test insureds table has required columns"""
        db_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'insureds'
        """)
        columns = [row[0] for row in db_cursor.fetchall()]
        
        required_columns = [
            'insured_id', 'first_name', 'last_name', 'email_address',
            'company_name', 'industry'
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} not found in insureds"
    
    def test_policies_columns(self, db_cursor):
        """Test policies table has required columns"""
        db_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'policies'
        """)
        columns = [row[0] for row in db_cursor.fetchall()]
        
        required_columns = [
            'policy_number', 'insured_id', 'policy_type',
            'effective_date', 'expiration_date', 'policy_status'
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} not found in policies"
    
    def test_foreign_key_constraints(self, db_cursor):
        """Test that foreign key constraints exist"""
        db_cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        
        foreign_keys = db_cursor.fetchall()
        assert len(foreign_keys) > 0, "No foreign keys found"
        
        # Check specific relationships
        fk_dict = {(row[0], row[1]): row[2] for row in foreign_keys}
        
        # policies -> insureds
        assert fk_dict.get(('policies', 'insured_id')) == 'insureds'
        
        # coverage_details -> policies
        assert fk_dict.get(('coverage_details', 'policy_number')) == 'policies'
        
        # ai_risk_profile -> policies
        assert fk_dict.get(('ai_risk_profile', 'policy_number')) == 'policies'
        
        # claims_history -> policies and insureds
        assert fk_dict.get(('claims_history', 'policy_number')) == 'policies'


class TestDatabaseData:
    """Test data integrity and presence"""
    
    def test_insureds_data_loaded(self, db_cursor):
        """Test that insureds data is loaded"""
        db_cursor.execute("SELECT COUNT(*) FROM insureds")
        count = db_cursor.fetchone()[0]
        assert count > 0, "No insureds data loaded"
    
    def test_policies_data_loaded(self, db_cursor):
        """Test that policies data is loaded"""
        db_cursor.execute("SELECT COUNT(*) FROM policies")
        count = db_cursor.fetchone()[0]
        assert count > 0, "No policies data loaded"
    
    def test_coverage_details_data_loaded(self, db_cursor):
        """Test that coverage details data is loaded"""
        db_cursor.execute("SELECT COUNT(*) FROM coverage_details")
        count = db_cursor.fetchone()[0]
        assert count > 0, "No coverage details data loaded"
    
    def test_ai_risk_profile_data_loaded(self, db_cursor):
        """Test that AI risk profile data is loaded"""
        db_cursor.execute("SELECT COUNT(*) FROM ai_risk_profile")
        count = db_cursor.fetchone()[0]
        assert count > 0, "No AI risk profile data loaded"
    
    def test_claims_history_data_loaded(self, db_cursor):
        """Test that claims history data is loaded"""
        db_cursor.execute("SELECT COUNT(*) FROM claims_history")
        count = db_cursor.fetchone()[0]
        assert count > 0, "No claims history data loaded"
    
    def test_data_relationships(self, db_cursor):
        """Test that data relationships are valid"""
        # Every policy should have a valid insured
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM policies p
            LEFT JOIN insureds i ON p.insured_id = i.insured_id
            WHERE i.insured_id IS NULL
        """)
        orphaned_policies = db_cursor.fetchone()[0]
        assert orphaned_policies == 0, "Found policies without valid insureds"
        
        # Every claim should have a valid policy
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM claims_history c
            LEFT JOIN policies p ON c.policy_number = p.policy_number
            WHERE p.policy_number IS NULL
        """)
        orphaned_claims = db_cursor.fetchone()[0]
        assert orphaned_claims == 0, "Found claims without valid policies"
    
    def test_sample_query(self, db_cursor):
        """Test a sample join query across tables"""
        db_cursor.execute("""
            SELECT 
                i.first_name,
                i.last_name,
                p.policy_type,
                c.coverage_tier,
                a.ai_system_type
            FROM insureds i
            JOIN policies p ON i.insured_id = p.insured_id
            JOIN coverage_details c ON p.policy_number = c.policy_number
            JOIN ai_risk_profile a ON p.policy_number = a.policy_number
            LIMIT 5
        """)
        
        results = db_cursor.fetchall()
        assert len(results) > 0, "Sample query returned no results"
        assert len(results[0]) == 5, "Sample query has wrong number of columns"


class TestDataIntegrity:
    """Test data integrity constraints"""
    
    def test_email_uniqueness(self, db_cursor):
        """Test that email addresses are unique"""
        db_cursor.execute("""
            SELECT email_address, COUNT(*) 
            FROM insureds 
            GROUP BY email_address 
            HAVING COUNT(*) > 1
        """)
        duplicates = db_cursor.fetchall()
        assert len(duplicates) == 0, f"Found duplicate emails: {duplicates}"
    
    def test_policy_dates(self, db_cursor):
        """Test that policy dates are valid"""
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM policies 
            WHERE expiration_date <= effective_date
        """)
        invalid_dates = db_cursor.fetchone()[0]
        assert invalid_dates == 0, "Found policies with invalid date ranges"
    
    def test_risk_score_range(self, db_cursor):
        """Test that risk scores are in valid range"""
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM ai_risk_profile 
            WHERE risk_score_internal < 0 OR risk_score_internal > 100
        """)
        invalid_scores = db_cursor.fetchone()[0]
        assert invalid_scores == 0, "Found risk scores outside valid range"
    
    def test_coverage_limits_positive(self, db_cursor):
        """Test that coverage limits are positive"""
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM coverage_details 
            WHERE coverage_limit <= 0 OR deductible < 0
        """)
        invalid_amounts = db_cursor.fetchone()[0]
        assert invalid_amounts == 0, "Found invalid coverage amounts"
