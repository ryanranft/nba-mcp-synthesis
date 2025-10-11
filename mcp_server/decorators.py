"""
Decorators for NBA MCP Server

Provides reusable decorators for error handling, rate limiting, and logging.
Based on best practices from ebook-mcp and lean-lsp-mcp implementations.
"""

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Dict, List
from collections import defaultdict

from .exceptions import (
    BookProcessingError,
    EpubProcessingError,
    PdfProcessingError,
    S3AccessError,
    RateLimitError
)

# Type variable for generic function return type
T = TypeVar('T')

# Global rate limit tracker
RATE_LIMITS: Dict[str, List[int]] = defaultdict(list)

# Get logger
logger = logging.getLogger(__name__)


def handle_book_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle book processing errors uniformly.

    Catches common exceptions and re-raises them with consistent error messages.
    Preserves detailed error information for debugging.

    Usage:
        @mcp.tool()
        @handle_book_errors
        async def read_book(params, ctx):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            raise
        except (EpubProcessingError, PdfProcessingError, S3AccessError) as e:
            # Re-raise custom exceptions as-is to preserve detailed error information
            logger.error(f"Processing error in {func.__name__}: {e}")
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            logger.error(f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}")
            raise BookProcessingError(
                str(e),
                "unknown",
                func.__name__,
                e
            )
    return wrapper


def handle_pdf_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle PDF-specific errors.

    Some PDF functions don't need FileNotFoundError handling
    as they handle it internally.

    Usage:
        @mcp.tool()
        @handle_pdf_errors
        async def extract_pdf_page(params, ctx):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except PdfProcessingError as e:
            logger.error(f"PDF error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise PdfProcessingError(
                str(e),
                "unknown",
                func.__name__,
                e
            )
    return wrapper


def rate_limited(category: str, max_requests: int, per_seconds: int):
    """
    Decorator to rate limit tool calls.

    Prevents API abuse and ensures compliance with service limits.
    Maintains a sliding window of request timestamps.

    Args:
        category: Rate limit category (e.g., "leansearch", "openai_api")
        max_requests: Maximum number of requests allowed
        per_seconds: Time window in seconds

    Usage:
        @mcp.tool()
        @rate_limited("search_api", max_requests=10, per_seconds=60)
        async def search_books(params, ctx):
            ...

    Returns:
        Decorator function that enforces rate limiting

    Raises:
        RateLimitError: If rate limit is exceeded
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = int(time.time())

            # Clean old timestamps (outside the time window)
            RATE_LIMITS[category] = [
                timestamp
                for timestamp in RATE_LIMITS[category]
                if timestamp > current_time - per_seconds
            ]

            # Check if limit exceeded
            if len(RATE_LIMITS[category]) >= max_requests:
                logger.warning(
                    f"Rate limit exceeded for {category}: "
                    f"{len(RATE_LIMITS[category])}/{max_requests} requests in {per_seconds}s"
                )
                raise RateLimitError(
                    f"Tool limit exceeded for {category}",
                    max_requests,
                    per_seconds
                )

            # Add current request
            RATE_LIMITS[category].append(current_time)

            # Log rate limit status
            logger.debug(
                f"Rate limit status for {category}: "
                f"{len(RATE_LIMITS[category])}/{max_requests} requests"
            )

            # Execute function
            return await func(*args, **kwargs)

        # Update docstring with rate limit info
        original_doc = wrapper.__doc__ or ""
        wrapper.__doc__ = f"[Rate: {max_requests}req/{per_seconds}s] {original_doc}"

        return wrapper

    return decorator


def cached_result(cache_key_func: Callable):
    """
    Decorator to cache function results based on a custom key function.

    Useful for caching expensive operations like S3 reads or complex computations.

    Args:
        cache_key_func: Function that generates cache key from args/kwargs

    Usage:
        def book_cache_key(params, ctx):
            return f"{params.book_path}:{params.chunk_number}"

        @mcp.tool()
        @cached_result(book_cache_key)
        async def read_book(params, ctx):
            ...
    """
    cache: Dict[str, any] = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)

            # Check cache
            if cache_key in cache:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cache[cache_key]

            # Execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            cache[cache_key] = result
            return result

        # Add cache clear method
        wrapper.clear_cache = lambda: cache.clear()

        return wrapper

    return decorator


def retry_on_error(max_attempts: int = 3, delay_seconds: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure with exponential backoff.

    Useful for transient network errors or S3 throttling.

    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries in seconds
        backoff: Multiplier for delay after each attempt

    Usage:
        @mcp.tool()
        @retry_on_error(max_attempts=3, delay_seconds=1.0)
        async def fetch_from_s3(params, ctx):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay_seconds

            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1

            # Should never reach here
            raise RuntimeError(f"Retry logic error in {func.__name__}")

        return wrapper

    return decorator


# Utility functions for rate limiting

def get_rate_limit_status(category: str) -> Dict[str, any]:
    """
    Get current rate limit status for a category.

    Args:
        category: Rate limit category

    Returns:
        Dict with current_requests, max_requests, and time_window
    """
    current_time = int(time.time())

    # Clean old timestamps
    RATE_LIMITS[category] = [
        timestamp
        for timestamp in RATE_LIMITS[category]
        if timestamp > current_time - 30  # Default 30s window
    ]

    return {
        "category": category,
        "current_requests": len(RATE_LIMITS[category]),
        "timestamps": RATE_LIMITS[category]
    }


def reset_rate_limit(category: str) -> None:
    """
    Reset rate limit counter for a category.

    Useful for testing or manual intervention.

    Args:
        category: Rate limit category to reset
    """
    RATE_LIMITS[category] = []
    logger.info(f"Reset rate limit for category: {category}")


def reset_all_rate_limits() -> None:
    """Reset all rate limit counters."""
    RATE_LIMITS.clear()
    logger.info("Reset all rate limits")
