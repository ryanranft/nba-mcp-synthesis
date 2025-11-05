# NBA MCP Econometric Framework - Best Practices Guide

**Version**: 1.0
**Last Updated**: November 1, 2025
**Audience**: Data scientists, analysts, engineers using the framework

---

## Table of Contents

1. [General Principles](#general-principles)
2. [Method Selection](#method-selection)
3. [Data Preparation](#data-preparation)
4. [Model Validation](#model-validation)
5. [Performance Optimization](#performance-optimization)
6. [Production Deployment](#production-deployment)
7. [Common Pitfalls](#common-pitfalls)
8. [Code Examples](#code-examples)

---

## General Principles

### 1. Start Simple, Then Add Complexity

**Guideline**: Begin with basic methods (OLS, t-tests) before moving to advanced methods (Bayesian VAR, particle filters).

**Why**: Simple methods:
- Are faster to compute and debug
- Have clearer assumptions
- Provide baseline results for comparison
- Help identify data issues early

**Example**:
```python
# Start with OLS
suite = EconometricSuite(data=df, outcome_var='points', treatment_var='minutes')
ols_result = suite.ols_analysis()

# If assumptions hold, proceed to time series
ts_result = suite.time_series_analysis(method='arima')

# Only if needed, use Bayesian methods
bayesian_result = suite.bayesian_time_series_analysis(method='bvar')
```

### 2. Always Validate Assumptions

**Key Assumptions by Method**:

| Method | Key Assumptions |
|--------|----------------|
| OLS | Linearity, independence, homoscedasticity, normality of residuals |
| Panel FE | No time-varying confounders (after FE) |
| ARIMA | Stationarity (after differencing), no autocorrelation in residuals |
| Propensity Score Matching | Conditional independence, common support |
| DiD | Parallel trends in absence of treatment |
| RDD | Continuity of potential outcomes at cutoff |

**Validation Tools**:
```python
# OLS diagnostics
result = suite.ols_analysis()
diagnostics = result.diagnostics

print(f"R²: {diagnostics['r_squared']}")
print(f"Normality test p-value: {diagnostics['normality_pvalue']}")
print(f"Heteroscedasticity test: {diagnostics['het_test']}")

# Plot residuals
suite.plot_diagnostics(result)
```

### 3. Quantify Uncertainty

**Guideline**: Always report confidence intervals, not just point estimates.

**Why**:
- Single-point estimates mislead about precision
- Decision-makers need to understand risk
- Statistical significance ≠ practical significance

**Example**:
```python
# Bad: Only point estimate
effect = result.params['treatment']

# Good: Include confidence interval
effect = result.params['treatment']
ci_lower, ci_upper = result.conf_int()['treatment']

print(f"Effect: {effect:.2f} (95% CI: [{ci_lower:.2f}, {ci_upper:.2f}])")

# Best: Report both statistical and practical significance
if ci_lower > 0:
    print("✓ Statistically significant at 5% level")
    if effect > 2.0:  # Domain-specific threshold
        print("✓ Practically significant (>2 points)")
```

---

## Method Selection

### Decision Tree

```
Is the outcome binary (Win/Loss)?
├─ YES → Use logistic_analysis()
└─ NO → Continue

Is there a time component?
├─ YES → Is it univariate?
│   ├─ YES → time_series_analysis(method='arima')
│   └─ NO → bayesian_time_series_analysis(method='bvar')
└─ NO → Continue

Multiple entities (players/teams) observed over time?
├─ YES → panel_data_analysis()
└─ NO → Continue

Evaluating a treatment/intervention?
├─ YES → causal_analysis(method='propensity_score_matching')
└─ NO → ols_analysis()
```

### Method Comparison Table

| Use Case | Recommended Method | Alternative | When to Use Alternative |
|----------|-------------------|-------------|------------------------|
| Player performance forecast | ARIMA | BSTS | Need component decomposition |
| Win probability | Logistic regression | Particle filter | Real-time updates needed |
| Contract valuation | OLS regression | Random forest | Non-linear relationships |
| Team comparison | Panel fixed effects | Hierarchical Bayesian | Need shrinkage/borrowing |
| Coaching change impact | Difference-in-differences | Synthetic control | No clear control group |
| Draft value | Regression discontinuity | IV regression | No sharp cutoff |
| Live game tracking | Particle filter | Kalman filter | Linear Gaussian system |

### Performance vs Accuracy Trade-off

| Method | Speed | Accuracy | Uncertainty Quantification |
|--------|-------|----------|---------------------------|
| OLS | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ |
| ARIMA | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| BVAR | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| BSTS | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Hierarchical Bayesian | ⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Particle Filter | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Data Preparation

### 1. Handle Missing Data Appropriately

**Options** (in order of preference):

1. **Use complete cases** (if missingness is <5%)
```python
df_complete = df.dropna(subset=['points', 'minutes', 'rebounds'])
```

2. **Forward fill for time series** (if missingness is sporadic)
```python
df['points'] = df.groupby('player')['points'].fillna(method='ffill')
```

3. **Impute with mean/median** (if missingness is random)
```python
df['points'].fillna(df['points'].median(), inplace=True)
```

4. **Multiple imputation** (if missingness is >10% and systematic)
```python
# Use scikit-learn IterativeImputer
from sklearn.impute import IterativeImputer
imputer = IterativeImputer(random_state=42)
df_imputed = imputer.fit_transform(df[numeric_cols])
```

**⚠️ Warning**: Never drop cases silently. Always report how missing data was handled.

### 2. Scale Variables When Needed

**When to scale**:
- Using regularized methods (Lasso, Ridge)
- Comparing coefficients across variables
- Numerical stability issues

**Example**:
```python
from sklearn.preprocessing import StandardScaler

# Scale continuous variables
scaler = StandardScaler()
df[['age', 'experience', 'salary']] = scaler.fit_transform(
    df[['age', 'experience', 'salary']]
)

# Don't scale binary/categorical variables
# Keep 'position', 'home_game' as is
```

### 3. Create Meaningful Time Variables

**For time series**:
```python
# Convert to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by time (critical!)
df = df.sort_values(['player', 'date'])

# Create time index
df['game_number'] = df.groupby('player').cumcount() + 1
df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
```

**For panel data**:
```python
# Set multi-index
df = df.set_index(['player', 'date'])

# Ensure balanced panel (optional)
df = df.unstack().stack(dropna=False)
```

---

## Model Validation

### 1. Train/Test Splits for Time Series

**Wrong** ❌:
```python
# Random split breaks temporal order!
from sklearn.model_selection import train_test_split
train, test = train_test_split(df, test_size=0.2)
```

**Correct** ✅:
```python
# Temporal split preserves order
split_point = int(len(df) * 0.8)
train = df.iloc[:split_point]
test = df.iloc[split_point:]
```

**Best** ⭐:
```python
# Rolling window cross-validation
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(df):
    train = df.iloc[train_idx]
    test = df.iloc[test_idx]
    # Fit and evaluate
```

### 2. Out-of-Sample Validation

**Guideline**: Always validate on holdout data.

```python
# Fit on training data
suite_train = EconometricSuite(data=train, outcome_var='points', treatment_var='minutes')
result = suite_train.ols_analysis()

# Predict on test data
predictions = result.predict(test)

# Evaluate
from sklearn.metrics import mean_absolute_error, r2_score
mae = mean_absolute_error(test['points'], predictions)
r2 = r2_score(test['points'], predictions)

print(f"Test MAE: {mae:.2f}")
print(f"Test R²: {r2:.3f}")
```

### 3. Check Convergence for Bayesian Methods

**Critical for MCMC**:

```python
result = suite.bayesian_time_series_analysis(
    method='bvar',
    draws=1000,
    tune=1000,
    chains=4
)

# Check diagnostics
print(f"Rhat max: {result.diagnostics['rhat_max']:.3f}")  # Should be <1.05
print(f"ESS min: {result.diagnostics['ess_min']:.0f}")    # Should be >400
print(f"Divergences: {result.diagnostics['divergences']}")  # Should be 0

if not result.convergence_ok:
    print("⚠️ Model did not converge! Increase draws or tune.")
```

---

## Performance Optimization

### 1. Start with Fewer Draws for Exploration

**Bayesian Methods**:

```python
# Exploration phase (fast)
result = suite.bayesian_time_series_analysis(
    method='bvar',
    draws=500,      # Reduce from 2000
    tune=500,       # Reduce from 1000
    chains=2        # Reduce from 4
)
# Time: ~30s

# Production phase (accurate)
result = suite.bayesian_time_series_analysis(
    method='bvar',
    draws=2000,
    tune=1000,
    chains=4
)
# Time: ~120s
```

### 2. Parallelize When Possible

**Multiple independent analyses**:

```python
from concurrent.futures import ProcessPoolExecutor

players = ['LeBron James', 'Stephen Curry', 'Kevin Durant']

def analyze_player(player_name):
    player_data = df[df['player'] == player_name]
    suite = EconometricSuite(data=player_data, outcome_var='points')
    return suite.time_series_analysis(method='arima')

# Parallel execution
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(analyze_player, players))
```

### 3. Cache Expensive Computations

```python
import joblib

# Cache model results
@joblib.Memory(location='./cache').cache
def fit_model(data_hash):
    suite = EconometricSuite(data=df, outcome_var='points')
    return suite.bayesian_time_series_analysis(method='bvar')

# Subsequent calls with same data use cache
result = fit_model(hash(df.to_string()))
```

### 4. Use Informative Priors for Bayesian Methods

**BVAR with Minnesota Prior** (essential):

```python
# Default: Informative prior (recommended)
result = suite.bayesian_time_series_analysis(
    method='bvar',
    lambda1=0.2  # Shrinkage toward random walk
)

# Improves convergence by 30-50%
```

---

## Production Deployment

### 1. Error Handling

```python
def analyze_with_fallback(df, method='bayesian'):
    """Robust analysis with fallback to simpler methods."""
    suite = EconometricSuite(data=df, outcome_var='points', treatment_var='minutes')

    try:
        if method == 'bayesian':
            return suite.bayesian_time_series_analysis(method='bvar')
    except Exception as e:
        print(f"Bayesian method failed: {e}")
        print("Falling back to ARIMA...")

        try:
            return suite.time_series_analysis(method='arima')
        except Exception as e2:
            print(f"ARIMA failed: {e2}")
            print("Falling back to OLS...")
            return suite.ols_analysis()
```

### 2. Logging and Monitoring

```python
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fit_model_with_logging(df):
    logger.info("Starting model fit...")
    start_time = time.time()

    suite = EconometricSuite(data=df, outcome_var='points')

    try:
        result = suite.bayesian_time_series_analysis(method='bvar')
        elapsed = time.time() - start_time

        logger.info(f"✓ Model fit successful in {elapsed:.1f}s")
        logger.info(f"  Convergence: {result.convergence_ok}")
        logger.info(f"  Rhat max: {result.diagnostics['rhat_max']:.3f}")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Model fit failed after {elapsed:.1f}s: {e}")
        raise
```

### 3. API Design

**RESTful endpoint example**:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ForecastRequest(BaseModel):
    player_id: str
    n_periods: int = 10

@app.post("/forecast")
async def forecast_player_performance(request: ForecastRequest):
    try:
        # Load data
        player_data = load_player_data(request.player_id)

        # Fit model
        suite = EconometricSuite(data=player_data, outcome_var='points')
        result = suite.time_series_analysis(
            method='arima',
            forecast_periods=request.n_periods
        )

        # Return forecast
        return {
            "player_id": request.player_id,
            "forecast": result.forecast['forecast'].tolist(),
            "lower_ci": result.forecast['lower_ci'].tolist(),
            "upper_ci": result.forecast['upper_ci'].tolist()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Common Pitfalls

### 1. P-Hacking and Multiple Testing

**Problem**: Testing many hypotheses increases false positive rate.

**Solution**: Adjust for multiple comparisons.

```python
from statsmodels.stats.multitest import multipletests

# Test multiple treatments
treatments = ['minutes', 'rebounds', 'assists', 'fouls']
pvalues = []

for treatment in treatments:
    suite = EconometricSuite(data=df, outcome_var='points', treatment_var=treatment)
    result = suite.ols_analysis()
    pvalues.append(result.pvalues[treatment])

# Bonferroni correction
reject, pvals_corrected, _, _ = multipletests(pvalues, method='bonferroni', alpha=0.05)

for treatment, pval, pval_corr, rej in zip(treatments, pvalues, pvals_corrected, reject):
    print(f"{treatment}: p={pval:.4f}, corrected={pval_corr:.4f}, significant={rej}")
```

### 2. Overfitting

**Problem**: Model fits training data too closely, generalizes poorly.

**Signs**:
- Train R² >> Test R²
- Many insignificant variables included
- High variance in predictions

**Solutions**:
```python
# 1. Regularization (L1/L2)
from sklearn.linear_model import LassoCV
lasso = LassoCV(cv=5)
lasso.fit(X_train, y_train)

# 2. Feature selection based on domain knowledge
# Don't include every possible variable!
important_vars = ['minutes', 'rebounds', 'assists']  # Not all 50 stats

# 3. Cross-validation
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='r2')
print(f"CV R²: {scores.mean():.3f} (±{scores.std():.3f})")
```

### 3. Ignoring Multicollinearity

**Problem**: Highly correlated predictors inflate standard errors.

**Detection**:
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Calculate VIF
vif_data = pd.DataFrame()
vif_data['feature'] = X.columns
vif_data['VIF'] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]

print(vif_data.sort_values('VIF', ascending=False))

# Rule of thumb: VIF > 10 indicates multicollinearity
```

**Solutions**:
```python
# 1. Drop correlated variables
# If 'total_points' and 'ppg' both included, drop one

# 2. Use PCA
from sklearn.decomposition import PCA
pca = PCA(n_components=0.95)  # Retain 95% variance
X_pca = pca.fit_transform(X)

# 3. Use regularization (Ridge handles multicollinearity)
from sklearn.linear_model import RidgeCV
ridge = RidgeCV(alphas=[0.1, 1.0, 10.0])
ridge.fit(X, y)
```

### 4. Confusing Correlation with Causation

**Problem**: X and Y are correlated, but X doesn't cause Y.

**Example**: Ice cream sales and drowning deaths (both caused by hot weather).

**Solutions**:

1. **Use causal methods** (PSM, DiD, RDD, IV)
```python
# Propensity score matching
result = suite.causal_analysis(method='propensity_score_matching')
```

2. **Check for confounders**
```python
# Include potential confounders
suite = EconometricSuite(
    data=df,
    outcome_var='points',
    treatment_var='minutes',
    control_vars=['fatigue', 'opponent_strength', 'home_game']
)
```

3. **Domain knowledge**
- Always ask: "Could something else explain this relationship?"
- Draw causal diagrams (DAGs)
- Think about time order (cause must precede effect)

---

## Code Examples

### Full Workflow Example

```python
import pandas as pd
import numpy as np
from mcp_server.econometric_suite import EconometricSuite

# 1. Load and prepare data
df = pd.read_csv('player_stats.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['player', 'date'])

# 2. Exploratory analysis
print(df[['points', 'minutes', 'rebounds']].describe())

# 3. Simple model first
suite = EconometricSuite(
    data=df,
    outcome_var='points',
    treatment_var='minutes',
    control_vars=['rebounds', 'assists']
)

ols_result = suite.ols_analysis()
print(f"OLS R²: {ols_result.rsquared:.3f}")

# 4. Check assumptions
diagnostics = ols_result.diagnostics
if diagnostics['normality_pvalue'] < 0.05:
    print("⚠️ Residuals not normal, consider transformations")

# 5. Time series analysis
player_df = df[df['player'] == 'LeBron James']
suite_ts = EconometricSuite(
    data=player_df,
    outcome_var='points',
    time_var='date'
)

ts_result = suite_ts.time_series_analysis(
    method='arima',
    forecast_periods=10
)

# 6. Validate forecast
# Split last 10 games for validation
train = player_df.iloc[:-10]
test = player_df.iloc[-10:]

suite_train = EconometricSuite(data=train, outcome_var='points', time_var='date')
forecast_result = suite_train.time_series_analysis(method='arima', forecast_periods=10)

mae = np.mean(np.abs(forecast_result.forecast['forecast'] - test['points'].values))
print(f"Forecast MAE: {mae:.2f} points")

# 7. Causal analysis
suite_causal = EconometricSuite(
    data=df,
    outcome_var='points',
    treatment_var='new_coach',
    control_vars=['minutes', 'fatigue', 'opponent']
)

causal_result = suite_causal.causal_analysis(method='propensity_score_matching')
print(f"Coaching effect: {causal_result.ate:.2f} points (95% CI: {causal_result.ate_ci})")

# 8. Production: Save model
import joblib
joblib.dump(ts_result, 'lebron_forecast_model.pkl')

# 9. Production: API endpoint (FastAPI example above)
```

---

## Summary Checklist

### Before Running Analysis

- [ ] Data is clean (no unexpected NaNs or duplicates)
- [ ] Variables are properly typed (numeric vs categorical)
- [ ] Time series data is sorted by time
- [ ] Outliers have been investigated
- [ ] Sample size is adequate (n > 30 for most methods)

### During Analysis

- [ ] Started with simple method (OLS, t-test)
- [ ] Checked assumptions (residual plots, tests)
- [ ] Used appropriate method for data structure
- [ ] Included relevant control variables
- [ ] Reported confidence intervals, not just point estimates

### After Analysis

- [ ] Validated on holdout data (if predictive)
- [ ] Checked for multiple testing issues
- [ ] Interpreted results in domain context
- [ ] Assessed practical vs statistical significance
- [ ] Documented methods and assumptions

### For Production

- [ ] Added error handling and logging
- [ ] Implemented fallback strategies
- [ ] Optimized performance (caching, parallelization)
- [ ] Set up monitoring and alerts
- [ ] Wrote tests for critical paths

---

## Additional Resources

- [EconometricSuite API Documentation](../mcp_server/econometric_suite.py)
- [Tutorial Notebooks](../examples/)
- [Performance Benchmarking Report](../BAYESIAN_METHODS_PERFORMANCE_REPORT.md)
- [Option C Final Summary](../OPTION_C_FINAL_SUMMARY.md)

---

**Questions or Issues?**
Open an issue on GitHub or contact the development team.

**Last Updated**: November 1, 2025
**Version**: 1.0
