# API Reference

Complete reference for the NBA MCP Analytics Platform.

## Table of Contents

- [EconometricSuite](#econometricsuite)
  - [Initialization](#initialization)
  - [Time Series Methods](#time-series-methods)
  - [Causal Inference Methods](#causal-inference-methods)
  - [Panel Data Methods](#panel-data-methods)
  - [Survival Analysis Methods](#survival-analysis-methods)
  - [Bayesian Methods](#bayesian-methods)
  - [Advanced Time Series Methods](#advanced-time-series-methods)
- [Streaming Analytics](#streaming-analytics)
- [Ensemble Methods](#ensemble-methods)
- [Exception Classes](#exception-classes)

---

## EconometricSuite

Main interface for econometric analysis. Provides unified access to 26+ statistical methods.

### Initialization

```python
EconometricSuite(
    data: pd.DataFrame,
    target: Optional[str] = None,
    time_col: Optional[str] = None,
    entity_col: Optional[str] = None,
    treatment_col: Optional[str] = None,
    outcome_col: Optional[str] = None,
    duration_col: Optional[str] = None,
    event_col: Optional[str] = None
)
```

**Parameters:**

- **data** (`pd.DataFrame`): Input dataset
- **target** (`str`, optional): Target variable for analysis
- **time_col** (`str`, optional): Time/date column for time series analysis
- **entity_col** (`str`, optional): Entity identifier for panel data
- **treatment_col** (`str`, optional): Treatment variable for causal inference
- **outcome_col** (`str`, optional): Outcome variable for causal inference
- **duration_col** (`str`, optional): Duration/time-to-event for survival analysis
- **event_col** (`str`, optional): Event indicator for survival analysis

**Raises:**

- `InvalidDataError`: If data is not a pandas DataFrame
- `InsufficientDataError`: If data is empty or has < 2 rows

**Example:**

```python
import pandas as pd
from mcp_server.econometric_suite import EconometricSuite

data = pd.read_csv('player_stats.csv')
suite = EconometricSuite(
    data=data,
    target='points',
    time_col='date'
)
```

---

### Time Series Methods

#### time_series_analysis()

Perform time series analysis using ARIMA, VAR, or Granger causality.

```python
time_series_analysis(
    method: str = "arima",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **method** (`str`): Time series method to use
  - `'arima'`: ARIMA model
  - `'auto_arima'`: Automatic ARIMA order selection
  - `'arimax'`: ARIMA with exogenous variables
  - `'var'`: Vector Autoregression
  - `'varmax'`: VAR with exogenous variables
  - `'sarimax'`: Seasonal ARIMA with exogenous variables
  - `'granger'`: Granger causality test
  - `'seasonal_decompose'`: Seasonal decomposition

**Method-Specific Parameters:**

**ARIMA:**
- `order` (`tuple`): (p, d, q) order (default: (1, 1, 1))
- `seasonal_order` (`tuple`): (P, D, Q, s) for seasonal ARIMA

**Auto ARIMA:**
- `max_p` (`int`): Maximum AR order (default: 5)
- `max_q` (`int`): Maximum MA order (default: 5)
- `max_d` (`int`): Maximum differencing order (default: 2)

**VAR:**
- `lags` (`int`): Number of lags (default: 1)
- `trend` (`str`): Trend type ('c', 'ct', 'ctt', 'n')

**Granger:**
- `max_lags` (`int`): Maximum lags to test (default: 4)

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Model-specific result object
  - `method_used`: Name of method used
  - `aic`, `bic`: Information criteria (when available)
  - `r_squared`: R-squared value (when available)

**Raises:**

- `MissingParameterError`: If target column not specified
- `InvalidDataError`: If target column not found in data
- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 30 observations
- `ModelFitError`: If model fitting fails

**Example:**

```python
# ARIMA forecasting
result = suite.time_series_analysis(
    method='arima',
    order=(2, 1, 2)
)
print(f"AIC: {result.result.aic:.2f}")

# Forecast next 10 periods
forecast = result.result.forecast(steps=10)
print(forecast)

# Auto ARIMA
result_auto = suite.time_series_analysis(method='auto_arima')
print(f"Best order: {result_auto.result.order}")

# Granger causality
result_granger = suite.time_series_analysis(
    method='granger',
    max_lags=5
)
print(result_granger.result)
```

---

### Causal Inference Methods

#### causal_analysis()

Estimate causal effects using matching, instrumental variables, or regression discontinuity.

```python
causal_analysis(
    treatment_col: Optional[str] = None,
    outcome_col: Optional[str] = None,
    method: str = "psm",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **treatment_col** (`str`, optional): Treatment variable (uses self.treatment_col if None)
- **outcome_col** (`str`, optional): Outcome variable (uses self.outcome_col if None)
- **method** (`str`): Causal inference method
  - `'psm'`: Propensity Score Matching
  - `'iv'`, `'instrumental_variables'`: Instrumental Variables (2SLS)
  - `'rdd'`, `'regression_discontinuity'`: Regression Discontinuity Design
  - `'did'`, `'difference_in_differences'`: Difference-in-Differences
  - `'doubly_robust'`: Doubly Robust Estimation
  - `'kernel'`, `'kernel_matching'`: Kernel Matching
  - `'radius'`, `'radius_matching'`: Radius Matching
  - `'synthetic'`, `'synthetic_control'`: Synthetic Control Method

**Method-Specific Parameters:**

**Propensity Score Matching (PSM):**
- `covariates` (`List[str]`): Covariates for matching
- `caliper` (`float`): Maximum propensity score distance (default: 0.1)
- `method` (`str`): Matching method ('nearest', 'greedy')

**Instrumental Variables (IV):**
- `instruments` (`List[str]`): Instrument variables (required)
- `formula` (`str`): Regression formula
- `robust` (`bool`): Use robust standard errors

**Regression Discontinuity (RDD):**
- `running_var` (`str`): Running variable (required)
- `cutoff` (`float`): Discontinuity cutoff (required)
- `bandwidth` (`float`): Bandwidth for local regression
- `polynomial_order` (`int`): Polynomial order (default: 1)

**Difference-in-Differences (DiD):**
- `time_col` (`str`): Time period indicator (required)
- `covariates` (`List[str]`): Additional covariates

**Doubly Robust:**
- `covariates` (`List[str]`): Covariates for both propensity and outcome models

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Causal effect estimates
  - `att`: Average Treatment Effect on Treated
  - `ate`: Average Treatment Effect (when available)

**Raises:**

- `MissingParameterError`: If treatment_col or outcome_col not specified
- `InvalidDataError`: If columns not found in data
- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 20 observations
- `ModelFitError`: If estimation fails

**Example:**

```python
# Propensity Score Matching
result_psm = suite.causal_analysis(
    treatment_col='home_game',
    outcome_col='win_probability',
    method='psm',
    covariates=['rest_days', 'opponent_strength'],
    caliper=0.15
)
print(f"ATT: {result_psm.result.att:.3f}")
print(f"SE: {result_psm.result.att_se:.3f}")

# Instrumental Variables
result_iv = suite.causal_analysis(
    treatment_col='payroll',
    outcome_col='wins',
    method='iv',
    instruments=['revenue', 'market_size'],
    robust=True
)

# Regression Discontinuity
result_rdd = suite.causal_analysis(
    treatment_col='all_star',
    outcome_col='endorsements',
    method='rdd',
    running_var='age',
    cutoff=25,
    bandwidth=3.0
)
```

---

### Panel Data Methods

#### panel_analysis()

Analyze panel data with fixed/random effects or dynamic panel GMM.

```python
panel_analysis(
    method: str = "fixed_effects",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **method** (`str`): Panel data method
  - `'fixed_effects'`, `'fe'`: Fixed Effects
  - `'random_effects'`, `'re'`: Random Effects
  - `'pooled_ols'`, `'pooled'`: Pooled OLS
  - `'first_diff'`, `'fd'`: First-Difference OLS
  - `'diff_gmm'`, `'arellano_bond'`: Difference GMM (Arellano-Bond)
  - `'sys_gmm'`, `'system_gmm'`, `'blundell_bond'`: System GMM (Blundell-Bond)
  - `'gmm_diagnostics'`: GMM diagnostic tests

**Method-Specific Parameters:**

**Fixed/Random Effects:**
- `formula` (`str`): Regression formula (optional)

**Dynamic Panel GMM:**
- `formula` (`str`): Model formula (required for GMM methods)
- `gmm_type` (`str`): 'one_step' or 'two_step'
- `max_lags` (`int`): Maximum instrument lags (default: 3)
- `collapse` (`bool`): Collapse instruments

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Panel model results
  - `r_squared`: R-squared value
  - `coefficients`: Estimated coefficients

**Raises:**

- `MissingParameterError`: If entity_col, time_col, or target not specified
- `InvalidDataError`: If columns not found in data
- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 10 observations
- `ModelFitError`: If model fitting fails

**Example:**

```python
# Fixed Effects
result_fe = suite.panel_analysis(method='fixed_effects')
print(result_fe.result.summary())

# Random Effects
result_re = suite.panel_analysis(method='random_effects')

# Arellano-Bond Difference GMM
result_gmm = suite.panel_analysis(
    method='diff_gmm',
    formula='wins ~ lag(wins, 1) + payroll + avg_age',
    gmm_type='two_step',
    max_lags=4
)
print(f"AR(2) p-value: {result_gmm.result.ar2_pvalue:.3f}")
print(f"Hansen J-test: {result_gmm.result.hansen_pvalue:.3f}")
```

---

### Survival Analysis Methods

#### survival_analysis()

Perform survival analysis with Cox, Kaplan-Meier, or competing risks models.

```python
survival_analysis(
    duration_col: Optional[str] = None,
    event_col: Optional[str] = None,
    method: str = "cox",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **duration_col** (`str`, optional): Duration variable (uses self.duration_col if None)
- **event_col** (`str`, optional): Event indicator (uses self.event_col if None)
- **method** (`str`): Survival analysis method
  - `'cox'`: Cox Proportional Hazards
  - `'kaplan_meier'`, `'km'`: Kaplan-Meier Estimator
  - `'parametric'`: Parametric Survival Models
  - `'competing_risks'`: Competing Risks Analysis
  - `'frailty'`: Frailty Model
  - `'fine_gray'`: Fine-Gray Competing Risks Regression
  - `'cure'`, `'cure_model'`: Mixture Cure Model
  - `'recurrent_events'`, `'pwp'`, `'ag'`, `'wlw'`: Recurrent Events Models

**Method-Specific Parameters:**

**Kaplan-Meier:**
- `groups` (`str`): Grouping variable for stratified analysis
- `alpha` (`float`): Confidence level (default: 0.05)
- `timeline` (`array`): Time points for estimation

**Parametric:**
- `model` (`str`): Distribution ('weibull', 'lognormal', 'loglogistic', 'exponential')
- `formula` (`str`): Regression formula

**Competing Risks:**
- `event_type_col` (`str`): Event type column (required)
- `event_types` (`List`): Event types to analyze (required)

**Fine-Gray:**
- `event_type_col` (`str`): Event type column (required)
- `event_of_interest` (any): Event of interest (required)
- `covariates` (`List[str]`): Covariate list

**Frailty:**
- `shared_frailty_col` (`str`): Shared frailty grouping variable
- `distribution` (`str`): Frailty distribution ('gamma', 'gaussian', 'inverse_gaussian')

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Survival model results
  - `aic`, `bic`: Information criteria (when available)
  - `log_likelihood`: Log-likelihood value

**Raises:**

- `MissingParameterError`: If duration_col or event_col not specified
- `InvalidDataError`: If columns not found in data
- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 10 observations
- `ModelFitError`: If model fitting fails

**Example:**

```python
# Cox Proportional Hazards
result_cox = suite.survival_analysis(
    duration_col='career_years',
    event_col='retired',
    method='cox'
)
print(f"AIC: {result_cox.result.aic:.2f}")

# Kaplan-Meier by position
result_km = suite.survival_analysis(
    duration_col='career_years',
    event_col='retired',
    method='kaplan_meier',
    groups='position'
)

# Parametric Weibull
result_weibull = suite.survival_analysis(
    duration_col='career_years',
    event_col='retired',
    method='parametric',
    model='weibull'
)
```

---

### Bayesian Methods

#### bayesian_time_series_analysis()

Perform Bayesian time series analysis with BVAR or structural models.

```python
bayesian_time_series_analysis(
    method: str = "bvar",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **method** (`str`): Bayesian time series method
  - `'bvar'`, `'bayesian_var'`: Bayesian VAR with Minnesota Prior
  - `'bsts'`, `'structural'`: Bayesian Structural Time Series (not yet implemented)
  - `'hierarchical_ts'`: Hierarchical Bayesian Time Series (not yet implemented)

**BVAR Parameters:**
- `var_names` (`List[str]`): Variable names for VAR (required or auto-detected)
- `lags` (`int`): Number of lags (default: 1)
- `draws` (`int`): MCMC draws (default: 2000)
- `tune` (`int`): MCMC tuning steps (default: 1000)
- `chains` (`int`): Number of chains (default: 4)
- `lambda1` (`float`): Overall tightness (default: 0.2)
- `lambda2` (`float`): Cross-variable shrinkage (default: 0.5)
- `lambda3` (`float`): Lag decay (default: 1.0)

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Bayesian model results with trace
  - `model`: PyMC model object
  - `waic`: WAIC (Watanabe-Akaike Information Criterion)

**Raises:**

- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 30 observations
- `MissingParameterError`: If var_names not specified
- `InvalidDataError`: If variables not found in data
- `ModelFitError`: If model fitting or sampling fails

**Example:**

```python
# Bayesian VAR
result_bvar = suite.bayesian_time_series_analysis(
    method='bvar',
    var_names=['points', 'assists', 'rebounds'],
    lags=2,
    draws=1000,
    tune=500
)
print(f"WAIC: {result_bvar.result.waic:.2f}")

# Access posterior samples
print(result_bvar.result.summary)
```

---

### Advanced Time Series Methods

#### advanced_time_series_analysis()

Perform advanced time series analysis with Kalman filters, Markov switching, or dynamic factor models.

```python
advanced_time_series_analysis(
    method: str = "kalman",
    **kwargs
) -> SuiteResult
```

**Parameters:**

- **method** (`str`): Advanced time series method
  - `'kalman'`: Kalman Filter
  - `'markov_switching'`, `'markov'`: Markov Switching Models
  - `'dynamic_factor'`: Dynamic Factor Model
  - `'structural'`: Structural Time Series (Unobserved Components)

**Method-Specific Parameters:**

**Kalman Filter:**
- `model` (`str`): State space model ('local_level', 'local_linear_trend', 'seasonal')
- `exog` (`array`): Exogenous variables

**Markov Switching:**
- `n_regimes` (`int`): Number of regimes (default: 2)
- `regime_type` (`str`): 'mean_shift', 'ar', 'variance_switch'
- `switching_variance` (`bool`): Whether variance switches between regimes

**Dynamic Factor:**
- `data` (`DataFrame`): Multivariate data for factor extraction
- `n_factors` (`int`): Number of factors (default: 1)
- `factor_order` (`int`): AR order for factors (default: 2)

**Structural:**
- `level` (`bool`): Include level component (default: True)
- `trend` (`bool`): Include trend component (default: False)
- `seasonal` (`int`): Seasonal period (None for no seasonality)
- `cycle` (`bool`): Include cycle component (default: False)

**Returns:**

- `SuiteResult`: Result object containing:
  - `result`: Model-specific results
  - `aic`, `bic`: Information criteria (when available)
  - `log_likelihood`: Log-likelihood value

**Raises:**

- `MissingParameterError`: If target not specified
- `InvalidDataError`: If target column not found in data
- `InvalidParameterError`: If method name is invalid
- `InsufficientDataError`: If < 30 observations
- `ModelFitError`: If model fitting fails

**Example:**

```python
# Kalman Filter
result_kalman = suite.advanced_time_series_analysis(
    method='kalman',
    model='local_linear_trend'
)
print(f"Log-likelihood: {result_kalman.result.log_likelihood:.2f}")

# Markov Switching
result_markov = suite.advanced_time_series_analysis(
    method='markov_switching',
    n_regimes=2,
    regime_type='mean_shift'
)
print(f"AIC: {result_markov.result.aic:.2f}")

# Dynamic Factor Model
result_dfm = suite.advanced_time_series_analysis(
    method='dynamic_factor',
    n_factors=2,
    factor_order=2
)
```

---

## Streaming Analytics

Real-time event processing with anomaly detection.

### StreamingAnalyzer

```python
from mcp_server.streaming_analytics import StreamingAnalyzer, StreamEvent, StreamEventType

analyzer = StreamingAnalyzer(
    window_seconds: float = 300.0,
    enable_metrics: bool = True
)
```

**Parameters:**

- **window_seconds** (`float`): Sliding window size in seconds (default: 300.0)
- **enable_metrics** (`bool`): Enable performance metrics tracking

**Methods:**

#### process_event()

Process a single event and return aggregated statistics.

```python
process_event(event: StreamEvent) -> Dict[str, Any]
```

**Parameters:**

- **event** (`StreamEvent`): Event to process

**Returns:**

- `Dict`: Aggregated results and metrics

#### detect_anomalies()

Detect anomalies in a metric using z-score.

```python
detect_anomalies(
    metric: str,
    threshold_std: float = 3.0
) -> List[Dict[str, Any]]
```

**Parameters:**

- **metric** (`str`): Metric name to check for anomalies
- **threshold_std** (`float`): Z-score threshold (default: 3.0)

**Returns:**

- `List[Dict]`: Detected anomalies with details

**Example:**

```python
from datetime import datetime

# Create analyzer
analyzer = StreamingAnalyzer(window_seconds=300)

# Process events
event = StreamEvent(
    event_type=StreamEventType.SHOT,
    player_id='player_123',
    timestamp=datetime.now(),
    data={'made': True, 'points': 3}
)

result = analyzer.process_event(event)
print(f"Latency: {result['processing_latency_ms']:.2f}ms")

# Detect anomalies
anomalies = analyzer.detect_anomalies(metric='points', threshold_std=2.5)
for anomaly in anomalies:
    print(f"Anomaly: {anomaly['value']:.1f} (z={anomaly['z_score']:.2f})")
```

---

## Ensemble Methods

Combine multiple models for robust predictions.

### WeightedEnsemble

Weighted averaging ensemble with inverse RMSE weighting.

```python
from mcp_server.ensemble import WeightedEnsemble

ensemble = WeightedEnsemble(
    models: List[Any],
    weights: Optional[np.ndarray] = None
)
```

**Parameters:**

- **models** (`List`): List of fitted models
- **weights** (`array`, optional): Manual weights (auto-computed if None)

**Methods:**

#### predict()

Generate weighted ensemble predictions.

```python
predict(n_steps: int = 10) -> EnsembleResult
```

**Returns:**

- `EnsembleResult`: Predictions with uncertainty and weights

### StackingEnsemble

Stacking ensemble with meta-learning.

```python
from mcp_server.ensemble import StackingEnsemble

ensemble = StackingEnsemble(
    models: List[Any],
    meta_learner: str = 'ridge'
)
```

**Parameters:**

- **models** (`List`): List of base models
- **meta_learner** (`str`): 'ridge' or 'lasso'

**Example:**

```python
# Train multiple models
model1 = suite.time_series_analysis(method='arima', order=(1,1,1))
model2 = suite.time_series_analysis(method='arima', order=(2,1,2))
model3 = suite.time_series_analysis(method='auto_arima')

# Create weighted ensemble
ensemble = WeightedEnsemble([model1.result, model2.result, model3.result])
predictions = ensemble.predict(n_steps=10)

print(f"Forecast: {predictions.predictions}")
print(f"Weights: {predictions.model_weights}")
```

---

## Exception Classes

Custom exceptions for better error handling.

### Exception Hierarchy

```
NBAAnalyticsError (base)
├── DataError
│   ├── InsufficientDataError
│   ├── InvalidDataError
│   ├── MissingDataError
│   └── DataShapeError
├── ModelError
│   ├── ModelFitError
│   ├── ConvergenceError
│   ├── ValidationError
│   └── PredictionError
├── ConfigurationError
│   ├── InvalidParameterError
│   ├── MissingParameterError
│   └── IncompatibleParametersError
└── ComputationError
    ├── NumericalError
    ├── TimeoutError
    └── ResourceError
```

### Exception Details

All exceptions include:
- `message`: Human-readable error message
- `error_code`: Machine-readable error code
- `details`: Dictionary with error context

**Methods:**

- `to_dict()`: Convert exception to dictionary for logging
- `__str__()`: String representation with details

**Example:**

```python
from mcp_server.exceptions import (
    InsufficientDataError,
    InvalidParameterError,
    validate_data_shape,
    validate_parameter
)

try:
    suite = EconometricSuite(data=small_data, target='points')
    result = suite.time_series_analysis(method='arima')
except InsufficientDataError as e:
    print(f"Error: {e.message}")
    print(f"Required: {e.details['required']}")
    print(f"Actual: {e.details['actual']}")
except InvalidParameterError as e:
    print(f"Invalid: {e.details['parameter']} = {e.details['value']}")
    print(f"Valid options: {e.details['valid_values']}")
```

---

## Utility Functions

### Validation Helpers

#### validate_data_shape()

```python
from mcp_server.exceptions import validate_data_shape

validate_data_shape(
    data,
    min_rows: Optional[int] = None,
    min_cols: Optional[int] = None,
    expected_shape: Optional[tuple] = None
)
```

**Raises:**
- `InsufficientDataError`: If not enough rows
- `DataShapeError`: If shape mismatch

#### validate_parameter()

```python
from mcp_server.exceptions import validate_parameter

validate_parameter(
    param_name: str,
    value: Any,
    valid_values: Optional[list] = None,
    value_type: Optional[type] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
)
```

**Raises:**
- `InvalidParameterError`: If validation fails

**Example:**

```python
# Validate data shape
validate_data_shape(data, min_rows=30, min_cols=3)

# Validate parameter
validate_parameter('method', method, valid_values=['arima', 'var'])
validate_parameter('alpha', alpha, min_value=0.0, max_value=1.0)
```

---

## Common Patterns

### Error Handling Pattern

```python
from mcp_server.econometric_suite import EconometricSuite
from mcp_server.exceptions import NBAAnalyticsError, InsufficientDataError

try:
    suite = EconometricSuite(data=data, target='points')
    result = suite.time_series_analysis(method='arima')
except InsufficientDataError as e:
    print(f"Need more data: {e.details}")
except NBAAnalyticsError as e:
    # Catch all NBA analytics errors
    logging.error(e.to_dict())
```

### Model Comparison Pattern

```python
# Train multiple models
results = []
for order in [(1,1,1), (2,1,2), (3,1,3)]:
    result = suite.time_series_analysis(method='arima', order=order)
    results.append((order, result.result.aic))

# Select best model
best_order, best_aic = min(results, key=lambda x: x[1])
print(f"Best model: ARIMA{best_order} (AIC={best_aic:.2f})")
```

---

## Individual Method Reference

The following sections document each method in detail with comprehensive examples.

---

### Time Series Module Methods

The `TimeSeriesAnalyzer` class provides individual methods for time series analysis.

```python
from mcp_server.time_series import TimeSeriesAnalyzer
import pandas as pd

# Initialize analyzer
data = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100, freq='D'),
    'points': [25, 28, 22, 30, ...]  # Player points per game
})

analyzer = TimeSeriesAnalyzer(
    data=data,
    target_column='points',
    time_column='date'
)
```

#### arima() / fit_arima()

Fit ARIMA (AutoRegressive Integrated Moving Average) model to univariate time series.

**When to use:** Time series forecasting, trend analysis, detecting patterns in sequential data (e.g., player performance trends, team winning streaks).

```python
fit_arima(
    order: Tuple[int, int, int],
    seasonal_order: Optional[Tuple[int, int, int, int]] = None,
    **kwargs
) -> ARIMAModelResult
```

**Parameters:**

- **order** (`Tuple[int, int, int]`): (p, d, q) ARIMA order
  - **p**: Autoregressive order (number of lag observations)
  - **d**: Degree of differencing (number of times data is differenced)
  - **q**: Moving average order (size of moving average window)
- **seasonal_order** (`Tuple[int, int, int, int]`, optional): (P, D, Q, s) seasonal ARIMA order
  - **P, D, Q**: Seasonal AR, differencing, MA orders
  - **s**: Seasonal period (e.g., 7 for weekly, 12 for monthly)
- **kwargs**: Additional arguments passed to `statsmodels.tsa.arima.model.ARIMA`

**Returns:**

- **ARIMAModelResult**: Contains:
  - `model`: Fitted statsmodels ARIMA model
  - `order`: (p, d, q) order used
  - `seasonal_order`: Seasonal order if specified
  - `aic`: Akaike Information Criterion
  - `bic`: Bayesian Information Criterion
  - `summary`: Full model summary string

**Raises:**

- `InvalidParameterError`: If order is invalid (negative values, all zeros)
- `InsufficientDataError`: If < 30 observations
- `ModelFitError`: If ARIMA fitting fails (e.g., non-invertibility)

**Example:**

```python
# Basic ARIMA(1,1,1) for player points forecasting
result = analyzer.fit_arima(order=(1, 1, 1))
print(f"AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")

# Forecast next 10 games
forecast = result.model.forecast(steps=10)
print(f"Next 10 games forecast: {forecast}")

# Get confidence intervals
forecast_result = result.model.get_forecast(steps=10)
conf_int = forecast_result.conf_int()
print(f"95% CI: {conf_int}")

# Seasonal ARIMA for weekly patterns
result_seasonal = analyzer.fit_arima(
    order=(1, 1, 1),
    seasonal_order=(1, 1, 1, 7)  # Weekly seasonality
)
```

**References:**
- Box, G. E., Jenkins, G. M., & Reinsel, G. C. (2015). Time Series Analysis: Forecasting and Control
- Related methods: `auto_arima()`, `fit_arimax()`

---

#### auto_arima()

Automatically select the best ARIMA model using grid search over parameter space.

**When to use:** When you don't know the optimal ARIMA order, want to compare multiple models, or need data-driven model selection.

```python
auto_arima(
    seasonal: bool = False,
    m: int = 1,
    max_p: int = 5,
    max_d: int = 2,
    max_q: int = 5,
    max_P: int = 2,
    max_D: int = 1,
    max_Q: int = 2,
    information_criterion: str = "aic"
) -> ARIMAModelResult
```

**Parameters:**

- **seasonal** (`bool`): Whether to fit seasonal ARIMA models (default: False)
- **m** (`int`): Seasonal period if seasonal=True (default: 1)
- **max_p** (`int`): Maximum autoregressive order to try (default: 5)
- **max_d** (`int`): Maximum differencing order to try (default: 2)
- **max_q** (`int`): Maximum moving average order to try (default: 5)
- **max_P** (`int`): Maximum seasonal AR order (default: 2)
- **max_D** (`int`): Maximum seasonal differencing (default: 1)
- **max_Q** (`int`): Maximum seasonal MA order (default: 2)
- **information_criterion** (`str`): 'aic' or 'bic' for model selection

**Returns:**

- **ARIMAModelResult**: Best model based on information criterion

**Raises:**

- `InsufficientDataError`: If < 30 observations
- `ModelFitError`: If no valid models can be fitted

**Example:**

```python
# Automatic model selection
result = analyzer.auto_arima(
    max_p=3,
    max_d=2,
    max_q=3,
    information_criterion='aic'
)
print(f"Best order: ARIMA{result.order}")
print(f"AIC: {result.aic:.2f}")

# Seasonal auto-selection for weekly data
result_seasonal = analyzer.auto_arima(
    seasonal=True,
    m=7,  # Weekly seasonality
    max_p=2,
    max_q=2,
    max_P=1,
    max_Q=1
)
print(f"Best seasonal model: ARIMA{result_seasonal.order}x{result_seasonal.seasonal_order}")
```

**NBA Analytics Use Case:**

```python
# Find best model for player scoring trends
player_data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82, freq='D'),  # Full season
    'points': player_points_data
})

analyzer = TimeSeriesAnalyzer(player_data, 'points', 'date')
best_model = analyzer.auto_arima(seasonal=False, max_p=5, max_q=5)

# Forecast remaining season performance
forecast = best_model.model.forecast(steps=20)
print(f"Projected scoring average: {forecast.mean():.1f} PPG")
```

**References:**
- Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: principles and practice
- Related methods: `fit_arima()`

---

#### arimax() / fit_arimax()

Fit ARIMAX model (ARIMA with exogenous/external variables).

**When to use:** When external factors influence your time series (e.g., player performance affected by rest days, opponent strength, home/away status).

```python
fit_arimax(
    order: Tuple[int, int, int],
    exog: Union[pd.DataFrame, np.ndarray],
    seasonal_order: Optional[Tuple[int, int, int, int]] = None,
    exog_forecast: Optional[Union[pd.DataFrame, np.ndarray]] = None,
    **kwargs
) -> ARIMAXResult
```

**Parameters:**

- **order** (`Tuple[int, int, int]`): (p, d, q) ARIMA order
- **exog** (`DataFrame` or `ndarray`): Exogenous variables (must have same length as time series)
- **seasonal_order** (`Tuple[int, int, int, int]`, optional): Seasonal order
- **exog_forecast** (`DataFrame` or `ndarray`, optional): Future exogenous values for forecasting
- **kwargs**: Additional arguments for SARIMAX model

**Returns:**

- **ARIMAXResult**: Contains:
  - `model`: Fitted SARIMAX model
  - `order`, `seasonal_order`: Model orders
  - `exog_names`: Names of exogenous variables
  - `exog_coefficients`: Coefficients for exogenous variables
  - `aic`, `bic`, `log_likelihood`: Model fit statistics
  - `summary`: Full summary string

**Raises:**

- `InvalidDataError`: If exog shape doesn't match time series length
- `MissingParameterError`: If exog_forecast needed but not provided
- `ModelFitError`: If ARIMAX fitting fails

**Example:**

```python
# Player performance with rest days and opponent strength
exog_vars = pd.DataFrame({
    'rest_days': [1, 0, 2, 1, 0, ...],  # Days of rest before game
    'opp_rating': [112.3, 108.7, 115.2, ...],  # Opponent defensive rating
    'home_game': [1, 0, 1, 1, 0, ...]  # 1=home, 0=away
})

result = analyzer.fit_arimax(
    order=(1, 1, 1),
    exog=exog_vars
)

print(f"Exogenous coefficients:")
print(result.exog_coefficients)

# Forecast with future exogenous variables
future_exog = pd.DataFrame({
    'rest_days': [2, 1, 0, 1, 1],
    'opp_rating': [110.0, 113.5, 109.2, 111.8, 107.5],
    'home_game': [1, 1, 0, 0, 1]
})

forecast = result.model.forecast(steps=5, exog=future_exog)
print(f"Next 5 games forecast: {forecast}")
```

**NBA Analytics Use Case:**

```python
# Predict team wins accounting for schedule difficulty
team_data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82),
    'wins': cumulative_wins,
    'strength_of_schedule': sos_ratings,
    'injuries': injury_count,
    'back_to_back': [0, 1, 0, 0, 1, ...]
})

analyzer = TimeSeriesAnalyzer(team_data, 'wins', 'date')
result = analyzer.fit_arimax(
    order=(2, 1, 1),
    exog=team_data[['strength_of_schedule', 'injuries', 'back_to_back']]
)

# See how much each factor matters
print("Impact of exogenous variables:")
for var, coef in result.exog_coefficients.items():
    print(f"  {var}: {coef:.3f}")
```

**References:**
- Related methods: `fit_arima()`, `fit_sarimax()`

---

#### sarimax() / fit_sarimax()

Fit SARIMAX model (Seasonal ARIMA with exogenous variables).

**When to use:** Time series with both seasonal patterns and external influences (e.g., playoff performance with seasonal effects and team changes).

```python
# Note: SARIMAX is typically accessed via fit_arimax with seasonal_order
fit_arimax(
    order=(p, d, q),
    seasonal_order=(P, D, Q, s),
    exog=external_variables
)
```

**Example:**

```python
# Team attendance with seasonal patterns and winning percentage
attendance_data = pd.DataFrame({
    'date': pd.date_range('2020-10-01', periods=246, freq='W'),  # 3 seasons weekly
    'attendance': weekly_attendance,
    'win_pct': rolling_win_percentage,
    'star_players': star_count
})

analyzer = TimeSeriesAnalyzer(attendance_data, 'attendance', 'date')
result = analyzer.fit_arimax(
    order=(1, 1, 1),
    seasonal_order=(1, 0, 1, 52),  # Annual seasonality (weekly data)
    exog=attendance_data[['win_pct', 'star_players']]
)

# Forecast next season attendance
future_exog = pd.DataFrame({
    'win_pct': [0.65] * 52,  # Projected win percentage
    'star_players': [3] * 52  # Expected star players
})
forecast = result.model.forecast(steps=52, exog=future_exog)
print(f"Average projected attendance: {forecast.mean():.0f}")
```

---

#### var() / fit_var()

Fit Vector Autoregression model for multivariate time series (multiple interrelated variables).

**When to use:** Analyzing relationships between multiple time series that influence each other (e.g., points, assists, rebounds; or multiple players' performances).

```python
fit_var(
    endog_data: pd.DataFrame,
    maxlags: Optional[int] = None,
    ic: str = "aic",
    trend: str = "c"
) -> VARResult
```

**Parameters:**

- **endog_data** (`DataFrame`): Multivariate time series data (each column = one variable)
- **maxlags** (`int`, optional): Maximum lags to consider (if None, uses AIC to select)
- **ic** (`str`): Information criterion for lag selection: 'aic', 'bic', 'hqic', 'fpe' (default: 'aic')
- **trend** (`str`): Deterministic trend: 'c' (constant), 'ct' (constant+trend), 'ctt' (constant+trend+trend²), 'n' (none)

**Returns:**

- **VARResult**: Contains:
  - `model`: Fitted VAR model
  - `order`: Selected lag order (p)
  - `n_variables`: Number of variables in system
  - `variable_names`: Names of variables
  - `aic`, `bic`, `hqic`, `fpe`: Model selection criteria
  - `log_likelihood`: Log-likelihood value
  - `coef_summary`: Coefficient estimates DataFrame
  - `granger_causality`: Optional Granger causality test results

**Raises:**

- `InvalidDataError`: If endog_data is not a DataFrame or has < 2 columns
- `InsufficientDataError`: If < 30 observations
- `ModelFitError`: If VAR fitting fails

**Example:**

```python
# Multi-dimensional player performance analysis
player_stats = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100),
    'points': player_points,
    'assists': player_assists,
    'rebounds': player_rebounds
})

analyzer = TimeSeriesAnalyzer(player_stats, 'points', 'date')
result = analyzer.fit_var(
    endog_data=player_stats[['points', 'assists', 'rebounds']],
    maxlags=5,
    ic='aic'
)

print(f"Optimal lag order: {result.order}")
print(f"AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")

# Forecast all variables simultaneously
forecast = result.model.forecast(result.model.y, steps=10)
print(f"10-game forecast:")
print(f"  Points: {forecast[:, 0]}")
print(f"  Assists: {forecast[:, 1]}")
print(f"  Rebounds: {forecast[:, 2]}")

# Analyze impulse responses (how one variable affects others)
irf = result.model.irf(periods=10)
irf.plot()
```

**NBA Analytics Use Case:**

```python
# Analyze team offense-defense dynamics
team_data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82),
    'offensive_rating': offensive_ratings,
    'defensive_rating': defensive_ratings,
    'pace': pace_values
})

analyzer = TimeSeriesAnalyzer(team_data, 'offensive_rating', 'date')
result = analyzer.fit_var(
    endog_data=team_data[['offensive_rating', 'defensive_rating', 'pace']],
    maxlags=3
)

# Test if offensive rating Granger-causes defensive rating
# (Do teams that score more play worse defense?)
from statsmodels.tsa.stattools import grangercausalitytests
granger_result = grangercausalitytests(
    team_data[['defensive_rating', 'offensive_rating']],
    maxlag=3
)
```

**References:**
- Lütkepohl, H. (2005). New Introduction to Multiple Time Series Analysis
- Related methods: `fit_varmax()`, `granger_causality_test()`

---

#### varmax() / fit_varmax()

Fit VARMAX model (Vector Autoregression Moving Average with exogenous variables).

**When to use:** Multivariate time series with both MA components and external influences. More flexible than VAR alone.

```python
fit_varmax(
    endog_data: pd.DataFrame,
    order: Tuple[int, int] = (1, 0),
    exog: Optional[Union[pd.DataFrame, np.ndarray]] = None,
    trend: str = "c",
    **kwargs
) -> VARMAXResult
```

**Parameters:**

- **endog_data** (`DataFrame`): Multivariate endogenous time series
- **order** (`Tuple[int, int]`): (p, q) for VAR and VMA orders
  - **p**: VAR lag order
  - **q**: VMA lag order
- **exog** (`DataFrame` or `ndarray`, optional): Exogenous variables
- **trend** (`str`): Trend specification: 'n', 'c', 't', 'ct'
- **kwargs**: Additional arguments for VARMAX model

**Returns:**

- **VARMAXResult**: Contains model, orders, variable names, AIC, BIC, log-likelihood, summary

**Raises:**

- `InvalidDataError`: If data shape or types invalid
- `ModelFitError`: If VARMAX fitting fails

**Example:**

```python
# Player offensive stats with coaching changes
player_stats = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100),
    'points': points_data,
    'field_goal_pct': fg_pct_data
})

exog_vars = pd.DataFrame({
    'coach_change': [0, 0, 1, 0, ...],  # Indicator for coaching change
    'minutes': minutes_data
})

result = analyzer.fit_varmax(
    endog_data=player_stats[['points', 'field_goal_pct']],
    order=(2, 1),  # VAR(2) + MA(1)
    exog=exog_vars,
    trend='c'
)

print(f"AIC: {result.aic:.2f}")
print(result.summary)
```

**References:**
- Related methods: `fit_var()`, `fit_arimax()`

---

#### granger_causality() / granger_causality_test()

Test whether one time series helps predict another (Granger causality).

**When to use:** Determining if one variable "causes" another in the predictive sense (e.g., does player A's performance predict player B's?).

```python
granger_causality_test(
    caused_series: Union[pd.Series, str],
    causing_series: Union[pd.Series, str],
    maxlag: int = 4,
    addconst: bool = True
) -> GrangerCausalityResult
```

**Parameters:**

- **caused_series** (`Series` or `str`): Variable being predicted (effect)
- **causing_series** (`Series` or `str`): Variable being tested as predictor (potential cause)
- **maxlag** (`int`): Maximum number of lags to test (default: 4)
- **addconst** (`bool`): Add constant term to regression (default: True)

**Returns:**

- **GrangerCausalityResult**: Contains:
  - `caused_variable`: Name of dependent variable
  - `causing_variable`: Name of independent variable
  - `max_lag`: Maximum lag tested
  - `test_results`: Dict mapping lag → {statistic, p_value, df_denom, df_num}
  - `min_p_value`: Minimum p-value across all lags
  - `significant_at_5pct`: Boolean indicating if significant at 5% level

**Raises:**

- `InvalidDataError`: If series not found or invalid
- `InsufficientDataError`: If too few observations for lags

**Example:**

```python
# Does player assist rate predict scoring?
player_data = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100),
    'points': points_per_game,
    'assist_rate': assist_rate
})

analyzer = TimeSeriesAnalyzer(player_data, 'points', 'date')
result = analyzer.granger_causality_test(
    caused_series='points',
    causing_series='assist_rate',
    maxlag=5
)

if result.significant_at_5pct:
    print(f"Assist rate DOES Granger-cause points (p={result.min_p_value:.4f})")
else:
    print(f"No Granger causality detected")

# Print results by lag
for lag, tests in result.test_results.items():
    print(f"Lag {lag}: F-stat={tests['statistic']:.2f}, p={tests['p_value']:.4f}")
```

**NBA Analytics Use Case:**

```python
# Does team pace predict offensive efficiency?
team_data = pd.DataFrame({
    'game': range(82),
    'pace': pace_by_game,
    'offensive_rating': off_rtg_by_game
})

analyzer = TimeSeriesAnalyzer(team_data, 'offensive_rating', time_column=None)
analyzer.data.index = pd.date_range('2023-10-01', periods=82)

result = analyzer.granger_causality_test(
    caused_series='offensive_rating',
    causing_series='pace',
    maxlag=3
)
```

**References:**
- Granger, C. W. J. (1969). "Investigating causal relations by econometric models and cross-spectral methods"
- Related methods: `fit_var()`

---

#### seasonal_decompose() / decompose()

Decompose time series into trend, seasonal, and residual components.

**When to use:** Understanding underlying patterns, detecting anomalies, detrending data before modeling.

```python
decompose(
    model: str = "additive",
    period: Optional[int] = None,
    method: str = "seasonal_decompose"
) -> DecompositionResult
```

**Parameters:**

- **model** (`str`): 'additive' (Y = T + S + R) or 'multiplicative' (Y = T × S × R)
  - Use additive when seasonal variation is constant
  - Use multiplicative when seasonal variation scales with level
- **period** (`int`, optional): Seasonal period (auto-inferred from frequency if None)
  - Daily data: 7 (weekly), 30 (monthly), 365 (yearly)
  - Weekly data: 52 (yearly)
  - Monthly data: 12 (yearly)
- **method** (`str`): 'seasonal_decompose' (classical) or 'stl' (robust STL)

**Returns:**

- **DecompositionResult**: Contains:
  - `observed`: Original series
  - `trend`: Trend component
  - `seasonal`: Seasonal component
  - `residual`: Residual component
  - `model`: Model type used
  - `period`: Period used
  - `plot_components()`: Method to visualize decomposition

**Raises:**

- `InvalidParameterError`: If period invalid or model unknown
- `InsufficientDataError`: If not enough data for decomposition

**Example:**

```python
# Decompose player performance to find trends and patterns
player_data = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=200, freq='D'),
    'points': daily_points
})

analyzer = TimeSeriesAnalyzer(player_data, 'points', 'date')
result = analyzer.decompose(
    model='additive',
    period=7,  # Weekly seasonality
    method='stl'  # Use robust STL
)

print(f"Trend (average): {result.trend.mean():.2f}")
print(f"Seasonal strength: {result.seasonal.std():.2f}")
print(f"Residual std: {result.residual.std():.2f}")

# Visualize components
import matplotlib.pyplot as plt
fig = result.plot_components()
plt.savefig('decomposition.png')

# Check if weekday matters
seasonal_by_day = result.seasonal.iloc[:7]
print(f"Day-of-week effects: {seasonal_by_day.values}")
```

**NBA Analytics Use Case:**

```python
# Identify team performance trends across a season
team_data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82),
    'point_differential': point_diff_per_game
})

analyzer = TimeSeriesAnalyzer(team_data, 'point_differential', 'date')
result = analyzer.decompose(model='additive', period=10)  # 10-game cycles

# Is team improving or declining?
trend_change = result.trend.iloc[-10].mean() - result.trend.iloc[:10].mean()
if trend_change > 0:
    print(f"Team improving: +{trend_change:.1f} point differential trend")
else:
    print(f"Team declining: {trend_change:.1f} point differential trend")
```

**References:**
- Cleveland, R. B., et al. (1990). "STL: A Seasonal-Trend Decomposition Procedure Based on Loess"
- Related methods: `detect_trend()`, `test_stationarity()`

---

#### exponential_smoothing()

*Note: If this method exists, document it. Otherwise, note it's not yet implemented.*

**Status:** Check implementation status in time_series.py

---

### Panel Data Module Methods

The `PanelDataAnalyzer` class provides methods for analyzing panel/longitudinal data with entity and time dimensions.

```python
from mcp_server.panel_data import PanelDataAnalyzer
import pandas as pd

# Initialize analyzer with panel data
data = pd.DataFrame({
    'player_id': [1, 1, 1, 2, 2, 2, ...],  # Entity dimension
    'season': [2021, 2022, 2023, 2021, 2022, 2023, ...],  # Time dimension
    'points': [25.3, 27.1, 28.5, 18.2, 19.8, 21.1, ...],
    'minutes': [32.1, 34.5, 35.2, 28.3, 30.1, 31.5, ...],
    'age': [24, 25, 26, 22, 23, 24, ...]
})

analyzer = PanelDataAnalyzer(
    data=data,
    entity_col='player_id',
    time_col='season'
)
```

#### pooled_ols()

Estimate pooled OLS regression ignoring panel structure (treats all observations as independent).

**When to use:** Baseline comparison, when panel structure doesn't matter, or for hypothesis testing against FE/RE models.

```python
pooled_ols(formula: str) -> PanelModelResult
```

**Parameters:**

- **formula** (`str`): Regression formula in Patsy format (e.g., 'points ~ minutes + age + C(position)')

**Returns:**

- **PanelModelResult**: Contains:
  - `coefficients`: Parameter estimates
  - `std_errors`: Standard errors
  - `t_stats`, `p_values`: Test statistics
  - `r_squared`, `adj_r_squared`: Goodness of fit
  - `f_statistic`, `f_pvalue`: Overall model test
  - `n_obs`: Number of observations
  - `model_type`: 'pooled_ols'
  - `summary`: Full regression summary

**Raises:**

- `InvalidParameterError`: If formula is invalid
- `InsufficientDataError`: If not enough observations
- `ModelFitError`: If estimation fails

**Example:**

```python
# Basic pooled OLS
result = analyzer.pooled_ols('points ~ minutes + age + experience')
print(result.summary)
print(f"R-squared: {result.r_squared:.3f}")

# Check coefficient significance
for var, coef in result.coefficients.items():
    pval = result.p_values[var]
    sig = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''
    print(f"{var}: {coef:.3f} {sig}")
```

**NBA Analytics Use Case:**

```python
# Analyze player scoring across multiple seasons
# (ignoring player-specific effects)
result = analyzer.pooled_ols('points ~ minutes + age + usage_rate + team_pace')

# Interpretation:
# - Assumes all players respond identically to variables
# - Ignores player-specific baseline talent
# - Use as baseline before FE/RE models
```

**References:**
- Related methods: `fixed_effects()`, `random_effects()`, `f_test_effects()`

---

#### fixed_effects() / fe()

Estimate fixed effects (within) model that controls for time-invariant entity characteristics.

**When to use:** When you suspect unobserved entity-specific factors (player talent, team culture) correlate with regressors. Removes omitted variable bias from time-invariant heterogeneity.

```python
fixed_effects(
    formula: str,
    entity_effects: bool = True,
    time_effects: bool = False
) -> PanelModelResult
```

**Parameters:**

- **formula** (`str`): Regression formula
- **entity_effects** (`bool`): Include entity fixed effects (default: True)
- **time_effects** (`bool`): Include time fixed effects (default: False)

**Returns:**

- **PanelModelResult**: Panel regression results with FE adjustments

**Raises:**

- `InvalidParameterError`: If formula invalid
- `ModelFitError`: If estimation fails (e.g., insufficient within-variation)

**Example:**

```python
# Player fixed effects (controls for player talent)
result_fe = analyzer.fixed_effects(
    'points ~ minutes + age',
    entity_effects=True,
    time_effects=False
)

print(f"Within R-squared: {result_fe.r_squared:.3f}")
print(result_fe.coefficients)

# Two-way fixed effects (entity + time)
result_twoway = analyzer.fixed_effects(
    'points ~ minutes + team_pace',
    entity_effects=True,
    time_effects=True  # Controls for league-wide trends
)
```

**NBA Analytics Use Case:**

```python
# Analyze effect of minutes on scoring, controlling for player talent
result = analyzer.fixed_effects(
    'points ~ minutes + usage_rate + three_pt_attempts',
    entity_effects=True,
    time_effects=True
)

# Interpretation:
# - Coefficients show within-player effects over time
# - Controls for player-specific talent (fixed effects absorb it)
# - time_effects=True controls for league-wide scoring trends
# - Only uses variation WITHIN each player across seasons

# Example: "Each additional minute increases scoring by X points,
# holding player talent and league trends constant"
```

**Technical Notes:**
- FE "de-means" variables within each entity
- Only time-varying regressors can be estimated
- Robust to correlation between unobserved effects and regressors

**References:**
- Wooldridge, J. M. (2010). Econometric Analysis of Cross Section and Panel Data
- Related methods: `random_effects()`, `hausman_test()`, `first_difference()`

---

#### random_effects() / re()

Estimate random effects (GLS) model assuming uncorrelated entity-specific effects.

**When to use:** When entity effects are uncorrelated with regressors (use Hausman test to check). More efficient than FE if assumption holds.

```python
random_effects(formula: str) -> PanelModelResult
```

**Parameters:**

- **formula** (`str`): Regression formula

**Returns:**

- **PanelModelResult**: Random effects estimation results

**Raises:**

- `ModelFitError`: If RE estimation fails

**Example:**

```python
# Random effects estimation
result_re = analyzer.random_effects('points ~ minutes + age + experience')
print(result_re.summary)

# Compare with FE using Hausman test
hausman = analyzer.hausman_test('points ~ minutes + age')
if hausman['p_value'] < 0.05:
    print("Use Fixed Effects (RE assumption violated)")
else:
    print("Random Effects is appropriate")
```

**NBA Analytics Use Case:**

```python
# Analyze career trajectories with random player effects
result = analyzer.random_effects('points ~ age + age_squared + minutes')

# When to use RE over FE:
# - You want to estimate time-invariant variables (draft position, college)
# - Player effects uncorrelated with regressors
# - More efficient estimates if assumption holds

# Always test with hausman_test() first!
```

**References:**
- Related methods: `fixed_effects()`, `hausman_test()`

---

#### first_difference() / fd()

Estimate first-difference model to remove fixed effects via differencing.

**When to use:** Alternative to FE that eliminates time-invariant effects. Useful when FE estimation has numerical issues or for testing robustness.

```python
first_difference(
    formula: str,
    cluster_entity: bool = True
) -> FirstDifferenceResult
```

**Parameters:**

- **formula** (`str`): Regression formula
- **cluster_entity** (`bool`): Cluster standard errors by entity (default: True)

**Returns:**

- **FirstDifferenceResult**: Contains differenced estimates, diagnostics, and original data info

**Raises:**

- `ModelFitError`: If first-differencing fails

**Example:**

```python
# First-difference estimation
result_fd = analyzer.first_difference(
    'points ~ minutes + team_pace',
    cluster_entity=True
)

print(f"Coefficients: {result_fd.coefficients}")
print(f"Clustered SE: {result_fd.std_errors}")

# Interpretation: Δpoints = β₁*Δminutes + β₂*Δteam_pace + Δε
# Shows how CHANGES in X relate to CHANGES in Y
```

**NBA Analytics Use Case:**

```python
# How do point changes relate to minute changes?
result = analyzer.first_difference('points ~ minutes + usage_rate')

# Interpretation:
# "When a player's minutes increase by 1 (from one season to next),
# their points increase by {coef} on average"

# Advantages over FE:
# - Sometimes more robust to specification
# - Focuses on period-to-period changes
# - Can be easier to interpret ("change in X → change in Y")
```

**References:**
- Related methods: `fixed_effects()`

---

#### difference_gmm() / arellano_bond()

Estimate Arellano-Bond Difference GMM for dynamic panel data with lagged dependent variables.

**When to use:** Dynamic models with lagged DV, endogenous regressors, fixed T and large N. Handles endogeneity via instrumental variables.

```python
difference_gmm(
    formula: str,
    gmm_type: str = "two_step",
    max_lags: int = 3,
    collapse: bool = False
) -> DifferenceGMMResult
```

**Parameters:**

- **formula** (`str`): Model formula with lag notation (e.g., 'points ~ lag(points, 1) + minutes')
- **gmm_type** (`str`): 'one_step' or 'two_step' GMM (default: 'two_step')
- **max_lags** (`int`): Maximum lags for instruments (default: 3)
- **collapse** (`bool`): Collapse instrument matrix to avoid overfitting (default: False)

**Returns:**

- **DifferenceGMMResult**: Contains:
  - `coefficients`, `std_errors`, `t_stats`, `p_values`
  - `ar1_pvalue`, `ar2_pvalue`: Arellano-Bond autocorrelation tests
  - `hansen_pvalue`: Hansen J-test for overidentifying restrictions
  - `n_instruments`: Number of instruments used
  - `summary`: Full estimation summary

**Raises:**

- `ModelFitError`: If GMM estimation fails
- `InvalidParameterError`: If formula or parameters invalid

**Example:**

```python
# Dynamic panel model: points depend on lagged points
result_gmm = analyzer.difference_gmm(
    formula='points ~ lag(points, 1) + minutes + age',
    gmm_type='two_step',
    max_lags=2
)

print(f"Lagged points coefficient: {result_gmm.coefficients['lag(points, 1)']:.3f}")
print(f"AR(1) test p-value: {result_gmm.ar1_pvalue:.3f}")  # Should be <0.05
print(f"AR(2) test p-value: {result_gmm.ar2_pvalue:.3f}")  # Should be >0.05
print(f"Hansen J p-value: {result_gmm.hansen_pvalue:.3f}")  # Should be >0.05

# Diagnostic checks:
# - AR(1) test should reject (expect serial correlation in differences)
# - AR(2) test should NOT reject (no second-order autocorrelation)
# - Hansen J test should NOT reject (instruments valid)
```

**NBA Analytics Use Case:**

```python
# Analyze scoring persistence (do high scorers stay high?)
result = analyzer.difference_gmm(
    formula='points ~ lag(points, 1) + lag(points, 2) + minutes + age + injuries',
    gmm_type='two_step',
    max_lags=3,
    collapse=True  # Avoid instrument proliferation
)

# Interpret lagged coefficient:
lag_coef = result.coefficients['lag(points, 1)']
print(f"Persistence: {lag_coef:.3f}")

if lag_coef > 0.8:
    print("High persistence - scoring is very stable")
elif lag_coef > 0.5:
    print("Moderate persistence")
else:
    print("Low persistence - scoring fluctuates significantly")

# Check instrument validity
if result.hansen_pvalue < 0.05:
    print("WARNING: Instruments may be invalid (try collapse=True)")
```

**Technical Notes:**
- First-differences to remove fixed effects
- Uses lagged levels as instruments for differenced variables
- Requires T ≥ 3 periods
- Can suffer from weak instruments if DV is highly persistent

**References:**
- Arellano, M., & Bond, S. (1991). "Some tests of specification for panel data"
- Related methods: `system_gmm()`, `first_difference()`

---

#### system_gmm() / blundell_bond()

Estimate Blundell-Bond System GMM combining differenced and levels equations.

**When to use:** More efficient than Difference GMM for persistent dependent variables. Combines moment conditions from both differences and levels.

```python
system_gmm(
    formula: str,
    gmm_type: str = "two_step",
    max_lags: int = 3,
    collapse: bool = False
) -> SystemGMMResult
```

**Parameters:**

- **formula** (`str`): Model formula with lags
- **gmm_type** (`str`): 'one_step' or 'two_step' (default: 'two_step')
- **max_lags** (`int`): Maximum instrument lags (default: 3)
- **collapse** (`bool`): Collapse instruments (default: False)

**Returns:**

- **SystemGMMResult**: Contains coefficients, diagnostics (AR tests, Hansen J, Sargan), and instrument count

**Raises:**

- `ModelFitError`: If System GMM estimation fails

**Example:**

```python
# System GMM for highly persistent scoring
result_sys = analyzer.system_gmm(
    formula='points ~ lag(points, 1) + minutes + usage_rate',
    gmm_type='two_step',
    max_lags=2,
    collapse=True
)

print(f"Persistence coefficient: {result_sys.coefficients['lag(points, 1)']:.3f}")
print(f"Hansen J p-value: {result_sys.hansen_pvalue:.3f}")

# System GMM is more efficient than Difference GMM
# when lagged DV coefficient is high (>0.8)
```

**NBA Analytics Use Case:**

```python
# Model team win persistence (do winners keep winning?)
result = analyzer.system_gmm(
    formula='win_pct ~ lag(win_pct, 1) + payroll + star_players + injuries',
    gmm_type='two_step',
    max_lags=2,
    collapse=True
)

# System GMM advantages:
# - Better for persistent variables (win_pct is very persistent)
# - More instruments = more efficient estimates
# - Uses both levels and differences equations
```

**References:**
- Blundell, R., & Bond, S. (1998). "Initial conditions and moment restrictions in dynamic panel data models"
- Related methods: `difference_gmm()`

---

#### hausman_test()

Test for correlation between random effects and regressors (choose between FE and RE).

**When to use:** After estimating both FE and RE models, to determine which is appropriate.

```python
hausman_test(
    formula: str,
    fe_result: Optional[PanelModelResult] = None,
    re_result: Optional[PanelModelResult] = None
) -> Dict[str, Any]
```

**Parameters:**

- **formula** (`str`): Model formula
- **fe_result** (`PanelModelResult`, optional): Pre-computed FE result
- **re_result** (`PanelModelResult`, optional): Pre-computed RE result

**Returns:**

- **Dict**: Contains:
  - `statistic`: Hausman test statistic (chi-squared)
  - `p_value`: P-value for test
  - `df`: Degrees of freedom
  - `reject_re`: Boolean indicating if RE should be rejected
  - `recommendation`: String recommendation ('use_fe' or 'use_re')

**Raises:**

- `ModelFitError`: If test computation fails

**Example:**

```python
# Hausman test to choose between FE and RE
hausman = analyzer.hausman_test('points ~ minutes + age + experience')

print(f"Hausman statistic: {hausman['statistic']:.2f}")
print(f"P-value: {hausman['p_value']:.4f}")
print(f"Recommendation: {hausman['recommendation']}")

if hausman['reject_re']:
    print("Use Fixed Effects (entity effects correlate with regressors)")
    result = analyzer.fixed_effects('points ~ minutes + age + experience')
else:
    print("Random Effects is appropriate")
    result = analyzer.random_effects('points ~ minutes + age + experience')
```

**NBA Analytics Use Case:**

```python
# Test if player talent correlates with minutes played
hausman = analyzer.hausman_test('points ~ minutes + usage_rate + team_pace')

# Interpretation:
# H0: RE is consistent and efficient (effects uncorrelated with X)
# H1: FE is needed (effects correlate with X)

# Typically reject H0 (use FE) because:
# - Better players get more minutes (selection)
# - Player talent correlates with regressors
# - FE controls for this correlation
```

**References:**
- Hausman, J. A. (1978). "Specification tests in econometrics"
- Related methods: `fixed_effects()`, `random_effects()`

---

#### f_test_effects()

F-test for presence of entity fixed effects (pooled OLS vs FE).

**When to use:** Test if panel structure matters - do entity fixed effects significantly improve model fit?

```python
f_test_effects(formula: str) -> Dict[str, Any]
```

**Parameters:**

- **formula** (`str`): Model formula

**Returns:**

- **Dict**: Contains:
  - `f_statistic`: F-test statistic
  - `p_value`: P-value for test
  - `df1`, `df2`: Degrees of freedom
  - `reject_pooled`: Boolean indicating if pooled OLS should be rejected
  - `recommendation`: String recommendation

**Raises:**

- `ModelFitError`: If test fails

**Example:**

```python
# Test if player fixed effects are needed
f_test = analyzer.f_test_effects('points ~ minutes + age')

print(f"F-statistic: {f_test['f_statistic']:.2f}")
print(f"P-value: {f_test['p_value']:.4f}")

if f_test['reject_pooled']:
    print("Entity effects present - use Fixed Effects or Random Effects")
else:
    print("Pooled OLS is adequate")
```

**NBA Analytics Use Case:**

```python
# Do players have significant individual effects beyond observables?
f_test = analyzer.f_test_effects('points ~ minutes + usage_rate + age + experience')

# Interpretation:
# H0: No entity effects (pooled OLS adequate)
# H1: Entity effects present (need FE/RE)

# Almost always reject H0 in NBA data because players differ
# in talent beyond measured variables
```

**References:**
- Related methods: `pooled_ols()`, `fixed_effects()`, `hausman_test()`

---

#### clustered_standard_errors()

Estimate model with clustered standard errors to account for within-entity correlation.

**When to use:** When observations within entities are correlated (almost always in panel data). Produces robust inference.

```python
clustered_standard_errors(
    formula: str,
    cluster_entity: bool = True
) -> PanelModelResult
```

**Parameters:**

- **formula** (`str`): Model formula
- **cluster_entity** (`bool`): Cluster by entity (default: True)

**Returns:**

- **PanelModelResult**: Results with cluster-robust standard errors

**Raises:**

- `ModelFitError`: If estimation fails

**Example:**

```python
# Estimate with clustered SE
result_clustered = analyzer.clustered_standard_errors(
    'points ~ minutes + age + team_pace',
    cluster_entity=True
)

# Compare with non-clustered
result_naive = analyzer.pooled_ols('points ~ minutes + age + team_pace')

print("Naive SE:", result_naive.std_errors['minutes'])
print("Clustered SE:", result_clustered.std_errors['minutes'])
# Clustered SE typically larger → more conservative inference
```

**NBA Analytics Use Case:**

```python
# Analyze effect of minutes on scoring with proper inference
result = analyzer.clustered_standard_errors(
    'points ~ minutes + usage_rate + C(position)',
    cluster_entity=True
)

# Why cluster by player?
# - Player observations across seasons are correlated
# - Standard errors assume independence (wrong!)
# - Clustering accounts for within-player correlation
# - Prevents over-rejection of null hypotheses
```

**References:**
- Cameron, A. C., & Miller, D. L. (2015). "A practitioner's guide to cluster-robust inference"
- Related methods: `pooled_ols()`, `fixed_effects()`

---

### Causal Inference Module Methods

The `CausalInferenceAnalyzer` class provides methods for estimating causal effects and counterfactual outcomes.

```python
from mcp_server.causal_inference import CausalInferenceAnalyzer
import pandas as pd

# Initialize analyzer
data = pd.DataFrame({
    'player_id': [...],
    'treatment': [0, 1, 1, 0, ...],  # E.g., coaching change, trade, etc.
    'outcome': [...],  # E.g., points, win_pct, etc.
    'covariate1': [...],
    'covariate2': [...]
})

analyzer = CausalInferenceAnalyzer(
    data=data,
    treatment_col='treatment',
    outcome_col='outcome',
    covariates=['covariate1', 'covariate2']
)
```

#### instrumental_variables() / iv()

Estimate causal effects using instrumental variables (2SLS/IV estimation).

**When to use:** When treatment is endogenous (correlated with unobservables) and you have valid instruments - variables correlated with treatment but affecting outcome only through treatment.

```python
instrumental_variables(
    instruments: Union[str, List[str]],
    formula: Optional[str] = None,
    robust: bool = True,
    entity_effects: bool = False
) -> IVResult
```

**Parameters:**

- **instruments** (`str` or `List[str]`): Instrument variable(s) - must be correlated with treatment, uncorrelated with error
- **formula** (`str`, optional): Regression formula (if None, uses outcome ~ treatment + covariates)
- **robust** (`bool`): Use robust standard errors (default: True)
- **entity_effects** (`bool`): Include entity fixed effects (default: False)

**Returns:**

- **IVResult**: Contains coefficients, std_errors, first_stage_f (instrument strength), iv_diagnostics (overid tests), summary

**Raises:**

- `InvalidParameterError`: If instruments invalid
- `ModelFitError`: If IV estimation fails (weak instruments, identification issues)

**Example:**

```python
# Example: Effect of draft position on career earnings
# Instrument: lottery outcome (random, correlated with draft pick)
result = analyzer.instrumental_variables(
    instruments=['lottery_outcome'],
    robust=True
)

print(f"Causal effect: {result.coefficients['treatment']:.3f}")
print(f"First-stage F-stat: {result.first_stage_f:.2f}")  # Should be >10

# Check instrument strength
if result.first_stage_f < 10:
    print("WARNING: Weak instruments - estimates may be biased")
```

**NBA Analytics Use Case:**

```python
# Does being an All-Star causally affect endorsement income?
# Problem: All-Stars are better players (selection bias)
# Instrument: Close All-Star voting outcomes (quasi-random)

data = pd.DataFrame({
    'player': player_ids,
    'all_star': all_star_selection,  # Treatment (endogenous)
    'endorsements': endorsement_income,  # Outcome
    'vote_margin': vote_margin_from_cutoff,  # Instrument (quasi-random near cutoff)
    'ppg': points_per_game,
    'team_wins': team_wins
})

analyzer = CausalInferenceAnalyzer(
    data=data,
    treatment_col='all_star',
    outcome_col='endorsements',
    covariates=['ppg', 'team_wins']
)

result = analyzer.instrumental_variables(
    instruments=['vote_margin'],
    robust=True
)

# Interpret:
# - First-stage: Does vote_margin predict all_star? (F>10?)
# - Second-stage: Causal effect of all_star on endorsements
# - Valid if vote_margin only affects endorsements through all_star selection
```

**References:**
- Angrist, J. D., & Pischke, J. S. (2009). Mostly Harmless Econometrics
- Related methods: `regression_discontinuity()`

---

#### regression_discontinuity() / rdd()

Estimate causal effects using Regression Discontinuity Design (sharp or fuzzy RDD).

**When to use:** When treatment assignment has a cutoff rule based on a running variable. Identifies local average treatment effect near cutoff.

```python
regression_discontinuity(
    running_var: str,
    cutoff: float,
    bandwidth: Optional[float] = None,
    kernel: str = "triangular",
    polynomial_order: int = 1,
    fuzzy: bool = False,
    optimal_bandwidth_method: str = "ik"
) -> RDDResult
```

**Parameters:**

- **running_var** (`str`): Assignment variable (e.g., age, performance metric)
- **cutoff** (`float`): Treatment cutoff value
- **bandwidth** (`float`, optional): Bandwidth around cutoff (if None, uses optimal bandwidth)
- **kernel** (`str`): Kernel function: 'triangular', 'uniform', 'epanechnikov' (default: 'triangular')
- **polynomial_order** (`int`): Polynomial order for regression (default: 1 = linear)
- **fuzzy** (`bool`): Fuzzy RDD (treatment probability jumps, not 0→1) (default: False)
- **optimal_bandwidth_method** (`str`): Method for optimal bandwidth: 'ik' (Imbens-Kalyanaraman), 'ccft' (default: 'ik')

**Returns:**

- **RDDResult**: Contains treatment_effect, std_error, bandwidth_used, continuity_test (McCrary density test), polynomial_order, n_treated, n_control

**Raises:**

- `MissingParameterError`: If running_var or cutoff not specified
- `ModelFitError`: If RDD estimation fails

**Example:**

```python
# Example: Effect of making playoffs on next season improvement
result = analyzer.regression_discontinuity(
    running_var='win_pct',
    cutoff=0.500,  # Playoff cutoff
    bandwidth=None,  # Use optimal
    polynomial_order=1,
    fuzzy=False
)

print(f"Local treatment effect: {result.treatment_effect:.3f} ± {result.std_error:.3f}")
print(f"Bandwidth used: {result.bandwidth_used:.3f}")
print(f"Continuity test p-value: {result.continuity_test['p_value']:.3f}")

# McCrary test: check if units manipulate running variable
if result.continuity_test['p_value'] < 0.05:
    print("WARNING: Discontinuity in density - RDD validity threatened")
```

**NBA Analytics Use Case:**

```python
# Effect of winning NBA Draft Lottery on future team performance
# Running var: lottery odds
# Cutoff: Winning vs not winning #1 pick

data = pd.DataFrame({
    'team': team_ids,
    'lottery_odds': lottery_odds,  # Running variable
    'won_lottery': won_first_pick,  # Treatment (sharp: 0/1)
    'win_improvement': win_pct_change_3_years,  # Outcome
    'market_size': market_size,
    'prior_wins': previous_season_wins
})

analyzer = CausalInferenceAnalyzer(
    data=data,
    treatment_col='won_lottery',
    outcome_col='win_improvement',
    covariates=['market_size', 'prior_wins']
)

result = analyzer.regression_discontinuity(
    running_var='lottery_odds',
    cutoff=lottery_winner_threshold,
    bandwidth=None,  # Optimal bandwidth selection
    polynomial_order=1,
    fuzzy=False
)

# Interpret:
# - Treatment effect: Impact of winning lottery on improvement
# - Valid near cutoff (teams with similar odds)
# - Assumes no manipulation of lottery (true for NBA)
```

**References:**
- Lee, D. S., & Lemieux, T. (2010). "Regression Discontinuity Designs in Economics"
- Related methods: `instrumental_variables()` (fuzzy RDD equivalent)

---

#### propensity_score_matching() / psm()

Estimate treatment effects by matching treated and control units with similar propensity scores.

**When to use:** When treatment is non-random but selection on observables holds (all confounders measured).

```python
propensity_score_matching(
    method: str = "nearest",
    n_neighbors: int = 1,
    caliper: Optional[float] = None,
    replace: bool = False,
    estimate_std_error: bool = True
) -> PSMResult
```

**Parameters:**

- **method** (`str`): Matching method: 'nearest', 'kernel', 'radius' (default: 'nearest')
- **n_neighbors** (`int`): Number of nearest neighbors for matching (default: 1)
- **caliper** (`float`, optional): Maximum propensity score distance for matches
- **replace** (`bool`): Match with replacement (default: False)
- **estimate_std_error** (`bool`): Bootstrap standard errors (default: True)

**Returns:**

- **PSMResult**: Contains att (average treatment effect on treated), ate (average treatment effect), propensity_scores, matched_pairs, balance_stats, common_support_fraction

**Raises:**

- `InsufficientDataError`: If too few treated/control units
- `ModelFitError`: If propensity score estimation fails

**Example:**

```python
# Estimate effect of coaching change on team performance
result = analyzer.propensity_score_matching(
    method='nearest',
    n_neighbors=1,
    caliper=0.1,  # Match only within 0.1 propensity score distance
    replace=False
)

print(f"ATT: {result.att:.3f} ± {result.att_se:.3f}")
print(f"ATE: {result.ate:.3f} ± {result.ate_se:.3f}")
print(f"Common support: {result.common_support_fraction:.1%}")

# Check covariate balance
print("\nBalance after matching:")
for var, balance in result.balance_stats.items():
    print(f"  {var}: std_diff = {balance['std_diff']:.3f}")
```

**NBA Analytics Use Case:**

```python
# Effect of home-court advantage in playoffs
data = pd.DataFrame({
    'game': game_ids,
    'home_team': [1, 0, 1, 0, ...],  # Treatment
    'won': [1, 0, 1, 1, ...],  # Outcome
    'team_rating': team_ratings,
    'opponent_rating': opponent_ratings,
    'rest_days': rest_days,
    'playoff_round': playoff_round
})

analyzer = CausalInferenceAnalyzer(
    data=data,
    treatment_col='home_team',
    outcome_col='won',
    covariates=['team_rating', 'opponent_rating', 'rest_days', 'playoff_round']
)

result = analyzer.propensity_score_matching(
    method='nearest',
    n_neighbors=2,
    caliper=0.05,
    replace=False
)

# Interpret ATT:
# "Playing at home increases win probability by {ATT} percentage points,
# after matching on team quality, opponent, and rest"
```

**References:**
- Rosenbaum, P. R., & Rubin, D. B. (1983). "The central role of the propensity score"
- Related methods: `kernel_matching()`, `radius_matching()`, `doubly_robust_estimation()`

---

#### kernel_matching()

Estimate treatment effects using kernel-weighted propensity score matching.

**When to use:** Alternative to nearest-neighbor matching that uses weighted averages of all controls. More efficient but requires more assumptions.

```python
kernel_matching(
    kernel: str = "gaussian",
    bandwidth: Optional[float] = None,
    estimate_std_error: bool = True
) -> PSMResult
```

**Parameters:**

- **kernel** (`str`): Kernel function: 'gaussian', 'epanechnikov', 'uniform' (default: 'gaussian')
- **bandwidth** (`float`, optional): Kernel bandwidth (if None, uses rule-of-thumb)
- **estimate_std_error** (`bool`): Bootstrap SE (default: True)

**Returns:**

- **PSMResult**: Treatment effect estimates with kernel weights

**Example:**

```python
result = analyzer.kernel_matching(
    kernel='gaussian',
    bandwidth=0.06
)
print(f"ATT (kernel): {result.att:.3f}")
```

**References:**
- Heckman, J. J., Ichimura, H., & Todd, P. (1998). "Matching as an econometric evaluation estimator"
- Related methods: `propensity_score_matching()`, `radius_matching()`

---

#### radius_matching() / caliper_matching()

Estimate treatment effects by matching within a propensity score radius.

**When to use:** When you want to match only sufficiently similar units (avoids bad matches).

```python
radius_matching(
    radius: float = 0.05,
    estimate_std_error: bool = True
) -> PSMResult
```

**Parameters:**

- **radius** (`float`): Maximum propensity score distance for matches (default: 0.05)
- **estimate_std_error** (`bool`): Bootstrap SE (default: True)

**Returns:**

- **PSMResult**: Treatment effects using radius matching

**Example:**

```python
result = analyzer.radius_matching(radius=0.05)
print(f"ATT (radius={0.05}): {result.att:.3f}")
print(f"Matched treated units: {result.n_matched_treated}/{result.n_treated}")
```

**References:**
- Dehejia, R. H., & Wahba, S. (1999). "Causal effects in nonexperimental studies"
- Related methods: `propensity_score_matching()`

---

#### doubly_robust_estimation() / dr()

Doubly robust estimator combining outcome regression and propensity score weighting.

**When to use:** More robust than PSM or regression alone - consistent if either outcome model OR propensity model is correct.

```python
doubly_robust_estimation(
    estimate_std_error: bool = True
) -> PSMResult
```

**Parameters:**

- **estimate_std_error** (`bool`): Bootstrap SE (default: True)

**Returns:**

- **PSMResult**: Doubly robust treatment effect estimates

**Example:**

```python
result = analyzer.doubly_robust_estimation()
print(f"DR-ATT: {result.att:.3f}")
print(f"DR-ATE: {result.ate:.3f}")

# Doubly robust is more reliable:
# - Protects against outcome model misspecification
# - Protects against propensity model misspecification
```

**NBA Analytics Use Case:**

```python
# Effect of star player acquisition on team performance
# DR estimator more robust to model misspecification

result = analyzer.doubly_robust_estimation(estimate_std_error=True)

print(f"Causal effect: {result.att:.3f} ± {result.att_se:.3f}")
print(f"95% CI: [{result.att - 1.96*result.att_se:.3f}, {result.att + 1.96*result.att_se:.3f}]")
```

**References:**
- Bang, H., & Robins, J. M. (2005). "Doubly robust estimation in missing data and causal inference models"
- Related methods: `propensity_score_matching()`

---

#### synthetic_control()

Estimate treatment effects using synthetic control method for comparative case studies.

**When to use:** One or few treated units, many control units, pre/post treatment data. Creates synthetic counterfactual.

```python
synthetic_control(
    treated_unit: Any,
    outcome_periods: List[int],
    treatment_period: int,
    donor_pool: Optional[List[Any]] = None,
    covariates_for_matching: Optional[List[str]] = None,
    n_placebo: int = 0
) -> SyntheticControlResult
```

**Parameters:**

- **treated_unit** (`Any`): ID of treated unit (e.g., team ID)
- **outcome_periods** (`List[int]`): Time periods for analysis
- **treatment_period** (`int`): When treatment begins
- **donor_pool** (`List`, optional): Control units for synthetic control (if None, uses all)
- **covariates_for_matching** (`List[str]`, optional): Covariates for weighting
- **n_placebo** (`int`): Number of placebo tests (default: 0)

**Returns:**

- **SyntheticControlResult**: Contains treatment_effect, weights (donor weights), pre_treatment_fit (RMSPE), post_treatment_fit, placebo_distribution, p_value

**Raises:**

- `MissingParameterError`: If treated_unit or periods not specified
- `ModelFitError`: If synthetic control construction fails

**Example:**

```python
# Effect of new arena on team revenue
result = analyzer.synthetic_control(
    treated_unit='LAL',  # Lakers
    outcome_periods=list(range(2010, 2025)),
    treatment_period=2020,  # New arena opened
    donor_pool=['BOS', 'GSW', 'MIA', ...],  # Similar market teams
    covariates_for_matching=['market_size', 'team_quality', 'prior_revenue'],
    n_placebo=100
)

print(f"Treatment effect: {result.treatment_effect:.2f}M")
print(f"Pre-treatment RMSPE: {result.pre_treatment_fit:.3f}")
print(f"P-value (placebo test): {result.p_value:.3f}")

# Visualize
import matplotlib.pyplot as plt
plt.plot(result.periods, result.treated_outcomes, label='Treated (actual)')
plt.plot(result.periods, result.synthetic_outcomes, label='Synthetic control')
plt.axvline(result.treatment_period, color='r', linestyle='--', label='Treatment')
plt.legend()
plt.show()
```

**NBA Analytics Use Case:**

```python
# Did moving to a new city affect team performance?
# Example: Seattle SuperSonics → Oklahoma City Thunder

result = analyzer.synthetic_control(
    treated_unit='OKC',
    outcome_periods=list(range(2003, 2015)),
    treatment_period=2008,  # Relocation year
    donor_pool=None,  # Use all other teams
    covariates_for_matching=['previous_win_pct', 'payroll', 'attendance', 'market_size'],
    n_placebo=50
)

# Interpretation:
# - Synthetic OKC = weighted average of similar teams
# - Treatment effect = Actual - Synthetic post-2008
# - P-value from placebo tests (apply to each donor, see if effects as large)
```

**References:**
- Abadie, A., Diamond, A., & Hainmueller, J. (2010). "Synthetic Control Methods for Comparative Case Studies"
- Related methods: `difference_in_differences()` (not shown here)

---

#### sensitivity_analysis()

Assess robustness of causal estimates to unobserved confounding.

**When to use:** After obtaining causal estimate, test how sensitive it is to hidden bias.

```python
sensitivity_analysis(
    method: str,
    effect_estimate: float,
    se_estimate: Optional[float] = None,
    gamma_range: Tuple[float, float] = (1.0, 3.0),
    n_gamma: int = 20
) -> SensitivityResult
```

**Parameters:**

- **method** (`str`): Sensitivity method: 'rosenbaum_bounds', 'e_value', 'confounding_function'
- **effect_estimate** (`float`): Point estimate of treatment effect
- **se_estimate** (`float`, optional): Standard error of estimate
- **gamma_range** (`Tuple[float, float]`): Range of sensitivity parameter Γ (default: (1.0, 3.0))
- **n_gamma** (`int`): Number of Γ values to test (default: 20)

**Returns:**

- **SensitivityResult**: Contains gamma_values, p_values (significance at each Γ), e_value (minimum confounding strength to nullify effect), robustness_summary

**Raises:**

- `InvalidParameterError`: If method unknown or parameters invalid

**Example:**

```python
# After PSM estimation
psm_result = analyzer.propensity_score_matching()

# Test sensitivity to unobserved confounding
sensitivity = analyzer.sensitivity_analysis(
    method='rosenbaum_bounds',
    effect_estimate=psm_result.att,
    se_estimate=psm_result.att_se,
    gamma_range=(1.0, 3.0),
    n_gamma=20
)

print(f"E-value: {sensitivity.e_value:.2f}")
print(f"Interpretation: Unmeasured confounder must have RR ≥ {sensitivity.e_value:.2f} to nullify effect")

# Find critical Γ where effect becomes non-significant
for gamma, pval in zip(sensitivity.gamma_values, sensitivity.p_values):
    if pval > 0.05:
        print(f"Effect becomes non-significant at Γ = {gamma:.2f}")
        break
```

**NBA Analytics Use Case:**

```python
# Sensitivity analysis for home-court advantage estimate
psm_result = analyzer.propensity_score_matching()

sensitivity = analyzer.sensitivity_analysis(
    method='e_value',
    effect_estimate=psm_result.att
)

print(f"E-value: {sensitivity.e_value:.2f}")
print(f"To explain away home-court effect, unmeasured confounder would need to:")
print(f"- Increase treatment odds by {sensitivity.e_value:.2f}x")
print(f"- Increase outcome odds by {sensitivity.e_value:.2f}x")
print(f"- Be perfectly measured (no residual confounding)")

# If E-value is high (>3), effect is robust to hidden bias
```

**References:**
- Rosenbaum, P. R. (2002). "Observational Studies"
- VanderWeele, T. J., & Ding, P. (2017). "Sensitivity analysis in observational research"
- Related methods: All causal inference methods (sensitivity check for each)

---

## Version Information

**Current Version:** 1.0.0
**Last Updated:** November 2025
**Python Version:** 3.11+
**Dependencies:** See `requirements.txt`

For more information, see:
- [Quick Start Guide](QUICK_START.md)
- [Best Practices Guide](BEST_PRACTICES.md) (coming soon)
- [Example Notebooks](../examples/)
