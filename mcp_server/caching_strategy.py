"""Advanced Caching Strategy - IMPORTANT 20"""
import redis
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching layer"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis cache
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        logger.info(f"✅ Connected to Redis: {host}:{port}/{db}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"❌ Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            serialized = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            logger.debug(f"✅ Cached: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.client.delete(key)
            logger.debug(f"✅ Deleted from cache: {key}")
            return True
        except Exception as e:
            logger.error(f"❌ Cache delete error: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache keys
        
        Args:
            pattern: Optional pattern to match keys (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if pattern:
                keys = self.client.keys(pattern)
                if keys:
                    return self.client.delete(*keys)
            else:
                return self.client.flushdb()
        except Exception as e:
            logger.error(f"❌ Cache clear error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"❌ Cache exists error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get remaining TTL for key (in seconds)"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"❌ Cache TTL error: {e}")
            return -1


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    use_kwargs: bool = True
):
    """
    Decorator to cache function results
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
        use_kwargs: Include kwargs in cache key
        
    Usage:
        @cached(ttl=600, key_prefix="player_stats")
        def get_player_stats(player_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            if use_kwargs:
                key_suffix = cache_key(*args, **kwargs)
            else:
                key_suffix = cache_key(*args)
            
            key = f"{key_prefix}:{func.__name__}:{key_suffix}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(key_pattern: str):
    """
    Decorator to invalidate cache on function execution
    
    Usage:
        @cache_invalidate("player_stats:*")
        def update_player_stats(player_id: int, stats: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache = get_cache()
            deleted = cache.clear(key_pattern)
            logger.info(f"🗑️  Invalidated {deleted} cache keys matching: {key_pattern}")
            
            return result
        
        return wrapper
    return decorator


class CacheManager:
    """Advanced cache management"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or execute factory function
        
        Args:
            key: Cache key
            factory: Function to execute if cache miss
            ttl: Cache TTL
            
        Returns:
            Cached or computed value
        """
        value = self.cache.get(key)
        
        if value is not None:
            return value
        
        # Cache miss - execute factory
        value = factory()
        self.cache.set(key, value, ttl)
        
        return value
    
    def mget(self, keys: list) -> dict:
        """
        Get multiple keys from cache
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict of key -> value
        """
        result = {}
        
        for key in keys:
            value = self.cache.get(key)
            if value is not None:
                result[key] = value
        
        return result
    
    def mset(self, data: dict, ttl: Optional[int] = None) -> bool:
        """
        Set multiple keys in cache
        
        Args:
            data: Dict of key -> value
            ttl: Cache TTL
            
        Returns:
            Success status
        """
        success = True
        
        for key, value in data.items():
            if not self.cache.set(key, value, ttl):
                success = False
        
        return success
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = self.cache.client.info("stats")
            
            return {
                "hits": int(info.get("keyspace_hits", 0)),
                "misses": int(info.get("keyspace_misses", 0)),
                "hit_rate": self._calculate_hit_rate(info),
                "keys": self.cache.client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A")
            }
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate"""
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total


# Global cache instance
_cache: Optional[RedisCache] = None
_cache_manager: Optional[CacheManager] = None


def get_cache() -> RedisCache:
    """Get global cache instance"""
    global _cache
    if _cache is None:
        import os
        _cache = RedisCache(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0))
        )
    return _cache


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(get_cache())
    return _cache_manager


# Example usage
if __name__ == "__main__":
    # Simple caching
    cache = get_cache()
    
    cache.set("user:123", {"name": "John", "age": 30}, ttl=300)
    user = cache.get("user:123")
    print(f"User: {user}")
    
    # Decorator-based caching
    @cached(ttl=600, key_prefix="player_stats")
    def get_player_stats(player_id: int):
        # Simulate expensive database query
        import time
        time.sleep(0.5)
        return {"player_id": player_id, "points": 25, "assists": 7}
    
    # First call - cache miss (slow)
    import time
    start = time.time()
    stats = get_player_stats(123)
    print(f"First call: {time.time() - start:.2f}s - {stats}")
    
    # Second call - cache hit (fast)
    start = time.time()
    stats = get_player_stats(123)
    print(f"Second call: {time.time() - start:.2f}s - {stats}")
    
    # Cache stats
    manager = get_cache_manager()
    stats = manager.get_stats()
    print(f"Cache stats: {stats}")

