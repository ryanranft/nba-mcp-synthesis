# Model Serving Guide

**Complete guide to model serving, A/B testing, and production deployment patterns**

---

## Table of Contents

1. [Model Serving Basics](#model-serving-basics)
2. [Multi-Version Serving](#multi-version-serving)
3. [A/B Testing](#ab-testing)
4. [Health Checks](#health-checks)
5. [Circuit Breaker Pattern](#circuit-breaker-pattern)
6. [Production Deployment Patterns](#production-deployment-patterns)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

---

## Model Serving Basics

### Initialization

```python
from mcp_server.model_serving import ModelServingManager

# Basic initialization
manager = ModelServingManager(
    enable_mlflow=True,
    mlflow_experiment="nba_serving",
    error_threshold=0.1,  # Circuit breaker threshold
    mock_mode=False
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_mlflow` | bool | False | Enable MLflow integration |
| `mlflow_experiment` | str | None | MLflow experiment name |
| `error_threshold` | float | 0.5 | Circuit breaker error threshold (0-1) |
| `mock_mode` | bool | False | Enable mock mode for testing |

### Deploying a Model

```python
from sklearn.ensemble import RandomForestClassifier

# Train your model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Deploy the model
success = manager.deploy_model(
    model_id="nba_win_predictor",
    version="v1.0",
    model_instance=model,
    set_active=True,  # Make this the active version
    metadata={"trained_by": "data_scientist_1", "date": "2025-10-25"}
)

if success:
    print("Model deployed successfully!")
```

### Making Predictions

```python
# Single prediction
result = manager.predict(
    model_id="nba_win_predictor",
    inputs=[{
        "home_ppg": 112.5,
        "away_ppg": 108.3,
        "home_def_rating": 105.2,
        "away_def_rating": 110.8
    }]
)

print(f"Win probability: {result[0]:.2f}")

# Batch predictions
batch_inputs = [
    {"home_ppg": 112.5, "away_ppg": 108.3, ...},
    {"home_ppg": 115.2, "away_ppg": 110.1, ...},
    {"home_ppg": 108.9, "away_ppg": 112.5, ...}
]

results = manager.predict(
    model_id="nba_win_predictor",
    inputs=batch_inputs
)

for i, prob in enumerate(results):
    print(f"Game {i+1} win probability: {prob:.2f}")
```

---

## Multi-Version Serving

### Deploy Multiple Versions

```python
# Deploy version 1.0 (baseline)
manager.deploy_model(
    model_id="nba_model",
    version="v1.0",
    model_instance=model_v1,
    set_active=True
)

# Deploy version 1.1 (improved)
manager.deploy_model(
    model_id="nba_model",
    version="v1.1",
    model_instance=model_v1_1,
    set_active=False  # Don't make active yet
)

# Deploy version 2.0 (major update)
manager.deploy_model(
    model_id="nba_model",
    version="v2.0",
    model_instance=model_v2,
    set_active=False
)
```

### Switch Active Version

```python
# Switch to version 1.1
manager.set_active_version(
    model_id="nba_model",
    version="v1.1"
)

# Verify active version
active = manager.active_models.get("nba_model")
print(f"Active version: {active}")  # "v1.1"
```

### Version Management

```python
# List all versions
status = manager.get_all_models_status()
for model_id, models in status.items():
    print(f"\nModel: {model_id}")
    for version, info in models.items():
        print(f"  {version}: {info['status']}, "
              f"requests={info['metrics'].request_count}")

# Retire old version
manager.retire_model(
    model_id="nba_model",
    version="v1.0"
)
```

---

## A/B Testing

### Basic A/B Test Setup

```python
# Deploy two versions
manager.deploy_model("nba_model", "v1.0", model_v1)
manager.deploy_model("nba_model", "v2.0", model_v2)

# Setup A/B test (50/50 split)
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.5, 0.5]
)

# Make predictions - automatically routed
for i in range(100):
    result = manager.predict("nba_model", [game_data])
    # Approximately 50 requests to v1.0, 50 to v2.0
```

### Weighted A/B Testing

```python
# Canary deployment: 95% v1.0, 5% v2.0
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.95, 0.05]
)

# Multi-variant testing: 70% v1.0, 20% v2.0, 10% v3.0
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0", "v3.0"],
    weights=[0.7, 0.2, 0.1]
)
```

### Monitor A/B Test Results

```python
# Get metrics for each version
status = manager.get_all_models_status()["nba_model"]

for version in ["v1.0", "v2.0"]:
    metrics = status[version]["metrics"]
    print(f"\n{version} Metrics:")
    print(f"  Requests: {metrics.request_count}")
    print(f"  Avg Latency: {metrics.avg_latency_ms:.2f}ms")
    print(f"  Error Rate: {metrics.error_rate:.2%}")

# Calculate statistical significance (example)
from scipy import stats

v1_results = [...]  # Collect prediction results
v2_results = [...]

t_stat, p_value = stats.ttest_ind(v1_results, v2_results)

if p_value < 0.05:
    print(f"Significant difference detected (p={p_value:.4f})")
    # Promote winner
    if np.mean(v2_results) > np.mean(v1_results):
        manager.set_active_version("nba_model", "v2.0")
```

### Gradual Rollout

```python
# Week 1: 5% traffic to new version
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.95, 0.05]
)

# Monitor for issues...
time.sleep(7 * 24 * 3600)  # Wait 1 week

# Week 2: 25% traffic
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.75, 0.25]
)

# Monitor...
time.sleep(7 * 24 * 3600)

# Week 3: 50% traffic
manager.setup_ab_test(
    model_id="nba_model",
    versions=["v1.0", "v2.0"],
    weights=[0.5, 0.5]
)

# If successful, promote to 100%
manager.set_active_version("nba_model", "v2.0")
```

---

## Health Checks

### Check Model Health

```python
from mcp_server.model_serving import HealthStatus

# Get health status
health = manager.health_check("nba_model", "v1.0")

print(f"Status: {health.status}")  # HEALTHY, UNHEALTHY, or UNKNOWN
print(f"Circuit Breaker: {'Open' if health.circuit_breaker_open else 'Closed'}")
print(f"Last Request: {health.last_request_time}")
print(f"Request Count: {health.request_count}")
print(f"Error Rate: {health.error_rate:.2%}")
```

### Health Status Meanings

| Status | Description | Action |
|--------|-------------|--------|
| `HEALTHY` | Model is operating normally | None |
| `UNHEALTHY` | Circuit breaker tripped or high errors | Investigate, consider rollback |
| `UNKNOWN` | No recent requests or model not found | Verify deployment |

### Custom Health Checks

```python
def custom_health_check(model, version):
    """Custom health check function"""
    # Check model is loaded
    if model is None:
        return False

    # Check model has predict method
    if not hasattr(model, 'predict'):
        return False

    # Test prediction
    try:
        test_input = [[0.0] * model.n_features_in_]
        _ = model.predict(test_input)
        return True
    except Exception:
        return False

# Deploy with custom health check
manager.deploy_model(
    model_id="nba_model",
    version="v1.0",
    model_instance=model,
    health_check_fn=custom_health_check
)
```

### Automated Health Monitoring

```python
import time
from datetime import datetime

def monitor_health(manager, model_id, interval_sec=60):
    """Continuously monitor model health"""
    while True:
        health = manager.health_check(model_id)

        if health.status == HealthStatus.UNHEALTHY:
            print(f"[{datetime.now()}] WARNING: {model_id} is unhealthy!")
            # Send alert
            send_alert(f"Model {model_id} health check failed")

            # Auto-rollback to previous version
            if health.circuit_breaker_open:
                print("Circuit breaker open, attempting rollback...")
                previous_version = get_previous_stable_version(model_id)
                manager.set_active_version(model_id, previous_version)

        time.sleep(interval_sec)

# Run in background
import threading
monitor_thread = threading.Thread(
    target=monitor_health,
    args=(manager, "nba_model"),
    daemon=True
)
monitor_thread.start()
```

---

## Circuit Breaker Pattern

### How It Works

The circuit breaker automatically opens (stops serving requests) when the error rate exceeds the configured threshold:

```
Error Rate > error_threshold → Circuit Breaker Opens → Status = DEGRADED
```

### Configuration

```python
# Set error threshold
manager = ModelServingManager(
    error_threshold=0.1  # Trip at 10% error rate
)

# Deploy model
manager.deploy_model(
    model_id="nba_model",
    version="v1.0",
    model_instance=model,
    error_threshold=0.15  # Override per-model
)
```

### Circuit Breaker States

1. **Closed** (Normal): Requests flow through, errors tracked
2. **Open** (Tripped): Requests rejected immediately, no predictions made
3. **Half-Open**: (Not implemented) Test requests to check if error is resolved

### Handling Circuit Breaker

```python
try:
    result = manager.predict("nba_model", [input_data])
except Exception as e:
    # Check if circuit breaker caused the error
    health = manager.health_check("nba_model")

    if health.circuit_breaker_open:
        # Circuit breaker is open
        print("Circuit breaker open, using fallback...")

        # Option 1: Use fallback model
        result = fallback_model.predict([input_data])

        # Option 2: Use cached predictions
        result = get_cached_prediction(input_data)

        # Option 3: Use default value
        result = [0.5]  # Neutral prediction
    else:
        # Other error, re-raise
        raise
```

### Manual Circuit Breaker Control

```python
# Manual reset (use with caution)
manager.reset_circuit_breaker("nba_model", "v1.0")

# Verify reset
health = manager.health_check("nba_model", "v1.0")
assert not health.circuit_breaker_open
```

### Circuit Breaker Best Practices

1. **Set appropriate thresholds**: Not too low (false positives) or too high (delays detection)
2. **Monitor error rates**: Track trends to prevent trips
3. **Have fallback plans**: Always have backup models or cached predictions
4. **Auto-rollback**: Automatically switch to previous stable version
5. **Alert on trips**: Set up notifications when circuit breaker opens

---

## Production Deployment Patterns

### 1. Blue-Green Deployment

Deploy new version alongside old, switch atomically:

```python
def blue_green_deployment(manager, model_id, new_model, new_version):
    """Blue-green deployment pattern"""

    # Current version is "blue"
    current_version = manager.active_models.get(model_id)
    print(f"Current (blue) version: {current_version}")

    # Deploy new version as "green"
    print(f"Deploying new (green) version: {new_version}")
    success = manager.deploy_model(
        model_id=model_id,
        version=new_version,
        model_instance=new_model,
        set_active=False  # Don't make active yet
    )

    if not success:
        print("Deployment failed!")
        return False

    # Test green version
    print("Testing green version...")
    test_passed = run_smoke_tests(manager, model_id, new_version)

    if test_passed:
        # Switch to green
        print("Tests passed, switching to green...")
        manager.set_active_version(model_id, new_version)
        print(f"Deployment successful! Active version: {new_version}")

        # Keep blue version for rollback
        return True
    else:
        # Rollback to blue
        print("Tests failed, staying on blue version")
        manager.retire_model(model_id, new_version)
        return False
```

### 2. Canary Deployment

Gradual rollout with monitoring:

```python
def canary_deployment(manager, model_id, new_model, new_version):
    """Canary deployment with gradual rollout"""

    current_version = manager.active_models.get(model_id)

    # Deploy canary
    manager.deploy_model(model_id, new_version, new_model, set_active=False)

    # Stage 1: 5% traffic
    print("Stage 1: 5% traffic to canary...")
    manager.setup_ab_test(
        model_id=model_id,
        versions=[current_version, new_version],
        weights=[0.95, 0.05]
    )

    # Monitor for issues
    if not monitor_canary(manager, model_id, new_version, duration_hours=24):
        rollback(manager, model_id, current_version)
        return False

    # Stage 2: 25% traffic
    print("Stage 2: 25% traffic to canary...")
    manager.setup_ab_test(
        model_id=model_id,
        versions=[current_version, new_version],
        weights=[0.75, 0.25]
    )

    if not monitor_canary(manager, model_id, new_version, duration_hours=48):
        rollback(manager, model_id, current_version)
        return False

    # Stage 3: 100% traffic
    print("Stage 3: Full rollout...")
    manager.set_active_version(model_id, new_version)

    return True

def monitor_canary(manager, model_id, canary_version, duration_hours):
    """Monitor canary for issues"""
    import time

    end_time = time.time() + (duration_hours * 3600)

    while time.time() < end_time:
        health = manager.health_check(model_id, canary_version)

        if health.circuit_breaker_open:
            print(f"Canary circuit breaker opened!")
            return False

        if health.error_rate > 0.05:  # 5% threshold
            print(f"Canary error rate too high: {health.error_rate:.2%}")
            return False

        time.sleep(300)  # Check every 5 minutes

    return True
```

### 3. Shadow Deployment

Run new version in shadow mode (predictions not returned):

```python
class ShadowDeployment:
    """Shadow deployment for comparing models"""

    def __init__(self, prod_manager, shadow_manager):
        self.prod_manager = prod_manager
        self.shadow_manager = shadow_manager
        self.comparisons = []

    def predict_with_shadow(self, model_id, inputs):
        """Make prediction with shadow model comparison"""

        # Production prediction
        prod_result = self.prod_manager.predict(model_id, inputs)

        # Shadow prediction (async, doesn't block)
        shadow_result = self.shadow_manager.predict(
            model_id + "_shadow",
            inputs
        )

        # Log comparison
        self.comparisons.append({
            'production': prod_result,
            'shadow': shadow_result,
            'input': inputs
        })

        # Return only production result
        return prod_result

    def analyze_shadow_performance(self):
        """Analyze shadow model performance"""
        if not self.comparisons:
            return None

        differences = []
        for comp in self.comparisons:
            diff = abs(comp['production'] - comp['shadow'])
            differences.append(diff)

        avg_diff = np.mean(differences)
        max_diff = np.max(differences)

        print(f"Shadow Model Analysis:")
        print(f"  Average difference: {avg_diff:.4f}")
        print(f"  Maximum difference: {max_diff:.4f}")
        print(f"  Samples compared: {len(self.comparisons)}")

        return avg_diff

# Usage
prod_manager = ModelServingManager()
shadow_manager = ModelServingManager()

# Deploy production and shadow
prod_manager.deploy_model("nba_model", "v1.0", model_v1, set_active=True)
shadow_manager.deploy_model("nba_model_shadow", "v2.0", model_v2, set_active=True)

# Use shadow deployment
deployment = ShadowDeployment(prod_manager, shadow_manager)

# Make predictions
for game in games:
    result = deployment.predict_with_shadow("nba_model", [game])

# Analyze after sufficient data
deployment.analyze_shadow_performance()
```

---

## Performance Optimization

### Batch Predictions

```python
# Instead of individual predictions
for game in games:
    result = manager.predict("nba_model", [game])  # Slower

# Use batch predictions
batch_size = 100
for i in range(0, len(games), batch_size):
    batch = games[i:i+batch_size]
    results = manager.predict("nba_model", batch)  # Faster
```

### Model Caching

```python
# Models are automatically cached in memory
# First prediction loads model
manager.predict("nba_model", [game1])  # Loads model

# Subsequent predictions use cached model
manager.predict("nba_model", [game2])  # Fast (cached)
```

### Request Batching

```python
import asyncio

async def predict_async(manager, model_id, inputs):
    """Async prediction wrapper"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        manager.predict,
        model_id,
        inputs
    )
    return result

# Concurrent predictions
async def predict_batch_async(manager, model_id, all_inputs):
    tasks = [
        predict_async(manager, model_id, [inp])
        for inp in all_inputs
    ]
    results = await asyncio.gather(*tasks)
    return results

# Usage
results = asyncio.run(predict_batch_async(manager, "nba_model", games))
```

---

## Troubleshooting

### Common Issues

#### 1. Model Not Found

```
Error: Model 'nba_model' not found or no active version set
```

**Solution:**
```python
# Check deployed models
status = manager.get_all_models_status()
print(status.keys())

# Deploy model if not found
manager.deploy_model("nba_model", "v1.0", model, set_active=True)
```

#### 2. Circuit Breaker Open

```
Error: Circuit breaker is open for model nba_model:v1.0
```

**Solution:**
```python
# Check error rate
health = manager.health_check("nba_model", "v1.0")
print(f"Error rate: {health.error_rate:.2%}")

# Reset if appropriate
manager.reset_circuit_breaker("nba_model", "v1.0")

# Or rollback to previous version
manager.set_active_version("nba_model", "v0.9")
```

#### 3. High Latency

```
Warning: Prediction latency exceeds 1000ms
```

**Solution:**
```python
# Check metrics
status = manager.get_all_models_status()["nba_model"]["v1.0"]
metrics = status["metrics"]
print(f"Avg latency: {metrics.avg_latency_ms:.2f}ms")

# Use batch predictions
results = manager.predict("nba_model", large_batch)  # Faster

# Or optimize model
optimized_model = optimize_model(model)
manager.deploy_model("nba_model", "v1.1", optimized_model)
```

---

## Best Practices

1. **Version everything**: Use semantic versioning (v1.0, v1.1, v2.0)
2. **Test before production**: Always test in staging environment
3. **Use gradual rollouts**: Canary deployments reduce risk
4. **Monitor continuously**: Track metrics and set up alerts
5. **Have rollback plans**: Keep previous versions deployed
6. **Set appropriate thresholds**: Configure circuit breaker based on use case
7. **Use health checks**: Implement custom health checks for critical models
8. **Log predictions**: Enable comprehensive logging for debugging
9. **Document changes**: Track what changed in each version
10. **Automate deployments**: Use CI/CD for consistent deployments

---

**Document Status:** COMPLETE
**Last Updated:** October 25, 2025
