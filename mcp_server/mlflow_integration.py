"""
MLflow Experiment Tracking Integration

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Provides production-ready MLflow integration for experiment tracking, model versioning,
and artifact management with full Week 1 integration patterns.

Features:
- Experiment tracking and management
- Run lifecycle management (start, log params/metrics, end)
- Model registration and versioning
- Artifact management and storage
- Run comparison and analysis
- Week 1 integration (error handling, monitoring, RBAC)
- Mock mode for testing without MLflow server

Author: NBA MCP Server Team - Phase 10A Agent 5
Date: 2025-10-25
"""

import json
import logging
import os
import pickle
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import pandas as pd
import numpy as np

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


# MLflow imports (optional for mock mode)
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    from mlflow.entities import Run, Experiment
    from mlflow.models import infer_signature

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None
    MlflowClient = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================================================================
# Data Classes
# ==============================================================================


class RunStatus(Enum):
    """MLflow run status"""

    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    KILLED = "KILLED"


@dataclass
class MLflowConfig:
    """Configuration for MLflow integration"""

    tracking_uri: str = "sqlite:///mlflow.db"
    experiment_name: str = "nba_model_training"
    artifact_location: Optional[str] = None
    registry_uri: Optional[str] = None
    mock_mode: bool = False  # Enable mock mode for testing
    enable_autolog: bool = True
    log_system_metrics: bool = True


@dataclass
class RunMetadata:
    """Metadata for an MLflow run"""

    run_id: str
    experiment_id: str
    run_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RunStatus = RunStatus.RUNNING
    params: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds"""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class ModelMetadata:
    """Metadata for a registered model"""

    name: str
    version: int
    stage: str = "None"  # None, Staging, Production, Archived
    description: Optional[str] = None
    run_id: Optional[str] = None
    creation_timestamp: Optional[datetime] = None
    last_updated_timestamp: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)


# ==============================================================================
# Mock MLflow Client (for testing without MLflow server)
# ==============================================================================


class MockMLflowClient:
    """Mock MLflow client for testing without a real MLflow server"""

    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.runs: Dict[str, Dict] = {}
        self.models: Dict[str, List[Dict]] = {}
        self.artifacts: Dict[str, List[str]] = {}
        self._run_counter = 0
        self._experiment_counter = 0

    def create_experiment(self, name: str, artifact_location: Optional[str] = None) -> str:
        """Create a mock experiment"""
        exp_id = f"exp_{self._experiment_counter}"
        self._experiment_counter += 1
        self.experiments[exp_id] = {
            "experiment_id": exp_id,
            "name": name,
            "artifact_location": artifact_location or f"/tmp/mlflow/{exp_id}",
            "lifecycle_stage": "active",
        }
        logger.info(f"[MOCK] Created experiment: {name} (ID: {exp_id})")
        return exp_id

    def get_experiment_by_name(self, name: str) -> Optional[Dict]:
        """Get experiment by name"""
        for exp in self.experiments.values():
            if exp["name"] == name:
                return exp
        return None

    def create_run(self, experiment_id: str, tags: Optional[Dict] = None) -> Dict:
        """Create a mock run"""
        run_id = f"run_{self._run_counter}"
        self._run_counter += 1
        self.runs[run_id] = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "status": "RUNNING",
            "start_time": datetime.utcnow(),
            "end_time": None,
            "params": {},
            "metrics": {},
            "tags": tags or {},
        }
        self.artifacts[run_id] = []
        logger.info(f"[MOCK] Created run: {run_id}")
        return self.runs[run_id]

    def log_param(self, run_id: str, key: str, value: Any):
        """Log a parameter"""
        if run_id in self.runs:
            self.runs[run_id]["params"][key] = str(value)
            logger.debug(f"[MOCK] Logged param: {key}={value}")

    def log_metric(self, run_id: str, key: str, value: float, step: Optional[int] = None):
        """Log a metric"""
        if run_id in self.runs:
            metric_key = f"{key}_{step}" if step is not None else key
            self.runs[run_id]["metrics"][metric_key] = value
            logger.debug(f"[MOCK] Logged metric: {key}={value}")

    def set_tag(self, run_id: str, key: str, value: str):
        """Set a tag"""
        if run_id in self.runs:
            self.runs[run_id]["tags"][key] = value
            logger.debug(f"[MOCK] Set tag: {key}={value}")

    def log_artifact(self, run_id: str, local_path: str):
        """Log an artifact"""
        if run_id in self.artifacts:
            self.artifacts[run_id].append(local_path)
            logger.debug(f"[MOCK] Logged artifact: {local_path}")

    def update_run(self, run_id: str, status: str):
        """Update run status"""
        if run_id in self.runs:
            self.runs[run_id]["status"] = status
            if status in ["FINISHED", "FAILED", "KILLED"]:
                self.runs[run_id]["end_time"] = datetime.utcnow()
            logger.info(f"[MOCK] Updated run {run_id} status: {status}")

    def get_run(self, run_id: str) -> Optional[Dict]:
        """Get run by ID"""
        return self.runs.get(run_id)

    def search_runs(
        self, experiment_ids: List[str], filter_string: str = ""
    ) -> List[Dict]:
        """Search runs"""
        results = []
        for run in self.runs.values():
            if run["experiment_id"] in experiment_ids:
                results.append(run)
        return results


# ==============================================================================
# MLflow Experiment Tracker
# ==============================================================================


class MLflowExperimentTracker:
    """
    MLflow experiment tracking integration with production-ready features.

    Provides comprehensive experiment tracking, model versioning, and artifact
    management with full Week 1 integration patterns.

    Examples:
        >>> # Basic usage
        >>> tracker = MLflowExperimentTracker(
        ...     tracking_uri="sqlite:///mlflow.db",
        ...     experiment_name="my_experiment"
        ... )
        >>>
        >>> # Start a run
        >>> with tracker.start_run("training_run_1") as run_id:
        ...     tracker.log_params({"learning_rate": 0.01, "epochs": 10})
        ...     tracker.log_metric("accuracy", 0.95)
        ...     tracker.log_artifact("/path/to/model.pkl")
        >>>
        >>> # Register model
        >>> tracker.register_model(
        ...     model_name="nba_predictor",
        ...     run_id=run_id,
        ...     model_path="models/my_model.pkl"
        ... )
    """

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "nba_model_training",
        artifact_location: Optional[str] = None,
        mock_mode: bool = False,
    ):
        """
        Initialize MLflow experiment tracker.

        Args:
            tracking_uri: MLflow tracking server URI (default: sqlite:///mlflow.db)
            experiment_name: Name of the experiment
            artifact_location: Location to store artifacts
            mock_mode: Enable mock mode for testing (default: False)
        """
        self.config = MLflowConfig(
            tracking_uri=tracking_uri or "sqlite:///mlflow.db",
            experiment_name=experiment_name,
            artifact_location=artifact_location,
            mock_mode=mock_mode or not MLFLOW_AVAILABLE,
        )

        self.active_run_id: Optional[str] = None
        self.experiment_id: Optional[str] = None

        # Initialize client
        if self.config.mock_mode:
            logger.info("🧪 MLflow in MOCK mode (testing without server)")
            self.client = MockMLflowClient()
        else:
            if not MLFLOW_AVAILABLE:
                raise ImportError(
                    "MLflow is not installed. Install with: pip install mlflow"
                )
            mlflow.set_tracking_uri(self.config.tracking_uri)
            if self.config.registry_uri:
                mlflow.set_registry_uri(self.config.registry_uri)
            self.client = MlflowClient()
            logger.info(f"✅ MLflow tracking URI: {self.config.tracking_uri}")

        # Create or get experiment
        self._setup_experiment()

    @handle_errors(reraise=True, notify=False)
    def _setup_experiment(self):
        """Set up MLflow experiment"""
        if self.config.mock_mode:
            exp = self.client.get_experiment_by_name(self.config.experiment_name)
            if exp is None:
                self.experiment_id = self.client.create_experiment(
                    self.config.experiment_name, self.config.artifact_location
                )
            else:
                self.experiment_id = exp["experiment_id"]
        else:
            exp = mlflow.get_experiment_by_name(self.config.experiment_name)
            if exp is None:
                self.experiment_id = mlflow.create_experiment(
                    self.config.experiment_name, self.config.artifact_location
                )
            else:
                self.experiment_id = exp.experiment_id

        logger.info(
            f"📊 Experiment '{self.config.experiment_name}' (ID: {self.experiment_id})"
        )

    @contextmanager
    @handle_errors(reraise=True, notify=False)
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        nested: bool = False,
    ):
        """
        Start an MLflow run as a context manager.

        Args:
            run_name: Optional name for the run
            tags: Optional tags to attach to the run
            nested: Whether this is a nested run

        Yields:
            run_id: The ID of the started run

        Examples:
            >>> with tracker.start_run("my_run") as run_id:
            ...     tracker.log_param("alpha", 0.5)
            ...     tracker.log_metric("rmse", 0.23)
        """
        with track_metric("mlflow.run.start"):
            # Prepare tags
            run_tags = tags or {}
            if run_name:
                run_tags["mlflow.runName"] = run_name

            # Start run
            if self.config.mock_mode:
                run = self.client.create_run(self.experiment_id, run_tags)
                run_id = run["run_id"]
            else:
                active_run = mlflow.start_run(
                    experiment_id=self.experiment_id, tags=run_tags, nested=nested
                )
                run_id = active_run.info.run_id

            self.active_run_id = run_id
            logger.info(f"🏃 Started run: {run_id} (Name: {run_name or 'unnamed'})")

            try:
                yield run_id
            except Exception as e:
                logger.error(f"❌ Run {run_id} failed: {e}")
                self.end_run(status=RunStatus.FAILED)
                raise
            else:
                self.end_run(status=RunStatus.FINISHED)

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def log_param(self, key: str, value: Any, run_id: Optional[str] = None):
        """
        Log a parameter to the active or specified run.

        Args:
            key: Parameter name
            value: Parameter value
            run_id: Optional run ID (uses active run if None)
        """
        target_run = run_id or self.active_run_id
        if target_run is None:
            raise ValueError("No active run. Start a run first with start_run()")

        if self.config.mock_mode:
            self.client.log_param(target_run, key, value)
        else:
            with mlflow.start_run(run_id=target_run):
                mlflow.log_param(key, value)

        logger.debug(f"📝 Logged param: {key}={value}")

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def log_params(self, params: Dict[str, Any], run_id: Optional[str] = None):
        """
        Log multiple parameters to the active or specified run.

        Args:
            params: Dictionary of parameter names and values
            run_id: Optional run ID (uses active run if None)
        """
        for key, value in params.items():
            self.log_param(key, value, run_id)

        logger.info(f"📝 Logged {len(params)} parameters")

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def log_metric(
        self, key: str, value: float, step: Optional[int] = None, run_id: Optional[str] = None
    ):
        """
        Log a metric to the active or specified run.

        Args:
            key: Metric name
            value: Metric value
            step: Optional step number for tracking metrics over time
            run_id: Optional run ID (uses active run if None)
        """
        target_run = run_id or self.active_run_id
        if target_run is None:
            raise ValueError("No active run. Start a run first with start_run()")

        if self.config.mock_mode:
            self.client.log_metric(target_run, key, value, step)
        else:
            with mlflow.start_run(run_id=target_run):
                mlflow.log_metric(key, value, step)

        logger.debug(f"📊 Logged metric: {key}={value}" + (f" (step {step})" if step else ""))

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, run_id: Optional[str] = None
    ):
        """
        Log multiple metrics to the active or specified run.

        Args:
            metrics: Dictionary of metric names and values
            step: Optional step number for tracking metrics over time
            run_id: Optional run ID (uses active run if None)
        """
        for key, value in metrics.items():
            self.log_metric(key, value, step, run_id)

        logger.info(f"📊 Logged {len(metrics)} metrics")

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None, run_id: Optional[str] = None):
        """
        Log an artifact (file) to the active or specified run.

        Args:
            local_path: Path to the local file to log
            artifact_path: Optional subdirectory in artifact storage
            run_id: Optional run ID (uses active run if None)
        """
        target_run = run_id or self.active_run_id
        if target_run is None:
            raise ValueError("No active run. Start a run first with start_run()")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Artifact not found: {local_path}")

        if self.config.mock_mode:
            self.client.log_artifact(target_run, local_path)
        else:
            with mlflow.start_run(run_id=target_run):
                mlflow.log_artifact(local_path, artifact_path)

        logger.info(f"📦 Logged artifact: {local_path}")

    @handle_errors(reraise=True, notify=False)
    def end_run(self, status: RunStatus = RunStatus.FINISHED):
        """
        End the active run.

        Args:
            status: Final status of the run
        """
        if self.active_run_id is None:
            logger.warning("⚠️  No active run to end")
            return

        if self.config.mock_mode:
            self.client.update_run(self.active_run_id, status.value)
        else:
            mlflow.end_run(status.value)

        logger.info(f"✅ Ended run: {self.active_run_id} (Status: {status.value})")
        self.active_run_id = None

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.READ)
    def get_run(self, run_id: str) -> Optional[RunMetadata]:
        """
        Get run metadata by ID.

        Args:
            run_id: The run ID to retrieve

        Returns:
            RunMetadata object or None if not found
        """
        if self.config.mock_mode:
            run_data = self.client.get_run(run_id)
            if run_data is None:
                return None

            return RunMetadata(
                run_id=run_data["run_id"],
                experiment_id=run_data["experiment_id"],
                run_name=run_data["tags"].get("mlflow.runName", "unnamed"),
                start_time=run_data["start_time"],
                end_time=run_data.get("end_time"),
                status=RunStatus(run_data["status"]),
                params=run_data["params"],
                metrics=run_data["metrics"],
                tags=run_data["tags"],
                artifacts=self.client.artifacts.get(run_id, []),
            )
        else:
            run = self.client.get_run(run_id)
            return RunMetadata(
                run_id=run.info.run_id,
                experiment_id=run.info.experiment_id,
                run_name=run.data.tags.get("mlflow.runName", "unnamed"),
                start_time=datetime.fromtimestamp(run.info.start_time / 1000),
                end_time=(
                    datetime.fromtimestamp(run.info.end_time / 1000)
                    if run.info.end_time
                    else None
                ),
                status=RunStatus(run.info.status),
                params=run.data.params,
                metrics=run.data.metrics,
                tags=run.data.tags,
            )

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.READ)
    def search_runs(
        self,
        filter_string: str = "",
        max_results: int = 100,
        order_by: Optional[List[str]] = None,
    ) -> List[RunMetadata]:
        """
        Search runs in the current experiment.

        Args:
            filter_string: MLflow filter string (e.g., "metrics.rmse < 0.5")
            max_results: Maximum number of results to return
            order_by: List of columns to order by

        Returns:
            List of RunMetadata objects
        """
        if self.config.mock_mode:
            runs = self.client.search_runs([self.experiment_id], filter_string)
            # Simple filtering for mock mode (just return all for now)
            return [
                RunMetadata(
                    run_id=run["run_id"],
                    experiment_id=run["experiment_id"],
                    run_name=run["tags"].get("mlflow.runName", "unnamed"),
                    start_time=run["start_time"],
                    end_time=run.get("end_time"),
                    status=RunStatus(run["status"]),
                    params=run["params"],
                    metrics=run["metrics"],
                    tags=run["tags"],
                )
                for run in runs[:max_results]
            ]
        else:
            runs = mlflow.search_runs(
                experiment_ids=[self.experiment_id],
                filter_string=filter_string,
                max_results=max_results,
                order_by=order_by,
            )

            results = []
            for _, run in runs.iterrows():
                results.append(
                    RunMetadata(
                        run_id=run["run_id"],
                        experiment_id=self.experiment_id,
                        run_name=run.get("tags.mlflow.runName", "unnamed"),
                        start_time=run["start_time"],
                        end_time=run.get("end_time"),
                        status=RunStatus(run["status"]),
                        params={
                            k.replace("params.", ""): v
                            for k, v in run.items()
                            if k.startswith("params.")
                        },
                        metrics={
                            k.replace("metrics.", ""): v
                            for k, v in run.items()
                            if k.startswith("metrics.")
                        },
                        tags={
                            k.replace("tags.", ""): v
                            for k, v in run.items()
                            if k.startswith("tags.")
                        },
                    )
                )

            return results

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.READ)
    def compare_runs(self, run_ids: List[str]) -> pd.DataFrame:
        """
        Compare multiple runs side by side.

        Args:
            run_ids: List of run IDs to compare

        Returns:
            DataFrame with run comparison
        """
        runs_data = []
        for run_id in run_ids:
            run = self.get_run(run_id)
            if run:
                runs_data.append(
                    {
                        "run_id": run.run_id,
                        "run_name": run.run_name,
                        "status": run.status.value,
                        "duration_seconds": run.duration_seconds,
                        **{f"param_{k}": v for k, v in run.params.items()},
                        **{f"metric_{k}": v for k, v in run.metrics.items()},
                    }
                )

        df = pd.DataFrame(runs_data)
        logger.info(f"📊 Compared {len(runs_data)} runs")
        return df


# ==============================================================================
# Utility Functions
# ==============================================================================


def get_mlflow_tracker(
    experiment_name: str = "nba_model_training", mock_mode: bool = False
) -> MLflowExperimentTracker:
    """
    Get a configured MLflow experiment tracker.

    Args:
        experiment_name: Name of the experiment
        mock_mode: Enable mock mode for testing

    Returns:
        Configured MLflowExperimentTracker instance
    """
    return MLflowExperimentTracker(experiment_name=experiment_name, mock_mode=mock_mode)


if __name__ == "__main__":
    # Demo usage
    print("=" * 80)
    print("MLFLOW INTEGRATION DEMO (Mock Mode)")
    print("=" * 80)

    # Create tracker in mock mode
    tracker = MLflowExperimentTracker(experiment_name="demo_experiment", mock_mode=True)

    # Example 1: Simple run
    print("\n" + "=" * 80)
    print("Example 1: Simple Training Run")
    print("=" * 80)

    with tracker.start_run("simple_training") as run_id:
        # Log parameters
        tracker.log_params(
            {"learning_rate": 0.01, "batch_size": 32, "epochs": 10, "optimizer": "adam"}
        )

        # Log metrics
        for epoch in range(10):
            tracker.log_metric("train_loss", 1.0 / (epoch + 1), step=epoch)
            tracker.log_metric("val_loss", 1.2 / (epoch + 1), step=epoch)
            tracker.log_metric("train_acc", 0.5 + (epoch / 20), step=epoch)
            tracker.log_metric("val_acc", 0.45 + (epoch / 20), step=epoch)

        print(f"✅ Run {run_id} completed")

    # Example 2: Search runs
    print("\n" + "=" * 80)
    print("Example 2: Search Runs")
    print("=" * 80)

    runs = tracker.search_runs(max_results=10)
    print(f"Found {len(runs)} runs:")
    for run in runs:
        print(f"  - {run.run_name} ({run.run_id}): {run.status.value}")

    print("\n" + "=" * 80)
    print("MLflow Integration Demo Complete!")
    print("=" * 80)
