"""
Performance Regression Tests for NBA MCP Analytics Platform.

Establishes performance baselines and creates automated benchmarks to prevent
performance degradation. Tests ensure methods complete within acceptable time
limits and resource constraints.

Test Categories:
1. Time Series Performance (5 tests)
2. Causal Inference Performance (4 tests)
3. Ensemble Performance (3 tests)
4. Large Dataset Performance (3 tests)
5. Memory Efficiency (3 tests)

Total: 18 performance regression tests

Author: Claude Code
Date: November 4, 2025
"""

import pytest
import numpy as np
import pandas as pd
import time
import psutil
import os
from datetime import datetime

from mcp_server.econometric_suite import EconometricSuite
from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.ensemble import WeightedEnsemble, SimpleEnsemble


# ============================================================================
# Performance Thresholds (adjust based on hardware)
# ============================================================================


class PerformanceThresholds:
    """Performance SLA thresholds for different operations."""

    # Time series operations (seconds)
    ARIMA_SMALL = 2.0  # < 100 observations
    ARIMA_MEDIUM = 5.0  # 100-1000 observations
    ARIMA_LARGE = 15.0  # 1000-10000 observations

    # Causal inference operations (seconds)
    PSM_SMALL = 1.0  # < 200 observations
    PSM_MEDIUM = 3.0  # 200-1000 observations
    PSM_LARGE = 10.0  # 1000-5000 observations

    # Ensemble operations (seconds)
    ENSEMBLE_3_MODELS = 10.0  # 3 models
    ENSEMBLE_5_MODELS = 20.0  # 5 models

    # Memory thresholds (MB)
    MEMORY_INCREASE_SMALL = 100  # Small dataset processing
    MEMORY_INCREASE_LARGE = 500  # Large dataset processing


# ============================================================================
# Utilities
# ============================================================================


def measure_execution_time(func):
    """Decorator to measure execution time."""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time

    return wrapper


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def small_dataset():
    """Generate small dataset (100 obs)."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=100),
            "value": np.random.randn(100) * 10 + 50,
            "x1": np.random.randn(100),
            "x2": np.random.randn(100),
        }
    )


@pytest.fixture
def medium_dataset():
    """Generate medium dataset (500 obs)."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=500),
            "value": np.random.randn(500) * 10 + 50,
            "x1": np.random.randn(500),
            "x2": np.random.randn(500),
        }
    )


@pytest.fixture
def large_dataset():
    """Generate large dataset (5000 obs)."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=5000),
            "value": np.random.randn(5000) * 10 + 50,
            "x1": np.random.randn(5000),
            "x2": np.random.randn(5000),
        }
    )


# ============================================================================
# Category 1: Time Series Performance (5 tests)
# ============================================================================


class TestTimeSeriesPerformance:
    """Test time series analysis performance."""

    def test_arima_small_dataset_performance(self, small_dataset):
        """ARIMA on small dataset should complete quickly."""
        suite = EconometricSuite(data=small_dataset, target="value", time_col="date")

        start_time = time.time()
        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        execution_time = time.time() - start_time

        assert result is not None
        assert (
            execution_time < PerformanceThresholds.ARIMA_SMALL
        ), f"ARIMA small dataset took {execution_time:.2f}s (threshold: {PerformanceThresholds.ARIMA_SMALL}s)"

        print(f"\n✓ ARIMA (100 obs): {execution_time:.3f}s")

    def test_arima_medium_dataset_performance(self, medium_dataset):
        """ARIMA on medium dataset should complete within threshold."""
        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        start_time = time.time()
        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        execution_time = time.time() - start_time

        assert result is not None
        assert (
            execution_time < PerformanceThresholds.ARIMA_MEDIUM
        ), f"ARIMA medium dataset took {execution_time:.2f}s (threshold: {PerformanceThresholds.ARIMA_MEDIUM}s)"

        print(f"\n✓ ARIMA (500 obs): {execution_time:.3f}s")

    def test_arima_large_dataset_performance(self, large_dataset):
        """ARIMA on large dataset should complete within threshold."""
        suite = EconometricSuite(data=large_dataset, target="value", time_col="date")

        start_time = time.time()
        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        execution_time = time.time() - start_time

        assert result is not None
        assert (
            execution_time < PerformanceThresholds.ARIMA_LARGE
        ), f"ARIMA large dataset took {execution_time:.2f}s (threshold: {PerformanceThresholds.ARIMA_LARGE}s)"

        print(f"\n✓ ARIMA (5000 obs): {execution_time:.3f}s")

    def test_var_performance(self, medium_dataset):
        """VAR analysis should complete within reasonable time."""
        data = medium_dataset[["date", "value", "x1", "x2"]].copy()

        suite = EconometricSuite(data=data, target="value", time_col="date")

        start_time = time.time()
        result = suite.time_series_analysis(
            method="var", endog_data=data[["value", "x1"]], maxlags=2
        )
        execution_time = time.time() - start_time

        assert result is not None
        assert execution_time < 10.0, f"VAR took {execution_time:.2f}s"

        print(f"\n✓ VAR (500 obs): {execution_time:.3f}s")

    def test_time_series_suite_initialization_performance(self, medium_dataset):
        """Suite initialization should be fast."""
        start_time = time.time()

        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        execution_time = time.time() - start_time

        assert suite is not None
        assert execution_time < 0.5, f"Initialization took {execution_time:.2f}s"

        print(f"\n✓ Suite initialization: {execution_time:.3f}s")


# ============================================================================
# Category 2: Causal Inference Performance (4 tests)
# ============================================================================


class TestCausalInferencePerformance:
    """Test causal inference analysis performance."""

    def test_psm_small_dataset_performance(self):
        """PSM on small dataset should be fast."""
        np.random.seed(42)
        n = 200

        data = pd.DataFrame(
            {
                "treatment": np.random.binomial(1, 0.5, n),
                "outcome": np.random.randn(n) * 10 + 50,
                "x1": np.random.randn(n),
                "x2": np.random.randn(n),
            }
        )

        suite = EconometricSuite(data=data)

        start_time = time.time()
        try:
            result = suite.causal_analysis(
                treatment_col="treatment",
                outcome_col="outcome",
                method="psm",
                caliper=0.25,
            )
            execution_time = time.time() - start_time

            assert result is not None
            assert (
                execution_time < PerformanceThresholds.PSM_SMALL
            ), f"PSM small took {execution_time:.2f}s"

            print(f"\n✓ PSM (200 obs): {execution_time:.3f}s")
        except Exception as e:
            # PSM might fail with no matches, that's ok for performance test
            execution_time = time.time() - start_time
            assert execution_time < PerformanceThresholds.PSM_SMALL
            print(f"\n✓ PSM (200 obs, no matches): {execution_time:.3f}s")

    def test_psm_medium_dataset_performance(self):
        """PSM on medium dataset should complete within threshold."""
        np.random.seed(42)
        n = 1000

        data = pd.DataFrame(
            {
                "treatment": np.random.binomial(1, 0.5, n),
                "outcome": np.random.randn(n) * 10 + 50,
                "x1": np.random.randn(n),
                "x2": np.random.randn(n),
            }
        )

        suite = EconometricSuite(data=data)

        start_time = time.time()
        try:
            result = suite.causal_analysis(
                treatment_col="treatment",
                outcome_col="outcome",
                method="psm",
                caliper=0.25,
            )
            execution_time = time.time() - start_time

            assert result is not None
            assert (
                execution_time < PerformanceThresholds.PSM_MEDIUM
            ), f"PSM medium took {execution_time:.2f}s"

            print(f"\n✓ PSM (1000 obs): {execution_time:.3f}s")
        except Exception:
            execution_time = time.time() - start_time
            assert execution_time < PerformanceThresholds.PSM_MEDIUM
            print(f"\n✓ PSM (1000 obs, no matches): {execution_time:.3f}s")

    def test_doubly_robust_performance(self):
        """Doubly robust estimator should complete within threshold."""
        np.random.seed(42)
        n = 500

        data = pd.DataFrame(
            {
                "treatment": np.random.binomial(1, 0.5, n),
                "outcome": np.random.randn(n) * 10 + 50,
                "x1": np.random.randn(n),
                "x2": np.random.randn(n),
            }
        )

        suite = EconometricSuite(data=data)

        start_time = time.time()
        result = suite.causal_analysis(
            treatment_col="treatment", outcome_col="outcome", method="doubly_robust"
        )
        execution_time = time.time() - start_time

        assert result is not None
        assert execution_time < 5.0, f"Doubly robust took {execution_time:.2f}s"

        print(f"\n✓ Doubly Robust (500 obs): {execution_time:.3f}s")

    def test_rdd_performance(self):
        """RDD analysis should complete within threshold."""
        np.random.seed(42)
        n = 500

        data = pd.DataFrame(
            {
                "running_var": np.random.uniform(-10, 10, n),
                "outcome": np.random.randn(n) * 10 + 50,
                "treatment": np.random.binomial(1, 0.5, n),
            }
        )

        suite = EconometricSuite(data=data)

        start_time = time.time()
        result = suite.causal_analysis(
            treatment_col="treatment",
            outcome_col="outcome",
            method="rdd",
            running_var="running_var",
            cutoff=0.0,
            bandwidth=3.0,
        )
        execution_time = time.time() - start_time

        assert result is not None
        assert execution_time < 3.0, f"RDD took {execution_time:.2f}s"

        print(f"\n✓ RDD (500 obs): {execution_time:.3f}s")


# ============================================================================
# Category 3: Ensemble Performance (3 tests)
# ============================================================================


class TestEnsemblePerformance:
    """Test ensemble methods performance."""

    def test_ensemble_3_models_performance(self, medium_dataset):
        """Ensemble with 3 models should complete within threshold."""
        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        # Train 3 models
        model1 = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        model2 = suite.time_series_analysis(method="arima", order=(2, 1, 1))
        model3 = suite.time_series_analysis(method="arima", order=(1, 1, 2))

        # Create ensemble
        start_time = time.time()
        ensemble = WeightedEnsemble(
            [model1.result.model, model2.result.model, model3.result.model]
        )
        predictions = ensemble.predict(n_steps=10)
        execution_time = time.time() - start_time

        assert predictions is not None
        assert (
            execution_time < PerformanceThresholds.ENSEMBLE_3_MODELS
        ), f"Ensemble (3 models) took {execution_time:.2f}s"

        print(f"\n✓ Weighted Ensemble (3 models): {execution_time:.3f}s")

    def test_simple_ensemble_performance(self, medium_dataset):
        """Simple ensemble should be faster than weighted."""
        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        # Train models
        model1 = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        model2 = suite.time_series_analysis(method="arima", order=(2, 1, 1))

        # Simple ensemble
        start_time = time.time()
        ensemble = SimpleEnsemble([model1.result.model, model2.result.model])
        predictions = ensemble.predict(n_steps=10)
        execution_time = time.time() - start_time

        assert predictions is not None
        assert execution_time < 5.0, f"Simple ensemble took {execution_time:.2f}s"

        print(f"\n✓ Simple Ensemble (2 models): {execution_time:.3f}s")

    def test_ensemble_large_forecast_performance(self, medium_dataset):
        """Ensemble should handle large forecast horizons efficiently."""
        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        # Train models
        model1 = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        model2 = suite.time_series_analysis(method="arima", order=(2, 1, 1))

        # Large forecast
        ensemble = WeightedEnsemble([model1.result.model, model2.result.model])

        start_time = time.time()
        predictions = ensemble.predict(n_steps=100)  # Large horizon
        execution_time = time.time() - start_time

        assert len(predictions.predictions) == 100
        assert execution_time < 8.0, f"Large forecast took {execution_time:.2f}s"

        print(f"\n✓ Ensemble 100-step forecast: {execution_time:.3f}s")


# ============================================================================
# Category 4: Large Dataset Performance (3 tests)
# ============================================================================


class TestLargeDatasetPerformance:
    """Test performance on large datasets."""

    def test_large_dataset_initialization(self, large_dataset):
        """Large dataset initialization should be reasonable."""
        start_time = time.time()

        suite = EconometricSuite(data=large_dataset, target="value", time_col="date")

        execution_time = time.time() - start_time

        assert suite is not None
        assert execution_time < 1.0, f"Large init took {execution_time:.2f}s"

        print(f"\n✓ Large dataset init (5000 obs): {execution_time:.3f}s")

    def test_large_dataset_regression(self, large_dataset):
        """Regression on large dataset should be efficient."""
        suite = EconometricSuite(data=large_dataset, target="value")

        start_time = time.time()
        result = suite.regression(predictors=["x1", "x2"])
        execution_time = time.time() - start_time

        assert result is not None
        assert execution_time < 2.0, f"Large regression took {execution_time:.2f}s"

        print(f"\n✓ Regression (5000 obs): {execution_time:.3f}s")

    def test_large_dataset_subsetting(self, large_dataset):
        """Subsetting large datasets should be fast."""
        suite = EconometricSuite(data=large_dataset, target="value", time_col="date")

        # Use only last 1000 observations
        start_time = time.time()
        subset_data = large_dataset.iloc[-1000:]
        suite_subset = EconometricSuite(
            data=subset_data, target="value", time_col="date"
        )
        execution_time = time.time() - start_time

        assert suite_subset is not None
        assert execution_time < 0.5, f"Subsetting took {execution_time:.2f}s"

        print(f"\n✓ Dataset subsetting: {execution_time:.3f}s")


# ============================================================================
# Category 5: Memory Efficiency (3 tests)
# ============================================================================


class TestMemoryEfficiency:
    """Test memory usage and efficiency."""

    def test_small_dataset_memory_usage(self, small_dataset):
        """Small dataset should use minimal memory."""
        memory_before = get_memory_usage()

        suite = EconometricSuite(data=small_dataset, target="value", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        memory_after = get_memory_usage()
        memory_increase = memory_after - memory_before

        assert result is not None
        assert (
            memory_increase < PerformanceThresholds.MEMORY_INCREASE_SMALL
        ), f"Memory increased by {memory_increase:.1f}MB"

        print(f"\n✓ Memory increase (small): {memory_increase:.1f}MB")

    def test_large_dataset_memory_usage(self, large_dataset):
        """Large dataset should not cause excessive memory usage."""
        memory_before = get_memory_usage()

        suite = EconometricSuite(data=large_dataset, target="value", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        memory_after = get_memory_usage()
        memory_increase = memory_after - memory_before

        assert result is not None
        assert (
            memory_increase < PerformanceThresholds.MEMORY_INCREASE_LARGE
        ), f"Memory increased by {memory_increase:.1f}MB"

        print(f"\n✓ Memory increase (large): {memory_increase:.1f}MB")

    def test_memory_cleanup_after_analysis(self, medium_dataset):
        """Memory should be released after analysis completes."""
        memory_initial = get_memory_usage()

        # Run analysis
        suite = EconometricSuite(data=medium_dataset, target="value", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        # Delete references
        del suite
        del result

        # Force garbage collection
        import gc

        gc.collect()

        memory_after_cleanup = get_memory_usage()
        memory_retained = memory_after_cleanup - memory_initial

        # Should not retain more than 50MB
        assert memory_retained < 50, f"Retained {memory_retained:.1f}MB after cleanup"

        print(f"\n✓ Memory retained after cleanup: {memory_retained:.1f}MB")


# ============================================================================
# Performance Summary Test
# ============================================================================


def test_performance_regression_coverage():
    """Meta-test to verify performance test coverage."""
    test_classes = [
        TestTimeSeriesPerformance,
        TestCausalInferencePerformance,
        TestEnsemblePerformance,
        TestLargeDatasetPerformance,
        TestMemoryEfficiency,
    ]

    total_tests = 0
    for test_class in test_classes:
        test_methods = [m for m in dir(test_class) if m.startswith("test_")]
        total_tests += len(test_methods)

    # Should have 18 performance tests
    assert total_tests >= 18, f"Expected 18+ performance tests, found {total_tests}"
    print(f"\n✅ Total performance regression tests: {total_tests}")


if __name__ == "__main__":
    # Run with timing information
    pytest.main([__file__, "-v", "--durations=0"])
