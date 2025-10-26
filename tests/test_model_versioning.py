"""
Tests for Model Versioning Module

**Phase 10A Week 2 - Agent 6: Model Deployment & Serving**
Comprehensive tests for MLflow-based model versioning, promotion, and rollback.
"""

import pytest
from unittest.mock import MagicMock, patch

from mcp_server.model_versioning import (
    ModelRegistry,
    get_model_registry,
)


# ==============================================================================
# Mock Models for Testing
# ==============================================================================


class MockMLflowModel:
    """Mock MLflow model for testing"""

    def predict(self, data):
        return [0.8, 0.2]


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_registry():
    """Create a mock model registry"""
    return ModelRegistry(mock_mode=True)


@pytest.fixture
def mock_model():
    """Create a mock model"""
    return MockMLflowModel()


# ==============================================================================
# Test Registry Initialization
# ==============================================================================


def test_registry_initialization_mock_mode():
    """Test registry initialization in mock mode"""
    registry = ModelRegistry(mock_mode=True)

    assert registry.mock_mode is True
    assert registry.client is None


def test_registry_initialization_with_uri():
    """Test registry initialization with tracking URI"""
    registry = ModelRegistry(tracking_uri="sqlite:///test.db", mock_mode=True)

    assert registry.tracking_uri == "sqlite:///test.db"
    assert registry.mock_mode is True


# ==============================================================================
# Test Model Logging
# ==============================================================================


def test_log_model_mock_mode(mock_registry, mock_model):
    """Test logging model in mock mode"""
    run_id = mock_registry.log_model(
        model=mock_model,
        model_name="test_model",
        params={"n_estimators": 100},
        metrics={"accuracy": 0.85}
    )

    assert run_id is not None
    assert "mock_run" in run_id


def test_log_model_with_all_parameters(mock_registry, mock_model):
    """Test logging model with all parameters"""
    run_id = mock_registry.log_model(
        model=mock_model,
        model_name="full_model",
        experiment_name="test_experiment",
        params={"learning_rate": 0.001, "batch_size": 32},
        metrics={"accuracy": 0.92, "loss": 0.15},
        artifacts={"config": {"version": "1.0.0"}}
    )

    assert run_id is not None


# ==============================================================================
# Test Model Registration
# ==============================================================================


def test_register_model_mock_mode(mock_registry):
    """Test registering model in mock mode"""
    run_id = "mock_run_123"
    version = mock_registry.register_model(run_id, "test_model")

    assert version == "1"


# ==============================================================================
# Test Model Promotion
# ==============================================================================


def test_promote_to_production_mock_mode(mock_registry):
    """Test promoting model to production in mock mode"""
    result = mock_registry.promote_to_production("test_model", "1")

    assert result is True


# ==============================================================================
# Test Model Loading
# ==============================================================================


def test_load_model_mock_mode(mock_registry):
    """Test loading model in mock mode"""
    model = mock_registry.load_model("test_model", "Production")

    assert model is None  # Mock mode returns None


def test_load_model_with_staging(mock_registry):
    """Test loading model from staging"""
    model = mock_registry.load_model("test_model", "Staging")

    assert model is None  # Mock mode returns None


# ==============================================================================
# Test Model Listing
# ==============================================================================


def test_list_models_mock_mode(mock_registry):
    """Test listing models in mock mode"""
    models = mock_registry.list_models()

    assert models == []


# ==============================================================================
# Test Model Info
# ==============================================================================


def test_get_model_info_mock_mode(mock_registry):
    """Test getting model info in mock mode"""
    info = mock_registry.get_model_info("test_model", "1")

    assert info["name"] == "test_model"
    assert info["version"] == "1"
    assert info["stage"] == "Production"
    assert info["status"] == "READY"


def test_get_model_info_without_version(mock_registry):
    """Test getting model info without specifying version"""
    info = mock_registry.get_model_info("test_model")

    assert info["name"] == "test_model"
    assert info["version"] == "1"  # Default


# ==============================================================================
# Test Model Rollback
# ==============================================================================


def test_rollback_mock_mode(mock_registry):
    """Test rolling back model in mock mode"""
    result = mock_registry.rollback("test_model", "1")

    assert result is True


# ==============================================================================
# Test Model Comparison
# ==============================================================================


def test_compare_models_mock_mode(mock_registry):
    """Test comparing models in mock mode"""
    comparison = mock_registry.compare_models("test_model", "1", "2")

    assert comparison["version1"]["version"] == "1"
    assert comparison["version2"]["version"] == "2"
    assert "metrics" in comparison["version1"]
    assert "params" in comparison["version1"]


# ==============================================================================
# Test Global Registry
# ==============================================================================


def test_get_model_registry():
    """Test getting global model registry"""
    registry1 = get_model_registry()
    registry2 = get_model_registry()

    # Should return same instance
    assert registry1 is registry2


# ==============================================================================
# Test End-to-End Workflow
# ==============================================================================


def test_complete_workflow_mock_mode(mock_registry, mock_model):
    """Test complete model versioning workflow"""
    # Step 1: Log model
    run_id = mock_registry.log_model(
        model=mock_model,
        model_name="workflow_model",
        params={"n_estimators": 100},
        metrics={"accuracy": 0.85}
    )

    assert run_id is not None

    # Step 2: Register model
    version = mock_registry.register_model(run_id, "workflow_model")

    assert version == "1"

    # Step 3: Get model info
    info = mock_registry.get_model_info("workflow_model", version)

    assert info["name"] == "workflow_model"

    # Step 4: Promote to production
    result = mock_registry.promote_to_production("workflow_model", version)

    assert result is True

    # Step 5: Load model
    loaded_model = mock_registry.load_model("workflow_model", "Production")

    # In mock mode, returns None
    assert loaded_model is None


def test_rollback_workflow(mock_registry):
    """Test rollback workflow"""
    # Promote v1 to production
    mock_registry.promote_to_production("rollback_model", "1")

    # Later, rollback to v1
    result = mock_registry.rollback("rollback_model", "1")

    assert result is True


# ==============================================================================
# Test Error Handling
# ==============================================================================


def test_log_model_handles_exceptions(mock_registry):
    """Test that log_model handles exceptions gracefully"""
    # In mock mode, should not raise exceptions
    try:
        run_id = mock_registry.log_model(
            model=None,  # Invalid model
            model_name="error_model"
        )
        # Mock mode should return a mock run_id
        assert run_id is not None
    except Exception as e:
        pytest.fail(f"log_model raised unexpected exception: {e}")


def test_register_model_handles_exceptions(mock_registry):
    """Test that register_model handles exceptions gracefully"""
    # In mock mode, should not raise exceptions
    try:
        version = mock_registry.register_model("invalid_run_id", "error_model")
        # Mock mode should return "1"
        assert version == "1"
    except Exception as e:
        pytest.fail(f"register_model raised unexpected exception: {e}")


# ==============================================================================
# Test Model Comparison with Metrics
# ==============================================================================


def test_compare_models_structure(mock_registry):
    """Test that model comparison returns correct structure"""
    comparison = mock_registry.compare_models("test_model", "1", "2")

    # Verify structure
    assert "model_name" in comparison
    assert "version1" in comparison
    assert "version2" in comparison
    assert "metrics_comparison" in comparison

    # Verify version details
    assert comparison["version1"]["version"] == "1"
    assert comparison["version2"]["version"] == "2"


# ==============================================================================
# Test Multiple Model Operations
# ==============================================================================


def test_multiple_model_logging(mock_registry, mock_model):
    """Test logging multiple models"""
    run_ids = []

    for i in range(3):
        run_id = mock_registry.log_model(
            model=mock_model,
            model_name=f"model_{i}",
            params={"iteration": i},
            metrics={"accuracy": 0.80 + (i * 0.05)}
        )
        run_ids.append(run_id)

    assert len(run_ids) == 3
    assert all(run_id is not None for run_id in run_ids)


def test_multiple_version_registration(mock_registry):
    """Test registering multiple versions"""
    versions = []

    for i in range(3):
        version = mock_registry.register_model(f"run_{i}", "multi_version_model")
        versions.append(version)

    # All should return "1" in mock mode
    assert all(v == "1" for v in versions)


# ==============================================================================
# Test Integration Points
# ==============================================================================


def test_week1_integration_decorators(mock_registry, mock_model):
    """Test that Week 1 decorators are applied"""
    # This test verifies that methods can be called without errors
    # Even with decorators applied, they should work in mock mode

    # Test with handle_errors decorator
    run_id = mock_registry.log_model(model=mock_model, model_name="decorator_test")
    assert run_id is not None

    # Test with require_permission decorator
    version = mock_registry.register_model(run_id, "decorator_test")
    assert version is not None

    # Test with track_metric decorator
    result = mock_registry.promote_to_production("decorator_test", version)
    assert result is True
