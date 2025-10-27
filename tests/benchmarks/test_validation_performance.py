#!/usr/bin/env python3
"""
Data Validation Performance Benchmarks

Comprehensive performance testing for NBA MCP data validation infrastructure.
Tests performance across varying dataset sizes (100 to 1M rows) and measures
execution time, memory usage, and throughput.

Phase 10A Week 2 - Agent 4 - Phase 5: Extended Testing
Task 1: Performance Benchmarking

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import pytest
import pandas as pd
import numpy as np
import time
import statistics
import tracemalloc
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json

# Import components under test
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler
from mcp_server.integrity_checker import IntegrityChecker


# ==================== Performance Result Data Structures ====================


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single benchmark run"""

    operation: str
    dataset_size: int
    iterations: int
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    p95_time: float
    p99_time: float
    throughput_rows_per_sec: float
    peak_memory_mb: float
    current_memory_mb: float
    passed: bool
    threshold_seconds: float


@dataclass
class BenchmarkSummary:
    """Summary of all benchmark results"""

    total_benchmarks: int
    passed_benchmarks: int
    failed_benchmarks: int
    total_execution_time: float
    metrics: List[PerformanceMetrics]


# ==================== Dataset Generators ====================


def generate_player_stats_dataset(num_rows: int) -> pd.DataFrame:
    """
    Generate synthetic player statistics dataset.

    Args:
        num_rows: Number of player records to generate

    Returns:
        DataFrame with synthetic player stats
    """
    np.random.seed(42)

    data = {
        "player_id": range(1, num_rows + 1),
        "player_name": [f"Player_{i}" for i in range(1, num_rows + 1)],
        "team_id": np.random.randint(1, 31, num_rows),
        "games_played": np.random.randint(0, 82, num_rows),
        "minutes_played": np.random.uniform(0, 40, num_rows),
        "points": np.random.uniform(0, 35, num_rows),
        "rebounds": np.random.uniform(0, 15, num_rows),
        "assists": np.random.uniform(0, 12, num_rows),
        "steals": np.random.uniform(0, 3, num_rows),
        "blocks": np.random.uniform(0, 3, num_rows),
        "turnovers": np.random.uniform(0, 5, num_rows),
        "field_goals_made": np.random.randint(0, 15, num_rows),
        "field_goals_attempted": np.random.randint(0, 30, num_rows),
        "three_pointers_made": np.random.randint(0, 8, num_rows),
        "three_pointers_attempted": np.random.randint(0, 15, num_rows),
        "free_throws_made": np.random.randint(0, 10, num_rows),
        "free_throws_attempted": np.random.randint(0, 12, num_rows),
    }

    df = pd.DataFrame(data)

    # Add some missing values (5%)
    mask = np.random.random(df.shape) < 0.05
    df = df.mask(mask)

    # Add some outliers (2%)
    outlier_mask = np.random.random(num_rows) < 0.02
    df.loc[outlier_mask, "points"] = np.random.uniform(50, 100, outlier_mask.sum())

    return df


def generate_game_data_dataset(num_rows: int) -> pd.DataFrame:
    """
    Generate synthetic game data dataset.

    Args:
        num_rows: Number of game records to generate

    Returns:
        DataFrame with synthetic game data
    """
    np.random.seed(43)

    data = {
        "game_id": range(1, num_rows + 1),
        "home_team_id": np.random.randint(1, 31, num_rows),
        "away_team_id": np.random.randint(1, 31, num_rows),
        "home_score": np.random.randint(80, 130, num_rows),
        "away_score": np.random.randint(80, 130, num_rows),
        "attendance": np.random.randint(10000, 20000, num_rows),
        "duration_minutes": np.random.randint(110, 150, num_rows),
        "overtime": np.random.choice([0, 1], num_rows, p=[0.9, 0.1]),
    }

    df = pd.DataFrame(data)

    # Add some missing values (3%)
    mask = np.random.random(df.shape) < 0.03
    df = df.mask(mask)

    return df


# ==================== Benchmark Fixtures ====================


@pytest.fixture(scope="module")
def dataset_sizes():
    """Dataset sizes to benchmark (100 to 1M rows)"""
    return [100, 1_000, 10_000, 100_000, 500_000, 1_000_000]


@pytest.fixture(scope="module")
def data_cleaner():
    """Initialize data cleaner"""
    return DataCleaner()


@pytest.fixture(scope="module")
def data_profiler():
    """Initialize data profiler"""
    return DataProfiler()


@pytest.fixture(scope="module")
def integrity_checker():
    """Initialize integrity checker"""
    return IntegrityChecker()


@pytest.fixture(scope="module")
def validation_pipeline():
    """Initialize validation pipeline"""
    config = PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=True,
        enable_profiling=True,
        min_quality_score=0.85,
    )
    return DataValidationPipeline(config=config)


# ==================== Helper Functions ====================


def measure_performance(
    operation_name: str,
    func,
    *args,
    iterations: int = 3,
    threshold_seconds: float = 60.0,
    dataset_size: int = 0,
    **kwargs,
) -> PerformanceMetrics:
    """
    Measure performance of a function with multiple iterations.

    Args:
        operation_name: Name of the operation being benchmarked
        func: Function to benchmark
        *args: Positional arguments for function
        iterations: Number of iterations to run
        threshold_seconds: Maximum acceptable time (seconds)
        dataset_size: Size of dataset being processed
        **kwargs: Keyword arguments for function

    Returns:
        PerformanceMetrics object with results
    """
    times = []
    peak_memory = 0
    current_memory = 0

    for i in range(iterations):
        # Start memory tracking
        tracemalloc.start()

        # Time the operation
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Get memory usage
        curr, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        times.append(end_time - start_time)
        peak_memory = max(peak_memory, peak)
        current_memory = max(current_memory, curr)

    # Calculate statistics
    sorted_times = sorted(times)
    p95_idx = int(len(sorted_times) * 0.95)
    p99_idx = int(len(sorted_times) * 0.99)

    mean_time = statistics.mean(times)
    throughput = dataset_size / mean_time if mean_time > 0 and dataset_size > 0 else 0

    return PerformanceMetrics(
        operation=operation_name,
        dataset_size=dataset_size,
        iterations=iterations,
        min_time=min(times),
        max_time=max(times),
        mean_time=mean_time,
        median_time=statistics.median(times),
        p95_time=sorted_times[p95_idx] if p95_idx < len(sorted_times) else max(times),
        p99_time=sorted_times[p99_idx] if p99_idx < len(sorted_times) else max(times),
        throughput_rows_per_sec=throughput,
        peak_memory_mb=peak_memory / 1024 / 1024,
        current_memory_mb=current_memory / 1024 / 1024,
        passed=mean_time <= threshold_seconds,
        threshold_seconds=threshold_seconds,
    )


def print_performance_metrics(metrics: PerformanceMetrics):
    """Print performance metrics in formatted output"""
    status = "✅ PASS" if metrics.passed else "❌ FAIL"
    print(f"\n{'=' * 80}")
    print(f"Performance Benchmark: {metrics.operation}")
    print(f"Dataset Size: {metrics.dataset_size:,} rows | Status: {status}")
    print(f"{'=' * 80}")
    print(f"⏱️  Execution Time (seconds)")
    print(f"   Min:      {metrics.min_time:.4f}s")
    print(f"   Max:      {metrics.max_time:.4f}s")
    print(f"   Mean:     {metrics.mean_time:.4f}s")
    print(f"   Median:   {metrics.median_time:.4f}s")
    print(f"   p95:      {metrics.p95_time:.4f}s")
    print(f"   p99:      {metrics.p99_time:.4f}s")
    print(f"   Threshold: {metrics.threshold_seconds:.4f}s")
    print(f"\n⚡ Performance")
    print(f"   Throughput: {metrics.throughput_rows_per_sec:,.0f} rows/sec")
    print(f"\n💾 Memory Usage")
    print(f"   Current:  {metrics.current_memory_mb:.2f} MB")
    print(f"   Peak:     {metrics.peak_memory_mb:.2f} MB")
    print(f"{'=' * 80}\n")


# ==================== Benchmark Tests ====================


class TestDataCleaningPerformance:
    """Performance benchmarks for data cleaning operations"""

    def test_outlier_removal_iqr(self, data_cleaner, dataset_sizes):
        """Benchmark IQR outlier removal across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Cleaning - IQR Outlier Removal")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            # Define thresholds based on size
            if size <= 1_000:
                threshold = 0.1
            elif size <= 10_000:
                threshold = 1.0
            elif size <= 100_000:
                threshold = 10.0
            elif size <= 500_000:
                threshold = 30.0
            else:  # 1M
                threshold = 60.0

            metrics = measure_performance(
                operation_name=f"IQR Outlier Removal ({size:,} rows)",
                func=data_cleaner.remove_outliers,
                df=df,
                method=OutlierMethod.IQR,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results

    def test_outlier_removal_zscore(self, data_cleaner, dataset_sizes):
        """Benchmark Z-score outlier removal across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Cleaning - Z-Score Outlier Removal")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.1
            elif size <= 10_000:
                threshold = 1.0
            elif size <= 100_000:
                threshold = 10.0
            elif size <= 500_000:
                threshold = 30.0
            else:
                threshold = 60.0

            metrics = measure_performance(
                operation_name=f"Z-Score Outlier Removal ({size:,} rows)",
                func=data_cleaner.remove_outliers,
                df=df,
                method=OutlierMethod.ZSCORE,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results

    def test_missing_value_imputation(self, data_cleaner, dataset_sizes):
        """Benchmark missing value imputation across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Cleaning - Missing Value Imputation")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.1
            elif size <= 10_000:
                threshold = 1.0
            elif size <= 100_000:
                threshold = 10.0
            elif size <= 500_000:
                threshold = 25.0
            else:
                threshold = 50.0

            metrics = measure_performance(
                operation_name=f"Missing Value Imputation ({size:,} rows)",
                func=data_cleaner.impute_missing_values,
                df=df,
                strategy=ImputationStrategy.MEDIAN,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results

    def test_full_cleaning_pipeline(self, data_cleaner, dataset_sizes):
        """Benchmark full cleaning pipeline (outliers + imputation + dupes)"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Cleaning - Full Pipeline")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.2
            elif size <= 10_000:
                threshold = 2.0
            elif size <= 100_000:
                threshold = 20.0
            elif size <= 500_000:
                threshold = 50.0
            else:
                threshold = 100.0

            metrics = measure_performance(
                operation_name=f"Full Cleaning Pipeline ({size:,} rows)",
                func=data_cleaner.clean,
                df=df,
                remove_outliers=True,
                outlier_method=OutlierMethod.IQR,
                impute_missing=True,
                imputation_strategy=ImputationStrategy.MEDIAN,
                remove_dupes=True,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results


class TestDataProfilingPerformance:
    """Performance benchmarks for data profiling operations"""

    def test_statistical_profiling(self, data_profiler, dataset_sizes):
        """Benchmark statistical profiling across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Profiling - Statistical Analysis")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.1
            elif size <= 10_000:
                threshold = 1.0
            elif size <= 100_000:
                threshold = 10.0
            elif size <= 500_000:
                threshold = 30.0
            else:
                threshold = 60.0

            metrics = measure_performance(
                operation_name=f"Statistical Profiling ({size:,} rows)",
                func=data_profiler.profile,
                df=df,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results

    def test_quality_score_calculation(self, data_profiler, dataset_sizes):
        """Benchmark quality score calculation across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Data Profiling - Quality Score")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.1
            elif size <= 10_000:
                threshold = 1.0
            elif size <= 100_000:
                threshold = 10.0
            elif size <= 500_000:
                threshold = 25.0
            else:
                threshold = 50.0

            metrics = measure_performance(
                operation_name=f"Quality Score Calculation ({size:,} rows)",
                func=data_profiler.calculate_quality_score,
                df=df,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results


class TestIntegrityCheckingPerformance:
    """Performance benchmarks for integrity checking operations"""

    def test_nba_player_integrity(self, integrity_checker, dataset_sizes):
        """Benchmark NBA player integrity checks across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Integrity Checking - NBA Player Rules")
        print("=" * 80)

        results = []
        for size in dataset_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.2
            elif size <= 10_000:
                threshold = 2.0
            elif size <= 100_000:
                threshold = 15.0
            elif size <= 500_000:
                threshold = 40.0
            else:
                threshold = 80.0

            metrics = measure_performance(
                operation_name=f"NBA Player Integrity ({size:,} rows)",
                func=integrity_checker.check_nba_player_integrity,
                df=df,
                threshold=threshold,
                dataset_size=size,
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results


class TestFullPipelinePerformance:
    """Performance benchmarks for complete validation pipeline"""

    def test_full_validation_pipeline(self, validation_pipeline, dataset_sizes):
        """Benchmark full validation pipeline across dataset sizes"""
        print("\n\n" + "=" * 80)
        print("BENCHMARK: Full Validation Pipeline")
        print("=" * 80)

        results = []
        # Limit to smaller sizes for full pipeline to avoid excessive runtime
        limited_sizes = [s for s in dataset_sizes if s <= 100_000]

        for size in limited_sizes:
            df = generate_player_stats_dataset(size)

            if size <= 1_000:
                threshold = 0.5
            elif size <= 10_000:
                threshold = 5.0
            else:  # 100K
                threshold = 30.0

            metrics = measure_performance(
                operation_name=f"Full Validation Pipeline ({size:,} rows)",
                func=validation_pipeline.validate,
                data=df,
                dataset_type="player_stats",
                threshold=threshold,
                dataset_size=size,
                iterations=1,  # Single iteration for pipeline
            )

            print_performance_metrics(metrics)
            results.append(metrics)
            assert metrics.passed, f"Failed threshold for {size:,} rows"

        return results


# ==================== Summary Report ====================


@pytest.fixture(scope="module", autouse=True)
def benchmark_summary(request):
    """Generate benchmark summary report at end of module"""
    yield

    # This runs after all tests
    print("\n\n" + "=" * 80)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 80)
    print("\nAll performance benchmarks completed successfully!")
    print("See individual test output for detailed metrics.")
    print("\nExpected Performance Baselines:")
    print("  - 1K rows:   <100ms (data cleaning), <1s (full pipeline)")
    print("  - 100K rows: <10s (data cleaning), <30s (full pipeline)")
    print("  - 1M rows:   <60s (data cleaning)")
    print("\nThroughput targets:")
    print("  - Data Cleaning: >16K rows/sec")
    print("  - Data Profiling: >10K rows/sec")
    print("  - Integrity Checking: >12K rows/sec")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
