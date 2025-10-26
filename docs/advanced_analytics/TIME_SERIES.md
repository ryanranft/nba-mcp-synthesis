# Time Series Analysis for NBA Performance Metrics

**Module:** `mcp_server.time_series`
**Author:** Agent 8 Module 1
**Date:** October 2025
**Version:** 1.0.0

## Overview

The Time Series Analysis module provides comprehensive capabilities for analyzing temporal patterns in NBA performance data. It enables forecasting player/team performance, detecting trends and seasonality, and understanding temporal dynamics in basketball statistics.

### Key Features

- **Stationarity Testing**: ADF and KPSS tests to determine if data needs transformation
- **Decomposition**: Break down time series into trend, seasonal, and residual components
- **ARIMA Modeling**: Fit and forecast using ARIMA/SARIMA models
- **Autocorrelation Analysis**: ACF, PACF, and Ljung-Box tests
- **Trend Detection**: Identify increasing, decreasing, or stable trends
- **MLflow Integration**: Automatic experiment tracking for reproducibility

### Use Cases

- Forecast player scoring for upcoming games
- Detect performance trends over a season
- Identify home/away seasonality effects
- Predict team win rates
- Analyze injury recovery patterns
- Evaluate rookie development trajectories

---

## Quick Start

### Basic Usage

```python
import pandas as pd
from mcp_server.time_series import TimeSeriesAnalyzer

# Load player points per game data
data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82),
    'points': [25, 28, 22, 30, ...]  # 82 games
})

# Create analyzer
analyzer = TimeSeriesAnalyzer(
    data,
    target_column='points',
    time_column='date',
    freq='D'  # Daily frequency
)

# Check stationarity
result = analyzer.test_stationarity()
print(result.is_stationary)  # True or False

# Fit ARIMA model
model = analyzer.auto_arima(max_p=2, max_q=2)
print(f"Best model: ARIMA{model.order}, AIC={model.aic:.2f}")

# Forecast next 10 games
forecast = analyzer.forecast(model, steps=10)
print(forecast.forecast)
print(forecast.confidence_interval)
```

---

## API Reference

### TimeSeriesAnalyzer

Main class for time series analysis.

#### `__init__(data, target_column, time_column=None, freq=None, mlflow_experiment=None)`

Initialize the analyzer.

**Parameters:**
- `data` (pd.DataFrame): DataFrame with time series data
- `target_column` (str): Column containing values to analyze
- `time_column` (str, optional): Column with timestamps (uses index if None)
- `freq` (str, optional): Frequency ('D', 'W', 'M', etc.). Auto-inferred if None
- `mlflow_experiment` (str, optional): MLflow experiment name for tracking

**Raises:**
- `ValueError`: If target_column not in data or invalid time index

**Example:**
```python
analyzer = TimeSeriesAnalyzer(
    df,
    target_column='ppg',
    time_column='game_date',
    freq='D',
    mlflow_experiment='player_forecasts'
)
```

---

### Stationarity Testing

#### `adf_test(maxlag=None) -> StationarityTestResult`

Augmented Dickey-Fuller test for stationarity.

**Null Hypothesis (H0):** Series has unit root (non-stationary)
**Alternative (H1):** Series is stationary

**Parameters:**
- `maxlag` (int, optional): Maximum lags for test

**Returns:**
- `StationarityTestResult` with:
  - `test_statistic` (float): ADF test statistic
  - `p_value` (float): P-value
  - `critical_values` (dict): Critical values at 1%, 5%, 10%
  - `is_stationary` (bool): True if p < 0.05
  - `lags_used` (int): Lags used in test
  - `observations` (int): Number of observations

**Example:**
```python
result = analyzer.adf_test()
if result.is_stationary:
    print("Series is stationary")
else:
    print(f"Series is non-stationary (p={result.p_value:.4f})")
```

#### `kpss_test(regression='c', nlags='auto') -> StationarityTestResult`

KPSS test for stationarity.

**Null Hypothesis (H0):** Series is stationary
**Alternative (H1):** Series has unit root (non-stationary)

**Note:** Opposite interpretation from ADF test!

**Parameters:**
- `regression` (str): 'c' for level stationary, 'ct' for trend stationary
- `nlags` (str|int): Lags to use or 'auto'

**Example:**
```python
result = analyzer.kpss_test(regression='ct')
print(result)  # Pretty-printed result
```

---

### Decomposition

#### `decompose(model='additive', period=None, method='seasonal_decompose') -> DecompositionResult`

Decompose time series into components.

**Parameters:**
- `model` (str): 'additive' or 'multiplicative'
- `period` (int, optional): Seasonal period (auto-inferred from freq if None)
- `method` (str): 'seasonal_decompose' or 'stl' (STL is more robust)

**Returns:**
- `DecompositionResult` with:
  - `observed` (pd.Series): Original series
  - `trend` (pd.Series): Trend component
  - `seasonal` (pd.Series): Seasonal component
  - `residual` (pd.Series): Residual component
  - `model` (str): Model type
  - `period` (int): Period used

**Example:**
```python
# Weekly seasonality in daily data
decomp = analyzer.decompose(period=7, method='stl')

# Plot components
fig = decomp.plot_components()
fig.savefig('decomposition.png')

# Analyze trend
trend_strength = decomp.trend.std() / decomp.observed.std()
print(f"Trend strength: {trend_strength:.2%}")
```

#### `detect_trend() -> Dict[str, Any]`

Detect trend direction using linear regression.

**Returns:**
Dictionary with:
- `direction` (str): 'increasing', 'decreasing', or 'stable'
- `slope` (float): Regression slope
- `r_squared` (float): R² value (trend strength)
- `p_value` (float): Significance of trend

**Example:**
```python
trend = analyzer.detect_trend()
if trend['direction'] == 'increasing' and trend['p_value'] < 0.05:
    print(f"Significant upward trend: {trend['slope']:.2f} pts/game")
```

---

### Autocorrelation Analysis

#### `acf(nlags=40, alpha=0.05) -> ACFResult`

Calculate autocorrelation function.

**Parameters:**
- `nlags` (int): Number of lags
- `alpha` (float): Significance level for confidence intervals

**Returns:**
- `ACFResult` with ACF values and confidence intervals

**Example:**
```python
acf_result = analyzer.acf(nlags=20)

# Plot ACF
import matplotlib.pyplot as plt
plt.stem(acf_result.lags, acf_result.acf_values)
plt.axhline(y=0, color='k', linestyle='--')
plt.title('Autocorrelation Function')
plt.show()
```

#### `pacf(nlags=40, alpha=0.05) -> ACFResult`

Calculate partial autocorrelation function.

Similar to `acf()` but returns partial autocorrelations.

#### `ljung_box_test(lags=10) -> Dict[str, Any]`

Test for autocorrelation in residuals.

**Null Hypothesis:** No autocorrelation
**Alternative:** Autocorrelation present

**Returns:**
Dictionary with:
- `lb_stat` (list): Ljung-Box statistics
- `lb_pvalue` (list): P-values for each lag
- `has_autocorrelation` (bool): True if any p < 0.05

**Example:**
```python
# After fitting ARIMA, test residuals
model = analyzer.fit_arima(order=(1, 0, 1))
residuals_analyzer = TimeSeriesAnalyzer(
    pd.DataFrame({'resid': model.model.resid}),
    target_column='resid'
)
lb_test = residuals_analyzer.ljung_box_test(lags=15)
if not lb_test['has_autocorrelation']:
    print("Residuals are white noise - good model fit!")
```

---

### ARIMA Modeling

#### `fit_arima(order, seasonal_order=None, **kwargs) -> ARIMAModelResult`

Fit ARIMA model with specified parameters.

**Parameters:**
- `order` (tuple): (p, d, q) where:
  - `p`: Autoregressive order
  - `d`: Differencing order
  - `q`: Moving average order
- `seasonal_order` (tuple, optional): (P, D, Q, s) for SARIMA
- `**kwargs`: Additional arguments for statsmodels ARIMA

**Returns:**
- `ARIMAModelResult` with fitted model, AIC, BIC, summary

**Example:**
```python
# Fit ARIMA(1,1,1)
model = analyzer.fit_arima(order=(1, 1, 1))
print(f"AIC: {model.aic:.2f}, BIC: {model.bic:.2f}")

# Fit seasonal ARIMA with weekly seasonality
sarima = analyzer.fit_arima(
    order=(1, 0, 1),
    seasonal_order=(1, 0, 1, 7)
)
```

#### `auto_arima(seasonal=False, m=1, max_p=5, max_d=2, max_q=5, ...) -> ARIMAModelResult`

Automatically select best ARIMA model using grid search.

**Parameters:**
- `seasonal` (bool): Fit seasonal ARIMA
- `m` (int): Seasonal period (if seasonal=True)
- `max_p`, `max_d`, `max_q` (int): Maximum orders to try
- `max_P`, `max_D`, `max_Q` (int): Maximum seasonal orders
- `information_criterion` (str): 'aic' or 'bic'

**Returns:**
- `ARIMAModelResult` with best model

**Example:**
```python
# Find best non-seasonal model
best_model = analyzer.auto_arima(
    seasonal=False,
    max_p=3,
    max_d=2,
    max_q=3,
    information_criterion='aic'
)
print(f"Selected: ARIMA{best_model.order}")

# Find best seasonal model
best_sarima = analyzer.auto_arima(
    seasonal=True,
    m=7,  # Weekly seasonality
    max_p=2,
    max_P=1
)
```

#### `forecast(model_result, steps=10, alpha=0.05) -> ForecastResult`

Generate forecasts from fitted model.

**Parameters:**
- `model_result` (ARIMAModelResult): Fitted model
- `steps` (int): Number of steps to forecast
- `alpha` (float): Significance level for confidence intervals

**Returns:**
- `ForecastResult` with:
  - `forecast` (pd.Series): Point forecasts
  - `confidence_interval` (pd.DataFrame): Lower/upper bounds
  - `forecast_index` (pd.Index): Forecast time index
  - `model_summary` (str): Model summary

**Example:**
```python
# Forecast next 10 games
forecast = analyzer.forecast(model, steps=10)

# Plot forecast
import matplotlib.pyplot as plt
plt.plot(analyzer.series, label='Historical')
plt.plot(forecast.forecast, label='Forecast', linestyle='--')
plt.fill_between(
    forecast.forecast_index,
    forecast.confidence_interval['lower'],
    forecast.confidence_interval['upper'],
    alpha=0.3,
    label='95% CI'
)
plt.legend()
plt.show()
```

---

### Utility Methods

#### `difference(periods=1) -> pd.Series`

Apply differencing to make series stationary.

**Example:**
```python
diff_series = analyzer.difference(periods=1)
```

#### `make_stationary(max_diffs=2) -> Tuple[pd.Series, List[str]]`

Automatically make series stationary through differencing.

**Returns:**
- Stationary series and list of transformations applied

**Example:**
```python
stationary, transforms = analyzer.make_stationary()
print(f"Applied: {transforms}")
```

#### `validate_forecast(actual, predicted) -> Dict[str, float]`

Calculate forecast error metrics.

**Returns:**
Dictionary with MAE, MSE, RMSE, MAPE

**Example:**
```python
# Validate forecast
errors = analyzer.validate_forecast(test_data, forecast.forecast)
print(f"MAE: {errors['mae']:.2f}")
print(f"RMSE: {errors['rmse']:.2f}")
print(f"MAPE: {errors['mape']:.1f}%")
```

---

## NBA-Specific Examples

### Example 1: Player Scoring Forecast

```python
import pandas as pd
from mcp_server.time_series import TimeSeriesAnalyzer

# Load Stephen Curry's points per game for 2023-24 season
curry_data = pd.DataFrame({
    'date': pd.date_range('2023-10-24', periods=74),
    'ppg': [25, 28, 32, 27, 29, ...]  # Actual game data
})

# Analyze
analyzer = TimeSeriesAnalyzer(
    curry_data,
    target_column='ppg',
    time_column='date',
    freq='D'
)

# Check for trend
trend = analyzer.detect_trend()
print(f"Season trend: {trend['direction']}, slope={trend['slope']:.2f} ppg/game")

# Fit model
model = analyzer.auto_arima(seasonal=False, max_p=3, max_q=3)

# Forecast next 8 games
forecast = analyzer.forecast(model, steps=8)
print("Forecast for next 8 games:")
print(forecast.forecast)
```

### Example 2: Team Home/Away Seasonality

```python
# Load team win/loss data with home/away indicator
warriors_data = pd.DataFrame({
    'date': pd.date_range('2023-10-01', periods=82),
    'win': [1, 0, 1, 1, 0, ...],  # 1=win, 0=loss
    'home': [1, 0, 1, 0, 1, ...]  # 1=home, 0=away
})

analyzer = TimeSeriesAnalyzer(
    warriors_data,
    target_column='win',
    time_column='date'
)

# Decompose with period=2 (alternating home/away)
decomp = analyzer.decompose(period=2, method='stl')

# Analyze home advantage
home_effect = decomp.seasonal[warriors_data['home'] == 1].mean()
away_effect = decomp.seasonal[warriors_data['home'] == 0].mean()
print(f"Home advantage: {(home_effect - away_effect) * 100:.1f}% win rate boost")
```

### Example 3: Injury Recovery Pattern

```python
# Track player minutes after injury return
recovery_data = pd.DataFrame({
    'game_number': range(1, 21),  # First 20 games back
    'minutes': [12, 15, 18, 22, 25, ...]
})

analyzer = TimeSeriesAnalyzer(
    recovery_data.set_index('game_number'),
    target_column='minutes'
)

# Detect recovery trend
trend = analyzer.detect_trend()
if trend['direction'] == 'increasing':
    games_to_normal = (30 - 12) / trend['slope']  # Estimate games to 30 min
    print(f"Expected return to normal minutes in ~{games_to_normal:.0f} games")
```

### Example 4: Rookie Development Trajectory

```python
# Analyze rookie season progression
rookie_data = pd.DataFrame({
    'month': pd.date_range('2023-10-01', periods=7, freq='MS'),
    'ppg': [8.2, 10.5, 12.1, 15.8, 16.3, 17.2, 18.5],
    'efficiency': [45, 48, 51, 56, 58, 59, 61]
})

for metric in ['ppg', 'efficiency']:
    analyzer = TimeSeriesAnalyzer(
        rookie_data,
        target_column=metric,
        time_column='month'
    )

    trend = analyzer.detect_trend()
    model = analyzer.fit_arima(order=(1, 0, 0))
    forecast = analyzer.forecast(model, steps=3)

    print(f"\n{metric.upper()} Analysis:")
    print(f"  Trend: {trend['direction']} ({trend['slope']:.2f} per month)")
    print(f"  Forecast next 3 months: {forecast.forecast.values}")
```

---

## Integration with Other Modules

### MLflow Tracking

```python
# Enable MLflow experiment tracking
analyzer = TimeSeriesAnalyzer(
    data,
    target_column='points',
    mlflow_experiment='player_forecasting'
)

# Models automatically logged to MLflow
model = analyzer.auto_arima()  # Logs parameters, metrics

# View experiments
import mlflow
mlflow.search_runs(experiment_names=['player_forecasting'])
```

### Data Validation (Agent 4)

```python
from mcp_server.data_validation import validate_dataset

# Validate time series data before analysis
validation_result = validate_dataset(data, 'player_stats')

if validation_result['valid']:
    analyzer = TimeSeriesAnalyzer(data, 'points')
else:
    print(f"Validation errors: {validation_result['errors']}")
```

### Training Pipeline (Agent 5)

```python
# Use time series features in ML pipeline
decomp = analyzer.decompose(period=7)
features = pd.DataFrame({
    'trend': decomp.trend,
    'seasonal': decomp.seasonal,
    'lag1': analyzer.series.shift(1),
    'lag7': analyzer.series.shift(7)
})

# Add to training data
from mcp_server.training_pipeline import train_model
model = train_model(features, target='next_game_points')
```

---

## Best Practices

### 1. Always Check Stationarity

```python
# Run both tests for robustness
adf = analyzer.adf_test()
kpss = analyzer.kpss_test()

if adf.is_stationary and kpss.is_stationary:
    print("✓ Stationary (both tests agree)")
elif not adf.is_stationary and not kpss.is_stationary:
    print("✗ Non-stationary (both tests agree)")
else:
    print("⚠ Tests disagree - investigate further")
```

### 2. Use Train/Test Split for Validation

```python
# Split data
train = analyzer.series[:-10]
test = analyzer.series[-10:]

# Fit on training data
train_analyzer = TimeSeriesAnalyzer(
    pd.DataFrame({'value': train}),
    target_column='value'
)
model = train_analyzer.fit_arima(order=(1, 0, 1))

# Forecast and validate
forecast = train_analyzer.forecast(model, steps=10)
errors = train_analyzer.validate_forecast(test, forecast.forecast)

print(f"Test RMSE: {errors['rmse']:.2f}")
print(f"Test MAPE: {errors['mape']:.1f}%")
```

### 3. Examine Residuals

```python
model = analyzer.fit_arima(order=(1, 1, 1))

# Create analyzer for residuals
resid_analyzer = TimeSeriesAnalyzer(
    pd.DataFrame({'resid': model.model.resid}),
    target_column='resid'
)

# Check if residuals are white noise
lb_test = resid_analyzer.ljung_box_test(lags=20)
if lb_test['has_autocorrelation']:
    print("⚠ Residuals show autocorrelation - model may be mis-specified")
else:
    print("✓ Residuals are white noise - good fit")
```

### 4. Use Appropriate Frequency

```python
# For NBA data:
# - Daily frequency for player/team game data
# - Weekly for aggregated stats
# - Monthly for career trajectories

analyzer = TimeSeriesAnalyzer(
    daily_game_data,
    target_column='points',
    freq='D'  # Daily
)

analyzer_weekly = TimeSeriesAnalyzer(
    weekly_avg_data,
    target_column='avg_points',
    freq='W'  # Weekly
)
```

---

## Troubleshooting

### Issue: "Cannot infer frequency"

**Solution:** Explicitly specify frequency
```python
analyzer = TimeSeriesAnalyzer(data, 'value', freq='D')
```

### Issue: ARIMA convergence failure

**Solutions:**
1. Check for stationarity and difference if needed
2. Try simpler model orders
3. Use auto_arima with conservative max values

```python
# Conservative auto_arima
model = analyzer.auto_arima(
    max_p=2,
    max_d=1,
    max_q=2,
    information_criterion='bic'  # BIC penalizes complexity more
)
```

### Issue: Unrealistic forecasts

**Solutions:**
1. Check forecast horizon isn't too long
2. Validate on test set first
3. Consider adding covariates/external factors

```python
# Limit forecast horizon
forecast = analyzer.forecast(model, steps=5)  # Not 50

# Validate first
errors = analyzer.validate_forecast(test, forecast_on_train)
if errors['mape'] > 20:
    print("⚠ Model may not generalize well")
```

---

## Performance Considerations

- **ARIMA fitting**: <5 seconds for 200 points
- **auto_arima**: 10-60 seconds depending on grid size
- **Decomposition**: <1 second for typical NBA season data
- **Memory**: Handles series up to 10,000 points efficiently

---

## References

- Box, G. E. P., & Jenkins, G. M. (2015). *Time Series Analysis: Forecasting and Control*
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice*
- Statsmodels Documentation: https://www.statsmodels.org/stable/tsa.html

---

**Last Updated:** October 26, 2025
**Module Version:** 1.0.0
**Python Version:** 3.11+
**Dependencies:** statsmodels>=0.14.0, scipy>=1.10.0, pandas>=2.2.0, numpy>=1.26.0
