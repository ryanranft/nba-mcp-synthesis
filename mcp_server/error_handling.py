"""
Robust Error Handling for NBA MCP Server

Provides comprehensive error handling, custom exceptions, error recovery,
and graceful degradation for the MCP server. This module extends the existing
error_handler.py with advanced features like retry logic, circuit breakers,
and error recovery strategies.

Features:
- Custom exception hierarchy (extends existing exceptions.py)
- Error categorization and tracking
- Retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Error reporting and alerting
- Graceful degradation strategies
- Context-aware error handling

Author: NBA MCP Server Team
Date: 2025-01-18
"""

import functools
import logging
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

# Import existing error infrastructure
from .error_handler import (
    ErrorCategory,
    ErrorSeverity,
    NBAMCPError,
    ValidationError as BaseValidationError,
    AuthenticationError as BaseAuthenticationError,
    DatabaseError as BaseDatabaseError,
    RateLimitError as BaseRateLimitError,
    NotFoundError as BaseNotFoundError,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Extended Exception Classes
# ==============================================================================


class DataValidationError(BaseValidationError):
    """
    Raised when data validation fails.

    This extends the base ValidationError with additional context
    for data validation scenarios.

    Examples:
        >>> raise DataValidationError(
        ...     "Invalid player stats",
        ...     details={"field": "points", "value": -5}
        ... )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_code = "DATA_VALIDATION_ERROR"


class ToolExecutionError(NBAMCPError):
    """
    Raised when tool execution fails.

    This is used for errors that occur during MCP tool execution,
    providing context about which tool failed and why.

    Examples:
        >>> raise ToolExecutionError(
        ...     "Query execution failed",
        ...     details={"tool": "query_database", "query": "SELECT ..."}
        ... )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            details=details,
        )
        self.error_code = "TOOL_EXECUTION_ERROR"


class ConfigurationError(NBAMCPError):
    """
    Raised when configuration is invalid.

    This is used for configuration errors that prevent the system
    from starting or operating correctly.

    Examples:
        >>> raise ConfigurationError(
        ...     "Missing required configuration",
        ...     details={"config_key": "DATABASE_URL"}
        ... )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            details=details,
        )
        self.error_code = "CONFIGURATION_ERROR"


class ServiceUnavailableError(NBAMCPError):
    """
    Raised when an external service is unavailable.

    This is used when a required external service (database, API, etc.)
    is temporarily unavailable.

    Examples:
        >>> raise ServiceUnavailableError(
        ...     "Database connection failed",
        ...     details={"service": "postgresql", "retry_after": 60}
        ... )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            details=details,
        )
        self.error_code = "SERVICE_UNAVAILABLE"


class CircuitBreakerOpenError(NBAMCPError):
    """
    Raised when circuit breaker is open.

    This is used when the circuit breaker prevents execution
    due to too many failures.

    Examples:
        >>> raise CircuitBreakerOpenError(
        ...     "Circuit breaker is open for query_database",
        ...     details={"failure_count": 5, "retry_after": 30}
        ... )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            details=details,
        )
        self.error_code = "CIRCUIT_BREAKER_OPEN"


# ==============================================================================
# Error Context
# ==============================================================================


@dataclass
class ErrorContext:
    """
    Context information for error handling.

    Provides additional context about where and when an error occurred,
    helping with debugging and error tracking.

    Attributes:
        tool_name: Name of the tool that was executing
        user_id: ID of the user who initiated the operation
        request_id: Unique identifier for the request
        operation: Name of the operation being performed
        timestamp: When the error occurred
        additional_context: Any additional context data

    Examples:
        >>> context = ErrorContext(
        ...     tool_name="query_database",
        ...     user_id="user_123",
        ...     request_id="req_456",
        ...     operation="SELECT query"
        ... )
    """

    tool_name: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            "tool_name": self.tool_name,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "additional_context": self.additional_context,
        }


# ==============================================================================
# Retry Logic
# ==============================================================================


class RetryStrategy(Enum):
    """Retry strategies for error recovery."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI_BACKOFF = "fibonacci_backoff"


@dataclass
class RetryConfig:
    """
    Configuration for retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for backoff calculation
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exceptions to retry on
    """

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_on: Tuple[Type[Exception], ...] = (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        import random

        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                self.base_delay * (self.backoff_factor**attempt), self.max_delay
            )
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(self.base_delay * (attempt + 1), self.max_delay)
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            # Generate fibonacci sequence
            # For attempt n, we want fib(n+2), where fib(0)=0, fib(1)=1
            fib = [0, 1]
            for i in range(2, attempt + 3):
                fib.append(fib[i - 1] + fib[i - 2])
            delay = min(self.base_delay * fib[attempt + 2], self.max_delay)
        else:
            delay = self.base_delay

        # Add jitter if enabled
        if self.jitter:
            delay = delay * (
                0.5 + random.random() * 0.5
            )  # nosec B311 - jitter doesn't need cryptographic randomness

        return delay


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """
    Decorator to retry function on failure with configurable backoff.

    This decorator provides automatic retry logic for functions that may
    fail transiently. It supports multiple retry strategies and can be
    customized for different failure scenarios.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        retry_on: Tuple of exception types to retry on
        strategy: Retry strategy to use
        on_retry: Optional callback called on each retry

    Returns:
        Decorated function with retry logic

    Examples:
        >>> @with_retry(max_retries=3, backoff_factor=2.0)
        ... async def query_database(query: str):
        ...     # May fail transiently
        ...     return await db.execute(query)

        >>> @with_retry(
        ...     max_retries=5,
        ...     retry_on=(DatabaseError, ServiceUnavailableError),
        ...     strategy=RetryStrategy.FIBONACCI_BACKOFF
        ... )
        ... async def fetch_data():
        ...     return await api.get_data()
    """
    config = RetryConfig(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        retry_on=retry_on,
        strategy=strategy,
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries + 1} failed "
                            f"for {func.__name__}: {e}. Retrying in {delay:.2f}s...",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_retries + 1,
                                "delay_seconds": delay,
                                "error_type": type(e).__name__,
                            },
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt)

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed "
                            f"for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "total_attempts": config.max_retries + 1,
                            },
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries + 1} failed "
                            f"for {func.__name__}: {e}. Retrying in {delay:.2f}s...",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_retries + 1,
                                "delay_seconds": delay,
                                "error_type": type(e).__name__,
                            },
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed "
                            f"for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "total_attempts": config.max_retries + 1,
                            },
                        )

            raise last_exception

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==============================================================================
# Circuit Breaker Pattern
# ==============================================================================


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls due to failures
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[Tuple[datetime, CircuitBreakerState]] = field(
        default_factory=list
    )

    def record_success(self):
        """Record a successful call."""
        self.success_count += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()

    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.now()

    def record_state_change(self, new_state: CircuitBreakerState):
        """Record a state change."""
        self.state_changes.append((datetime.now(), new_state))

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "last_success_time": (
                self.last_success_time.isoformat() if self.last_success_time else None
            ),
            "total_state_changes": len(self.state_changes),
        }


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by temporarily blocking operations
    that are likely to fail. The circuit breaker has three states:

    - CLOSED: Normal operation, all calls go through
    - OPEN: Blocking calls due to failures, immediate failure
    - HALF_OPEN: Testing if service recovered, limited calls allowed

    The circuit breaker automatically transitions between states based
    on success/failure patterns.

    Attributes:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening
        success_threshold: Number of successes to close from half-open
        timeout: Seconds before transitioning from open to half-open
        expected_exception: Exception type that triggers the circuit

    Examples:
        >>> breaker = CircuitBreaker(
        ...     name="database_queries",
        ...     failure_threshold=5,
        ...     timeout=60
        ... )

        >>> @breaker.protect
        ... async def query_database(query: str):
        ...     return await db.execute(query)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.on_open = on_open
        self.on_close = on_close

        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._last_failure_time: Optional[datetime] = None

    def _should_allow_call(self) -> bool:
        """Check if call should be allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has expired
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self._transition_to_half_open()
                    return True
            return False

        if self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitBreakerState.OPEN
        self.stats.record_state_change(CircuitBreakerState.OPEN)
        self._last_failure_time = datetime.now()

        logger.warning(
            f"Circuit breaker '{self.name}' opened due to {self.stats.consecutive_failures} "
            f"consecutive failures",
            extra={
                "circuit_breaker": self.name,
                "state": "open",
                "consecutive_failures": self.stats.consecutive_failures,
                "failure_threshold": self.failure_threshold,
            },
        )

        if self.on_open:
            self.on_open()

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.stats.record_state_change(CircuitBreakerState.HALF_OPEN)

        logger.info(
            f"Circuit breaker '{self.name}' transitioning to half-open for testing",
            extra={
                "circuit_breaker": self.name,
                "state": "half_open",
            },
        )

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.stats.record_state_change(CircuitBreakerState.CLOSED)

        logger.info(
            f"Circuit breaker '{self.name}' closed after {self.stats.consecutive_successes} "
            f"consecutive successes",
            extra={
                "circuit_breaker": self.name,
                "state": "closed",
                "consecutive_successes": self.stats.consecutive_successes,
            },
        )

        if self.on_close:
            self.on_close()

    def record_success(self):
        """Record a successful call."""
        self.stats.record_success()

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.success_threshold:
                self._transition_to_closed()

    def record_failure(self):
        """Record a failed call."""
        self.stats.record_failure()

        if self.state == CircuitBreakerState.CLOSED:
            if self.stats.consecutive_failures >= self.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during testing, reopen circuit
            self._transition_to_open()

    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker.

        Args:
            func: Function to protect

        Returns:
            Protected function
        """

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self._should_allow_call():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open",
                    details={
                        "circuit_breaker": self.name,
                        "state": self.state.value,
                        "retry_after": self.timeout,
                        "stats": self.stats.to_dict(),
                    },
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self._should_allow_call():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open",
                    details={
                        "circuit_breaker": self.name,
                        "state": self.state.value,
                        "retry_after": self.timeout,
                        "stats": self.stats.to_dict(),
                    },
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": self.stats.to_dict(),
            "config": {
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "timeout": self.timeout,
            },
        }


# ==============================================================================
# Error Handler
# ==============================================================================


class ErrorHandler:
    """
    Centralized error handling for MCP server.

    Provides comprehensive error handling with tracking, categorization,
    and recovery strategies.

    Features:
    - Error tracking and metrics
    - Circuit breaker management
    - Retry coordination
    - Error reporting and alerting
    - Graceful degradation

    Examples:
        >>> handler = ErrorHandler()

        >>> # Handle an error
        >>> try:
        ...     result = risky_operation()
        ... except Exception as e:
        ...     handler.handle_error(e, context=ErrorContext(tool_name="query"))

        >>> # Get error statistics
        >>> stats = handler.get_error_stats()
    """

    def __init__(self, enable_alerting: bool = False):
        self.enable_alerting = enable_alerting
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_history: deque = deque(maxlen=1000)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_rate_window: deque = deque(maxlen=100)

    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        notify: bool = False,
        reraise: bool = True,
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and tracking.

        Args:
            error: The exception to handle
            context: Additional context about the error
            notify: Whether to send notifications for this error
            reraise: Whether to re-raise the error after handling

        Returns:
            Error information dictionary

        Raises:
            Exception: Re-raises the error if reraise=True
        """
        # Convert to NBAMCPError if not already
        if isinstance(error, NBAMCPError):
            mcp_error = error
        else:
            mcp_error = ToolExecutionError(
                str(error),
                details={
                    "original_type": type(error).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

        # Track error
        error_key = f"{mcp_error.category.value}:{type(error).__name__}"
        self.error_counts[error_key] += 1

        # Add to history
        error_info = {
            "timestamp": datetime.now(),
            "error": mcp_error,
            "context": context.to_dict() if context else {},
        }
        self.error_history.append(error_info)
        self.error_rate_window.append(datetime.now())

        # Log error
        log_extra = {
            "error_category": mcp_error.category.value,
            "error_severity": mcp_error.severity.value,
            "error_code": getattr(mcp_error, "error_code", "UNKNOWN"),
        }

        if context:
            log_extra.update(context.to_dict())

        if mcp_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(
                f"Error [{mcp_error.category.value}]: {mcp_error.message}",
                extra=log_extra,
                exc_info=True,
            )
        else:
            logger.warning(
                f"Error [{mcp_error.category.value}]: {mcp_error.message}",
                extra=log_extra,
            )

        # Send alerts if enabled and severity is high
        if (
            self.enable_alerting
            and notify
            and mcp_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        ):
            self._send_alert(mcp_error, context)

        # Build response
        response = mcp_error.to_dict()
        if context:
            response["context"] = context.to_dict()

        # Re-raise if requested
        if reraise:
            raise error

        return response

    def _send_alert(self, error: NBAMCPError, context: Optional[ErrorContext]):
        """Send alert for critical error."""
        # Placeholder for alerting integration
        # In production, this would integrate with PagerDuty, Slack, etc.
        logger.critical(
            f"ALERT: {error.message}",
            extra={
                "alert": True,
                "error_severity": error.severity.value,
                "context": context.to_dict() if context else {},
            },
        )

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Circuit breaker name
            **kwargs: Circuit breaker configuration

        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.

        Returns:
            Dictionary with error statistics including:
            - Total errors
            - Errors by category
            - Error rate
            - Recent errors
            - Circuit breaker stats
        """
        # Calculate error rate (errors per minute)
        now = datetime.now()
        recent_errors = [
            ts for ts in self.error_rate_window if (now - ts).total_seconds() < 60
        ]
        error_rate = len(recent_errors)

        return {
            "total_errors": sum(self.error_counts.values()),
            "errors_by_type": dict(self.error_counts),
            "error_rate_per_minute": error_rate,
            "recent_errors": [
                {
                    "timestamp": e["timestamp"].isoformat(),
                    "error": e["error"].message,
                    "category": e["error"].category.value,
                    "severity": e["error"].severity.value,
                }
                for e in list(self.error_history)[-10:]
            ],
            "circuit_breakers": {
                name: breaker.get_stats()
                for name, breaker in self.circuit_breakers.items()
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get error statistics (alias for get_error_stats).

        Returns:
            Dictionary with error statistics
        """
        return self.get_error_stats()

    def clear_stats(self):
        """Clear error statistics (useful for testing)."""
        self.error_counts.clear()
        self.error_history.clear()
        self.error_rate_window.clear()


# ==============================================================================
# Global Error Handler Instance
# ==============================================================================

_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        Global ErrorHandler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_error_handler(handler: ErrorHandler):
    """
    Set the global error handler instance.

    Args:
        handler: ErrorHandler instance to use globally
    """
    global _global_error_handler
    _global_error_handler = handler


# ==============================================================================
# Convenience Decorators
# ==============================================================================


def handle_errors(
    context: Optional[Dict[str, Any]] = None,
    notify: bool = False,
    reraise: bool = True,
):
    """
    Decorator to automatically handle errors in a function.

    Args:
        context: Additional context to include with errors
        notify: Whether to send notifications for errors
        reraise: Whether to re-raise errors after handling

    Returns:
        Decorated function

    Examples:
        >>> @handle_errors(context={"tool": "query_database"})
        ... async def query_database(query: str):
        ...     return await db.execute(query)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = get_error_handler()
            error_context = ErrorContext(
                tool_name=func.__name__,
                operation=func.__name__,
                additional_context=context or {},
            )

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # handle_error will raise if reraise=True, otherwise return None
                handler.handle_error(e, error_context, notify, reraise)
                return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = get_error_handler()
            error_context = ErrorContext(
                tool_name=func.__name__,
                operation=func.__name__,
                additional_context=context or {},
            )

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # handle_error will raise if reraise=True, otherwise return None
                handler.handle_error(e, error_context, notify, reraise)
                return None

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
