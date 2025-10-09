"""
Resilience Module
Provides retry logic, circuit breakers, and error recovery for MCP client
"""

import asyncio
import time
import logging
from typing import Callable, Any, Optional, TypeVar, Awaitable
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Prevents cascading failures by failing fast when service is down
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "default"
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before trying again (half-open)
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def call(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator to wrap function with circuit breaker"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker [{self.name}] entering HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker [{self.name}] is OPEN. "
                        f"Service unavailable. Retry after {self.timeout}s."
                    )

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Success - update state
                self._on_success()
                return result

            except Exception as e:
                # Failure - update state
                self._on_failure()
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open state"""
        if self.last_failure_time is None:
            return False

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                # Close circuit - service recovered
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker [{self.name}] closed - service recovered")
        else:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during test - reopen circuit
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(f"Circuit breaker [{self.name}] reopened - service still failing")

        elif self.failure_count >= self.failure_threshold:
            # Too many failures - open circuit
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker [{self.name}] opened - "
                f"{self.failure_count} consecutive failures"
            )

    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker [{self.name}] manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        retry_on: Tuple of exceptions to retry on

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Attempt the function
                    result = await func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded on attempt {attempt + 1}"
                        )

                    return result

                except retry_on as e:
                    last_exception = e

                    if attempt >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> T:
    """
    Functional retry wrapper (without decorator)

    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts
        base_delay: Initial delay between retries
        *args, **kwargs: Arguments for func

    Returns:
        Result from func

    Example:
        result = await retry_async(fetch_data, url="http://...", max_retries=3)
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt >= max_retries:
                raise

            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
            )
            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception


class ConnectionPool:
    """
    Simple connection pool for reusing connections
    """

    def __init__(self, max_size: int = 10):
        """
        Initialize connection pool

        Args:
            max_size: Maximum number of connections
        """
        self.max_size = max_size
        self.connections = []
        self.in_use = set()
        self.lock = asyncio.Lock()

    async def acquire(self, factory: Callable[..., Awaitable[Any]]) -> Any:
        """
        Acquire a connection from pool

        Args:
            factory: Async function to create new connection

        Returns:
            Connection object
        """
        async with self.lock:
            # Try to get existing connection
            if self.connections:
                conn = self.connections.pop()
                self.in_use.add(conn)
                return conn

            # Create new connection if under limit
            if len(self.in_use) < self.max_size:
                conn = await factory()
                self.in_use.add(conn)
                return conn

            # Wait for connection to be released
            # (In production, implement proper waiting with timeout)
            raise RuntimeError("Connection pool exhausted")

    async def release(self, conn: Any):
        """
        Release connection back to pool

        Args:
            conn: Connection to release
        """
        async with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                self.connections.append(conn)

    async def close_all(self):
        """Close all connections in pool"""
        async with self.lock:
            for conn in self.connections:
                if hasattr(conn, 'close'):
                    try:
                        await conn.close()
                    except:
                        pass

            self.connections.clear()
            self.in_use.clear()


class RateLimiter:
    """
    Token bucket rate limiter
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize rate limiter

        Args:
            rate: Tokens per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add new tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_for_token(self, tokens: int = 1):
        """
        Wait until tokens are available

        Args:
            tokens: Number of tokens needed
        """
        while not await self.acquire(tokens):
            # Calculate wait time
            async with self.lock:
                needed = tokens - self.tokens
                wait_time = needed / self.rate

            await asyncio.sleep(min(wait_time, 0.1))


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """
    Get or create circuit breaker by name

    Args:
        name: Circuit breaker name
        **kwargs: CircuitBreaker initialization arguments

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)

    return _circuit_breakers[name]


# Example usage decorators
def with_mcp_retry(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator for MCP operations with retry"""
    return retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        retry_on=(ConnectionError, TimeoutError, OSError)
    )(func)


def with_mcp_circuit_breaker(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator for MCP operations with circuit breaker"""
    cb = get_circuit_breaker("mcp_server", failure_threshold=5, timeout=60)
    return cb.call(func)
