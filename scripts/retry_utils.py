"""
Retry utilities for API calls with exponential backoff
"""

import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
) -> Any:
    """Retry async function with exponential backoff"""
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed. Last error: {e}")
                raise

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

async def retry_api_call(
    api_func: Callable,
    model_name: str,
    max_retries: int = 3
) -> Any:
    """Retry API call with model-specific error handling"""
    async def wrapped_func():
        try:
            return await api_func()
        except Exception as e:
            error_msg = str(e).lower()

            # Don't retry authentication errors
            if any(keyword in error_msg for keyword in ['auth', 'key', 'unauthorized', 'forbidden']):
                logger.error(f"❌ {model_name} authentication error - not retrying: {e}")
                raise

            # Don't retry rate limit errors immediately
            if 'rate limit' in error_msg or 'quota' in error_msg:
                logger.warning(f"⚠️ {model_name} rate limit hit: {e}")
                raise

            # Retry other errors
            logger.warning(f"🔄 {model_name} API error (will retry): {e}")
            raise

    return await retry_with_backoff(wrapped_func, max_retries)




