"""
MongoDB data cleanup utility
Removes all test/seed data while preserving collections and indexes
"""

import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MongoDB connection settings (use root credentials)
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_ROOT_USER", "mongo_admin")
MONGO_PASSWORD = os.getenv("MONGO_ROOT_PASSWORD", "mongo_secure_pass_2025")
MONGO_DB = os.getenv("MONGO_DB", "insurance_users")
AUTH_DB = "admin"


def get_mongo_client():
    """Create and return MongoDB client"""
    try:
        connection_string = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000
        )
        # Test connection
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
        return client
    except errors.ServerSelectionTimeoutError as e:
        print(f"✗ Could not connect to MongoDB: {e}")
        return None


def clean_data():
    """Remove all data from collections while preserving structure"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client[MONGO_DB]
        
        # Count documents before deletion
        user_count_before = db.user_profiles.count_documents({})
        query_count_before = db.query_history.count_documents({})
        
        print(f"\n📊 Current Data:")
        print(f"   User Profiles: {user_count_before}")
        print(f"   Query History: {query_count_before}")
        
        # Delete all documents
        user_result = db.user_profiles.delete_many({})
        query_result = db.query_history.delete_many({})
        
        print(f"\n🗑️  Data Deleted:")
        print(f"   User Profiles: {user_result.deleted_count}")
        print(f"   Query History: {query_result.deleted_count}")
        
        # Verify deletion
        user_count_after = db.user_profiles.count_documents({})
        query_count_after = db.query_history.count_documents({})
        
        print(f"\n📊 Remaining Data:")
        print(f"   User Profiles: {user_count_after}")
        print(f"   Query History: {query_count_after}")
        
        # Verify collections and indexes still exist
        collections = db.list_collection_names()
        print(f"\n✓ Collections preserved: {collections}")
        
        user_indexes = list(db.user_profiles.list_indexes())
        query_indexes = list(db.query_history.list_indexes())
        print(f"✓ user_profiles indexes: {len(user_indexes)}")
        print(f"✓ query_history indexes: {len(query_indexes)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning data: {e}")
        return False
    finally:
        client.close()


if __name__ == "__main__":
    print("Cleaning MongoDB test/seed data...\n")
    success = clean_data()
    if success:
        print("\n✅ MongoDB data cleaned successfully!")
        print("   Collections and indexes preserved for production use.")
    else:
        print("\n❌ Failed to clean MongoDB data")
