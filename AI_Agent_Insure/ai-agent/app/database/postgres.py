"""
PostgreSQL database connection and utilities for AI Agent
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Connection pool
_pool = None


def init_postgres_pool():
    """Initialize PostgreSQL connection pool with optimized settings"""
    global _pool
    if _pool is None:
        try:
            # Optimized pool settings: increased max connections for better concurrency
            _pool = SimpleConnectionPool(
                minconn=2,  # Keep at least 2 connections ready
                maxconn=20,  # Increased from 10 to 20 for better throughput
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                connect_timeout=10  # 10 second connection timeout
            )
            logger.info(f"PostgreSQL connection pool initialized: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db} (maxconn=20)")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
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
        logger.info("PostgreSQL connection pool closed")


def check_postgres_health() -> bool:
    """Check if PostgreSQL is accessible"""
    try:
        with get_postgres_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        return False

