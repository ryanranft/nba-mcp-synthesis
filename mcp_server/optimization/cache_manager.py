"""
Cache Manager for Query Results

Provides Redis-based caching with TTL, invalidation, and memory fallback.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache")


@dataclass
class CacheEntry:
    """Represents a cached query result"""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0
    last_accessed: Optional[datetime] = None


class CacheManager:
    """
    Manages query result caching with Redis or in-memory fallback.

    Features:
    - TTL-based expiration
    - LRU eviction for memory cache
    - Cache statistics
    - Pattern-based invalidation
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,  # 1 hour
        max_memory_cache_size: int = 1000,
        enabled: bool = True
    ):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            default_ttl: Default TTL in seconds
            max_memory_cache_size: Max entries for in-memory cache
            enabled: Enable/disable caching globally
        """
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.max_memory_cache_size = max_memory_cache_size

        # Try to connect to Redis
        self.redis_client = None
        self.use_redis = False

        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.redis_client = None

        # In-memory cache fallback
        self.memory_cache: Dict[str, CacheEntry] = {}

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }

        logger.info(
            f"CacheManager initialized (backend={'Redis' if self.use_redis else 'Memory'}, "
            f"ttl={default_ttl}s, enabled={enabled})"
        )

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        try:
            if self.use_redis:
                value = self._get_from_redis(key)
            else:
                value = self._get_from_memory(key)

            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT: {key}")
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache MISS: {key}")

            return value

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self.stats["misses"] += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: TTL in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        ttl = ttl or self.default_ttl

        try:
            if self.use_redis:
                success = self._set_in_redis(key, value, ttl)
            else:
                success = self._set_in_memory(key, value, ttl)

            if success:
                self.stats["sets"] += 1
                logger.debug(f"Cache SET: {key} (ttl={ttl}s)")

            return success

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if self.use_redis:
                deleted = self.redis_client.delete(key) > 0
            else:
                deleted = key in self.memory_cache
                if deleted:
                    del self.memory_cache[key]

            if deleted:
                self.stats["deletes"] += 1
                logger.debug(f"Cache DELETE: {key}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "player:*", "query:*")

        Returns:
            Number of keys invalidated
        """
        if not self.enabled:
            return 0

        try:
            if self.use_redis:
                # Use SCAN for safe pattern matching
                count = 0
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
                    count += 1
                return count
            else:
                # In-memory pattern matching
                import fnmatch
                matching_keys = [
                    key for key in self.memory_cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in matching_keys:
                    del self.memory_cache[key]
                return len(matching_keys)

        except Exception as e:
            logger.error(f"Error invalidating pattern: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all cache entries"""
        if not self.enabled:
            return False

        try:
            if self.use_redis:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()

            logger.info("Cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_cache_key_for_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key for SQL query.

        Args:
            query: SQL query string
            params: Query parameters (if any)

        Returns:
            Cache key string
        """
        # Normalize query
        import re
        normalized = re.sub(r'\s+', ' ', query.strip().lower())

        # Include params in key
        if params:
            normalized += json.dumps(params, sort_keys=True)

        # Hash to create key
        hash_val = hashlib.md5(normalized.encode()).hexdigest()
        return f"query:{hash_val}"

    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        value_str = self.redis_client.get(key)
        if value_str:
            return json.loads(value_str)
        return None

    def _set_in_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis"""
        value_str = json.dumps(value)
        return self.redis_client.setex(key, ttl, value_str)

    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        if key not in self.memory_cache:
            return None

        entry = self.memory_cache[key]

        # Check if expired
        age = (datetime.now() - entry.created_at).total_seconds()
        if age > entry.ttl_seconds:
            del self.memory_cache[key]
            return None

        # Update access stats
        entry.hit_count += 1
        entry.last_accessed = datetime.now()

        return entry.value

    def _set_in_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in in-memory cache with LRU eviction"""
        # Check if we need to evict
        if len(self.memory_cache) >= self.max_memory_cache_size:
            self._evict_lru()

        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            ttl_seconds=ttl
        )

        self.memory_cache[key] = entry
        return True

    def _evict_lru(self):
        """Evict least recently used entry from memory cache"""
        if not self.memory_cache:
            return

        # Find LRU entry
        lru_key = None
        lru_time = datetime.now()

        for key, entry in self.memory_cache.items():
            access_time = entry.last_accessed or entry.created_at
            if access_time < lru_time:
                lru_time = access_time
                lru_key = key

        if lru_key:
            del self.memory_cache[lru_key]
            self.stats["evictions"] += 1
            logger.debug(f"Evicted LRU entry: {lru_key}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "backend": "Redis" if self.use_redis else "Memory",
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "evictions": self.stats["evictions"],
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "cache_size": len(self.memory_cache) if not self.use_redis else "N/A",
            "default_ttl": self.default_ttl
        }

    def __del__(self):
        """Cleanup Redis connection on deletion"""
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
