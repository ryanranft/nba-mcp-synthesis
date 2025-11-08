"""
Tests for CacheManager

Tests query result caching with both Redis and in-memory backends.
"""

import pytest
import json
from datetime import datetime, timedelta
from mcp_server.optimization.cache_manager import CacheManager, CacheEntry


class TestCacheManager:
    """Test suite for CacheManager"""

    @pytest.fixture
    def memory_cache(self):
        """Create in-memory cache manager"""
        return CacheManager(
            redis_url=None,  # Force memory cache
            default_ttl=60,
            max_memory_cache_size=100,
            enabled=True
        )

    @pytest.fixture
    def sample_data(self):
        """Sample data for caching"""
        return {
            "player_id": 123,
            "name": "LeBron James",
            "stats": {"ppg": 27.1, "rpg": 7.5, "apg": 7.4}
        }

    def test_cache_initialization(self):
        """Test cache manager initializes correctly"""
        cache = CacheManager(
            default_ttl=120,
            max_memory_cache_size=500,
            enabled=True
        )

        assert cache.enabled is True
        assert cache.default_ttl == 120
        assert cache.max_memory_cache_size == 500
        assert cache.use_redis is False  # No Redis URL provided
        assert len(cache.memory_cache) == 0

    def test_set_and_get(self, memory_cache, sample_data):
        """Test basic set and get operations"""
        key = "player:123"

        # Set value
        success = memory_cache.set(key, sample_data, ttl=60)
        assert success is True

        # Get value
        retrieved = memory_cache.get(key)
        assert retrieved == sample_data

    def test_get_nonexistent_key(self, memory_cache):
        """Test getting a key that doesn't exist"""
        result = memory_cache.get("nonexistent:key")
        assert result is None

    def test_cache_expiration(self, memory_cache):
        """Test that cached values expire after TTL"""
        key = "expiring:key"
        value = {"data": "test"}

        # Set with very short TTL
        memory_cache.set(key, value, ttl=1)

        # Should be available immediately
        assert memory_cache.get(key) == value

        # Wait for expiration
        import time
        time.sleep(1.5)

        # Should be expired
        assert memory_cache.get(key) is None

    def test_delete_key(self, memory_cache, sample_data):
        """Test deleting a cached key"""
        key = "delete:test"

        # Set and verify
        memory_cache.set(key, sample_data)
        assert memory_cache.get(key) is not None

        # Delete
        deleted = memory_cache.delete(key)
        assert deleted is True

        # Verify deleted
        assert memory_cache.get(key) is None

        # Delete non-existent key
        deleted_again = memory_cache.delete(key)
        assert deleted_again is False

    def test_cache_statistics(self, memory_cache):
        """Test cache statistics tracking"""
        # Perform various operations
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        memory_cache.get("key1")  # Hit
        memory_cache.get("key1")  # Hit
        memory_cache.get("key3")  # Miss
        memory_cache.delete("key2")

        stats = memory_cache.get_statistics()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["sets"] == 2
        assert stats["deletes"] == 1
        assert stats["hit_rate"] == pytest.approx(0.666, rel=0.01)
        assert stats["backend"] == "Memory"

    def test_get_cache_key_for_query(self, memory_cache):
        """Test generating cache keys from SQL queries"""
        query1 = "SELECT * FROM players WHERE id = 1"
        query2 = "select   *   from   players   where  id = 1"  # Same query, different whitespace

        key1 = memory_cache.get_cache_key_for_query(query1)
        key2 = memory_cache.get_cache_key_for_query(query2)

        # Should generate same key for normalized queries
        assert key1 == key2
        assert key1.startswith("query:")

    def test_get_cache_key_with_params(self, memory_cache):
        """Test cache key generation with parameters"""
        query = "SELECT * FROM players WHERE id = ?"
        params1 = {"id": 1}
        params2 = {"id": 2}

        key1 = memory_cache.get_cache_key_for_query(query, params1)
        key2 = memory_cache.get_cache_key_for_query(query, params2)

        # Different params should produce different keys
        assert key1 != key2

    def test_invalidate_pattern_memory(self, memory_cache):
        """Test pattern-based invalidation in memory cache"""
        # Set multiple keys
        memory_cache.set("player:1", {"name": "Player 1"})
        memory_cache.set("player:2", {"name": "Player 2"})
        memory_cache.set("team:1", {"name": "Team 1"})

        # Invalidate player keys
        count = memory_cache.invalidate_pattern("player:*")

        assert count == 2
        assert memory_cache.get("player:1") is None
        assert memory_cache.get("player:2") is None
        assert memory_cache.get("team:1") is not None  # Should remain

    def test_clear_cache(self, memory_cache):
        """Test clearing entire cache"""
        # Add some data
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        memory_cache.set("key3", "value3")

        assert len(memory_cache.memory_cache) == 3

        # Clear
        success = memory_cache.clear()
        assert success is True
        assert len(memory_cache.memory_cache) == 0

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Create cache with small size
        cache = CacheManager(max_memory_cache_size=3)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new key (should evict key2, the LRU)
        cache.set("key4", "value4")

        assert cache.get("key1") is not None  # Recently accessed
        assert cache.get("key2") is None  # Should be evicted
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

        # Check eviction stats
        stats = cache.get_statistics()
        assert stats["evictions"] == 1

    def test_disabled_cache(self):
        """Test that operations fail gracefully when cache is disabled"""
        cache = CacheManager(enabled=False)

        # All operations should return None/False
        assert cache.set("key", "value") is False
        assert cache.get("key") is None
        assert cache.delete("key") is False
        assert cache.invalidate_pattern("*") == 0

    def test_cache_entry_creation(self):
        """Test CacheEntry dataclass creation"""
        entry = CacheEntry(
            key="test:key",
            value={"data": "test"},
            created_at=datetime.now(),
            ttl_seconds=300
        )

        assert entry.key == "test:key"
        assert entry.value == {"data": "test"}
        assert entry.ttl_seconds == 300
        assert entry.hit_count == 0
        assert entry.last_accessed is None

    def test_access_tracking_in_memory(self, memory_cache):
        """Test that memory cache tracks access times"""
        key = "tracked:key"
        memory_cache.set(key, "value")

        # Access multiple times
        memory_cache.get(key)
        memory_cache.get(key)
        memory_cache.get(key)

        # Check entry
        entry = memory_cache.memory_cache[key]
        assert entry.hit_count == 3
        assert entry.last_accessed is not None
        assert entry.last_accessed > entry.created_at

    def test_default_ttl_used(self, memory_cache):
        """Test that default TTL is used when not specified"""
        key = "default:ttl"
        memory_cache.set(key, "value")  # No TTL specified

        entry = memory_cache.memory_cache[key]
        assert entry.ttl_seconds == memory_cache.default_ttl

    def test_custom_ttl_overrides_default(self, memory_cache):
        """Test that custom TTL overrides default"""
        key = "custom:ttl"
        custom_ttl = 3600
        memory_cache.set(key, "value", ttl=custom_ttl)

        entry = memory_cache.memory_cache[key]
        assert entry.ttl_seconds == custom_ttl
        assert entry.ttl_seconds != memory_cache.default_ttl

    def test_json_serializable_values(self, memory_cache):
        """Test that various JSON-serializable types work"""
        test_cases = [
            ("string:key", "string value"),
            ("int:key", 42),
            ("float:key", 3.14),
            ("list:key", [1, 2, 3]),
            ("dict:key", {"a": 1, "b": 2}),
            ("bool:key", True),
            ("null:key", None)
        ]

        for key, value in test_cases:
            memory_cache.set(key, value)
            retrieved = memory_cache.get(key)
            assert retrieved == value

    def test_hit_rate_calculation(self, memory_cache):
        """Test hit rate calculation in statistics"""
        # 3 hits, 2 misses = 60% hit rate
        memory_cache.set("key1", "value1")
        memory_cache.get("key1")  # Hit
        memory_cache.get("key1")  # Hit
        memory_cache.get("key1")  # Hit
        memory_cache.get("key2")  # Miss
        memory_cache.get("key3")  # Miss

        stats = memory_cache.get_statistics()
        assert stats["hit_rate"] == pytest.approx(0.6, rel=0.01)

    def test_empty_cache_hit_rate(self, memory_cache):
        """Test hit rate when cache is empty (no divide by zero)"""
        stats = memory_cache.get_statistics()
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0
