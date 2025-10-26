"""
Tests for Training Pipeline Module

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Comprehensive tests for training pipeline orchestration, MLflow integration,
and stage execution.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from mcp_server.training_pipeline import (
    TrainingPipeline,
    PipelineStage,
    PipelineStatus,
    TrainingPipelineRun,
    PipelineStageResult,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_mlflow_tracker():
    """Create a mock MLflow tracker"""
    tracker = MagicMock()
    tracker.start_run = MagicMock()
    tracker.start_run.return_value.__enter__ = MagicMock(return_value="run_123")
    tracker.start_run.return_value.__exit__ = MagicMock(return_value=False)
    tracker.log_params = MagicMock()
    tracker.log_metric = MagicMock()
    tracker.end_run = MagicMock()
    return tracker


@pytest.fixture
def simple_stage_fn():
    """Simple stage function that returns success"""

    def stage_fn(input_data, config):
        return {
            "status": "success",
            "output": "processed_data",
            "metrics": {"processing_time": 1.5, "rows_processed": 100},
        }

    return stage_fn


@pytest.fixture
def failing_stage_fn():
    """Stage function that raises an exception"""

    def stage_fn(input_data, config):
        raise ValueError("Stage execution failed")

    return stage_fn


# ==============================================================================
# Test TrainingPipeline Initialization
# ==============================================================================


def test_pipeline_initialization_basic():
    """Test basic pipeline initialization"""
    pipeline = TrainingPipeline(name="test_pipeline")

    assert pipeline.name == "test_pipeline"
    assert pipeline.config == {}
    assert pipeline.stages == {}
    assert pipeline.runs == []
    assert pipeline.enable_mlflow is False


def test_pipeline_initialization_with_config():
    """Test pipeline initialization with configuration"""
    config = {"param1": "value1", "param2": 42}
    pipeline = TrainingPipeline(name="test_pipeline", config=config)

    assert pipeline.config == config


def test_pipeline_initialization_with_mlflow(mock_mlflow_tracker):
    """Test pipeline initialization with MLflow tracker"""
    pipeline = TrainingPipeline(
        name="test_pipeline",
        mlflow_tracker=mock_mlflow_tracker,
        enable_mlflow=True,
    )

    assert pipeline.mlflow_tracker is mock_mlflow_tracker
    assert pipeline.enable_mlflow is True


def test_pipeline_initialization_mlflow_without_tracker():
    """Test that MLflow is disabled if no tracker provided"""
    pipeline = TrainingPipeline(name="test_pipeline", enable_mlflow=True)

    # Should be disabled because no tracker was provided
    assert pipeline.enable_mlflow is False


# ==============================================================================
# Test Stage Management
# ==============================================================================


def test_add_stage(simple_stage_fn):
    """Test adding a stage to the pipeline"""
    pipeline = TrainingPipeline(name="test_pipeline")

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    assert PipelineStage.DATA_VALIDATION in pipeline.stages
    assert pipeline.stages[PipelineStage.DATA_VALIDATION] == simple_stage_fn


def test_add_multiple_stages(simple_stage_fn):
    """Test adding multiple stages"""
    pipeline = TrainingPipeline(name="test_pipeline")

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)
    pipeline.add_stage(PipelineStage.DATA_PREPARATION, simple_stage_fn)
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, simple_stage_fn)

    assert len(pipeline.stages) == 3


# ==============================================================================
# Test Pipeline Execution
# ==============================================================================


def test_execute_pipeline_basic(simple_stage_fn):
    """Test basic pipeline execution"""
    pipeline = TrainingPipeline(name="test_pipeline")

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, simple_stage_fn)

    run = pipeline.execute()

    assert run.status == PipelineStatus.SUCCESS
    assert len(run.stage_results) == 2
    assert run.end_time is not None
    assert run.run_id is not None


def test_execute_pipeline_with_run_id(simple_stage_fn):
    """Test pipeline execution with custom run ID"""
    pipeline = TrainingPipeline(name="test_pipeline")

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    run = pipeline.execute(run_id="custom_run_123")

    assert run.run_id == "custom_run_123"


def test_execute_pipeline_with_mlflow(mock_mlflow_tracker, simple_stage_fn):
    """Test pipeline execution with MLflow tracking"""
    pipeline = TrainingPipeline(
        name="test_pipeline",
        config={"param1": "value1"},
        mlflow_tracker=mock_mlflow_tracker,
        enable_mlflow=True,
    )

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    run = pipeline.execute()

    # Verify MLflow was used
    assert mock_mlflow_tracker.start_run.called
    assert mock_mlflow_tracker.log_params.called
    assert mock_mlflow_tracker.log_metric.called
    assert mock_mlflow_tracker.end_run.called


def test_execute_pipeline_stage_failure(simple_stage_fn, failing_stage_fn):
    """Test pipeline execution with stage failure"""
    pipeline = TrainingPipeline(name="test_pipeline")

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, failing_stage_fn)  # This will fail
    pipeline.add_stage(
        PipelineStage.MODEL_EVALUATION, simple_stage_fn
    )  # Should not execute

    run = pipeline.execute()

    assert run.status == PipelineStatus.FAILED
    # Only first two stages should have results (second one failed)
    assert len(run.stage_results) == 2
    assert run.stage_results[0].status == PipelineStatus.SUCCESS
    assert run.stage_results[1].status == PipelineStatus.FAILED


def test_execute_pipeline_empty():
    """Test executing pipeline with no stages"""
    pipeline = TrainingPipeline(name="test_pipeline")

    run = pipeline.execute()

    assert run.status == PipelineStatus.SUCCESS
    assert len(run.stage_results) == 0


def test_execute_pipeline_stage_order(simple_stage_fn):
    """Test that stages execute in correct order"""
    call_order = []

    def tracking_stage_fn(input_data, config):
        call_order.append(config.get("stage_name", "unknown"))
        return {"status": "success", "metrics": {}}

    pipeline = TrainingPipeline(name="test_pipeline")

    # Add stages in mixed order
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, tracking_stage_fn)
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, tracking_stage_fn)
    pipeline.add_stage(PipelineStage.DATA_PREPARATION, tracking_stage_fn)

    # Update config for each stage
    pipeline.config = {}

    run = pipeline.execute()

    # Stages should execute in predefined order, not insertion order
    assert len(run.stage_results) == 3
    assert run.stage_results[0].stage == PipelineStage.DATA_VALIDATION
    assert run.stage_results[1].stage == PipelineStage.DATA_PREPARATION
    assert run.stage_results[2].stage == PipelineStage.MODEL_TRAINING


# ==============================================================================
# Test Stage Execution
# ==============================================================================


def test_stage_execution_success(simple_stage_fn):
    """Test successful stage execution"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    run = pipeline.execute()

    stage_result = run.stage_results[0]
    assert stage_result.status == PipelineStatus.SUCCESS
    assert stage_result.duration_seconds is not None
    assert stage_result.metrics == {"processing_time": 1.5, "rows_processed": 100}


def test_stage_execution_failure(failing_stage_fn):
    """Test failed stage execution"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, failing_stage_fn)

    run = pipeline.execute()

    stage_result = run.stage_results[0]
    assert stage_result.status == PipelineStatus.FAILED
    assert stage_result.error is not None
    assert "Stage execution failed" in stage_result.error


# ==============================================================================
# Test Run History
# ==============================================================================


def test_get_run_history(simple_stage_fn):
    """Test retrieving run history"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    # Execute multiple runs
    run1 = pipeline.execute(run_id="run_1")
    run2 = pipeline.execute(run_id="run_2")
    run3 = pipeline.execute(run_id="run_3")

    history = pipeline.get_run_history()

    assert len(history) == 3
    # Should be in reverse chronological order
    assert history[0]["run_id"] == "run_3"
    assert history[1]["run_id"] == "run_2"
    assert history[2]["run_id"] == "run_1"


def test_get_run_history_with_limit(simple_stage_fn):
    """Test run history with limit"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    # Execute 5 runs
    for i in range(5):
        pipeline.execute(run_id=f"run_{i}")

    history = pipeline.get_run_history(limit=2)

    assert len(history) == 2


def test_get_run_history_empty():
    """Test run history when no runs exist"""
    pipeline = TrainingPipeline(name="test_pipeline")

    history = pipeline.get_run_history()

    assert history == []


# ==============================================================================
# Test Run Comparison
# ==============================================================================


def test_compare_runs(simple_stage_fn):
    """Test comparing multiple runs"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    run1 = pipeline.execute(run_id="run_1")
    run2 = pipeline.execute(run_id="run_2")

    comparison = pipeline.compare_runs(["run_1", "run_2"])

    assert "runs" in comparison
    assert len(comparison["runs"]) == 2
    assert comparison["runs"][0]["run_id"] in ["run_1", "run_2"]
    assert comparison["runs"][1]["run_id"] in ["run_1", "run_2"]


def test_compare_runs_nonexistent():
    """Test comparing runs that don't exist"""
    pipeline = TrainingPipeline(name="test_pipeline")

    comparison = pipeline.compare_runs(["nonexistent_1", "nonexistent_2"])

    assert "error" in comparison


# ==============================================================================
# Test Run Metadata Saving
# ==============================================================================


def test_save_run_metadata(simple_stage_fn, tmp_path):
    """Test that run metadata is saved to disk"""
    # Create pipeline with temporary artifacts path
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.artifacts_path = tmp_path
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    run = pipeline.execute(run_id="test_run")

    # Check metadata file was created
    metadata_file = tmp_path / "test_run_metadata.json"
    assert metadata_file.exists()


# ==============================================================================
# Test Clear Run History
# ==============================================================================


def test_clear_run_history(simple_stage_fn):
    """Test clearing run history"""
    pipeline = TrainingPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, simple_stage_fn)

    # Execute some runs
    pipeline.execute()
    pipeline.execute()

    assert len(pipeline.runs) == 2

    # Clear history
    pipeline.clear_run_history()

    assert len(pipeline.runs) == 0


# ==============================================================================
# Test Integration
# ==============================================================================


def test_full_pipeline_workflow(mock_mlflow_tracker):
    """Test complete pipeline workflow with all stages"""

    def validation_fn(input_data, config):
        return {"status": "valid", "metrics": {"validation_score": 0.95}}

    def preparation_fn(input_data, config):
        return {"train_data": "data", "metrics": {"train_size": 800}}

    def training_fn(input_data, config):
        return {"model": "trained_model", "metrics": {"accuracy": 0.92}}

    def evaluation_fn(input_data, config):
        return {"metrics": {"test_accuracy": 0.90, "f1_score": 0.88}}

    pipeline = TrainingPipeline(
        name="full_pipeline",
        config={"model_type": "random_forest"},
        mlflow_tracker=mock_mlflow_tracker,
        enable_mlflow=True,
    )

    pipeline.add_stage(PipelineStage.DATA_VALIDATION, validation_fn)
    pipeline.add_stage(PipelineStage.DATA_PREPARATION, preparation_fn)
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, training_fn)
    pipeline.add_stage(PipelineStage.MODEL_EVALUATION, evaluation_fn)

    run = pipeline.execute()

    # Verify pipeline completed successfully
    assert run.status == PipelineStatus.SUCCESS
    assert len(run.stage_results) == 4

    # Verify all stages succeeded
    for stage_result in run.stage_results:
        assert stage_result.status == PipelineStatus.SUCCESS

    # Verify MLflow integration
    assert mock_mlflow_tracker.start_run.called
    assert mock_mlflow_tracker.end_run.called
    # Multiple metrics logged
    assert mock_mlflow_tracker.log_metric.call_count > 0
