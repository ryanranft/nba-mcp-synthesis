"""
Tests for System Health Checker Module

Tests health checking functionality for all system components.
"""

import pytest
import time
from datetime import datetime
from mcp_server.system_health import (
    SystemHealthChecker,
    HealthStatus,
    HealthCheckResult,
    quick_health_check,
)


class TestHealthCheckResult:
    """Test HealthCheckResult class."""

    def test_health_check_result_creation(self):
        """Test creating health check result."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Component is healthy",
            details={"key": "value"},
            response_time_ms=10.5,
        )

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Component is healthy"
        assert result.details == {"key": "value"}
        assert result.response_time_ms == 10.5
        assert isinstance(result.timestamp, datetime)

    def test_health_check_result_to_dict(self):
        """Test converting result to dictionary."""
        result = HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message="Component degraded",
            details={"reason": "high latency"},
            response_time_ms=50.0,
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "degraded"
        assert result_dict["message"] == "Component degraded"
        assert result_dict["details"]["reason"] == "high latency"
        assert result_dict["response_time_ms"] == 50.0
        assert "timestamp" in result_dict

    def test_is_healthy_check(self):
        """Test is_healthy() method."""
        healthy_result = HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")
        degraded_result = HealthCheckResult(
            status=HealthStatus.DEGRADED, message="Degraded"
        )
        unhealthy_result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY, message="Unhealthy"
        )

        assert healthy_result.is_healthy() is True
        assert degraded_result.is_healthy() is False
        assert unhealthy_result.is_healthy() is False

    def test_is_degraded_check(self):
        """Test is_degraded() method."""
        healthy_result = HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")
        degraded_result = HealthCheckResult(
            status=HealthStatus.DEGRADED, message="Degraded"
        )

        assert healthy_result.is_degraded() is False
        assert degraded_result.is_degraded() is True

    def test_is_unhealthy_check(self):
        """Test is_unhealthy() method."""
        unhealthy_result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY, message="Failed"
        )
        healthy_result = HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        assert unhealthy_result.is_unhealthy() is True
        assert healthy_result.is_unhealthy() is False


class TestSystemHealthChecker:
    """Test SystemHealthChecker class."""

    def test_checker_initialization(self):
        """Test health checker initialization."""
        checker = SystemHealthChecker()

        assert checker is not None
        assert hasattr(checker, "component_checkers")
        assert "data_validation" in checker.component_checkers
        assert "model_training" in checker.component_checkers
        assert "model_deployment" in checker.component_checkers
        assert "model_monitoring" in checker.component_checkers

    def test_check_system_health(self):
        """Test checking overall system health."""
        checker = SystemHealthChecker()

        health = checker.check_system_health()

        # Verify structure
        assert "status" in health
        assert "components" in health
        assert "timestamp" in health
        assert "response_time_ms" in health
        assert "healthy_components" in health
        assert "total_components" in health

        # Verify status is valid
        assert health["status"] in ["healthy", "degraded", "unhealthy", "unknown"]

        # Verify we checked all expected components
        expected_components = [
            "data_validation",
            "model_training",
            "model_deployment",
            "model_monitoring",
            "database",
            "storage",
            "mlflow",
            "cache",
        ]
        for component in expected_components:
            assert component in health["components"]

        # Verify response time was measured
        assert health["response_time_ms"] > 0

    def test_check_component_health_data_validation(self):
        """Test checking data validation component health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("data_validation")

        assert isinstance(result, HealthCheckResult)
        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert result.message != ""
        assert isinstance(result.details, dict)

    def test_check_component_health_training(self):
        """Test checking training component health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("model_training")

        assert isinstance(result, HealthCheckResult)
        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert result.message != ""

    def test_check_component_health_deployment(self):
        """Test checking deployment component health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("model_deployment")

        assert isinstance(result, HealthCheckResult)
        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert result.message != ""

    def test_check_component_health_monitoring(self):
        """Test checking monitoring component health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("model_monitoring")

        assert isinstance(result, HealthCheckResult)
        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert result.message != ""

    def test_check_component_health_database(self):
        """Test checking database health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("database")

        assert isinstance(result, HealthCheckResult)
        # Database should be healthy (sqlite3 in-memory test)
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]

    def test_check_component_health_storage(self):
        """Test checking storage health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("storage")

        assert isinstance(result, HealthCheckResult)
        # Storage should be healthy (temp file write test)
        assert result.status == HealthStatus.HEALTHY

    def test_check_component_health_mlflow(self):
        """Test checking MLflow health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("mlflow")

        assert isinstance(result, HealthCheckResult)
        # MLflow might not be installed, so degraded is OK
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def test_check_component_health_cache(self):
        """Test checking cache system health."""
        checker = SystemHealthChecker()

        result = checker.check_component_health("cache")

        assert isinstance(result, HealthCheckResult)
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

        # Should have cache stats in details
        if result.status == HealthStatus.HEALTHY:
            assert "model_cache" in result.details
            assert "data_cache" in result.details

    def test_check_invalid_component(self):
        """Test checking invalid component raises error."""
        checker = SystemHealthChecker()

        with pytest.raises(ValueError, match="Unknown component"):
            checker.check_component_health("invalid_component")

    def test_aggregate_status_all_healthy(self):
        """Test status aggregation with all healthy."""
        checker = SystemHealthChecker()

        statuses = [HealthStatus.HEALTHY, HealthStatus.HEALTHY, HealthStatus.HEALTHY]

        aggregated = checker._aggregate_status(statuses)
        assert aggregated == HealthStatus.HEALTHY

    def test_aggregate_status_with_degraded(self):
        """Test status aggregation with degraded component."""
        checker = SystemHealthChecker()

        statuses = [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.HEALTHY]

        aggregated = checker._aggregate_status(statuses)
        assert aggregated == HealthStatus.DEGRADED

    def test_aggregate_status_with_unhealthy(self):
        """Test status aggregation with unhealthy component."""
        checker = SystemHealthChecker()

        statuses = [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

        aggregated = checker._aggregate_status(statuses)
        assert aggregated == HealthStatus.UNHEALTHY

    def test_aggregate_status_empty_list(self):
        """Test status aggregation with empty list."""
        checker = SystemHealthChecker()

        aggregated = checker._aggregate_status([])
        assert aggregated == HealthStatus.UNKNOWN

    def test_get_health_summary(self):
        """Test getting human-readable health summary."""
        checker = SystemHealthChecker()

        summary = checker.get_health_summary()

        # Verify summary contains key information
        assert "System Health:" in summary
        assert "Healthy Components:" in summary
        assert "Response Time:" in summary
        assert "Component Status:" in summary

        # Verify it contains component names
        assert "data_validation" in summary
        assert "model_training" in summary
        assert "model_deployment" in summary

    def test_health_check_response_time(self):
        """Test that health checks measure response time."""
        checker = SystemHealthChecker()

        start_time = time.time()
        health = checker.check_system_health()
        elapsed = (time.time() - start_time) * 1000

        # Response time should be measured and reasonable
        assert health["response_time_ms"] > 0
        assert health["response_time_ms"] < elapsed + 100  # Allow some overhead

    def test_component_health_includes_details(self):
        """Test that component health checks include useful details."""
        checker = SystemHealthChecker()

        # Check data validation details
        val_result = checker.check_component_health("data_validation")
        assert (
            "pipeline_initialized" in val_result.details
            or "error" in val_result.details
        )

        # Check training details
        train_result = checker.check_component_health("model_training")
        assert (
            "pipeline_initialized" in train_result.details
            or "error" in train_result.details
        )

        # Check deployment details
        deploy_result = checker.check_component_health("model_deployment")
        assert (
            "serving_initialized" in deploy_result.details
            or "error" in deploy_result.details
        )

    def test_quick_health_check_function(self):
        """Test quick health check utility function."""
        result = quick_health_check()

        # Should return boolean
        assert isinstance(result, bool)

        # Note: Result may be False in test environment if dependencies missing
        # In production with all dependencies, should return True

    def test_health_check_consistency(self):
        """Test that repeated health checks are consistent."""
        checker = SystemHealthChecker()

        health1 = checker.check_system_health()
        time.sleep(0.1)
        health2 = checker.check_system_health()

        # Status should be consistent
        assert health1["status"] == health2["status"]

        # Component count should be the same
        assert health1["total_components"] == health2["total_components"]

    def test_health_check_concurrent_safe(self):
        """Test that health checks are safe to run concurrently."""
        import threading

        checker = SystemHealthChecker()
        results = []

        def check_health():
            result = checker.check_system_health()
            results.append(result)

        # Run health checks in parallel
        threads = [threading.Thread(target=check_health) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All checks should complete
        assert len(results) == 5

        # All should have valid status
        for result in results:
            assert result["status"] in ["healthy", "degraded", "unhealthy", "unknown"]


class TestHealthStatusEnum:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_health_status_comparison(self):
        """Test comparing health statuses."""
        status1 = HealthStatus.HEALTHY
        status2 = HealthStatus.HEALTHY
        status3 = HealthStatus.DEGRADED

        assert status1 == status2
        assert status1 != status3
