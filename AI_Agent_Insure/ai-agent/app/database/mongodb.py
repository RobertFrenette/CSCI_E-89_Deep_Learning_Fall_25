"""
MongoDB database connection and utilities for query logging
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
import os

settings = get_settings()

# Global MongoDB client
_mongo_client = None
_mongo_db = None


def get_mongo_client():
    """Get or create MongoDB client with optimized connection pool settings"""
    global _mongo_client
    if _mongo_client is None:
        # Use root user credentials from environment
        mongo_user = os.getenv("MONGO_ROOT_USER") or settings.mongo_user
        mongo_password = os.getenv("MONGO_ROOT_PASSWORD") or settings.mongo_password
        
        # MongoDB root user authenticates against 'admin' database
        connection_string = (
            f"mongodb://{mongo_user}:{mongo_password}"
            f"@{settings.mongo_host}:{settings.mongo_port}/?authSource=admin"
        )
        # Optimized connection pool settings
        _mongo_client = AsyncIOMotorClient(
            connection_string,
            maxPoolSize=50,  # Maximum number of connections in the pool
            minPoolSize=5,   # Minimum number of connections to maintain
            maxIdleTimeMS=45000,  # Close connections after 45 seconds of inactivity
            serverSelectionTimeoutMS=5000  # 5 second timeout for server selection
        )
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

