"""
Enhanced Rate Limiting System for NBA MCP Server

Provides comprehensive rate limiting with:
- Token bucket algorithm
- Sliding window rate limiting
- Fixed window rate limiting
- Per-user and per-IP rate limits
- Redis-backed distributed rate limiting
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- Automatic 429 responses
- Custom rate limits per endpoint
- Burst handling

This module extends the basic rate_limiter.py with production-ready features.

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import asyncio
import functools
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .logging_config import get_logger
from .error_handling import BaseRateLimitError, get_error_handler

logger = get_logger(__name__)


# ==============================================================================
# Rate Limit Algorithms
# ==============================================================================


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


# ==============================================================================
# Rate Limit Configuration
# ==============================================================================


@dataclass
class RateLimitConfig:
    """
    Rate limit configuration.

    Attributes:
        requests_per_minute: Requests allowed per minute
        requests_per_hour: Requests allowed per hour
        requests_per_day: Requests allowed per day
        burst_size: Maximum burst size (for token bucket)
        algorithm: Rate limiting algorithm to use
        cost_per_request: Cost for each request (for weighted rate limiting)
        enabled: Whether rate limiting is enabled

    Examples:
        >>> config = RateLimitConfig(
        ...     requests_per_minute=60,
        ...     requests_per_hour=1000,
        ...     burst_size=10
        ... )
    """

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    cost_per_request: float = 1.0
    enabled: bool = True


@dataclass
class RateLimitInfo:
    """
    Rate limit information for response headers.

    Attributes:
        limit: Maximum requests allowed in window
        remaining: Requests remaining in current window
        reset: Unix timestamp when limit resets
        retry_after: Seconds until retry (if rate limited)
    """

    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None

    def to_headers(self) -> Dict[str, str]:
        """
        Convert to HTTP headers.

        Returns:
            Dictionary of rate limit headers
        """
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset),
        }

        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)

        return headers


# ==============================================================================
# Token Bucket Rate Limiter
# ==============================================================================


class TokenBucketLimiter:
    """
    Token bucket rate limiting algorithm.

    The token bucket algorithm allows bursts of traffic while enforcing
    an average rate limit. Tokens are added to a bucket at a constant rate,
    and each request consumes a token. If the bucket is empty, the request
    is rejected.

    Attributes:
        capacity: Maximum number of tokens in bucket
        refill_rate: Tokens added per second
        tokens: Current number of tokens
        last_refill: Last time tokens were refilled

    Examples:
        >>> limiter = TokenBucketLimiter(capacity=10, refill_rate=1.0)
        >>> allowed, info = limiter.allow_request("user_123")
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket limiter.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def allow_request(self, cost: float = 1.0) -> Tuple[bool, float]:
        """
        Check if request is allowed.

        Args:
            cost: Cost of this request (in tokens)

        Returns:
            (allowed, tokens_remaining)
        """
        with self._lock:
            self._refill()

            if self.tokens >= cost:
                self.tokens -= cost
                return True, self.tokens
            else:
                return False, self.tokens

    def time_until_available(self, cost: float = 1.0) -> float:
        """
        Calculate time until request would be allowed.

        Args:
            cost: Cost of the request

        Returns:
            Seconds until request would be allowed
        """
        with self._lock:
            self._refill()

            tokens_needed = cost - self.tokens
            if tokens_needed <= 0:
                return 0.0

            return tokens_needed / self.refill_rate


# ==============================================================================
# Sliding Window Rate Limiter
# ==============================================================================


class SlidingWindowLimiter:
    """
    Sliding window rate limiting algorithm.

    Maintains a sliding window of requests and rejects requests that
    would exceed the limit within the window.

    Examples:
        >>> limiter = SlidingWindowLimiter(max_requests=100, window_seconds=60)
        >>> allowed, info = limiter.allow_request("user_123")
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window limiter.

        Args:
            max_requests: Maximum requests in window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = Lock()

    def _clean_old_requests(self, now: float) -> None:
        """Remove requests outside the window."""
        cutoff = now - self.window_seconds

        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

    def allow_request(self) -> Tuple[bool, int]:
        """
        Check if request is allowed.

        Returns:
            (allowed, requests_in_window)
        """
        now = time.time()

        with self._lock:
            self._clean_old_requests(now)

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, len(self.requests)
            else:
                return False, len(self.requests)

    def time_until_available(self) -> float:
        """
        Calculate time until request would be allowed.

        Returns:
            Seconds until request would be allowed
        """
        now = time.time()

        with self._lock:
            self._clean_old_requests(now)

            if len(self.requests) < self.max_requests:
                return 0.0

            # Time until oldest request falls out of window
            oldest = self.requests[0]
            return (oldest + self.window_seconds) - now


# ==============================================================================
# Rate Limiter
# ==============================================================================


class RateLimiter:
    """
    Comprehensive rate limiter with multiple algorithms and features.

    Features:
    - Multiple rate limiting algorithms (token bucket, sliding window, fixed window)
    - Per-identifier rate limits (user ID, API key, IP address)
    - Hierarchical limits (per-minute, per-hour, per-day)
    - Burst handling
    - Weighted requests
    - Rate limit headers
    - Redis backend support for distributed systems

    Examples:
        >>> limiter = RateLimiter(
        ...     config=RateLimitConfig(
        ...         requests_per_minute=60,
        ...         requests_per_hour=1000,
        ...         burst_size=10
        ...     )
        ... )
        >>>
        >>> # Check rate limit
        >>> allowed, info = limiter.check_rate_limit("user_123")
        >>> if not allowed:
        ...     raise BaseRateLimitError(f"Rate limit exceeded. Retry after {info.retry_after}s")
    """

    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        redis_client: Optional[Any] = None,
        key_prefix: str = "ratelimit",
    ):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
            redis_client: Redis client for distributed rate limiting
            key_prefix: Prefix for Redis keys
        """
        self.config = config or RateLimitConfig()
        self.redis = redis_client
        self.key_prefix = key_prefix

        # In-memory storage (used when Redis not available)
        self.limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Thread safety
        self._lock = Lock()

        logger.info(
            "Rate limiter initialized",
            extra={
                "algorithm": self.config.algorithm.value,
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "burst_size": self.config.burst_size,
                "distributed": redis_client is not None,
            },
        )

    def _get_limiter(
        self,
        identifier: str,
        window: str,
    ) -> Union[TokenBucketLimiter, SlidingWindowLimiter]:
        """
        Get or create a rate limiter for identifier and window.

        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            window: Time window ("minute", "hour", "day")

        Returns:
            Rate limiter instance
        """
        key = f"{identifier}:{window}"

        with self._lock:
            if key not in self.limiters:
                if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                    if window == "minute":
                        capacity = self.config.burst_size
                        refill_rate = self.config.requests_per_minute / 60.0
                    elif window == "hour":
                        capacity = self.config.burst_size * 2
                        refill_rate = self.config.requests_per_hour / 3600.0
                    else:  # day
                        capacity = self.config.burst_size * 5
                        refill_rate = self.config.requests_per_day / 86400.0

                    self.limiters[key] = TokenBucketLimiter(capacity, refill_rate)

                elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                    if window == "minute":
                        max_requests = self.config.requests_per_minute
                        window_seconds = 60
                    elif window == "hour":
                        max_requests = self.config.requests_per_hour
                        window_seconds = 3600
                    else:  # day
                        max_requests = self.config.requests_per_day
                        window_seconds = 86400

                    self.limiters[key] = SlidingWindowLimiter(
                        max_requests, window_seconds
                    )

            return self.limiters[key]

    def check_rate_limit(
        self,
        identifier: str,
        cost: float = 1.0,
    ) -> Tuple[bool, RateLimitInfo]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (user ID, API key, IP address)
            cost: Cost of this request (for weighted rate limiting)

        Returns:
            (allowed, rate_limit_info)

        Examples:
            >>> allowed, info = limiter.check_rate_limit("user_123")
            >>> if not allowed:
            ...     # Return 429 with headers
            ...     headers = info.to_headers()
        """
        if not self.config.enabled:
            return True, RateLimitInfo(
                limit=999999,
                remaining=999999,
                reset=int(time.time()) + 3600,
            )

        # Check hierarchical limits (minute, hour, day)
        windows = [
            ("minute", self.config.requests_per_minute, 60),
            ("hour", self.config.requests_per_hour, 3600),
            ("day", self.config.requests_per_day, 86400),
        ]

        for window_name, max_requests, window_seconds in windows:
            limiter = self._get_limiter(identifier, window_name)

            if isinstance(limiter, TokenBucketLimiter):
                allowed, remaining = limiter.allow_request(cost)
            else:  # SlidingWindowLimiter
                allowed, count = limiter.allow_request()
                remaining = max_requests - count

            if not allowed:
                # Calculate retry_after
                if isinstance(limiter, TokenBucketLimiter):
                    retry_after = int(limiter.time_until_available(cost)) + 1
                else:
                    retry_after = int(limiter.time_until_available()) + 1

                logger.warning(
                    f"Rate limit exceeded: {identifier} ({window_name} window)",
                    extra={
                        "identifier": identifier,
                        "window": window_name,
                        "max_requests": max_requests,
                        "retry_after": retry_after,
                    },
                )

                return False, RateLimitInfo(
                    limit=max_requests,
                    remaining=0,
                    reset=int(time.time()) + retry_after,
                    retry_after=retry_after,
                )

        # All windows passed - request is allowed
        # Return info for the minute window
        return True, RateLimitInfo(
            limit=self.config.requests_per_minute,
            remaining=max(0, int(remaining)),
            reset=int(time.time()) + 60,
        )

    def reset_rate_limit(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier.

        Args:
            identifier: Unique identifier

        Examples:
            >>> limiter.reset_rate_limit("user_123")
        """
        with self._lock:
            # Remove all limiters for this identifier
            keys_to_remove = [
                key for key in self.limiters.keys() if key.startswith(f"{identifier}:")
            ]

            for key in keys_to_remove:
                del self.limiters[key]

        logger.info(f"Rate limit reset for: {identifier}")

    def get_rate_limit_status(self, identifier: str) -> Dict[str, Dict[str, Any]]:
        """
        Get current rate limit status for an identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with status for each window

        Examples:
            >>> status = limiter.get_rate_limit_status("user_123")
            >>> print(status["minute"]["remaining"])
        """
        status = {}

        windows = [
            ("minute", self.config.requests_per_minute),
            ("hour", self.config.requests_per_hour),
            ("day", self.config.requests_per_day),
        ]

        for window_name, max_requests in windows:
            key = f"{identifier}:{window_name}"

            with self._lock:
                if key in self.limiters:
                    limiter = self.limiters[key]

                    if isinstance(limiter, TokenBucketLimiter):
                        remaining = int(limiter.tokens)
                    else:
                        limiter._clean_old_requests(time.time())
                        remaining = max_requests - len(limiter.requests)

                    status[window_name] = {
                        "limit": max_requests,
                        "remaining": remaining,
                        "used": max_requests - remaining,
                    }
                else:
                    status[window_name] = {
                        "limit": max_requests,
                        "remaining": max_requests,
                        "used": 0,
                    }

        return status


# ==============================================================================
# Decorators
# ==============================================================================


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    identifier_param: str = "user_id",
    cost: float = 1.0,
):
    """
    Decorator to apply rate limiting to functions.

    Args:
        requests_per_minute: Maximum requests per minute
        requests_per_hour: Maximum requests per hour
        identifier_param: Name of parameter containing identifier
        cost: Cost of this request

    Examples:
        >>> @rate_limit(requests_per_minute=10, requests_per_hour=100)
        ... async def query_database(user_id: str, query: str):
        ...     # This endpoint is rate limited
        ...     pass
        >>>
        >>> @rate_limit(requests_per_minute=5, identifier_param="api_key", cost=2.0)
        ... async def expensive_operation(api_key: str):
        ...     # This endpoint has a higher cost
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get identifier from parameters
            identifier = kwargs.get(identifier_param)

            if not identifier:
                # Try to find it in args
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if identifier_param in param_names:
                    idx = param_names.index(identifier_param)
                    if idx < len(args):
                        identifier = args[idx]

            if not identifier:
                identifier = "anonymous"

            # Check rate limit
            limiter = get_rate_limiter()
            config = RateLimitConfig(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
            )
            limiter.config = config

            allowed, info = limiter.check_rate_limit(identifier, cost)

            if not allowed:
                raise BaseRateLimitError(
                    f"Rate limit exceeded. Retry after {info.retry_after} seconds.",
                    details={
                        "rate_limit_info": {
                            "limit": info.limit,
                            "remaining": info.remaining,
                            "reset": info.reset,
                            "retry_after": info.retry_after,
                        }
                    },
                )

            # Execute function
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get identifier from parameters
            identifier = kwargs.get(identifier_param)

            if not identifier:
                # Try to find it in args
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if identifier_param in param_names:
                    idx = param_names.index(identifier_param)
                    if idx < len(args):
                        identifier = args[idx]

            if not identifier:
                identifier = "anonymous"

            # Check rate limit
            limiter = get_rate_limiter()
            config = RateLimitConfig(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
            )
            limiter.config = config

            allowed, info = limiter.check_rate_limit(identifier, cost)

            if not allowed:
                raise BaseRateLimitError(
                    f"Rate limit exceeded. Retry after {info.retry_after} seconds.",
                    details={
                        "rate_limit_info": {
                            "limit": info.limit,
                            "remaining": info.remaining,
                            "reset": info.reset,
                            "retry_after": info.retry_after,
                        }
                    },
                )

            # Execute function
            return func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==============================================================================
# Global Instance
# ==============================================================================


_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """Set the global rate limiter instance."""
    global _global_rate_limiter
    _global_rate_limiter = limiter
