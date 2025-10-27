"""
Tests for Model Registry Module

**Phase 10A Week 2 - Agent 6: Model Deployment & Serving**
Comprehensive tests for model registry, lifecycle management, and model comparison.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mcp_server.model_registry import (
    ModelRegistry,
    ModelVersion,
    ModelStage,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def temp_registry_path():
    """Create a temporary registry path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def registry(temp_registry_path):
    """Create a model registry for testing"""
    return ModelRegistry(registry_path=temp_registry_path, mock_mode=True)


@pytest.fixture
def registry_with_mlflow(temp_registry_path):
    """Create a model registry with MLflow enabled"""
    return ModelRegistry(
        registry_path=temp_registry_path, enable_mlflow=True, mock_mode=True
    )


# ==============================================================================
# Test Registry Initialization
# ==============================================================================


def test_registry_initialization_basic(temp_registry_path):
    """Test basic registry initialization"""
    registry = ModelRegistry(registry_path=temp_registry_path)

    assert registry.registry_path == Path(temp_registry_path)
    assert registry.models == {}
    assert registry.enable_mlflow is False


def test_registry_initialization_with_mlflow(temp_registry_path):
    """Test registry initialization with MLflow"""
    registry = ModelRegistry(
        registry_path=temp_registry_path, enable_mlflow=True, mock_mode=True
    )

    assert registry.enable_mlflow is True
    assert registry.mlflow_tracker is not None


def test_registry_creates_directory(temp_registry_path):
    """Test that registry creates storage directory"""
    registry_path = Path(temp_registry_path) / "new_registry"
    registry = ModelRegistry(registry_path=str(registry_path))

    assert registry_path.exists()
    assert registry_path.is_dir()


# ==============================================================================
# Test Model Registration
# ==============================================================================


def test_register_model_basic(registry):
    """Test basic model registration"""
    model_version = registry.register_model(
        model_id="test_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="test_user",
        metrics={"accuracy": 0.85, "f1": 0.83},
        hyperparameters={"n_estimators": 100, "max_depth": 10},
    )

    assert model_version.model_id == "test_model"
    assert model_version.version == "1.0.0"
    assert model_version.framework == "sklearn"
    assert model_version.algorithm == "RandomForest"
    assert model_version.stage == ModelStage.DEVELOPMENT
    assert model_version.metrics["accuracy"] == 0.85


def test_register_multiple_versions(registry):
    """Test registering multiple versions of same model"""
    # Register v1.0.0
    v1 = registry.register_model(
        model_id="model_a",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        metrics={"accuracy": 0.80},
    )

    # Register v1.1.0
    v2 = registry.register_model(
        model_id="model_a",
        version="1.1.0",
        framework="sklearn",
        algorithm="GradientBoosting",
        created_by="user2",
        metrics={"accuracy": 0.85},
        parent_version="1.0.0",
    )

    assert len(registry.models["model_a"]) == 2
    assert v1.version == "1.0.0"
    assert v2.version == "1.1.0"
    assert v2.parent_version == "1.0.0"


def test_register_model_with_all_metadata(registry):
    """Test registering model with complete metadata"""
    model_version = registry.register_model(
        model_id="full_model",
        version="1.0.0",
        framework="pytorch",
        algorithm="CNN",
        created_by="ml_engineer",
        metrics={"accuracy": 0.92, "loss": 0.15},
        hyperparameters={"learning_rate": 0.001, "batch_size": 32},
        training_dataset="nba_stats_2023",
        artifact_path="/models/full_model/1.0.0",
        description="Production CNN model",
        tags={"team": "ml", "project": "nba"},
        stage=ModelStage.PRODUCTION,
    )

    assert model_version.training_dataset == "nba_stats_2023"
    assert model_version.artifact_path == "/models/full_model/1.0.0"
    assert model_version.description == "Production CNN model"
    assert model_version.tags["team"] == "ml"
    assert model_version.stage == ModelStage.PRODUCTION


# ==============================================================================
# Test Model Retrieval
# ==============================================================================


def test_get_model_version_specific(registry):
    """Test retrieving specific model version"""
    registry.register_model(
        model_id="model_b",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
    )
    registry.register_model(
        model_id="model_b",
        version="2.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
    )

    version = registry.get_model_version("model_b", "1.0.0")

    assert version is not None
    assert version.version == "1.0.0"


def test_get_model_version_latest(registry):
    """Test retrieving latest model version"""
    registry.register_model(
        model_id="model_c",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
    )
    registry.register_model(
        model_id="model_c",
        version="2.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
    )

    # Get latest (should be v2.0.0)
    version = registry.get_model_version("model_c")

    assert version is not None
    assert version.version == "2.0.0"


def test_get_model_version_nonexistent(registry):
    """Test retrieving nonexistent model version"""
    version = registry.get_model_version("nonexistent", "1.0.0")

    assert version is None


def test_get_production_model(registry):
    """Test retrieving production model"""
    registry.register_model(
        model_id="prod_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        stage=ModelStage.DEVELOPMENT,
    )
    registry.register_model(
        model_id="prod_model",
        version="2.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        stage=ModelStage.PRODUCTION,
    )

    prod_version = registry.get_production_model("prod_model")

    assert prod_version is not None
    assert prod_version.version == "2.0.0"
    assert prod_version.stage == ModelStage.PRODUCTION


def test_get_production_model_none_available(registry):
    """Test retrieving production model when none exists"""
    registry.register_model(
        model_id="dev_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        stage=ModelStage.DEVELOPMENT,
    )

    prod_version = registry.get_production_model("dev_model")

    assert prod_version is None


# ==============================================================================
# Test Model Promotion
# ==============================================================================


def test_promote_model(registry):
    """Test promoting model to new stage"""
    registry.register_model(
        model_id="promote_test",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        stage=ModelStage.DEVELOPMENT,
    )

    result = registry.promote_model("promote_test", "1.0.0", ModelStage.PRODUCTION)

    assert result is True
    version = registry.get_model_version("promote_test", "1.0.0")
    assert version.stage == ModelStage.PRODUCTION


def test_promote_nonexistent_model(registry):
    """Test promoting nonexistent model raises error"""
    with pytest.raises(ValueError, match="not found"):
        registry.promote_model("nonexistent", "1.0.0", ModelStage.PRODUCTION)


# ==============================================================================
# Test Model Search
# ==============================================================================


def test_search_models_by_framework(registry):
    """Test searching models by framework"""
    registry.register_model(
        model_id="model_1",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
    )
    registry.register_model(
        model_id="model_2",
        version="1.0.0",
        framework="pytorch",
        algorithm="CNN",
        created_by="user1",
    )

    results = registry.search_models(framework="sklearn")

    assert len(results) == 1
    assert results[0].framework == "sklearn"


def test_search_models_by_stage(registry):
    """Test searching models by stage"""
    registry.register_model(
        model_id="model_3",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        stage=ModelStage.PRODUCTION,
    )
    registry.register_model(
        model_id="model_4",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        stage=ModelStage.DEVELOPMENT,
    )

    results = registry.search_models(stage=ModelStage.PRODUCTION)

    assert len(results) == 1
    assert results[0].stage == ModelStage.PRODUCTION


def test_search_models_by_min_accuracy(registry):
    """Test searching models by minimum accuracy"""
    registry.register_model(
        model_id="model_5",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        metrics={"accuracy": 0.75},
    )
    registry.register_model(
        model_id="model_6",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        metrics={"accuracy": 0.90},
    )

    results = registry.search_models(min_accuracy=0.85)

    assert len(results) == 1
    assert results[0].metrics["accuracy"] == 0.90


def test_search_models_combined_criteria(registry):
    """Test searching models with multiple criteria"""
    registry.register_model(
        model_id="model_7",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        metrics={"accuracy": 0.90},
        tags={"team": "ml"},
        stage=ModelStage.PRODUCTION,
    )
    registry.register_model(
        model_id="model_8",
        version="1.0.0",
        framework="pytorch",
        algorithm="CNN",
        created_by="user1",
        metrics={"accuracy": 0.85},
        stage=ModelStage.DEVELOPMENT,
    )

    results = registry.search_models(
        framework="sklearn",
        stage=ModelStage.PRODUCTION,
        tags={"team": "ml"},
        min_accuracy=0.85,
    )

    assert len(results) == 1
    assert results[0].model_id == "model_7"


# ==============================================================================
# Test Model Lineage
# ==============================================================================


def test_get_model_lineage(registry):
    """Test retrieving model lineage"""
    registry.register_model(
        model_id="lineage_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
    )
    registry.register_model(
        model_id="lineage_model",
        version="1.1.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        parent_version="1.0.0",
    )
    registry.register_model(
        model_id="lineage_model",
        version="1.2.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        parent_version="1.1.0",
    )

    lineage = registry.get_model_lineage("lineage_model", "1.2.0")

    assert len(lineage) == 3
    assert lineage[0].version == "1.2.0"
    assert lineage[1].version == "1.1.0"
    assert lineage[2].version == "1.0.0"


# ==============================================================================
# Test Registry Statistics
# ==============================================================================


def test_get_registry_stats(registry):
    """Test retrieving registry statistics"""
    registry.register_model(
        model_id="stats_model_1",
        version="1.0.0",
        framework="sklearn",
        algorithm="SVM",
        created_by="user1",
        stage=ModelStage.PRODUCTION,
    )
    registry.register_model(
        model_id="stats_model_2",
        version="1.0.0",
        framework="pytorch",
        algorithm="CNN",
        created_by="user1",
        stage=ModelStage.DEVELOPMENT,
    )
    registry.register_model(
        model_id="stats_model_2",
        version="1.1.0",
        framework="pytorch",
        algorithm="CNN",
        created_by="user1",
        stage=ModelStage.STAGING,
    )

    stats = registry.get_registry_stats()

    assert stats["total_models"] == 2
    assert stats["total_versions"] == 3
    assert stats["by_stage"]["production"] == 1
    assert stats["by_stage"]["development"] == 1
    assert stats["by_stage"]["staging"] == 1
    assert stats["by_framework"]["sklearn"] == 1
    assert stats["by_framework"]["pytorch"] == 2


# ==============================================================================
# Test Model Comparison
# ==============================================================================


def test_compare_models(registry):
    """Test comparing two model versions"""
    registry.register_model(
        model_id="compare_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
        metrics={"accuracy": 0.80, "f1": 0.78},
    )
    registry.register_model(
        model_id="compare_model",
        version="2.0.0",
        framework="sklearn",
        algorithm="GradientBoosting",
        created_by="user2",
        metrics={"accuracy": 0.90, "f1": 0.88},
    )

    comparison = registry.compare_models("compare_model", "1.0.0", "2.0.0")

    assert comparison["model_id"] == "compare_model"
    assert comparison["version1"]["version"] == "1.0.0"
    assert comparison["version2"]["version"] == "2.0.0"
    assert comparison["algorithm_changed"] is True
    assert abs(comparison["metrics_comparison"]["accuracy"]["diff"] - 0.10) < 0.01


def test_compare_models_invalid_version(registry):
    """Test comparing models with invalid version returns error"""
    registry.register_model(
        model_id="invalid_compare",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
    )

    comparison = registry.compare_models("invalid_compare", "1.0.0", "2.0.0")

    assert "error" in comparison


# ==============================================================================
# Test Persistence
# ==============================================================================


def test_registry_persistence(temp_registry_path):
    """Test that registry persists across instances"""
    # Create first instance and register model
    registry1 = ModelRegistry(registry_path=temp_registry_path)
    registry1.register_model(
        model_id="persist_model",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="user1",
    )

    # Create second instance and verify model exists
    registry2 = ModelRegistry(registry_path=temp_registry_path)

    version = registry2.get_model_version("persist_model", "1.0.0")
    assert version is not None
    assert version.version == "1.0.0"
