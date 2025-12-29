"""Database package initialization"""
from app.database.postgres import (
    get_postgres_connection,
    get_postgres_cursor,
    init_postgres_pool,
    close_postgres_pool
)
from app.database.mongodb import (
    get_mongo_client,
    get_mongo_db,
    close_mongo_connection
)

__all__ = [
    "get_postgres_connection",
    "get_postgres_cursor",
    "init_postgres_pool",
    "close_postgres_pool",
    "get_mongo_client",
    "get_mongo_db",
    "close_mongo_connection"
]
