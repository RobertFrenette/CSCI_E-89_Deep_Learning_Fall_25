"""
MongoDB connection and data loading utilities
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import random

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MongoDB connection settings (use root credentials for data loading)
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_ROOT_USER", "mongo_admin")
MONGO_PASSWORD = os.getenv("MONGO_ROOT_PASSWORD", "mongo_secure_pass_2025")
MONGO_DB = os.getenv("MONGO_DB", "insurance_users")
AUTH_DB = "admin"  # Authenticate against admin database


def get_mongo_client():
    """Create and return MongoDB client"""
    try:
        connection_string = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource={AUTH_DB}"
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


def load_seed_data():
    """Load seed data into MongoDB collections"""
    client = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client[MONGO_DB]
        
        # Sample user profiles with authentication data
        usernames = ["jsmith", "mjohnson", "rwilliams", "ebrown", "djones", 
                    "mgarcia", "awilson", "jmartinez", "tanderson", "ctaylor",
                    "lthomas", "jmoore", "pjackson", "dwhite", "sharris",
                    "kmartin", "rthompson", "blee", "jwalker", "aclark"]
        
        user_profiles = []
        for idx, username in enumerate(usernames, 1):
            user_profiles.append({
                "username": username,
                "email": f"{username}@example.com",
                "password": f"$2b$12${'x' * 50}",  # Placeholder for bcrypt hash
                "created_at": datetime.now() - timedelta(days=random.randint(30, 365)),
                "updated_at": datetime.now() - timedelta(days=random.randint(0, 10)),
                "last_login": datetime.now() - timedelta(days=random.randint(0, 30))
            })
        
        # Clear existing data
        db.user_profiles.delete_many({})
        db.query_history.delete_many({})
        
        # Create indexes for user_profiles
        db.user_profiles.create_index("email", unique=True)
        db.user_profiles.create_index("username", unique=True)
        db.user_profiles.create_index([("created_at", -1)])
        
        # Create indexes for query_history
        db.query_history.create_index("user_id")
        db.query_history.create_index([("query_timestamp", -1)])
        db.query_history.create_index("query_type")
        db.query_history.create_index([("user_id", 1), ("query_timestamp", -1)])
        print("✓ Created MongoDB indexes")
        
        # Insert user profiles
        result = db.user_profiles.insert_many(user_profiles)
        user_ids = result.inserted_ids
        print(f"✓ Inserted {len(user_ids)} user profiles")
        
        # Sample query history
        query_types = ["policy_info", "claims", "coverage", "general"]
        sample_queries = [
            "What is my current coverage amount?",
            "How do I file a claim?",
            "When does my policy expire?",
            "What AI systems are covered under my policy?",
            "How much is my deductible?",
            "Can you explain my liability coverage?",
            "What is the claims process timeline?",
            "How do I update my contact information?",
            "What are the exclusions in my policy?",
            "How does the AI risk assessment work?"
        ]
        
        query_history = []
        for user_id in user_ids[:10]:  # Add queries for first 10 users
            num_queries = random.randint(3, 10)
            for _ in range(num_queries):
                query_history.append({
                    "user_id": user_id,  # MongoDB ObjectId reference
                    "query_text": random.choice(sample_queries),
                    "query_type": random.choice(query_types),
                    "rag_response": "This is a sample AI-generated response based on policy documents and database information.",
                    "sources_used": [
                        "policy_document.pdf",
                        "coverage_details_table",
                        "faq_database"
                    ],
                    "satisfaction_rating": random.randint(3, 5),
                    "query_timestamp": datetime.now() - timedelta(
                        days=random.randint(0, 90),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                })
        
        # Insert query history
        result = db.query_history.insert_many(query_history)
        print(f"✓ Inserted {len(result.inserted_ids)} query history records")
        
        # Verify data
        user_count = db.user_profiles.count_documents({})
        query_count = db.query_history.count_documents({})
        
        print(f"\n📊 MongoDB Data Summary:")
        print(f"   Users: {user_count}")
        print(f"   Query History: {query_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading seed data: {e}")
        return False
    finally:
        client.close()


if __name__ == "__main__":
    print("Loading MongoDB seed data...\n")
    success = load_seed_data()
    if success:
        print("\n✅ MongoDB seed data loaded successfully!")
    else:
        print("\n❌ Failed to load MongoDB seed data")
