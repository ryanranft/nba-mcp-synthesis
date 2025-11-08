"""
Performance Profiling for Function-Level Analysis

Provides decorators and tools for profiling execution time and memory usage.
"""

import time
import logging
import functools
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import tracemalloc

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result from profiling a function"""
    function_name: str
    execution_time_ms: float
    call_count: int = 1
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    memory_peak_mb: Optional[float] = None
    memory_delta_mb: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    args_sample: Optional[tuple] = None
    kwargs_sample: Optional[Dict] = None


class PerformanceProfiler:
    """
    Tracks and analyzes function performance across the application.

    Features:
    - Execution time tracking
    - Memory profiling
    - Call count statistics
    - Bottleneck identification
    """

    def __init__(
        self,
        enabled: bool = True,
        track_memory: bool = False,
        slow_threshold_ms: float = 100.0
    ):
        """
        Initialize performance profiler.

        Args:
            enabled: Enable/disable profiling
            track_memory: Track memory usage (adds overhead)
            slow_threshold_ms: Threshold for flagging slow functions
        """
        self.enabled = enabled
        self.track_memory = track_memory
        self.slow_threshold_ms = slow_threshold_ms

        # Profile storage
        self.profiles: Dict[str, List[ProfileResult]] = {}

        # Aggregate statistics
        self.total_calls = 0
        self.total_time_ms = 0.0

        logger.info(
            f"PerformanceProfiler initialized (enabled={enabled}, "
            f"memory_tracking={track_memory}, slow_threshold={slow_threshold_ms}ms)"
        )

    def record(self, result: ProfileResult):
        """
        Record a profile result.

        Args:
            result: ProfileResult to record
        """
        if not self.enabled:
            return

        func_name = result.function_name

        if func_name not in self.profiles:
            self.profiles[func_name] = []

        self.profiles[func_name].append(result)

        # Update aggregate stats
        self.total_calls += 1
        self.total_time_ms += result.execution_time_ms

        # Log slow functions
        if result.execution_time_ms > self.slow_threshold_ms:
            logger.warning(
                f"Slow function detected: {func_name} took {result.execution_time_ms:.2f}ms "
                f"(threshold: {self.slow_threshold_ms}ms)"
            )

    def get_function_stats(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Get aggregated statistics for a specific function.

        Args:
            function_name: Name of function

        Returns:
            Dict with aggregated stats or None if not profiled
        """
        if function_name not in self.profiles:
            return None

        results = self.profiles[function_name]

        execution_times = [r.execution_time_ms for r in results]

        return {
            "function_name": function_name,
            "call_count": len(results),
            "total_time_ms": sum(execution_times),
            "avg_time_ms": sum(execution_times) / len(results),
            "min_time_ms": min(execution_times),
            "max_time_ms": max(execution_times),
            "median_time_ms": sorted(execution_times)[len(execution_times) // 2],
            "slow_calls": sum(1 for t in execution_times if t > self.slow_threshold_ms),
            "last_called": results[-1].timestamp.isoformat()
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all profiled functions.

        Returns:
            Dict with stats for each function
        """
        stats = {}

        for func_name in self.profiles.keys():
            stats[func_name] = self.get_function_stats(func_name)

        return stats

    def get_slowest_functions(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the N slowest functions by average execution time.

        Args:
            n: Number of functions to return

        Returns:
            List of function stats, sorted by avg time (descending)
        """
        all_stats = self.get_all_stats()

        sorted_stats = sorted(
            all_stats.values(),
            key=lambda s: s["avg_time_ms"],
            reverse=True
        )

        return sorted_stats[:n]

    def get_most_called_functions(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the N most frequently called functions.

        Args:
            n: Number of functions to return

        Returns:
            List of function stats, sorted by call count (descending)
        """
        all_stats = self.get_all_stats()

        sorted_stats = sorted(
            all_stats.values(),
            key=lambda s: s["call_count"],
            reverse=True
        )

        return sorted_stats[:n]

    def identify_bottlenecks(
        self,
        time_threshold_ms: Optional[float] = None,
        call_threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks.

        A bottleneck is a function that is:
        - Called frequently (above call_threshold)
        - Takes significant time (above time_threshold_ms)

        Args:
            time_threshold_ms: Avg time threshold (uses slow_threshold if None)
            call_threshold: Minimum calls to consider

        Returns:
            List of bottleneck functions with recommendations
        """
        time_threshold_ms = time_threshold_ms or self.slow_threshold_ms

        bottlenecks = []

        for func_name, stats in self.get_all_stats().items():
            if (stats["call_count"] >= call_threshold and
                    stats["avg_time_ms"] > time_threshold_ms):

                # Calculate impact score
                impact_score = stats["call_count"] * stats["avg_time_ms"]

                bottleneck = {
                    **stats,
                    "impact_score": impact_score,
                    "recommendations": self._generate_recommendations(stats)
                }

                bottlenecks.append(bottleneck)

        # Sort by impact score
        bottlenecks.sort(key=lambda b: b["impact_score"], reverse=True)

        return bottlenecks

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on stats"""
        recommendations = []

        if stats["avg_time_ms"] > self.slow_threshold_ms:
            recommendations.append(
                f"Average execution time ({stats['avg_time_ms']:.2f}ms) exceeds threshold. "
                "Consider optimization or caching."
            )

        if stats["call_count"] > 100:
            recommendations.append(
                f"Called {stats['call_count']} times. Consider caching or batching."
            )

        if stats["max_time_ms"] > stats["avg_time_ms"] * 3:
            recommendations.append(
                "High variance in execution time. Investigate edge cases."
            )

        return recommendations

    def reset(self):
        """Reset all profiling data"""
        self.profiles.clear()
        self.total_calls = 0
        self.total_time_ms = 0.0
        logger.info("Profiling data reset")

    def get_summary(self) -> Dict[str, Any]:
        """Get overall profiling summary"""
        return {
            "enabled": self.enabled,
            "total_functions_profiled": len(self.profiles),
            "total_calls": self.total_calls,
            "total_time_ms": self.total_time_ms,
            "avg_time_per_call_ms": (
                self.total_time_ms / self.total_calls if self.total_calls > 0 else 0.0
            ),
            "slow_threshold_ms": self.slow_threshold_ms,
            "memory_tracking": self.track_memory
        }


# Global profiler instance
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance"""
    return _global_profiler


def profile(
    func: Optional[Callable] = None,
    *,
    profiler: Optional[PerformanceProfiler] = None,
    track_memory: bool = False
):
    """
    Decorator to profile a synchronous function.

    Usage:
        @profile
        def my_function():
            pass

        @profile(track_memory=True)
        def memory_intensive_function():
            pass

    Args:
        func: Function to profile (when used without parentheses)
        profiler: Custom profiler instance (uses global if None)
        track_memory: Track memory usage for this function
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            prof = profiler or _global_profiler

            if not prof.enabled:
                return f(*args, **kwargs)

            # Start memory tracking if enabled
            if track_memory or prof.track_memory:
                tracemalloc.start()
                snapshot_before = tracemalloc.take_snapshot()

            # Time execution
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                return result

            finally:
                execution_time_ms = (time.time() - start_time) * 1000

                # Get memory stats if tracking
                memory_peak_mb = None
                memory_delta_mb = None

                if track_memory or prof.track_memory:
                    snapshot_after = tracemalloc.take_snapshot()
                    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

                    if top_stats:
                        memory_delta_mb = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)

                    current, peak = tracemalloc.get_traced_memory()
                    memory_peak_mb = peak / (1024 * 1024)

                    tracemalloc.stop()

                # Record result
                profile_result = ProfileResult(
                    function_name=f"{f.__module__}.{f.__name__}",
                    execution_time_ms=execution_time_ms,
                    memory_peak_mb=memory_peak_mb,
                    memory_delta_mb=memory_delta_mb,
                    args_sample=args[:3] if args else None,  # First 3 args
                    kwargs_sample=dict(list(kwargs.items())[:3]) if kwargs else None
                )

                prof.record(profile_result)

        return wrapper

    # Handle both @profile and @profile()
    if func is None:
        return decorator
    else:
        return decorator(func)


def profile_async(
    func: Optional[Callable] = None,
    *,
    profiler: Optional[PerformanceProfiler] = None,
    track_memory: bool = False
):
    """
    Decorator to profile an async function.

    Usage:
        @profile_async
        async def my_async_function():
            pass

    Args:
        func: Function to profile
        profiler: Custom profiler instance
        track_memory: Track memory usage
    """

    def decorator(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            prof = profiler or _global_profiler

            if not prof.enabled:
                return await f(*args, **kwargs)

            # Start memory tracking if enabled
            if track_memory or prof.track_memory:
                tracemalloc.start()
                snapshot_before = tracemalloc.take_snapshot()

            # Time execution
            start_time = time.time()

            try:
                result = await f(*args, **kwargs)
                return result

            finally:
                execution_time_ms = (time.time() - start_time) * 1000

                # Get memory stats if tracking
                memory_peak_mb = None
                memory_delta_mb = None

                if track_memory or prof.track_memory:
                    snapshot_after = tracemalloc.take_snapshot()
                    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

                    if top_stats:
                        memory_delta_mb = sum(stat.size_diff for stat in top_stats) / (1024 * 1024)

                    current, peak = tracemalloc.get_traced_memory()
                    memory_peak_mb = peak / (1024 * 1024)

                    tracemalloc.stop()

                # Record result
                profile_result = ProfileResult(
                    function_name=f"{f.__module__}.{f.__name__}",
                    execution_time_ms=execution_time_ms,
                    memory_peak_mb=memory_peak_mb,
                    memory_delta_mb=memory_delta_mb,
                    args_sample=args[:3] if args else None,
                    kwargs_sample=dict(list(kwargs.items())[:3]) if kwargs else None
                )

                prof.record(profile_result)

        return wrapper

    # Handle both @profile_async and @profile_async()
    if func is None:
        return decorator
    else:
        return decorator(func)
