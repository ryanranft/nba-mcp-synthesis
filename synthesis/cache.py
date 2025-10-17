#!/usr/bin/env python3
"""
Redis Cache Layer
Provides caching for synthesis results and MCP responses
"""

import json
import hashlib
import os
from typing import Optional, Any, Dict
from datetime import timedelta
import logging

# Try to import redis, make it optional
try:
    import redis
    from redis.exceptions import RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisError = Exception

# Import hierarchical environment helper
try:
    from mcp_server.env_helper import get_hierarchical_env
except ImportError:
    # Fallback for when running outside the project
    def get_hierarchical_env(key: str, project: str, context: str) -> Optional[str]:
        return os.getenv(key)


logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client with fallback to in-memory cache"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enabled: bool = True,
        default_ttl: int = 3600,  # 1 hour
    ):
        self.enabled = enabled and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.redis_client = None
        self._memory_cache: Dict[str, Any] = {}

        if self.enabled:
            try:
                redis_url = redis_url or (
                    get_hierarchical_env("REDIS_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                    or "redis://localhost:6379/0"
                )
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✅ Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable, using in-memory cache: {e}")
                self.redis_client = None
        else:
            if not REDIS_AVAILABLE:
                logger.info("Redis not installed, using in-memory cache")
            else:
                logger.info("Cache disabled")

    def _generate_key(self, prefix: str, data: Dict) -> str:
        """Generate cache key from prefix and data"""
        # Sort dict for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"✅ Cache HIT: {key}")
                    return json.loads(value)
                else:
                    logger.debug(f"❌ Cache MISS: {key}")
                    return None
            else:
                # Fallback to memory cache
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.enabled:
            return False

        try:
            ttl = ttl or self.default_ttl
            value_str = json.dumps(value)

            if self.redis_client:
                self.redis_client.setex(key, ttl, value_str)
                logger.debug(f"💾 Cached: {key} (TTL: {ttl}s)")
                return True
            else:
                # Fallback to memory cache (no TTL)
                self._memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False

        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
            logger.debug(f"🗑️  Deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear(self, pattern: str = "*") -> int:
        """Clear cache keys matching pattern"""
        if not self.enabled:
            return 0

        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
                    logger.info(f"🗑️  Cleared {count} keys matching '{pattern}'")
                    return count
                return 0
            else:
                # Clear memory cache
                count = len(self._memory_cache)
                self._memory_cache.clear()
                return count
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}

        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    "enabled": True,
                    "backend": "redis",
                    "keys": self.redis_client.dbsize(),
                    "memory_used": info.get("used_memory_human", "N/A"),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(
                        info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                    ),
                }
            else:
                return {
                    "enabled": True,
                    "backend": "memory",
                    "keys": len(self._memory_cache),
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": False, "error": str(e)}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")


# Global cache instance
_cache_instance: Optional[CacheClient] = None


def get_cache() -> CacheClient:
    """Get or create global cache instance"""
    global _cache_instance

    if _cache_instance is None:
        # Check if caching is enabled via env var
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        _cache_instance = CacheClient(enabled=cache_enabled)

    return _cache_instance


# Cache decorators


def cache_synthesis_result(ttl: int = 3600):
    """Decorator to cache synthesis results"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key from function args
            cache_key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs),
            }
            cache_key = cache._generate_key("synthesis", cache_key_data)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"📦 Returning cached synthesis result")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            if result and result.get("status") == "success":
                cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def cache_mcp_response(ttl: int = 1800):
    """Decorator to cache MCP tool responses"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            cache_key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs),
            }
            cache_key = cache._generate_key("mcp", cache_key_data)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"📦 Returning cached MCP response")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache successful responses
            if result:
                cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator
