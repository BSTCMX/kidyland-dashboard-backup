"""
Analytics Cache Service.

In-memory cache for analytics metrics with TTL support.
Designed to be easily replaceable with Redis in the future.

Thread-safe for async operations using asyncio.Lock.
Suitable for single-instance deployments.

Note: For multi-zone/multi-instance deployments, consider Redis.
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalyticsCache:
    """
    In-memory cache for analytics metrics.
    
    Features:
    - TTL (Time To Live) configurable per key
    - Thread-safe for async operations
    - Automatic expiration cleanup
    - Prepared for Redis migration (interface compatible)
    
    Usage:
        cache = AnalyticsCache()
        await cache.set("sales:report:123", {"total": 1000}, ttl=300)
        data = await cache.get("sales:report:123")
        await cache.invalidate("sales:report:*")
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize the cache.
        
        Args:
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        # Cache structure: {key: {"value": data, "expires_at": timestamp}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        
        logger.info(
            f"AnalyticsCache initialized with default_ttl={default_ttl}s"
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        async with self._lock:
            if key not in self._cache:
                logger.debug(f"Cache MISS: {key}")
                return None
            
            cache_entry = self._cache[key]
            expires_at = cache_entry.get("expires_at", 0)
            
            # Check if expired
            if time.time() > expires_at:
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"Cache EXPIRED: {key}")
                return None
            
            logger.debug(f"Cache HIT: {key}")
            return cache_entry["value"]
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (uses default_ttl if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            
            logger.debug(
                f"Cache SET: {key} (TTL: {ttl}s, expires at: {datetime.fromtimestamp(expires_at)})"
            )
    
    async def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            pattern: Pattern to match keys (if None, clears all cache)
                    Supports simple prefix matching (e.g., "sales:*")
                    
        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            if pattern is None:
                # Clear all cache
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cache CLEARED: {count} entries")
                return count
            
            # Pattern matching (simple prefix matching)
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                keys_to_remove = [
                    key for key in self._cache.keys() 
                    if key.startswith(prefix)
                ]
            else:
                # Exact match
                keys_to_remove = [pattern] if pattern in self._cache else []
            
            # Remove matched keys
            for key in keys_to_remove:
                del self._cache[key]
            
            logger.info(
                f"Cache INVALIDATED: {len(keys_to_remove)} entries matching '{pattern}'"
            )
            return len(keys_to_remove)
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        async with self._lock:
            for key, entry in self._cache.items():
                expires_at = entry.get("expires_at", 0)
                if current_time > expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.debug(
                f"Cache CLEANUP: Removed {len(expired_keys)} expired entries"
            )
        
        return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            total_entries = len(self._cache)
            current_time = time.time()
            
            # Count expired entries
            expired_count = sum(
                1 for entry in self._cache.values()
                if current_time > entry.get("expires_at", 0)
            )
            
            # Calculate average TTL remaining
            valid_entries = [
                entry for entry in self._cache.values()
                if current_time <= entry.get("expires_at", 0)
            ]
            
            if valid_entries:
                avg_ttl_remaining = sum(
                    entry["expires_at"] - current_time
                    for entry in valid_entries
                ) / len(valid_entries)
            else:
                avg_ttl_remaining = 0
            
            return {
                "total_entries": total_entries,
                "valid_entries": total_entries - expired_count,
                "expired_entries": expired_count,
                "average_ttl_remaining_seconds": round(avg_ttl_remaining, 2),
                "default_ttl_seconds": self.default_ttl
            }
    
    def _generate_key(
        self, 
        prefix: str, 
        *args, 
        **kwargs
    ) -> str:
        """
        Generate a cache key from prefix and parameters.
        
        Args:
            prefix: Key prefix (e.g., "sales", "stock")
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Generated cache key
        """
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        # Add keyword args (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)


# Global cache instance (singleton pattern)
_cache_instance: Optional[AnalyticsCache] = None


def get_cache() -> AnalyticsCache:
    """
    Get the global cache instance (singleton).
    
    Returns:
        AnalyticsCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AnalyticsCache(default_ttl=300)  # 5 minutes default
    return _cache_instance


