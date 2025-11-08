# NBA MCP Synthesis - Quick Reference

**One-page cheat sheet** for the most common methods. For complete documentation, see [API Reference](API_REFERENCE.md).

---

## 🚀 Quick Start

```python
from mcp_server.econometric_suite import EconometricSuite
from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.survival_analysis import SurvivalAnalyzer
```

---

## 📊 Time Series Analysis

### Basic Setup
```python
analyzer = TimeSeriesAnalyzer(data=df, target_column='points', time_column='date')
```

### Common Methods
```python
# Stationarity
analyzer.adf_test()                              # ~5ms
analyzer.kpss_test()                             # ~5ms
analyzer.test_stationarity()                     # ~10ms

# Decomposition
analyzer.decompose(period=7)                     # ~20ms
analyzer.stl_decompose(period=7)                 # ~30ms
analyzer.detect_trend()                          # ~10ms

# Forecasting
analyzer.fit_arima(order=(1,1,1))                # ~50ms
analyzer.auto_arima()                            # ~500ms
analyzer.forecast(steps=10)                      # ~30ms
analyzer.validate_forecast(test_size=20)         # ~100ms

# Multivariate
analyzer.fit_var(columns=['pts','ast'], maxlags=2)  # ~100ms
analyzer.granger_causality_test('assists', 'points')  # ~50ms
```

---

## 👥 Panel Data Analysis

### Basic Setup
```python
analyzer = PanelDataAnalyzer(data=df, entity_col='player_id', time_col='season')
```

### Common Methods
```python
# Regression Models
analyzer.pooled_ols(formula='y ~ x1 + x2')       # ~30ms
analyzer.fixed_effects(formula='y ~ x1 + x2')    # ~50ms
analyzer.random_effects(formula='y ~ x1 + x2')   # ~80ms

# Tests
analyzer.hausman_test(formula='y ~ x1 + x2')     # ~100ms
analyzer.f_test_effects(formula='y ~ x1 + x2')   # ~60ms

# Advanced
analyzer.first_difference(formula='y ~ x1')      # ~40ms
analyzer.clustered_standard_errors(formula='y ~ x1')  # ~70ms
```

---

## 🎯 Causal Inference

### Basic Setup
```python
analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='coaching_change',
    outcome_col='wins',
    covariates=['payroll', 'win_pct_prev']
)
```

### Common Methods
```python
# Matching Methods
analyzer.propensity_score_matching()             # ~150ms
analyzer.kernel_matching()                       # ~200ms
analyzer.radius_matching(caliper=0.1)            # ~180ms

# Other Methods
analyzer.instrumental_variables(instruments=['Z'])  # ~100ms
analyzer.regression_discontinuity(running_var='score', cutoff=50)  # ~120ms
analyzer.synthetic_control(treatment_time=10)    # ~300ms
analyzer.doubly_robust_estimation()              # ~200ms
analyzer.sensitivity_analysis()                  # ~150ms
```

---

## 📈 Survival Analysis

### Basic Setup
```python
analyzer = SurvivalAnalyzer(
    data=df,
    duration_col='career_years',
    event_col='retired',
    covariates=['age', 'performance']
)
```

### Common Methods
```python
# Non-parametric
analyzer.kaplan_meier()                          # ~5ms
analyzer.logrank_test(group_col='position')      # ~10ms

# Regression
analyzer.cox_proportional_hazards()              # ~40ms
analyzer.cox_time_varying()                      # ~80ms
analyzer.parametric_survival(distribution='weibull')  # ~50ms

# Competing Risks
analyzer.competing_risks()                       # ~60ms
analyzer.fine_gray_model(event_of_interest=1)    # ~90ms
```

---

## 🎲 Bayesian Methods

### Basic Setup
```python
analyzer = BayesianAnalyzer(data=df, target='points')
```

### Common Methods
```python
# Model Building
analyzer.build_simple_model(formula='points ~ age + minutes')  # ~100ms
analyzer.hierarchical_model(group_col='team_id')  # ~150ms

# Inference (slower - MCMC)
analyzer.sample_posterior(draws=1000, tune=500)  # ~5s
analyzer.variational_inference(n=5000)           # ~2s

# Analysis
analyzer.posterior_summary()                     # ~50ms
analyzer.credible_interval('age', probability=0.95)  # ~20ms
analyzer.check_convergence()                     # ~30ms
analyzer.waic()                                  # ~100ms
analyzer.loo()                                   # ~100ms
analyzer.posterior_predictive_check()            # ~200ms
```

---

## 🚦 Real-Time Analytics

### Particle Filters
```python
from mcp_server.particle_filters import PlayerPerformanceParticleFilter

# Setup
pf = PlayerPerformanceParticleFilter(n_particles=1000)

# Track performance
result = pf.filter_player_season(
    data=player_data,
    target_col='points'
)  # ~10ms per game
```

### Streaming Analytics
```python
from mcp_server.streaming_analytics import StreamingAnalyzer

# Setup
stream = StreamingAnalyzer(buffer_size=1000, window_seconds=300)

# Process events
stream.process_event(event)                      # <1ms
stream.get_live_stats()                          # <1ms
stream.detect_anomalies(metric='points')         # ~2ms
```

### Live Game Tracking
```python
from mcp_server.particle_filters import LiveGameProbabilityFilter

# Setup
game_filter = LiveGameProbabilityFilter(
    n_particles=2000,
    home_strength=5.0,
    away_strength=3.0
)

# Track game
result = game_filter.track_game(score_updates)   # ~5ms per update
```

---

## 🤖 Ensemble Methods

### Simple Ensemble
```python
from mcp_server.ensemble import SimpleEnsemble

ensemble = SimpleEnsemble(models=[model1, model2, model3])
predictions = ensemble.predict(n_steps=10)       # ~50ms
metrics = ensemble.evaluate(y_true=actual, n_steps=10)  # ~30ms
```

### Weighted Ensemble
```python
from mcp_server.ensemble import WeightedEnsemble

ensemble = WeightedEnsemble(
    models=[model1, model2],
    optimize_weights=True
)
predictions = ensemble.predict(n_steps=10)       # ~60ms
```

### Stacking Ensemble
```python
from mcp_server.ensemble import StackingEnsemble
from sklearn.linear_model import Ridge

ensemble = StackingEnsemble(
    base_models=[model1, model2, model3],
    meta_model=Ridge(),
    cv_folds=5
)
ensemble.fit(X_train, y_train)                   # ~200ms
predictions = ensemble.predict(X_test)           # ~20ms
```

---

## 🔧 Common Patterns

### Pattern 1: Quick Exploration
```python
from mcp_server.econometric_suite import EconometricSuite

suite = EconometricSuite(data=df, target='outcome')
result = suite.analyze(method='arima')
```

### Pattern 2: Custom Pipeline
```python
# Step 1: Test stationarity
ts = TimeSeriesAnalyzer(data=df, target_column='points')
if not ts.adf_test().is_stationary:
    ts.difference(periods=1)

# Step 2: Forecast
result = ts.fit_arima(order=(2,1,1))
forecast = ts.forecast(steps=10)

# Step 3: Validate
validation = ts.validate_forecast(test_size=20)
```

### Pattern 3: Comparison Study
```python
# Compare multiple players
panel = PanelDataAnalyzer(data=multi_player_df, entity_col='player_id')
fe_result = panel.fixed_effects(formula='points ~ age + minutes')

# Extract individual effects
effects = fe_result.entity_effects
top_players = effects.nlargest(5)
```

---

## 📋 Data Requirements

| Method | Min Observations | Data Structure |
|--------|-----------------|----------------|
| ARIMA | 30-50 | Time series |
| VAR | 50-100 | Multivariate TS |
| Panel FE/RE | 30+ entities, 5+ time | Panel |
| PSM | 100+ | Cross-sectional |
| Cox Model | 50+ | Survival data |
| Bayesian MCMC | 20+ | Any |
| Particle Filter | 20+ | Time series |

---

## ⚡ Performance Guide

| Speed Category | Time Range | Methods |
|---------------|------------|---------|
| **Lightning** | <1ms | Streaming analytics |
| **Real-time** | 1-10ms | Particle filters, KM |
| **Fast** | 10-100ms | ARIMA, Cox, FE/RE |
| **Medium** | 100-500ms | VAR, PSM, ensembles |
| **Slow** | 0.5-5s | MCMC, cross-validation |

---

## 🐛 Common Issues

### Issue: "Insufficient data"
```python
# Need more observations
assert len(df) >= 30, "Need at least 30 observations for ARIMA"
```

### Issue: "Non-convergence"
```python
# Increase MCMC samples
result = analyzer.sample_posterior(draws=2000, tune=1000)
```

### Issue: "Singular matrix"
```python
# Check for collinearity
from statsmodels.stats.outliers_influence import variance_inflation_factor
for i, col in enumerate(X.columns):
    vif = variance_inflation_factor(X.values, i)
    print(f"{col}: {vif}")
```

---

## 🔍 Quick Diagnostics

```python
# Time Series
ts.test_stationarity()                    # Check stationarity
ts.ljung_box_test(lags=10)                # Check autocorrelation
ts.detect_structural_breaks()             # Find break points

# Panel Data
panel.balance_check()                     # Check balanced/unbalanced
panel.hausman_test(formula='y ~ x')       # FE vs RE

# Survival
survival.model_comparison()               # Compare models

# Bayesian
bayes.check_convergence()                 # Check MCMC convergence
bayes.posterior_predictive_check()        # Model fit
```

---

## 📚 More Resources

- **[Getting Started](GETTING_STARTED.md)** - Installation and first steps
- **[Complete Tutorial](tutorials/COMPLETE_WORKFLOW_TUTORIAL.md)** - End-to-end workflow
- **[API Reference](API_REFERENCE.md)** - Full method documentation
- **[Benchmarks](plans/BENCHMARKING_COMPLETION_SUMMARY.md)** - Performance data

---

**💡 Tip:** Start with simple methods (ARIMA, FE) before complex ones (MCMC, VAR). Validate results with multiple approaches.

**🏀 NBA MCP Synthesis - 100+ Methods, One Platform**
