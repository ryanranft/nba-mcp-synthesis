# NBA MCP Server Monitoring Guide

Comprehensive guide for monitoring the NBA MCP Server using the integrated monitoring infrastructure.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Health Monitoring](#health-monitoring)
5. [Metrics Collection](#metrics-collection)
6. [Alerting System](#alerting-system)
7. [Real-time Dashboard](#real-time-dashboard)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

## Overview

The NBA MCP Server monitoring system provides comprehensive observability into system performance, health, and business metrics. It consists of four main components:

- **Metrics Collection** - Tracks system, application, and NBA-specific metrics
- **Health Monitoring** - Performs periodic health checks on all components
- **Alerting System** - Triggers notifications when thresholds are exceeded
- **Real-time Dashboard** - Provides live visualization of metrics and health status

### Key Features

- **Minimal Overhead**: <5% CPU impact from metrics collection
- **Real-time Monitoring**: Updates every 1-60 seconds
- **Prometheus Integration**: Standard Prometheus export format
- **Multi-channel Alerts**: Email, Slack, webhook notifications
- **Production-ready**: Thread-safe, auto-recovery, graceful degradation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NBA MCP Server                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Metrics     │  │   Health     │  │    Alert     │      │
│  │  Collector   │→ │   Monitor    │→ │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          Real-time Monitoring Dashboard              │    │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                     ↓
  ┌───────────┐      ┌─────────────┐      ┌──────────────┐
  │Prometheus │      │  Web         │      │ Notification │
  │  Scraper  │      │  Dashboard   │      │  Channels    │
  └───────────┘      └─────────────┘      └──────────────┘
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- psutil package (for system metrics)
- boto3 (for S3 health checks)
- Access to database and S3 storage

### Basic Setup

```python
from mcp_server.nba_metrics import get_metrics_collector
from mcp_server.monitoring import get_health_monitor, get_alert_manager
from mcp_server.monitoring_dashboard import get_dashboard

# Initialize components
collector = get_metrics_collector()
monitor = get_health_monitor()
manager = get_alert_manager()
dashboard = get_dashboard()

# Start monitoring
monitor.start()  # Start automatic health checks
dashboard.start()  # Start dashboard updates
```

### Environment Variables

```bash
# Alert notifications (optional)
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export ALERT_FROM_EMAIL="alerts@nba-mcp.com"
export ALERT_TO_EMAILS="admin@example.com,ops@example.com"

# Slack webhook (optional)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Custom webhook (optional)
export ALERT_WEBHOOK_URL="https://your-monitoring-service.com/webhook"

# S3 configuration
export S3_BUCKET_NAME="nba-mcp-data"
```

## Health Monitoring

### Running Health Checks

#### Manual Health Checks

```python
from mcp_server.monitoring import get_health_monitor

monitor = get_health_monitor()

# Run all health checks
checks = monitor.run_all_checks()

# Print results
for check in checks:
    print(f"{check.name}: {check.status.value} - {check.message}")

# Get overall health
overall = monitor.get_overall_health()
print(f"Overall Status: {overall.status.value}")
print(f"Healthy: {overall.healthy_count}/{len(overall.checks)}")
```

#### Automatic Health Checks

```python
# Start automatic health checking (every 30 seconds)
monitor.start()

# Stop automatic health checking
monitor.stop()
```

### Health Check Components

The health monitor checks these components:

1. **Database** - PostgreSQL connectivity and query performance
2. **S3 Storage** - AWS S3 bucket accessibility
3. **System Resources** - CPU, memory, disk utilization
4. **Application** - Request latency, error rates, throughput
5. **NBA Data** - Data freshness, cache hit rate, query performance

### Health Status Levels

- **HEALTHY**: Component functioning normally
- **DEGRADED**: Component functional but experiencing issues
- **UNHEALTHY**: Component not functioning correctly
- **UNKNOWN**: Component health cannot be determined

### HTTP Health Endpoint

Integrate with load balancers and orchestrators:

```python
# Flask example
from flask import Flask, jsonify
from mcp_server.monitoring import get_health_monitor

app = Flask(__name__)

@app.route('/health')
def health():
    monitor = get_health_monitor()
    health = monitor.get_overall_health()

    status_code = 200 if health.status.is_healthy else 503

    return jsonify(health.to_dict()), status_code

# FastAPI example
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get('/health')
async def health():
    monitor = get_health_monitor()
    health = monitor.get_overall_health()

    status_code = 200 if health.status.is_healthy else 503

    return JSONResponse(
        content=health.to_dict(),
        status_code=status_code
    )
```

## Metrics Collection

### Available Metrics

#### System Metrics

- CPU utilization percentage
- Memory usage (total, used, available)
- Disk I/O (read/write bytes and operations)
- Disk usage percentage
- Network I/O (bytes sent/received, packets, errors)
- Open file handles and connections

#### Application Metrics

- Total request count
- Active request count
- Request rate (requests/second)
- Latency percentiles (P50, P95, P99)
- Error count and rate
- Success rate percentage
- Total processing time

#### NBA-Specific Metrics

- Database queries per second
- Total query count
- Average query latency
- Cache hit rate
- Data freshness (age in seconds)
- Active tool executions
- Tool success rate
- Games/players processed
- S3 operations (reads/writes)
- Active database connections

### Collecting Metrics

```python
from mcp_server.nba_metrics import get_metrics_collector

collector = get_metrics_collector()

# Collect all metrics
metrics = collector.collect_all_metrics()

# Access specific metric types
print(f"CPU: {metrics.system.cpu_percent}%")
print(f"Memory: {metrics.system.memory_percent}%")
print(f"Requests: {metrics.application.request_count}")
print(f"P95 Latency: {metrics.application.p95_latency_ms}ms")
print(f"Cache Hit Rate: {metrics.nba.cache_hit_rate_percent}%")

# Export as JSON
json_data = metrics.to_json()

# Export for Prometheus
prometheus_data = collector.export_prometheus()
```

### Recording Custom Metrics

```python
# Record a request
collector.record_request(latency_ms=125.5, error=False)

# Record a database query
collector.record_nba_query(latency_ms=45.2)

# Record cache operations
collector.record_cache_hit()
collector.record_cache_miss()

# Record tool execution
collector.record_tool_execution(success=True)

# Record data processing
collector.record_game_processed()
collector.record_player_processed()

# Record S3 operations
collector.record_s3_read()
collector.record_s3_write()

# Update data freshness
collector.record_data_update()
```

### Using Context Managers

```python
# Automatic request tracking
with collector.track_request("process_game_stats"):
    # Your code here
    result = process_game_stats()

# Automatic query tracking
with collector.track_query("SELECT * FROM games"):
    # Your database query
    results = db.execute(query)

# Using decorators
from mcp_server.nba_metrics import track_latency

@track_latency("expensive_operation")
async def expensive_operation():
    await asyncio.sleep(1)
    return "result"
```

## Alerting System

### Registering Alert Thresholds

```python
from mcp_server.monitoring import (
    get_alert_manager,
    AlertThreshold,
    AlertSeverity,
)

manager = get_alert_manager()

# CPU usage alert
manager.register_threshold(AlertThreshold(
    metric_name="system_cpu_percent",
    threshold=80.0,
    comparison="gt",  # greater than
    severity=AlertSeverity.WARNING,
    description="CPU usage above 80%",
    window_seconds=60,
    min_occurrences=3,
))

# Memory usage alert (critical)
manager.register_threshold(AlertThreshold(
    metric_name="system_memory_percent",
    threshold=90.0,
    comparison="gt",
    severity=AlertSeverity.CRITICAL,
    description="Memory usage critically high",
))

# Low cache hit rate
manager.register_threshold(AlertThreshold(
    metric_name="nba_cache_hit_rate_percent",
    threshold=50.0,
    comparison="lt",  # less than
    severity=AlertSeverity.WARNING,
    description="Cache performance degraded",
))

# High latency
manager.register_threshold(AlertThreshold(
    metric_name="application_p95_latency_ms",
    threshold=500.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Response time degraded",
))
```

### Checking Thresholds

```python
# Check all registered thresholds
triggered_alerts = manager.check_all_thresholds()

for alert in triggered_alerts:
    print(f"[{alert.severity.value.upper()}] {alert.name}")
    print(f"  {alert.message}")
    print(f"  Current: {alert.current_value:.2f}, Threshold: {alert.threshold_value:.2f}")

# Get active alerts
active = manager.get_active_alerts()
print(f"Active alerts: {len(active)}")

# Resolve an alert
manager.resolve_alert(alert.id)
```

### Default Alert Thresholds

Quick setup with sensible defaults:

```python
from mcp_server.monitoring import register_default_thresholds

# Registers default thresholds for:
# - CPU > 80% (warning), > 95% (critical)
# - Memory > 90% (warning)
# - Disk > 85% (warning)
# - P95 latency > 500ms (warning)
# - Error rate > 10/min (warning)
# - Success rate < 95% (critical)
# - Data age > 1 hour (warning)
# - Cache hit rate < 50% (warning)
register_default_thresholds()
```

### Notification Channels

#### Email Alerts

Configured via environment variables:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="alerts@example.com"
export SMTP_PASSWORD="app-password"
export ALERT_TO_EMAILS="admin@example.com,ops@example.com"
```

Enable in code:

```python
manager = AlertManager(enable_email=True)
```

#### Slack Alerts

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK"
```

```python
manager = AlertManager(enable_slack=True)
```

#### Custom Webhook

```bash
export ALERT_WEBHOOK_URL="https://your-service.com/webhook"
```

```python
manager = AlertManager(enable_webhook=True)
```

## Real-time Dashboard

### Starting the Dashboard

```python
from mcp_server.monitoring_dashboard import get_dashboard

dashboard = get_dashboard()

# Start background updates (every 5 seconds)
dashboard.start()

# Access dashboard data
snapshot = dashboard.get_snapshot()
health_summary = dashboard.get_health_summary()
metrics_summary = dashboard.get_metrics_summary()
alerts_summary = dashboard.get_alerts_summary()

# Stop dashboard
dashboard.stop()
```

### Dashboard API

```python
from mcp_server.monitoring_dashboard import DashboardAPI

api = DashboardAPI(dashboard)

# API endpoints (integrate with Flask/FastAPI)
health_data = api.get_health()
metrics_data = api.get_metrics()
alerts_data = api.get_alerts()
snapshot_data = api.get_snapshot()

# Time series data
cpu_series = api.get_time_series("cpu_percent", hours=1)
```

### Recording Game Events

```python
from mcp_server.monitoring_dashboard import GameEvent
from datetime import datetime

event = GameEvent(
    game_id="game_123",
    event_type="shot",
    timestamp=datetime.now(),
    player_id="player_456",
    team_id="LAL",
    description="LeBron James makes 3-pointer",
    data={"points": 3, "quarter": 1}
)

dashboard.record_game_event(event)

# Retrieve recent events
recent_events = dashboard.get_recent_game_events(limit=50)
```

### Exporting Dashboard Data

```python
# Export to JSON file
dashboard.export_dashboard_data("/path/to/export.json")

# Get dashboard statistics
stats = dashboard.get_statistics()
print(f"Total Updates: {stats['total_updates']}")
print(f"Uptime: {stats['uptime_seconds']}s")
```

## Best Practices

### 1. Metric Collection

- Use context managers for automatic tracking
- Record metrics at appropriate granularity
- Don't over-collect (keep overhead <5%)
- Use sampling for high-frequency operations

### 2. Health Monitoring

- Run health checks every 30-60 seconds
- Set appropriate timeouts for checks
- Monitor trends, not just current state
- Implement graceful degradation

### 3. Alerting

- Start with default thresholds, tune based on load
- Use severity levels appropriately
- Avoid alert fatigue (deduplicate, aggregate)
- Set up escalation policies

### 4. Dashboard

- Keep update intervals reasonable (5-60s)
- Limit historical data retention
- Export data periodically for archival
- Monitor dashboard performance

## Troubleshooting

### High Metrics Collection Overhead

```python
# Reduce collection frequency
collector = MetricsCollector(
    enable_system_metrics=True,
    enable_application_metrics=True,
    enable_nba_metrics=False,  # Disable if not needed
    latency_window_size=1000,  # Reduce window size
)
```

### Health Checks Failing

```bash
# Check database connectivity
python -c "from mcp_server.connectors.db import get_db_connection; print(get_db_connection())"

# Check S3 access
aws s3 ls s3://nba-mcp-data/

# Check system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"
```

### Missing Alerts

```python
# Verify thresholds are registered
manager = get_alert_manager()
print(f"Registered thresholds: {len(manager.thresholds)}")

# Check if alerts are being triggered
alerts = manager.check_all_thresholds()
print(f"Triggered alerts: {len(alerts)}")

# Verify notification channels are configured
print(f"Email enabled: {manager.enable_email}")
print(f"Slack enabled: {manager.enable_slack}")
```

### Dashboard Not Updating

```python
# Check if dashboard is running
dashboard = get_dashboard()
stats = dashboard.get_statistics()
print(f"Running: {stats['running']}")
print(f"Total updates: {stats['total_updates']}")

# Manually trigger update
dashboard._update_data()
```

## Advanced Configuration

### Custom Metrics Collector

```python
collector = MetricsCollector(
    enable_system_metrics=True,
    enable_application_metrics=True,
    enable_nba_metrics=True,
    collection_interval=60,
    latency_window_size=10000,
)

set_metrics_collector(collector)
```

### Custom Health Monitor

```python
monitor = HealthMonitor(
    check_interval=30,
    enable_auto_checks=True,
    metrics_collector=collector,
)

set_health_monitor(monitor)
```

### Custom Alert Manager

```python
manager = AlertManager(
    enable_email=True,
    enable_slack=True,
    enable_webhook=False,
    metrics_collector=collector,
)

set_alert_manager(manager)
```

### Prometheus Integration

```bash
# Add to prometheus.yml
scrape_configs:
  - job_name: 'nba-mcp-server'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

```python
# Serve metrics endpoint
from flask import Flask, Response
from mcp_server.nba_metrics import get_metrics_collector

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    collector = get_metrics_collector()
    prometheus_data = collector.export_prometheus()
    return Response(prometheus_data, mimetype='text/plain')

app.run(host='0.0.0.0', port=8080)
```

---

**For more information:**
- See [METRICS.md](./METRICS.md) for detailed metrics reference
- See [ALERTING.md](./ALERTING.md) for alert configuration guide
- See integration examples in `mcp_server/monitoring_integration_example.py`
