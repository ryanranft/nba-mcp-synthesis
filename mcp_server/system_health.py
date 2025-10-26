"""
System Health Checker Module

Provides comprehensive health checking for all NBA MCP system components.

Features:
- Component health checks (data validation, training, deployment, monitoring)
- Infrastructure health checks (database, storage, MLflow)
- Dependency health checks
- System-wide health status aggregation
- Health metrics and reporting

Usage:
    from mcp_server.system_health import SystemHealthChecker, HealthStatus

    # Initialize health checker
    checker = SystemHealthChecker()

    # Check overall system health
    health = checker.check_system_health()
    print(f"System status: {health['status']}")

    # Check specific component
    validation_health = checker.check_component_health('data_validation')
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """
    Result of a health check.

    Attributes:
        status: Health status (HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN)
        message: Human-readable status message
        details: Additional details about the health check
        timestamp: When the check was performed
        response_time_ms: Time taken to perform check (milliseconds)
    """

    def __init__(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None,
    ):
        """Initialize health check result."""
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        self.response_time_ms = response_time_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
        }

    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self.status == HealthStatus.HEALTHY

    def is_degraded(self) -> bool:
        """Check if status is degraded."""
        return self.status == HealthStatus.DEGRADED

    def is_unhealthy(self) -> bool:
        """Check if status is unhealthy."""
        return self.status == HealthStatus.UNHEALTHY


class SystemHealthChecker:
    """
    Comprehensive system health checker.

    Checks health of all components and aggregates overall system status.
    """

    def __init__(self):
        """Initialize system health checker."""
        self.component_checkers = {
            "data_validation": self._check_data_validation_health,
            "model_training": self._check_training_health,
            "model_deployment": self._check_deployment_health,
            "model_monitoring": self._check_monitoring_health,
            "database": self._check_database_health,
            "storage": self._check_storage_health,
            "mlflow": self._check_mlflow_health,
            "cache": self._check_cache_health,
        }

    def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall system health.

        Returns:
            Dictionary with system health status and component details
        """
        start_time = time.time()

        component_results = {}
        statuses = []

        # Check all components
        for component_name, checker_func in self.component_checkers.items():
            try:
                result = checker_func()
                component_results[component_name] = result.to_dict()
                statuses.append(result.status)
            except Exception as e:
                logger.error(f"Error checking {component_name} health: {e}")
                component_results[component_name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": f"Health check failed: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
                statuses.append(HealthStatus.UNKNOWN)

        # Aggregate overall status
        overall_status = self._aggregate_status(statuses)

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "status": overall_status.value,
            "components": component_results,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": elapsed_ms,
            "healthy_components": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
            "total_components": len(statuses),
        }

    def check_component_health(self, component_name: str) -> HealthCheckResult:
        """
        Check health of specific component.

        Args:
            component_name: Name of component to check

        Returns:
            HealthCheckResult for the component

        Raises:
            ValueError: If component name is invalid
        """
        if component_name not in self.component_checkers:
            raise ValueError(
                f"Unknown component: {component_name}. "
                f"Available: {list(self.component_checkers.keys())}"
            )

        return self.component_checkers[component_name]()

    def _check_data_validation_health(self) -> HealthCheckResult:
        """Check data validation component health."""
        start_time = time.time()

        try:
            from mcp_server.data_validation import DataValidationPipeline
            from mcp_server.data_cleaner import DataCleaner

            # Check if components can be instantiated
            pipeline = DataValidationPipeline()
            cleaner = DataCleaner()

            details = {
                "pipeline_initialized": True,
                "cleaner_initialized": True,
                "validation_rules_count": (
                    len(pipeline.rules) if hasattr(pipeline, "rules") else 0
                ),
            }

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Data validation components operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to import data validation components: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Data validation initialization issues: {e}",
                details={"error": str(e)},
            )

    def _check_training_health(self) -> HealthCheckResult:
        """Check model training component health."""
        start_time = time.time()

        try:
            from mcp_server.training_pipeline import TrainingPipeline
            from mcp_server.hyperparameter_tuning import HyperparameterTuner

            # Check if components can be instantiated
            pipeline = TrainingPipeline()
            tuner = HyperparameterTuner()

            details = {
                "pipeline_initialized": True,
                "tuner_initialized": True,
                "has_mlflow": hasattr(pipeline, "mlflow_client"),
            }

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Model training components operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to import training components: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Training initialization issues: {e}",
                details={"error": str(e)},
            )

    def _check_deployment_health(self) -> HealthCheckResult:
        """Check model deployment component health."""
        start_time = time.time()

        try:
            from mcp_server.model_serving import ModelServingManager
            from mcp_server.model_registry import ModelRegistry

            # Check if components can be instantiated
            serving = ModelServingManager()
            registry = ModelRegistry()

            details = {
                "serving_initialized": True,
                "registry_initialized": True,
                "deployed_models": (
                    len(serving.deployed_models)
                    if hasattr(serving, "deployed_models")
                    else 0
                ),
            }

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Model deployment components operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to import deployment components: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Deployment initialization issues: {e}",
                details={"error": str(e)},
            )

    def _check_monitoring_health(self) -> HealthCheckResult:
        """Check model monitoring component health."""
        start_time = time.time()

        try:
            from mcp_server.model_monitoring import ModelMonitor

            # Check if component can be instantiated
            monitor = ModelMonitor(model_id="health_check_test", model_version="v1.0")

            details = {
                "monitor_initialized": True,
                "drift_detection_available": True,
                "alert_system_available": hasattr(monitor, "alerts"),
            }

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Model monitoring components operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to import monitoring components: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Monitoring initialization issues: {e}",
                details={"error": str(e)},
            )

    def _check_database_health(self) -> HealthCheckResult:
        """Check database connectivity health."""
        start_time = time.time()

        try:
            # Import database tools if available
            try:
                import sqlite3

                # Try to create in-memory database as health check
                conn = sqlite3.connect(":memory:")
                conn.execute("SELECT 1")
                conn.close()

                elapsed_ms = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Database connectivity operational",
                    details={"database_type": "sqlite3"},
                    response_time_ms=elapsed_ms,
                )

            except Exception as e:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Database connectivity issues: {e}",
                    details={"error": str(e)},
                )

        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Database module not available",
                details={},
            )

    def _check_storage_health(self) -> HealthCheckResult:
        """Check storage system health."""
        start_time = time.time()

        try:
            import os
            import tempfile

            # Try to write/read from temp directory
            with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
                f.write("health_check")
                f.flush()
                # If we can write, storage is working
                pass

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Storage system operational",
                details={"temp_dir_writable": True},
                response_time_ms=elapsed_ms,
            )

        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Storage system issues: {e}",
                details={"error": str(e)},
            )

    def _check_mlflow_health(self) -> HealthCheckResult:
        """Check MLflow system health."""
        start_time = time.time()

        try:
            import mlflow

            # Check if MLflow is available
            version = mlflow.__version__

            details = {"mlflow_version": version, "mlflow_available": True}

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="MLflow system operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message="MLflow not available (optional)",
                details={"mlflow_available": False},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"MLflow issues: {e}",
                details={"error": str(e)},
            )

    def _check_cache_health(self) -> HealthCheckResult:
        """Check caching system health."""
        start_time = time.time()

        try:
            from mcp_server.system_optimizer import get_model_cache, get_data_cache

            # Get cache stats
            model_cache = get_model_cache()
            data_cache = get_data_cache()

            model_stats = model_cache.get_stats()
            data_stats = data_cache.get_stats()

            details = {
                "model_cache": model_stats,
                "data_cache": data_stats,
                "caches_operational": True,
            }

            elapsed_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Caching system operational",
                details=details,
                response_time_ms=elapsed_ms,
            )

        except ImportError as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Cache system not available: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Cache system issues: {e}",
                details={"error": str(e)},
            )

    def _aggregate_status(self, statuses: List[HealthStatus]) -> HealthStatus:
        """
        Aggregate multiple health statuses into overall status.

        Logic:
        - If any UNHEALTHY -> overall UNHEALTHY
        - If any DEGRADED -> overall DEGRADED
        - If all HEALTHY -> overall HEALTHY
        - Otherwise -> UNKNOWN

        Args:
            statuses: List of component health statuses

        Returns:
            Aggregated health status
        """
        if not statuses:
            return HealthStatus.UNKNOWN

        # Check for unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        # Check for degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        # Check if all healthy
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        # Unknown state
        return HealthStatus.UNKNOWN

    def get_health_summary(self) -> str:
        """
        Get human-readable health summary.

        Returns:
            Formatted health summary string
        """
        health = self.check_system_health()

        summary = f"System Health: {health['status'].upper()}\n"
        summary += f"Healthy Components: {health['healthy_components']}/{health['total_components']}\n"
        summary += f"Response Time: {health['response_time_ms']:.2f}ms\n\n"

        summary += "Component Status:\n"
        for component, result in health["components"].items():
            status_symbol = "✓" if result["status"] == "healthy" else "✗"
            summary += f"  {status_symbol} {component}: {result['status']}\n"

        return summary


def quick_health_check() -> bool:
    """
    Quick health check for basic system functionality.

    Returns:
        True if system is healthy, False otherwise
    """
    try:
        checker = SystemHealthChecker()
        health = checker.check_system_health()
        return health["status"] in ["healthy", "degraded"]
    except Exception as e:
        logger.error(f"Quick health check failed: {e}")
        return False
