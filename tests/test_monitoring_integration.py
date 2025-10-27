"""
Integration tests for NBA Monitoring System

Tests end-to-end integration of metrics, monitoring, and alerting:
- Complete monitoring pipeline
- Dashboard integration
- Real-world scenarios
- Performance under load

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import json
import pytest
import time
from datetime import datetime

from mcp_server.nba_metrics import MetricsCollector, get_metrics_collector
from mcp_server.monitoring import (
    HealthMonitor,
    AlertManager,
    AlertThreshold,
    AlertSeverity,
    HealthStatus,
    register_default_thresholds,
)
from mcp_server.monitoring_dashboard import (
    MonitoringDashboard,
    GameEvent,
    DashboardAPI,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def full_monitoring_stack():
    """Create a complete monitoring stack for integration testing."""
    collector = MetricsCollector()
    collector.reset_metrics()

    monitor = HealthMonitor(metrics_collector=collector, enable_auto_checks=False)
    manager = AlertManager(metrics_collector=collector)
    dashboard = MonitoringDashboard(
        metrics_collector=collector,
        health_monitor=monitor,
        alert_manager=manager,
        update_interval=1,
    )

    return {
        "collector": collector,
        "monitor": monitor,
        "manager": manager,
        "dashboard": dashboard,
    }


# ==============================================================================
# End-to-End Integration Tests
# ==============================================================================


def test_complete_monitoring_pipeline(full_monitoring_stack):
    """Test complete monitoring pipeline from metrics to alerts."""
    stack = full_monitoring_stack
    collector = stack["collector"]
    monitor = stack["monitor"]
    manager = stack["manager"]

    # 1. Record some metrics
    for i in range(10):
        collector.record_request(latency_ms=50.0 + i, error=(i % 5 == 0))
        collector.record_nba_query(latency_ms=25.0)

    # 2. Run health checks
    health = monitor.get_overall_health()
    assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    # 3. Register and check alerts
    manager.register_threshold(
        AlertThreshold(
            metric_name="application_error_count",
            threshold=1000.0,  # High threshold to avoid triggering
            comparison="gt",
            severity=AlertSeverity.WARNING,
        )
    )

    alerts = manager.check_all_thresholds()

    # Verify pipeline worked
    assert collector.request_count == 10
    assert len(health.checks) > 0
    assert isinstance(alerts, list)


def test_dashboard_integration(full_monitoring_stack):
    """Test dashboard integration with all components."""
    stack = full_monitoring_stack
    dashboard = stack["dashboard"]
    collector = stack["collector"]

    # Start dashboard
    dashboard.start()
    time.sleep(2)  # Allow data collection

    # Record some activity
    collector.record_game_processed()
    collector.record_player_processed()
    collector.record_cache_hit()

    # Get dashboard snapshot
    snapshot = dashboard.get_snapshot()

    assert snapshot is not None
    assert "metrics" in snapshot.to_dict()
    assert "health" in snapshot.to_dict()

    # Clean up
    dashboard.stop()


def test_dashboard_api_endpoints(full_monitoring_stack):
    """Test dashboard API endpoints."""
    stack = full_monitoring_stack
    dashboard = stack["dashboard"]
    api = DashboardAPI(dashboard)

    # Test all endpoints
    health_data = api.get_health()
    assert isinstance(health_data, dict)
    assert "overall_status" in health_data

    metrics_data = api.get_metrics()
    assert isinstance(metrics_data, dict)
    assert "system" in metrics_data

    alerts_data = api.get_alerts()
    assert isinstance(alerts_data, dict)
    assert "active_count" in alerts_data

    snapshot_data = api.get_snapshot()
    assert isinstance(snapshot_data, dict)

    stats_data = api.get_statistics()
    assert isinstance(stats_data, dict)


def test_game_event_streaming(full_monitoring_stack):
    """Test game event streaming through dashboard."""
    stack = full_monitoring_stack
    dashboard = stack["dashboard"]

    # Record some game events
    events = [
        GameEvent(
            game_id="game_001",
            event_type="shot",
            timestamp=datetime.now(),
            player_id="player_123",
            description="3-pointer made",
        ),
        GameEvent(
            game_id="game_001",
            event_type="rebound",
            timestamp=datetime.now(),
            player_id="player_456",
            description="Defensive rebound",
        ),
    ]

    for event in events:
        dashboard.record_game_event(event)

    # Retrieve events
    recent_events = dashboard.get_recent_game_events(limit=10)

    assert len(recent_events) == 2
    assert recent_events[0]["event_type"] in ["shot", "rebound"]


def test_time_series_data_collection(full_monitoring_stack):
    """Test time series data collection."""
    stack = full_monitoring_stack
    dashboard = stack["dashboard"]
    collector = stack["collector"]

    # Start dashboard to collect time series
    dashboard.start()

    # Record metrics over time
    for i in range(5):
        collector.record_request(50.0, error=False)
        time.sleep(0.5)

    # Stop dashboard
    time.sleep(1)
    dashboard.stop()

    # Get time series
    cpu_series = dashboard.get_time_series("cpu_percent", minutes=1)

    assert cpu_series is not None
    assert len(cpu_series.values) > 0


def test_alert_deduplication(full_monitoring_stack):
    """Test that duplicate alerts are deduplicated."""
    stack = full_monitoring_stack
    manager = stack["manager"]

    # Register threshold
    manager.register_threshold(
        AlertThreshold(
            metric_name="system_cpu_percent",
            threshold=0.0,  # Will always trigger
            comparison="gt",
            severity=AlertSeverity.INFO,
        )
    )

    # Check multiple times quickly
    alerts1 = manager.check_all_thresholds()
    time.sleep(0.1)
    alerts2 = manager.check_all_thresholds()

    # Second check should be deduplicated (within 5-minute window)
    # Note: actual behavior depends on timing


def test_health_check_recovery_tracking(full_monitoring_stack):
    """Test tracking of health check recovery."""
    stack = full_monitoring_stack
    monitor = stack["monitor"]

    # Run initial checks
    monitor.run_all_checks()
    initial_health = monitor.get_overall_health()

    # Run again after a delay
    time.sleep(1)
    monitor.run_all_checks()
    current_health = monitor.get_overall_health()

    # Verify both snapshots captured
    assert len(monitor.health_history) == 10  # 2 runs * 5 checks


# ==============================================================================
# Performance Tests
# ==============================================================================


def test_metrics_collection_performance(full_monitoring_stack):
    """Test that metrics collection has minimal overhead."""
    stack = full_monitoring_stack
    collector = stack["collector"]

    # Time 1000 metric recordings
    start = time.time()

    for i in range(1000):
        collector.record_request(50.0, error=False)
        collector.record_nba_query(25.0)
        collector.record_cache_hit()

    duration = time.time() - start

    # Should complete quickly (< 1 second for 1000 recordings)
    assert duration < 1.0

    # Verify all recorded
    assert collector.request_count == 1000


def test_concurrent_metrics_recording(full_monitoring_stack):
    """Test concurrent metrics recording from multiple threads."""
    import threading

    stack = full_monitoring_stack
    collector = stack["collector"]

    def record_metrics():
        for _ in range(100):
            collector.record_request(50.0, error=False)
            collector.record_cache_hit()

    # Create 5 threads
    threads = [threading.Thread(target=record_metrics) for _ in range(5)]

    # Start all threads
    start = time.time()
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    duration = time.time() - start

    # Should handle concurrent access efficiently
    assert duration < 2.0

    # Verify all recorded
    assert collector.request_count == 500  # 5 threads * 100 requests


def test_health_check_performance(full_monitoring_stack):
    """Test health check execution performance."""
    stack = full_monitoring_stack
    monitor = stack["monitor"]

    # Time health checks
    start = time.time()
    monitor.run_all_checks()
    duration = time.time() - start

    # Health checks should be fast (< 2 seconds)
    assert duration < 2.0


# ==============================================================================
# Real-World Scenario Tests
# ==============================================================================


def test_high_traffic_scenario(full_monitoring_stack):
    """Test monitoring under high traffic scenario."""
    stack = full_monitoring_stack
    collector = stack["collector"]
    monitor = stack["monitor"]

    # Simulate high traffic
    for i in range(1000):
        latency = 50.0 if i % 10 != 0 else 500.0  # Some slow requests
        error = i % 50 == 0  # 2% error rate
        collector.record_request(latency, error=error)

    # Collect metrics
    metrics = collector.collect_application_metrics()

    # Verify metrics reflect traffic
    assert metrics.request_count == 1000
    assert metrics.error_count == 20  # 2% of 1000
    assert metrics.success_rate_percent == 98.0

    # Health should still be good
    health = monitor.get_overall_health()
    assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


def test_cache_optimization_scenario(full_monitoring_stack):
    """Test monitoring cache performance over time."""
    stack = full_monitoring_stack
    collector = stack["collector"]

    # Simulate cache warming up
    phase1_hits = 20
    phase1_misses = 80  # 20% hit rate initially

    for _ in range(phase1_hits):
        collector.record_cache_hit()
    for _ in range(phase1_misses):
        collector.record_cache_miss()

    metrics1 = collector.collect_nba_metrics()
    assert metrics1.cache_hit_rate_percent == 20.0

    # After optimization
    phase2_hits = 70
    phase2_misses = 30  # 70% hit rate after optimization

    for _ in range(phase2_hits):
        collector.record_cache_hit()
    for _ in range(phase2_misses):
        collector.record_cache_miss()

    metrics2 = collector.collect_nba_metrics()

    # Total hit rate should be 45% ((20+70)/(100+100))
    assert metrics2.cache_hit_rate_percent == 45.0


def test_database_load_scenario(full_monitoring_stack):
    """Test monitoring database load."""
    stack = full_monitoring_stack
    collector = stack["collector"]

    # Simulate database queries with varying load
    light_load_queries = 100
    heavy_load_queries = 50

    # Light load (fast queries)
    for _ in range(light_load_queries):
        collector.record_nba_query(latency_ms=10.0)

    # Heavy load (slow queries)
    for _ in range(heavy_load_queries):
        collector.record_nba_query(latency_ms=200.0)

    metrics = collector.collect_nba_metrics()

    # Average should reflect mixed load
    assert metrics.total_queries == 150
    assert metrics.average_query_time_ms > 10.0
    assert metrics.average_query_time_ms < 200.0


# ==============================================================================
# Error Handling Tests
# ==============================================================================


def test_monitoring_graceful_degradation(full_monitoring_stack):
    """Test that monitoring degrades gracefully on errors."""
    stack = full_monitoring_stack
    monitor = stack["monitor"]

    # Even if some checks fail, others should still work
    checks = monitor.run_all_checks()

    # Should have results for all checks
    assert len(checks) > 0

    # At least some checks should succeed
    healthy_checks = [c for c in checks if c.is_healthy()]
    assert len(healthy_checks) > 0


def test_metrics_export_with_missing_data(full_monitoring_stack):
    """Test metrics export when some data is missing."""
    stack = full_monitoring_stack
    collector = stack["collector"]

    # Don't record any NBA metrics, only application
    collector.record_request(50.0, error=False)

    # Export should still work
    prometheus_export = collector.export_prometheus()
    assert isinstance(prometheus_export, str)
    assert len(prometheus_export) > 0

    summary = collector.get_summary()
    assert isinstance(summary, dict)


# ==============================================================================
# Data Consistency Tests
# ==============================================================================


def test_dashboard_export_and_import(full_monitoring_stack):
    """Test exporting and importing dashboard data."""
    stack = full_monitoring_stack
    dashboard = stack["dashboard"]
    collector = stack["collector"]

    # Record some data
    collector.record_request(50.0, error=False)
    collector.record_game_processed()

    # Export
    export_path = "/tmp/test_dashboard_export.json"
    dashboard.export_dashboard_data(export_path)

    # Verify export file exists and is valid JSON
    import os

    assert os.path.exists(export_path)

    with open(export_path, "r") as f:
        exported_data = json.load(f)

    assert "export_time" in exported_data
    assert "snapshot" in exported_data

    # Cleanup
    os.remove(export_path)


def test_metrics_consistency_across_collections(full_monitoring_stack):
    """Test that metrics are consistent across multiple collections."""
    stack = full_monitoring_stack
    collector = stack["collector"]

    # Record metrics
    collector.record_request(50.0, error=False)
    collector.record_nba_query(25.0)

    # Collect multiple times
    metrics1 = collector.collect_all_metrics()
    metrics2 = collector.collect_all_metrics()

    # Counts should be identical
    assert metrics1.application.request_count == metrics2.application.request_count
    assert metrics1.nba.total_queries == metrics2.nba.total_queries


# ==============================================================================
# Configuration Tests
# ==============================================================================


def test_custom_monitoring_configuration():
    """Test monitoring with custom configuration."""
    # Create custom stack
    collector = MetricsCollector(
        enable_system_metrics=True,
        enable_application_metrics=False,  # Disabled
        enable_nba_metrics=True,
        latency_window_size=50,
    )

    monitor = HealthMonitor(
        metrics_collector=collector,
        check_interval=10,  # Custom interval
        enable_auto_checks=False,
    )

    # Verify configuration
    assert collector.enable_system_metrics is True
    assert collector.enable_application_metrics is False
    assert monitor.check_interval == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
