"""Rate limiting using Redis"""
import time
from typing import Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# In production, use actual Redis
# For now, use in-memory dict (not production-ready)
_rate_limit_store = {}


class RateLimiter:
    """Rate limiter using sliding window"""

    def __init__(self, redis_client=None):
        """Initialize rate limiter"""
        self.redis = redis_client
        self.store = _rate_limit_store if not redis_client else None

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is allowed

        Args:
            key: Unique identifier (user_id, IP, API key)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        window_start = now - window_seconds

        if self.redis:
            # Use Redis (production)
            return self._check_redis(key, max_requests, window_start, now)
        else:
            # Use in-memory (dev only)
            return self._check_memory(key, max_requests, window_start, now)

    def _check_memory(self, key: str, max_requests: int, window_start: float, now: float) -> bool:
        """In-memory rate limiting (not production-ready)"""
        if key not in self.store:
            self.store[key] = []

        # Remove old timestamps
        self.store[key] = [ts for ts in self.store[key] if ts > window_start]

        # Check limit
        if len(self.store[key]) >= max_requests:
            logger.warning(f"⚠️  Rate limit exceeded for {key}")
            return False

        # Add new timestamp
        self.store[key].append(now)
        return True

    def _check_redis(self, key: str, max_requests: int, window_start: float, now: float) -> bool:
        """Redis-based rate limiting (production)"""
        # Redis sorted set implementation
        redis_key = f"ratelimit:{key}"

        # Remove old entries
        self.redis.zremrangebyscore(redis_key, 0, window_start)

        # Count current requests
        current = self.redis.zcard(redis_key)

        if current >= max_requests:
            logger.warning(f"⚠️  Rate limit exceeded for {key}")
            return False

        # Add new request
        self.redis.zadd(redis_key, {str(now): now})
        self.redis.expire(redis_key, int(window_start))

        return True


# Global instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds

    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        def my_endpoint(user_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user identifier from args/kwargs
            user_id = kwargs.get('user_id') or (args[0] if args else 'anonymous')

            limiter = get_rate_limiter()
            if not limiter.is_allowed(str(user_id), max_requests, window_seconds):
                raise PermissionError(f"Rate limit exceeded: {max_requests} requests per {window_seconds}s")

            return func(*args, **kwargs)
        return wrapper
    return decorator

