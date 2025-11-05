# NBA MCP Econometric Framework - Quick Reference

**Version**: 1.0 | **Date**: November 1, 2025

---

## Initialization

```python
from mcp_server.econometric_suite import EconometricSuite

# Basic setup
suite = EconometricSuite(
    data=df,
    outcome_var='points',
    treatment_var='minutes',
    control_vars=['rebounds', 'assists']
)
```

---

## Method Quick Reference

### Basic Analysis

| Method | Code | When to Use | Output |
|--------|------|-------------|--------|
| **OLS Regression** | `suite.ols_analysis()` | Linear relationships, continuous outcome | coefficients, R², p-values |
| **Logistic Regression** | `suite.logistic_analysis()` | Binary outcome (win/loss) | odds ratios, predictions |
| **T-Test** | `suite.ttest_analysis()` | Compare two groups | t-statistic, p-value |
| **Correlation** | `suite.correlation_analysis()` | Measure associations | correlation matrix |

### Time Series

| Method | Code | When to Use | Output |
|--------|------|-------------|--------|
| **ARIMA** | `suite.time_series_analysis(method='arima', forecast_periods=10)` | Univariate forecasting | forecasts + CI |
| **BVAR** | `suite.bayesian_time_series_analysis(method='bvar')` | Multivariate with uncertainty | forecasts, IRF, FEVD |
| **BSTS** | `suite.bayesian_time_series_analysis(method='bsts')` | Component decomposition | trend, seasonality |

### Panel Data

| Method | Code | When to Use | Output |
|--------|------|-------------|--------|
| **Fixed Effects** | `suite.panel_data_analysis(entity_effects=True)` | Multiple entities over time | within-entity effects |
| **Hierarchical Bayesian** | `suite.bayesian_time_series_analysis(method='hierarchical')` | Nested structure, shrinkage | player/team effects |

### Causal Inference

| Method | Code | When to Use | Output |
|--------|------|-------------|--------|
| **PSM** | `suite.causal_analysis(method='propensity_score_matching')` | Evaluate treatment effect | ATE, ATT |
| **DiD** | `suite.difference_in_differences(time_var='period')` | Before/after comparison | DiD estimator |
| **RDD** | `suite.regression_discontinuity(running_var='draft_pick', cutoff=14.5)` | Sharp threshold | discontinuity estimate |

### Real-Time Methods

| Method | Code | When to Use | Output |
|--------|------|-------------|--------|
| **Particle Filter (Player)** | `create_player_filter(data, n_particles=1000)` | Track player performance live | skill/form estimates |
| **Particle Filter (Game)** | `create_game_filter(home_rating, away_rating)` | Live win probability | win prob history |

---

## Common Parameters

### MCMC Settings (Bayesian Methods)

```python
result = suite.bayesian_time_series_analysis(
    method='bvar',
    draws=1000,        # Number of posterior samples (default: 1000)
    tune=1000,         # Burn-in iterations (default: 1000)
    chains=4,          # Parallel chains (default: 4)
    lambda1=0.2        # Minnesota prior shrinkage (BVAR only)
)
```

**Quick Guide**:
- **Exploration**: `draws=500, tune=500, chains=2` → ~30s
- **Production**: `draws=2000, tune=1000, chains=4` → ~120s

### Time Series

```python
result = suite.time_series_analysis(
    method='arima',
    forecast_periods=10,    # Number of periods to forecast
    seasonal_period=None    # Seasonal period (e.g., 7 for weekly)
)
```

### Panel Data

```python
result = suite.panel_data_analysis(
    entity_effects=True,     # Player/team fixed effects
    time_effects=False,      # Time period fixed effects
    entity_var='player',     # Entity identifier
    time_var='date'          # Time identifier
)
```

### Particle Filters

```python
# Player performance tracking
pf = create_player_filter(data, n_particles=1000)
result = pf.filter_player_season(data, target_col='points')

# Live game probability
pf = create_game_filter(home_rating=3.0, away_rating=2.5, n_particles=2000)
result = pf.track_game(score_updates=[(12.0, 25, 22), (24.0, 50, 48)])
```

---

## Result Attributes

### OLS Result

```python
result = suite.ols_analysis()

# Coefficients
result.params['treatment']               # Point estimate
result.pvalues['treatment']              # P-value
result.conf_int()['treatment']           # Confidence interval

# Model fit
result.rsquared                          # R²
result.rsquared_adj                      # Adjusted R²
result.aic                               # AIC
result.bic                               # BIC

# Diagnostics
result.diagnostics['normality_pvalue']   # Jarque-Bera test
result.diagnostics['het_test']           # Heteroscedasticity test

# Predictions
predictions = result.predict(new_data)
```

### Time Series Result

```python
result = suite.time_series_analysis(method='arima', forecast_periods=10)

# Forecast
result.forecast['forecast']              # Point forecasts
result.forecast['lower_ci']              # Lower CI
result.forecast['upper_ci']              # Upper CI

# Model info
result.summary                           # Full summary
result.aic                               # AIC
```

### Bayesian Time Series Result

```python
result = suite.bayesian_time_series_analysis(method='bvar')

# Convergence
result.convergence_ok                    # Boolean
result.diagnostics['rhat_max']           # Max Rhat (should be <1.05)
result.diagnostics['ess_min']            # Min ESS (should be >400)

# Forecasts
result.forecast                          # Forecast distribution

# BVAR-specific
result.irf                               # Impulse response functions
result.fevd                              # Forecast error variance decomp
```

### Causal Analysis Result

```python
result = suite.causal_analysis(method='propensity_score_matching')

# Treatment effects
result.ate                               # Average treatment effect
result.att                               # Effect on treated
result.ate_ci                            # ATE confidence interval

# Diagnostics
result.common_support                    # Common support check
result.balance_stats                     # Covariate balance
```

### Particle Filter Result

```python
# Player tracking
result = pf.filter_player_season(data, target_col='points')

result.final_skill_mean                  # Final skill estimate
result.final_form_mean                   # Final form estimate
result.skill_history                     # Skill over time
result.form_history                      # Form over time
result.ess_history                       # Effective sample size

# Game tracking
result = pf.track_game(score_updates)

result.final_win_prob                    # Final win probability
result.win_prob_history                  # Win prob over time
result.resampling_history                # When resampling occurred
```

---

## Data Preparation Cheat Sheet

### Required Data Format

| Analysis Type | Required Columns | Index | Sorting |
|--------------|------------------|-------|---------|
| OLS | outcome, treatment, controls | - | No |
| Time Series | outcome, date | date | Yes (by date) |
| Panel Data | outcome, entity_id, time, vars | (entity, time) | Yes |
| PSM | outcome, treatment, controls | - | No |
| Particle Filter | target variable, date/possession | - | Yes (by time) |

### Common Transformations

```python
# Date handling
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Create lags
df['points_lag1'] = df.groupby('player')['points'].shift(1)

# Create differences
df['points_diff'] = df.groupby('player')['points'].diff()

# Rolling statistics
df['points_ma5'] = df.groupby('player')['points'].rolling(5).mean().reset_index(drop=True)

# Binary variables
df['won'] = (df['points'] > df['opp_points']).astype(int)

# Categorical encoding
df = pd.get_dummies(df, columns=['position'], drop_first=True)
```

---

## Error Messages & Solutions

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `KeyError: 'outcome_var'` | Column not in DataFrame | Check column names match exactly |
| `Rhat > 1.05` | MCMC not converged | Increase `draws` and `tune` |
| `LinAlgError: Singular matrix` | Perfect multicollinearity | Remove redundant variables |
| `ValueError: could not convert string to float` | Non-numeric data | Convert or encode categorical variables |
| `IndexError` | Missing time index | Set date as index for time series |

---

## Performance Guidelines

| Method | Typical Time | When to Use | When to Avoid |
|--------|--------------|-------------|---------------|
| OLS | <1s | Always start here | Non-linear relationships |
| ARIMA | ~5s | Forecasting | Need multi-series |
| BVAR | 60-120s | Multivariate forecast + uncertainty | Time-critical applications |
| Hierarchical | 80-180s | Nested data structure | Small sample (<50 entities) |
| Particle Filter | <1s | Real-time tracking | Batch processing |

**Optimization Tips**:
- Use `draws=500` for exploration
- Parallelize chains: `chains=4` on 4-core CPU
- Use informative priors: `lambda1=0.2` for BVAR
- Cache results for repeated analyses

---

## Validation Checklist

**Before Analysis**:
- [ ] Data sorted correctly (time series)
- [ ] No missing values in key variables
- [ ] Outcome variable is appropriate type (numeric/binary)
- [ ] Sample size adequate (n > 30)

**After Fitting**:
- [ ] Check p-values and confidence intervals
- [ ] Validate assumptions (residual plots)
- [ ] For Bayesian: `rhat_max < 1.05`, `ess_min > 400`
- [ ] Test on holdout data

---

## Plotting

```python
import matplotlib.pyplot as plt

# Coefficients plot
result.plot_coefficients()

# Residuals
result.plot_residuals()

# Forecasts with CI
result.plot_forecast()

# IRF (BVAR)
result.plot_irf()

# Particle filter tracking
result.plot_states()
```

---

## Import Shortcuts

```python
# Everything you need
from mcp_server.econometric_suite import EconometricSuite
from mcp_server.particle_filters import create_player_filter, create_game_filter
from mcp_server.bayesian_time_series import BVARAnalyzer, BayesianStructuralTS, HierarchicalBayesianTS

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

---

## Useful Links

- **Full Tutorials**: `examples/01_nba_101_getting_started.ipynb` → `05_live_game_analytics_dashboard.ipynb`
- **Best Practices**: `examples/BEST_PRACTICES.md`
- **Performance Report**: `BAYESIAN_METHODS_PERFORMANCE_REPORT.md`
- **API Docs**: `mcp_server/econometric_suite.py`
- **GitHub Issues**: https://github.com/anthropics/nba-mcp-synthesis/issues

---

## Method Selection Flowchart

```
START
  ↓
Binary outcome (0/1)?
  YES → Logistic Regression
  NO → Continue
  ↓
Time series data?
  YES → Univariate?
      YES → ARIMA
      NO → BVAR
  NO → Continue
  ↓
Panel data (entities × time)?
  YES → Fixed Effects or Hierarchical Bayesian
  NO → Continue
  ↓
Causal question?
  YES → Treatment occurred?
      YES → PSM or DiD
      NO → RDD (if threshold)
  NO → OLS Regression
  ↓
END
```

---

**Print this page and keep it handy while coding!**

Last Updated: November 1, 2025 | Version 1.0
