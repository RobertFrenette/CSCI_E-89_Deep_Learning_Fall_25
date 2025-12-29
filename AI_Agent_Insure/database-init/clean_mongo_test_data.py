"""
Clean up all data from MongoDB after integration tests
Removes all user profiles and query history records
"""
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MongoDB connection settings (use localhost when running from host)
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_ROOT_USER", "mongo_admin")
MONGO_PASSWORD = os.getenv("MONGO_ROOT_PASSWORD", "mongo_secure_pass_2025")
MONGO_DB = os.getenv("MONGO_DB", "insurance_users")
AUTH_DB = "admin"

# Override MONGO_HOST if it's set to Docker service name (when running from host)
if MONGO_HOST == "mongodb":
    MONGO_HOST = "localhost"

def clean_all_data():
    """Remove all user profiles and query history from MongoDB"""
    try:
        connection_string = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource={AUTH_DB}"
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client[MONGO_DB]
        
        # Get counts before deletion
        user_count_before = db.user_profiles.count_documents({})
        query_count_before = db.query_history.count_documents({})
        
        # Delete all query history
        query_result = db.query_history.delete_many({})
        print(f"✓ Deleted {query_result.deleted_count} query history records")
        
        # Delete all user profiles
        user_result = db.user_profiles.delete_many({})
        print(f"✓ Deleted {user_result.deleted_count} user profiles")
        
        # Verify deletion
        user_count_after = db.user_profiles.count_documents({})
        query_count_after = db.query_history.count_documents({})
        
        print(f"\n🧹 Cleaned up all MongoDB data:")
        print(f"   Users: {user_count_before} → {user_count_after}")
        print(f"   Query History: {query_count_before} → {query_count_after}")
        
        if user_count_after == 0 and query_count_after == 0:
            print("\n✅ All MongoDB data successfully deleted")
        else:
            print(f"\n⚠️  Warning: Some data may still remain (Users: {user_count_after}, Queries: {query_count_after})")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning MongoDB data: {e}")
        return False


if __name__ == "__main__":
    print("Cleaning up all MongoDB data...\n")
    success = clean_all_data()
    if success:
        print("\n✅ MongoDB data cleanup completed!")
    else:
        print("\n❌ Failed to clean up MongoDB data")

