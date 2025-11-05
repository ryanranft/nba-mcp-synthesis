# Advanced Time Series Methods for NBA Analytics

**Module 4C - Agent 8**
**Author**: Agent 8
**Date**: October 2025

## Overview

The `advanced_time_series.py` module extends basic time series analysis with sophisticated state-space methods designed for complex temporal patterns in NBA data. This module provides tools for:

- **State Space Models**: Kalman filtering and smoothing for real-time tracking
- **Dynamic Factor Models**: Extract latent factors (e.g., team momentum)
- **Markov Switching Models**: Detect regime changes (hot/cold streaks)
- **Structural Time Series**: Decompose into level, trend, seasonal, and irregular components

## Installation

```bash
# Required dependencies
pip install statsmodels>=0.14.0 numpy pandas scipy

# Optional: MLflow integration
pip install mlflow
```

## Quick Start

```python
from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer
import pandas as pd

# Load player performance data
data = pd.read_csv('player_points.csv', index_col='date', parse_dates=True)
analyzer = AdvancedTimeSeriesAnalyzer(data['points'])

# Kalman filter for real-time tracking
result = analyzer.kalman_filter(model='local_level')
current_state = result.filtered_state[:, -1]

# Detect hot/cold streaks
result = analyzer.markov_switching(n_regimes=2)
hot_streaks = result.get_regime_periods(regime=1)
```

## Core Components

### 1. Kalman Filtering and Smoothing

**Use Cases**:
- Real-time player performance tracking
- Missing data imputation
- Signal extraction from noisy observations
- Online updates as new data arrives

**Example: Real-Time Performance Tracking**

```python
# Track player performance with Kalman filter
analyzer = AdvancedTimeSeriesAnalyzer(player_points)

# Local level model (random walk + noise)
result = analyzer.kalman_filter(model='local_level')

# Current estimated performance level
current_level = result.filtered_state[0, -1]
uncertainty = result.filtered_state_cov[0, 0, -1]

print(f"Current level: {current_level:.1f} ± {np.sqrt(uncertainty):.1f}")
```

**Example: Trend Tracking**

```python
# Local linear trend model (level + trend)
result = analyzer.kalman_filter(model='local_linear_trend')

# Extract level and trend
level = result.filtered_state[0, :]  # Current performance level
trend = result.filtered_state[1, :]  # Rate of improvement/decline

# Player improving if trend > 0
improving = trend[-1] > 0
```

**Example: Historical Reconstruction**

```python
# Kalman smoother uses both past and future data
result = analyzer.kalman_smoother(model='local_linear_trend')

# Smoothed estimates (better than filter for historical analysis)
smooth_level = result.smoothed_state[0, :]
smooth_trend = result.smoothed_state[1, :]
```

**Example: Missing Data Imputation**

```python
# Data with missing values
player_data = pd.Series([20, 22, np.nan, np.nan, 25, 24, ...])

analyzer = AdvancedTimeSeriesAnalyzer(player_data)
imputed = analyzer.impute_missing(method='kalman', model='local_level')

# Now imputed.isna().sum() == 0
```

### 2. Dynamic Factor Models

**Use Cases**:
- Extract team momentum/chemistry as latent factor
- Model league-wide trends affecting multiple players
- Decompose multi-player performance into common and idiosyncratic components

**Example: Team Momentum Factor**

```python
# Multiple players on the same team
team_data = pd.DataFrame({
    'player1_pts': player1_points,
    'player2_pts': player2_points,
    'player3_pts': player3_points,
})

analyzer = AdvancedTimeSeriesAnalyzer(team_data)

# Extract single common factor (team momentum)
result = analyzer.dynamic_factor_model(
    data=team_data,
    n_factors=1,
    factor_order=2  # AR(2) for factor dynamics
)

# Team momentum over time
team_momentum = result.factors['factor_0']

# How each player loads on team momentum
print(result.factor_loadings)
# Output:
#              factor_0
# player1_pts      0.85  (strongly influenced by team)
# player2_pts      0.62
# player3_pts      0.71
```

**Example: Model Selection**

```python
# Compare models with different numbers of factors
results = []
for k in range(1, 4):
    result = analyzer.dynamic_factor_model(data=team_data, n_factors=k)
    results.append({
        'n_factors': k,
        'AIC': result.aic,
        'BIC': result.bic,
    })

# Select model with lowest BIC
best_model = min(results, key=lambda x: x['BIC'])
```

### 3. Markov Switching Models

**Use Cases**:
- Detect hot/cold shooting streaks
- Identify season phases (early/mid/late)
- Playoff vs regular season regime shifts
- Injury recovery phases

**Example: Hot/Cold Streak Detection**

```python
# Fit 2-regime model
result = analyzer.markov_switching(
    n_regimes=2,
    regime_type='mean_shift'
)

# Regime parameters
print(f"Cold regime mean: {result.regime_parameters[0]['mean']:.1f}")
print(f"Hot regime mean: {result.regime_parameters[1]['mean']:.1f}")

# Extract hot streak periods
hot_streaks = result.get_regime_periods(regime=1)
for start, end in hot_streaks:
    duration = end - start
    print(f"Hot streak: games {start}-{end} ({duration} games)")

# Transition probabilities
print(result.transition_matrix)
# [[0.95, 0.05],   <- From cold: 95% stay cold, 5% switch to hot
#  [0.10, 0.90]]   <- From hot: 10% switch to cold, 90% stay hot
```

**Example: Regime Probability Tracking**

```python
# Probability of being in each regime over time
regime_probs = result.regime_probabilities

# Plot regime probabilities
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 4))
plt.plot(regime_probs['regime_0'], label='Cold regime', alpha=0.7)
plt.plot(regime_probs['regime_1'], label='Hot regime', alpha=0.7)
plt.fill_between(
    range(len(regime_probs)),
    0, regime_probs['regime_1'],
    alpha=0.3, label='Hot probability'
)
plt.legend()
plt.title('Regime Probabilities Over Time')
plt.show()
```

**Example: Season Phase Detection**

```python
# 3 regimes for early/mid/late season
result = analyzer.markov_switching(n_regimes=3)

# Identify which regime corresponds to which phase
for i in range(3):
    periods = result.get_regime_periods(regime=i)
    avg_game_number = np.mean([start for start, _ in periods])
    print(f"Regime {i}: typically around game {avg_game_number:.0f}")
```

### 4. Structural Time Series (Unobserved Components)

**Use Cases**:
- Decompose performance into skill level, trend, and seasonality
- Career trajectory modeling
- Identify seasonal patterns (back-to-backs, month effects)

**Example: Performance Decomposition**

```python
# Decompose into level + trend
result = analyzer.structural_time_series(
    level=True,
    trend=True,
    seasonal=None
)

# Current skill level
current_skill = result.level.iloc[-1]

# Career trajectory (trend)
career_trend = result.trend.iloc[-1]
improving = career_trend > 0

print(f"Current skill level: {current_skill:.1f}")
print(f"Career trend: {'+' if improving else ''}{career_trend:.2f} pts/game")
```

**Example: Seasonal Patterns**

```python
# Weekly seasonality (back-to-backs, rest days)
result = analyzer.structural_time_series(
    level=True,
    trend=True,
    seasonal=7  # Weekly period
)

# Seasonal component
seasonal_effect = result.seasonal

# Find which day of week has best performance
weekly_pattern = seasonal_effect.iloc[:7]  # First week
best_day = weekly_pattern.argmax()
print(f"Best performance on day {best_day} of the week")
```

**Example: Model Comparison**

```python
# Simple model (level only)
simple = analyzer.structural_time_series(level=True, trend=False)

# Complex model (level + trend + seasonal)
complex = analyzer.structural_time_series(
    level=True,
    trend=True,
    seasonal=7
)

# Compare via information criteria
print(f"Simple model BIC: {simple.bic:.2f}")
print(f"Complex model BIC: {complex.bic:.2f}")

# Lower BIC is better
best = simple if simple.bic < complex.bic else complex
```

### 5. Forecasting

**Example: State Space Forecasting**

```python
# Forecast next 10 games
forecast = analyzer.forecast_state_space(
    model='local_linear_trend',
    steps=10,
    alpha=0.05  # 95% confidence interval
)

# Forecast with uncertainty
print("10-game forecast:")
for i, (f, lb, ub) in enumerate(zip(
    forecast['forecast'],
    forecast['lower_bound'],
    forecast['upper_bound']
), 1):
    print(f"Game +{i}: {f:.1f} ({lb:.1f}, {ub:.1f})")
```

## Advanced Use Cases

### Multi-Player Analysis with Dynamic Factors

```python
# Analyze entire starting lineup
lineup_data = team_stats[['player1_pts', 'player2_pts', 'player3_pts',
                           'player4_pts', 'player5_pts']]

analyzer = AdvancedTimeSeriesAnalyzer(lineup_data)

# Extract 2 factors: offensive flow + defensive intensity
result = analyzer.dynamic_factor_model(data=lineup_data, n_factors=2)

# Identify which factor is which
factor0_loadings = result.factor_loadings['factor_0']
factor1_loadings = result.factor_loadings['factor_1']

if factor0_loadings.std() > factor1_loadings.std():
    print("Factor 0: common factor (team chemistry)")
    print("Factor 1: role differentiation")
else:
    print("Factor 0: role differentiation")
    print("Factor 1: common factor (team chemistry)")
```

### Injury Recovery Tracking

```python
# Track recovery with regime switching
recovery_data = player_points_post_injury

analyzer = AdvancedTimeSeriesAnalyzer(recovery_data)

# 3 regimes: struggling, recovering, back to normal
result = analyzer.markov_switching(n_regimes=3)

# Current regime
current_regime = result.regimes.iloc[-1]
current_mean = result.regime_parameters[current_regime]['mean']

print(f"Current status: Regime {current_regime} (avg {current_mean:.1f} pts)")

# Probability of full recovery
prob_full_recovery = result.regime_probabilities.iloc[-1].max()
print(f"Confidence in current regime: {prob_full_recovery:.1%}")
```

### Playoff Performance Shift

```python
# Detect playoff vs regular season performance
season_data = player_points  # Include both regular + playoff

analyzer = AdvancedTimeSeriesAnalyzer(season_data)

# 2 regimes: regular season vs playoff
result = analyzer.markov_switching(n_regimes=2)

# Identify which regime is playoff
# (Assuming playoff is later in the data)
late_season_regime = result.regimes.iloc[-20:].mode()[0]

playoff_mean = result.regime_parameters[late_season_regime]['mean']
regular_mean = result.regime_parameters[1 - late_season_regime]['mean']

playoff_boost = playoff_mean - regular_mean
print(f"Playoff performance change: {'+' if playoff_boost > 0 else ''}{playoff_boost:.1f} pts")
```

## Integration with Other Modules

### With Panel Data (Module 4B)

```python
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer

# Panel data: multiple players over time
panel = PanelDataAnalyzer(data, entity_col='player_id', time_col='game_date')

# Apply Kalman filter to each player
results = {}
for player_id in panel.data['player_id'].unique():
    player_data = panel.data[panel.data['player_id'] == player_id]['points']
    analyzer = AdvancedTimeSeriesAnalyzer(player_data)
    results[player_id] = analyzer.kalman_filter(model='local_level')
```

### With Bayesian Methods (Module 4D)

```python
from mcp_server.bayesian import BayesianAnalyzer
from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer

# Compare frequentist Kalman filter vs Bayesian approach
freq_analyzer = AdvancedTimeSeriesAnalyzer(data)
freq_result = freq_analyzer.kalman_filter(model='local_level')

bayes_analyzer = BayesianAnalyzer(data)
bayes_result = bayes_analyzer.bayesian_structural_time_series()

# Both provide uncertainty quantification, different philosophies
```

### With MLflow Tracking

```python
import mlflow

# Track experiments
analyzer = AdvancedTimeSeriesAnalyzer(
    data,
    mlflow_experiment='player_tracking'
)

with mlflow.start_run():
    result = analyzer.kalman_filter(model='local_linear_trend')

    mlflow.log_metric('log_likelihood', result.log_likelihood)
    mlflow.log_param('model', 'local_linear_trend')
```

## Performance Considerations

### Computational Complexity

- **Kalman Filter**: O(n·k²) where n = observations, k = state dimension
- **Dynamic Factor**: O(n·m·f²) where m = series, f = factors
- **Markov Switching**: O(n·r²) where r = regimes (can be slow for r > 3)
- **Structural TS**: O(n·k²) similar to Kalman filter

### Convergence Issues

Some models (especially Markov switching with many regimes) may fail to converge:

```python
import warnings

# Handle convergence warnings
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=ConvergenceWarning)
    result = analyzer.markov_switching(n_regimes=3)

# Check convergence
if hasattr(result.model, 'mle_retvals'):
    if result.model.mle_retvals['converged']:
        print("✓ Model converged")
    else:
        print("⚠ Convergence issues - results may be unreliable")
```

### Tips for Better Convergence

1. **Start with simpler models** (fewer factors/regimes)
2. **Scale your data** to have reasonable magnitude
3. **Provide good initial values** if available
4. **Use more iterations**: `model_kwargs={'maxiter': 1000}`

## API Reference

### AdvancedTimeSeriesAnalyzer

**Constructor**:
```python
AdvancedTimeSeriesAnalyzer(
    data: Union[pd.Series, pd.DataFrame],
    freq: Optional[str] = None,
    mlflow_experiment: Optional[str] = None
)
```

**Methods**:

- `kalman_filter(model, exog=None, **kwargs) -> KalmanFilterResult`
- `kalman_smoother(model, **kwargs) -> SmootherResult`
- `forecast_state_space(model, steps, **kwargs) -> Dict`
- `dynamic_factor_model(data, n_factors, **kwargs) -> DynamicFactorResult`
- `markov_switching(n_regimes, regime_type, **kwargs) -> MarkovSwitchingResult`
- `structural_time_series(level, trend, seasonal, **kwargs) -> StructuralTimeSeriesResult`
- `impute_missing(method, model, **kwargs) -> pd.Series`

### Result Objects

All result objects support:
- Rich `__repr__` for interactive exploration
- Access to fitted statsmodels model via `.model` attribute
- Information criteria (AIC, BIC, log-likelihood)

## Testing

Run the comprehensive test suite:

```bash
# All tests
pytest tests/test_advanced_time_series.py -v

# Specific test category
pytest tests/test_advanced_time_series.py -k "kalman" -v
pytest tests/test_advanced_time_series.py -k "markov" -v
pytest tests/test_advanced_time_series.py -k "dynamic_factor" -v
pytest tests/test_advanced_time_series.py -k "structural" -v
```

**Test Coverage**: 28 tests covering all major functionality (100% pass rate)

## Known Limitations

1. **Convergence**: Markov switching models with >2 regimes may fail to converge
2. **Data Requirements**: Models need sufficient data (n > 50 recommended)
3. **Missing Data**: Large gaps in data may cause issues for some methods
4. **Multivariate**: Dynamic factor models require m > f (more series than factors)
5. **Seasonality**: Seasonal models need data covering multiple seasonal periods

## References

- Durbin, J., & Koopman, S. J. (2012). *Time Series Analysis by State Space Methods*. Oxford University Press.
- Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press.
- Harvey, A. C. (1990). *Forecasting, Structural Time Series Models and the Kalman Filter*. Cambridge University Press.
- Statsmodels State Space Documentation: https://www.statsmodels.org/stable/statespace.html

## Support

For issues, questions, or contributions:
- GitHub: [nba-mcp-synthesis](https://github.com/yourusername/nba-mcp-synthesis)
- Tests: `tests/test_advanced_time_series.py`
- Module: `mcp_server/advanced_time_series.py`

---

**Module Status**: ✅ Complete (Module 4C)
**Test Coverage**: 28/28 tests passing (100%)
**Lines of Code**: ~850 LOC (implementation) + ~600 LOC (tests)
