"""
Training Pipeline Automation Module

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Enhanced with MLflow integration, Week 1 patterns, and Agent 4 data validation integration.

Features:
- Multi-stage training pipeline orchestration
- MLflow experiment tracking integration
- Agent 4 data validation integration
- Week 1 integration (error handling, monitoring, RBAC)
- Automatic artifact management
- Pipeline run history and comparison
- Comprehensive metrics logging

Author: NBA MCP Server Team - Phase 10A Agent 5
Date: 2025-10-25
"""

import logging
from typing import Dict, Optional, Any, Callable, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext, DataValidationError
    from mcp_server.monitoring import get_health_monitor, track_metric
    from mcp_server.rbac import require_permission, Permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    # Fallback decorators for standalone usage
    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def track_metric(metric_name):
        from contextlib import contextmanager

        @contextmanager
        def dummy_context():
            yield

        return dummy_context()

    def require_permission(permission):
        def decorator(func):
            return func

        return decorator

    class Permission:
        READ = "read"
        WRITE = "write"
        ADMIN = "admin"


# MLflow Integration (optional)
try:
    from mcp_server.mlflow_integration import MLflowExperimentTracker

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    MLflowExperimentTracker = None

# Agent 4 Data Validation Integration (optional)
try:
    from mcp_server.data_validation_pipeline import DataValidationPipeline

    DATA_VALIDATION_AVAILABLE = True
except ImportError:
    DATA_VALIDATION_AVAILABLE = False
    DataValidationPipeline = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Training pipeline stages"""

    DATA_VALIDATION = "data_validation"
    DATA_PREPARATION = "data_preparation"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_REGISTRATION = "model_registration"
    MODEL_DEPLOYMENT = "model_deployment"


class PipelineStatus(Enum):
    """Pipeline execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineStageResult:
    """Result from a pipeline stage"""

    stage: PipelineStage
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingPipelineRun:
    """Training pipeline execution run"""

    run_id: str
    pipeline_name: str
    start_time: datetime
    status: PipelineStatus = PipelineStatus.PENDING
    end_time: Optional[datetime] = None
    stage_results: List[PipelineStageResult] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)


class TrainingPipeline:
    """
    Automated ML training pipeline with MLflow and Week 1 integration.

    Orchestrates end-to-end model training with experiment tracking, data validation,
    and comprehensive monitoring.

    Examples:
        >>> pipeline = TrainingPipeline(
        ...     name="nba_player_performance",
        ...     mlflow_tracker=tracker,
        ...     enable_validation=True
        ... )
        >>> pipeline.add_stage(PipelineStage.DATA_VALIDATION, validate_fn)
        >>> pipeline.add_stage(PipelineStage.MODEL_TRAINING, train_fn)
        >>> run = pipeline.execute()
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict] = None,
        mlflow_tracker: Optional[Any] = None,
        enable_mlflow: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize training pipeline.

        Args:
            name: Pipeline name
            config: Pipeline configuration
            mlflow_tracker: Optional MLflow tracker for experiment logging
            enable_mlflow: Whether to enable MLflow integration
            enable_validation: Whether to enable data validation
        """
        self.name = name
        self.config = config or {}
        self.stages: Dict[PipelineStage, Callable] = {}
        self.runs: List[TrainingPipelineRun] = []

        # MLflow integration
        self.mlflow_tracker = mlflow_tracker
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE
        self.enable_validation = enable_validation and DATA_VALIDATION_AVAILABLE

        if self.enable_mlflow and not self.mlflow_tracker:
            logger.warning("MLflow enabled but no tracker provided")
            self.enable_mlflow = False

        # Storage path for pipeline artifacts
        self.artifacts_path = Path(f"./pipeline_artifacts/{name}")
        self.artifacts_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized training pipeline '{name}' "
            f"(MLflow: {self.enable_mlflow}, Validation: {self.enable_validation})"
        )

    def add_stage(self, stage: PipelineStage, func: Callable):
        """
        Add a stage to the pipeline.

        Args:
            stage: Pipeline stage
            func: Function to execute for this stage
        """
        self.stages[stage] = func
        logger.info(f"Added stage {stage.value} to pipeline {self.name}")

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    def execute(self, run_id: Optional[str] = None) -> TrainingPipelineRun:
        """
        Execute the training pipeline with MLflow tracking.

        Args:
            run_id: Optional run identifier

        Returns:
            TrainingPipelineRun object with results

        Raises:
            DataValidationError: If data validation fails
            Exception: If pipeline execution fails
        """
        with track_metric("pipeline.execution"):
            if not run_id:
                run_id = f"{self.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            run = TrainingPipelineRun(
                run_id=run_id,
                pipeline_name=self.name,
                start_time=datetime.utcnow(),
                status=PipelineStatus.RUNNING,
                config=self.config.copy(),
            )

            logger.info(f"🚀 Starting pipeline run: {run_id}")

            # Start MLflow run if enabled
            mlflow_run_id = None
            if self.enable_mlflow and self.mlflow_tracker:
                mlflow_run_id = self.mlflow_tracker.start_run(
                    run_name=run_id, tags={"pipeline": self.name, "stage": "full_pipeline"}
                ).__enter__()
                self.mlflow_tracker.log_params(self.config)
                logger.info(f"📊 Started MLflow run: {mlflow_run_id}")

            try:
                # Execute stages in order
                stage_order = [
                    PipelineStage.DATA_VALIDATION,
                    PipelineStage.DATA_PREPARATION,
                    PipelineStage.FEATURE_ENGINEERING,
                    PipelineStage.MODEL_TRAINING,
                    PipelineStage.MODEL_EVALUATION,
                    PipelineStage.MODEL_REGISTRATION,
                    PipelineStage.MODEL_DEPLOYMENT,
                ]

                previous_output = None

                for stage in stage_order:
                    if stage not in self.stages:
                        logger.debug(f"⏭️  Skipping stage {stage.value} (not configured)")
                        continue

                    stage_result = self._execute_stage(
                        stage, self.stages[stage], previous_output, run
                    )

                    run.stage_results.append(stage_result)

                    # Log stage metrics to MLflow
                    if self.enable_mlflow and self.mlflow_tracker:
                        for metric_name, metric_value in stage_result.metrics.items():
                            self.mlflow_tracker.log_metric(
                                f"{stage.value}.{metric_name}", metric_value
                            )
                        self.mlflow_tracker.log_metric(
                            f"{stage.value}.duration_seconds",
                            stage_result.duration_seconds or 0,
                        )

                    if stage_result.status == PipelineStatus.FAILED:
                        run.status = PipelineStatus.FAILED
                        logger.error(f"❌ Pipeline {run_id} failed at stage {stage.value}")
                        break

                    previous_output = stage_result.output

                # Finalize run
                if run.status != PipelineStatus.FAILED:
                    run.status = PipelineStatus.SUCCESS

                run.end_time = datetime.utcnow()
                duration = (run.end_time - run.start_time).total_seconds()

                # Log final metrics to MLflow
                if self.enable_mlflow and self.mlflow_tracker:
                    self.mlflow_tracker.log_metric("pipeline.duration_seconds", duration)
                    self.mlflow_tracker.log_metric(
                        "pipeline.stages_completed",
                        len([r for r in run.stage_results if r.status == PipelineStatus.SUCCESS]),
                    )
                    self.mlflow_tracker.log_metric(
                        "pipeline.success", 1.0 if run.status == PipelineStatus.SUCCESS else 0.0
                    )

            except Exception as e:
                run.status = PipelineStatus.FAILED
                run.end_time = datetime.utcnow()
                logger.error(f"❌ Pipeline execution failed: {e}")
                raise

            finally:
                # End MLflow run
                if self.enable_mlflow and self.mlflow_tracker and mlflow_run_id:
                    self.mlflow_tracker.end_run(
                        status="FINISHED" if run.status == PipelineStatus.SUCCESS else "FAILED"
                    )
                    logger.info(f"📊 Ended MLflow run: {mlflow_run_id}")

                self.runs.append(run)

                # Save run metadata
                self._save_run_metadata(run)

                status_icon = "✅" if run.status == PipelineStatus.SUCCESS else "❌"
                logger.info(
                    f"{status_icon} Pipeline run {run_id} completed with status {run.status.value} "
                    f"in {(run.end_time - run.start_time).total_seconds():.2f}s"
                )

            return run

    @handle_errors(reraise=True, notify=False)
    def _execute_stage(
        self,
        stage: PipelineStage,
        func: Callable,
        input_data: Any,
        run: TrainingPipelineRun,
    ) -> PipelineStageResult:
        """Execute a single pipeline stage with monitoring"""
        with track_metric(f"pipeline.stage.{stage.value}"):
            stage_result = PipelineStageResult(
                stage=stage, status=PipelineStatus.RUNNING, start_time=datetime.utcnow()
            )

            logger.info(f"⚙️  Executing stage: {stage.value}")

            try:
                # Execute stage function
                output = func(input_data, self.config)

                stage_result.status = PipelineStatus.SUCCESS
                stage_result.output = output

                # Extract metrics if available
                if isinstance(output, dict) and "metrics" in output:
                    stage_result.metrics = output["metrics"]

                logger.info(f"✅ Stage {stage.value} completed successfully")

            except Exception as e:
                stage_result.status = PipelineStatus.FAILED
                stage_result.error = str(e)
                logger.error(f"❌ Stage {stage.value} failed: {e}")

            finally:
                stage_result.end_time = datetime.utcnow()
                stage_result.duration_seconds = (
                    stage_result.end_time - stage_result.start_time
                ).total_seconds()

            return stage_result

    def _save_run_metadata(self, run: TrainingPipelineRun):
        """Save run metadata to disk"""
        metadata_file = self.artifacts_path / f"{run.run_id}_metadata.json"

        metadata = {
            "run_id": run.run_id,
            "pipeline_name": run.pipeline_name,
            "start_time": run.start_time.isoformat(),
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "status": run.status.value,
            "config": run.config,
            "stages": [
                {
                    "stage": result.stage.value,
                    "status": result.status.value,
                    "duration_seconds": result.duration_seconds,
                    "metrics": result.metrics,
                    "error": result.error,
                }
                for result in run.stage_results
            ],
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved run metadata to {metadata_file}")

    @require_permission(Permission.READ)
    def get_run_history(self, limit: int = 10) -> List[Dict]:
        """
        Get pipeline run history.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summary dictionaries
        """
        return [
            {
                "run_id": run.run_id,
                "status": run.status.value,
                "start_time": run.start_time.isoformat(),
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "duration_seconds": (
                    (run.end_time - run.start_time).total_seconds()
                    if run.end_time
                    else None
                ),
                "stages_completed": len(
                    [r for r in run.stage_results if r.status == PipelineStatus.SUCCESS]
                ),
                "total_stages": len(run.stage_results),
            }
            for run in sorted(self.runs, key=lambda r: r.start_time, reverse=True)[
                :limit
            ]
        ]

    @require_permission(Permission.READ)
    def compare_runs(self, run_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple pipeline runs.

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Comparison dictionary with metrics and stage results
        """
        runs = [r for r in self.runs if r.run_id in run_ids]

        if not runs:
            return {"error": "No runs found with provided IDs"}

        comparison = {
            "runs": [],
            "metrics_comparison": {},
            "stage_comparison": {},
        }

        for run in runs:
            run_summary = {
                "run_id": run.run_id,
                "status": run.status.value,
                "duration_seconds": (
                    (run.end_time - run.start_time).total_seconds()
                    if run.end_time and run.start_time
                    else None
                ),
                "stages": {},
            }

            for stage_result in run.stage_results:
                run_summary["stages"][stage_result.stage.value] = {
                    "status": stage_result.status.value,
                    "duration_seconds": stage_result.duration_seconds,
                    "metrics": stage_result.metrics,
                }

            comparison["runs"].append(run_summary)

        return comparison

    @require_permission(Permission.ADMIN)
    def clear_run_history(self):
        """Clear all pipeline run history."""
        self.runs = []
        logger.info(f"Cleared run history for pipeline {self.name}")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("TRAINING PIPELINE AUTOMATION DEMO")
    print("=" * 80)

    # Define stage functions
    def validate_data(input_data, config):
        print(
            f"  → Validating data with config: {config.get('validation_rules', 'default')}"
        )
        return {"status": "valid", "rows": 1000, "metrics": {"null_count": 5}}

    def prepare_data(input_data, config):
        print(f"  → Preparing data (train/test split: {config.get('test_size', 0.2)})")
        return {
            "train": {"rows": 800},
            "test": {"rows": 200},
            "metrics": {"train_size": 800, "test_size": 200},
        }

    def engineer_features(input_data, config):
        print(
            f"  → Engineering features (strategy: {config.get('feature_strategy', 'auto')})"
        )
        return {
            "features": ["points", "assists", "rebounds", "per"],
            "metrics": {"feature_count": 4},
        }

    def train_model(input_data, config):
        print(
            f"  → Training model (algorithm: {config.get('algorithm', 'random_forest')})"
        )
        return {
            "model_id": "model_v1",
            "metrics": {"accuracy": 0.92, "training_time": 45.3},
        }

    def evaluate_model(input_data, config):
        print(f"  → Evaluating model (threshold: {config.get('eval_threshold', 0.85)})")
        return {
            "metrics": {"accuracy": 0.92, "precision": 0.89, "recall": 0.91, "f1": 0.90}
        }

    def register_model(input_data, config):
        print("  → Registering model in registry")
        return {"registry_id": "registry_123", "version": "1.0.0"}

    # Create pipeline
    print("\n" + "=" * 80)
    print("CREATING PIPELINE")
    print("=" * 80)

    pipeline = TrainingPipeline(
        name="nba_player_performance",
        config={
            "validation_rules": "strict",
            "test_size": 0.2,
            "feature_strategy": "advanced",
            "algorithm": "gradient_boosting",
            "eval_threshold": 0.85,
        },
    )

    # Add stages
    pipeline.add_stage(PipelineStage.DATA_VALIDATION, validate_data)
    pipeline.add_stage(PipelineStage.DATA_PREPARATION, prepare_data)
    pipeline.add_stage(PipelineStage.FEATURE_ENGINEERING, engineer_features)
    pipeline.add_stage(PipelineStage.MODEL_TRAINING, train_model)
    pipeline.add_stage(PipelineStage.MODEL_EVALUATION, evaluate_model)
    pipeline.add_stage(PipelineStage.MODEL_REGISTRATION, register_model)

    print(f"\n✅ Created pipeline with {len(pipeline.stages)} stages")

    # Execute pipeline
    print("\n" + "=" * 80)
    print("EXECUTING PIPELINE")
    print("=" * 80)

    run = pipeline.execute()

    # Show results
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)

    print(f"\nRun ID: {run.run_id}")
    print(f"Status: {run.status.value}")
    print(f"Duration: {(run.end_time - run.start_time).total_seconds():.2f}s")

    print("\nStage Results:")
    for stage_result in run.stage_results:
        status_icon = "✅" if stage_result.status == PipelineStatus.SUCCESS else "❌"
        print(f"\n  {status_icon} {stage_result.stage.value}")
        print(f"     Duration: {stage_result.duration_seconds:.2f}s")
        if stage_result.metrics:
            print(f"     Metrics: {stage_result.metrics}")

    # Run history
    print("\n" + "=" * 80)
    print("RUN HISTORY")
    print("=" * 80)

    history = pipeline.get_run_history()
    for h in history:
        print(f"\n{h['run_id']}:")
        print(f"  Status: {h['status']}")
        print(f"  Duration: {h['duration_seconds']:.2f}s")
        print(f"  Stages: {h['stages_completed']}")

    print("\n" + "=" * 80)
    print("Training Pipeline Demo Complete!")
    print("=" * 80)
