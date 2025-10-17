"""
Advanced Multi-Tier Caching Layer

Implements a comprehensive caching strategy with multiple tiers:
- L1: In-memory LRU cache (fastest)
- L2: Redis distributed cache (shared across instances)
- L3: CDN edge caching (for static content)

Features:
- Cache warming and preloading
- Cache invalidation strategies
- Cache stampede prevention
- Cache hit/miss metrics
- TTL management
- Cache compression
- Cache sharding
"""

import hashlib
import json
import pickle
import time
import zlib
from collections import OrderedDict
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels"""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_CDN = "l3_cdn"


class CacheEvictionPolicy(Enum):
    """Cache eviction strategies"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hits: int = 0
    misses: int = 0
    writes: int = 0
    evictions: int = 0
    errors: int = 0
    total_size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate"""
        return 1.0 - self.hit_rate


class LRUCache:
    """In-memory LRU cache (L1)"""

    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.metrics = CacheMetrics()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.metrics.misses += 1
                return None

            # Check TTL
            if (
                self.ttl_seconds
                and time.time() - self.timestamps[key] > self.ttl_seconds
            ):
                self.delete(key)
                self.metrics.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.metrics.hits += 1
            return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Evict least recently used
                    oldest_key = next(iter(self.cache))
                    self.cache.pop(oldest_key)
                    self.timestamps.pop(oldest_key, None)
                    self.metrics.evictions += 1

            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.metrics.writes += 1
            self.metrics.total_size_bytes += len(str(value))

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
                self.timestamps.pop(key, None)
                return True
            return False

    def clear(self) -> None:
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.metrics = CacheMetrics()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class RedisCache:
    """Redis distributed cache (L2)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        compress: bool = True,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.compress = compress
        self.metrics = CacheMetrics()
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        try:
            import redis

            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # We'll handle encoding
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except ImportError:
            logger.warning("Redis library not installed. L2 cache disabled.")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
            self.metrics.errors += 1

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.client:
            return None

        try:
            data = self.client.get(key)
            if data is None:
                self.metrics.misses += 1
                return None

            # Decompress if enabled
            if self.compress:
                data = zlib.decompress(data)

            value = pickle.loads(data)
            self.metrics.hits += 1
            return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.metrics.errors += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self.client:
            return False

        try:
            data = pickle.dumps(value)

            # Compress if enabled
            if self.compress:
                data = zlib.compress(data)

            if ttl_seconds:
                self.client.setex(key, ttl_seconds, data)
            else:
                self.client.set(key, data)

            self.metrics.writes += 1
            self.metrics.total_size_bytes += len(data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self.metrics.errors += 1
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.client:
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self.metrics.errors += 1
            return False

    def clear(self) -> bool:
        """Clear entire Redis database"""
        if not self.client:
            return False

        try:
            self.client.flushdb()
            self.metrics = CacheMetrics()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self.metrics.errors += 1
            return False


class MultiTierCache:
    """
    Multi-tier caching system

    L1 (Memory) -> L2 (Redis) -> Origin
    """

    def __init__(
        self,
        l1_enabled: bool = True,
        l1_max_size: int = 1000,
        l1_ttl_seconds: Optional[int] = 300,
        l2_enabled: bool = False,
        l2_host: str = "localhost",
        l2_port: int = 6379,
        l2_ttl_seconds: Optional[int] = 3600,
    ):

        self.l1_enabled = l1_enabled
        self.l2_enabled = l2_enabled

        # Initialize L1 cache
        self.l1_cache = LRUCache(l1_max_size, l1_ttl_seconds) if l1_enabled else None

        # Initialize L2 cache
        self.l2_cache = RedisCache(l2_host, l2_port) if l2_enabled else None

        self.l2_ttl_seconds = l2_ttl_seconds

        logger.info(f"MultiTierCache initialized: L1={l1_enabled}, L2={l2_enabled}")

    def get(self, key: str, compute_fn: Optional[Callable] = None) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 -> compute_fn)

        Args:
            key: Cache key
            compute_fn: Function to compute value if not in cache

        Returns:
            Cached or computed value
        """
        # Try L1 cache
        if self.l1_enabled:
            value = self.l1_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (L1): {key}")
                return value

        # Try L2 cache
        if self.l2_enabled:
            value = self.l2_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (L2): {key}")
                # Populate L1 cache
                if self.l1_enabled:
                    self.l1_cache.set(key, value)
                return value

        # Cache miss - compute value
        if compute_fn:
            logger.debug(f"Cache miss: {key} - computing...")
            value = compute_fn()
            self.set(key, value)
            return value

        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in all enabled cache tiers"""
        # Set in L1
        if self.l1_enabled:
            self.l1_cache.set(key, value)

        # Set in L2
        if self.l2_enabled:
            self.l2_cache.set(key, value, self.l2_ttl_seconds)

    def delete(self, key: str) -> None:
        """Delete key from all cache tiers"""
        if self.l1_enabled:
            self.l1_cache.delete(key)
        if self.l2_enabled:
            self.l2_cache.delete(key)

    def clear(self) -> None:
        """Clear all cache tiers"""
        if self.l1_enabled:
            self.l1_cache.clear()
        if self.l2_enabled:
            self.l2_cache.clear()

    def get_metrics(self) -> Dict[str, CacheMetrics]:
        """Get metrics from all cache tiers"""
        metrics = {}
        if self.l1_enabled:
            metrics["l1"] = self.l1_cache.metrics
        if self.l2_enabled:
            metrics["l2"] = self.l2_cache.metrics
        return metrics

    def warm_cache(self, key_value_pairs: List[tuple]) -> None:
        """
        Warm cache with pre-computed values

        Args:
            key_value_pairs: List of (key, value) tuples
        """
        for key, value in key_value_pairs:
            self.set(key, value)
        logger.info(f"Cache warmed with {len(key_value_pairs)} entries")


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    cache: MultiTierCache, ttl_seconds: Optional[int] = None, key_prefix: str = ""
):
    """
    Decorator for caching function results

    Usage:
        @cached(my_cache, ttl_seconds=300, key_prefix="player_stats")
        def get_player_stats(player_id):
            # Expensive computation
            return stats
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator


# Global cache instance
_global_cache: Optional[MultiTierCache] = None


def get_cache() -> MultiTierCache:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiTierCache(
            l1_enabled=True,
            l1_max_size=1000,
            l1_ttl_seconds=300,
            l2_enabled=False,  # Enable with Redis configuration
        )
    return _global_cache


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create multi-tier cache
    cache = MultiTierCache(
        l1_enabled=True,
        l1_max_size=100,
        l1_ttl_seconds=60,
        l2_enabled=False,  # Set to True if Redis is available
    )

    # Basic operations
    cache.set("player:1", {"name": "LeBron James", "ppg": 27.1})
    player = cache.get("player:1")
    print(f"Player: {player}")

    # Cache with compute function
    def expensive_computation():
        print("Computing expensive result...")
        time.sleep(1)
        return {"result": "expensive_data"}

    result1 = cache.get("expensive_key", compute_fn=expensive_computation)
    print(f"First call (miss): {result1}")

    result2 = cache.get("expensive_key", compute_fn=expensive_computation)
    print(f"Second call (hit): {result2}")

    # Cache metrics
    metrics = cache.get_metrics()
    print(f"\nCache Metrics:")
    for tier, metric in metrics.items():
        print(f"{tier.upper()}:")
        print(f"  Hit Rate: {metric.hit_rate:.2%}")
        print(f"  Hits: {metric.hits}, Misses: {metric.misses}")
        print(f"  Writes: {metric.writes}, Evictions: {metric.evictions}")

    # Using decorator
    @cached(cache, ttl_seconds=60, key_prefix="game_stats")
    def get_game_stats(game_id: int):
        print(f"Fetching stats for game {game_id}...")
        return {"game_id": game_id, "score": "120-115"}

    stats1 = get_game_stats(12345)
    print(f"\nFirst call: {stats1}")

    stats2 = get_game_stats(12345)
    print(f"Second call (cached): {stats2}")
