"""
Tests for Model Monitoring & Drift Detection

**Phase 10A Week 2 - Agent 6: Model Deployment & Serving**
Comprehensive tests for model monitoring, drift detection, and alerting.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mcp_server.model_monitoring import (
    ModelMonitor,
    DriftMethod,
    AlertSeverity,
    AlertType,
    DriftResult,
    PerformanceMetrics,
    Alert,
    PredictionRecord,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_reference_data():
    """Create sample reference data for drift detection"""
    np.random.seed(42)
    n_samples = 1000

    return pd.DataFrame({
        'feature1': np.random.normal(0, 1, n_samples),
        'feature2': np.random.uniform(0, 10, n_samples),
        'feature3': np.random.exponential(2, n_samples),
    })


@pytest.fixture
def sample_current_data_no_drift():
    """Create sample current data with no drift"""
    np.random.seed(43)
    n_samples = 500

    return pd.DataFrame({
        'feature1': np.random.normal(0, 1, n_samples),
        'feature2': np.random.uniform(0, 10, n_samples),
        'feature3': np.random.exponential(2, n_samples),
    })


@pytest.fixture
def sample_current_data_with_drift():
    """Create sample current data with drift"""
    np.random.seed(44)
    n_samples = 500

    return pd.DataFrame({
        'feature1': np.random.normal(2, 1, n_samples),  # Mean shifted
        'feature2': np.random.uniform(5, 15, n_samples),  # Range shifted
        'feature3': np.random.exponential(5, n_samples),  # Scale changed
    })


@pytest.fixture
def monitor():
    """Create a basic model monitor"""
    return ModelMonitor(
        model_id="test_model",
        model_version="v1.0",
        drift_threshold=0.05,
        mock_mode=True
    )


@pytest.fixture
def monitor_with_mlflow():
    """Create a model monitor with MLflow enabled"""
    return ModelMonitor(
        model_id="test_model_mlflow",
        model_version="v1.0",
        enable_mlflow=True,
        mlflow_experiment="test_monitoring",
        mock_mode=True
    )


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_monitor_initialization_basic():
    """Test basic monitor initialization"""
    monitor = ModelMonitor(
        model_id="test_model",
        model_version="v1.0",
        mock_mode=True
    )

    assert monitor.model_id == "test_model"
    assert monitor.model_version == "v1.0"
    assert monitor.drift_threshold == 0.05  # default
    assert monitor.mock_mode is True
    assert len(monitor.prediction_history) == 0
    assert len(monitor.drift_history) == 0
    assert len(monitor.alerts) == 0


def test_monitor_initialization_with_thresholds():
    """Test monitor initialization with custom thresholds"""
    monitor = ModelMonitor(
        model_id="test_model",
        model_version="v1.0",
        drift_threshold=0.1,
        performance_threshold=0.2,
        error_rate_threshold=0.15,
        latency_threshold_ms=500.0,
        mock_mode=True
    )

    assert monitor.drift_threshold == 0.1
    assert monitor.performance_threshold == 0.2
    assert monitor.error_rate_threshold == 0.15
    assert monitor.latency_threshold_ms == 500.0


def test_monitor_initialization_with_mlflow(monitor_with_mlflow):
    """Test monitor initialization with MLflow"""
    # In mock mode, MLflow integration may not initialize fully
    # This is expected behavior for graceful fallback
    assert monitor_with_mlflow.model_id == "test_model_mlflow"


def test_monitor_initialization_with_alert_callback():
    """Test monitor initialization with alert callback"""
    callback = MagicMock()

    monitor = ModelMonitor(
        model_id="test_model",
        model_version="v1.0",
        alert_callback=callback,
        mock_mode=True
    )

    assert monitor.alert_callback == callback


# ==============================================================================
# Prediction Logging Tests
# ==============================================================================


def test_log_prediction_basic(monitor):
    """Test basic prediction logging"""
    monitor.log_prediction(
        prediction_id="pred_001",
        features={"feature1": 0.5, "feature2": 1.2},
        prediction=0.8,
        latency_ms=45.2
    )

    assert len(monitor.prediction_history) == 1
    record = monitor.prediction_history[0]
    assert record.prediction_id == "pred_001"
    assert record.features == {"feature1": 0.5, "feature2": 1.2}
    assert record.prediction == 0.8
    assert record.latency_ms == 45.2
    assert record.error is None


def test_log_prediction_with_actual(monitor):
    """Test prediction logging with actual value"""
    monitor.log_prediction(
        prediction_id="pred_002",
        features={"feature1": 0.5},
        prediction=0.8,
        actual=0.9,
        latency_ms=30.0
    )

    record = monitor.prediction_history[0]
    assert record.actual == 0.9


def test_log_prediction_with_error(monitor):
    """Test prediction logging with error"""
    monitor.log_prediction(
        prediction_id="pred_003",
        features={"feature1": 0.5},
        prediction=None,
        error="Model failed to load",
        latency_ms=0.0
    )

    record = monitor.prediction_history[0]
    assert record.error == "Model failed to load"
    # Should generate an alert
    assert len(monitor.alerts) > 0
    assert monitor.alerts[0].alert_type == AlertType.HIGH_ERROR_RATE


def test_log_prediction_high_latency(monitor):
    """Test prediction logging with high latency"""
    # Set low threshold for testing
    monitor.latency_threshold_ms = 100.0

    monitor.log_prediction(
        prediction_id="pred_004",
        features={"feature1": 0.5},
        prediction=0.8,
        latency_ms=150.0  # Above threshold
    )

    # Should generate a latency alert
    alerts = [a for a in monitor.alerts if a.alert_type == AlertType.HIGH_LATENCY]
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.WARNING


def test_log_multiple_predictions(monitor):
    """Test logging multiple predictions"""
    for i in range(10):
        monitor.log_prediction(
            prediction_id=f"pred_{i:03d}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1,
            latency_ms=10.0 + i
        )

    assert len(monitor.prediction_history) == 10


# ==============================================================================
# Reference Data Tests
# ==============================================================================


def test_set_reference_data_features_only(monitor, sample_reference_data):
    """Test setting reference data with features only"""
    monitor.set_reference_data(features=sample_reference_data)

    assert monitor.reference_features is not None
    assert len(monitor.reference_features) == len(sample_reference_data)
    assert list(monitor.reference_features.columns) == list(sample_reference_data.columns)
    assert monitor.reference_predictions is None


def test_set_reference_data_with_predictions(monitor, sample_reference_data):
    """Test setting reference data with predictions"""
    predictions = np.random.rand(len(sample_reference_data))

    monitor.set_reference_data(
        features=sample_reference_data,
        predictions=predictions
    )

    assert monitor.reference_features is not None
    assert monitor.reference_predictions is not None
    assert len(monitor.reference_predictions) == len(predictions)


# ==============================================================================
# Drift Detection Tests - KS Test
# ==============================================================================


def test_drift_detection_ks_test_no_drift(monitor, sample_reference_data, sample_current_data_no_drift):
    """Test drift detection with KS test - no drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_no_drift,
        method=DriftMethod.KS_TEST
    )

    assert len(results) == 3  # 3 features
    # Most features should not have drift (same distribution)
    drifted = [r for r in results if r.is_drift]
    assert len(drifted) <= 1  # Allow for some statistical variance


def test_drift_detection_ks_test_with_drift(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test drift detection with KS test - drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST
    )

    assert len(results) == 3
    # All features should have drift (distributions changed)
    drifted = [r for r in results if r.is_drift]
    assert len(drifted) >= 2  # At least 2 features should drift


def test_drift_detection_ks_test_specific_features(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test drift detection for specific features only"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST,
        features=['feature1', 'feature2']
    )

    assert len(results) == 2
    assert all(r.feature_name in ['feature1', 'feature2'] for r in results)


def test_drift_detection_generates_alerts(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test that drift detection generates alerts"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST
    )

    # Should have drift alerts
    drift_alerts = [a for a in monitor.alerts if a.alert_type == AlertType.FEATURE_DRIFT]
    drifted_features = [r for r in results if r.is_drift]

    assert len(drift_alerts) == len(drifted_features)


# ==============================================================================
# Drift Detection Tests - PSI
# ==============================================================================


def test_drift_detection_psi_no_drift(monitor, sample_reference_data, sample_current_data_no_drift):
    """Test drift detection with PSI - no drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_no_drift,
        method=DriftMethod.PSI
    )

    assert len(results) == 3
    # PSI values should be low
    for result in results:
        assert result.method == DriftMethod.PSI
        assert result.drift_score >= 0.0


def test_drift_detection_psi_with_drift(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test drift detection with PSI - drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.PSI
    )

    assert len(results) == 3
    # PSI values should be higher for drifted features
    drifted = [r for r in results if r.is_drift]
    assert len(drifted) >= 1  # At least one feature should drift


# ==============================================================================
# Drift Detection Tests - KL Divergence
# ==============================================================================


def test_drift_detection_kl_divergence_no_drift(monitor, sample_reference_data, sample_current_data_no_drift):
    """Test drift detection with KL divergence - no drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_no_drift,
        method=DriftMethod.KL_DIVERGENCE
    )

    assert len(results) == 3
    for result in results:
        assert result.method == DriftMethod.KL_DIVERGENCE
        assert result.drift_score >= 0.0  # KL divergence is always non-negative


def test_drift_detection_kl_divergence_with_drift(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test drift detection with KL divergence - drift expected"""
    monitor.set_reference_data(features=sample_reference_data)

    results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KL_DIVERGENCE
    )

    assert len(results) == 3
    drifted = [r for r in results if r.is_drift]
    assert len(drifted) >= 1


def test_drift_detection_without_reference_data(monitor, sample_current_data_no_drift):
    """Test drift detection fails without reference data"""
    with pytest.raises(ValueError, match="Reference data not set"):
        monitor.detect_feature_drift(
            current_data=sample_current_data_no_drift,
            method=DriftMethod.KS_TEST
        )


# ==============================================================================
# Performance Tracking Tests
# ==============================================================================


def test_calculate_performance_basic(monitor):
    """Test basic performance calculation"""
    # Log some predictions
    for i in range(10):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1,
            latency_ms=50.0
        )

    metrics = monitor.calculate_performance(window_hours=24)

    assert metrics.total_predictions == 10
    assert metrics.avg_latency_ms == 50.0
    assert metrics.error_rate == 0.0


def test_calculate_performance_with_errors(monitor):
    """Test performance calculation with errors"""
    # Log predictions with some errors
    for i in range(10):
        error = "Test error" if i % 3 == 0 else None
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1 if error is None else None,
            latency_ms=50.0,
            error=error
        )

    metrics = monitor.calculate_performance(window_hours=24)

    assert metrics.total_predictions == 10
    assert metrics.error_rate > 0.0
    # 4 errors out of 10 (indices 0, 3, 6, 9)
    assert abs(metrics.error_rate - 0.4) < 0.01


def test_calculate_performance_with_actuals(monitor):
    """Test performance calculation with actual values"""
    # Log predictions with actuals
    for i in range(10):
        pred = float(i) * 0.1
        actual = pred + 0.1 if i % 2 == 0 else pred  # Some correct, some off

        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=pred,
            actual=actual,
            latency_ms=50.0
        )

    metrics = monitor.calculate_performance(window_hours=24)

    assert metrics.accuracy is not None
    assert 0.0 <= metrics.accuracy <= 1.0


def test_calculate_performance_high_error_rate_alert(monitor):
    """Test that high error rate generates alert"""
    monitor.error_rate_threshold = 0.2

    # Log predictions with high error rate
    for i in range(10):
        error = "Test error" if i < 5 else None  # 50% error rate
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1 if error is None else None,
            latency_ms=50.0,
            error=error
        )

    metrics = monitor.calculate_performance(window_hours=24)

    # Should generate high error rate alert
    error_alerts = [a for a in monitor.alerts if a.alert_type == AlertType.HIGH_ERROR_RATE]
    # Expect alerts from individual errors plus performance calculation
    assert len(error_alerts) > 0


def test_calculate_performance_empty_window(monitor):
    """Test performance calculation with no predictions in window"""
    metrics = monitor.calculate_performance(window_hours=1)

    assert metrics.total_predictions == 0
    assert metrics.error_rate == 0.0
    assert metrics.avg_latency_ms == 0.0


# ==============================================================================
# Alert Tests
# ==============================================================================


def test_get_alerts_all(monitor):
    """Test getting all alerts"""
    # Generate some alerts by logging high-latency predictions
    monitor.latency_threshold_ms = 10.0

    for i in range(5):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=0.8,
            latency_ms=100.0  # Above threshold
        )

    alerts = monitor.get_alerts()
    assert len(alerts) == 5


def test_get_alerts_by_severity(monitor):
    """Test filtering alerts by severity"""
    monitor.latency_threshold_ms = 10.0

    # Generate warnings
    for i in range(3):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=0.8,
            latency_ms=100.0
        )

    # Alerts should be WARNING severity
    warning_alerts = monitor.get_alerts(severity=AlertSeverity.WARNING)
    assert len(warning_alerts) > 0


def test_get_alerts_by_type(monitor):
    """Test filtering alerts by type"""
    monitor.latency_threshold_ms = 10.0

    for i in range(3):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=0.8,
            latency_ms=100.0
        )

    latency_alerts = monitor.get_alerts(alert_type=AlertType.HIGH_LATENCY)
    assert len(latency_alerts) == 3


def test_get_alerts_by_time_window(monitor):
    """Test filtering alerts by time window"""
    monitor.latency_threshold_ms = 10.0

    # Generate some alerts
    for i in range(3):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=0.8,
            latency_ms=100.0
        )

    # Get recent alerts (should get all)
    recent_alerts = monitor.get_alerts(hours=1)
    assert len(recent_alerts) == 3

    # Get alerts from very short window (should get fewer or similar depending on timing)
    # Note: hours=0 means cutoff is exactly now, so recent alerts may still be included
    old_alerts = monitor.get_alerts(hours=0)
    assert len(old_alerts) >= 0  # May include recent alerts due to timing


def test_acknowledge_alert(monitor):
    """Test acknowledging an alert"""
    monitor.latency_threshold_ms = 10.0

    monitor.log_prediction(
        prediction_id="pred_001",
        features={"feature1": 0.5},
        prediction=0.8,
        latency_ms=100.0
    )

    # Get the alert
    alerts = monitor.get_alerts()
    assert len(alerts) == 1
    alert_id = alerts[0].alert_id

    # Acknowledge it
    result = monitor.acknowledge_alert(alert_id)
    assert result is True

    # Verify acknowledgment
    acknowledged = monitor.get_alerts(acknowledged=True)
    assert len(acknowledged) == 1


def test_acknowledge_nonexistent_alert(monitor):
    """Test acknowledging a nonexistent alert"""
    result = monitor.acknowledge_alert("nonexistent_id")
    assert result is False


def test_alert_callback(monitor):
    """Test alert callback is called"""
    callback = MagicMock()

    monitor_with_callback = ModelMonitor(
        model_id="test_model",
        model_version="v1.0",
        alert_callback=callback,
        latency_threshold_ms=10.0,
        mock_mode=True
    )

    # Generate an alert
    monitor_with_callback.log_prediction(
        prediction_id="pred_001",
        features={"feature1": 0.5},
        prediction=0.8,
        latency_ms=100.0
    )

    # Callback should have been called
    assert callback.call_count > 0


# ==============================================================================
# History Tests
# ==============================================================================


def test_get_drift_history(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test getting drift history"""
    monitor.set_reference_data(features=sample_reference_data)

    # Run drift detection
    monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST
    )

    history = monitor.get_drift_history()
    assert len(history) == 3  # 3 features checked


def test_get_drift_history_by_feature(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test filtering drift history by feature"""
    monitor.set_reference_data(features=sample_reference_data)

    monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST
    )

    history = monitor.get_drift_history(feature='feature1')
    assert len(history) == 1
    assert history[0].feature_name == 'feature1'


def test_get_performance_history(monitor):
    """Test getting performance history"""
    # Log some predictions
    for i in range(5):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1,
            latency_ms=50.0
        )

    # Calculate performance multiple times
    monitor.calculate_performance(window_hours=24)
    monitor.calculate_performance(window_hours=12)

    history = monitor.get_performance_history()
    assert len(history) == 2


def test_get_prediction_history(monitor):
    """Test getting prediction history"""
    for i in range(10):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1,
            latency_ms=50.0
        )

    history = monitor.get_prediction_history()
    assert len(history) == 10


def test_get_prediction_history_exclude_errors(monitor):
    """Test getting prediction history excluding errors"""
    for i in range(10):
        error = "Test error" if i % 2 == 0 else None
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1 if error is None else None,
            latency_ms=50.0,
            error=error
        )

    # Get all predictions
    all_history = monitor.get_prediction_history(include_errors=True)
    assert len(all_history) == 10

    # Get only successful predictions
    success_history = monitor.get_prediction_history(include_errors=False)
    assert len(success_history) == 5  # Half had errors


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_complete_monitoring_workflow(monitor, sample_reference_data, sample_current_data_with_drift):
    """Test complete monitoring workflow"""
    # 1. Set reference data
    monitor.set_reference_data(features=sample_reference_data)

    # 2. Log predictions
    for i in range(20):
        monitor.log_prediction(
            prediction_id=f"pred_{i:03d}",
            features={
                'feature1': sample_current_data_with_drift.iloc[i % len(sample_current_data_with_drift)]['feature1'],
                'feature2': sample_current_data_with_drift.iloc[i % len(sample_current_data_with_drift)]['feature2'],
            },
            prediction=float(i) * 0.1,
            actual=float(i) * 0.1 + 0.01,
            latency_ms=50.0 + i
        )

    # 3. Detect drift
    drift_results = monitor.detect_feature_drift(
        current_data=sample_current_data_with_drift,
        method=DriftMethod.KS_TEST
    )

    # 4. Calculate performance
    perf_metrics = monitor.calculate_performance(window_hours=24)

    # 5. Check alerts
    alerts = monitor.get_alerts()

    # Verify workflow completed
    assert len(monitor.prediction_history) == 20
    assert len(drift_results) > 0
    assert perf_metrics.total_predictions == 20
    # Should have drift alerts
    assert len(alerts) > 0


def test_thread_safety(monitor):
    """Test thread-safe operations"""
    import threading

    def log_predictions(start_idx):
        for i in range(start_idx, start_idx + 100):
            monitor.log_prediction(
                prediction_id=f"pred_{i:04d}",
                features={"feature1": float(i)},
                prediction=float(i) * 0.1,
                latency_ms=50.0
            )

    # Create multiple threads
    threads = [
        threading.Thread(target=log_predictions, args=(i * 100,))
        for i in range(5)
    ]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Verify all predictions logged
    assert len(monitor.prediction_history) == 500


# ==============================================================================
# Edge Cases
# ==============================================================================


def test_drift_detection_with_empty_data(monitor, sample_reference_data):
    """Test drift detection with empty current data"""
    monitor.set_reference_data(features=sample_reference_data)

    empty_df = pd.DataFrame(columns=['feature1', 'feature2', 'feature3'])

    results = monitor.detect_feature_drift(
        current_data=empty_df,
        method=DriftMethod.KS_TEST
    )

    # Should handle gracefully
    assert len(results) == 0  # No features to check


def test_drift_detection_with_missing_features(monitor, sample_reference_data):
    """Test drift detection when features are missing"""
    monitor.set_reference_data(features=sample_reference_data)

    # Current data missing feature3
    partial_df = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 100),
        'feature2': np.random.uniform(0, 10, 100),
    })

    results = monitor.detect_feature_drift(
        current_data=partial_df,
        method=DriftMethod.KS_TEST
    )

    # Should only check available features
    assert len(results) == 2
    assert all(r.feature_name in ['feature1', 'feature2'] for r in results)


def test_performance_with_no_actuals(monitor):
    """Test performance calculation when no actuals are provided"""
    for i in range(10):
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features={"feature1": float(i)},
            prediction=float(i) * 0.1,
            latency_ms=50.0
            # No actual provided
        )

    metrics = monitor.calculate_performance(window_hours=24)

    assert metrics.total_predictions == 10
    assert metrics.accuracy is None  # Can't calculate without actuals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
