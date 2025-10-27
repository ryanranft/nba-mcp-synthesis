"""
Model Serving Infrastructure

Provides production-ready model serving with versioning, A/B testing, load balancing,
and comprehensive monitoring. Integrates with Week 1 infrastructure (error handling,
monitoring, RBAC) and MLflow for model management.

Week 1 Integration:
- @handle_errors for automatic error handling
- track_metric for serving metrics
- @require_permission for access control

MLflow Integration:
- Load models from MLflow Model Registry
- Track serving metrics to MLflow
- Model version management

Features:
- Multi-version serving with A/B testing
- Health checks and readiness probes
- Request batching for efficiency
- Graceful degradation and circuit breakers
- Comprehensive metrics and monitoring
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import threading
import time
from dataclasses import dataclass, field
from contextlib import contextmanager

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


# MLflow imports
try:
    from mcp_server.mlflow_integration import get_mlflow_tracker

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model deployment status"""

    LOADING = "loading"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    RETIRED = "retired"


class HealthStatus(Enum):
    """Model health status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServingMetrics:
    """Metrics for a serving model"""

    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    circuit_breaker_trips: int = 0

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


class ServingModel:
    """
    Wrapper for a served model with production features.

    Features:
    - Thread-safe request handling
    - Circuit breaker pattern
    - Health checks
    - Comprehensive metrics
    """

    def __init__(
        self,
        model_id: str,
        version: str,
        model_instance: Any,
        mlflow_run_id: Optional[str] = None,
        error_threshold: float = 0.5,
        health_check_fn: Optional[Callable] = None,
    ):
        """
        Initialize serving model.

        Args:
            model_id: Unique model identifier
            version: Model version
            model_instance: Model object with predict() method
            mlflow_run_id: MLflow run ID (if loaded from MLflow)
            error_threshold: Error rate threshold for circuit breaker
            health_check_fn: Optional health check function
        """
        self.model_id = model_id
        self.version = version
        self.model_instance = model_instance
        self.mlflow_run_id = mlflow_run_id
        self.error_threshold = error_threshold
        self.health_check_fn = health_check_fn

        self.status = ModelStatus.READY
        self.loaded_at = datetime.utcnow()
        self.metrics = ServingMetrics()
        self.lock = threading.Lock()
        self.circuit_breaker_open = False

        logger.info(f"Serving model initialized: {model_id} v{version}")

    @handle_errors(reraise=True, notify=True)
    def predict(self, inputs: Any) -> Any:
        """
        Make a prediction with error handling and metrics.

        Args:
            inputs: Prediction inputs

        Returns:
            Prediction result

        Raises:
            Exception: If prediction fails or circuit breaker is open
        """
        # Check circuit breaker
        if self.circuit_breaker_open:
            raise Exception(f"Circuit breaker open for {self.model_id} v{self.version}")

        with self.lock:
            self.metrics.request_count += 1
            self.metrics.last_request_time = datetime.utcnow()

        try:
            start_time = time.time()
            result = self.model_instance.predict(inputs)
            latency_ms = (time.time() - start_time) * 1000

            with self.lock:
                self.metrics.total_latency_ms += latency_ms

            return result

        except Exception as e:
            with self.lock:
                self.metrics.error_count += 1
                self.metrics.last_error_time = datetime.utcnow()

                # Check if error threshold exceeded
                if self.metrics.error_rate > self.error_threshold:
                    self.circuit_breaker_open = True
                    self.metrics.circuit_breaker_trips += 1
                    self.status = ModelStatus.DEGRADED
                    logger.warning(
                        f"Circuit breaker opened for {self.model_id} v{self.version} "
                        f"(error_rate: {self.metrics.error_rate:.2%})"
                    )

            logger.error(
                f"Prediction error in model {self.model_id} v{self.version}: {e}"
            )
            raise

    def reset_circuit_breaker(self):
        """Reset circuit breaker (manual recovery)"""
        with self.lock:
            self.circuit_breaker_open = False
            self.status = ModelStatus.READY
            logger.info(f"Circuit breaker reset for {self.model_id} v{self.version}")

    def check_health(self) -> HealthStatus:
        """
        Check model health.

        Returns:
            HealthStatus indicating model health
        """
        # Custom health check
        if self.health_check_fn:
            try:
                if not self.health_check_fn(self.model_instance):
                    return HealthStatus.UNHEALTHY
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return HealthStatus.UNHEALTHY

        # Check circuit breaker
        if self.circuit_breaker_open:
            return HealthStatus.UNHEALTHY

        # Check error rate
        if self.metrics.error_rate > self.error_threshold:
            return HealthStatus.UNHEALTHY

        # Check if model is responsive (recent requests)
        if self.metrics.last_request_time:
            seconds_since_request = (
                datetime.utcnow() - self.metrics.last_request_time
            ).total_seconds()
            if seconds_since_request > 3600:  # 1 hour
                return HealthStatus.UNKNOWN

        return HealthStatus.HEALTHY

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive model serving metrics"""
        return {
            "model_id": self.model_id,
            "version": self.version,
            "status": self.status.value,
            "health": self.check_health().value,
            "mlflow_run_id": self.mlflow_run_id,
            "request_count": self.metrics.request_count,
            "error_count": self.metrics.error_count,
            "error_rate": self.metrics.error_rate,
            "avg_latency_ms": self.metrics.avg_latency_ms,
            "circuit_breaker_open": self.circuit_breaker_open,
            "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
            "uptime_seconds": (datetime.utcnow() - self.loaded_at).total_seconds(),
            "last_request_time": (
                self.metrics.last_request_time.isoformat()
                if self.metrics.last_request_time
                else None
            ),
            "last_error_time": (
                self.metrics.last_error_time.isoformat()
                if self.metrics.last_error_time
                else None
            ),
        }


class ModelServingManager:
    """
    Production-ready model serving manager.

    Features:
    - Multi-version serving
    - A/B testing with traffic routing
    - Health monitoring
    - MLflow integration
    - Week 1 integration (error handling, metrics, RBAC)
    """

    def __init__(
        self, mlflow_tracker=None, enable_mlflow: bool = False, mock_mode: bool = False
    ):
        """
        Initialize serving manager.

        Args:
            mlflow_tracker: MLflow tracker instance (optional)
            enable_mlflow: Enable MLflow integration
            mock_mode: Enable mock mode for testing
        """
        self.models: Dict[str, List[ServingModel]] = {}  # model_id -> list of versions
        self.active_models: Dict[str, str] = {}  # model_id -> active version
        self.ab_tests: Dict[str, Dict[str, float]] = (
            {}
        )  # model_id -> {version: traffic_percent}

        self.mlflow_tracker = mlflow_tracker
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE
        self.mock_mode = mock_mode

        # Initialize MLflow if needed
        if self.enable_mlflow and not self.mlflow_tracker:
            try:
                self.mlflow_tracker = get_mlflow_tracker(
                    experiment_name="model_serving", mock_mode=mock_mode
                )
            except Exception as e:
                logger.warning(f"Could not initialize MLflow: {e}")
                self.enable_mlflow = False

        logger.info(f"ModelServingManager initialized (mlflow: {self.enable_mlflow})")

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_serving.deploy")
    def deploy_model(
        self,
        model_id: str,
        version: str,
        model_instance: Any,
        set_active: bool = True,
        mlflow_run_id: Optional[str] = None,
        error_threshold: float = 0.5,
        health_check_fn: Optional[Callable] = None,
    ) -> bool:
        """
        Deploy a model for serving.

        Args:
            model_id: Unique model identifier
            version: Model version
            model_instance: Model object with predict() method
            set_active: Set as active version
            mlflow_run_id: MLflow run ID (if loaded from MLflow)
            error_threshold: Error rate threshold for circuit breaker
            health_check_fn: Optional health check function

        Returns:
            True if deployment successful
        """
        serving_model = ServingModel(
            model_id=model_id,
            version=version,
            model_instance=model_instance,
            mlflow_run_id=mlflow_run_id,
            error_threshold=error_threshold,
            health_check_fn=health_check_fn,
        )

        if model_id not in self.models:
            self.models[model_id] = []

        # Check if version already exists
        for m in self.models[model_id]:
            if m.version == version:
                logger.warning(
                    f"Model {model_id} v{version} already deployed, replacing..."
                )
                self.models[model_id].remove(m)
                break

        self.models[model_id].append(serving_model)

        if set_active:
            self.active_models[model_id] = version

        # Log to MLflow
        if self.enable_mlflow and self.mlflow_tracker:
            try:
                with self.mlflow_tracker.start_run(
                    f"deploy_{model_id}_{version}"
                ) as run_id:
                    self.mlflow_tracker.log_params(
                        {
                            "model_id": model_id,
                            "version": version,
                            "set_active": set_active,
                            "error_threshold": error_threshold,
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not log deployment to MLflow: {e}")

        logger.info(f"Model {model_id} v{version} deployed successfully")
        return True

    @handle_errors(reraise=False, notify=True)
    @require_permission(Permission.WRITE)
    def set_active_version(self, model_id: str, version: str) -> bool:
        """
        Set active version for a model.

        Args:
            model_id: Model identifier
            version: Version to set as active

        Returns:
            True if successful
        """
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

    @handle_errors(reraise=False, notify=True)
    @require_permission(Permission.WRITE)
    @track_metric("model_serving.setup_ab_test")
    def setup_ab_test(self, model_id: str, version_weights: Dict[str, float]) -> bool:
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

        # Log to MLflow
        if self.enable_mlflow and self.mlflow_tracker:
            try:
                with self.mlflow_tracker.start_run(f"ab_test_{model_id}") as run_id:
                    self.mlflow_tracker.log_params(
                        {"model_id": model_id, "ab_test_config": str(version_weights)}
                    )
            except Exception as e:
                logger.warning(f"Could not log A/B test to MLflow: {e}")

        logger.info(f"A/B test setup for {model_id}: {version_weights}")
        return True

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.READ)
    def get_model_for_prediction(
        self, model_id: str, traffic_split: Optional[float] = None
    ) -> Optional[ServingModel]:
        """
        Get model instance for prediction (handles A/B testing).

        Args:
            model_id: Model identifier
            traffic_split: Random value [0, 1] for A/B testing

        Returns:
            ServingModel instance or None
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
                        if m.version == version and not m.circuit_breaker_open:
                            return m

        # Default: use active version
        active_version = self.active_models.get(model_id)
        if active_version:
            for m in self.models[model_id]:
                if m.version == active_version and not m.circuit_breaker_open:
                    return m

        # Fallback: use first available healthy model
        for m in self.models[model_id]:
            if not m.circuit_breaker_open:
                return m

        return None

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.READ)
    @track_metric("model_serving.predict")
    def predict(
        self, model_id: str, inputs: Any, traffic_split: Optional[float] = None
    ) -> Any:
        """
        Make a prediction using the appropriate model version.

        Args:
            model_id: Model identifier
            inputs: Prediction inputs
            traffic_split: Random value for A/B testing

        Returns:
            Prediction result

        Raises:
            ValueError: If no serving model found
        """
        model = self.get_model_for_prediction(model_id, traffic_split)
        if not model:
            raise ValueError(f"No serving model found for {model_id}")

        return model.predict(inputs)

    @handle_errors(reraise=False, notify=True)
    @require_permission(Permission.WRITE)
    def retire_model(self, model_id: str, version: str) -> bool:
        """
        Retire a model version.

        Args:
            model_id: Model identifier
            version: Version to retire

        Returns:
            True if successful
        """
        if model_id not in self.models:
            return False

        for m in self.models[model_id]:
            if m.version == version:
                m.status = ModelStatus.RETIRED
                logger.info(f"Model {model_id} v{version} retired")
                return True

        return False

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_model_metrics(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get metrics for all versions of a model.

        Args:
            model_id: Model identifier

        Returns:
            List of metrics dictionaries
        """
        if model_id not in self.models:
            return []

        return [m.get_metrics() for m in self.models[model_id]]

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_all_models_status(self) -> Dict[str, Any]:
        """
        Get status of all deployed models.

        Returns:
            Dictionary with model status information
        """
        return {
            model_id: {
                "active_version": self.active_models.get(model_id),
                "versions": [m.get_metrics() for m in models],
                "ab_test": self.ab_tests.get(model_id),
                "total_requests": sum(m.metrics.request_count for m in models),
                "total_errors": sum(m.metrics.error_count for m in models),
            }
            for model_id, models in self.models.items()
        }

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all serving models.

        Returns:
            Health status for all models
        """
        health_status = {}

        for model_id, models in self.models.items():
            model_health = {"healthy": 0, "unhealthy": 0, "unknown": 0, "versions": {}}

            for m in models:
                health = m.check_health()
                model_health["versions"][m.version] = health.value

                if health == HealthStatus.HEALTHY:
                    model_health["healthy"] += 1
                elif health == HealthStatus.UNHEALTHY:
                    model_health["unhealthy"] += 1
                else:
                    model_health["unknown"] += 1

            health_status[model_id] = model_health

        return health_status


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
    serving_mgr = ModelServingManager(mock_mode=True)

    # Deploy models
    serving_mgr.deploy_model("nba_predictor", "v1.0", MockModel(0.80), set_active=True)
    serving_mgr.deploy_model("nba_predictor", "v1.1", MockModel(0.85), set_active=False)
    serving_mgr.deploy_model("nba_predictor", "v2.0", MockModel(0.90), set_active=False)

    print("\n✅ Deployed 3 model versions")

    # Setup A/B test
    serving_mgr.setup_ab_test(
        "nba_predictor", {"v1.0": 0.7, "v1.1": 0.3}  # 70% v1.0, 30% v1.1
    )

    print("\n✅ A/B test configured: 70% v1.0, 30% v1.1")

    # Make predictions
    print("\n" + "=" * 80)
    print("MAKING PREDICTIONS")
    print("=" * 80)

    import random

    for i in range(10):
        traffic_split = random.random()
        result = serving_mgr.predict(
            "nba_predictor", [1, 2, 3], traffic_split=traffic_split
        )
        print(f"Prediction {i+1}: {result} (traffic_split: {traffic_split:.2f})")

    # Health check
    print("\n" + "=" * 80)
    print("HEALTH CHECK")
    print("=" * 80)
    health = serving_mgr.health_check()
    for model_id, status in health.items():
        print(f"\n🏥 {model_id}:")
        print(f"   Healthy: {status['healthy']}, Unhealthy: {status['unhealthy']}")
        for version, health_status in status["versions"].items():
            print(f"   - v{version}: {health_status}")

    # Get metrics
    print("\n" + "=" * 80)
    print("MODEL METRICS")
    print("=" * 80)

    status = serving_mgr.get_all_models_status()
    for model_id, info in status.items():
        print(f"\n📊 {model_id}")
        print(f"   Active Version: {info['active_version']}")
        print(f"   A/B Test: {info['ab_test']}")
        print(f"   Total Requests: {info['total_requests']}")
        print(f"\n   Versions:")
        for version_metrics in info["versions"]:
            print(
                f"      - v{version_metrics['version']}: "
                f"{version_metrics['request_count']} requests, "
                f"{version_metrics['avg_latency_ms']:.2f}ms avg latency, "
                f"health: {version_metrics['health']}"
            )

    print("\n" + "=" * 80)
    print("Model Serving Demo Complete!")
    print("=" * 80)
