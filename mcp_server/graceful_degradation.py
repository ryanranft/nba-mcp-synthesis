"""Graceful Degradation - IMPORTANT 3"""

import logging
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for graceful degradation"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            logger.info("✅ Circuit breaker CLOSED - service recovered")

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(
                f"🔴 Circuit breaker OPEN - too many failures ({self.failure_count})"
            )

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        if not self.last_failure_time:
            return True

        time_since_failure = (
            datetime.utcnow() - self.last_failure_time
        ).total_seconds()
        return time_since_failure >= self.timeout_duration


def with_fallback(fallback_func: Callable):
    """Decorator to provide fallback when primary function fails"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️  Primary function failed, using fallback: {e}")
                return fallback_func(*args, **kwargs)

        return wrapper

    return decorator


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for a service"""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    return _circuit_breakers[service_name]


# Example: Database with fallback to cache
@with_fallback(lambda *args, **kwargs: {"source": "cache", "data": []})
def query_database(query: str):
    """Query database with fallback to cache"""
    # Simulate database query
    from mcp_server.database import get_database_engine

    engine = get_database_engine()
    with engine.connect() as conn:
        result = conn.execute(query)
        return {"source": "database", "data": list(result)}
