# Econometric Suite - Unified Analysis Interface

**Module 4D - Agent 8**
**Author**: Agent 8
**Date**: October 2025

## Overview

The Econometric Suite provides a unified interface for all econometric methods in the NBA analytics framework. It automatically detects data structure and selects appropriate methods, making advanced econometric analysis accessible through a single, consistent API.

**Key Features**:
- **Auto-Detection**: Identifies data structure (cross-section, time series, panel, survival, causal)
- **Unified API**: Access all 6 econometric modules through one interface
- **Smart Selection**: Recommends appropriate methods based on data characteristics
- **Model Comparison**: Compare multiple methods with information criteria
- **Model Averaging**: Ensemble predictions with flexible weighting
- **MLflow Integration**: Comprehensive experiment tracking

## Quick Start

```python
from mcp_server.econometric_suite import EconometricSuite
import pandas as pd

# Load your data
df = pd.read_csv('player_stats.csv')

# Initialize suite - it auto-detects data structure
suite = EconometricSuite(
    data=df,
    target='points_per_game',
    entity_col='player_id',
    time_col='season'
)

# Auto-select and run best method
result = suite.analyze(method='auto')

# View results
print(result.summary())
```

## Installation

No additional dependencies beyond existing econometric modules:

```bash
# All required packages already installed from previous modules
pip install statsmodels pmdarima linearmodels pymc arviz dowhy networkx lifelines scikit-survival mlflow
```

## Data Structure Detection

The Suite automatically detects your data structure and recommends appropriate methods:

| Data Structure | Detection Criteria | Recommended Methods |
|----------------|-------------------|---------------------|
| **Cross-Section** | Single time point, no entities | Bayesian |
| **Time Series** | Single entity over time | Time Series, Advanced Time Series, Bayesian |
| **Panel** | Multiple entities over time | Panel Data, Bayesian |
| **Event History** | Duration + event columns | Survival Analysis |
| **Treatment-Outcome** | Treatment + outcome columns | Causal Inference |

### Detection Examples

```python
# Cross-sectional data
df = pd.DataFrame({
    'player_id': range(100),
    'points': [...],
    'assists': [...]
})
suite = EconometricSuite(data=df, target='points')
print(suite.characteristics)
# Output: DataCharacteristics(structure=cross_section, n_obs=100)

# Time series data
df = pd.DataFrame({
    'date': pd.date_range('2020-01-01', periods=200),
    'points': [...]
})
suite = EconometricSuite(data=df.set_index('date'), target='points')
print(suite.characteristics)
# Output: DataCharacteristics(structure=time_series, n_obs=200)

# Panel data
df = pd.DataFrame({
    'player_id': [...],
    'season': [...],
    'points': [...]
})
suite = EconometricSuite(
    data=df,
    target='points',
    entity_col='player_id',
    time_col='season'
)
print(suite.characteristics)
# Output: DataCharacteristics(structure=panel, n_entities=50, n_periods=10)
```

## Core Functionality

### 1. Auto-Analysis

Let the Suite automatically select the best method:

```python
suite = EconometricSuite(data=panel_df, target='points', entity_col='player_id', time_col='season')

# Auto-detect and analyze
result = suite.analyze(method='auto')

print(f"Method used: {result.method_used}")
print(f"R²: {result.r_squared:.3f}")
print(f"AIC: {result.aic:.2f}")
```

### 2. Specific Method Access

Access specific econometric modules directly:

#### Time Series Analysis

```python
suite = EconometricSuite(data=ts_data, target='points')

# ARIMA modeling
result = suite.time_series_analysis(method='arima', order=(1, 1, 1))

# Auto-ARIMA
result = suite.time_series_analysis(method='auto_arima')
```

#### Panel Data Analysis

```python
suite = EconometricSuite(
    data=panel_df,
    target='points',
    entity_col='player_id',
    time_col='season'
)

# Fixed effects
fe_result = suite.panel_analysis(method='fixed_effects')

# Random effects
re_result = suite.panel_analysis(method='random_effects')

print(f"FE R²: {fe_result.r_squared:.3f}")
print(f"RE R²: {re_result.r_squared:.3f}")
```

#### Causal Inference

```python
suite = EconometricSuite(
    data=df,
    treatment_col='new_coach',
    outcome_col='wins'
)

# Propensity score matching
result = suite.causal_analysis(method='psm', n_neighbors=3)

print(f"Average Treatment Effect: {result.result.ate:.2f}")
print(f"ATT: {result.result.att:.2f}")
```

#### Survival Analysis

```python
suite = EconometricSuite(
    data=career_df,
    duration_col='career_years',
    event_col='retired'
)

# Cox proportional hazards
result = suite.survival_analysis(method='cox')

print(f"Concordance Index: {result.result.concordance_index:.3f}")
print(f"Median Survival: {result.result.median_survival_time:.1f} years")
```

#### Advanced Time Series

```python
suite = EconometricSuite(data=ts_data, target='points')

# Kalman filtering
result = suite.advanced_time_series_analysis(method='kalman', model='local_level')

print(f"Log-Likelihood: {result.log_likelihood:.2f}")
```

#### Bayesian Analysis

```python
suite = EconometricSuite(data=df, target='points')

# Hierarchical modeling
result = suite.bayesian_analysis(method='hierarchical')
```

### 3. Model Comparison

Compare multiple methods systematically:

```python
suite = EconometricSuite(
    data=panel_df,
    target='points',
    entity_col='player_id',
    time_col='season'
)

# Define methods to compare
methods = [
    {'category': 'panel', 'method': 'fixed_effects', 'params': {}},
    {'category': 'panel', 'method': 'random_effects', 'params': {}}
]

# Compare using BIC
comparison = suite.compare_methods(methods, metric='bic')

print(comparison)
# Output:
#                  method  aic    bic  r_squared  log_likelihood  rank
# 0         Fixed Effects  1234  1256      0.721          -610.0   1.0
# 1        Random Effects  1245  1267      0.715          -616.0   2.0
```

### 4. Model Averaging

Combine predictions from multiple methods:

```python
from mcp_server.econometric_suite import ModelAverager

# Get predictions from multiple models
fe_pred = fe_model.predict()
re_pred = re_model.predict()

predictions = {
    'fixed_effects': fe_pred,
    'random_effects': re_pred
}

# Equal weights
avg_equal = ModelAverager.average(predictions, weights='equal')

# AIC-based weights
model_metrics = {
    'fixed_effects': {'aic': 1234.5, 'bic': 1256.0},
    'random_effects': {'aic': 1245.0, 'bic': 1267.0}
}
avg_aic = ModelAverager.average(predictions, weights='aic', model_metrics=model_metrics)

# Custom weights
avg_custom = ModelAverager.average(
    predictions,
    weights={'fixed_effects': 0.7, 'random_effects': 0.3}
)
```

## Real-World Examples

### Example 1: Player Performance Analysis (Panel Data)

```python
import pandas as pd
from mcp_server.econometric_suite import EconometricSuite

# Load multi-season player data
df = pd.read_csv('player_seasons.csv')

# Initialize suite
suite = EconometricSuite(
    data=df,
    target='points_per_game',
    entity_col='player_id',
    time_col='season',
    mlflow_experiment='player_performance'
)

# Auto-analyze
result = suite.analyze(method='auto')
print(result.summary())

# Compare fixed vs random effects
methods = [
    {'category': 'panel', 'method': 'fixed_effects', 'params': {}},
    {'category': 'panel', 'method': 'random_effects', 'params': {}}
]
comparison = suite.compare_methods(methods, metric='bic')
print("\nModel Comparison:")
print(comparison)
```

### Example 2: Career Longevity Study (Survival Analysis)

```python
# Load player career data
careers = pd.read_csv('player_careers.csv')

suite = EconometricSuite(
    data=careers,
    duration_col='years_played',
    event_col='retired'
)

# Cox proportional hazards
result = suite.survival_analysis(method='cox')

print(f"Concordance Index: {result.result.concordance_index:.3f}")
print("\nHazard Ratios:")
print(result.result.hazard_ratios)
```

### Example 3: Coaching Change Impact (Causal Inference)

```python
# Load team-season data
teams = pd.read_csv('team_seasons.csv')

suite = EconometricSuite(
    data=teams,
    treatment_col='coaching_change',
    outcome_col='win_pct'
)

# Propensity score matching
result = suite.causal_analysis(method='psm', n_neighbors=3, caliper=0.1)

print(f"Average Treatment Effect on Treated: {result.result.att:.3f}")
print(f"95% CI: {result.result.confidence_interval}")
print(f"\nMatched: {result.result.n_matched}")
print(f"Unmatched: {result.result.n_unmatched}")

# Check balance
print("\nCovariate Balance:")
print(result.result.balance_statistics)
```

### Example 4: Time Series Forecasting

```python
# Load daily scoring data
daily = pd.read_csv('daily_points.csv', index_col='date', parse_dates=True)

suite = EconometricSuite(data=daily, target='points')

# Compare ARIMA models
methods = [
    {'category': 'time_series', 'method': 'arima', 'params': {'order': (1,1,1)}},
    {'category': 'time_series', 'method': 'arima', 'params': {'order': (2,1,0)}},
    {'category': 'time_series', 'method': 'arima', 'params': {'order': (1,1,2)}}
]

comparison = suite.compare_methods(methods, metric='aic')
print("Best model by AIC:")
print(comparison.iloc[0])

# Use best model for forecasting
best_result = suite.time_series_analysis(
    method='arima',
    order=eval(comparison.iloc[0]['params'] if 'params' in comparison else '(1,1,1)')
)
```

### Example 5: Multi-Method Ensemble

```python
# Panel data with multiple analysis approaches
suite = EconometricSuite(
    data=panel_df,
    target='points',
    entity_col='player_id',
    time_col='season'
)

# Run multiple methods
fe_result = suite.panel_analysis(method='fixed_effects')
re_result = suite.panel_analysis(method='random_effects')
bayes_result = suite.bayesian_analysis(method='hierarchical')

# Get predictions (hypothetical - would need to implement predict methods)
predictions = {
    'fixed_effects': fe_result.result.fitted_values,
    'random_effects': re_result.result.fitted_values,
    'bayesian': bayes_result.result.posterior_predictive
}

# Ensemble with AIC weights
model_metrics = {
    'fixed_effects': {'aic': fe_result.aic},
    'random_effects': {'aic': re_result.aic},
    'bayesian': {'aic': bayes_result.aic}
}

ensemble = ModelAverager.average(
    predictions,
    weights='aic',
    model_metrics=model_metrics
)
```

## MLflow Integration

Track all experiments automatically:

```python
suite = EconometricSuite(
    data=df,
    target='points',
    entity_col='player_id',
    time_col='season',
    mlflow_experiment='panel_comparison'
)

# All analyze() calls are tracked
result = suite.analyze(method='auto')

# Logged automatically:
# - Data characteristics (n_obs, n_entities, n_periods)
# - Method used
# - Model metrics (AIC, BIC, R²)
# - Timestamp

# View in MLflow UI
# mlflow ui --port 5000
```

## API Reference

### EconometricSuite Class

```python
class EconometricSuite:
    def __init__(
        self,
        data: pd.DataFrame,
        target: Optional[str] = None,
        entity_col: Optional[str] = None,
        time_col: Optional[str] = None,
        duration_col: Optional[str] = None,
        event_col: Optional[str] = None,
        treatment_col: Optional[str] = None,
        outcome_col: Optional[str] = None,
        mlflow_experiment: Optional[str] = None
    )
```

**Attributes**:
- `characteristics`: Detected data structure and properties
- `recommended_methods`: List of appropriate method categories

**Methods**:
- `analyze(method='auto', **kwargs)` - Auto-select and run analysis
- `time_series_analysis(method, **kwargs)` - Access time series methods
- `panel_analysis(method, **kwargs)` - Access panel data methods
- `causal_analysis(method, **kwargs)` - Access causal inference methods
- `survival_analysis(method, **kwargs)` - Access survival methods
- `bayesian_analysis(method, **kwargs)` - Access Bayesian methods
- `advanced_time_series_analysis(method, **kwargs)` - Access advanced TS methods
- `compare_methods(methods, metric)` - Compare multiple methods
- `diagnostic_summary(result)` - Generate diagnostic report

### SuiteResult Class

```python
@dataclass
class SuiteResult:
    data_structure: DataStructure
    method_category: MethodCategory
    method_used: str
    result: Any  # Specific result object
    model: Any   # Fitted model (if available)
    aic: Optional[float]
    bic: Optional[float]
    log_likelihood: Optional[float]
    r_squared: Optional[float]
    n_obs: int
    n_params: int
    timestamp: datetime
    warnings: List[str]
```

**Methods**:
- `summary()` - Generate human-readable summary

### ModelAverager Class

```python
class ModelAverager:
    @staticmethod
    def average(
        predictions: Dict[str, np.ndarray],
        weights: Union[str, Dict[str, float]] = 'equal',
        model_metrics: Optional[Dict] = None
    ) -> np.ndarray
```

**Weight Options**:
- `'equal'`: Simple average
- `'aic'`: AIC-based weights (requires model_metrics)
- `'bic'`: BIC-based weights (requires model_metrics)
- `'performance'`: R²-based weights (requires model_metrics)
- `dict`: Custom weights

## Testing

Run the comprehensive test suite:

```bash
# All 31 tests
pytest tests/test_econometric_suite.py -v

# Specific categories
pytest tests/test_econometric_suite.py -k "test_detect" -v  # Data detection (5 tests)
pytest tests/test_econometric_suite.py -k "test_recommend" -v  # Recommendations (5 tests)
pytest tests/test_econometric_suite.py -k "test_suite_initialization" -v  # Init (3 tests)
pytest tests/test_econometric_suite.py -k "test_.*_analysis" -v  # Method access (6 tests)
pytest tests/test_econometric_suite.py -k "test_model_averaging" -v  # Averaging (4 tests)
pytest tests/test_econometric_suite.py -k "test_compare" -v  # Comparison (2 tests)
pytest tests/test_econometric_suite.py -k "test_auto" -v  # Auto-analysis (3 tests)
```

**Test Coverage**: 31/31 tests passing (100%)

## Integration with Existing Modules

The Suite integrates all 6 econometric modules:

1. **time_series.py**: Basic ARIMA, VAR, seasonal decomposition
2. **panel_data.py**: Fixed/random effects, DID
3. **bayesian.py**: Hierarchical models, MCMC
4. **advanced_time_series.py**: Kalman, Markov switching, dynamic factors
5. **causal_inference.py**: IV, RDD, PSM, synthetic control
6. **survival_analysis.py**: Cox, Kaplan-Meier, competing risks

Each module can still be used independently, or accessed through the unified Suite interface.

## Performance Considerations

- **Auto-detection**: O(n) scan of data structure
- **Method execution**: Depends on specific method (see individual module docs)
- **Model comparison**: Linear in number of methods
- **Model averaging**: O(n·m) where n=observations, m=models

## Known Limitations

1. **Method-specific**: Not all methods from each module are exposed yet
2. **Formula construction**: Panel methods use simple `target ~ 1` formula
3. **Prediction**: Not all result objects have `.predict()` methods
4. **Model objects**: Some results don't include underlying model objects

## Future Enhancements

1. **Expand method coverage**: Add more methods from each module
2. **Smart formula building**: Automatically select covariates
3. **Cross-validation**: Built-in CV for model selection
4. **Visualization dashboard**: Interactive result exploration
5. **Pipeline builder**: Chain multiple analyses
6. **Automated reporting**: Generate LaTeX/HTML reports

## Support and Documentation

**Related Documentation**:
- `ADVANCED_TIME_SERIES.md` - Advanced time series methods
- `docs/advanced_analytics/CAUSAL_INFERENCE.md` - Causal inference guide
- Individual module docstrings

**Example Notebooks**:
- Create notebooks in `examples/econometric_suite/` for common workflows

**For Questions**:
- Check test files for usage examples
- Review individual module documentation
- Consult academic references in module docs

---

**Module 4D Status**: ✅ Complete
**Test Coverage**: 31/31 tests passing (100%)
**Lines of Code**: ~1,000 LOC (implementation) + ~500 LOC (tests)

**Integration**: All 6 econometric modules unified under single API
