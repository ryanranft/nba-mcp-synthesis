# Hyperparameter Tuning Strategies

**Component:** Model Training & Experimentation
**Module:** `mcp_server/hyperparameter_tuning.py`

Complete guide to hyperparameter optimization strategies in the NBA MCP Synthesis project.

---

## Overview

The `HyperparameterTuner` class provides three optimization strategies:

1. **Grid Search** - Exhaustive search over parameter grid
2. **Random Search** - Random sampling from parameter distributions
3. **Bayesian Optimization** - Smart search using Gaussian Processes

All methods support:
- Cross-validation for robust evaluation
- MLflow logging for experiment tracking
- Early stopping to save computation
- Week 1 integration (error handling, monitoring, RBAC)

---

## Method Comparison

| Strategy | Best For | Pros | Cons | Typical Use |
|----------|----------|------|------|-------------|
| **Grid Search** | Small parameter spaces | Exhaustive, reproducible | Slow for large spaces | 2-3 parameters with few values |
| **Random Search** | Medium parameter spaces | Faster than grid, simple | Not intelligent | 3-5 parameters, quick exploration |
| **Bayesian** | Large parameter spaces | Most efficient, intelligent | Requires scikit-optimize | 5+ parameters, production |

---

## 1. Grid Search

### When to Use

- Small parameter spaces (< 100 combinations)
- Need exhaustive search
- Parameters are well-understood

### Basic Usage

```python
from mcp_server.hyperparameter_tuning import HyperparameterTuner
from mcp_server.mlflow_integration import get_mlflow_tracker

# Setup
tracker = get_mlflow_tracker(experiment_name="grid_search_demo")
tuner = HyperparameterTuner(mlflow_tracker=tracker, enable_mlflow=True)

# Define training and evaluation
def train_fn(params):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(**params, random_state=42)
    model.fit(X_train, y_train)
    return model

def eval_fn(model):
    from sklearn.metrics import accuracy_score
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)

# Grid search
best = tuner.grid_search(
    param_grid={
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, 15],
        "min_samples_split": [2, 5, 10]
    },
    train_fn=train_fn,
    eval_fn=eval_fn,
    maximize=True,
    cv_folds=5  # 5-fold cross-validation
)

print(f"Best params: {best['params']}")
print(f"Best score: {best['score']:.4f}")
print(f"Trials evaluated: {best['trial']}")
```

### Parameter Grid Examples

```python
# Small grid (27 combinations)
small_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, 15],
    "min_samples_split": [2, 5, 10]
}

# Medium grid (144 combinations)
medium_grid = {
    "n_estimators": [50, 100, 200, 500],
    "max_depth": [5, 10, 15, 20],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4]
}

# Too large for grid search! (1,000 combinations)
# Use random search or Bayesian instead
large_grid = {
    "n_estimators": [50, 100, 200, 500, 1000],
    "max_depth": [3, 5, 10, 15, 20],
    "min_samples_split": [2, 5, 10, 20],
    "min_samples_leaf": [1, 2, 4, 8],
    "max_features": ["sqrt", "log2", None, 0.5, 0.7]
}
```

---

## 2. Random Search

### When to Use

- Medium to large parameter spaces
- Want faster exploration than grid search
- Parameters are continuous or have many values

### Basic Usage

```python
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_mlflow=True,
    enable_early_stopping=True,
    early_stopping_patience=10  # Stop if no improvement for 10 trials
)

best = tuner.random_search(
    param_distributions={
        "n_estimators": [50, 100, 200, 500, 1000],
        "max_depth": [3, 5, 10, 15, 20, 25],
        "min_samples_split": [2, 5, 10, 20],
        "min_samples_leaf": [1, 2, 4, 8],
        "max_features": ["sqrt", "log2", None, 0.5, 0.7]
    },
    n_iter=50,  # Try 50 random combinations
    train_fn=train_fn,
    eval_fn=eval_fn,
    maximize=True,
    cv_folds=5,
    random_state=42
)
```

### Advantages Over Grid Search

```python
# Grid search: 5 * 6 * 4 * 4 * 5 = 2,400 combinations
# Random search: Only 50 trials, but smart sampling

# Random search often finds good solutions faster:
# - Samples diverse combinations
# - Can try extreme values
# - Early stopping saves time
```

---

## 3. Bayesian Optimization

### When to Use

- Large parameter spaces
- Training is expensive (time/compute)
- Want most efficient search
- Have scikit-optimize installed

### Installation

```bash
pip install scikit-optimize
```

### Basic Usage

```python
best = tuner.bayesian_optimization(
    param_space={
        "learning_rate": (0.0001, 0.1, "log-uniform"),
        "max_depth": (3, 20),
        "n_estimators": (50, 1000),
        "min_samples_split": (2, 20)
    },
    train_fn=train_fn,
    eval_fn=eval_fn,
    n_calls=50,  # Number of iterations
    n_initial_points=10,  # Random exploration first
    cv_folds=5,
    random_state=42
)
```

### Parameter Space Syntax

```python
# Continuous parameters
{
    "learning_rate": (0.001, 0.1),  # Uniform sampling
    "log_lr": (0.0001, 0.1, "log-uniform"),  # Log-uniform (better for learning rates)
}

# Integer parameters
{
    "max_depth": (5, 20),  # Will round to integers
    "n_estimators": (50, 500),
}

# Categorical parameters
{
    "max_features": ["sqrt", "log2", None],  # Discrete choices
}

# Mixed example
param_space = {
    "learning_rate": (0.0001, 0.1, "log-uniform"),
    "max_depth": (3, 15),
    "n_estimators": (50, 1000),
    "min_samples_split": (2, 20),
    "max_features": ["sqrt", "log2", None]
}
```

### How Bayesian Optimization Works

1. **Initial Random Exploration** (n_initial_points trials)
   - Tries random parameter combinations
   - Builds initial understanding of search space

2. **Gaussian Process Modeling**
   - Fits probabilistic model of score vs parameters
   - Predicts which areas likely have good scores

3. **Acquisition Function**
   - Balances exploration (uncertain areas) vs exploitation (promising areas)
   - Suggests next parameter combination to try

4. **Iterative Refinement**
   - Updates model after each trial
   - Converges to optimal region efficiently

---

## Cross-Validation

All methods support k-fold cross-validation for robust evaluation.

### Basic Cross-Validation

```python
# 5-fold cross-validation (recommended)
best = tuner.grid_search(
    param_grid=params,
    train_fn=train_fn,
    eval_fn=eval_fn,
    cv_folds=5  # Splits data into 5 folds
)

# 10-fold cross-validation (more robust, slower)
best = tuner.random_search(
    param_distributions=params,
    n_iter=50,
    train_fn=train_fn,
    eval_fn=eval_fn,
    cv_folds=10
)
```

### How CV Works

```python
# Without CV: Single train/test split
# - Fast but may overfit to test set
# - Less reliable score estimate

# With CV (k=5):
# - Splits data into 5 folds
# - Trains 5 models (each using 4 folds for training, 1 for validation)
# - Returns mean score across 5 folds
# - More reliable but 5x slower
```

### Choosing Number of Folds

```python
# Small datasets (< 1000 samples): Use 10 folds
best = tuner.grid_search(..., cv_folds=10)

# Medium datasets (1000-10000 samples): Use 5 folds
best = tuner.grid_search(..., cv_folds=5)

# Large datasets (> 10000 samples): Use 3 folds or single split
best = tuner.grid_search(..., cv_folds=3)

# Very large datasets: Don't use CV (too slow)
best = tuner.grid_search(...)  # cv_folds=None (default)
```

---

## Early Stopping

Save computation by stopping when no improvement is observed.

### Configuration

```python
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_early_stopping=True,
    early_stopping_patience=10  # Stop after 10 trials without improvement
)

# Run search
best = tuner.random_search(
    param_distributions=params,
    n_iter=100,  # Max 100 trials
    train_fn=train_fn,
    eval_fn=eval_fn,
    maximize=True
)

# May stop early if no improvement after 10 trials
print(f"Stopped after {best['trial']} trials")  # May be < 100
```

### When Early Stopping Helps

```python
# Good use case: Random search with many iterations
# - Tries 100 random combinations
# - Stops at 45 if no improvement since trial 35
# - Saves 55 * training_time

# Less useful: Grid search
# - Grid search is systematic, may miss best params if stopped early
# - Use with caution

# Not useful: Bayesian optimization
# - Bayesian is already efficient
# - Early stopping may prevent convergence
```

---

## MLflow Integration

All tuning methods automatically log to MLflow when enabled.

### Automatic Logging

```python
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_mlflow=True  # Automatic logging
)

# Each trial logs:
# - Parameters tried
# - Score achieved
# - CV scores (if using cross-validation)
# - Trial number
# - Method used (grid/random/bayesian)
```

### Viewing Results in MLflow UI

```bash
# Start MLflow UI
mlflow ui --port 5000

# Navigate to http://localhost:5000
# - View all trials
# - Sort by score
# - Compare parameter values
# - Download results
```

### Comparing Tuning Runs

```python
# Get tuning summary
summary = tuner.get_tuning_summary()
print(f"Total trials: {summary['total_trials']}")
print(f"Best score: {summary['best_score']:.4f}")
print(f"Mean score: {summary['mean_score']:.4f}")
print(f"Std dev: {summary['std_score']:.4f}")
print(f"Methods used: {summary['methods_used']}")

# Get top N results
top_5 = tuner.get_top_results(n=5)
for i, result in enumerate(top_5, 1):
    print(f"{i}. Score: {result['score']:.4f}, Params: {result['params']}")
```

---

## Best Practices

### 1. Start with Random Search

```python
# First: Quick random search to understand space
quick_best = tuner.random_search(
    param_distributions=large_space,
    n_iter=20,  # Just 20 trials
    train_fn=train_fn,
    eval_fn=eval_fn
)

# Then: Refined grid search around promising area
refined_best = tuner.grid_search(
    param_grid={
        "n_estimators": [quick_best['params']['n_estimators'] - 50,
                         quick_best['params']['n_estimators'],
                         quick_best['params']['n_estimators'] + 50],
        "max_depth": [quick_best['params']['max_depth'] - 2,
                      quick_best['params']['max_depth'],
                      quick_best['params']['max_depth'] + 2]
    },
    train_fn=train_fn,
    eval_fn=eval_fn
)
```

### 2. Use Cross-Validation for Small Datasets

```python
# Dataset < 5000 samples: Always use CV
if len(X) < 5000:
    best = tuner.grid_search(..., cv_folds=5)
else:
    best = tuner.grid_search(...)  # Single split is fine
```

### 3. Enable Early Stopping for Long Searches

```python
# Long searches: Enable early stopping
tuner = HyperparameterTuner(
    enable_early_stopping=True,
    early_stopping_patience=15
)
```

### 4. Use Bayesian Optimization for Expensive Training

```python
# If each trial takes > 1 minute: Use Bayesian
if training_time_per_trial > 60:
    best = tuner.bayesian_optimization(
        param_space=space,
        n_calls=30  # Fewer trials needed
    )
else:
    best = tuner.random_search(
        param_distributions=space,
        n_iter=100  # Can afford more trials
    )
```

### 5. Always Log to MLflow

```python
# Good: Track all experiments
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_mlflow=True
)

# Bad: No tracking, can't reproduce
tuner = HyperparameterTuner()
```

---

## Example: Complete Tuning Workflow

```python
from mcp_server.hyperparameter_tuning import HyperparameterTuner
from mcp_server.mlflow_integration import get_mlflow_tracker
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd

# Load data
data = pd.read_csv('nba_player_stats.csv')
X = data.drop(columns=['all_star'])
y = data['all_star']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Setup MLflow
tracker = get_mlflow_tracker(experiment_name="nba_rf_tuning")

# Setup tuner
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_mlflow=True,
    enable_early_stopping=True,
    early_stopping_patience=10
)

# Define functions
def train_fn(params):
    model = RandomForestClassifier(**params, random_state=42)
    model.fit(X_train, y_train)
    return model

def eval_fn(model):
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)

# Phase 1: Quick random search
print("Phase 1: Quick exploration...")
quick_best = tuner.random_search(
    param_distributions={
        "n_estimators": [50, 100, 200, 500],
        "max_depth": [5, 10, 15, 20],
        "min_samples_split": [2, 5, 10, 20],
        "min_samples_leaf": [1, 2, 4, 8]
    },
    n_iter=20,
    train_fn=train_fn,
    eval_fn=eval_fn,
    maximize=True
)
print(f"Quick best: {quick_best['score']:.4f}")

# Phase 2: Refined Bayesian optimization
print("\nPhase 2: Bayesian optimization...")
final_best = tuner.bayesian_optimization(
    param_space={
        "n_estimators": (50, 500),
        "max_depth": (5, 20),
        "min_samples_split": (2, 20),
        "min_samples_leaf": (1, 8)
    },
    train_fn=train_fn,
    eval_fn=eval_fn,
    n_calls=30,
    cv_folds=5,  # Use CV for final tuning
    random_state=42
)
print(f"Final best: {final_best['score']:.4f}")

# Get summary
summary = tuner.get_tuning_summary()
print(f"\nTotal trials: {summary['total_trials']}")
print(f"Best score: {summary['best_score']:.4f}")
print(f"Improvement: {summary['best_score'] - quick_best['score']:.4f}")
```

---

## Related Documentation

- [Model Training README](README.md)
- [MLflow Setup Guide](MLFLOW_GUIDE.md)
- [Training Pipeline](README.md#3-complete-training-pipeline)

---

**Document Status:** AGENT 5 - PHASE 4 DOCUMENTATION
**Created:** October 25, 2025
**Component:** Hyperparameter Tuning
**See Also:** [README.md](README.md) | [MLFLOW_GUIDE.md](MLFLOW_GUIDE.md)
