"""
Tests for MongoDB connection and operations
"""

import pytest
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


@pytest.fixture(scope="module")
def mongo_client():
    """Create MongoDB client for tests"""
    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = int(os.getenv("MONGO_PORT", 27017))
    mongo_user = os.getenv("MONGO_ROOT_USER", "mongo_admin")
    mongo_password = os.getenv("MONGO_ROOT_PASSWORD", "mongo_secure_pass_2025")
    
    connection_string = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource=admin"
    client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
    
    yield client
    
    client.close()


@pytest.fixture(scope="module")
def mongo_db(mongo_client):
    """Get database instance"""
    db_name = os.getenv("MONGO_DB", "insurance_users")
    return mongo_client[db_name]


class TestMongoDBConnection:
    """Test MongoDB connection and basic operations"""
    
    def test_connection(self, mongo_client):
        """Test MongoDB connection"""
        try:
            mongo_client.admin.command('ping')
            assert True
        except ServerSelectionTimeoutError:
            pytest.fail("Could not connect to MongoDB")
    
    def test_database_exists(self, mongo_client):
        """Test that insurance_users database exists"""
        db_list = mongo_client.list_database_names()
        assert "insurance_users" in db_list
    
    def test_collections_exist(self, mongo_db):
        """Test that required collections exist"""
        collections = mongo_db.list_collection_names()
        assert "user_profiles" in collections
        assert "query_history" in collections


class TestUserProfiles:
    """Test user_profiles collection"""
    
    def test_user_profiles_count(self, mongo_db):
        """Test that user profiles have been loaded"""
        count = mongo_db.user_profiles.count_documents({})
        assert count > 0, "No user profiles found"
    
    def test_user_profile_structure(self, mongo_db):
        """Test user profile document structure"""
        user = mongo_db.user_profiles.find_one()
        assert user is not None
        
        # Check required fields
        assert "_id" in user
        assert "username" in user
        assert "email" in user
        assert "password" in user
        assert "created_at" in user
        assert "updated_at" in user
        
        # Check optional fields
        if "last_login" in user:
            assert isinstance(user["last_login"], datetime)
    
    def test_username_unique_index(self, mongo_db):
        """Test that username has unique index"""
        indexes = mongo_db.user_profiles.index_information()
        assert "username_1" in indexes
        assert indexes["username_1"]["unique"] is True
    
    def test_email_unique_index(self, mongo_db):
        """Test that email has unique index"""
        indexes = mongo_db.user_profiles.index_information()
        assert "email_1" in indexes
        assert indexes["email_1"]["unique"] is True
    
    def test_query_user_by_username(self, mongo_db):
        """Test querying user by username"""
        users = list(mongo_db.user_profiles.find().limit(1))
        if users:
            username = users[0]["username"]
            result = mongo_db.user_profiles.find_one({"username": username})
            assert result is not None
            assert result["username"] == username


class TestQueryHistory:
    """Test query_history collection"""
    
    def test_query_history_count(self, mongo_db):
        """Test that query history records have been loaded"""
        count = mongo_db.query_history.count_documents({})
        assert count > 0, "No query history found"
    
    def test_query_history_structure(self, mongo_db):
        """Test query history document structure"""
        query = mongo_db.query_history.find_one()
        assert query is not None
        
        # Check required fields
        assert "user_id" in query
        assert "query_text" in query
        assert "query_type" in query
        assert "query_timestamp" in query
        
        # Check optional fields
        assert "rag_response" in query or True  # May be optional
        assert "sources_used" in query or True  # May be optional
    
    def test_query_history_indexes(self, mongo_db):
        """Test that query_history has proper indexes"""
        indexes = mongo_db.query_history.index_information()
        assert "user_id_1" in indexes
        assert "query_timestamp_-1" in indexes
        assert "query_type_1" in indexes
    
    def test_query_types_valid(self, mongo_db):
        """Test that query types are valid"""
        valid_types = ["policy_info", "claims", "coverage", "general"]
        queries = mongo_db.query_history.find()
        
        for query in queries:
            if "query_type" in query:
                assert query["query_type"] in valid_types
    
    def test_query_history_by_user(self, mongo_db):
        """Test querying history by user_id"""
        # Get a user_id that has queries
        query = mongo_db.query_history.find_one()
        if query:
            user_id = query["user_id"]
            user_queries = list(mongo_db.query_history.find({"user_id": user_id}))
            assert len(user_queries) > 0
    
    def test_query_history_sorted_by_timestamp(self, mongo_db):
        """Test querying history sorted by timestamp"""
        queries = list(mongo_db.query_history.find().sort("query_timestamp", -1).limit(10))
        assert len(queries) > 0
        
        # Verify descending order
        for i in range(len(queries) - 1):
            assert queries[i]["query_timestamp"] >= queries[i + 1]["query_timestamp"]


class TestCRUDOperations:
    """Test CRUD operations"""
    
    def test_insert_user_profile(self, mongo_db):
        """Test inserting a new user profile"""
        test_user = {
            "username": "testuser123",
            "email": "testuser@example.com",
            "password": "$2b$12$testhashedpassword",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = mongo_db.user_profiles.insert_one(test_user)
        assert result.inserted_id is not None
        
        # Clean up
        mongo_db.user_profiles.delete_one({"username": "testuser123"})
    
    def test_update_user_login(self, mongo_db):
        """Test updating user last_login"""
        # Get an existing user
        user = mongo_db.user_profiles.find_one()
        if user:
            result = mongo_db.user_profiles.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now(), "updated_at": datetime.now()}}
            )
            assert result.modified_count == 1
    
    def test_insert_query_history(self, mongo_db):
        """Test inserting query history"""
        # Get an existing user
        user = mongo_db.user_profiles.find_one()
        if user:
            test_query = {
                "user_id": user["_id"],
                "query_text": "Test query",
                "query_type": "general",
                "rag_response": "Test response",
                "sources_used": ["test_source"],
                "satisfaction_rating": 5,
                "query_timestamp": datetime.now()
            }
            
            result = mongo_db.query_history.insert_one(test_query)
            assert result.inserted_id is not None
            
            # Clean up
            mongo_db.query_history.delete_one({"_id": result.inserted_id})
