"""
Simple in-memory cache service for query results
Provides TTL-based caching for common queries
"""
import time
import hashlib
import logging
from typing import Optional, Any, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class CacheService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache service
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _make_key(self, query: str, query_type: str, user_id: Optional[str] = None) -> str:
        """
        Create a cache key from query parameters
        
        Args:
            query: Query text
            query_type: Query type (sql, rag, hybrid, etc.)
            user_id: Optional user ID
            
        Returns:
            Cache key string
        """
        key_string = f"{query_type}:{query}:{user_id or 'anonymous'}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, query_type: str, user_id: Optional[str] = None) -> Optional[Any]:
        """
        Get cached result if available and not expired
        
        Args:
            query: Query text
            query_type: Query type
            user_id: Optional user ID
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(query, query_type, user_id)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if time.time() > entry['expires_at']:
            del self._cache[key]
            logger.debug(f"Cache entry expired for key: {key[:8]}...")
            return None
        
        logger.debug(f"Cache hit for key: {key[:8]}...")
        return entry['value']
    
    def set(
        self,
        query: str,
        query_type: str,
        value: Any,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        Store result in cache
        
        Args:
            query: Query text
            query_type: Query type
            value: Value to cache
            user_id: Optional user ID
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        key = self._make_key(query, query_type, user_id)
        ttl = ttl or self.default_ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        logger.debug(f"Cached result for key: {key[:8]}... (TTL: {ttl}s)")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        now = time.time()
        active = sum(1 for entry in self._cache.values() if now <= entry['expires_at'])
        expired = len(self._cache) - active
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active,
            'expired_entries': expired,
            'default_ttl': self.default_ttl
        }


# Global cache instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(default_ttl=300)  # 5 minutes default
    return _cache_service

