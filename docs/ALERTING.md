# NBA MCP Server Alerting Configuration Guide

Comprehensive guide for configuring and managing alerts in the NBA MCP Server.

## Table of Contents

1. [Overview](#overview)
2. [Alert Basics](#alert-basics)
3. [Threshold Configuration](#threshold-configuration)
4. [Notification Channels](#notification-channels)
5. [Alert Management](#alert-management)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Overview

The alerting system monitors metrics and triggers notifications when thresholds are exceeded. It supports:

- **Threshold-based alerts**: Trigger when metrics cross configured values
- **Multi-severity levels**: INFO, WARNING, CRITICAL
- **Multiple channels**: Email, Slack, webhooks
- **Deduplication**: Prevents alert spam
- **Resolution tracking**: Tracks when issues are resolved

## Alert Basics

### Alert Severity Levels

| Severity | Priority | Use Case | Response Time |
|----------|----------|----------|---------------|
| **INFO** | Low | Informational events | Review during business hours |
| **WARNING** | Medium | Issues that may need attention | Review within hours |
| **CRITICAL** | High | Urgent issues requiring immediate action | Respond immediately |

### Alert Lifecycle

```
1. Threshold Exceeded → 2. Alert Created → 3. Notification Sent → 4. Alert Resolved
```

### Quick Start

```python
from mcp_server.monitoring import (
    get_alert_manager,
    register_default_thresholds,
)

# Register default thresholds
register_default_thresholds()

# Or create custom thresholds
manager = get_alert_manager()
manager.register_threshold(AlertThreshold(
    metric_name="cpu_percent",
    threshold=80.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
))

# Check thresholds
alerts = manager.check_all_thresholds()
```

## Threshold Configuration

### Creating Alert Thresholds

```python
from mcp_server.monitoring import AlertThreshold, AlertSeverity

threshold = AlertThreshold(
    metric_name="system_cpu_percent",           # Metric to monitor
    threshold=80.0,                             # Threshold value
    comparison="gt",                            # Comparison operator
    severity=AlertSeverity.WARNING,             # Alert severity
    window_seconds=60,                          # Evaluation window
    min_occurrences=3,                          # Min occurrences before alert
    enabled=True,                               # Whether threshold is active
    description="CPU usage above 80%",          # Human-readable description
)
```

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `gt` | Greater than | `value > threshold` |
| `lt` | Less than | `value < threshold` |
| `eq` | Equal to | `value == threshold` |
| `gte` | Greater than or equal | `value >= threshold` |
| `lte` | Less than or equal | `value <= threshold` |

### Recommended Thresholds

#### System Resources

```python
# CPU - Warning at 80%, Critical at 95%
manager.register_threshold(AlertThreshold(
    metric_name="system_cpu_percent",
    threshold=80.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="CPU usage elevated",
))

manager.register_threshold(AlertThreshold(
    metric_name="system_cpu_percent",
    threshold=95.0,
    comparison="gt",
    severity=AlertSeverity.CRITICAL,
    description="CPU usage critical",
))

# Memory - Warning at 90%
manager.register_threshold(AlertThreshold(
    metric_name="system_memory_percent",
    threshold=90.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Memory usage high",
))

# Disk - Warning at 85%
manager.register_threshold(AlertThreshold(
    metric_name="system_disk_usage_percent",
    threshold=85.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Disk space low",
))
```

#### Application Performance

```python
# High latency
manager.register_threshold(AlertThreshold(
    metric_name="application_p95_latency_ms",
    threshold=500.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="P95 latency above 500ms",
))

# High error rate
manager.register_threshold(AlertThreshold(
    metric_name="application_error_rate_per_minute",
    threshold=10.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Error rate elevated",
))

# Low success rate
manager.register_threshold(AlertThreshold(
    metric_name="application_success_rate_percent",
    threshold=95.0,
    comparison="lt",
    severity=AlertSeverity.CRITICAL,
    description="Success rate below 95%",
))
```

#### NBA-Specific

```python
# Stale data
manager.register_threshold(AlertThreshold(
    metric_name="nba_data_freshness_seconds",
    threshold=3600.0,  # 1 hour
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Data not updated in over 1 hour",
))

# Low cache performance
manager.register_threshold(AlertThreshold(
    metric_name="nba_cache_hit_rate_percent",
    threshold=50.0,
    comparison="lt",
    severity=AlertSeverity.WARNING,
    description="Cache hit rate below 50%",
))

# Slow queries
manager.register_threshold(AlertThreshold(
    metric_name="nba_average_query_time_ms",
    threshold=100.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Database queries running slow",
))
```

## Notification Channels

### Email Notifications

#### Configuration

```bash
# Environment variables
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="alerts@example.com"
export SMTP_PASSWORD="your-app-password"
export ALERT_FROM_EMAIL="nba-mcp-alerts@example.com"
export ALERT_TO_EMAILS="admin@example.com,ops@example.com,oncall@example.com"
```

#### Enable in Code

```python
manager = AlertManager(enable_email=True)
```

#### Email Format

```
Subject: [WARNING] High CPU Usage

NBA MCP Server Alert

Severity: WARNING
Metric: cpu_percent
Current Value: 85.50
Threshold: 80.00
Time: 2025-01-18T10:30:00Z

Message: CPU usage above 80%

Details:
{
  "comparison": "gt",
  "description": "CPU usage elevated"
}
```

### Slack Notifications

#### Setup Slack Webhook

1. Go to https://api.slack.com/apps
2. Create new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy webhook URL

#### Configuration

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
```

```python
manager = AlertManager(enable_slack=True)
```

#### Slack Message Format

Alerts appear in Slack with:
- Color coding (green=INFO, yellow=WARNING, red=CRITICAL)
- Alert title and message
- Metric details (current value, threshold)
- Timestamp

### Custom Webhooks

#### Configuration

```bash
export ALERT_WEBHOOK_URL="https://your-service.com/webhook"
```

```python
manager = AlertManager(enable_webhook=True)
```

#### Webhook Payload

```json
{
  "id": "alert_123",
  "name": "High CPU Usage",
  "message": "CPU usage above 80%",
  "severity": "warning",
  "metric_name": "cpu_percent",
  "current_value": 85.5,
  "threshold_value": 80.0,
  "timestamp": "2025-01-18T10:30:00Z",
  "tags": ["threshold", "warning"],
  "resolved": false,
  "resolved_at": null,
  "details": {
    "comparison": "gt",
    "description": "CPU usage elevated"
  }
}
```

### Multiple Notification Channels

```python
# Enable all channels
manager = AlertManager(
    enable_email=True,
    enable_slack=True,
    enable_webhook=True,
)
```

## Alert Management

### Checking Thresholds

```python
# Manual threshold check
alerts = manager.check_all_thresholds()

for alert in alerts:
    print(f"[{alert.severity.value}] {alert.name}")
    print(f"  Current: {alert.current_value:.2f}")
    print(f"  Threshold: {alert.threshold_value:.2f}")
```

### Viewing Active Alerts

```python
# Get all active alerts
active_alerts = manager.get_active_alerts()

print(f"Active alerts: {len(active_alerts)}")

for alert in active_alerts:
    if alert.severity == AlertSeverity.CRITICAL:
        print(f"🔴 CRITICAL: {alert.name}")
    elif alert.severity == AlertSeverity.WARNING:
        print(f"🟡 WARNING: {alert.name}")
```

### Alert History

```python
# Get recent alert history
history = manager.get_alert_history(limit=100)

print(f"Total alerts in history: {len(history)}")

# Analyze alert patterns
critical_count = sum(1 for a in history if a.severity == AlertSeverity.CRITICAL)
warning_count = sum(1 for a in history if a.severity == AlertSeverity.WARNING)

print(f"Critical: {critical_count}, Warnings: {warning_count}")
```

### Resolving Alerts

```python
# Resolve a specific alert
success = manager.resolve_alert(alert_id)

if success:
    print(f"Alert {alert_id} resolved")
else:
    print(f"Alert {alert_id} not found")

# Auto-resolution happens when:
# - Metric returns to normal
# - Alert is manually resolved
# - Threshold is disabled/removed
```

### Disabling Thresholds

```python
# Temporarily disable a threshold
threshold = manager.thresholds["cpu_percent"]
threshold.enabled = False

# Or unregister completely
manager.unregister_threshold("cpu_percent")
```

## Best Practices

### 1. Alert Threshold Tuning

```python
# Start conservative, tune based on actual load
initial_threshold = AlertThreshold(
    metric_name="cpu_percent",
    threshold=90.0,  # Start high
    comparison="gt",
    severity=AlertSeverity.WARNING,
)

# After observing normal load, adjust:
# - Lower threshold if never triggered
# - Raise threshold if too noisy
# - Add min_occurrences to reduce noise
```

### 2. Alert Fatigue Prevention

```python
# Use min_occurrences to avoid flapping
manager.register_threshold(AlertThreshold(
    metric_name="application_error_rate_per_minute",
    threshold=5.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    window_seconds=300,        # 5 minute window
    min_occurrences=3,         # Must occur 3 times
))

# Deduplication is automatic (5-minute window)
# Alerts for same metric won't repeat within 5 minutes
```

### 3. Severity Escalation

```python
# Use multiple thresholds with escalating severity
# WARNING at 80%
manager.register_threshold(AlertThreshold(
    metric_name="cpu_percent",
    threshold=80.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
))

# CRITICAL at 95%
manager.register_threshold(AlertThreshold(
    metric_name="cpu_percent",
    threshold=95.0,
    comparison="gt",
    severity=AlertSeverity.CRITICAL,
))
```

### 4. Actionable Alerts

```python
# Include actionable information in descriptions
manager.register_threshold(AlertThreshold(
    metric_name="disk_usage_percent",
    threshold=85.0,
    comparison="gt",
    severity=AlertSeverity.WARNING,
    description="Disk space low - cleanup logs or expand volume",
))
```

### 5. Alert Testing

```python
# Test alerts before production
test_threshold = AlertThreshold(
    metric_name="test_metric",
    threshold=0.0,  # Will always trigger
    comparison="gt",
    severity=AlertSeverity.INFO,
    description="Test alert - verify notifications work",
)

manager.register_threshold(test_threshold)
alerts = manager.check_all_thresholds()

# Verify notifications sent
# Then remove test threshold
manager.unregister_threshold("test_metric")
```

## Troubleshooting

### Alerts Not Triggering

```python
# Check if thresholds are registered
print(f"Registered thresholds: {len(manager.thresholds)}")

# Check current metric values
metrics = collector.collect_all_metrics()
print(f"CPU: {metrics.system.cpu_percent}%")

# Manually check threshold
threshold = manager.thresholds["cpu_percent"]
current_value = metrics.system.cpu_percent
would_trigger = threshold.evaluate(current_value)
print(f"Would trigger: {would_trigger}")
```

### Notifications Not Received

```python
# Verify notification channels are enabled
print(f"Email enabled: {manager.enable_email}")
print(f"Slack enabled: {manager.enable_slack}")

# Check environment variables
import os
print(f"SMTP_USER: {os.getenv('SMTP_USER', 'NOT SET')}")
print(f"SLACK_WEBHOOK_URL: {os.getenv('SLACK_WEBHOOK_URL', 'NOT SET')}")

# Test email configuration
from mcp_server.monitoring import AlertManager
test_manager = AlertManager(enable_email=True)
# Trigger test alert and check logs for errors
```

### Too Many Alerts

```python
# Increase thresholds
threshold.threshold = 85.0  # was 80.0

# Add minimum occurrences
threshold.min_occurrences = 5  # was 3

# Increase window size
threshold.window_seconds = 600  # was 300

# Or disable noisy alerts
threshold.enabled = False
```

### Alert Deduplication Issues

```python
# Check last alert time
last_time = manager.last_alert_time.get("cpu_percent")
if last_time:
    from datetime import datetime
    time_since = datetime.now() - last_time
    print(f"Last alert: {time_since.total_seconds()}s ago")

# Adjust deduplication window (default: 5 minutes)
manager.min_alert_interval = timedelta(minutes=10)
```

---

**Related Documentation:**
- [MONITORING.md](./MONITORING.md) - Complete monitoring guide
- [METRICS.md](./METRICS.md) - Metrics reference
- See `mcp_server/monitoring_integration_example.py` for examples
