# Model Monitoring Guide

**Complete guide to drift detection, performance tracking, and alerting**

---

## Table of Contents

1. [Monitoring Basics](#monitoring-basics)
2. [Drift Detection](#drift-detection)
3. [Performance Tracking](#performance-tracking)
4. [Alerting System](#alerting-system)
5. [MLflow Integration](#mlflow-integration)
6. [Production Monitoring Patterns](#production-monitoring-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Monitoring Basics

### Initialization

```python
from mcp_server.model_monitoring import ModelMonitor

# Basic initialization
monitor = ModelMonitor(
    model_id="nba_win_predictor",
    model_version="v1.0",
    drift_threshold=0.05,          # P-value threshold for drift detection
    performance_threshold=0.1,      # Performance degradation threshold
    error_rate_threshold=0.1,       # Maximum acceptable error rate
    latency_threshold_ms=1000.0,    # Maximum acceptable latency
    enable_mlflow=True,
    mlflow_experiment="nba_monitoring"
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | str | Required | Model identifier |
| `model_version` | str | Required | Model version |
| `drift_threshold` | float | 0.05 | P-value threshold for drift (0-1) |
| `performance_threshold` | float | 0.1 | Performance degradation threshold |
| `error_rate_threshold` | float | 0.1 | Error rate alert threshold |
| `latency_threshold_ms` | float | 1000.0 | Latency alert threshold in ms |
| `enable_mlflow` | bool | False | Enable MLflow integration |
| `alert_callback` | callable | None | Function called when alerts generated |

### Logging Predictions

```python
# Log a prediction for monitoring
monitor.log_prediction(
    prediction_id="pred_20251025_001",
    features={
        "home_ppg": 112.5,
        "away_ppg": 108.3,
        "home_def_rating": 105.2
    },
    prediction=0.68,           # Model prediction
    actual=1.0,                # Actual outcome (if available)
    latency_ms=45.2,           # Prediction latency
    error=None                 # Error message (if any)
)

# View prediction history
history = monitor.get_prediction_history(hours=24)
print(f"Predictions in last 24h: {len(history)}")
```

---

## Drift Detection

Drift detection identifies when your model's input data distribution changes significantly from the reference distribution.

### Setting Reference Data

First, establish a reference distribution:

```python
import pandas as pd

# Load reference data (training data or production baseline)
reference_data = pd.read_csv("reference_features.csv")

# Set as reference
monitor.set_reference_data(
    features=reference_data,
    predictions=reference_predictions  # Optional
)

print(f"Reference data set: {len(reference_data)} samples")
```

### Drift Detection Methods

Three methods available:

1. **Kolmogorov-Smirnov (KS) Test**: Statistical test comparing distributions
2. **Population Stability Index (PSI)**: Measures distribution shift
3. **Kullback-Leibler (KL) Divergence**: Information-theoretic measure

### 1. KS Test (Recommended for Continuous Features)

```python
from mcp_server.model_monitoring import DriftMethod

# Get current production data
current_data = get_recent_production_features()

# Detect drift using KS test
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.KS_TEST
)

# Analyze results
for result in drift_results:
    if result.is_drift:
        print(f"⚠️  Drift detected in {result.feature_name}:")
        print(f"   KS statistic: {result.drift_score:.4f}")
        print(f"   P-value: {result.p_value:.4f}")
        print(f"   Threshold: {result.threshold}")
```

**When to use:**
- Continuous numerical features
- Need statistical significance (p-value)
- Comparing distributions directly

**Interpretation:**
- `p_value < threshold`: Significant drift detected
- Lower p-value = stronger evidence of drift

### 2. PSI (Recommended for Categorical Features)

```python
# Detect drift using PSI
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.PSI
)

for result in drift_results:
    if result.is_drift:
        print(f"⚠️  Drift in {result.feature_name}:")
        print(f"   PSI: {result.drift_score:.4f}")

        # PSI interpretation
        if result.drift_score < 0.1:
            level = "No significant change"
        elif result.drift_score < 0.2:
            level = "Small shift"
        else:
            level = "Large shift"

        print(f"   Level: {level}")
```

**PSI Thresholds:**
- `< 0.1`: No significant population change
- `0.1 - 0.2`: Small population shift (monitor)
- `> 0.2`: Large population shift (action required)

**When to use:**
- Categorical or binned features
- Industry standard for model monitoring
- Easy interpretation

### 3. KL Divergence (Recommended for Probability Distributions)

```python
# Detect drift using KL divergence
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.KL_DIVERGENCE
)

for result in drift_results:
    print(f"{result.feature_name}: KL={result.drift_score:.4f}")
```

**When to use:**
- Measuring information loss
- Comparing probability distributions
- Asymmetric drift detection (direction matters)

**Interpretation:**
- `KL = 0`: Identical distributions
- `KL > 0`: Distributions differ (higher = more different)

### Drift Detection on Specific Features

```python
# Check only specific features
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.KS_TEST,
    features=['home_ppg', 'away_ppg', 'home_def_rating']
)
```

### Drift History

```python
# Get all drift checks
history = monitor.get_drift_history()

# Get drift history for specific feature
ppg_drift = monitor.get_drift_history(
    feature='home_ppg',
    hours=168  # Last week
)

# Plot drift over time
import matplotlib.pyplot as plt

timestamps = [d.timestamp for d in ppg_drift]
drift_scores = [d.drift_score for d in ppg_drift]

plt.plot(timestamps, drift_scores)
plt.axhline(y=monitor.drift_threshold, color='r', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Drift Score')
plt.title('Feature Drift Over Time: home_ppg')
plt.show()
```

---

## Performance Tracking

Monitor model performance metrics over time.

### Calculate Performance Metrics

```python
# Calculate performance for last 24 hours
metrics = monitor.calculate_performance(window_hours=24)

print(f"Performance Metrics (24h):")
print(f"  Total Predictions: {metrics.total_predictions}")
print(f"  Accuracy: {metrics.accuracy:.2%}" if metrics.accuracy else "  Accuracy: N/A")
print(f"  Average Latency: {metrics.avg_latency_ms:.2f}ms")
print(f"  Error Rate: {metrics.error_rate:.2%}")
```

### Performance Metrics Available

| Metric | Description | Calculation |
|--------|-------------|-------------|
| `total_predictions` | Total predictions in window | Count of predictions |
| `accuracy` | Classification accuracy | Correct / Total (requires actuals) |
| `precision` | Precision score | TP / (TP + FP) |
| `recall` | Recall score | TP / (TP + FN) |
| `f1_score` | F1 score | 2 * (precision * recall) / (precision + recall) |
| `avg_latency_ms` | Average latency | Mean of all latencies |
| `error_rate` | Error rate | Errors / Total |

### Performance Over Time

```python
# Track performance at regular intervals
import time

while True:
    # Calculate current performance
    metrics = monitor.calculate_performance(window_hours=1)

    # Log to monitoring system
    log_metrics({
        'timestamp': datetime.now(),
        'accuracy': metrics.accuracy,
        'latency': metrics.avg_latency_ms,
        'error_rate': metrics.error_rate
    })

    # Wait 1 hour
    time.sleep(3600)
```

### Performance History

```python
# Get performance history
history = monitor.get_performance_history(hours=168)  # Last week

# Analyze trends
accuracies = [h.accuracy for h in history if h.accuracy is not None]
latencies = [h.avg_latency_ms for h in history]

print(f"Accuracy trend: {np.mean(accuracies):.2%} ± {np.std(accuracies):.2%}")
print(f"Latency trend: {np.mean(latencies):.2f}ms ± {np.std(latencies):.2f}ms")

# Detect degradation
if len(accuracies) > 1:
    recent_accuracy = np.mean(accuracies[-10:])
    baseline_accuracy = np.mean(accuracies[:10])

    if recent_accuracy < baseline_accuracy - 0.05:
        print("⚠️  Performance degradation detected!")
```

---

## Alerting System

Automated alerting for drift and performance issues.

### Alert Types

```python
from mcp_server.model_monitoring import AlertType, AlertSeverity

# Available alert types:
# - FEATURE_DRIFT: Feature distribution drift
# - PREDICTION_DRIFT: Prediction distribution drift
# - PERFORMANCE_DEGRADATION: Model performance drop
# - HIGH_ERROR_RATE: Error rate exceeded threshold
# - HIGH_LATENCY: Latency exceeded threshold
```

### Getting Alerts

```python
# Get all unacknowledged alerts
alerts = monitor.get_alerts(acknowledged=False)

for alert in alerts:
    print(f"\n[{alert.severity.value.upper()}] {alert.alert_type.value}")
    print(f"  Message: {alert.message}")
    print(f"  Time: {alert.timestamp}")
    print(f"  Details: {alert.details}")
```

### Filtering Alerts

```python
# Get critical alerts only
critical_alerts = monitor.get_alerts(
    severity=AlertSeverity.CRITICAL,
    acknowledged=False
)

# Get drift alerts
drift_alerts = monitor.get_alerts(
    alert_type=AlertType.FEATURE_DRIFT,
    hours=24  # Last 24 hours
)

# Get recent alerts
recent_alerts = monitor.get_alerts(hours=1)
```

### Acknowledging Alerts

```python
# Acknowledge an alert
alert_id = alerts[0].alert_id
success = monitor.acknowledge_alert(alert_id)

if success:
    print(f"Alert {alert_id} acknowledged")
```

### Custom Alert Callback

```python
def alert_handler(alert):
    """Custom alert handler"""

    # Send email
    if alert.severity == AlertSeverity.CRITICAL:
        send_email(
            to="data-science-team@example.com",
            subject=f"Critical Alert: {alert.alert_type.value}",
            body=alert.message
        )

    # Send Slack notification
    send_slack_message(
        channel="#ml-alerts",
        message=f"⚠️  {alert.message}",
        severity=alert.severity.value
    )

    # Create incident ticket
    if alert.alert_type == AlertType.PERFORMANCE_DEGRADATION:
        create_jira_ticket(
            title=f"Model Performance Issue: {alert.details}",
            priority="High"
        )

# Initialize monitor with callback
monitor = ModelMonitor(
    model_id="nba_model",
    model_version="v1.0",
    alert_callback=alert_handler
)
```

### Alert Dashboard

```python
def create_alert_dashboard(monitor):
    """Create alert summary dashboard"""

    # Get alerts
    all_alerts = monitor.get_alerts(hours=168)  # Last week

    # Group by type
    alerts_by_type = {}
    for alert in all_alerts:
        alert_type = alert.alert_type.value
        if alert_type not in alerts_by_type:
            alerts_by_type[alert_type] = []
        alerts_by_type[alert_type].append(alert)

    # Print summary
    print("\n=== Alert Dashboard (7 days) ===\n")

    for alert_type, alerts in alerts_by_type.items():
        count = len(alerts)
        unacked = len([a for a in alerts if not a.acknowledged])

        print(f"{alert_type}:")
        print(f"  Total: {count}")
        print(f"  Unacknowledged: {unacked}")
        print(f"  Acknowledged: {count - unacked}")
        print()

# Usage
create_alert_dashboard(monitor)
```

---

## MLflow Integration

Track monitoring metrics in MLflow for long-term analysis.

### Automatic MLflow Logging

When `enable_mlflow=True`, metrics are automatically logged:

```python
monitor = ModelMonitor(
    model_id="nba_model",
    model_version="v1.0",
    enable_mlflow=True,
    mlflow_experiment="nba_monitoring"
)

# Drift detection automatically logs to MLflow
drift_results = monitor.detect_feature_drift(current_data, DriftMethod.KS_TEST)
# Logs: features_checked, features_drifted, drift_rate

# Performance calculation automatically logs to MLflow
metrics = monitor.calculate_performance(window_hours=24)
# Logs: accuracy, error_rate, avg_latency_ms, total_predictions
```

### View Metrics in MLflow

```python
from mcp_server.mlflow_integration import get_mlflow_tracker

tracker = get_mlflow_tracker(experiment_name="nba_monitoring")

# Search runs
runs = tracker.search_runs(filter_string="metrics.drift_rate > 0.1")

for run in runs:
    print(f"Run {run.info.run_id}:")
    print(f"  Drift Rate: {run.data.metrics['drift_rate']:.2%}")
    print(f"  Features Drifted: {run.data.metrics['features_drifted']}")
```

### Custom MLflow Metrics

```python
# Log additional metrics manually
if monitor.enable_mlflow and monitor.mlflow_tracker:
    with monitor.mlflow_tracker.start_run("custom_metrics") as run_id:
        monitor.mlflow_tracker.log_metrics({
            "custom_metric_1": value1,
            "custom_metric_2": value2
        })
```

---

## Production Monitoring Patterns

### 1. Continuous Monitoring Loop

```python
import time
from datetime import datetime

def continuous_monitor(monitor, check_interval_minutes=60):
    """Continuously monitor model in production"""

    while True:
        try:
            print(f"\n[{datetime.now()}] Running monitoring checks...")

            # 1. Check for drift
            current_data = fetch_recent_production_data(hours=24)
            drift_results = monitor.detect_feature_drift(
                current_data=current_data,
                method=DriftMethod.KS_TEST
            )

            drifted = [r for r in drift_results if r.is_drift]
            if drifted:
                print(f"⚠️  {len(drifted)} features drifting!")
                for r in drifted:
                    print(f"   - {r.feature_name}")

            # 2. Calculate performance
            perf = monitor.calculate_performance(window_hours=24)
            print(f"✓ Performance: accuracy={perf.accuracy:.2%}, "
                  f"error_rate={perf.error_rate:.2%}")

            # 3. Check for critical alerts
            critical = monitor.get_alerts(
                severity=AlertSeverity.CRITICAL,
                acknowledged=False
            )

            if critical:
                print(f"🚨 {len(critical)} critical alerts!")
                for alert in critical:
                    handle_critical_alert(alert)

        except Exception as e:
            print(f"Monitoring error: {e}")

        # Wait before next check
        time.sleep(check_interval_minutes * 60)

# Run in background
import threading
monitor_thread = threading.Thread(
    target=continuous_monitor,
    args=(monitor, 60),  # Check every hour
    daemon=True
)
monitor_thread.start()
```

### 2. Scheduled Drift Reports

```python
def generate_drift_report(monitor, period_hours=168):
    """Generate weekly drift report"""

    # Get drift history
    history = monitor.get_drift_history(hours=period_hours)

    # Group by feature
    by_feature = {}
    for drift in history:
        if drift.feature_name not in by_feature:
            by_feature[drift.feature_name] = []
        by_feature[drift.feature_name].append(drift)

    # Generate report
    report = f"\n=== Drift Report ({period_hours}h) ===\n\n"

    for feature, drifts in by_feature.items():
        drift_count = sum(1 for d in drifts if d.is_drift)
        drift_rate = drift_count / len(drifts) if drifts else 0

        report += f"{feature}:\n"
        report += f"  Checks: {len(drifts)}\n"
        report += f"  Drift detected: {drift_count} ({drift_rate:.1%})\n"

        if drift_count > 0:
            avg_score = np.mean([d.drift_score for d in drifts if d.is_drift])
            report += f"  Avg drift score: {avg_score:.4f}\n"

        report += "\n"

    return report

# Schedule weekly reports
import schedule

def send_weekly_report():
    report = generate_drift_report(monitor, period_hours=168)
    send_email(to="team@example.com", subject="Weekly Drift Report", body=report)

schedule.every().monday.at("09:00").do(send_weekly_report)
```

### 3. Real-time Alerting Pipeline

```python
class MonitoringPipeline:
    """Real-time monitoring and alerting pipeline"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.alert_thresholds = {
            'drift_rate': 0.2,        # 20% of features drifting
            'error_rate': 0.05,       # 5% error rate
            'latency_p95': 500.0,     # 500ms p95 latency
        }

    def process_prediction(self, prediction_id, features, prediction, actual=None):
        """Process a single prediction through monitoring pipeline"""

        start_time = time.time()

        # Log prediction
        self.monitor.log_prediction(
            prediction_id=prediction_id,
            features=features,
            prediction=prediction,
            actual=actual,
            latency_ms=(time.time() - start_time) * 1000
        )

        # Real-time checks (every N predictions)
        if self.should_check():
            self.run_checks()

    def should_check(self):
        """Determine if we should run checks"""
        # Check every 1000 predictions or every hour
        history = self.monitor.get_prediction_history(hours=1)
        return len(history) % 1000 == 0

    def run_checks(self):
        """Run monitoring checks"""

        # Check performance
        perf = self.monitor.calculate_performance(window_hours=1)

        if perf.error_rate > self.alert_thresholds['error_rate']:
            self.trigger_alert(
                f"High error rate: {perf.error_rate:.2%}",
                severity=AlertSeverity.CRITICAL
            )

        # Check for drift (hourly)
        current_data = self.get_recent_features()
        drift_results = self.monitor.detect_feature_drift(
            current_data=current_data,
            method=DriftMethod.KS_TEST
        )

        drift_rate = sum(1 for r in drift_results if r.is_drift) / len(drift_results)
        if drift_rate > self.alert_thresholds['drift_rate']:
            self.trigger_alert(
                f"High drift rate: {drift_rate:.2%}",
                severity=AlertSeverity.WARNING
            )

    def trigger_alert(self, message, severity):
        """Trigger an alert"""
        print(f"[{severity.value.upper()}] {message}")
        # Send to alerting system
        send_to_pagerduty(message, severity)

# Usage
pipeline = MonitoringPipeline(monitor)

# Process predictions
for pred_id, features, prediction in prediction_stream:
    pipeline.process_prediction(pred_id, features, prediction)
```

---

## Best Practices

### 1. Choose Appropriate Thresholds

```python
# Start conservative, adjust based on false positive rate
monitor = ModelMonitor(
    model_id="nba_model",
    model_version="v1.0",
    drift_threshold=0.01,          # Strict (more sensitive)
    error_rate_threshold=0.02,     # 2% error rate
    latency_threshold_ms=200.0     # 200ms max latency
)

# After monitoring for a week, adjust:
# - If too many false positives → increase thresholds
# - If missing real issues → decrease thresholds
```

### 2. Monitor at Multiple Time Scales

```python
# Short-term (real-time issues)
hourly_perf = monitor.calculate_performance(window_hours=1)

# Medium-term (daily trends)
daily_perf = monitor.calculate_performance(window_hours=24)

# Long-term (weekly patterns)
weekly_perf = monitor.calculate_performance(window_hours=168)

# Compare across time scales
if hourly_perf.error_rate > 2 * daily_perf.error_rate:
    print("⚠️  Sudden spike in errors!")
```

### 3. Use Reference Data from Production

```python
# Option 1: Use training data (baseline)
training_data = pd.read_csv("training_features.csv")
monitor.set_reference_data(features=training_data)

# Option 2: Use early production data (more realistic)
# Collect first 2 weeks of production data
early_production = collect_production_features(days=14)
monitor.set_reference_data(features=early_production)

# Option 3: Update reference periodically (adaptive)
def update_reference_monthly():
    """Update reference data monthly"""
    last_month = collect_production_features(days=30)
    monitor.set_reference_data(features=last_month)

schedule.every().month.do(update_reference_monthly)
```

### 4. Combine Multiple Drift Methods

```python
def comprehensive_drift_check(monitor, current_data):
    """Check drift using multiple methods"""

    methods = [
        DriftMethod.KS_TEST,
        DriftMethod.PSI,
        DriftMethod.KL_DIVERGENCE
    ]

    all_results = {}
    for method in methods:
        results = monitor.detect_feature_drift(
            current_data=current_data,
            method=method
        )
        all_results[method] = results

    # Feature is drifting if detected by 2+ methods
    features_drifting = set()
    for method, results in all_results.items():
        for r in results:
            if r.is_drift:
                features_drifting.add(r.feature_name)

    return features_drifting

# Usage
drifting = comprehensive_drift_check(monitor, current_data)
if drifting:
    print(f"⚠️  Drift confirmed in: {drifting}")
```

### 5. Log All Predictions with Actuals

```python
# At prediction time
prediction_id = generate_prediction_id()
monitor.log_prediction(
    prediction_id=prediction_id,
    features=features,
    prediction=prediction,
    actual=None,  # Not available yet
    latency_ms=latency
)

# Later, when actual is available
def update_with_actual(prediction_id, actual_value):
    """Update prediction with actual value"""
    # Find prediction in history
    history = monitor.get_prediction_history()
    for pred in history:
        if pred.prediction_id == prediction_id:
            pred.actual = actual_value
            break

# For NBA: Update after game completes
game_result = wait_for_game_completion(game_id)
update_with_actual(prediction_id, game_result)
```

---

## Troubleshooting

### High False Positive Rate for Drift

**Problem:** Too many drift alerts, but manual review shows no real drift

**Solutions:**
```python
# 1. Increase drift threshold
monitor.drift_threshold = 0.01  # More sensitive
monitor.drift_threshold = 0.10  # Less sensitive

# 2. Use different drift method
# KS test may be too sensitive for your data
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.PSI  # Try PSI instead
)

# 3. Increase sample size
# Ensure current_data has enough samples (1000+)
if len(current_data) < 1000:
    print("Sample size too small for reliable drift detection")
```

### Missing Drift Detection

**Problem:** Real drift not being detected

**Solutions:**
```python
# 1. Check reference data is appropriate
print(f"Reference samples: {len(monitor.reference_features)}")
print(f"Reference date range: {get_date_range(monitor.reference_features)}")

# 2. Use more sensitive threshold
monitor.drift_threshold = 0.01  # More sensitive

# 3. Check feature distributions
for feature in features:
    print(f"{feature}:")
    print(f"  Reference: {monitor.reference_features[feature].describe()}")
    print(f"  Current: {current_data[feature].describe()}")
```

### Inaccurate Performance Metrics

**Problem:** Accuracy metrics don't match expectations

**Solutions:**
```python
# 1. Verify actuals are being logged
history = monitor.get_prediction_history(include_errors=False)
with_actuals = [p for p in history if p.actual is not None]

print(f"Predictions with actuals: {len(with_actuals)} / {len(history)}")

# 2. Check for data lag
# Ensure actuals are updated within reasonable time

# 3. Verify prediction/actual format consistency
for pred in history[:5]:
    print(f"Prediction: {pred.prediction} (type: {type(pred.prediction)})")
    print(f"Actual: {pred.actual} (type: {type(pred.actual)})")
```

---

## Monitoring Checklist

- [ ] Set appropriate reference data
- [ ] Configure thresholds based on use case
- [ ] Enable MLflow logging for long-term tracking
- [ ] Set up alert callbacks for critical issues
- [ ] Log all predictions with features and actuals
- [ ] Run drift detection regularly (daily/weekly)
- [ ] Calculate performance metrics continuously
- [ ] Review and acknowledge alerts promptly
- [ ] Update reference data periodically
- [ ] Monitor at multiple time scales
- [ ] Document threshold changes and rationale
- [ ] Test monitoring in staging before production

---

**Document Status:** COMPLETE
**Last Updated:** October 25, 2025
