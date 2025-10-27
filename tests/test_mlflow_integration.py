"""
Tests for MLflow Integration Module

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Comprehensive tests for MLflow experiment tracking, run management, and artifact handling.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import pandas as pd

from mcp_server.mlflow_integration import (
    MLflowExperimentTracker,
    MLflowConfig,
    RunMetadata,
    RunStatus,
    ModelMetadata,
    get_mlflow_tracker,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_tracker():
    """Create a tracker in mock mode for testing"""
    return MLflowExperimentTracker(experiment_name="test_experiment", mock_mode=True)


@pytest.fixture
def temp_artifact_file():
    """Create a temporary file for artifact testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test artifact content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ==============================================================================
# Test MLflowExperimentTracker Initialization
# ==============================================================================


def test_tracker_initialization_mock_mode():
    """Test tracker initialization in mock mode"""
    tracker = MLflowExperimentTracker(experiment_name="test_exp", mock_mode=True)

    assert tracker.config.experiment_name == "test_exp"
    assert tracker.config.mock_mode is True
    assert tracker.experiment_id is not None
    assert tracker.active_run_id is None


def test_tracker_initialization_default_config():
    """Test tracker initialization with default configuration"""
    tracker = MLflowExperimentTracker(mock_mode=True)

    assert tracker.config.experiment_name == "nba_model_training"
    assert tracker.experiment_id is not None


def test_get_mlflow_tracker_utility():
    """Test the get_mlflow_tracker utility function"""
    tracker = get_mlflow_tracker(experiment_name="utility_test", mock_mode=True)

    assert isinstance(tracker, MLflowExperimentTracker)
    assert tracker.config.experiment_name == "utility_test"


# ==============================================================================
# Test Run Management
# ==============================================================================


def test_start_and_end_run(mock_tracker):
    """Test starting and ending a run"""
    with mock_tracker.start_run("test_run") as run_id:
        assert run_id is not None
        assert mock_tracker.active_run_id == run_id

    # After context manager, run should be ended
    assert mock_tracker.active_run_id is None


def test_start_run_with_tags(mock_tracker):
    """Test starting a run with custom tags"""
    tags = {"team": "data_science", "project": "nba_predictor"}

    with mock_tracker.start_run("tagged_run", tags=tags) as run_id:
        run_metadata = mock_tracker.get_run(run_id)
        assert "team" in run_metadata.tags
        assert run_metadata.tags["team"] == "data_science"


def test_multiple_sequential_runs(mock_tracker):
    """Test running multiple sequential runs"""
    run_ids = []

    for i in range(3):
        with mock_tracker.start_run(f"run_{i}") as run_id:
            run_ids.append(run_id)
            mock_tracker.log_param("iteration", i)

    # All runs should be different
    assert len(set(run_ids)) == 3

    # All runs should be ended
    assert mock_tracker.active_run_id is None


def test_run_failure_handling(mock_tracker):
    """Test that run is marked as failed on exception"""
    try:
        with mock_tracker.start_run("failing_run") as run_id:
            mock_tracker.log_param("test", "value")
            raise ValueError("Intentional failure")
    except ValueError:
        pass

    # Run should be marked as failed
    run = mock_tracker.get_run(run_id)
    assert run.status == RunStatus.FAILED


# ==============================================================================
# Test Parameter Logging
# ==============================================================================


def test_log_single_param(mock_tracker):
    """Test logging a single parameter"""
    with mock_tracker.start_run("param_test") as run_id:
        mock_tracker.log_param("learning_rate", 0.01)

        run = mock_tracker.get_run(run_id)
        assert "learning_rate" in run.params
        assert run.params["learning_rate"] == "0.01"


def test_log_multiple_params(mock_tracker):
    """Test logging multiple parameters at once"""
    params = {
        "learning_rate": 0.01,
        "batch_size": 32,
        "epochs": 10,
        "optimizer": "adam",
    }

    with mock_tracker.start_run("multi_param_test") as run_id:
        mock_tracker.log_params(params)

        run = mock_tracker.get_run(run_id)
        assert len(run.params) == 4
        assert run.params["batch_size"] == "32"
        assert run.params["optimizer"] == "adam"


def test_log_param_without_active_run(mock_tracker):
    """Test that logging param without active run raises error"""
    with pytest.raises(ValueError, match="No active run"):
        mock_tracker.log_param("test", "value")


def test_log_param_various_types(mock_tracker):
    """Test logging parameters of various types"""
    with mock_tracker.start_run("type_test") as run_id:
        mock_tracker.log_param("int_param", 42)
        mock_tracker.log_param("float_param", 3.14)
        mock_tracker.log_param("str_param", "hello")
        mock_tracker.log_param("bool_param", True)

        run = mock_tracker.get_run(run_id)
        assert run.params["int_param"] == "42"
        assert run.params["float_param"] == "3.14"
        assert run.params["str_param"] == "hello"
        assert run.params["bool_param"] == "True"


# ==============================================================================
# Test Metric Logging
# ==============================================================================


def test_log_single_metric(mock_tracker):
    """Test logging a single metric"""
    with mock_tracker.start_run("metric_test") as run_id:
        mock_tracker.log_metric("accuracy", 0.95)

        run = mock_tracker.get_run(run_id)
        assert "accuracy" in run.metrics


def test_log_metric_with_steps(mock_tracker):
    """Test logging metrics with step numbers"""
    with mock_tracker.start_run("step_test") as run_id:
        for step in range(5):
            mock_tracker.log_metric("train_loss", 1.0 / (step + 1), step=step)

        run = mock_tracker.get_run(run_id)
        # In mock mode, metrics with steps are stored with step suffix
        assert len(run.metrics) == 5


def test_log_multiple_metrics(mock_tracker):
    """Test logging multiple metrics at once"""
    metrics = {
        "train_accuracy": 0.95,
        "val_accuracy": 0.92,
        "train_loss": 0.05,
        "val_loss": 0.08,
    }

    with mock_tracker.start_run("multi_metric_test") as run_id:
        mock_tracker.log_metrics(metrics)

        run = mock_tracker.get_run(run_id)
        assert len(run.metrics) == 4


def test_log_metric_without_active_run(mock_tracker):
    """Test that logging metric without active run raises error"""
    with pytest.raises(ValueError, match="No active run"):
        mock_tracker.log_metric("test", 0.5)


# ==============================================================================
# Test Artifact Logging
# ==============================================================================


def test_log_artifact(mock_tracker, temp_artifact_file):
    """Test logging an artifact file"""
    with mock_tracker.start_run("artifact_test") as run_id:
        mock_tracker.log_artifact(temp_artifact_file)

        run = mock_tracker.get_run(run_id)
        assert len(run.artifacts) == 1
        assert temp_artifact_file in run.artifacts


def test_log_artifact_nonexistent_file(mock_tracker):
    """Test that logging nonexistent artifact raises error"""
    with mock_tracker.start_run("missing_artifact_test"):
        with pytest.raises(FileNotFoundError):
            mock_tracker.log_artifact("/nonexistent/path/file.txt")


def test_log_artifact_without_active_run(mock_tracker, temp_artifact_file):
    """Test that logging artifact without active run raises error"""
    with pytest.raises(ValueError, match="No active run"):
        mock_tracker.log_artifact(temp_artifact_file)


# ==============================================================================
# Test Run Retrieval and Search
# ==============================================================================


def test_get_run(mock_tracker):
    """Test retrieving a run by ID"""
    with mock_tracker.start_run("retrieve_test") as run_id:
        mock_tracker.log_param("test_param", "test_value")
        mock_tracker.log_metric("test_metric", 0.99)

    run = mock_tracker.get_run(run_id)
    assert run is not None
    assert run.run_id == run_id
    assert run.run_name == "retrieve_test"
    assert run.status == RunStatus.FINISHED
    assert "test_param" in run.params
    assert "test_metric" in run.metrics


def test_get_nonexistent_run(mock_tracker):
    """Test retrieving a nonexistent run returns None"""
    run = mock_tracker.get_run("nonexistent_run_id")
    assert run is None


def test_search_runs_empty(mock_tracker):
    """Test searching runs when none exist"""
    runs = mock_tracker.search_runs()
    assert isinstance(runs, list)


def test_search_runs_multiple(mock_tracker):
    """Test searching returns multiple runs"""
    # Create several runs
    for i in range(3):
        with mock_tracker.start_run(f"search_test_{i}") as run_id:
            mock_tracker.log_param("iteration", i)
            mock_tracker.log_metric("score", i * 0.1)

    # Search for runs
    runs = mock_tracker.search_runs()
    assert len(runs) >= 3


def test_search_runs_with_max_results(mock_tracker):
    """Test search with max_results limit"""
    # Create several runs
    for i in range(5):
        with mock_tracker.start_run(f"limit_test_{i}"):
            pass

    # Search with limit
    runs = mock_tracker.search_runs(max_results=2)
    assert len(runs) <= 2


# ==============================================================================
# Test Run Comparison
# ==============================================================================


def test_compare_runs(mock_tracker):
    """Test comparing multiple runs"""
    run_ids = []

    # Create runs with different params and metrics
    for i in range(3):
        with mock_tracker.start_run(f"compare_run_{i}") as run_id:
            run_ids.append(run_id)
            mock_tracker.log_param("model", f"model_{i}")
            mock_tracker.log_metric("accuracy", 0.8 + i * 0.05)

    # Compare runs
    comparison_df = mock_tracker.compare_runs(run_ids)

    assert isinstance(comparison_df, pd.DataFrame)
    assert len(comparison_df) == 3
    assert "run_id" in comparison_df.columns
    assert "run_name" in comparison_df.columns
    assert "status" in comparison_df.columns


def test_compare_runs_empty_list(mock_tracker):
    """Test comparing empty list of runs"""
    comparison_df = mock_tracker.compare_runs([])
    assert isinstance(comparison_df, pd.DataFrame)
    assert len(comparison_df) == 0


# ==============================================================================
# Test RunMetadata
# ==============================================================================


def test_run_metadata_duration():
    """Test RunMetadata duration calculation"""
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = datetime(2025, 1, 1, 10, 5, 30)

    metadata = RunMetadata(
        run_id="test_run",
        experiment_id="test_exp",
        run_name="duration_test",
        start_time=start,
        end_time=end,
        status=RunStatus.FINISHED,
    )

    assert metadata.duration_seconds == 330.0  # 5 minutes 30 seconds


def test_run_metadata_duration_no_end_time():
    """Test RunMetadata duration when run is still running"""
    metadata = RunMetadata(
        run_id="test_run",
        experiment_id="test_exp",
        run_name="running_test",
        start_time=datetime.utcnow(),
        status=RunStatus.RUNNING,
    )

    assert metadata.duration_seconds is None


# ==============================================================================
# Test Error Cases
# ==============================================================================


def test_end_run_without_active_run(mock_tracker):
    """Test ending run when no run is active"""
    # Should not raise error, just log warning
    mock_tracker.end_run()
    assert mock_tracker.active_run_id is None


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_full_training_workflow(mock_tracker):
    """Test a complete training workflow"""
    # Start experiment
    with mock_tracker.start_run("full_workflow_test") as run_id:
        # Log hyperparameters
        mock_tracker.log_params(
            {
                "learning_rate": 0.001,
                "batch_size": 64,
                "epochs": 20,
                "optimizer": "adam",
                "model_type": "random_forest",
            }
        )

        # Simulate training loop
        for epoch in range(20):
            train_loss = 1.0 / (epoch + 1)
            val_loss = 1.1 / (epoch + 1)
            train_acc = min(0.99, 0.5 + epoch * 0.025)
            val_acc = min(0.95, 0.45 + epoch * 0.025)

            mock_tracker.log_metric("train_loss", train_loss, step=epoch)
            mock_tracker.log_metric("val_loss", val_loss, step=epoch)
            mock_tracker.log_metric("train_accuracy", train_acc, step=epoch)
            mock_tracker.log_metric("val_accuracy", val_acc, step=epoch)

        # Log final metrics
        mock_tracker.log_metrics({"final_train_acc": 0.99, "final_val_acc": 0.95})

    # Verify run was logged correctly
    run = mock_tracker.get_run(run_id)
    assert run.status == RunStatus.FINISHED
    assert len(run.params) == 5
    assert len(run.metrics) > 0


def test_multiple_experiments_workflow(mock_tracker):
    """Test running multiple experiments with different configurations"""
    configurations = [
        {"lr": 0.001, "bs": 32, "opt": "adam"},
        {"lr": 0.01, "bs": 64, "opt": "sgd"},
        {"lr": 0.0001, "bs": 128, "opt": "rmsprop"},
    ]

    run_ids = []
    for i, config in enumerate(configurations):
        with mock_tracker.start_run(f"experiment_{i}") as run_id:
            run_ids.append(run_id)
            mock_tracker.log_params(config)
            # Simulate different performance based on config
            accuracy = 0.8 + (i * 0.05)
            mock_tracker.log_metric("accuracy", accuracy)

    # Compare all experiments
    comparison = mock_tracker.compare_runs(run_ids)
    assert len(comparison) == 3
    assert all(f"param_{k}" in comparison.columns for k in ["lr", "bs", "opt"])
