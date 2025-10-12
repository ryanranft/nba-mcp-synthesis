"""
Model Serving Infrastructure
Provides model serving with versioning, A/B testing, and load balancing.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model deployment status"""
    LOADING = "loading"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    RETIRED = "retired"


class ServingModel:
    """Wrapper for a served model"""

    def __init__(self, model_id: str, version: str, model_instance: Any):
        self.model_id = model_id
        self.version = version
        self.model_instance = model_instance
        self.status = ModelStatus.READY
        self.loaded_at = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
        self.total_latency_ms = 0.0
        self.lock = threading.Lock()

    def predict(self, inputs: Any) -> Any:
        """Make a prediction"""
        with self.lock:
            self.request_count += 1

        try:
            start_time = time.time()
            result = self.model_instance.predict(inputs)
            latency_ms = (time.time() - start_time) * 1000

            with self.lock:
                self.total_latency_ms += latency_ms

            return result

        except Exception as e:
            with self.lock:
                self.error_count += 1
            logger.error(f"Prediction error in model {self.model_id} v{self.version}: {e}")
            raise

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count

    def get_metrics(self) -> Dict[str, Any]:
        """Get model serving metrics"""
        return {
            "model_id": self.model_id,
            "version": self.version,
            "status": self.status.value,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "uptime_seconds": (datetime.utcnow() - self.loaded_at).total_seconds()
        }


class ModelServingManager:
    """Manages model serving with versioning and load balancing"""

    def __init__(self):
        self.models: Dict[str, List[ServingModel]] = {}  # model_id -> list of versions
        self.active_models: Dict[str, str] = {}  # model_id -> active version
        self.ab_tests: Dict[str, Dict[str, float]] = {}  # model_id -> {version: traffic_percent}

    def deploy_model(
        self,
        model_id: str,
        version: str,
        model_instance: Any,
        set_active: bool = True
    ) -> bool:
        """
        Deploy a model for serving.

        Args:
            model_id: Unique model identifier
            version: Model version
            model_instance: Model object with predict() method
            set_active: Set as active version

        Returns:
            True if deployment successful
        """
        try:
            serving_model = ServingModel(model_id, version, model_instance)

            if model_id not in self.models:
                self.models[model_id] = []

            # Check if version already exists
            for m in self.models[model_id]:
                if m.version == version:
                    logger.warning(f"Model {model_id} v{version} already deployed, replacing...")
                    self.models[model_id].remove(m)
                    break

            self.models[model_id].append(serving_model)

            if set_active:
                self.active_models[model_id] = version

            logger.info(f"Model {model_id} v{version} deployed successfully")
            return True

        except Exception as e:
            logger.error(f"Error deploying model {model_id} v{version}: {e}")
            return False

    def set_active_version(self, model_id: str, version: str) -> bool:
        """Set active version for a model"""
        if model_id not in self.models:
            logger.error(f"Model {model_id} not found")
            return False

        version_found = any(m.version == version for m in self.models[model_id])
        if not version_found:
            logger.error(f"Version {version} not found for model {model_id}")
            return False

        self.active_models[model_id] = version
        logger.info(f"Model {model_id} active version set to {version}")
        return True

    def setup_ab_test(
        self,
        model_id: str,
        version_weights: Dict[str, float]
    ) -> bool:
        """
        Setup A/B test for model versions.

        Args:
            model_id: Model identifier
            version_weights: Dict of {version: traffic_percent}
                            e.g., {"v1.0": 0.8, "v1.1": 0.2}

        Returns:
            True if setup successful
        """
        # Validate weights sum to 1.0
        total_weight = sum(version_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.error(f"Version weights must sum to 1.0, got {total_weight}")
            return False

        # Validate all versions exist
        for version in version_weights.keys():
            if not any(m.version == version for m in self.models.get(model_id, [])):
                logger.error(f"Version {version} not found for model {model_id}")
                return False

        self.ab_tests[model_id] = version_weights
        logger.info(f"A/B test setup for {model_id}: {version_weights}")
        return True

    def get_model_for_prediction(
        self,
        model_id: str,
        traffic_split: Optional[float] = None
    ) -> Optional[ServingModel]:
        """
        Get model instance for prediction (handles A/B testing).

        Args:
            model_id: Model identifier
            traffic_split: Random value [0, 1] for A/B testing

        Returns:
            ServingModel instance
        """
        if model_id not in self.models:
            logger.error(f"Model {model_id} not found")
            return None

        # Check if A/B test is configured
        if model_id in self.ab_tests and traffic_split is not None:
            cumulative = 0.0
            for version, weight in self.ab_tests[model_id].items():
                cumulative += weight
                if traffic_split <= cumulative:
                    # Find model with this version
                    for m in self.models[model_id]:
                        if m.version == version:
                            return m

        # Default: use active version
        active_version = self.active_models.get(model_id)
        if active_version:
            for m in self.models[model_id]:
                if m.version == active_version:
                    return m

        # Fallback: use first available model
        if self.models[model_id]:
            return self.models[model_id][0]

        return None

    def predict(
        self,
        model_id: str,
        inputs: Any,
        traffic_split: Optional[float] = None
    ) -> Any:
        """
        Make a prediction using the appropriate model version.

        Args:
            model_id: Model identifier
            inputs: Prediction inputs
            traffic_split: Random value for A/B testing

        Returns:
            Prediction result
        """
        model = self.get_model_for_prediction(model_id, traffic_split)
        if not model:
            raise ValueError(f"No serving model found for {model_id}")

        return model.predict(inputs)

    def retire_model(self, model_id: str, version: str) -> bool:
        """Retire a model version"""
        if model_id not in self.models:
            return False

        for m in self.models[model_id]:
            if m.version == version:
                m.status = ModelStatus.RETIRED
                logger.info(f"Model {model_id} v{version} retired")
                return True

        return False

    def get_model_metrics(self, model_id: str) -> List[Dict[str, Any]]:
        """Get metrics for all versions of a model"""
        if model_id not in self.models:
            return []

        return [m.get_metrics() for m in self.models[model_id]]

    def get_all_models_status(self) -> Dict[str, Any]:
        """Get status of all deployed models"""
        return {
            model_id: {
                "active_version": self.active_models.get(model_id),
                "versions": [m.get_metrics() for m in models],
                "ab_test": self.ab_tests.get(model_id)
            }
            for model_id, models in self.models.items()
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL SERVING INFRASTRUCTURE DEMO")
    print("=" * 80)

    # Mock models
    class MockModel:
        def __init__(self, accuracy: float):
            self.accuracy = accuracy

        def predict(self, inputs):
            import numpy as np
            return np.random.rand() < self.accuracy

    # Initialize serving manager
    serving_mgr = ModelServingManager()

    # Deploy models
    serving_mgr.deploy_model("nba_predictor", "v1.0", MockModel(0.80), set_active=True)
    serving_mgr.deploy_model("nba_predictor", "v1.1", MockModel(0.85), set_active=False)
    serving_mgr.deploy_model("nba_predictor", "v2.0", MockModel(0.90), set_active=False)

    print("\n✅ Deployed 3 model versions")

    # Setup A/B test
    serving_mgr.setup_ab_test(
        "nba_predictor",
        {"v1.0": 0.7, "v1.1": 0.3}  # 70% v1.0, 30% v1.1
    )

    print("\n✅ A/B test configured: 70% v1.0, 30% v1.1")

    # Make predictions
    print("\n" + "=" * 80)
    print("MAKING PREDICTIONS")
    print("=" * 80)

    import random
    for i in range(10):
        traffic_split = random.random()
        result = serving_mgr.predict("nba_predictor", [1, 2, 3], traffic_split=traffic_split)
        print(f"Prediction {i+1}: {result} (traffic_split: {traffic_split:.2f})")

    # Get metrics
    print("\n" + "=" * 80)
    print("MODEL METRICS")
    print("=" * 80)

    status = serving_mgr.get_all_models_status()
    for model_id, info in status.items():
        print(f"\n📊 {model_id}")
        print(f"   Active Version: {info['active_version']}")
        print(f"   A/B Test: {info['ab_test']}")
        print(f"\n   Versions:")
        for version_metrics in info['versions']:
            print(f"      - v{version_metrics['version']}: "
                  f"{version_metrics['request_count']} requests, "
                  f"{version_metrics['avg_latency_ms']:.2f}ms avg latency")

    print("\n" + "=" * 80)
    print("Model Serving Demo Complete!")
    print("=" * 80)

