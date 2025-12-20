"""
Unit tests for AnalyticsCache service.
"""
import pytest
import asyncio
import time
from services.analytics_cache import AnalyticsCache, get_cache


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_get_set():
    """Test basic get and set operations."""
    cache = AnalyticsCache(default_ttl=60)
    
    # Set a value
    await cache.set("test_key", {"value": 123}, ttl=60)
    
    # Get the value
    result = await cache.get("test_key")
    assert result is not None
    assert result["value"] == 123


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_expiration():
    """Test that cache entries expire correctly."""
    cache = AnalyticsCache(default_ttl=1)  # 1 second TTL
    
    # Set a value
    await cache.set("expire_key", {"value": 456}, ttl=1)
    
    # Should be available immediately
    result = await cache.get("expire_key")
    assert result is not None
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Should be expired
    result = await cache.get("expire_key")
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_invalidate_all():
    """Test invalidating all cache entries."""
    cache = AnalyticsCache()
    
    # Set multiple values
    await cache.set("key1", {"value": 1})
    await cache.set("key2", {"value": 2})
    await cache.set("key3", {"value": 3})
    
    # Invalidate all
    count = await cache.invalidate()
    assert count == 3
    
    # All should be gone
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.get("key3") is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_invalidate_pattern():
    """Test invalidating cache entries by pattern."""
    cache = AnalyticsCache()
    
    # Set values with different prefixes
    await cache.set("sales:123", {"value": 1})
    await cache.set("sales:456", {"value": 2})
    await cache.set("stock:123", {"value": 3})
    
    # Invalidate sales:* pattern
    count = await cache.invalidate("sales:*")
    assert count == 2
    
    # Sales entries should be gone
    assert await cache.get("sales:123") is None
    assert await cache.get("sales:456") is None
    
    # Stock entry should remain
    assert await cache.get("stock:123") is not None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_cleanup_expired():
    """Test cleanup of expired entries."""
    cache = AnalyticsCache(default_ttl=1)
    
    # Set values with short TTL
    await cache.set("key1", {"value": 1}, ttl=1)
    await cache.set("key2", {"value": 2}, ttl=1)
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Cleanup expired
    count = await cache.cleanup_expired()
    assert count == 2
    
    # Both should be gone
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_get_stats():
    """Test getting cache statistics."""
    cache = AnalyticsCache(default_ttl=300)
    
    # Set some values
    await cache.set("key1", {"value": 1}, ttl=300)
    await cache.set("key2", {"value": 2}, ttl=300)
    
    # Get stats
    stats = await cache.get_stats()
    assert stats["total_entries"] == 2
    assert stats["valid_entries"] == 2
    assert stats["expired_entries"] == 0
    assert stats["default_ttl_seconds"] == 300


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_generate_key():
    """Test cache key generation."""
    cache = AnalyticsCache()
    
    # Generate keys
    key1 = cache._generate_key("sales", "123", "2024-01-01", "2024-01-31")
    key2 = cache._generate_key("sales", "123", "2024-01-01", "2024-01-31")
    
    # Should be consistent
    assert key1 == key2
    assert "sales" in key1
    assert "123" in key1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_cache_singleton():
    """Test that get_cache returns singleton instance."""
    cache1 = get_cache()
    cache2 = get_cache()
    
    # Should be the same instance
    assert cache1 is cache2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cache_thread_safety():
    """Test that cache operations are thread-safe."""
    cache = AnalyticsCache()
    
    # Concurrent set operations
    await asyncio.gather(
        cache.set("key1", {"value": 1}),
        cache.set("key2", {"value": 2}),
        cache.set("key3", {"value": 3}),
    )
    
    # All should be set correctly
    assert await cache.get("key1") is not None
    assert await cache.get("key2") is not None
    assert await cache.get("key3") is not None


