"""
Unit Tests for Simulation Quality Framework (Agent 10, Module 2)

Tests quality metrics, realism scoring, and variance analysis.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from mcp_server.simulations.validation.quality_framework import (
    SimulationQualityChecker,
    QualityMetrics,
    HistoricalStats,
)


class TestHistoricalStats:
    """Test HistoricalStats dataclass"""

    def test_historical_stats_creation(self):
        """Test creating historical stats"""
        stats = HistoricalStats(
            stat_name="points",
            mean=100.0,
            std=10.0,
            min_value=70.0,
            max_value=130.0,
            percentile_25=95.0,
            percentile_50=100.0,
            percentile_75=105.0,
        )
        assert stats.stat_name == "points"
        assert stats.mean == 100.0

    def test_is_within_range_true(self):
        """Test value within range"""
        stats = HistoricalStats("points", 100.0, 10.0, 70.0, 130.0, 95.0, 100.0, 105.0)
        assert stats.is_within_range(105.0) is True  # Within 3 std devs

    def test_is_within_range_false(self):
        """Test value outside range"""
        stats = HistoricalStats("points", 100.0, 10.0, 70.0, 130.0, 95.0, 100.0, 105.0)
        assert stats.is_within_range(150.0) is False  # > 3 std devs

    def test_is_within_range_custom_threshold(self):
        """Test value with custom std dev threshold"""
        stats = HistoricalStats("points", 100.0, 10.0, 70.0, 130.0, 95.0, 100.0, 105.0)
        assert stats.is_within_range(115.0, std_devs=1.0) is False
        assert stats.is_within_range(115.0, std_devs=2.0) is True


class TestQualityMetrics:
    """Test QualityMetrics dataclass"""

    def test_quality_metrics_creation(self):
        """Test creating quality metrics"""
        metrics = QualityMetrics(
            realism_score=0.85,
            variance_score=0.90,
            historical_alignment=0.88,
            anomaly_count=0,
        )
        assert metrics.realism_score == 0.85
        assert metrics.variance_score == 0.90
        assert isinstance(metrics.computed_at, datetime)

    def test_is_high_quality_true(self):
        """Test high quality detection"""
        metrics = QualityMetrics(
            realism_score=0.85,
            variance_score=0.90,
            historical_alignment=0.88,
            anomaly_count=0,
        )
        assert metrics.is_high_quality() is True

    def test_is_high_quality_false_low_realism(self):
        """Test low quality due to realism"""
        metrics = QualityMetrics(
            realism_score=0.70,  # Below threshold
            variance_score=0.90,
            historical_alignment=0.88,
            anomaly_count=0,
        )
        assert metrics.is_high_quality() is False

    def test_is_high_quality_false_anomalies(self):
        """Test low quality due to anomalies"""
        metrics = QualityMetrics(
            realism_score=0.85,
            variance_score=0.90,
            historical_alignment=0.88,
            anomaly_count=5,  # Has anomalies
        )
        assert metrics.is_high_quality() is False

    def test_is_high_quality_custom_threshold(self):
        """Test custom quality threshold"""
        metrics = QualityMetrics(
            realism_score=0.75,
            variance_score=0.80,
            historical_alignment=0.77,
            anomaly_count=0,
        )
        assert metrics.is_high_quality(threshold=0.70) is True
        assert metrics.is_high_quality(threshold=0.80) is False


class TestSimulationQualityChecker:
    """Test SimulationQualityChecker class"""

    @pytest.fixture
    def historical_data(self):
        """Create sample historical data"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "points": np.random.normal(100, 10, 100),
                "rebounds": np.random.normal(45, 5, 100),
                "assists": np.random.normal(25, 4, 100),
            }
        )

    @pytest.fixture
    def checker(self, historical_data):
        """Create quality checker with historical data"""
        return SimulationQualityChecker(historical_data)

    def test_checker_initialization_no_data(self):
        """Test initializing without historical data"""
        checker = SimulationQualityChecker()
        assert checker.historical_data is None
        assert len(checker.historical_stats) == 0
        assert checker.quality_checks_performed == 0

    def test_checker_initialization_with_data(self, checker, historical_data):
        """Test initializing with historical data"""
        assert checker.historical_data is not None
        assert len(checker.historical_stats) > 0
        assert "points" in checker.historical_stats
        assert "rebounds" in checker.historical_stats
        assert "assists" in checker.historical_stats

    def test_compute_historical_stats(self, checker):
        """Test historical stats computation"""
        stats = checker.historical_stats["points"]
        assert isinstance(stats, HistoricalStats)
        assert stats.stat_name == "points"
        assert stats.mean > 0
        assert stats.std > 0

    def test_compute_realism_score_no_historical(self):
        """Test realism score without historical data"""
        checker = SimulationQualityChecker()
        sim_data = {"points": 100.0}
        score = checker.compute_realism_score(sim_data)
        assert score == 0.5  # Neutral score

    def test_compute_realism_score_perfect_match(self, checker):
        """Test realism score for perfect match"""
        # Get mean from historical stats
        mean_points = checker.historical_stats["points"].mean
        sim_data = {"points": mean_points}
        score = checker.compute_realism_score(sim_data)
        assert score >= 0.95  # Should be very high

    def test_compute_realism_score_outlier(self, checker):
        """Test realism score for outlier"""
        sim_data = {"points": 200.0}  # Way above normal
        score = checker.compute_realism_score(sim_data)
        assert score < 0.5  # Should be low

    def test_compute_realism_score_with_weights(self, checker):
        """Test realism score with custom weights"""
        sim_data = {"points": 100.0, "rebounds": 45.0}
        weights = {"points": 2.0, "rebounds": 1.0}
        score = checker.compute_realism_score(sim_data, weights)
        assert 0.0 <= score <= 1.0

    def test_analyze_variance_single_run(self, checker):
        """Test variance analysis with single run"""
        runs = [{"points": 100.0}]
        score = checker.analyze_variance(runs)
        assert score == 0.5  # Need multiple runs

    def test_analyze_variance_multiple_runs(self, checker):
        """Test variance analysis with multiple runs"""
        runs = [
            {"points": 100.0, "rebounds": 45.0},
            {"points": 105.0, "rebounds": 47.0},
            {"points": 95.0, "rebounds": 43.0},
            {"points": 102.0, "rebounds": 46.0},
            {"points": 98.0, "rebounds": 44.0},
        ]
        score = checker.analyze_variance(runs)
        assert 0.0 <= score <= 1.0

    def test_analyze_variance_with_expected(self, checker):
        """Test variance analysis with expected variance"""
        runs = [{"points": 100.0}, {"points": 110.0}, {"points": 90.0}]
        expected_var = {"points": 100.0}
        score = checker.analyze_variance(runs, expected_var)
        assert 0.0 <= score <= 1.0

    def test_validate_historical_alignment_good(self, checker):
        """Test historical alignment for good data"""
        sim_stats = {
            "points": 100.0,  # Close to historical mean
            "rebounds": 45.0,
            "assists": 25.0,
        }
        alignment, anomalies = checker.validate_historical_alignment(sim_stats)
        assert alignment >= 0.8
        assert len(anomalies) == 0

    def test_validate_historical_alignment_outliers(self, checker):
        """Test historical alignment with outliers"""
        sim_stats = {
            "points": 200.0,  # Way above normal
            "rebounds": 10.0,  # Way below normal
            "assists": 25.0,  # Normal
        }
        alignment, anomalies = checker.validate_historical_alignment(sim_stats)
        assert alignment < 1.0
        assert len(anomalies) > 0

    def test_validate_historical_alignment_no_historical(self):
        """Test historical alignment without historical data"""
        checker = SimulationQualityChecker()
        sim_stats = {"points": 100.0}
        alignment, anomalies = checker.validate_historical_alignment(sim_stats)
        assert alignment == 0.5
        assert len(anomalies) == 0

    def test_detect_anomalies_none(self, checker):
        """Test anomaly detection with normal data"""
        sim_data = {"points": 100.0, "rebounds": 45.0, "assists": 25.0}
        anomalies = checker.detect_anomalies(sim_data)
        assert len(anomalies) == 0

    def test_detect_anomalies_present(self, checker):
        """Test anomaly detection with outliers"""
        sim_data = {
            "points": 200.0,  # Anomaly
            "rebounds": 45.0,  # Normal
            "assists": 5.0,  # Anomaly
        }
        anomalies = checker.detect_anomalies(sim_data, threshold=3.0)
        assert len(anomalies) > 0
        assert any("points" in a for a in anomalies)

    def test_detect_anomalies_custom_threshold(self, checker):
        """Test anomaly detection with custom threshold"""
        sim_data = {"points": 120.0}  # Moderate outlier

        # Stricter threshold
        anomalies_strict = checker.detect_anomalies(sim_data, threshold=1.0)
        # Lenient threshold
        anomalies_lenient = checker.detect_anomalies(sim_data, threshold=5.0)

        # Stricter should catch more anomalies
        assert len(anomalies_strict) >= len(anomalies_lenient)

    def test_compute_quality_metrics_single_run(self, checker):
        """Test computing quality metrics for single run"""
        sim_data = {"points": 100.0, "rebounds": 45.0, "assists": 25.0}
        metrics = checker.compute_quality_metrics(sim_data)

        assert isinstance(metrics, QualityMetrics)
        assert 0.0 <= metrics.realism_score <= 1.0
        assert 0.0 <= metrics.historical_alignment <= 1.0

    def test_compute_quality_metrics_multiple_runs(self, checker):
        """Test computing quality metrics with multiple runs"""
        sim_data = {"points": 100.0, "rebounds": 45.0}
        sim_runs = [
            {"points": 100.0, "rebounds": 45.0},
            {"points": 105.0, "rebounds": 47.0},
            {"points": 95.0, "rebounds": 43.0},
        ]
        metrics = checker.compute_quality_metrics(sim_data, sim_runs)

        assert isinstance(metrics, QualityMetrics)
        assert 0.0 <= metrics.variance_score <= 1.0

    def test_get_statistics(self, checker):
        """Test getting checker statistics"""
        # Perform some checks
        checker.compute_realism_score({"points": 100.0})
        checker.detect_anomalies({"points": 100.0})

        stats = checker.get_statistics()
        assert stats["total_checks"] == 2
        assert stats["has_historical_data"] is True
        assert stats["historical_stats_available"] > 0

    def test_quality_checks_counter(self, checker):
        """Test quality checks counter increments"""
        initial_count = checker.quality_checks_performed

        checker.compute_realism_score({"points": 100.0})
        assert checker.quality_checks_performed == initial_count + 1

        checker.analyze_variance([{"points": 100.0}, {"points": 105.0}])
        assert checker.quality_checks_performed == initial_count + 2

        checker.validate_historical_alignment({"points": 100.0})
        assert checker.quality_checks_performed == initial_count + 3
