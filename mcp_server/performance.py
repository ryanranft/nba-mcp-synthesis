"""Performance Profiling & Optimization - IMPORTANT 13"""
import time
import functools
import cProfile
import pstats
import io
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor function performance"""

    def __init__(self):
        self.metrics = {}

    def track(self, func_name: str, duration: float):
        """Track function execution time"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }

        metrics = self.metrics[func_name]
        metrics["count"] += 1
        metrics["total_time"] += duration
        metrics["min_time"] = min(metrics["min_time"], duration)
        metrics["max_time"] = max(metrics["max_time"], duration)

    def get_stats(self) -> dict:
        """Get performance statistics"""
        stats = {}
        for func_name, metrics in self.metrics.items():
            stats[func_name] = {
                "calls": metrics["count"],
                "total_time": f"{metrics['total_time']:.3f}s",
                "avg_time": f"{metrics['total_time'] / metrics['count']:.3f}s",
                "min_time": f"{metrics['min_time']:.3f}s",
                "max_time": f"{metrics['max_time']:.3f}s"
            }
        return stats

    def print_stats(self):
        """Print performance statistics"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE STATISTICS")
        print("=" * 80)

        for func_name, stats in sorted(self.get_stats().items()):
            print(f"\n{func_name}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        print("=" * 80 + "\n")


# Global monitor
_perf_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _perf_monitor


def profile(func: Callable = None, *, enabled: bool = True):
    """
    Decorator to profile function execution time

    Usage:
        @profile
        def my_function():
            ...

        @profile(enabled=False)  # Disable profiling
        def another_function():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            if not enabled:
                return f(*args, **kwargs)

            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                get_monitor().track(f.__name__, duration)

                # Log slow functions
                if duration > 1.0:  # More than 1 second
                    logger.warning(f"⚠️  Slow function: {f.__name__} took {duration:.3f}s")

        return wrapper

    # Handle both @profile and @profile()
    if func is None:
        return decorator
    else:
        return decorator(func)


def profile_code_block(name: str):
    """
    Context manager to profile a code block

    Usage:
        with profile_code_block("data_processing"):
            # ... code to profile ...
    """
    class ProfileContext:
        def __init__(self, block_name: str):
            self.block_name = block_name
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            get_monitor().track(self.block_name, duration)

    return ProfileContext(name)


def detailed_profile(func: Callable) -> Callable:
    """
    Decorator for detailed profiling with cProfile

    Usage:
        @detailed_profile
        def complex_function():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()

            # Print stats
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions

            logger.info(f"\n📊 Detailed profile for {func.__name__}:\n{s.getvalue()}")

    return wrapper


# Example usage
if __name__ == "__main__":
    @profile
    def slow_function():
        time.sleep(0.1)
        return "done"

    @profile
    def fast_function():
        return sum(range(1000))

    # Run functions
    for _ in range(10):
        slow_function()
        fast_function()

    # Print stats
    get_monitor().print_stats()

