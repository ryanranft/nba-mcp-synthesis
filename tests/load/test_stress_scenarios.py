#!/usr/bin/env python3
"""
Data Validation Load Testing & Stress Scenarios

Comprehensive stress testing for NBA MCP data validation infrastructure.
Tests system behavior under extreme load, concurrent operations, sustained
processing, and resource constraints.

Phase 10A Week 2 - Agent 4 - Phase 5: Extended Testing
Task 2: Load Testing

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import pytest
import pandas as pd
import numpy as np
import time
import asyncio
import psutil
import gc
import threading
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
import json

# Import components under test
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler
from mcp_server.integrity_checker import IntegrityChecker


# ==================== Load Test Result Structures ====================


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing"""

    test_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_duration_seconds: float
    operations_per_second: float
    mean_latency_seconds: float
    median_latency_seconds: float
    p95_latency_seconds: float
    p99_latency_seconds: float
    peak_cpu_percent: float
    peak_memory_mb: float
    memory_leaked_mb: float
    error_rate: float
    passed: bool


@dataclass
class OperationResult:
    """Result of a single operation"""

    operation_id: int
    success: bool
    duration_seconds: float
    error_message: str = None


# ==================== Resource Monitoring ====================


class ResourceMonitor:
    """Monitor CPU and memory usage during tests"""

    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self._monitoring = False
        self._thread = None
        self.process = psutil.Process()

    def start(self):
        """Start monitoring"""
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _monitor_loop(self):
        """Monitoring loop"""
        while self._monitoring:
            try:
                cpu = self.process.cpu_percent(interval=None)
                memory_mb = self.process.memory_info().rss / 1024 / 1024

                self.cpu_samples.append(cpu)
                self.memory_samples.append(memory_mb)

                time.sleep(self.sample_interval)
            except Exception:
                pass

    def get_peak_cpu(self) -> float:
        """Get peak CPU usage"""
        return max(self.cpu_samples) if self.cpu_samples else 0.0

    def get_peak_memory(self) -> float:
        """Get peak memory usage (MB)"""
        return max(self.memory_samples) if self.memory_samples else 0.0

    def get_memory_leak(self, baseline_mb: float) -> float:
        """Calculate memory leak (current - baseline)"""
        current_mb = self.memory_samples[-1] if self.memory_samples else 0.0
        return max(0.0, current_mb - baseline_mb)


# ==================== Dataset Generators ====================


def generate_large_player_dataset(
    num_rows: int, add_noise: bool = True
) -> pd.DataFrame:
    """
    Generate large synthetic player dataset for load testing.

    Args:
        num_rows: Number of rows to generate
        add_noise: Add missing values and outliers

    Returns:
        DataFrame with player statistics
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

    if add_noise:
        # Add missing values (5%)
        mask = np.random.random(df.shape) < 0.05
        df = df.mask(mask)

        # Add outliers (2%)
        outlier_mask = np.random.random(num_rows) < 0.02
        df.loc[outlier_mask, "points"] = np.random.uniform(50, 100, outlier_mask.sum())

    return df


# ==================== Load Test Scenarios ====================


class LoadTestScenarios:
    """Collection of load test scenarios"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.profiler = DataProfiler()
        self.integrity_checker = IntegrityChecker()
        self.pipeline = DataValidationPipeline(
            config=PipelineConfig(
                enable_schema_validation=True,
                enable_quality_check=True,
                enable_business_rules=True,
                min_quality_score=0.85,
            )
        )

    def single_validation_operation(
        self, df: pd.DataFrame, operation_id: int
    ) -> OperationResult:
        """Execute single validation operation"""
        start_time = time.time()
        success = True
        error_msg = None

        try:
            result = self.pipeline.validate(df, "player_stats")
            # Validation completed
        except Exception as e:
            success = False
            error_msg = str(e)

        duration = time.time() - start_time
        return OperationResult(operation_id, success, duration, error_msg)

    def single_cleaning_operation(
        self, df: pd.DataFrame, operation_id: int
    ) -> OperationResult:
        """Execute single cleaning operation"""
        start_time = time.time()
        success = True
        error_msg = None

        try:
            cleaned_df, report = self.cleaner.clean(
                df,
                remove_outliers=True,
                outlier_method=OutlierMethod.IQR,
                impute_missing=True,
                imputation_strategy=ImputationStrategy.MEDIAN,
            )
        except Exception as e:
            success = False
            error_msg = str(e)

        duration = time.time() - start_time
        return OperationResult(operation_id, success, duration, error_msg)

    def single_profiling_operation(
        self, df: pd.DataFrame, operation_id: int
    ) -> OperationResult:
        """Execute single profiling operation"""
        start_time = time.time()
        success = True
        error_msg = None

        try:
            profile = self.profiler.profile(df)
        except Exception as e:
            success = False
            error_msg = str(e)

        duration = time.time() - start_time
        return OperationResult(operation_id, success, duration, error_msg)


# ==================== Load Tests ====================


class TestMassiveDatasetLoad:
    """Test with very large datasets (1M+ rows)"""

    @pytest.mark.slow
    def test_1m_row_validation(self):
        """Test validation with 1M row dataset"""
        print("\n" + "=" * 80)
        print("LOAD TEST: 1M Row Dataset Validation")
        print("=" * 80)

        # Generate 1M row dataset
        print("Generating 1M row dataset...")
        df = generate_large_player_dataset(1_000_000)
        print(
            f"Dataset size: {len(df):,} rows, {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        )

        # Setup monitoring
        monitor = ResourceMonitor()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Run validation
        scenarios = LoadTestScenarios()

        print("Starting validation...")
        monitor.start()
        start_time = time.time()

        try:
            result = scenarios.single_validation_operation(df, 1)
            duration = time.time() - start_time

            monitor.stop()

            # Collect metrics
            peak_cpu = monitor.get_peak_cpu()
            peak_memory = monitor.get_peak_memory()
            memory_leak = monitor.get_memory_leak(baseline_memory)

            # Print results
            print(f"\n{'=' * 80}")
            print("Results:")
            print(f"  Success: {result.success}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Peak CPU: {peak_cpu:.1f}%")
            print(f"  Peak Memory: {peak_memory:.2f} MB")
            print(f"  Memory Leak: {memory_leak:.2f} MB")
            print(f"{'=' * 80}\n")

            # Assertions
            assert result.success, f"Validation failed: {result.error_message}"
            assert duration < 120, f"Validation took too long: {duration:.2f}s"
            assert memory_leak < 100, f"Excessive memory leak: {memory_leak:.2f} MB"

        finally:
            monitor.stop()
            gc.collect()


class TestConcurrentLoad:
    """Test with concurrent parallel operations"""

    @pytest.mark.slow
    def test_concurrent_validations_10_workers(self):
        """Test 10 concurrent validation operations"""
        print("\n" + "=" * 80)
        print("LOAD TEST: 10 Concurrent Validations (100K rows each)")
        print("=" * 80)

        num_workers = 10
        dataset_size = 100_000

        # Generate datasets
        print(f"Generating {num_workers} datasets of {dataset_size:,} rows each...")
        datasets = [
            generate_large_player_dataset(dataset_size) for _ in range(num_workers)
        ]

        # Setup monitoring
        monitor = ResourceMonitor()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        scenarios = LoadTestScenarios()

        print(f"Running {num_workers} concurrent validations...")
        monitor.start()
        start_time = time.time()

        results = []
        latencies = []

        try:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(scenarios.single_validation_operation, df, i)
                    for i, df in enumerate(datasets)
                ]

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    latencies.append(result.duration_seconds)

            total_duration = time.time() - start_time
            monitor.stop()

            # Calculate metrics
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            error_rate = failed / len(results)

            latencies.sort()
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)

            metrics = LoadTestMetrics(
                test_name="10_concurrent_validations",
                total_operations=len(results),
                successful_operations=successful,
                failed_operations=failed,
                total_duration_seconds=total_duration,
                operations_per_second=len(results) / total_duration,
                mean_latency_seconds=sum(latencies) / len(latencies),
                median_latency_seconds=latencies[len(latencies) // 2],
                p95_latency_seconds=latencies[p95_idx],
                p99_latency_seconds=latencies[p99_idx],
                peak_cpu_percent=monitor.get_peak_cpu(),
                peak_memory_mb=monitor.get_peak_memory(),
                memory_leaked_mb=monitor.get_memory_leak(baseline_memory),
                error_rate=error_rate,
                passed=error_rate < 0.1 and total_duration < 120,
            )

            # Print results
            print(f"\n{'=' * 80}")
            print("Concurrent Load Test Results:")
            print(f"  Total Operations: {metrics.total_operations}")
            print(f"  Successful: {metrics.successful_operations}")
            print(f"  Failed: {metrics.failed_operations}")
            print(f"  Error Rate: {metrics.error_rate * 100:.2f}%")
            print(f"  Total Duration: {metrics.total_duration_seconds:.2f}s")
            print(f"  Throughput: {metrics.operations_per_second:.2f} ops/sec")
            print(f"  Mean Latency: {metrics.mean_latency_seconds:.2f}s")
            print(f"  p95 Latency: {metrics.p95_latency_seconds:.2f}s")
            print(f"  Peak CPU: {metrics.peak_cpu_percent:.1f}%")
            print(f"  Peak Memory: {metrics.peak_memory_mb:.2f} MB")
            print(f"  Memory Leak: {metrics.memory_leaked_mb:.2f} MB")
            print(f"{'=' * 80}\n")

            # Assertions
            assert metrics.passed, "Concurrent load test failed criteria"
            assert (
                metrics.error_rate < 0.1
            ), f"Error rate too high: {metrics.error_rate * 100:.2f}%"
            assert (
                metrics.memory_leaked_mb < 200
            ), f"Excessive memory leak: {metrics.memory_leaked_mb:.2f} MB"

        finally:
            monitor.stop()
            gc.collect()


class TestSustainedLoad:
    """Test sustained load over time"""

    @pytest.mark.slow
    def test_sustained_load_100_operations(self):
        """Test 100 sequential operations (sustained load)"""
        print("\n" + "=" * 80)
        print("LOAD TEST: 100 Sequential Operations (10K rows each)")
        print("=" * 80)

        num_operations = 100
        dataset_size = 10_000

        # Setup monitoring
        monitor = ResourceMonitor()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        scenarios = LoadTestScenarios()

        print(f"Running {num_operations} sequential validations...")
        monitor.start()
        start_time = time.time()

        results = []
        latencies = []

        try:
            for i in range(num_operations):
                df = generate_large_player_dataset(dataset_size)
                result = scenarios.single_validation_operation(df, i)
                results.append(result)
                latencies.append(result.duration_seconds)

                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{num_operations} operations completed")

                # Force garbage collection every 20 operations
                if (i + 1) % 20 == 0:
                    gc.collect()

            total_duration = time.time() - start_time
            monitor.stop()

            # Calculate metrics
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            error_rate = failed / len(results)

            latencies.sort()
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)

            metrics = LoadTestMetrics(
                test_name="100_sustained_operations",
                total_operations=len(results),
                successful_operations=successful,
                failed_operations=failed,
                total_duration_seconds=total_duration,
                operations_per_second=len(results) / total_duration,
                mean_latency_seconds=sum(latencies) / len(latencies),
                median_latency_seconds=latencies[len(latencies) // 2],
                p95_latency_seconds=latencies[p95_idx],
                p99_latency_seconds=latencies[p99_idx],
                peak_cpu_percent=monitor.get_peak_cpu(),
                peak_memory_mb=monitor.get_peak_memory(),
                memory_leaked_mb=monitor.get_memory_leak(baseline_memory),
                error_rate=error_rate,
                passed=error_rate < 0.05 and total_duration < 300,
            )

            # Print results
            print(f"\n{'=' * 80}")
            print("Sustained Load Test Results:")
            print(f"  Total Operations: {metrics.total_operations}")
            print(f"  Successful: {metrics.successful_operations}")
            print(f"  Failed: {metrics.failed_operations}")
            print(f"  Error Rate: {metrics.error_rate * 100:.2f}%")
            print(f"  Total Duration: {metrics.total_duration_seconds:.2f}s")
            print(f"  Throughput: {metrics.operations_per_second:.2f} ops/sec")
            print(f"  Mean Latency: {metrics.mean_latency_seconds:.2f}s")
            print(f"  p95 Latency: {metrics.p95_latency_seconds:.2f}s")
            print(f"  Peak CPU: {metrics.peak_cpu_percent:.1f}%")
            print(f"  Peak Memory: {metrics.peak_memory_mb:.2f} MB")
            print(f"  Memory Leak: {metrics.memory_leaked_mb:.2f} MB")
            print(f"{'=' * 80}\n")

            # Assertions
            assert metrics.passed, "Sustained load test failed criteria"
            assert (
                metrics.error_rate < 0.05
            ), f"Error rate too high: {metrics.error_rate * 100:.2f}%"
            assert (
                metrics.memory_leaked_mb < 50
            ), f"Memory leak detected: {metrics.memory_leaked_mb:.2f} MB"

        finally:
            monitor.stop()
            gc.collect()


class TestMemoryPressure:
    """Test behavior under memory pressure"""

    @pytest.mark.slow
    def test_memory_leak_detection(self):
        """Test for memory leaks over 50 operations"""
        print("\n" + "=" * 80)
        print("LOAD TEST: Memory Leak Detection (50 operations)")
        print("=" * 80)

        num_operations = 50
        dataset_size = 50_000

        scenarios = LoadTestScenarios()

        # Track memory over time
        memory_samples = []

        for i in range(num_operations):
            df = generate_large_player_dataset(dataset_size)
            result = scenarios.single_validation_operation(df, i)

            # Sample memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)

            # Force garbage collection
            del df
            gc.collect()

        # Analyze memory trend
        early_memory = sum(memory_samples[:10]) / 10
        late_memory = sum(memory_samples[-10:]) / 10
        memory_growth = late_memory - early_memory

        print(f"\n{'=' * 80}")
        print("Memory Leak Analysis:")
        print(f"  Early Memory (ops 1-10): {early_memory:.2f} MB")
        print(f"  Late Memory (ops 41-50): {late_memory:.2f} MB")
        print(f"  Memory Growth: {memory_growth:.2f} MB")
        print(f"  Growth per Operation: {memory_growth / num_operations:.2f} MB")
        print(f"{'=' * 80}\n")

        # Memory leak threshold: <1 MB per operation
        assert (
            memory_growth / num_operations < 1.0
        ), f"Memory leak detected: {memory_growth / num_operations:.2f} MB/op"


class TestGracefulDegradation:
    """Test graceful degradation under extreme load"""

    @pytest.mark.slow
    def test_extreme_concurrent_load(self):
        """Test with 25 concurrent workers (stress test)"""
        print("\n" + "=" * 80)
        print("LOAD TEST: Extreme Concurrent Load (25 workers)")
        print("=" * 80)

        num_workers = 25
        dataset_size = 50_000

        # Generate datasets
        print(f"Generating {num_workers} datasets of {dataset_size:,} rows each...")
        datasets = [
            generate_large_player_dataset(dataset_size) for _ in range(num_workers)
        ]

        # Setup monitoring
        monitor = ResourceMonitor()

        scenarios = LoadTestScenarios()

        print(f"Running {num_workers} concurrent validations (stress test)...")
        monitor.start()
        start_time = time.time()

        results = []

        try:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(scenarios.single_validation_operation, df, i)
                    for i, df in enumerate(datasets)
                ]

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

            total_duration = time.time() - start_time
            monitor.stop()

            # Calculate metrics
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            error_rate = failed / len(results)

            print(f"\n{'=' * 80}")
            print("Extreme Load Test Results:")
            print(f"  Total Operations: {len(results)}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Error Rate: {error_rate * 100:.2f}%")
            print(f"  Total Duration: {total_duration:.2f}s")
            print(f"  Peak CPU: {monitor.get_peak_cpu():.1f}%")
            print(f"  Peak Memory: {monitor.get_peak_memory():.2f} MB")
            print(f"{'=' * 80}\n")

            # Under extreme load, accept higher error rate but system shouldn't crash
            assert (
                error_rate < 0.15
            ), f"Error rate too high even under stress: {error_rate * 100:.2f}%"
            assert successful > 0, "System completely failed under load"

        finally:
            monitor.stop()
            gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "slow"])
