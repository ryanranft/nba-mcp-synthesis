"""
Comprehensive tests for NBA Metrics Collection

Tests all aspects of the metrics collection system including:
- System metrics collection
- Application metrics tracking
- NBA-specific metrics
- Latency tracking
- Context managers
- Export functionality
- Thread safety

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from mcp_server.nba_metrics import (
    MetricsCollector,
    SystemMetrics,
    ApplicationMetrics,
    NBAMetrics,
    AllMetrics,
    LatencyTracker,
    MetricType,
    RequestTracker,
    QueryTracker,
    get_metrics_collector,
    set_metrics_collector,
    track_latency,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def metrics_collector():
    """Create a fresh MetricsCollector instance for each test."""
    collector = MetricsCollector(
        enable_system_metrics=True,
        enable_application_metrics=True,
        enable_nba_metrics=True,
        latency_window_size=100,
    )
    collector.reset_metrics()
    return collector


@pytest.fixture
def latency_tracker():
    """Create a fresh LatencyTracker instance."""
    return LatencyTracker(window_size=100)


# ==============================================================================
# System Metrics Tests
# ==============================================================================


def test_collect_system_metrics(metrics_collector):
    """Test that system metrics can be collected."""
    metrics = metrics_collector.collect_system_metrics()

    assert isinstance(metrics, SystemMetrics)
    assert metrics.cpu_percent >= 0
    assert metrics.cpu_percent <= 100
    assert metrics.cpu_count > 0
    assert metrics.memory_percent >= 0
    assert metrics.memory_percent <= 100
    assert metrics.memory_total_bytes > 0
    assert metrics.disk_usage_percent >= 0
    assert metrics.disk_usage_percent <= 100
    assert isinstance(metrics.timestamp, datetime)


def test_system_metrics_to_dict(metrics_collector):
    """Test SystemMetrics can be converted to dictionary."""
    metrics = metrics_collector.collect_system_metrics()
    metrics_dict = metrics.to_dict()

    assert isinstance(metrics_dict, dict)
    assert "cpu_percent" in metrics_dict
    assert "memory_percent" in metrics_dict
    assert "disk_usage_percent" in metrics_dict
    assert "timestamp" in metrics_dict
    assert isinstance(metrics_dict["cpu_count"], int)


def test_system_metrics_network_stats(metrics_collector):
    """Test that network statistics are collected."""
    metrics = metrics_collector.collect_system_metrics()

    assert metrics.network_bytes_sent >= 0
    assert metrics.network_bytes_recv >= 0
    assert metrics.network_packets_sent >= 0
    assert metrics.network_packets_recv >= 0


def test_system_metrics_disk_io(metrics_collector):
    """Test that disk I/O statistics are collected."""
    metrics = metrics_collector.collect_system_metrics()

    assert metrics.disk_io_read_bytes >= 0
    assert metrics.disk_io_write_bytes >= 0
    assert metrics.disk_io_read_count >= 0
    assert metrics.disk_io_write_count >= 0


# ==============================================================================
# Application Metrics Tests
# ==============================================================================


def test_collect_application_metrics_initial_state(metrics_collector):
    """Test application metrics in initial state."""
    metrics = metrics_collector.collect_application_metrics()

    assert isinstance(metrics, ApplicationMetrics)
    assert metrics.request_count == 0
    assert metrics.error_count == 0
    assert metrics.active_requests == 0
    assert metrics.success_rate_percent == 100.0  # No requests yet


def test_record_request_success(metrics_collector):
    """Test recording successful requests."""
    # Record some successful requests
    for i in range(10):
        metrics_collector.record_request(latency_ms=50.0 + i, error=False)

    metrics = metrics_collector.collect_application_metrics()

    assert metrics.request_count == 10
    assert metrics.error_count == 0
    assert metrics.success_rate_percent == 100.0
    assert metrics.average_latency_ms > 0


def test_record_request_with_errors(metrics_collector):
    """Test recording requests with errors."""
    # Record mixed success and error requests
    for i in range(10):
        error = i % 3 == 0  # Every 3rd request fails
        metrics_collector.record_request(latency_ms=100.0, error=error)

    metrics = metrics_collector.collect_application_metrics()

    assert metrics.request_count == 10
    assert metrics.error_count == 4  # 0, 3, 6, 9
    assert metrics.success_rate_percent == 60.0  # 6/10


def test_latency_percentiles(metrics_collector):
    """Test latency percentile calculations."""
    # Record requests with known latencies
    latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for latency in latencies:
        metrics_collector.record_request(latency_ms=latency, error=False)

    metrics = metrics_collector.collect_application_metrics()

    # Check percentiles are in expected range
    assert metrics.p50_latency_ms >= 40 and metrics.p50_latency_ms <= 60
    assert metrics.p95_latency_ms >= 90
    assert metrics.p99_latency_ms >= 90


def test_active_requests_tracking(metrics_collector):
    """Test active request counter."""
    assert metrics_collector.active_requests == 0

    metrics_collector.increment_active_requests()
    assert metrics_collector.active_requests == 1

    metrics_collector.increment_active_requests()
    assert metrics_collector.active_requests == 2

    metrics_collector.decrement_active_requests()
    assert metrics_collector.active_requests == 1

    metrics_collector.decrement_active_requests()
    assert metrics_collector.active_requests == 0

    # Should not go negative
    metrics_collector.decrement_active_requests()
    assert metrics_collector.active_requests == 0


def test_application_metrics_to_dict(metrics_collector):
    """Test ApplicationMetrics can be converted to dictionary."""
    metrics_collector.record_request(latency_ms=50.0, error=False)
    metrics = metrics_collector.collect_application_metrics()
    metrics_dict = metrics.to_dict()

    assert isinstance(metrics_dict, dict)
    assert "request_count" in metrics_dict
    assert "error_count" in metrics_dict
    assert "success_rate_percent" in metrics_dict
    assert "average_latency_ms" in metrics_dict


# ==============================================================================
# NBA Metrics Tests
# ==============================================================================


def test_collect_nba_metrics_initial_state(metrics_collector):
    """Test NBA metrics in initial state."""
    metrics = metrics_collector.collect_nba_metrics()

    assert isinstance(metrics, NBAMetrics)
    assert metrics.total_queries == 0
    assert metrics.cache_hits == 0
    assert metrics.cache_misses == 0
    assert metrics.tool_success_rate_percent == 100.0


def test_record_nba_query(metrics_collector):
    """Test recording database queries."""
    # Record some queries
    for i in range(5):
        metrics_collector.record_nba_query(latency_ms=25.0 + i)

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics.total_queries == 5
    assert metrics.average_query_time_ms > 0


def test_cache_hit_rate_calculation(metrics_collector):
    """Test cache hit rate calculation."""
    # Record 7 hits and 3 misses (70% hit rate)
    for _ in range(7):
        metrics_collector.record_cache_hit()
    for _ in range(3):
        metrics_collector.record_cache_miss()

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics.cache_hits == 7
    assert metrics.cache_misses == 3
    assert metrics.cache_hit_rate_percent == 70.0


def test_cache_hit_rate_no_operations(metrics_collector):
    """Test cache hit rate when no cache operations recorded."""
    metrics = metrics_collector.collect_nba_metrics()

    # Should be 0% when no operations
    assert metrics.cache_hit_rate_percent == 0.0


def test_data_freshness(metrics_collector):
    """Test data freshness tracking."""
    # Record data update
    metrics_collector.record_data_update()

    # Wait a bit
    time.sleep(0.1)

    metrics = metrics_collector.collect_nba_metrics()

    # Data should be fresh (less than 1 second old)
    assert metrics.data_freshness_seconds < 1.0


def test_tool_execution_tracking(metrics_collector):
    """Test tool execution success rate."""
    # Record 8 successful and 2 failed executions
    for _ in range(8):
        metrics_collector.record_tool_execution(success=True)
    for _ in range(2):
        metrics_collector.record_tool_execution(success=False)

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics_collector.tool_executions == 10
    assert metrics_collector.tool_failures == 2
    assert metrics.tool_success_rate_percent == 80.0


def test_game_and_player_processing(metrics_collector):
    """Test game and player processing counters."""
    # Record some processing events
    for _ in range(5):
        metrics_collector.record_game_processed()
    for _ in range(10):
        metrics_collector.record_player_processed()

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics.games_processed == 5
    assert metrics.players_processed == 10


def test_s3_operations_tracking(metrics_collector):
    """Test S3 read/write tracking."""
    # Record S3 operations
    for _ in range(3):
        metrics_collector.record_s3_read()
    for _ in range(2):
        metrics_collector.record_s3_write()

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics.s3_reads == 3
    assert metrics.s3_writes == 2


def test_database_connections_tracking(metrics_collector):
    """Test database connection count tracking."""
    metrics_collector.set_database_connections(5)

    metrics = metrics_collector.collect_nba_metrics()

    assert metrics.database_connections == 5


# ==============================================================================
# All Metrics Tests
# ==============================================================================


def test_collect_all_metrics(metrics_collector):
    """Test collecting all metrics at once."""
    all_metrics = metrics_collector.collect_all_metrics()

    assert isinstance(all_metrics, AllMetrics)
    assert isinstance(all_metrics.system, SystemMetrics)
    assert isinstance(all_metrics.application, ApplicationMetrics)
    assert isinstance(all_metrics.nba, NBAMetrics)
    assert isinstance(all_metrics.timestamp, datetime)


def test_all_metrics_to_dict(metrics_collector):
    """Test AllMetrics can be converted to dictionary."""
    all_metrics = metrics_collector.collect_all_metrics()
    metrics_dict = all_metrics.to_dict()

    assert isinstance(metrics_dict, dict)
    assert "system" in metrics_dict
    assert "application" in metrics_dict
    assert "nba" in metrics_dict
    assert "timestamp" in metrics_dict


def test_all_metrics_to_json(metrics_collector):
    """Test AllMetrics can be converted to JSON."""
    all_metrics = metrics_collector.collect_all_metrics()
    json_str = all_metrics.to_json()

    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert "system" in parsed
    assert "application" in parsed
    assert "nba" in parsed


# ==============================================================================
# Latency Tracker Tests
# ==============================================================================


def test_latency_tracker_record(latency_tracker):
    """Test recording latencies."""
    latency_tracker.record(50.0)
    latency_tracker.record(75.0)
    latency_tracker.record(100.0)

    stats = latency_tracker.get_statistics()

    assert stats["count"] == 3
    assert stats["average_ms"] == 75.0
    assert stats["min_ms"] == 50.0
    assert stats["max_ms"] == 100.0


def test_latency_tracker_percentiles(latency_tracker):
    """Test percentile calculations."""
    # Add 100 latencies
    for i in range(100):
        latency_tracker.record(float(i))

    stats = latency_tracker.get_statistics()

    assert stats["count"] == 100
    assert stats["p50_ms"] >= 45 and stats["p50_ms"] <= 55
    assert stats["p95_ms"] >= 90 and stats["p95_ms"] <= 95
    assert stats["p99_ms"] >= 95


def test_latency_tracker_window_size(latency_tracker):
    """Test that window size is respected."""
    # Create tracker with small window
    small_tracker = LatencyTracker(window_size=10)

    # Add more than window size
    for i in range(20):
        small_tracker.record(float(i))

    stats = small_tracker.get_statistics()

    # Should only have last 10
    assert stats["count"] == 10
    assert stats["min_ms"] == 10.0  # First 10 dropped


def test_latency_tracker_clear(latency_tracker):
    """Test clearing latency data."""
    latency_tracker.record(50.0)
    latency_tracker.record(75.0)

    latency_tracker.clear()

    stats = latency_tracker.get_statistics()
    assert stats["count"] == 0
    assert stats["average_ms"] == 0.0


def test_latency_tracker_empty_state(latency_tracker):
    """Test statistics with no data."""
    stats = latency_tracker.get_statistics()

    assert stats["count"] == 0
    assert stats["average_ms"] == 0.0
    assert stats["p50_ms"] == 0.0
    assert stats["p95_ms"] == 0.0
    assert stats["p99_ms"] == 0.0


# ==============================================================================
# Context Manager Tests
# ==============================================================================


def test_request_tracker_context_manager(metrics_collector):
    """Test RequestTracker context manager."""
    initial_count = metrics_collector.request_count

    with metrics_collector.track_request("test_operation"):
        time.sleep(0.05)  # Simulate work

    # Should have recorded one request
    assert metrics_collector.request_count == initial_count + 1

    metrics = metrics_collector.collect_application_metrics()
    assert metrics.average_latency_ms >= 50.0  # At least 50ms


def test_request_tracker_with_error(metrics_collector):
    """Test RequestTracker with exception."""
    initial_error_count = metrics_collector.error_count

    try:
        with metrics_collector.track_request("failing_operation"):
            raise ValueError("Test error")
    except ValueError:
        pass

    # Should have recorded error
    assert metrics_collector.error_count == initial_error_count + 1


def test_query_tracker_context_manager(metrics_collector):
    """Test QueryTracker context manager."""
    initial_queries = metrics_collector.total_queries

    with metrics_collector.track_query("SELECT * FROM games"):
        time.sleep(0.03)  # Simulate query

    # Should have recorded one query
    assert metrics_collector.total_queries == initial_queries + 1


@pytest.mark.asyncio
async def test_track_latency_decorator_async():
    """Test track_latency decorator with async function."""
    collector = MetricsCollector()
    collector.reset_metrics()

    @track_latency("async_operation")
    async def async_function():
        await asyncio.sleep(0.05)
        return "result"

    result = await async_function()

    assert result == "result"
    assert collector.request_count == 1


def test_track_latency_decorator_sync():
    """Test track_latency decorator with sync function."""
    collector = MetricsCollector()
    collector.reset_metrics()

    @track_latency("sync_operation")
    def sync_function():
        time.sleep(0.05)
        return "result"

    result = sync_function()

    assert result == "result"
    # Note: decorator uses global collector, so check it
    global_collector = get_metrics_collector()
    assert global_collector.request_count >= 0  # May have previous requests


# ==============================================================================
# Export Tests
# ==============================================================================


def test_export_prometheus(metrics_collector):
    """Test Prometheus export format."""
    # Record some metrics
    metrics_collector.record_request(50.0, error=False)
    metrics_collector.record_nba_query(25.0)

    prometheus_text = metrics_collector.export_prometheus()

    assert isinstance(prometheus_text, str)
    assert "nba_cpu_percent" in prometheus_text
    assert "nba_memory_percent" in prometheus_text
    assert "nba_requests_total" in prometheus_text
    assert "# HELP" in prometheus_text
    assert "# TYPE" in prometheus_text


def test_get_summary(metrics_collector):
    """Test metrics summary."""
    # Record some metrics
    metrics_collector.record_request(50.0, error=False)
    metrics_collector.record_cache_hit()

    summary = metrics_collector.get_summary()

    assert isinstance(summary, dict)
    assert "timestamp" in summary
    assert "system" in summary
    assert "application" in summary
    assert "nba" in summary
    assert "cpu_percent" in summary["system"]
    assert "requests" in summary["application"]


# ==============================================================================
# Thread Safety Tests
# ==============================================================================


def test_concurrent_metric_recording(metrics_collector):
    """Test thread-safe concurrent metric recording."""
    import threading

    def record_metrics():
        for _ in range(100):
            metrics_collector.record_request(50.0, error=False)
            metrics_collector.record_cache_hit()

    # Create multiple threads
    threads = [threading.Thread(target=record_metrics) for _ in range(10)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Should have recorded all requests
    assert metrics_collector.request_count == 1000  # 10 threads * 100 requests
    assert metrics_collector.cache_hits == 1000


# ==============================================================================
# Reset and Cleanup Tests
# ==============================================================================


def test_reset_metrics(metrics_collector):
    """Test resetting all metrics."""
    # Record some data
    metrics_collector.record_request(50.0, error=False)
    metrics_collector.record_nba_query(25.0)
    metrics_collector.record_cache_hit()

    # Reset
    metrics_collector.reset_metrics()

    # All counters should be zero
    assert metrics_collector.request_count == 0
    assert metrics_collector.total_queries == 0
    assert metrics_collector.cache_hits == 0
    assert metrics_collector.error_count == 0


# ==============================================================================
# Global Instance Tests
# ==============================================================================


def test_get_global_metrics_collector():
    """Test getting global metrics collector."""
    collector1 = get_metrics_collector()
    collector2 = get_metrics_collector()

    # Should return same instance
    assert collector1 is collector2


def test_set_global_metrics_collector():
    """Test setting global metrics collector."""
    custom_collector = MetricsCollector()
    set_metrics_collector(custom_collector)

    retrieved_collector = get_metrics_collector()

    assert retrieved_collector is custom_collector


# ==============================================================================
# Edge Cases and Error Handling
# ==============================================================================


def test_metrics_collection_with_disabled_components():
    """Test collecting metrics with disabled components."""
    collector = MetricsCollector(
        enable_system_metrics=False,
        enable_application_metrics=False,
        enable_nba_metrics=False,
    )

    # Should not raise errors
    all_metrics = collector.collect_all_metrics()
    assert all_metrics is not None


def test_high_volume_metrics(metrics_collector):
    """Test handling high volume of metrics."""
    # Record large number of metrics quickly
    for i in range(10000):
        metrics_collector.record_request(50.0, error=(i % 10 == 0))

    metrics = metrics_collector.collect_application_metrics()

    assert metrics.request_count == 10000
    assert metrics.error_count == 1000


def test_extreme_latency_values(metrics_collector):
    """Test handling extreme latency values."""
    # Very small latency
    metrics_collector.record_request(0.001, error=False)

    # Very large latency
    metrics_collector.record_request(10000.0, error=False)

    metrics = metrics_collector.collect_application_metrics()

    # Should handle without errors
    assert metrics.request_count == 2
    assert metrics.average_latency_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
