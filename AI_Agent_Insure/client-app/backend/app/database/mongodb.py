"""
MongoDB database connection and utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

# Global MongoDB client
_mongo_client = None
_mongo_db = None


def get_mongo_client():
    """Get or create MongoDB client"""
    global _mongo_client
    if _mongo_client is None:
        # Always use root user credentials from environment (ignore .env MONGO_USER)
        import os
        # Priority: MONGO_ROOT_USER env var > default mongo_admin (ignore settings.mongo_user)
        mongo_user = os.getenv("MONGO_ROOT_USER") or "mongo_admin"
        mongo_password = os.getenv("MONGO_ROOT_PASSWORD") or "mongo_secure_pass_2025"
        
        # MongoDB root user authenticates against 'admin' database
        connection_string = (
            f"mongodb://{mongo_user}:{mongo_password}"
            f"@{settings.mongo_host}:{settings.mongo_port}/?authSource=admin"
        )
        _mongo_client = AsyncIOMotorClient(connection_string)
    return _mongo_client


def get_mongo_db():
    """Get MongoDB database instance"""
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client[settings.mongo_db]
    return _mongo_db


async def close_mongo_connection():
    """Close MongoDB connection"""
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
