"""
NBA MCP Server Monitoring Integration Examples

Comprehensive examples demonstrating how to integrate monitoring, metrics,
and alerting into the NBA MCP Server. Shows common patterns and best practices
for production deployments.

This module provides 5 key integration patterns:
1. Basic metrics collection
2. Health check endpoints
3. Custom alert configuration
4. Real-time dashboard
5. Integration with existing tools

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List

# Import monitoring infrastructure
from .nba_metrics import (
    MetricsCollector,
    get_metrics_collector,
    track_latency,
)
from .monitoring import (
    HealthMonitor,
    AlertManager,
    AlertThreshold,
    AlertSeverity,
    HealthStatus,
    get_health_monitor,
    get_alert_manager,
    register_default_thresholds,
)
from .monitoring_dashboard import (
    MonitoringDashboard,
    GameEvent,
    get_dashboard,
)
from .error_handling import (
    get_error_handler,
    with_retry,
)
from .logging_config import (
    get_logger,
    RequestContext,
)

logger = get_logger(__name__)


# ==============================================================================
# PATTERN 1: Basic Metrics Collection
# ==============================================================================


def example_basic_metrics_collection():
    """
    Example: Basic metrics collection and reporting.

    Demonstrates how to:
    - Collect system, application, and NBA metrics
    - Access individual metric components
    - Export metrics in different formats
    - Track metrics over time
    """
    print("\n" + "=" * 80)
    print("PATTERN 1: Basic Metrics Collection")
    print("=" * 80 + "\n")

    # Get the global metrics collector
    collector = get_metrics_collector()

    # Collect all metrics
    print("1. Collecting all metrics...")
    metrics = collector.collect_all_metrics()

    # Access system metrics
    print(f"\n2. System Metrics:")
    print(f"   CPU Usage: {metrics.system.cpu_percent:.1f}%")
    print(f"   Memory Usage: {metrics.system.memory_percent:.1f}%")
    print(f"   Disk Usage: {metrics.system.disk_usage_percent:.1f}%")
    print(f"   CPU Cores: {metrics.system.cpu_count}")

    # Access application metrics
    print(f"\n3. Application Metrics:")
    print(f"   Total Requests: {metrics.application.request_count}")
    print(f"   Active Requests: {metrics.application.active_requests}")
    print(f"   Error Count: {metrics.application.error_count}")
    print(f"   Success Rate: {metrics.application.success_rate_percent:.1f}%")
    print(f"   Avg Latency: {metrics.application.average_latency_ms:.2f}ms")
    print(f"   P95 Latency: {metrics.application.p95_latency_ms:.2f}ms")
    print(f"   P99 Latency: {metrics.application.p99_latency_ms:.2f}ms")

    # Access NBA-specific metrics
    print(f"\n4. NBA Metrics:")
    print(f"   Total Queries: {metrics.nba.total_queries}")
    print(f"   Queries/Second: {metrics.nba.queries_per_second:.2f}")
    print(f"   Cache Hit Rate: {metrics.nba.cache_hit_rate_percent:.1f}%")
    print(f"   Data Age: {metrics.nba.data_freshness_seconds:.0f}s")
    print(f"   Tool Success Rate: {metrics.nba.tool_success_rate_percent:.1f}%")

    # Export in different formats
    print("\n5. Export Formats:")

    # JSON export
    json_export = metrics.to_json()
    print(f"   JSON: {len(json_export)} characters")

    # Prometheus export
    prometheus_export = collector.export_prometheus()
    print(f"   Prometheus: {len(prometheus_export.splitlines())} lines")

    # Summary export
    summary = collector.get_summary()
    print(f"   Summary: {len(summary)} keys")
    print(f"   {summary}")

    print("\n✅ Basic metrics collection completed")


# ==============================================================================
# PATTERN 2: Health Check Endpoint
# ==============================================================================


def example_health_check_endpoint():
    """
    Example: Health check endpoint implementation.

    Demonstrates how to:
    - Run comprehensive health checks
    - Get overall system health status
    - Check individual component health
    - Integrate with load balancers/orchestrators
    """
    print("\n" + "=" * 80)
    print("PATTERN 2: Health Check Endpoint")
    print("=" * 80 + "\n")

    # Get the global health monitor
    monitor = get_health_monitor()

    # Run all health checks
    print("1. Running comprehensive health checks...")
    checks = monitor.run_all_checks()

    print(f"\n2. Individual Check Results:")
    for check in checks:
        status_symbol = "✅" if check.is_healthy() else "❌"
        print(f"   {status_symbol} {check.name}: {check.status.value}")
        print(f"      Message: {check.message}")
        print(f"      Response Time: {check.response_time_ms:.2f}ms")

    # Get overall health
    print("\n3. Overall System Health:")
    overall_health = monitor.get_overall_health()
    print(f"   Status: {overall_health.status.value}")
    print(f"   Healthy: {overall_health.healthy_count}/{len(overall_health.checks)}")
    print(f"   Degraded: {overall_health.degraded_count}")
    print(f"   Unhealthy: {overall_health.unhealthy_count}")

    # Check if system is healthy
    if overall_health.status == HealthStatus.HEALTHY:
        print("\n   ✅ System is HEALTHY - ready to accept traffic")
        return_code = 200
    elif overall_health.status == HealthStatus.DEGRADED:
        print("\n   ⚠️  System is DEGRADED - operating but experiencing issues")
        return_code = 200
    else:
        print("\n   ❌ System is UNHEALTHY - not ready for traffic")
        return_code = 503

    # Get failing checks
    print("\n4. Failing Checks:")
    failing = monitor.get_failing_checks()
    if failing:
        for check in failing:
            print(f"   ⚠️  {check.name}: {check.message}")
    else:
        print("   ✅ No failing checks")

    # Example: Integration with web framework
    print("\n5. Integration Example (HTTP endpoint):")
    print(
        f"""
   # Flask example:
   @app.route('/health')
   def health():
       monitor = get_health_monitor()
       health = monitor.get_overall_health()

       return jsonify(health.to_dict()), {return_code}

   # FastAPI example:
   @app.get('/health')
   async def health():
       monitor = get_health_monitor()
       health = monitor.get_overall_health()

       return JSONResponse(
           content=health.to_dict(),
           status_code={return_code}
       )
    """
    )

    print("\n✅ Health check endpoint example completed")


# ==============================================================================
# PATTERN 3: Custom Alert Configuration
# ==============================================================================


def example_custom_alert_configuration():
    """
    Example: Custom alert configuration and management.

    Demonstrates how to:
    - Register custom alert thresholds
    - Configure alert severity levels
    - Set up alert notifications
    - Check thresholds and trigger alerts
    """
    print("\n" + "=" * 80)
    print("PATTERN 3: Custom Alert Configuration")
    print("=" * 80 + "\n")

    # Get the global alert manager
    manager = get_alert_manager()

    # Register default thresholds
    print("1. Registering default alert thresholds...")
    register_default_thresholds()
    print("   ✅ Default thresholds registered")

    # Register custom thresholds
    print("\n2. Registering custom NBA-specific thresholds...")

    # Low cache hit rate alert
    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_cache_hit_rate_percent",
            threshold=30.0,
            comparison="lt",
            severity=AlertSeverity.CRITICAL,
            description="Cache hit rate critically low - performance impact expected",
            window_seconds=300,
            min_occurrences=3,
        )
    )
    print("   ✅ Cache hit rate threshold registered")

    # High query latency alert
    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_average_query_time_ms",
            threshold=100.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="Database queries running slower than expected",
            window_seconds=60,
            min_occurrences=5,
        )
    )
    print("   ✅ Query latency threshold registered")

    # Stale data alert
    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_data_freshness_seconds",
            threshold=7200.0,  # 2 hours
            comparison="gt",
            severity=AlertSeverity.CRITICAL,
            description="NBA data has not been updated in over 2 hours",
            window_seconds=600,
            min_occurrences=1,
        )
    )
    print("   ✅ Data freshness threshold registered")

    # Tool failure rate alert
    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_tool_success_rate_percent",
            threshold=90.0,
            comparison="lt",
            severity=AlertSeverity.WARNING,
            description="Tool success rate below 90%",
            window_seconds=300,
            min_occurrences=2,
        )
    )
    print("   ✅ Tool success rate threshold registered")

    # Check all thresholds
    print("\n3. Checking all thresholds...")
    triggered_alerts = manager.check_all_thresholds()

    if triggered_alerts:
        print(f"   ⚠️  {len(triggered_alerts)} alert(s) triggered:")
        for alert in triggered_alerts:
            severity_symbol = "🔴" if alert.severity == AlertSeverity.CRITICAL else "🟡"
            print(f"   {severity_symbol} [{alert.severity.value.upper()}] {alert.name}")
            print(f"      {alert.message}")
    else:
        print("   ✅ No alerts triggered - all metrics within thresholds")

    # Get active alerts
    print("\n4. Active Alerts:")
    active_alerts = manager.get_active_alerts()
    if active_alerts:
        for alert in active_alerts:
            print(f"   ⚠️  {alert.name}")
            print(f"      Severity: {alert.severity.value}")
            print(f"      Triggered: {alert.timestamp.isoformat()}")
    else:
        print("   ✅ No active alerts")

    # Example: Resolve an alert
    if active_alerts:
        print("\n5. Resolving an alert...")
        alert_to_resolve = active_alerts[0]
        manager.resolve_alert(alert_to_resolve.id)
        print(f"   ✅ Resolved: {alert_to_resolve.name}")

    print("\n✅ Custom alert configuration completed")


# ==============================================================================
# PATTERN 4: Real-Time Dashboard
# ==============================================================================


def example_real_time_dashboard():
    """
    Example: Real-time monitoring dashboard.

    Demonstrates how to:
    - Start the monitoring dashboard
    - Get current dashboard snapshot
    - Access time series data
    - Track game events
    - Export dashboard data
    """
    print("\n" + "=" * 80)
    print("PATTERN 4: Real-Time Dashboard")
    print("=" * 80 + "\n")

    # Get the global dashboard
    dashboard = get_dashboard()

    # Start the dashboard
    print("1. Starting dashboard background updates...")
    dashboard.start()
    print("   ✅ Dashboard started")

    # Give it a moment to collect some data
    time.sleep(2)

    # Get current snapshot
    print("\n2. Getting current dashboard snapshot...")
    snapshot = dashboard.get_snapshot()
    print(f"   Timestamp: {snapshot.timestamp.isoformat()}")
    print(f"   Health Status: {snapshot.health['status']}")
    print(f"   Active Alerts: {len(snapshot.active_alerts)}")

    # Get health summary
    print("\n3. Health Summary:")
    health_summary = dashboard.get_health_summary()
    print(f"   Overall: {health_summary['overall_status']}")
    print(f"   Healthy: {health_summary['healthy_count']}")
    print(f"   Degraded: {health_summary['degraded_count']}")
    print(f"   Unhealthy: {health_summary['unhealthy_count']}")
    print(f"   Uptime: {health_summary['uptime_seconds']:.0f}s")

    # Get metrics summary
    print("\n4. Metrics Summary:")
    metrics_summary = dashboard.get_metrics_summary()
    print(f"   CPU: {metrics_summary['system']['cpu_percent']:.1f}%")
    print(f"   Memory: {metrics_summary['system']['memory_percent']:.1f}%")
    print(f"   Requests: {metrics_summary['requests']['total']}")
    print(f"   P95 Latency: {metrics_summary['latency']['p95_ms']:.2f}ms")
    print(f"   Cache Hit Rate: {metrics_summary['nba']['cache_hit_rate']:.1f}%")

    # Get time series data
    print("\n5. Time Series Data:")
    cpu_series = dashboard.get_time_series("cpu_percent", minutes=5)
    if cpu_series:
        print(f"   CPU (last 5 min): {len(cpu_series.values)} data points")
        if cpu_series.values:
            print(f"   Latest: {cpu_series.values[-1]:.1f}%")

    # Record some game events
    print("\n6. Recording game events...")
    events = [
        GameEvent(
            game_id="game_001",
            event_type="shot",
            timestamp=datetime.now(),
            player_id="player_123",
            team_id="LAL",
            description="LeBron James makes 3-pointer",
        ),
        GameEvent(
            game_id="game_001",
            event_type="rebound",
            timestamp=datetime.now(),
            player_id="player_456",
            team_id="BOS",
            description="Jayson Tatum defensive rebound",
        ),
    ]

    for event in events:
        dashboard.record_game_event(event)
    print(f"   ✅ Recorded {len(events)} game events")

    # Get recent events
    recent_events = dashboard.get_recent_game_events(limit=10)
    print(f"\n7. Recent Game Events: {len(recent_events)}")
    for event in recent_events[-2:]:
        print(f"   📊 {event['description']}")

    # Export dashboard data
    print("\n8. Exporting dashboard data...")
    export_path = "/tmp/nba_dashboard_export.json"
    dashboard.export_dashboard_data(export_path)
    print(f"   ✅ Exported to {export_path}")

    # Dashboard statistics
    print("\n9. Dashboard Statistics:")
    stats = dashboard.get_statistics()
    print(f"   Running: {stats['running']}")
    print(f"   Total Updates: {stats['total_updates']}")
    print(f"   Metrics History: {stats['metrics_history_count']} entries")
    print(f"   Time Series: {stats['time_series_count']} metrics")

    print("\n✅ Real-time dashboard example completed")


# ==============================================================================
# PATTERN 5: Integration with Existing Tools
# ==============================================================================


def example_integration_with_existing_tools():
    """
    Example: Integration with existing error handling and logging.

    Demonstrates how to:
    - Integrate metrics with error handling
    - Use monitoring with existing logging
    - Track tool execution with metrics
    - Combine retry logic with monitoring
    - Use context managers for automatic tracking
    """
    print("\n" + "=" * 80)
    print("PATTERN 5: Integration with Existing Tools")
    print("=" * 80 + "\n")

    # Get infrastructure instances
    collector = get_metrics_collector()
    error_handler = get_error_handler()

    # Example 1: Track a database query with metrics
    print("1. Database Query with Metrics Tracking:")

    async def query_database_with_metrics(query: str):
        """Example: Database query with automatic metrics tracking."""
        with collector.track_query(query):
            # Simulate database query
            await asyncio.sleep(0.05)  # 50ms query

            # Record successful query
            collector.record_nba_query(latency_ms=50.0)

            return {"rows": 100}

    # Run the example
    result = asyncio.run(query_database_with_metrics("SELECT * FROM games"))
    print(f"   ✅ Query completed: {result['rows']} rows")
    print(f"   📊 Total queries: {collector.total_queries}")

    # Example 2: Track request with automatic error handling
    print("\n2. Request with Metrics and Error Handling:")

    @track_latency("process_game_stats")
    @with_retry(max_retries=3)
    async def process_game_stats(game_id: str):
        """Example: Process game stats with monitoring."""
        # Track that we're processing a game
        collector.record_game_processed()

        # Simulate processing
        await asyncio.sleep(0.1)

        # Record tool execution
        collector.record_tool_execution(success=True)

        return {"game_id": game_id, "stats_processed": True}

    # Run the example
    result = asyncio.run(process_game_stats("game_123"))
    print(f"   ✅ Processed game: {result['game_id']}")
    print(f"   📊 Games processed: {collector.games_processed}")
    print(f"   📊 Tool executions: {collector.tool_executions}")

    # Example 3: Cache operations with metrics
    print("\n3. Cache Operations with Metrics:")

    def get_from_cache(key: str) -> Any:
        """Example: Cache lookup with metrics."""
        # Simulate cache lookup
        import random

        cache_hit = random.random() > 0.5

        if cache_hit:
            collector.record_cache_hit()
            print(f"   ✅ Cache HIT for key: {key}")
            return {"data": "cached_value"}
        else:
            collector.record_cache_miss()
            print(f"   ❌ Cache MISS for key: {key}")
            return None

    # Try a few cache lookups
    for i in range(5):
        get_from_cache(f"player_{i}")

    metrics = collector.collect_nba_metrics()
    print(f"\n   📊 Cache Statistics:")
    print(f"      Hits: {metrics.cache_hits}")
    print(f"      Misses: {metrics.cache_misses}")
    print(f"      Hit Rate: {metrics.cache_hit_rate_percent:.1f}%")

    # Example 4: S3 operations tracking
    print("\n4. S3 Operations Tracking:")

    async def upload_to_s3(filename: str, data: bytes):
        """Example: S3 upload with metrics."""
        # Record S3 write
        collector.record_s3_write()

        # Simulate upload
        await asyncio.sleep(0.2)

        print(f"   ✅ Uploaded to S3: {filename}")

    async def download_from_s3(filename: str):
        """Example: S3 download with metrics."""
        # Record S3 read
        collector.record_s3_read()

        # Simulate download
        await asyncio.sleep(0.15)

        print(f"   ✅ Downloaded from S3: {filename}")
        return b"file_data"

    # Run S3 operations
    asyncio.run(upload_to_s3("game_stats.json", b"{}"))
    asyncio.run(download_from_s3("player_data.json"))

    print(f"\n   📊 S3 Operations:")
    print(f"      Reads: {collector.s3_reads}")
    print(f"      Writes: {collector.s3_writes}")

    # Example 5: Complete request flow with logging
    print("\n5. Complete Request Flow:")

    async def handle_api_request(request_id: str, operation: str):
        """Example: Full request handling with monitoring."""
        # Use request context for logging
        with RequestContext(logger, operation, request_id=request_id):
            # Track the request
            with collector.track_request(operation):
                try:
                    # Simulate work
                    await asyncio.sleep(0.1)

                    # Record successful request
                    collector.record_request(latency_ms=100.0, error=False)

                    logger.info(f"Request completed successfully: {operation}")

                except Exception as e:
                    # Record failed request
                    collector.record_request(latency_ms=100.0, error=True)

                    logger.error(f"Request failed: {operation}", exc_info=True)
                    raise

    # Run request
    asyncio.run(handle_api_request("req_789", "get_player_stats"))

    print(f"\n   ✅ Request completed with full monitoring")

    app_metrics = collector.collect_application_metrics()
    print(f"\n   📊 Application Metrics:")
    print(f"      Total Requests: {app_metrics.request_count}")
    print(f"      Errors: {app_metrics.error_count}")
    print(f"      Success Rate: {app_metrics.success_rate_percent:.1f}%")

    print("\n✅ Integration with existing tools completed")


# ==============================================================================
# Main Example Runner
# ==============================================================================


def run_all_examples():
    """
    Run all integration examples.

    This demonstrates the complete monitoring infrastructure:
    - Metrics collection
    - Health checks
    - Alert configuration
    - Real-time dashboard
    - Tool integration
    """
    print("\n" + "=" * 80)
    print("NBA MCP SERVER MONITORING INTEGRATION EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating 5 key integration patterns:")
    print("1. Basic Metrics Collection")
    print("2. Health Check Endpoint")
    print("3. Custom Alert Configuration")
    print("4. Real-Time Dashboard")
    print("5. Integration with Existing Tools")
    print("\n" + "=" * 80)

    try:
        # Run all examples
        example_basic_metrics_collection()
        example_health_check_endpoint()
        example_custom_alert_configuration()
        example_real_time_dashboard()
        example_integration_with_existing_tools()

        # Final summary
        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)

        # Get final metrics
        collector = get_metrics_collector()
        final_metrics = collector.get_summary()

        print("\n📊 Final Metrics Summary:")
        print(f"   CPU: {final_metrics['system']['cpu_percent']:.1f}%")
        print(f"   Memory: {final_metrics['system']['memory_percent']:.1f}%")
        print(f"   Requests: {final_metrics['application']['requests']}")
        print(f"   Errors: {final_metrics['application']['errors']}")
        print(f"   Success Rate: {final_metrics['application']['success_rate']:.1f}%")
        print(f"   Cache Hit Rate: {final_metrics['nba']['cache_hit_rate']:.1f}%")

        print("\n✅ Monitoring infrastructure is ready for production!")
        print("\nNext steps:")
        print("1. Review the examples above")
        print("2. Integrate patterns into your code")
        print("3. Configure alert thresholds for your use case")
        print("4. Set up notification channels (email, Slack, etc.)")
        print("5. Deploy dashboard for real-time monitoring")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run all examples
    run_all_examples()
