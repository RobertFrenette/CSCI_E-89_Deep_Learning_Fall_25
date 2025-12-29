"""Database package initialization"""
from app.database.mongodb import (
    get_mongo_client,
    get_mongo_db,
    close_mongo_connection
)
from app.database.postgres import (
    init_postgres_pool,
    get_postgres_pool,
    get_postgres_connection,
    get_postgres_cursor,
    close_postgres_pool,
    check_postgres_health
)

__all__ = [
    "get_mongo_client",
    "get_mongo_db",
    "close_mongo_connection",
    "init_postgres_pool",
    "get_postgres_pool",
    "get_postgres_connection",
    "get_postgres_cursor",
    "close_postgres_pool",
    "check_postgres_health"
]

