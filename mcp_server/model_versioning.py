"""
Model Versioning with MLflow

Production-ready model versioning system with MLflow integration.
Provides version control, rollback capabilities, and model lifecycle management.

Week 1 Integration:
- @handle_errors for automatic error handling
- track_metric for versioning operations tracking
- @require_permission for access control

MLflow Integration:
- Model logging and registry
- Version comparison
- Production promotion and rollback
"""

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.pytorch

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json

# Week 1 imports
try:
    from mcp_server.error_handling import handle_errors, NBAMCPError
    from mcp_server.monitoring import track_metric
    from mcp_server.rbac import require_permission, Permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    # Fallback decorators
    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def track_metric(metric_name):
        def decorator(func):
            return func

        return decorator

    def require_permission(permission):
        def decorator(func):
            return func

        return decorator

    class Permission:
        READ = "read"
        WRITE = "write"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    MLflow-based model registry with production features.

    Features:
    - Model logging and versioning
    - Production promotion and rollback
    - Version comparison
    - Week 1 integration (error handling, metrics, RBAC)
    """

    def __init__(
        self, tracking_uri: str = "sqlite:///mlflow.db", mock_mode: bool = False
    ):
        """
        Initialize model registry.

        Args:
            tracking_uri: MLflow tracking URI
            mock_mode: Enable mock mode for testing
        """
        self.tracking_uri = tracking_uri
        self.mock_mode = mock_mode

        if not mock_mode:
            try:
                mlflow.set_tracking_uri(tracking_uri)
                self.client = mlflow.tracking.MlflowClient()
                logger.info(
                    f"ModelRegistry initialized with MLflow (uri: {tracking_uri})"
                )
            except Exception as e:
                logger.warning(f"Could not initialize MLflow client: {e}")
                self.mock_mode = True
                self.client = None
        else:
            self.client = None
            logger.info("ModelRegistry initialized in mock mode")

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_versioning.log")
    def log_model(
        self,
        model: Any,
        model_name: str,
        experiment_name: str = "nba_models",
        params: Optional[Dict] = None,
        metrics: Optional[Dict] = None,
        artifacts: Optional[Dict] = None,
    ) -> str:
        """
        Log a model to MLflow.

        Args:
            model: Trained model
            model_name: Name of the model
            experiment_name: MLflow experiment name
            params: Model parameters/hyperparameters
            metrics: Model metrics
            artifacts: Additional artifacts to log

        Returns:
            Run ID

        Raises:
            ValueError: If in mock mode
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(f"Mock mode: Would log model {model_name}")
            return f"mock_run_{model_name}_{datetime.utcnow().timestamp()}"

        # Set experiment
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run() as run:
            # Log parameters
            if params:
                mlflow.log_params(params)

            # Log metrics
            if metrics:
                mlflow.log_metrics(metrics)

            # Log model
            if hasattr(model, "sklearn"):
                mlflow.sklearn.log_model(model, model_name)
            elif hasattr(model, "pytorch"):
                mlflow.pytorch.log_model(model, model_name)
            else:
                # Generic Python model
                mlflow.pyfunc.log_model(model_name, python_model=model)

            # Log additional artifacts
            if artifacts:
                for name, content in artifacts.items():
                    # Save artifact to temp file
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        mode="w", delete=False, suffix=".json"
                    ) as f:
                        json.dump(content, f)
                        mlflow.log_artifact(f.name, name)

            # Add tags
            mlflow.set_tags(
                {
                    "model_name": model_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "stage": "staging",
                }
            )

            logger.info(f"Model logged: {model_name} (run_id: {run.info.run_id})")
            return run.info.run_id

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_versioning.register")
    def register_model(self, run_id: str, model_name: str) -> str:
        """
        Register a model in the MLflow Model Registry.

        Args:
            run_id: MLflow run ID
            model_name: Name for registered model

        Returns:
            Model version

        Raises:
            Exception: If registration fails
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(f"Mock mode: Would register model {model_name}")
            return "1"

        model_uri = f"runs:/{run_id}/{model_name}"

        try:
            # Register model
            model_version = mlflow.register_model(model_uri, model_name)

            logger.info(f"Model registered: {model_name} v{model_version.version}")
            return model_version.version
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            raise

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_versioning.promote")
    def promote_to_production(self, model_name: str, version: str) -> bool:
        """
        Promote a model version to production.

        Args:
            model_name: Name of registered model
            version: Model version to promote

        Returns:
            True if promotion successful
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(
                f"Mock mode: Would promote {model_name} v{version} to production"
            )
            return True

        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True,
        )

        logger.info(f"Model promoted to production: {model_name} v{version}")
        return True

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.READ)
    @track_metric("model_versioning.load")
    def load_model(self, model_name: str, stage: str = "Production") -> Any:
        """
        Load a model from registry.

        Args:
            model_name: Name of registered model
            stage: Model stage (Production, Staging, etc.)

        Returns:
            Loaded model

        Raises:
            Exception: If model loading fails
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(f"Mock mode: Would load model {model_name} ({stage})")
            return None

        model_uri = f"models:/{model_name}/{stage}"

        try:
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"Loaded model: {model_name} ({stage})")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def list_models(self) -> List[Dict]:
        """
        List all registered models.

        Returns:
            List of registered models
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info("Mock mode: Returning empty model list")
            return []

        models = self.client.list_registered_models()

        model_list = []
        for model in models:
            model_list.append(
                {
                    "name": model.name,
                    "creation_timestamp": model.creation_timestamp,
                    "latest_versions": [
                        {
                            "version": v.version,
                            "stage": v.current_stage,
                            "status": v.status,
                        }
                        for v in model.latest_versions
                    ],
                }
            )

        logger.info(f"Listed {len(model_list)} models")
        return model_list

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.READ)
    def get_model_info(self, model_name: str, version: Optional[str] = None) -> Dict:
        """
        Get information about a model version.

        Args:
            model_name: Name of registered model
            version: Model version (latest if not specified)

        Returns:
            Model information

        Raises:
            ValueError: If model not found
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(f"Mock mode: Returning mock info for {model_name}")
            return {
                "name": model_name,
                "version": version or "1",
                "stage": "Production",
                "status": "READY",
            }

        if not version:
            # Get latest version
            versions = self.client.search_model_versions(f"name='{model_name}'")
            if not versions:
                raise ValueError(f"Model {model_name} not found")
            version = str(max(int(v.version) for v in versions))

        model_version = self.client.get_model_version(model_name, version)

        return {
            "name": model_version.name,
            "version": model_version.version,
            "stage": model_version.current_stage,
            "status": model_version.status,
            "creation_timestamp": model_version.creation_timestamp,
            "last_updated_timestamp": model_version.last_updated_timestamp,
            "source": model_version.source,
            "run_id": model_version.run_id,
        }

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_versioning.rollback")
    def rollback(self, model_name: str, target_version: str) -> bool:
        """
        Rollback to a previous model version.

        Args:
            model_name: Name of registered model
            target_version: Version to rollback to

        Returns:
            True if rollback successful
        """
        # Promote target version to production
        result = self.promote_to_production(model_name, target_version)

        logger.info(f"Rolled back to {model_name} v{target_version}")
        return result

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    @track_metric("model_versioning.compare")
    def compare_models(self, model_name: str, version1: str, version2: str) -> Dict:
        """
        Compare two model versions.

        Args:
            model_name: Name of registered model
            version1: First version
            version2: Second version

        Returns:
            Comparison results
        """
        if self.mock_mode or not MLFLOW_AVAILABLE:
            logger.info(
                f"Mock mode: Would compare {model_name} v{version1} vs v{version2}"
            )
            return {
                "model_name": model_name,
                "version1": {"version": version1, "metrics": {}, "params": {}},
                "version2": {"version": version2, "metrics": {}, "params": {}},
                "metrics_comparison": {},
            }

        v1_info = self.get_model_info(model_name, version1)
        v2_info = self.get_model_info(model_name, version2)

        # Get metrics for both versions
        v1_run = self.client.get_run(v1_info["run_id"])
        v2_run = self.client.get_run(v2_info["run_id"])

        # Calculate metric differences
        metrics_diff = {}
        all_metrics = set(v1_run.data.metrics.keys()) | set(v2_run.data.metrics.keys())
        for metric in all_metrics:
            val1 = v1_run.data.metrics.get(metric, 0.0)
            val2 = v2_run.data.metrics.get(metric, 0.0)
            metrics_diff[metric] = {
                "v1": val1,
                "v2": val2,
                "diff": val2 - val1,
                "pct_change": ((val2 - val1) / val1 * 100) if val1 != 0 else 0,
            }

        comparison = {
            "model_name": model_name,
            "version1": {
                "version": version1,
                "metrics": v1_run.data.metrics,
                "params": v1_run.data.params,
            },
            "version2": {
                "version": version2,
                "metrics": v2_run.data.metrics,
                "params": v2_run.data.params,
            },
            "metrics_comparison": metrics_diff,
        }

        logger.info(f"Model comparison: {model_name} v{version1} vs v{version2}")
        return comparison


# Global registry
_model_registry = None


def get_model_registry() -> ModelRegistry:
    """Get global model registry"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


# Example usage
if __name__ == "__main__":
    registry = get_model_registry()

    # Example: Log a model
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=100)
    # ... train model ...

    run_id = registry.log_model(
        model=model,
        model_name="nba_win_predictor",
        params={"n_estimators": 100, "max_depth": 10},
        metrics={"accuracy": 0.85, "f1_score": 0.83},
    )

    # Register model
    version = registry.register_model(run_id, "nba_win_predictor")

    # Promote to production
    registry.promote_to_production("nba_win_predictor", version)

    # Load model
    loaded_model = registry.load_model("nba_win_predictor", "Production")
