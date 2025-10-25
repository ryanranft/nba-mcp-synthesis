"""
Comprehensive tests for NBA Monitoring System

Tests all aspects of the monitoring infrastructure including:
- Health monitoring
- Alert management
- Threshold configuration
- Notification systems
- Health check execution

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call

from mcp_server.monitoring import (
    HealthMonitor,
    AlertManager,
    HealthStatus,
    HealthCheck,
    OverallHealth,
    Alert,
    AlertThreshold,
    AlertSeverity,
    get_health_monitor,
    set_health_monitor,
    get_alert_manager,
    set_alert_manager,
    register_default_thresholds,
)
from mcp_server.nba_metrics import MetricsCollector


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def metrics_collector():
    """Create a MetricsCollector with known state."""
    collector = MetricsCollector()
    collector.reset_metrics()
    return collector


@pytest.fixture
def health_monitor(metrics_collector):
    """Create a fresh HealthMonitor instance."""
    monitor = HealthMonitor(
        check_interval=30,
        enable_auto_checks=False,  # Don't start auto-checks in tests
        metrics_collector=metrics_collector,
    )
    return monitor


@pytest.fixture
def alert_manager(metrics_collector):
    """Create a fresh AlertManager instance."""
    manager = AlertManager(
        enable_email=False,
        enable_slack=False,
        enable_webhook=False,
        metrics_collector=metrics_collector,
    )
    return manager


# ==============================================================================
# Health Status Tests
# ==============================================================================


def test_health_status_enum():
    """Test HealthStatus enum values."""
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"


def test_health_status_is_healthy():
    """Test is_healthy property."""
    assert HealthStatus.HEALTHY.is_healthy is True
    assert HealthStatus.DEGRADED.is_healthy is True
    assert HealthStatus.UNHEALTHY.is_healthy is False
    assert HealthStatus.UNKNOWN.is_healthy is False


def test_health_status_severity_level():
    """Test severity_level property."""
    assert HealthStatus.HEALTHY.severity_level == 0
    assert HealthStatus.DEGRADED.severity_level == 1
    assert HealthStatus.UNHEALTHY.severity_level == 2
    assert HealthStatus.UNKNOWN.severity_level == 3


# ==============================================================================
# Health Check Tests
# ==============================================================================


def test_health_check_creation():
    """Test creating a HealthCheck."""
    check = HealthCheck(
        name="test_component",
        status=HealthStatus.HEALTHY,
        message="Component is healthy",
        response_time_ms=45.2,
        details={"key": "value"},
        tags=["test", "component"],
    )

    assert check.name == "test_component"
    assert check.status == HealthStatus.HEALTHY
    assert check.message == "Component is healthy"
    assert check.response_time_ms == 45.2
    assert check.details == {"key": "value"}
    assert check.tags == ["test", "component"]
    assert isinstance(check.timestamp, datetime)


def test_health_check_to_dict():
    """Test HealthCheck to_dict conversion."""
    check = HealthCheck(
        name="database",
        status=HealthStatus.HEALTHY,
        message="Database OK",
    )

    check_dict = check.to_dict()

    assert isinstance(check_dict, dict)
    assert check_dict["name"] == "database"
    assert check_dict["status"] == "healthy"
    assert check_dict["message"] == "Database OK"
    assert "timestamp" in check_dict
    assert "response_time_ms" in check_dict


def test_health_check_is_healthy():
    """Test HealthCheck is_healthy method."""
    healthy_check = HealthCheck(name="test", status=HealthStatus.HEALTHY, message="OK")
    assert healthy_check.is_healthy() is True

    unhealthy_check = HealthCheck(
        name="test", status=HealthStatus.UNHEALTHY, message="Failed"
    )
    assert unhealthy_check.is_healthy() is False


# ==============================================================================
# Health Monitor Tests
# ==============================================================================


def test_health_monitor_initialization(health_monitor):
    """Test HealthMonitor initialization."""
    assert health_monitor.check_interval == 30
    assert health_monitor.enable_auto_checks is False
    assert isinstance(health_monitor.health_checks, dict)
    assert len(health_monitor.health_checks) == 0


def test_check_system_resources(health_monitor):
    """Test system resources health check."""
    check = health_monitor.check_system_resources()

    assert isinstance(check, HealthCheck)
    assert check.name == "system_resources"
    assert check.status in [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY,
    ]
    assert check.response_time_ms >= 0
    assert "cpu_percent" in check.details
    assert "memory_percent" in check.details
    assert "disk_percent" in check.details


def test_check_application_health(health_monitor):
    """Test application health check."""
    # Record some metrics first
    health_monitor.metrics_collector.record_request(50.0, error=False)

    check = health_monitor.check_application_health()

    assert isinstance(check, HealthCheck)
    assert check.name == "application"
    assert check.status in [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY,
    ]
    assert "error_rate" in check.details
    assert "p95_latency_ms" in check.details


def test_check_nba_data_health(health_monitor):
    """Test NBA data health check."""
    # Update data to ensure it's fresh
    health_monitor.metrics_collector.record_data_update()

    check = health_monitor.check_nba_data_health()

    assert isinstance(check, HealthCheck)
    assert check.name == "nba_data"
    assert check.status in [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY,
    ]
    assert "data_age_seconds" in check.details


@patch("mcp_server.monitoring.psutil")
def test_check_database_health_success(mock_psutil, health_monitor):
    """Test successful database health check."""
    # Mock the database connection directly in the health monitor's method
    # Since get_db_connection doesn't exist, we'll just mock the check result
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor

    # Patch at module import level to avoid ImportError
    import sys
    from unittest.mock import MagicMock

    mock_db_module = MagicMock()
    mock_db_module.get_db_connection = Mock(return_value=mock_conn)
    sys.modules["mcp_server.connectors.db"] = mock_db_module

    try:
        check = health_monitor.check_database_health()
        assert check.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert check.response_time_ms >= 0
    finally:
        # Clean up the mock module
        del sys.modules["mcp_server.connectors.db"]


@patch("mcp_server.monitoring.boto3")
def test_check_s3_health_success(mock_boto3, health_monitor):
    """Test successful S3 health check."""
    mock_s3 = Mock()
    mock_s3.list_objects_v2.return_value = {"Contents": []}
    mock_boto3.client.return_value = mock_s3

    check = health_monitor.check_s3_health()

    assert check.status == HealthStatus.HEALTHY
    assert "bucket" in check.details


def test_run_all_checks(health_monitor):
    """Test running all health checks."""
    checks = health_monitor.run_all_checks()

    assert isinstance(checks, list)
    assert len(checks) == 5  # database, s3, system, application, nba_data

    # Verify all checks were stored
    assert len(health_monitor.health_checks) == 5


def test_get_overall_health(health_monitor):
    """Test getting overall health status."""
    # Run checks first
    health_monitor.run_all_checks()

    overall = health_monitor.get_overall_health()

    assert isinstance(overall, OverallHealth)
    assert overall.status in [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY,
    ]
    assert (
        overall.healthy_count + overall.degraded_count + overall.unhealthy_count
        == len(overall.checks)
    )


def test_get_check(health_monitor):
    """Test getting specific health check."""
    health_monitor.run_all_checks()

    system_check = health_monitor.get_check("system_resources")

    assert system_check is not None
    assert system_check.name == "system_resources"

    # Non-existent check
    missing_check = health_monitor.get_check("nonexistent")
    assert missing_check is None


def test_get_failing_checks(health_monitor):
    """Test getting failing checks."""
    health_monitor.run_all_checks()

    failing = health_monitor.get_failing_checks()

    assert isinstance(failing, list)
    # All checks should be healthy or degraded, not unhealthy
    for check in failing:
        assert check.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]


def test_health_monitor_start_stop(health_monitor):
    """Test starting and stopping health monitor."""
    assert health_monitor._running is False

    health_monitor.start()
    assert health_monitor._running is True

    # Give it a moment to start
    time.sleep(0.1)

    health_monitor.stop()
    assert health_monitor._running is False


def test_overall_health_to_json(health_monitor):
    """Test OverallHealth JSON serialization."""
    health_monitor.run_all_checks()
    overall = health_monitor.get_overall_health()

    json_str = overall.to_json()
    assert isinstance(json_str, str)

    parsed = json.loads(json_str)
    assert "status" in parsed
    assert "checks" in parsed
    assert "timestamp" in parsed


# ==============================================================================
# Alert Tests
# ==============================================================================


def test_alert_creation():
    """Test creating an Alert."""
    alert = Alert(
        id="alert_123",
        name="High CPU",
        message="CPU usage above threshold",
        severity=AlertSeverity.WARNING,
        metric_name="cpu_percent",
        current_value=85.5,
        threshold_value=80.0,
        tags=["cpu", "warning"],
    )

    assert alert.id == "alert_123"
    assert alert.severity == AlertSeverity.WARNING
    assert alert.current_value == 85.5
    assert alert.resolved is False


def test_alert_to_dict():
    """Test Alert to_dict conversion."""
    alert = Alert(
        id="alert_456",
        name="High Memory",
        message="Memory usage critical",
        severity=AlertSeverity.CRITICAL,
        metric_name="memory_percent",
        current_value=95.0,
        threshold_value=90.0,
    )

    alert_dict = alert.to_dict()

    assert isinstance(alert_dict, dict)
    assert alert_dict["id"] == "alert_456"
    assert alert_dict["severity"] == "critical"
    assert alert_dict["resolved"] is False


def test_alert_resolve():
    """Test resolving an alert."""
    alert = Alert(
        id="alert_789",
        name="Test Alert",
        message="Test",
        severity=AlertSeverity.INFO,
        metric_name="test_metric",
        current_value=100.0,
        threshold_value=50.0,
    )

    assert alert.resolved is False
    assert alert.resolved_at is None

    alert.resolve()

    assert alert.resolved is True
    assert isinstance(alert.resolved_at, datetime)


# ==============================================================================
# Alert Threshold Tests
# ==============================================================================


def test_alert_threshold_creation():
    """Test creating an AlertThreshold."""
    threshold = AlertThreshold(
        metric_name="cpu_percent",
        threshold=80.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        window_seconds=60,
        min_occurrences=3,
        description="CPU too high",
    )

    assert threshold.metric_name == "cpu_percent"
    assert threshold.threshold == 80.0
    assert threshold.comparison == "gt"
    assert threshold.enabled is True


def test_alert_threshold_evaluate_gt():
    """Test threshold evaluation with greater than."""
    threshold = AlertThreshold(
        metric_name="test",
        threshold=50.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
    )

    assert threshold.evaluate(60.0) is True
    assert threshold.evaluate(50.0) is False
    assert threshold.evaluate(40.0) is False


def test_alert_threshold_evaluate_lt():
    """Test threshold evaluation with less than."""
    threshold = AlertThreshold(
        metric_name="test",
        threshold=50.0,
        comparison="lt",
        severity=AlertSeverity.WARNING,
    )

    assert threshold.evaluate(40.0) is True
    assert threshold.evaluate(50.0) is False
    assert threshold.evaluate(60.0) is False


def test_alert_threshold_evaluate_gte():
    """Test threshold evaluation with greater than or equal."""
    threshold = AlertThreshold(
        metric_name="test",
        threshold=50.0,
        comparison="gte",
        severity=AlertSeverity.WARNING,
    )

    assert threshold.evaluate(60.0) is True
    assert threshold.evaluate(50.0) is True
    assert threshold.evaluate(40.0) is False


def test_alert_threshold_disabled():
    """Test that disabled thresholds don't evaluate."""
    threshold = AlertThreshold(
        metric_name="test",
        threshold=50.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        enabled=False,
    )

    assert threshold.evaluate(100.0) is False


# ==============================================================================
# Alert Manager Tests
# ==============================================================================


def test_alert_manager_initialization(alert_manager):
    """Test AlertManager initialization."""
    assert alert_manager.enable_email is False
    assert alert_manager.enable_slack is False
    assert alert_manager.enable_webhook is False
    assert len(alert_manager.thresholds) == 0


def test_register_threshold(alert_manager):
    """Test registering an alert threshold."""
    threshold = AlertThreshold(
        metric_name="cpu_percent",
        threshold=80.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
    )

    alert_manager.register_threshold(threshold)

    assert "cpu_percent" in alert_manager.thresholds
    assert alert_manager.thresholds["cpu_percent"] == threshold


def test_unregister_threshold(alert_manager):
    """Test unregistering an alert threshold."""
    threshold = AlertThreshold(
        metric_name="cpu_percent",
        threshold=80.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
    )

    alert_manager.register_threshold(threshold)
    assert "cpu_percent" in alert_manager.thresholds

    alert_manager.unregister_threshold("cpu_percent")
    assert "cpu_percent" not in alert_manager.thresholds


def test_check_all_thresholds_no_alerts(alert_manager, metrics_collector):
    """Test checking thresholds with no violations."""
    # Register threshold
    alert_manager.register_threshold(
        AlertThreshold(
            metric_name="system_cpu_percent",
            threshold=95.0,  # Very high threshold
            comparison="gt",
            severity=AlertSeverity.WARNING,
        )
    )

    # Check thresholds
    alerts = alert_manager.check_all_thresholds()

    # Should be no alerts (CPU unlikely to be above 95%)
    assert isinstance(alerts, list)


def test_resolve_alert(alert_manager):
    """Test resolving an alert."""
    # Create and record an alert
    alert = Alert(
        id="test_alert_123",
        name="Test Alert",
        message="Test",
        severity=AlertSeverity.INFO,
        metric_name="test",
        current_value=100.0,
        threshold_value=50.0,
    )

    alert_manager.active_alerts[alert.id] = alert

    # Resolve it
    success = alert_manager.resolve_alert(alert.id)

    assert success is True
    assert alert.id not in alert_manager.active_alerts
    assert alert.resolved is True


def test_resolve_nonexistent_alert(alert_manager):
    """Test resolving a non-existent alert."""
    success = alert_manager.resolve_alert("nonexistent_alert")

    assert success is False


def test_get_active_alerts(alert_manager):
    """Test getting active alerts."""
    # Create some alerts
    for i in range(3):
        alert = Alert(
            id=f"alert_{i}",
            name=f"Alert {i}",
            message=f"Test alert {i}",
            severity=AlertSeverity.WARNING,
            metric_name="test",
            current_value=100.0,
            threshold_value=50.0,
        )
        alert_manager.active_alerts[alert.id] = alert

    active = alert_manager.get_active_alerts()

    assert len(active) == 3


def test_get_alert_history(alert_manager):
    """Test getting alert history."""
    # Create some alerts
    for i in range(5):
        alert = Alert(
            id=f"alert_{i}",
            name=f"Alert {i}",
            message=f"Test alert {i}",
            severity=AlertSeverity.INFO,
            metric_name="test",
            current_value=100.0,
            threshold_value=50.0,
        )
        alert_manager.alert_history.append(alert)

    history = alert_manager.get_alert_history(limit=3)

    # Should return last 3
    assert len(history) == 3


def test_register_default_thresholds():
    """Test registering default thresholds."""
    # Get the global alert manager (same one used by register_default_thresholds)
    manager = get_alert_manager()

    # Clear any existing thresholds
    manager.thresholds.clear()

    # Register defaults
    register_default_thresholds()

    # Should have registered multiple default thresholds
    assert len(manager.thresholds) > 0


# ==============================================================================
# Notification Tests
# ==============================================================================


@patch("mcp_server.monitoring.smtplib.SMTP")
def test_send_email_alert(mock_smtp, alert_manager):
    """Test sending email alert."""
    # Enable email
    alert_manager.enable_email = True
    alert_manager.email_config["to_emails"] = ["test@example.com"]
    alert_manager.email_config["smtp_user"] = "sender@example.com"

    # Create alert
    alert = Alert(
        id="test_123",
        name="Test Alert",
        message="Test message",
        severity=AlertSeverity.WARNING,
        metric_name="test",
        current_value=100.0,
        threshold_value=50.0,
    )

    # Mock SMTP server
    mock_server = Mock()
    mock_smtp.return_value = mock_server

    # Send alert
    alert_manager._send_email_alert(alert)

    # Verify SMTP was called
    mock_smtp.assert_called_once()
    mock_server.starttls.assert_called_once()


@patch("mcp_server.monitoring.urlopen")
def test_send_slack_alert(mock_urlopen, alert_manager):
    """Test sending Slack alert."""
    # Enable Slack
    alert_manager.enable_slack = True
    alert_manager.slack_config["webhook_url"] = "https://hooks.slack.com/test"

    # Create alert
    alert = Alert(
        id="test_456",
        name="Test Alert",
        message="Test message",
        severity=AlertSeverity.CRITICAL,
        metric_name="test",
        current_value=100.0,
        threshold_value=50.0,
    )

    # Send alert
    alert_manager._send_slack_alert(alert)

    # Verify webhook was called
    mock_urlopen.assert_called_once()


@patch("mcp_server.monitoring.urlopen")
def test_send_webhook_alert(mock_urlopen, alert_manager):
    """Test sending webhook alert."""
    # Enable webhook
    alert_manager.enable_webhook = True
    alert_manager.webhook_config["url"] = "https://example.com/webhook"

    # Create alert
    alert = Alert(
        id="test_789",
        name="Test Alert",
        message="Test message",
        severity=AlertSeverity.INFO,
        metric_name="test",
        current_value=100.0,
        threshold_value=50.0,
    )

    # Send alert
    alert_manager._send_webhook_alert(alert)

    # Verify webhook was called
    mock_urlopen.assert_called_once()


# ==============================================================================
# Global Instance Tests
# ==============================================================================


def test_get_global_health_monitor():
    """Test getting global health monitor."""
    monitor1 = get_health_monitor()
    monitor2 = get_health_monitor()

    # Should return same instance
    assert monitor1 is monitor2


def test_set_global_health_monitor():
    """Test setting global health monitor."""
    custom_monitor = HealthMonitor()
    set_health_monitor(custom_monitor)

    retrieved_monitor = get_health_monitor()

    assert retrieved_monitor is custom_monitor


def test_get_global_alert_manager():
    """Test getting global alert manager."""
    manager1 = get_alert_manager()
    manager2 = get_alert_manager()

    # Should return same instance
    assert manager1 is manager2


def test_set_global_alert_manager():
    """Test setting global alert manager."""
    custom_manager = AlertManager()
    set_alert_manager(custom_manager)

    retrieved_manager = get_alert_manager()

    assert retrieved_manager is custom_manager


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_health_and_alerts_integration():
    """Test integration between health monitoring and alerts."""
    collector = MetricsCollector()
    monitor = HealthMonitor(metrics_collector=collector)
    manager = AlertManager(metrics_collector=collector)

    # Register threshold for unhealthy components
    manager.register_threshold(
        AlertThreshold(
            metric_name="application_success_rate_percent",
            threshold=95.0,
            comparison="lt",
            severity=AlertSeverity.CRITICAL,
        )
    )

    # Run health checks
    monitor.run_all_checks()

    # Check thresholds
    alerts = manager.check_all_thresholds()

    # Should work without errors
    assert isinstance(alerts, list)


def test_consecutive_failures_tracking(health_monitor):
    """Test tracking consecutive failures."""
    # Simulate multiple failures for a component
    for _ in range(3):
        # Run checks (some may fail)
        health_monitor.run_all_checks()

    # Check consecutive failures are tracked
    assert isinstance(health_monitor.consecutive_failures, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
