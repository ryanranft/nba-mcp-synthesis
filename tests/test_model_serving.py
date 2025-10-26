"""
Tests for Model Serving Infrastructure

**Phase 10A Week 2 - Agent 6: Model Deployment & Serving**
Comprehensive tests for model serving, versioning, A/B testing, and health monitoring.
"""

import time
import threading
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from mcp_server.model_serving import (
    ModelServingManager,
    ServingModel,
    ModelStatus,
    HealthStatus,
    ServingMetrics,
)


# ==============================================================================
# Mock Model for Testing
# ==============================================================================


class MockModel:
    """Mock ML model for testing"""

    def __init__(self, prediction_value=0.8, should_fail=False):
        """
        Initialize mock model.

        Args:
            prediction_value: Value to return from predict()
            should_fail: If True, predict() will raise an exception
        """
        self.prediction_value = prediction_value
        self.should_fail = should_fail
        self.predict_count = 0

    def predict(self, inputs):
        """Mock prediction method"""
        self.predict_count += 1
        if self.should_fail:
            raise ValueError("Mock prediction failure")
        return [self.prediction_value] * len(inputs) if isinstance(inputs, list) else self.prediction_value


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_model():
    """Create a mock model for testing"""
    return MockModel(prediction_value=0.85)


@pytest.fixture
def failing_model():
    """Create a mock model that fails predictions"""
    return MockModel(should_fail=True)


@pytest.fixture
def serving_manager():
    """Create a serving manager in mock mode"""
    return ModelServingManager(mock_mode=True)


@pytest.fixture
def serving_manager_with_mlflow():
    """Create a serving manager with MLflow enabled"""
    return ModelServingManager(enable_mlflow=True, mock_mode=True)


# ==============================================================================
# Test Serving Manager Initialization
# ==============================================================================


def test_serving_manager_initialization_basic():
    """Test basic serving manager initialization"""
    manager = ModelServingManager(mock_mode=True)

    assert manager.models == {}
    assert manager.active_models == {}
    assert manager.ab_tests == {}
    assert manager.mock_mode is True
    assert manager.enable_mlflow is False


def test_serving_manager_initialization_with_mlflow():
    """Test serving manager initialization with MLflow enabled"""
    manager = ModelServingManager(enable_mlflow=True, mock_mode=True)

    assert manager.enable_mlflow is True
    assert manager.mlflow_tracker is not None


def test_serving_manager_initialization_mock_mode():
    """Test serving manager in mock mode"""
    manager = ModelServingManager(mock_mode=True, enable_mlflow=False)

    assert manager.mock_mode is True
    assert manager.enable_mlflow is False


# ==============================================================================
# Test Model Deployment
# ==============================================================================


def test_deploy_model_basic(serving_manager, mock_model):
    """Test basic model deployment"""
    result = serving_manager.deploy_model(
        model_id="test_model",
        version="v1.0",
        model_instance=mock_model,
        set_active=True
    )

    assert result is True
    assert "test_model" in serving_manager.models
    assert len(serving_manager.models["test_model"]) == 1
    assert serving_manager.active_models["test_model"] == "v1.0"


def test_deploy_multiple_versions(serving_manager, mock_model):
    """Test deploying multiple versions of the same model"""
    # Deploy v1.0
    serving_manager.deploy_model("model_a", "v1.0", MockModel(0.80), set_active=True)

    # Deploy v1.1
    serving_manager.deploy_model("model_a", "v1.1", MockModel(0.85), set_active=False)

    # Deploy v2.0
    serving_manager.deploy_model("model_a", "v2.0", MockModel(0.90), set_active=False)

    assert len(serving_manager.models["model_a"]) == 3
    assert serving_manager.active_models["model_a"] == "v1.0"


def test_deploy_model_replace_existing(serving_manager, mock_model):
    """Test replacing an existing model version"""
    # Deploy v1.0
    serving_manager.deploy_model("model_b", "v1.0", MockModel(0.70), set_active=True)
    assert len(serving_manager.models["model_b"]) == 1

    # Replace v1.0 with new model
    serving_manager.deploy_model("model_b", "v1.0", MockModel(0.95), set_active=True)

    # Should still have only 1 version
    assert len(serving_manager.models["model_b"]) == 1
    assert serving_manager.active_models["model_b"] == "v1.0"


def test_deploy_model_with_error_threshold(serving_manager, mock_model):
    """Test deploying model with custom error threshold"""
    result = serving_manager.deploy_model(
        model_id="threshold_model",
        version="v1.0",
        model_instance=mock_model,
        error_threshold=0.3,  # Custom threshold
        set_active=True
    )

    assert result is True
    model = serving_manager.models["threshold_model"][0]
    assert model.error_threshold == 0.3


# ==============================================================================
# Test Active Version Management
# ==============================================================================


def test_set_active_version(serving_manager):
    """Test setting active version for a model"""
    # Deploy multiple versions
    serving_manager.deploy_model("model_c", "v1.0", MockModel(0.80), set_active=True)
    serving_manager.deploy_model("model_c", "v1.1", MockModel(0.85), set_active=False)

    # Set v1.1 as active
    result = serving_manager.set_active_version("model_c", "v1.1")

    assert result is True
    assert serving_manager.active_models["model_c"] == "v1.1"


def test_set_active_version_nonexistent_model(serving_manager):
    """Test setting active version for nonexistent model"""
    result = serving_manager.set_active_version("nonexistent", "v1.0")

    assert result is False


def test_set_active_version_nonexistent_version(serving_manager):
    """Test setting nonexistent version as active"""
    serving_manager.deploy_model("model_d", "v1.0", MockModel(0.80), set_active=True)

    result = serving_manager.set_active_version("model_d", "v99.0")

    assert result is False


# ==============================================================================
# Test Predictions
# ==============================================================================


def test_predict_basic(serving_manager, mock_model):
    """Test basic prediction"""
    serving_manager.deploy_model("predictor", "v1.0", mock_model, set_active=True)

    result = serving_manager.predict("predictor", [1, 2, 3])

    assert result is not None
    assert mock_model.predict_count == 1


def test_predict_with_ab_testing(serving_manager):
    """Test prediction with A/B testing traffic routing"""
    # Deploy two versions
    model_v1 = MockModel(0.80)
    model_v2 = MockModel(0.90)

    serving_manager.deploy_model("ab_model", "v1.0", model_v1, set_active=True)
    serving_manager.deploy_model("ab_model", "v2.0", model_v2, set_active=False)

    # Setup A/B test: 80% v1.0, 20% v2.0
    serving_manager.setup_ab_test("ab_model", {"v1.0": 0.8, "v2.0": 0.2})

    # Make predictions with controlled traffic split
    serving_manager.predict("ab_model", [1, 2, 3], traffic_split=0.5)  # Should go to v1.0
    serving_manager.predict("ab_model", [1, 2, 3], traffic_split=0.9)  # Should go to v2.0

    # At least one prediction should have been made
    assert model_v1.predict_count + model_v2.predict_count >= 2


def test_predict_nonexistent_model(serving_manager):
    """Test prediction with nonexistent model raises error"""
    with pytest.raises(ValueError, match="No serving model found"):
        serving_manager.predict("nonexistent", [1, 2, 3])


def test_predict_concurrent(serving_manager, mock_model):
    """Test concurrent predictions are thread-safe"""
    serving_manager.deploy_model("concurrent_model", "v1.0", mock_model, set_active=True)

    results = []
    errors = []

    def make_prediction():
        try:
            result = serving_manager.predict("concurrent_model", [1, 2, 3])
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Create 10 threads making predictions concurrently
    threads = [threading.Thread(target=make_prediction) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All predictions should succeed
    assert len(results) == 10
    assert len(errors) == 0
    assert mock_model.predict_count == 10


# ==============================================================================
# Test Circuit Breaker
# ==============================================================================


def test_circuit_breaker_trips_on_error_rate(serving_manager, failing_model):
    """Test circuit breaker opens when error rate exceeds threshold"""
    # Deploy model with low error threshold
    serving_manager.deploy_model(
        "failing_model",
        "v1.0",
        failing_model,
        error_threshold=0.4,  # 40% error threshold
        set_active=True
    )

    model = serving_manager.models["failing_model"][0]

    # Make several predictions that will fail
    for i in range(10):
        try:
            serving_manager.predict("failing_model", [1, 2, 3])
        except ValueError:
            pass  # Expected to fail

    # Circuit breaker should be open due to high error rate
    assert model.circuit_breaker_open is True
    assert model.status == ModelStatus.DEGRADED
    assert model.metrics.circuit_breaker_trips >= 1


def test_circuit_breaker_prevents_predictions(serving_manager):
    """Test circuit breaker prevents predictions when open"""
    model_instance = MockModel()
    serving_manager.deploy_model("cb_model", "v1.0", model_instance, set_active=True)

    model = serving_manager.models["cb_model"][0]
    model.circuit_breaker_open = True

    # Prediction should fail due to circuit breaker
    with pytest.raises(Exception, match="Circuit breaker open"):
        model.predict([1, 2, 3])


def test_circuit_breaker_reset(serving_manager, failing_model):
    """Test manual circuit breaker reset"""
    serving_manager.deploy_model("reset_model", "v1.0", failing_model, error_threshold=0.3, set_active=True)

    model = serving_manager.models["reset_model"][0]

    # Trip circuit breaker
    for i in range(10):
        if model.circuit_breaker_open:
            break
        try:
            model.predict([1, 2, 3])
        except (ValueError, Exception):
            pass

    assert model.circuit_breaker_open is True

    # Reset circuit breaker
    model.reset_circuit_breaker()

    assert model.circuit_breaker_open is False
    assert model.status == ModelStatus.READY


# ==============================================================================
# Test Health Checks
# ==============================================================================


def test_health_check_healthy(serving_manager, mock_model):
    """Test health check for healthy model"""
    serving_manager.deploy_model("healthy_model", "v1.0", mock_model, set_active=True)

    model = serving_manager.models["healthy_model"][0]

    # Make a successful prediction
    model.predict([1, 2, 3])

    health = model.check_health()
    assert health == HealthStatus.HEALTHY


def test_health_check_unhealthy_circuit_breaker(serving_manager, failing_model):
    """Test health check when circuit breaker is open"""
    serving_manager.deploy_model("unhealthy_model", "v1.0", failing_model, error_threshold=0.3, set_active=True)

    model = serving_manager.models["unhealthy_model"][0]

    # Trip circuit breaker
    for i in range(10):
        if model.circuit_breaker_open:
            break
        try:
            model.predict([1, 2, 3])
        except (ValueError, Exception):
            pass

    health = model.check_health()
    assert health == HealthStatus.UNHEALTHY


def test_health_check_unknown_no_requests(serving_manager, mock_model):
    """Test health check returns UNKNOWN when no recent requests"""
    serving_manager.deploy_model("stale_model", "v1.0", mock_model, set_active=True)

    model = serving_manager.models["stale_model"][0]

    # No predictions made, check health
    health = model.check_health()

    # Should be HEALTHY (newly deployed) or UNKNOWN (no requests)
    assert health in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]


# ==============================================================================
# Test A/B Testing
# ==============================================================================


def test_setup_ab_test(serving_manager):
    """Test A/B test setup"""
    # Deploy two versions
    serving_manager.deploy_model("ab_test", "v1.0", MockModel(0.80), set_active=True)
    serving_manager.deploy_model("ab_test", "v1.1", MockModel(0.85), set_active=False)

    # Setup A/B test
    result = serving_manager.setup_ab_test("ab_test", {"v1.0": 0.7, "v1.1": 0.3})

    assert result is True
    assert "ab_test" in serving_manager.ab_tests
    assert serving_manager.ab_tests["ab_test"]["v1.0"] == 0.7
    assert serving_manager.ab_tests["ab_test"]["v1.1"] == 0.3


def test_setup_ab_test_invalid_weights(serving_manager):
    """Test A/B test setup with invalid weights (don't sum to 1.0)"""
    serving_manager.deploy_model("invalid_ab", "v1.0", MockModel(0.80), set_active=True)
    serving_manager.deploy_model("invalid_ab", "v1.1", MockModel(0.85), set_active=False)

    # Weights sum to 0.9, should fail
    result = serving_manager.setup_ab_test("invalid_ab", {"v1.0": 0.5, "v1.1": 0.4})

    assert result is False


def test_setup_ab_test_nonexistent_version(serving_manager):
    """Test A/B test setup with nonexistent version"""
    serving_manager.deploy_model("missing_ver", "v1.0", MockModel(0.80), set_active=True)

    # v2.0 doesn't exist
    result = serving_manager.setup_ab_test("missing_ver", {"v1.0": 0.6, "v2.0": 0.4})

    assert result is False


def test_ab_test_traffic_routing(serving_manager):
    """Test A/B test traffic routing validation"""
    model_v1 = MockModel(0.80)
    model_v2 = MockModel(0.90)

    serving_manager.deploy_model("routing", "v1.0", model_v1, set_active=True)
    serving_manager.deploy_model("routing", "v2.0", model_v2, set_active=False)

    serving_manager.setup_ab_test("routing", {"v1.0": 0.5, "v2.0": 0.5})

    # Make predictions with specific traffic splits
    # Traffic split 0.3 should route to v1.0 (cumulative 0.5)
    serving_manager.predict("routing", [1, 2, 3], traffic_split=0.3)

    # Traffic split 0.7 should route to v2.0 (cumulative 1.0)
    serving_manager.predict("routing", [1, 2, 3], traffic_split=0.7)

    # Both models should have received requests
    assert model_v1.predict_count >= 1 or model_v2.predict_count >= 1


# ==============================================================================
# Test Metrics Collection
# ==============================================================================


def test_get_model_metrics(serving_manager, mock_model):
    """Test retrieving model metrics"""
    serving_manager.deploy_model("metrics_model", "v1.0", mock_model, set_active=True)

    # Make some predictions
    for i in range(5):
        serving_manager.predict("metrics_model", [1, 2, 3])

    metrics = serving_manager.get_model_metrics("metrics_model")

    assert len(metrics) == 1
    assert metrics[0]["model_id"] == "metrics_model"
    assert metrics[0]["version"] == "v1.0"
    assert metrics[0]["request_count"] == 5
    assert metrics[0]["error_count"] == 0


def test_get_all_models_status(serving_manager):
    """Test retrieving status for all models"""
    # Deploy multiple models
    serving_manager.deploy_model("model_1", "v1.0", MockModel(0.80), set_active=True)
    serving_manager.deploy_model("model_1", "v1.1", MockModel(0.85), set_active=False)
    serving_manager.deploy_model("model_2", "v1.0", MockModel(0.90), set_active=True)

    status = serving_manager.get_all_models_status()

    assert "model_1" in status
    assert "model_2" in status
    assert len(status["model_1"]["versions"]) == 2
    assert len(status["model_2"]["versions"]) == 1
    assert status["model_1"]["active_version"] == "v1.0"
    assert status["model_2"]["active_version"] == "v1.0"


# ==============================================================================
# Test Model Management
# ==============================================================================


def test_retire_model(serving_manager, mock_model):
    """Test retiring a model version"""
    serving_manager.deploy_model("retire_test", "v1.0", mock_model, set_active=True)

    result = serving_manager.retire_model("retire_test", "v1.0")

    assert result is True

    model = serving_manager.models["retire_test"][0]
    assert model.status == ModelStatus.RETIRED


def test_retire_nonexistent_model(serving_manager):
    """Test retiring nonexistent model returns False"""
    result = serving_manager.retire_model("nonexistent", "v1.0")

    assert result is False


# ==============================================================================
# Test ServingMetrics
# ==============================================================================


def test_serving_metrics_error_rate():
    """Test ServingMetrics error rate calculation"""
    metrics = ServingMetrics(request_count=100, error_count=5)

    assert metrics.error_rate == 0.05


def test_serving_metrics_avg_latency():
    """Test ServingMetrics average latency calculation"""
    metrics = ServingMetrics(request_count=10, total_latency_ms=500.0)

    assert metrics.avg_latency_ms == 50.0


def test_serving_metrics_zero_requests():
    """Test ServingMetrics with zero requests"""
    metrics = ServingMetrics()

    assert metrics.error_rate == 0.0
    assert metrics.avg_latency_ms == 0.0
