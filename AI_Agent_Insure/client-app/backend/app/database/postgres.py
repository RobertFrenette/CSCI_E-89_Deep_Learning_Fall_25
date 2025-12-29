"""
PostgreSQL database connection and utilities
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from app.config import get_settings

settings = get_settings()

# Connection pool
_pool = None


def init_postgres_pool():
    """Initialize PostgreSQL connection pool"""
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
    return _pool


def get_postgres_pool():
    """Get or create PostgreSQL connection pool"""
    if _pool is None:
        return init_postgres_pool()
    return _pool


@contextmanager
def get_postgres_connection():
    """Context manager for PostgreSQL connections"""
    pool = get_postgres_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_postgres_cursor(dict_cursor=True):
    """Context manager for PostgreSQL cursors"""
    with get_postgres_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def close_postgres_pool():
    """Close all connections in the pool"""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
