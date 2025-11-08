"""
Tests for Performance Profiling

Tests profiling decorators, metrics tracking, and bottleneck identification.
"""

import pytest
import time
import asyncio
from mcp_server.profiling.performance import (
    PerformanceProfiler,
    profile,
    profile_async,
    ProfileResult,
    get_profiler
)


class TestPerformanceProfiler:
    """Test suite for PerformanceProfiler"""

    @pytest.fixture
    def profiler(self):
        """Create profiler instance"""
        return PerformanceProfiler(
            enabled=True,
            track_memory=False,
            slow_threshold_ms=50.0
        )

    def test_profiler_initialization(self):
        """Test profiler initializes correctly"""
        profiler = PerformanceProfiler(
            enabled=True,
            track_memory=True,
            slow_threshold_ms=100.0
        )

        assert profiler.enabled is True
        assert profiler.track_memory is True
        assert profiler.slow_threshold_ms == 100.0
        assert len(profiler.profiles) == 0

    def test_record_profile_result(self, profiler):
        """Test recording profile results"""
        result = ProfileResult(
            function_name="test.function",
            execution_time_ms=25.5
        )

        profiler.record(result)

        assert "test.function" in profiler.profiles
        assert len(profiler.profiles["test.function"]) == 1
        assert profiler.total_calls == 1
        assert profiler.total_time_ms == 25.5

    def test_get_function_stats(self, profiler):
        """Test getting aggregated function stats"""
        # Record multiple results
        for i in range(5):
            result = ProfileResult(
                function_name="test.function",
                execution_time_ms=10.0 + i
            )
            profiler.record(result)

        stats = profiler.get_function_stats("test.function")

        assert stats is not None
        assert stats["call_count"] == 5
        assert stats["min_time_ms"] == 10.0
        assert stats["max_time_ms"] == 14.0
        assert stats["avg_time_ms"] == 12.0

    def test_get_nonexistent_function_stats(self, profiler):
        """Test getting stats for function that wasn't profiled"""
        stats = profiler.get_function_stats("nonexistent.function")
        assert stats is None

    def test_get_slowest_functions(self, profiler):
        """Test identifying slowest functions"""
        # Create functions with different speeds
        functions = [
            ("fast.function", 5.0),
            ("medium.function", 25.0),
            ("slow.function", 100.0),
            ("very_slow.function", 200.0)
        ]

        for func_name, exec_time in functions:
            for _ in range(3):
                result = ProfileResult(
                    function_name=func_name,
                    execution_time_ms=exec_time
                )
                profiler.record(result)

        slowest = profiler.get_slowest_functions(n=2)

        assert len(slowest) == 2
        assert slowest[0]["function_name"] == "very_slow.function"
        assert slowest[1]["function_name"] == "slow.function"

    def test_get_most_called_functions(self, profiler):
        """Test identifying most frequently called functions"""
        # Create functions with different call counts
        for i in range(10):
            profiler.record(ProfileResult("frequent.function", 10.0))

        for i in range(5):
            profiler.record(ProfileResult("medium.function", 10.0))

        for i in range(2):
            profiler.record(ProfileResult("rare.function", 10.0))

        most_called = profiler.get_most_called_functions(n=2)

        assert len(most_called) == 2
        assert most_called[0]["function_name"] == "frequent.function"
        assert most_called[0]["call_count"] == 10
        assert most_called[1]["function_name"] == "medium.function"
        assert most_called[1]["call_count"] == 5

    def test_identify_bottlenecks(self, profiler):
        """Test bottleneck identification"""
        # Create a bottleneck (called frequently AND slow)
        for _ in range(20):
            profiler.record(ProfileResult("bottleneck.function", 75.0))

        # Fast but frequent (not a bottleneck)
        for _ in range(100):
            profiler.record(ProfileResult("fast.frequent", 5.0))

        # Slow but rare (not a bottleneck)
        for _ in range(3):
            profiler.record(ProfileResult("slow.rare", 150.0))

        bottlenecks = profiler.identify_bottlenecks(
            time_threshold_ms=50.0,
            call_threshold=10
        )

        # Only bottleneck.function should be identified
        assert len(bottlenecks) >= 1
        assert bottlenecks[0]["function_name"] == "bottleneck.function"
        assert "recommendations" in bottlenecks[0]

    def test_reset(self, profiler):
        """Test resetting profiler data"""
        # Add some data
        profiler.record(ProfileResult("test.function", 10.0))
        profiler.record(ProfileResult("test.function", 20.0))

        assert len(profiler.profiles) > 0
        assert profiler.total_calls > 0

        # Reset
        profiler.reset()

        assert len(profiler.profiles) == 0
        assert profiler.total_calls == 0
        assert profiler.total_time_ms == 0.0

    def test_get_summary(self, profiler):
        """Test getting profiler summary"""
        # Add some data
        for i in range(5):
            profiler.record(ProfileResult(f"func{i}", 10.0 * (i + 1)))

        summary = profiler.get_summary()

        assert summary["enabled"] is True
        assert summary["total_functions_profiled"] == 5
        assert summary["total_calls"] == 5
        assert summary["total_time_ms"] == 150.0  # 10+20+30+40+50
        assert summary["avg_time_per_call_ms"] == 30.0

    def test_disabled_profiler(self):
        """Test that disabled profiler doesn't record"""
        profiler = PerformanceProfiler(enabled=False)

        profiler.record(ProfileResult("test.function", 10.0))

        assert len(profiler.profiles) == 0
        assert profiler.total_calls == 0


class TestProfileDecorator:
    """Test suite for @profile decorator"""

    @pytest.fixture
    def test_profiler(self):
        """Create clean profiler for testing"""
        profiler = PerformanceProfiler()
        profiler.reset()
        return profiler

    def test_profile_simple_function(self, test_profiler):
        """Test profiling a simple function"""
        @profile(profiler=test_profiler)
        def simple_function(x):
            return x * 2

        result = simple_function(5)

        assert result == 10
        assert len(test_profiler.profiles) == 1

        # Check that function was profiled
        func_name = list(test_profiler.profiles.keys())[0]
        assert "simple_function" in func_name

    def test_profile_with_execution_time(self, test_profiler):
        """Test that execution time is tracked"""
        @profile(profiler=test_profiler)
        def slow_function():
            time.sleep(0.05)  # 50ms
            return "done"

        slow_function()

        stats = test_profiler.get_all_stats()
        func_stats = list(stats.values())[0]

        # Should have taken at least 40ms (allowing some variance)
        assert func_stats["avg_time_ms"] > 40.0

    def test_profile_multiple_calls(self, test_profiler):
        """Test profiling multiple calls to same function"""
        @profile(profiler=test_profiler)
        def add_numbers(a, b):
            return a + b

        add_numbers(1, 2)
        add_numbers(3, 4)
        add_numbers(5, 6)

        func_name = list(test_profiler.profiles.keys())[0]
        assert test_profiler.profiles[func_name]
        assert len(test_profiler.profiles[func_name]) == 3

    def test_profile_with_exception(self, test_profiler):
        """Test that profiling works even if function raises exception"""
        @profile(profiler=test_profiler)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Should still have recorded the execution
        assert len(test_profiler.profiles) == 1

    def test_profile_decorator_without_parentheses(self, test_profiler):
        """Test using @profile without parentheses"""
        @profile
        def simple_func():
            return 42

        result = simple_func()
        assert result == 42

        # Should use global profiler
        global_profiler = get_profiler()
        assert len(global_profiler.profiles) > 0

    def test_profile_with_memory_tracking(self, test_profiler):
        """Test profiling with memory tracking enabled"""
        @profile(profiler=test_profiler, track_memory=True)
        def memory_function():
            # Allocate some memory
            data = [i for i in range(10000)]
            return len(data)

        memory_function()

        profiles = list(test_profiler.profiles.values())[0]
        result = profiles[0]

        assert result.memory_peak_mb is not None
        assert result.memory_delta_mb is not None


class TestProfileAsyncDecorator:
    """Test suite for @profile_async decorator"""

    @pytest.fixture
    def test_profiler(self):
        """Create clean profiler for testing"""
        profiler = PerformanceProfiler()
        profiler.reset()
        return profiler

    @pytest.mark.asyncio
    async def test_profile_async_function(self, test_profiler):
        """Test profiling async function"""
        @profile_async(profiler=test_profiler)
        async def async_function(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = await async_function(5)

        assert result == 10
        assert len(test_profiler.profiles) == 1

    @pytest.mark.asyncio
    async def test_profile_async_execution_time(self, test_profiler):
        """Test that async execution time is tracked"""
        @profile_async(profiler=test_profiler)
        async def slow_async_function():
            await asyncio.sleep(0.05)  # 50ms
            return "done"

        await slow_async_function()

        stats = test_profiler.get_all_stats()
        func_stats = list(stats.values())[0]

        # Should have taken at least 40ms
        assert func_stats["avg_time_ms"] > 40.0

    @pytest.mark.asyncio
    async def test_profile_async_multiple_calls(self, test_profiler):
        """Test profiling multiple async calls"""
        @profile_async(profiler=test_profiler)
        async def async_add(a, b):
            await asyncio.sleep(0.001)
            return a + b

        await async_add(1, 2)
        await async_add(3, 4)
        await async_add(5, 6)

        func_name = list(test_profiler.profiles.keys())[0]
        assert len(test_profiler.profiles[func_name]) == 3


class TestGlobalProfiler:
    """Test global profiler instance"""

    def test_get_global_profiler(self):
        """Test getting global profiler instance"""
        profiler1 = get_profiler()
        profiler2 = get_profiler()

        assert profiler1 is profiler2  # Same instance

    def test_global_profiler_usage(self):
        """Test using global profiler"""
        profiler = get_profiler()
        profiler.reset()

        @profile  # Uses global profiler
        def test_function():
            return 42

        test_function()

        assert len(profiler.profiles) > 0
