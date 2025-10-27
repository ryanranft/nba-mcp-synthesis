# NBA MCP Model Deployment & Serving

**Phase 10A Week 2 - Agent 6: Model Deployment & Serving**

Complete model deployment infrastructure with production-ready serving, versioning, registry, and monitoring capabilities.

---

## Overview

This system provides comprehensive model deployment infrastructure for the NBA MCP Synthesis project. It integrates with Week 1 infrastructure (error handling, monitoring, RBAC) and MLflow for complete observability and lifecycle management.

### Key Components

1. **Model Serving** (`mcp_server/model_serving.py`)
   - Multi-version serving with active version management
   - A/B testing with configurable traffic routing
   - Circuit breaker pattern for fault tolerance
   - Health checks and readiness probes
   - Thread-safe concurrent request handling
   - Comprehensive metrics tracking

2. **Model Registry** (`mcp_server/model_registry.py`)
   - Centralized model catalog with versioning
   - Lifecycle management (dev → staging → production)
   - Model comparison with metric diffs
   - MLflow Model Registry sync
   - Model lineage tracking
   - Advanced search capabilities

3. **Model Versioning** (`mcp_server/model_versioning.py`)
   - Version management with MLflow integration
   - Production promotion workflows
   - Rollback capabilities
   - Version comparison and analysis
   - Mock mode for testing

4. **Model Monitoring** (`mcp_server/model_monitoring.py`)
   - Prediction logging and tracking
   - Feature drift detection (KS test, PSI, KL divergence)
   - Prediction drift detection
   - Performance tracking (accuracy, latency, error rate)
   - Alert generation with configurable thresholds
   - MLflow metrics logging

---

## Quick Start

### 1. Model Serving

```python
from mcp_server.model_serving import ModelServingManager

# Initialize serving manager
manager = ModelServingManager(
    enable_mlflow=True,
    mlflow_experiment="nba_serving",
    mock_mode=False
)

# Deploy a model
success = manager.deploy_model(
    model_id="nba_win_predictor",
    version="v1.0",
    model_instance=trained_model,
    set_active=True
)

# Make predictions
result = manager.predict(
    model_id="nba_win_predictor",
    inputs=[{
        "home_ppg": 112.5,
        "away_ppg": 108.3,
        "home_def_rating": 105.2
    }]
)

print(f"Prediction: {result}")
```

### 2. A/B Testing

```python
# Deploy two model versions
manager.deploy_model(
    model_id="nba_win_predictor",
    version="v1.0",
    model_instance=model_v1
)

manager.deploy_model(
    model_id="nba_win_predictor",
    version="v2.0",
    model_instance=model_v2
)

# Setup A/B test (70% v1.0, 30% v2.0)
manager.setup_ab_test(
    model_id="nba_win_predictor",
    versions=["v1.0", "v2.0"],
    weights=[0.7, 0.3]
)

# Predictions automatically routed based on weights
for _ in range(100):
    result = manager.predict(
        model_id="nba_win_predictor",
        inputs=[game_data]
    )
```

### 3. Model Registry

```python
from mcp_server.model_registry import ModelRegistry, ModelStage

# Initialize registry
registry = ModelRegistry(
    registry_dir="./model_registry",
    enable_mlflow=True
)

# Register a model
registry.register_model(
    model_id="nba_win_predictor",
    version="v1.0",
    stage=ModelStage.DEVELOPMENT,
    framework="sklearn",
    algorithm="RandomForest",
    metrics={"accuracy": 0.92, "f1_score": 0.89},
    hyperparameters={"n_estimators": 100, "max_depth": 10}
)

# Promote to production
registry.promote_model(
    model_id="nba_win_predictor",
    version="v1.0",
    target_stage=ModelStage.PRODUCTION
)

# Get production model
prod_model = registry.get_model(
    model_id="nba_win_predictor",
    stage=ModelStage.PRODUCTION
)
```

### 4. Model Monitoring

```python
from mcp_server.model_monitoring import ModelMonitor, DriftMethod
import pandas as pd

# Initialize monitor
monitor = ModelMonitor(
    model_id="nba_win_predictor",
    model_version="v1.0",
    drift_threshold=0.05,
    enable_mlflow=True
)

# Set reference data for drift detection
reference_data = pd.DataFrame({
    'home_ppg': [110.2, 115.3, 108.9, ...],
    'away_ppg': [107.5, 112.1, 109.3, ...],
    'home_def_rating': [105.2, 103.8, 106.1, ...]
})

monitor.set_reference_data(features=reference_data)

# Log predictions
monitor.log_prediction(
    prediction_id="pred_001",
    features={"home_ppg": 112.5, "away_ppg": 108.3},
    prediction=0.68,
    actual=1.0,  # After game completes
    latency_ms=45.2
)

# Detect drift
current_data = get_recent_game_features()
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.KS_TEST
)

for result in drift_results:
    if result.is_drift:
        print(f"Drift detected in {result.feature_name}: "
              f"score={result.drift_score:.4f}")

# Calculate performance
metrics = monitor.calculate_performance(window_hours=24)
print(f"24h Performance: accuracy={metrics.accuracy:.2f}, "
      f"error_rate={metrics.error_rate:.2%}")
```

---

## Architecture

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                     Model Deployment System                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌────────────┐│
│  │   Registry   │◄────►│  Versioning  │◄────►│   MLflow   ││
│  │              │      │              │      │  Registry  ││
│  └──────┬───────┘      └──────┬───────┘      └────────────┘│
│         │                     │                              │
│         │ register            │ load                         │
│         ▼                     ▼                              │
│  ┌──────────────────────────────────────┐                   │
│  │       Model Serving Manager          │                   │
│  │  ┌────────────┐  ┌────────────────┐ │                   │
│  │  │  Version   │  │   A/B Testing  │ │                   │
│  │  │ Management │  │   & Routing    │ │                   │
│  │  └────────────┘  └────────────────┘ │                   │
│  │  ┌────────────┐  ┌────────────────┐ │                   │
│  │  │  Circuit   │  │  Health Checks │ │                   │
│  │  │  Breaker   │  │   & Metrics    │ │                   │
│  │  └────────────┘  └────────────────┘ │                   │
│  └──────────────┬───────────────────────┘                   │
│                 │                                            │
│                 │ predictions                                │
│                 ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │        Model Monitor                 │                   │
│  │  ┌────────────┐  ┌────────────────┐ │                   │
│  │  │   Drift    │  │  Performance   │ │                   │
│  │  │ Detection  │  │   Tracking     │ │                   │
│  │  └────────────┘  └────────────────┘ │                   │
│  │  ┌────────────┐  ┌────────────────┐ │                   │
│  │  │  Alerting  │  │    Metrics     │ │                   │
│  │  │   System   │  │    Logging     │ │                   │
│  │  └────────────┘  └────────────────┘ │                   │
│  └──────────────────────────────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  Week 1  │        │  MLflow  │        │   NBA    │
  │  Error   │        │ Tracking │        │   API    │
  │ Handling │        │          │        │          │
  └──────────┘        └──────────┘        └──────────┘
```

### Data Flow

1. **Model Registration Flow**
   ```
   Train Model → Register in Registry → Version in MLflow → Deploy to Serving
   ```

2. **Prediction Flow**
   ```
   Request → Serving Manager → Model Selection (A/B) → Prediction → Monitor → Response
   ```

3. **Monitoring Flow**
   ```
   Predictions → Monitor → Drift Detection → Alerts → MLflow Metrics
   ```

---

## Features

### Model Serving Features

- **Multi-Version Serving**: Deploy and manage multiple model versions simultaneously
- **Active Version Management**: Set and switch active versions dynamically
- **A/B Testing**: Configure traffic routing with percentage-based weights
- **Circuit Breaker**: Automatic failover on high error rates
- **Health Checks**: Comprehensive health monitoring with status endpoints
- **Metrics Tracking**: Detailed metrics for requests, latency, and errors
- **Thread Safety**: Safe for concurrent serving scenarios
- **MLflow Integration**: Track deployments and A/B tests in MLflow

### Registry Features

- **Lifecycle Management**: Manage models through dev → staging → production
- **Version Tracking**: Complete version history with metadata
- **Model Comparison**: Compare models with automatic metric diff calculation
- **Advanced Search**: Search by framework, stage, metrics, and tags
- **Lineage Tracking**: Track parent-child relationships between models
- **MLflow Sync**: Synchronize with MLflow Model Registry
- **Persistence**: Automatic save/load of registry state

### Monitoring Features

- **Drift Detection**: 3 methods (KS test, PSI, KL divergence)
- **Performance Tracking**: Accuracy, latency, error rate over time
- **Alert System**: Configurable alerts with severity levels
- **Prediction Logging**: Complete prediction history with features and actuals
- **MLflow Metrics**: Automatic logging of drift and performance metrics
- **Thread Safety**: Safe for concurrent monitoring

---

## Production Patterns

### 1. Blue-Green Deployment

```python
# Deploy new version (green)
manager.deploy_model(
    model_id="nba_model",
    version="v2.0",
    model_instance=new_model,
    set_active=False  # Don't set active yet
)

# Test new version
test_results = run_tests_on_version("v2.0")

if test_results.passed:
    # Switch to new version
    manager.set_active_version(
        model_id="nba_model",
        version="v2.0"
    )
    # Old version (v1.0) still available for rollback
else:
    # Keep old version active
    manager.retire_model("nba_model", "v2.0")
```

### 2. Canary Deployment

```python
# Start with 5% traffic to new version
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.95, 0.05]
)

# Monitor for 1 hour
time.sleep(3600)
metrics = monitor.calculate_performance(window_hours=1)

if metrics.error_rate < 0.01:
    # Gradually increase traffic
    manager.setup_ab_test(
        model_id="nba_model",
        versions=["v1.0", "v2.0"],
        weights=[0.7, 0.3]  # 30% traffic
    )
```

### 3. Shadow Deployment

```python
# Deploy shadow model (predictions not returned to users)
shadow_manager = ModelServingManager(
    enable_mlflow=True,
    shadow_mode=True
)

shadow_manager.deploy_model(
    model_id="nba_model_shadow",
    version="v2.0",
    model_instance=new_model
)

# Compare predictions
for input_data in production_traffic:
    # Production prediction
    prod_pred = manager.predict("nba_model", [input_data])

    # Shadow prediction (not returned)
    shadow_pred = shadow_manager.predict("nba_model_shadow", [input_data])

    # Log comparison
    comparison_logger.log(prod_pred, shadow_pred)
```

### 4. Circuit Breaker Pattern

```python
# Configure circuit breaker
manager = ModelServingManager(
    error_threshold=0.1,  # Trip at 10% error rate
    enable_mlflow=True
)

# Circuit breaker automatically trips on high errors
try:
    result = manager.predict("nba_model", [input_data])
except Exception as e:
    # Circuit breaker may be open
    health = manager.health_check("nba_model")

    if health.circuit_breaker_open:
        # Use fallback model or cached predictions
        result = fallback_prediction(input_data)
    else:
        raise

# Manual reset if needed
manager.reset_circuit_breaker("nba_model", "v1.0")
```

---

## Integration with Week 1

All deployment components integrate with Week 1 infrastructure:

```python
# Error handling
@handle_errors(reraise=True, notify=True)
def deploy_model(...):
    # Automatic error handling and notification
    ...

# Metrics tracking
@track_metric("model_serving.predict")
def predict(...):
    # Automatic metric collection
    ...

# RBAC
@require_permission(Permission.WRITE)
def promote_model(...):
    # Access control
    ...
```

### Week 1 Features Available

- **Error Handling**: Automatic error catching, logging, and notification
- **Monitoring**: Built-in metrics collection and tracking
- **RBAC**: Role-based access control for sensitive operations
- **Logging**: Structured logging with context
- **Alerting**: Integration with alerting system

---

## Integration with MLflow

### Model Registry Sync

```python
from mcp_server.model_registry import ModelRegistry

registry = ModelRegistry(enable_mlflow=True)

# Register automatically syncs to MLflow Model Registry
registry.register_model(
    model_id="nba_model",
    version="v1.0",
    stage=ModelStage.PRODUCTION,
    # ... other parameters
)

# MLflow Model Registry updated with:
# - Model version
# - Stage (None, Staging, Production, Archived)
# - Tags and metadata
```

### Serving Metrics

```python
from mcp_server.model_serving import ModelServingManager

manager = ModelServingManager(enable_mlflow=True)

# Deployments logged to MLflow
manager.deploy_model(...)  # Creates MLflow run

# A/B tests logged to MLflow
manager.setup_ab_test(...)  # Logs configuration

# Metrics automatically tracked:
# - Prediction count
# - Latency
# - Error rate
# - A/B test performance
```

### Monitoring Metrics

```python
from mcp_server.model_monitoring import ModelMonitor

monitor = ModelMonitor(enable_mlflow=True)

# Drift metrics logged to MLflow
drift_results = monitor.detect_feature_drift(...)
# Logs: features_checked, features_drifted, drift_rate

# Performance metrics logged to MLflow
metrics = monitor.calculate_performance(...)
# Logs: accuracy, error_rate, avg_latency_ms
```

---

## Testing

### Unit Tests

```bash
# Test model serving
pytest tests/test_model_serving.py -v

# Test model registry
pytest tests/test_model_registry.py -v

# Test model versioning
pytest tests/test_model_versioning.py -v

# Test model monitoring
pytest tests/test_model_monitoring.py -v
```

### Integration Tests

```bash
# Run all deployment tests
pytest tests/test_model_*.py -v

# With coverage
pytest tests/test_model_*.py --cov=mcp_server --cov-report=html
```

### Mock Mode

All components support mock mode for testing without external dependencies:

```python
# Mock serving (no MLflow required)
manager = ModelServingManager(mock_mode=True)

# Mock registry (no file system writes)
registry = ModelRegistry(mock_mode=True)

# Mock monitoring (no MLflow required)
monitor = ModelMonitor(mock_mode=True)
```

---

## Configuration

### Environment Variables

```bash
# MLflow configuration
export MLFLOW_TRACKING_URI="http://localhost:5000"
export MLFLOW_EXPERIMENT_NAME="nba_deployment"

# Model registry
export MODEL_REGISTRY_DIR="./model_registry"
export ENABLE_MLFLOW_REGISTRY="true"

# Monitoring
export DRIFT_THRESHOLD="0.05"
export ERROR_RATE_THRESHOLD="0.1"
export LATENCY_THRESHOLD_MS="1000"
```

### Configuration Files

```python
# deployment_config.py
from dataclasses import dataclass

@dataclass
class DeploymentConfig:
    """Deployment configuration"""

    # Serving
    enable_mlflow: bool = True
    error_threshold: float = 0.1
    health_check_interval_sec: int = 60

    # Registry
    registry_dir: str = "./model_registry"
    enable_mlflow_registry: bool = True

    # Monitoring
    drift_threshold: float = 0.05
    performance_threshold: float = 0.1
    error_rate_threshold: float = 0.1
    latency_threshold_ms: float = 1000.0
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

### Quick Diagnostics

```python
# Check serving health
health = manager.health_check("nba_model")
print(f"Status: {health.status}")
print(f"Circuit Breaker: {health.circuit_breaker_open}")

# Check registry state
stats = registry.get_statistics()
print(f"Total models: {stats['total_models']}")
print(f"Production models: {stats['production_count']}")

# Check monitoring alerts
alerts = monitor.get_alerts(severity=AlertSeverity.CRITICAL)
for alert in alerts:
    print(f"{alert.alert_type}: {alert.message}")
```

---

## Best Practices

1. **Always use version tags**: Use semantic versioning (v1.0, v1.1, v2.0)
2. **Test before production**: Use staging environment for validation
3. **Monitor continuously**: Set up drift detection and performance tracking
4. **Use circuit breakers**: Configure error thresholds for automatic failover
5. **Keep model registry clean**: Retire old, unused models
6. **Document model changes**: Use descriptions and tags in registry
7. **Log all predictions**: Enable comprehensive monitoring
8. **Set up alerts**: Configure alerts for drift and performance degradation
9. **Use A/B testing**: Validate new models with gradual rollout
10. **Maintain rollback capability**: Keep previous versions available

---

## API Reference

See the following guides for detailed API documentation:

- [Serving Guide](./SERVING_GUIDE.md) - Model serving and A/B testing
- [Monitoring Guide](./MONITORING_GUIDE.md) - Drift detection and performance tracking

---

## Examples

See `examples/model_deployment/` for complete examples:

- `basic_serving.py` - Simple model deployment
- `ab_testing.py` - A/B testing configuration
- `drift_detection.py` - Drift monitoring setup
- `production_deployment.py` - Complete production deployment workflow

---

## Related Documentation

- [Model Training Guide](../model_training/README.md) - Train models for deployment
- [Data Validation Guide](../data_validation/README.md) - Validate data quality
- [Week 1 Infrastructure](../../docs/ERROR_HANDLING.md) - Error handling and monitoring

---

**Document Status:** COMPLETE
**Last Updated:** October 25, 2025
**Agent:** Agent 6 - Model Deployment & Serving
