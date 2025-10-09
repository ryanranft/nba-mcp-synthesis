#!/usr/bin/env python3
"""
Test Suite for Resilience Module
Tests retry logic, circuit breakers, connection pooling, and rate limiting
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import resilience module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.resilience import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    retry_with_backoff,
    retry_async,
    ConnectionPool,
    RateLimiter,
    get_circuit_breaker,
    with_mcp_retry,
    with_mcp_circuit_breaker
)


# ==============================================================================
# Circuit Breaker Tests
# ==============================================================================

class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_calls(self):
        """Test circuit breaker with all successful calls"""
        cb = CircuitBreaker(name="test", failure_threshold=3)

        @cb.call
        async def success_func():
            return "success"

        # Multiple successful calls
        for _ in range(5):
            result = await success_func()
            assert result == "success"
            assert cb.state == CircuitState.CLOSED
            assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        call_count = 0

        @cb.call
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Service unavailable")

        # First 3 failures should raise original exception
        for i in range(3):
            with pytest.raises(ConnectionError):
                await failing_func()

            if i < 2:
                assert cb.state == CircuitState.CLOSED
            else:
                assert cb.state == CircuitState.OPEN

        # 4th call should raise CircuitBreakerOpenError immediately
        with pytest.raises(CircuitBreakerOpenError):
            await failing_func()

        # Verify call_count didn't increase (circuit open)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_to_closed(self):
        """Test circuit breaker recovery from HALF_OPEN to CLOSED"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            success_threshold=2,
            timeout=1  # 1 second timeout
        )

        @cb.call
        async def func(should_fail=False):
            if should_fail:
                raise ConnectionError("Failure")
            return "success"

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await func(should_fail=True)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # First call after timeout should enter HALF_OPEN
        result = await func(should_fail=False)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1

        # Second successful call should close circuit
        result = await func(should_fail=False)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_reopens_on_failure(self):
        """Test circuit breaker reopens if HALF_OPEN call fails"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout=1
        )

        @cb.call
        async def func(should_fail=False):
            if should_fail:
                raise ConnectionError("Failure")
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await func(should_fail=True)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Fail during HALF_OPEN - should reopen
        with pytest.raises(ConnectionError):
            await func(should_fail=True)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreaker(name="test", failure_threshold=2)

        @cb.call
        async def failing_func():
            raise ConnectionError("Failure")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await failing_func()

        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0


# ==============================================================================
# Retry with Backoff Tests
# ==============================================================================

class TestRetryWithBackoff:
    """Test retry with exponential backoff"""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test no retry needed on first success"""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful retry after initial failures"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1, jitter=False)
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        start_time = time.time()
        result = await eventually_succeeds()
        elapsed = time.time() - start_time

        assert result == "success"
        assert call_count == 3
        # Should have delays: 0.1, 0.2 = ~0.3s total
        assert 0.2 < elapsed < 0.5

    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """Test failure after max retries"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.05)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError, match="Permanent failure"):
            await always_fails()

        assert call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff timing"""
        delays = []
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False
        )
        async def track_delays():
            nonlocal call_count
            if call_count > 0:
                delays.append(time.time())
            call_count += 1
            if call_count < 4:
                raise ConnectionError("Failure")
            return "success"

        await track_delays()

        # Calculate actual delays
        actual_delays = [delays[i] - delays[i-1] for i in range(1, len(delays))]

        # Expected delays: 0.1, 0.2, 0.4
        expected = [0.1, 0.2, 0.4]
        for actual, expected_val in zip(actual_delays, expected):
            assert abs(actual - expected_val) < 0.25  # 250ms tolerance for CI/CD variability

    @pytest.mark.asyncio
    async def test_retry_max_delay_cap(self):
        """Test max_delay caps exponential backoff"""
        call_count = 0

        @retry_with_backoff(
            max_retries=5,
            base_delay=1.0,
            max_delay=2.0,
            exponential_base=2.0,
            jitter=False
        )
        async def capped_delays():
            nonlocal call_count
            call_count += 1
            if call_count < 6:
                raise ConnectionError("Failure")
            return "success"

        start_time = time.time()
        await capped_delays()
        elapsed = time.time() - start_time

        # Delays: 1.0, 2.0, 2.0, 2.0, 2.0 = 9.0s total
        # (2nd delay would be 2.0, capped; 3rd would be 4.0, capped to 2.0, etc.)
        assert 8.5 < elapsed < 10.0

    @pytest.mark.asyncio
    async def test_retry_specific_exceptions(self):
        """Test retry only on specific exceptions"""
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.05,
            retry_on=(ConnectionError, TimeoutError)
        )
        async def specific_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Retry this")
            elif call_count == 2:
                raise ValueError("Don't retry this")
            return "success"

        # ValueError should not be retried
        with pytest.raises(ValueError, match="Don't retry this"):
            await specific_errors()

        assert call_count == 2  # Initial + 1 retry


# ==============================================================================
# Retry Async (Functional) Tests
# ==============================================================================

class TestRetryAsync:
    """Test functional retry wrapper"""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test retry_async with successful call"""
        call_count = 0

        async def func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(func, max_retries=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_with_args(self):
        """Test retry_async with arguments"""
        async def func(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await retry_async(
            func,
            "arg1",
            "arg2",
            c="kwarg",
            max_retries=2
        )
        assert result == "arg1-arg2-kwarg"

    @pytest.mark.asyncio
    async def test_retry_async_failure(self):
        """Test retry_async with failures"""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Failed")

        with pytest.raises(ConnectionError):
            await retry_async(failing_func, max_retries=2, base_delay=0.05)

        assert call_count == 3  # Initial + 2 retries


# ==============================================================================
# Connection Pool Tests
# ==============================================================================

class TestConnectionPool:
    """Test connection pool functionality"""

    @pytest.mark.asyncio
    async def test_connection_pool_acquire_new(self):
        """Test acquiring new connection from empty pool"""
        pool = ConnectionPool(max_size=5)

        class MockConnection:
            def __init__(self, conn_id):
                self.id = conn_id

        async def create_connection():
            return MockConnection("conn1")

        conn = await pool.acquire(create_connection)
        assert conn.id == "conn1"
        assert len(pool.in_use) == 1

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self):
        """Test connection reuse from pool"""
        pool = ConnectionPool(max_size=5)
        connection_ids = []

        class MockConnection:
            def __init__(self, conn_id):
                self.id = conn_id

        async def create_connection():
            conn_id = len(connection_ids)
            connection_ids.append(conn_id)
            return MockConnection(conn_id)

        # Acquire and release
        conn1 = await pool.acquire(create_connection)
        await pool.release(conn1)

        # Acquire again - should reuse
        conn2 = await pool.acquire(create_connection)

        assert conn1 is conn2  # Same object
        assert len(connection_ids) == 1  # Only one connection created

    @pytest.mark.asyncio
    async def test_connection_pool_max_size(self):
        """Test connection pool respects max_size"""
        pool = ConnectionPool(max_size=2)

        class MockConnection:
            def __init__(self, conn_id):
                self.id = conn_id

        async def create_connection():
            return MockConnection(time.time())

        # Acquire max connections
        conn1 = await pool.acquire(create_connection)
        conn2 = await pool.acquire(create_connection)

        # Third acquire should fail (pool exhausted)
        with pytest.raises(RuntimeError, match="pool exhausted"):
            await pool.acquire(create_connection)

        # Release one and try again
        await pool.release(conn1)
        conn3 = await pool.acquire(create_connection)
        assert conn3 is conn1  # Reused

    @pytest.mark.asyncio
    async def test_connection_pool_close_all(self):
        """Test closing all connections"""
        pool = ConnectionPool(max_size=3)

        class MockConnection:
            def __init__(self):
                self.closed = False

            async def close(self):
                self.closed = True

        async def create_connection():
            return MockConnection()

        # Create connections
        conn1 = await pool.acquire(create_connection)
        conn2 = await pool.acquire(create_connection)
        await pool.release(conn1)
        await pool.release(conn2)

        # Close all
        await pool.close_all()

        assert len(pool.connections) == 0
        assert len(pool.in_use) == 0
        assert conn1.closed
        assert conn2.closed


# ==============================================================================
# Rate Limiter Tests
# ==============================================================================

class TestRateLimiter:
    """Test token bucket rate limiter"""

    @pytest.mark.asyncio
    async def test_rate_limiter_initial_capacity(self):
        """Test rate limiter starts with full capacity"""
        limiter = RateLimiter(rate=10.0, capacity=10)

        # Should be able to acquire full capacity immediately
        for _ in range(10):
            acquired = await limiter.acquire(1)
            assert acquired is True

        # 11th should fail
        acquired = await limiter.acquire(1)
        assert acquired is False

    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """Test rate limiter token refill over time"""
        limiter = RateLimiter(rate=10.0, capacity=10)

        # Consume all tokens
        for _ in range(10):
            await limiter.acquire(1)

        # Should fail immediately
        acquired = await limiter.acquire(1)
        assert acquired is False

        # Wait for refill (0.2s = 2 tokens at 10/s)
        await asyncio.sleep(0.2)

        # Should be able to acquire 2 tokens
        acquired = await limiter.acquire(1)
        assert acquired is True
        acquired = await limiter.acquire(1)
        assert acquired is True

        # 3rd should fail
        acquired = await limiter.acquire(1)
        assert acquired is False

    @pytest.mark.asyncio
    async def test_rate_limiter_wait_for_token(self):
        """Test wait_for_token blocks until available"""
        limiter = RateLimiter(rate=10.0, capacity=5)

        # Consume all tokens
        for _ in range(5):
            await limiter.acquire(1)

        # wait_for_token should block until token available
        start = time.time()
        await limiter.wait_for_token(1)
        elapsed = time.time() - start

        # Should wait ~0.1s for 1 token (1/10 = 0.1)
        assert 0.05 < elapsed < 0.2

    @pytest.mark.asyncio
    async def test_rate_limiter_capacity_cap(self):
        """Test rate limiter doesn't exceed capacity"""
        limiter = RateLimiter(rate=100.0, capacity=5)

        # Wait for potential overflow
        await asyncio.sleep(0.2)  # 20 tokens would accumulate without cap

        # Should only be able to acquire capacity (5)
        success_count = 0
        for _ in range(10):
            if await limiter.acquire(1):
                success_count += 1

        assert success_count == 5


# ==============================================================================
# Global Circuit Breaker Tests
# ==============================================================================

class TestGlobalCircuitBreakers:
    """Test global circuit breaker registry"""

    def test_get_circuit_breaker_creates_new(self):
        """Test get_circuit_breaker creates new instance"""
        cb = get_circuit_breaker("test_service", failure_threshold=10)
        assert cb.name == "test_service"
        assert cb.failure_threshold == 10

    def test_get_circuit_breaker_returns_same_instance(self):
        """Test get_circuit_breaker returns same instance for same name"""
        cb1 = get_circuit_breaker("test_service2")
        cb2 = get_circuit_breaker("test_service2")
        assert cb1 is cb2


# ==============================================================================
# Decorator Helper Tests
# ==============================================================================

class TestDecoratorHelpers:
    """Test convenience decorator helpers"""

    @pytest.mark.asyncio
    async def test_with_mcp_retry(self):
        """Test with_mcp_retry decorator"""
        call_count = 0

        @with_mcp_retry
        async def mcp_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await mcp_operation()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_with_mcp_circuit_breaker(self):
        """Test with_mcp_circuit_breaker decorator"""
        # Reset circuit breaker
        cb = get_circuit_breaker("mcp_server")
        cb.reset()

        @with_mcp_circuit_breaker
        async def mcp_operation(should_fail=False):
            if should_fail:
                raise ConnectionError("Service down")
            return "success"

        # Should succeed
        result = await mcp_operation(should_fail=False)
        assert result == "success"

        # Fail enough times to open circuit
        for _ in range(5):
            with pytest.raises(ConnectionError):
                await mcp_operation(should_fail=True)

        # Circuit should be open
        assert cb.state == CircuitState.OPEN

        # Should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await mcp_operation(should_fail=False)


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Test combined resilience features"""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Test retry logic with circuit breaker"""
        cb = CircuitBreaker(name="integration_test", failure_threshold=3)
        cb.reset()

        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.05)
        @cb.call
        async def resilient_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        # Retry is outer decorator, circuit breaker is inner
        # Each retry calls the circuit breaker
        # With 2 retries, we get 3 total calls to circuit breaker
        # Need 3 failures to open circuit, so 1 call should open it

        with pytest.raises(ConnectionError):
            await resilient_operation()

        # Circuit should be open after 3 failures (1 initial + 2 retries)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rate_limited_with_retry(self):
        """Test rate limiting with retry logic"""
        limiter = RateLimiter(rate=5.0, capacity=2)

        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def rate_limited_operation():
            nonlocal call_count
            call_count += 1

            if not await limiter.acquire(1):
                raise Exception("Rate limit exceeded")

            return "success"

        # First 2 should succeed immediately
        await rate_limited_operation()
        await rate_limited_operation()

        # 3rd should retry until tokens available
        start = time.time()
        result = await rate_limited_operation()
        elapsed = time.time() - start

        assert result == "success"
        # Should have waited for refill
        assert elapsed > 0.1


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
