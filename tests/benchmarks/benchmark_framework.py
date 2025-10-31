"""
Performance benchmarking framework for econometric tools.

Provides infrastructure for timing, memory profiling, and performance tracking.
"""

import time
import tracemalloc
import statistics
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime
import numpy as np


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    tool_name: str
    dataset_size: str  # 'small', 'medium', 'large', 'xlarge'
    n_observations: int
    execution_time_ms: float
    memory_peak_mb: float
    memory_delta_mb: float
    success: bool
    error: Optional[str] = None
    iterations: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "dataset_size": self.dataset_size,
            "n_observations": self.n_observations,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 2),
            "success": self.success,
            "error": self.error,
            "iterations": self.iterations,
            "timestamp": self.timestamp,
        }


@dataclass
class PerformanceThresholds:
    """Performance thresholds for tool validation."""

    max_time_small_ms: float = 1000  # 1 second for small datasets
    max_time_medium_ms: float = 5000  # 5 seconds for medium datasets
    max_time_large_ms: float = 15000  # 15 seconds for large datasets
    max_memory_mb: float = 500  # 500 MB max memory
    max_memory_growth_mb: float = 200  # 200 MB max growth per call


class BenchmarkFramework:
    """
    Framework for benchmarking econometric tool performance.

    Provides timing, memory profiling, and result aggregation.
    """

    def __init__(self, output_dir: str = "benchmark_results"):
        """Initialize benchmark framework."""
        self.output_dir = output_dir
        self.results: List[BenchmarkResult] = []
        self.thresholds = PerformanceThresholds()

    async def benchmark_tool(
        self,
        tool_name: str,
        tool_func: Callable,
        params: Any,
        context: Any,
        dataset_size: str,
        n_observations: int,
        iterations: int = 1,
    ) -> BenchmarkResult:
        """
        Benchmark a single tool execution.

        Args:
            tool_name: Name of the tool being benchmarked
            tool_func: Async function to benchmark
            params: Parameters for the tool
            context: Mock context for the tool
            dataset_size: 'small', 'medium', 'large', or 'xlarge'
            n_observations: Number of observations in dataset
            iterations: Number of times to run (for averaging)

        Returns:
            BenchmarkResult with timing and memory metrics
        """
        execution_times = []
        memory_peaks = []
        memory_deltas = []
        success = True
        error = None

        for _ in range(iterations):
            # Start memory tracking
            tracemalloc.start()
            start_memory = tracemalloc.get_traced_memory()[0]

            # Time execution
            start_time = time.perf_counter()

            try:
                result = await tool_func(params, context)
                success = success and result.success

                if not result.success:
                    error = result.error

            except Exception as e:
                success = False
                error = str(e)

            end_time = time.perf_counter()

            # Capture memory metrics
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Calculate metrics
            execution_time_ms = (end_time - start_time) * 1000
            memory_peak_mb = peak_memory / (1024 * 1024)
            memory_delta_mb = (current_memory - start_memory) / (1024 * 1024)

            execution_times.append(execution_time_ms)
            memory_peaks.append(memory_peak_mb)
            memory_deltas.append(memory_delta_mb)

        # Average results across iterations
        avg_time = statistics.mean(execution_times) if execution_times else 0
        avg_peak = statistics.mean(memory_peaks) if memory_peaks else 0
        avg_delta = statistics.mean(memory_deltas) if memory_deltas else 0

        result = BenchmarkResult(
            tool_name=tool_name,
            dataset_size=dataset_size,
            n_observations=n_observations,
            execution_time_ms=avg_time,
            memory_peak_mb=avg_peak,
            memory_delta_mb=avg_delta,
            success=success,
            error=error,
            iterations=iterations,
        )

        self.results.append(result)
        return result

    def check_thresholds(self, result: BenchmarkResult) -> Dict[str, bool]:
        """
        Check if result meets performance thresholds.

        Returns:
            Dict with threshold checks (True = passed, False = failed)
        """
        checks = {}

        # Time thresholds based on dataset size
        if result.dataset_size == "small":
            checks["time_threshold"] = (
                result.execution_time_ms <= self.thresholds.max_time_small_ms
            )
        elif result.dataset_size == "medium":
            checks["time_threshold"] = (
                result.execution_time_ms <= self.thresholds.max_time_medium_ms
            )
        elif result.dataset_size == "large":
            checks["time_threshold"] = (
                result.execution_time_ms <= self.thresholds.max_time_large_ms
            )
        else:
            checks["time_threshold"] = True  # No threshold for xlarge

        # Memory thresholds
        checks["memory_peak_threshold"] = (
            result.memory_peak_mb <= self.thresholds.max_memory_mb
        )
        checks["memory_growth_threshold"] = (
            result.memory_delta_mb <= self.thresholds.max_memory_growth_mb
        )

        checks["all_passed"] = all(checks.values())

        return checks

    def get_results_by_tool(self, tool_name: str) -> List[BenchmarkResult]:
        """Get all results for a specific tool."""
        return [r for r in self.results if r.tool_name == tool_name]

    def get_results_by_size(self, dataset_size: str) -> List[BenchmarkResult]:
        """Get all results for a specific dataset size."""
        return [r for r in self.results if r.dataset_size == dataset_size]

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics across all benchmarks.

        Returns:
            Dict with aggregate metrics and statistics
        """
        if not self.results:
            return {"error": "No benchmark results available"}

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        summary = {
            "total_benchmarks": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "by_size": {},
            "by_tool": {},
            "performance_summary": {},
        }

        # Aggregate by dataset size
        for size in ["small", "medium", "large", "xlarge"]:
            size_results = [r for r in successful if r.dataset_size == size]
            if size_results:
                times = [r.execution_time_ms for r in size_results]
                memory = [r.memory_peak_mb for r in size_results]

                summary["by_size"][size] = {
                    "count": len(size_results),
                    "avg_time_ms": round(statistics.mean(times), 2),
                    "median_time_ms": round(statistics.median(times), 2),
                    "max_time_ms": round(max(times), 2),
                    "avg_memory_mb": round(statistics.mean(memory), 2),
                    "max_memory_mb": round(max(memory), 2),
                }

        # Aggregate by tool
        tools = set(r.tool_name for r in self.results)
        for tool in tools:
            tool_results = [r for r in successful if r.tool_name == tool]
            if tool_results:
                times = [r.execution_time_ms for r in tool_results]
                memory = [r.memory_peak_mb for r in tool_results]

                summary["by_tool"][tool] = {
                    "benchmarks": len(tool_results),
                    "avg_time_ms": round(statistics.mean(times), 2),
                    "avg_memory_mb": round(statistics.mean(memory), 2),
                    "sizes_tested": list(set(r.dataset_size for r in tool_results)),
                }

        # Overall performance summary
        if successful:
            all_times = [r.execution_time_ms for r in successful]
            all_memory = [r.memory_peak_mb for r in successful]

            summary["performance_summary"] = {
                "fastest_time_ms": round(min(all_times), 2),
                "slowest_time_ms": round(max(all_times), 2),
                "avg_time_ms": round(statistics.mean(all_times), 2),
                "median_time_ms": round(statistics.median(all_times), 2),
                "min_memory_mb": round(min(all_memory), 2),
                "max_memory_mb": round(max(all_memory), 2),
                "avg_memory_mb": round(statistics.mean(all_memory), 2),
            }

        # Threshold violations
        violations = []
        for result in successful:
            checks = self.check_thresholds(result)
            if not checks["all_passed"]:
                violations.append(
                    {
                        "tool": result.tool_name,
                        "size": result.dataset_size,
                        "time_ms": result.execution_time_ms,
                        "memory_mb": result.memory_peak_mb,
                        "failed_checks": [k for k, v in checks.items() if not v],
                    }
                )

        summary["threshold_violations"] = violations

        return summary

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to JSON file."""
        import os

        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)

        output = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_benchmarks": len(self.results),
                "framework_version": "1.0.0",
            },
            "results": [r.to_dict() for r in self.results],
            "summary": self.generate_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        return filepath

    def print_summary(self):
        """Print formatted summary to console."""
        summary = self.generate_summary()

        print("\n" + "=" * 70)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 70)

        print(f"\nTotal Benchmarks: {summary['total_benchmarks']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")

        if "performance_summary" in summary:
            perf = summary["performance_summary"]
            print("\n" + "-" * 70)
            print("Overall Performance:")
            print(f"  Fastest: {perf['fastest_time_ms']:.2f} ms")
            print(f"  Slowest: {perf['slowest_time_ms']:.2f} ms")
            print(f"  Average: {perf['avg_time_ms']:.2f} ms")
            print(f"  Memory (avg): {perf['avg_memory_mb']:.2f} MB")
            print(f"  Memory (max): {perf['max_memory_mb']:.2f} MB")

        if summary.get("by_size"):
            print("\n" + "-" * 70)
            print("Performance by Dataset Size:")
            for size, metrics in summary["by_size"].items():
                print(f"\n  {size.upper()}:")
                print(f"    Benchmarks: {metrics['count']}")
                print(f"    Avg Time: {metrics['avg_time_ms']:.2f} ms")
                print(f"    Max Time: {metrics['max_time_ms']:.2f} ms")
                print(f"    Avg Memory: {metrics['avg_memory_mb']:.2f} MB")

        if summary.get("threshold_violations"):
            print("\n" + "-" * 70)
            print(f"⚠️  Threshold Violations: {len(summary['threshold_violations'])}")
            for violation in summary["threshold_violations"][:5]:  # Show first 5
                print(f"  - {violation['tool']} ({violation['size']})")
                print(f"    Time: {violation['time_ms']:.2f} ms")
                print(f"    Failed: {', '.join(violation['failed_checks'])}")

        print("\n" + "=" * 70 + "\n")
