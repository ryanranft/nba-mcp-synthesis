"""Model Versioning with MLflow - BOOK RECOMMENDATION 1"""

import mlflow
import mlflow.sklearn
import mlflow.pytorch
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ModelRegistry:
    """MLflow-based model registry"""

    def __init__(self, tracking_uri: str = "sqlite:///mlflow.db"):
        """
        Initialize model registry

        Args:
            tracking_uri: MLflow tracking URI
        """
        mlflow.set_tracking_uri(tracking_uri)
        self.client = mlflow.tracking.MlflowClient()

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
        Log a model to MLflow

        Args:
            model: Trained model
            model_name: Name of the model
            experiment_name: MLflow experiment name
            params: Model parameters/hyperparameters
            metrics: Model metrics
            artifacts: Additional artifacts to log

        Returns:
            Run ID
        """
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

            logger.info(f"✅ Model logged: {model_name} (run_id: {run.info.run_id})")
            return run.info.run_id

    def register_model(self, run_id: str, model_name: str) -> str:
        """
        Register a model in the MLflow Model Registry

        Args:
            run_id: MLflow run ID
            model_name: Name for registered model

        Returns:
            Model version
        """
        model_uri = f"runs:/{run_id}/{model_name}"

        try:
            # Register model
            model_version = mlflow.register_model(model_uri, model_name)

            logger.info(f"✅ Model registered: {model_name} v{model_version.version}")
            return model_version.version
        except Exception as e:
            logger.error(f"❌ Failed to register model: {e}")
            raise

    def promote_to_production(self, model_name: str, version: str):
        """
        Promote a model version to production

        Args:
            model_name: Name of registered model
            version: Model version to promote
        """
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True,
        )

        logger.info(f"✅ Model promoted to production: {model_name} v{version}")

    def load_model(self, model_name: str, stage: str = "Production") -> Any:
        """
        Load a model from registry

        Args:
            model_name: Name of registered model
            stage: Model stage (Production, Staging, etc.)

        Returns:
            Loaded model
        """
        model_uri = f"models:/{model_name}/{stage}"

        try:
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"✅ Loaded model: {model_name} ({stage})")
            return model
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    def list_models(self) -> List[Dict]:
        """
        List all registered models

        Returns:
            List of registered models
        """
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

        return model_list

    def get_model_info(self, model_name: str, version: Optional[str] = None) -> Dict:
        """
        Get information about a model version

        Args:
            model_name: Name of registered model
            version: Model version (latest if not specified)

        Returns:
            Model information
        """
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

    def rollback(self, model_name: str, target_version: str):
        """
        Rollback to a previous model version

        Args:
            model_name: Name of registered model
            target_version: Version to rollback to
        """
        # Promote target version to production
        self.promote_to_production(model_name, target_version)

        logger.info(f"✅ Rolled back to {model_name} v{target_version}")

    def compare_models(self, model_name: str, version1: str, version2: str) -> Dict:
        """
        Compare two model versions

        Args:
            model_name: Name of registered model
            version1: First version
            version2: Second version

        Returns:
            Comparison results
        """
        v1_info = self.get_model_info(model_name, version1)
        v2_info = self.get_model_info(model_name, version2)

        # Get metrics for both versions
        v1_run = self.client.get_run(v1_info["run_id"])
        v2_run = self.client.get_run(v2_info["run_id"])

        comparison = {
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
        }

        logger.info(f"📊 Model comparison: {model_name} v{version1} vs v{version2}")
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
