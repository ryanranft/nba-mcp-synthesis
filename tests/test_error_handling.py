"""
Comprehensive tests for error handling module.

Tests all error handling functionality including:
- Custom exceptions
- Error handler
- Retry decorator
- Circuit breaker
- Error recovery
- Error context
- Error statistics

Author: NBA MCP Server Team
Date: 2025-01-18
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from mcp_server.error_handling import (
    # Exceptions
    DataValidationError,
    ToolExecutionError,
    ConfigurationError,
    ServiceUnavailableError,
    CircuitBreakerOpenError,
    # Error context
    ErrorContext,
    # Retry logic
    RetryStrategy,
    RetryConfig,
    with_retry,
    # Circuit breaker
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerStats,
    # Error handler
    ErrorHandler,
    get_error_handler,
    set_error_handler,
    handle_errors,
)
from mcp_server.error_handler import (
    ErrorCategory,
    ErrorSeverity,
)


# ==============================================================================
# Test Custom Exceptions
# ==============================================================================


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_data_validation_error(self):
        """Test DataValidationError creation and attributes."""
        error = DataValidationError(
            "Invalid data", details={"field": "points", "value": -5}
        )

        assert "Invalid data" in str(error)
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.details["field"] == "points"
        assert error.error_code == "DATA_VALIDATION_ERROR"

    def test_tool_execution_error(self):
        """Test ToolExecutionError creation and attributes."""
        error = ToolExecutionError(
            "Tool failed", details={"tool": "query_database", "query": "SELECT *"}
        )

        assert "Tool failed" in str(error)
        assert error.category == ErrorCategory.INTERNAL
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["tool"] == "query_database"
        assert error.error_code == "TOOL_EXECUTION_ERROR"

    def test_configuration_error(self):
        """Test ConfigurationError creation and attributes."""
        error = ConfigurationError(
            "Missing config", details={"config_key": "DATABASE_URL"}
        )

        assert "Missing config" in str(error)
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.details["config_key"] == "DATABASE_URL"
        assert error.error_code == "CONFIGURATION_ERROR"

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError creation and attributes."""
        error = ServiceUnavailableError(
            "Service down", details={"service": "database", "retry_after": 60}
        )

        assert "Service down" in str(error)
        assert error.category == ErrorCategory.EXTERNAL_API
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["service"] == "database"
        assert error.error_code == "SERVICE_UNAVAILABLE"

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError creation and attributes."""
        error = CircuitBreakerOpenError(
            "Circuit open", details={"failure_count": 5, "retry_after": 30}
        )

        assert "Circuit open" in str(error)
        assert error.category == ErrorCategory.INTERNAL
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["failure_count"] == 5
        assert error.error_code == "CIRCUIT_BREAKER_OPEN"

    def test_error_to_dict(self):
        """Test error serialization to dictionary."""
        error = DataValidationError("Invalid data", details={"field": "points"})

        error_dict = error.to_dict()

        assert error_dict["error"] == "Invalid data"
        assert error_dict["category"] == "validation"
        assert error_dict["severity"] == "low"
        assert error_dict["details"]["field"] == "points"
        assert "timestamp" in error_dict


# ==============================================================================
# Test Error Context
# ==============================================================================


class TestErrorContext:
    """Test ErrorContext class."""

    def test_error_context_creation(self):
        """Test basic ErrorContext creation."""
        context = ErrorContext(
            tool_name="query_database",
            user_id="user_123",
            request_id="req_456",
            operation="SELECT query",
        )

        assert context.tool_name == "query_database"
        assert context.user_id == "user_123"
        assert context.request_id == "req_456"
        assert context.operation == "SELECT query"
        assert isinstance(context.timestamp, datetime)

    def test_error_context_to_dict(self):
        """Test ErrorContext serialization."""
        context = ErrorContext(
            tool_name="query_database",
            user_id="user_123",
            additional_context={"query": "SELECT *"},
        )

        context_dict = context.to_dict()

        assert context_dict["tool_name"] == "query_database"
        assert context_dict["user_id"] == "user_123"
        assert context_dict["additional_context"]["query"] == "SELECT *"
        assert "timestamp" in context_dict

    def test_error_context_defaults(self):
        """Test ErrorContext with default values."""
        context = ErrorContext()

        assert context.tool_name is None
        assert context.user_id is None
        assert context.request_id is None
        assert context.operation is None
        assert isinstance(context.timestamp, datetime)
        assert isinstance(context.additional_context, dict)


# ==============================================================================
# Test Retry Logic
# ==============================================================================


class TestRetryLogic:
    """Test retry logic and strategies."""

    def test_retry_config_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        # Test delays
        assert config.calculate_delay(0) == 1.0  # 1 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_retry_config_linear_backoff(self):
        """Test linear backoff calculation."""
        config = RetryConfig(
            base_delay=1.0, strategy=RetryStrategy.LINEAR_BACKOFF, jitter=False
        )

        assert config.calculate_delay(0) == 1.0  # 1 * (0 + 1)
        assert config.calculate_delay(1) == 2.0  # 1 * (1 + 1)
        assert config.calculate_delay(2) == 3.0  # 1 * (2 + 1)

    def test_retry_config_fixed_delay(self):
        """Test fixed delay strategy."""
        config = RetryConfig(
            base_delay=2.0, strategy=RetryStrategy.FIXED_DELAY, jitter=False
        )

        assert config.calculate_delay(0) == 2.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 2.0

    def test_retry_config_max_delay(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0, backoff_factor=2.0, max_delay=5.0, jitter=False
        )

        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 5.0  # Capped at max
        assert config.calculate_delay(4) == 5.0  # Still capped

    def test_retry_config_fibonacci_backoff(self):
        """Test Fibonacci backoff strategy."""
        config = RetryConfig(
            base_delay=1.0, strategy=RetryStrategy.FIBONACCI_BACKOFF, jitter=False
        )

        # Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13...
        assert config.calculate_delay(0) == 1.0  # 1 * fib(1) = 1
        assert config.calculate_delay(1) == 2.0  # 1 * fib(2) = 2
        assert config.calculate_delay(2) == 3.0  # 1 * fib(3) = 3
        assert config.calculate_delay(3) == 5.0  # 1 * fib(4) = 5

    def test_retry_decorator_success(self):
        """Test retry decorator with successful call."""
        call_count = 0

        @with_retry(max_retries=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1  # Should succeed on first try

    def test_retry_decorator_failure_then_success(self):
        """Test retry decorator with initial failures."""
        call_count = 0

        @with_retry(max_retries=3, backoff_factor=0.1)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_then_success()

        assert result == "success"
        assert call_count == 3  # Should succeed on third try

    def test_retry_decorator_all_failures(self):
        """Test retry decorator when all attempts fail."""
        call_count = 0

        @with_retry(max_retries=3, backoff_factor=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError, match="Permanent failure"):
            always_fails()

        assert call_count == 4  # Initial + 3 retries

    def test_retry_decorator_specific_exceptions(self):
        """Test retry decorator with specific exception types."""
        call_count = 0

        @with_retry(max_retries=3, retry_on=(ValueError,), backoff_factor=0.1)
        def raises_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            raise TypeError("Non-retryable error")

        with pytest.raises(TypeError):
            raises_different_exceptions()

        assert call_count == 2  # Initial call + 1 retry for ValueError

    @pytest.mark.asyncio
    async def test_retry_decorator_async(self):
        """Test retry decorator with async function."""
        call_count = 0

        @with_retry(max_retries=3, backoff_factor=0.1)
        async def async_failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "async_success"

        result = await async_failing_then_success()

        assert result == "async_success"
        assert call_count == 2

    def test_retry_with_callback(self):
        """Test retry decorator with on_retry callback."""
        retry_attempts = []

        def on_retry_callback(error, attempt):
            retry_attempts.append((type(error).__name__, attempt))

        @with_retry(max_retries=3, backoff_factor=0.1, on_retry=on_retry_callback)
        def fails_twice():
            if len(retry_attempts) < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = fails_twice()

        assert result == "success"
        assert len(retry_attempts) == 2
        assert retry_attempts[0] == ("ValueError", 0)
        assert retry_attempts[1] == ("ValueError", 1)


# ==============================================================================
# Test Circuit Breaker
# ==============================================================================


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_breaker_creation(self):
        """Test basic circuit breaker creation."""
        breaker = CircuitBreaker(name="test_breaker", failure_threshold=5, timeout=60)

        assert breaker.name == "test_breaker"
        assert breaker.failure_threshold == 5
        assert breaker.timeout == 60
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        # Record failures
        for i in range(3):
            breaker.record_failure()

        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.stats.failure_count == 3
        assert breaker.stats.consecutive_failures == 3

    def test_circuit_breaker_stays_closed_with_successes(self):
        """Test that circuit breaker stays closed with successes."""
        breaker = CircuitBreaker(name="test", failure_threshold=5)

        # Mix of failures and successes
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        breaker.record_failure()

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.stats.consecutive_failures == 1

    def test_circuit_breaker_half_open_transition(self):
        """Test transition to half-open state after timeout."""
        breaker = CircuitBreaker(
            name="test", failure_threshold=2, timeout=1  # 1 second timeout
        )

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Should allow call and transition to half-open
        assert breaker._should_allow_call()
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_closes_after_successes(self):
        """Test that circuit breaker closes after successful calls in half-open."""
        breaker = CircuitBreaker(
            name="test", failure_threshold=2, success_threshold=2, timeout=1
        )

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

        # Transition to half-open
        time.sleep(1.1)
        breaker._should_allow_call()
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        # Record successes to close
        breaker.record_success()
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        breaker.record_success()
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test that circuit reopens on failure during half-open."""
        breaker = CircuitBreaker(name="test", failure_threshold=2, timeout=1)

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()

        # Transition to half-open
        time.sleep(1.1)
        breaker._should_allow_call()
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        # Failure reopens circuit
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker decorator with successful calls."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        @breaker.protect
        def successful_function():
            return "success"

        result = successful_function()

        assert result == "success"
        assert breaker.stats.success_count == 1
        assert breaker.stats.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_decorator_opens_on_failures(self):
        """Test circuit breaker decorator opens after failures."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        call_count = 0

        @breaker.protect
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        # Make failing calls
        for i in range(3):
            with pytest.raises(ValueError):
                failing_function()

        assert breaker.state == CircuitBreakerState.OPEN
        assert call_count == 3

        # Circuit should now block calls
        with pytest.raises(CircuitBreakerOpenError):
            failing_function()

        # Call count shouldn't increase when circuit is open
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_decorator(self):
        """Test circuit breaker with async functions."""
        breaker = CircuitBreaker(name="test_async", failure_threshold=3)

        @breaker.protect
        async def async_function():
            return "async_success"

        result = await async_function()

        assert result == "async_success"
        assert breaker.stats.success_count == 1

    def test_circuit_breaker_callbacks(self):
        """Test circuit breaker open/close callbacks."""
        opened = []
        closed = []

        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            success_threshold=1,
            timeout=1,
            on_open=lambda: opened.append(True),
            on_close=lambda: closed.append(True),
        )

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert len(opened) == 1

        # Transition to half-open and close
        time.sleep(1.1)
        breaker._should_allow_call()
        breaker.record_success()
        assert len(closed) == 1

    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        breaker.record_success()
        breaker.record_success()
        breaker.record_failure()
        breaker.record_failure()

        stats = breaker.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["stats"]["success_count"] == 2
        assert stats["stats"]["failure_count"] == 2
        assert stats["stats"]["consecutive_failures"] == 2


# ==============================================================================
# Test Error Handler
# ==============================================================================


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_error_handler_creation(self):
        """Test basic error handler creation."""
        handler = ErrorHandler()

        assert handler.enable_alerting is False
        assert len(handler.error_counts) == 0
        assert len(handler.circuit_breakers) == 0

    def test_error_handler_handle_error(self):
        """Test error handling."""
        handler = ErrorHandler()

        error = DataValidationError("Invalid data")
        context = ErrorContext(tool_name="test_tool")

        # Should not raise if reraise=False
        result = handler.handle_error(error, context, reraise=False)

        assert "error" in result
        assert "context" in result
        assert handler.error_counts["validation:DataValidationError"] == 1

    def test_error_handler_wraps_unknown_errors(self):
        """Test that unknown errors are wrapped."""
        handler = ErrorHandler()

        error = RuntimeError("Unknown error")

        with pytest.raises(RuntimeError):
            handler.handle_error(error, reraise=True)

        # Should have tracked as internal error
        assert any("internal:" in key for key in handler.error_counts.keys())

    def test_error_handler_tracks_multiple_errors(self):
        """Test tracking multiple errors."""
        handler = ErrorHandler()

        # Generate multiple errors
        for i in range(3):
            handler.handle_error(DataValidationError(f"Error {i}"), reraise=False)

        for i in range(2):
            handler.handle_error(ToolExecutionError(f"Error {i}"), reraise=False)

        assert handler.error_counts["validation:DataValidationError"] == 3
        assert handler.error_counts["internal:ToolExecutionError"] == 2

    def test_error_handler_error_history(self):
        """Test error history tracking."""
        handler = ErrorHandler()

        errors = [
            DataValidationError("Error 1"),
            ToolExecutionError("Error 2"),
            ConfigurationError("Error 3"),
        ]

        for error in errors:
            handler.handle_error(error, reraise=False)

        assert len(handler.error_history) == 3

    def test_error_handler_get_stats(self):
        """Test getting error statistics."""
        handler = ErrorHandler()

        # Generate some errors
        handler.handle_error(DataValidationError("Error 1"), reraise=False)
        handler.handle_error(DataValidationError("Error 2"), reraise=False)
        handler.handle_error(ToolExecutionError("Error 3"), reraise=False)

        stats = handler.get_stats()

        assert stats["total_errors"] == 3
        assert len(stats["errors_by_type"]) == 2
        assert "recent_errors" in stats
        assert len(stats["recent_errors"]) == 3

    def test_error_handler_error_rate(self):
        """Test error rate calculation."""
        handler = ErrorHandler()

        # Generate errors
        for i in range(5):
            handler.handle_error(DataValidationError(f"Error {i}"), reraise=False)

        stats = handler.get_stats()

        assert stats["error_rate_per_minute"] == 5

    def test_error_handler_circuit_breaker_management(self):
        """Test circuit breaker creation and management."""
        handler = ErrorHandler()

        # Get or create circuit breaker
        breaker1 = handler.get_circuit_breaker("test_breaker", failure_threshold=5)
        breaker2 = handler.get_circuit_breaker("test_breaker")

        assert breaker1 is breaker2  # Should return same instance
        assert breaker1.name == "test_breaker"
        assert breaker1.failure_threshold == 5

        stats = handler.get_error_stats()
        assert "test_breaker" in stats["circuit_breakers"]

    def test_error_handler_clear_stats(self):
        """Test clearing error statistics."""
        handler = ErrorHandler()

        # Generate errors
        handler.handle_error(DataValidationError("Error"), reraise=False)
        handler.handle_error(ToolExecutionError("Error"), reraise=False)

        assert handler.get_stats()["total_errors"] == 2

        # Clear stats
        handler.clear_stats()

        assert handler.get_stats()["total_errors"] == 0
        assert len(handler.error_counts) == 0

    @patch("mcp_server.error_handling.logger")
    def test_error_handler_logging(self, mock_logger):
        """Test that errors are logged appropriately."""
        handler = ErrorHandler()

        # High severity error
        handler.handle_error(ConfigurationError("Critical error"), reraise=False)

        # Should log as error
        mock_logger.error.assert_called()

        # Low severity error
        handler.handle_error(DataValidationError("Minor error"), reraise=False)

        # Should log as warning
        mock_logger.warning.assert_called()


# ==============================================================================
# Test Global Error Handler
# ==============================================================================


class TestGlobalErrorHandler:
    """Test global error handler instance."""

    def test_get_global_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()

        assert handler1 is handler2  # Should return same instance

    def test_set_global_error_handler(self):
        """Test setting global error handler."""
        custom_handler = ErrorHandler(enable_alerting=True)
        set_error_handler(custom_handler)

        handler = get_error_handler()

        assert handler is custom_handler
        assert handler.enable_alerting is True

        # Reset for other tests
        set_error_handler(ErrorHandler())


# ==============================================================================
# Test Decorators
# ==============================================================================


class TestDecorators:
    """Test convenience decorators."""

    def test_handle_errors_decorator_success(self):
        """Test handle_errors decorator with successful function."""
        handler = ErrorHandler()
        set_error_handler(handler)

        @handle_errors(context={"test": "value"})
        def successful_function():
            return "success"

        result = successful_function()

        assert result == "success"
        assert handler.get_stats()["total_errors"] == 0

    def test_handle_errors_decorator_with_error(self):
        """Test handle_errors decorator with error."""
        handler = ErrorHandler()
        set_error_handler(handler)

        @handle_errors(context={"test": "value"}, reraise=False)
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()

        assert result is None  # Returns None when reraise=False
        assert handler.get_stats()["total_errors"] == 1

    def test_handle_errors_decorator_reraise(self):
        """Test handle_errors decorator with reraise."""
        handler = ErrorHandler()
        set_error_handler(handler)

        @handle_errors(reraise=True)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        assert handler.get_stats()["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_handle_errors_async_decorator(self):
        """Test handle_errors decorator with async function."""
        handler = ErrorHandler()
        set_error_handler(handler)

        @handle_errors(context={"test": "async"})
        async def async_function():
            return "async_success"

        result = await async_function()

        assert result == "async_success"
        assert handler.get_stats()["total_errors"] == 0


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_retry_with_circuit_breaker(self):
        """Test combining retry logic with circuit breaker."""
        handler = ErrorHandler()
        breaker = handler.get_circuit_breaker("test", failure_threshold=2)
        call_count = 0

        @breaker.protect
        @with_retry(max_retries=2, backoff_factor=0.1)
        def function_with_both():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        # First attempt: retries 3 times (initial + 2 retries)
        with pytest.raises(ValueError):
            function_with_both()

        assert call_count == 3
        assert breaker.stats.failure_count == 1

        # Second attempt: retries 3 times, opens circuit
        call_count = 0
        with pytest.raises(ValueError):
            function_with_both()

        assert call_count == 3
        assert breaker.state == CircuitBreakerState.OPEN

        # Third attempt: circuit blocks immediately
        call_count = 0
        with pytest.raises(CircuitBreakerOpenError):
            function_with_both()

        assert call_count == 0  # Circuit blocked call

    def test_error_handler_with_context_and_retry(self):
        """Test error handler with context and retry."""
        handler = ErrorHandler()
        set_error_handler(handler)
        attempt_count = 0

        @handle_errors(context={"operation": "test"}, reraise=False)
        @with_retry(max_retries=2, backoff_factor=0.1)
        def function_with_context_and_retry():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = function_with_context_and_retry()

        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_full_error_handling_flow(self):
        """Test complete error handling flow."""
        handler = ErrorHandler()
        set_error_handler(handler)
        breaker = handler.get_circuit_breaker("integration_test", failure_threshold=3)

        success_count = 0
        failure_count = 0

        @handle_errors(context={"flow": "integration"}, reraise=False)
        @breaker.protect
        @with_retry(max_retries=2, backoff_factor=0.1)
        async def complex_operation(should_succeed: bool):
            nonlocal success_count, failure_count
            if should_succeed:
                success_count += 1
                return "success"
            else:
                failure_count += 1
                raise ValueError("Operation failed")

        # Successful operations
        result1 = await complex_operation(True)
        result2 = await complex_operation(True)

        assert result1 == "success"
        assert result2 == "success"
        assert success_count == 2

        # Failed operations (3 times to open circuit)
        for _ in range(3):
            await complex_operation(False)

        # Circuit should be open
        assert breaker.state == CircuitBreakerState.OPEN

        # Next call should be blocked by circuit
        initial_failure_count = failure_count
        await complex_operation(False)

        # Failure count shouldn't increase (circuit blocked)
        assert failure_count == initial_failure_count  # Circuit blocks execution


# ==============================================================================
# Performance Tests
# ==============================================================================


class TestPerformance:
    """Test performance of error handling."""

    def test_retry_performance(self):
        """Test that retry logic doesn't add significant overhead."""

        @with_retry(max_retries=0)  # No retries
        def fast_function():
            return "result"

        start_time = time.time()
        for _ in range(1000):
            fast_function()
        elapsed = time.time() - start_time

        # Should complete 1000 calls in under 0.1 seconds
        assert elapsed < 0.1

    def test_circuit_breaker_performance(self):
        """Test circuit breaker performance."""
        breaker = CircuitBreaker(name="perf_test", failure_threshold=10)

        @breaker.protect
        def fast_function():
            return "result"

        start_time = time.time()
        for _ in range(1000):
            fast_function()
        elapsed = time.time() - start_time

        # Should complete 1000 calls in under 0.1 seconds
        assert elapsed < 0.1

    def test_error_handler_performance(self):
        """Test error handler performance with many errors."""
        handler = ErrorHandler()

        start_time = time.time()
        for i in range(1000):
            handler.handle_error(DataValidationError(f"Error {i}"), reraise=False)
        elapsed = time.time() - start_time

        # Should handle 1000 errors in under 1 second
        assert elapsed < 1.0
        assert handler.get_stats()["total_errors"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
