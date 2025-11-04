# Best Practices for NBA MCP Analytics

**Proven patterns and common pitfalls to avoid**

---

## Method Selection

### Use the Decision Tree

Before choosing a method, ask yourself:

```
1. What type of data do I have?
   ├─ Time-ordered observations → Time Series
   ├─ Entities × Time → Panel Data
   ├─ Time-to-event → Survival Analysis
   └─ Treatment/Control → Causal Inference

2. What question am I asking?
   ├─ "Will X continue?" → Forecasting (ARIMA, VAR)
   ├─ "Did Y cause Z?" → Causal Inference (PSM, IV, RDD)
   ├─ "When will event occur?" → Survival (Cox PH, Kaplan-Meier)
   └─ "How do groups differ?" → Panel (Fixed/Random Effects)
```

### Start Simple

```python
# ❌ BAD: Start with complex model
result = suite.time_series_analysis(
    method='arima',
    order=(5, 2, 5),  # Too complex!
    seasonal_order=(2, 1, 2, 12)
)

# ✅ GOOD: Start simple, increase complexity if needed
result = suite.time_series_analysis(method='arima', order='auto')
```

---

## Data Preparation

### 1. Check Data Quality First

```python
import pandas as pd
import numpy as np

# ✅ GOOD: Validate data before analysis
def validate_data(df, target_col):
    """Comprehensive data validation"""

    # Check for missing values
    missing_pct = df[target_col].isna().mean() * 100
    if missing_pct > 10:
        print(f"Warning: {missing_pct:.1f}% missing values in {target_col}")

    # Check for duplicates
    dups = df.duplicated().sum()
    if dups > 0:
        print(f"Warning: {dups} duplicate rows found")

    # Check data types
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise ValueError(f"{target_col} must be numeric")

    # Check for outliers (IQR method)
    Q1 = df[target_col].quantile(0.25)
    Q3 = df[target_col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((df[target_col] < Q1 - 3*IQR) | (df[target_col] > Q3 + 3*IQR)).sum()
    if outliers > 0:
        print(f"Warning: {outliers} potential outliers detected")

    return True

# Use it
data = pd.read_csv('player_stats.csv')
validate_data(data, 'points')
```

### 2. Handle Missing Data Properly

```python
# ❌ BAD: Drop all missing data
data_clean = data.dropna()  # May lose too much data!

# ✅ GOOD: Strategic imputation
from sklearn.impute import SimpleImputer

# For time series: forward fill
data['points'] = data['points'].ffill()

# For cross-sectional: mean/median imputation
imputer = SimpleImputer(strategy='median')
data[['points', 'assists']] = imputer.fit_transform(data[['points', 'assists']])

# Document your choice
print(f"Imputation: forward-fill for time series, median for cross-sectional")
```

### 3. Check Stationarity (Time Series)

```python
from statsmodels.tsa.stattools import adfuller, kpss

def check_stationarity(series, name='series'):
    """Test for stationarity using ADF and KPSS tests"""

    # ADF test (H0: non-stationary)
    adf_result = adfuller(series)
    print(f"\n{name} - ADF Test:")
    print(f"  Statistic: {adf_result[0]:.4f}")
    print(f"  p-value: {adf_result[1]:.4f}")
    is_stationary_adf = adf_result[1] < 0.05

    # KPSS test (H0: stationary)
    kpss_result = kpss(series, regression='ct')
    print(f"\n{name} - KPSS Test:")
    print(f"  Statistic: {kpss_result[0]:.4f}")
    print(f"  p-value: {kpss_result[1]:.4f}")
    is_stationary_kpss = kpss_result[1] > 0.05

    # Both tests should agree
    if is_stationary_adf and is_stationary_kpss:
        print(f"✓ {name} is stationary")
        return True, 0  # No differencing needed
    else:
        print(f"✗ {name} is non-stationary - try differencing")
        return False, 1  # Differencing recommended

# Use it
data = pd.read_csv('player_stats.csv')
is_stationary, d_order = check_stationarity(data['points'], 'Points')
```

---

## Time Series Analysis

### Diagnostic Checks

**Always check these 4 things:**

```python
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# 1. Residual autocorrelation
result = suite.time_series_analysis(method='arima', order=(1,1,1))
residuals = result.result.resid

lb_test = acorr_ljungbox(residuals, lags=20)
if (lb_test['lb_pvalue'] > 0.05).all():
    print("✓ Residuals are white noise")
else:
    print("✗ Residuals show autocorrelation - try different order")

# 2. Normality of residuals
from scipy.stats import jarque_bera
jb_stat, jb_pvalue = jarque_bera(residuals)
if jb_pvalue > 0.05:
    print("✓ Residuals are normally distributed")
else:
    print("⚠ Residuals not normal - forecasts may be biased")

# 3. Heteroskedasticity
from statsmodels.stats.diagnostic import het_arch
lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(residuals)
if lm_pvalue > 0.05:
    print("✓ No heteroskedasticity")
else:
    print("⚠ Heteroskedasticity detected - consider GARCH model")

# 4. Model selection (compare AICs)
models = []
for p in range(3):
    for q in range(3):
        try:
            res = suite.time_series_analysis(method='arima', order=(p,1,q))
            models.append({'order': (p,1,q), 'aic': res.aic})
        except:
            pass

best_model = min(models, key=lambda x: x['aic'])
print(f"Best model: ARIMA{best_model['order']} (AIC={best_model['aic']:.2f})")
```

### Common Pitfalls

**Pitfall 1: Using non-stationary data**

```python
# ❌ BAD: Fit ARIMA on trending data
data['points'] = data['points'].cumsum()  # Creates trend
result = suite.time_series_analysis(method='arima', order=(1,0,1))
# → Spurious regression!

# ✅ GOOD: Test and difference
from statsmodels.tsa.stattools import adfuller
if adfuller(data['points'])[1] > 0.05:
    data['points_diff'] = data['points'].diff().dropna()
    result = suite.time_series_analysis(
        method='arima',
        order=(1,1,1)  # d=1 for differencing
    )
```

**Pitfall 2: Overfitting**

```python
# ❌ BAD: Too many parameters
result = suite.time_series_analysis(method='arima', order=(10,1,10))
# → Overfits training data, poor forecasts

# ✅ GOOD: Use information criteria
result = suite.time_series_analysis(method='arima', order='auto')
# → Balances fit and complexity
```

---

## Causal Inference

### Check Balance in PSM

```python
# After matching, ALWAYS check balance
result = suite.causal_analysis(
    method='psm',
    covariates=['experience', 'position', 'age'],
    caliper=0.1
)

balance = result.result.balance_statistics

# Rule of thumb: SMD < 0.1 after matching
if (balance['smd_after'] < 0.1).all():
    print("✓ Good balance achieved")
else:
    poor_balance = balance[balance['smd_after'] >= 0.1]
    print(f"✗ Poor balance on: {list(poor_balance.index)}")
    print("Try: Tighter caliper or different covariates")
```

### IV Strength Check

```python
# For Instrumental Variables, ALWAYS check instrument strength
result = suite.causal_analysis(
    method='iv',
    instruments=['draft_position']
)

# Rule of thumb: F-stat > 10
f_stat = result.result.first_stage_f_stat
if f_stat > 10:
    print(f"✓ Strong instrument (F={f_stat:.2f})")
else:
    print(f"✗ Weak instrument (F={f_stat:.2f})")
    print("⚠ Estimates may be biased - find better instrument")
```

### Sensitivity Analysis

```python
# ALWAYS run sensitivity analysis for observational studies
result_psm = suite.causal_analysis(
    method='psm',
    covariates=['experience', 'position']
)

# Rosenbaum bounds
result_sens = suite.causal_analysis(
    method='sensitivity',
    effect_estimate=result_psm.result.att,
    se_estimate=result_psm.result.std_error
)

# Interpret: How strong must confounding be to overturn result?
print(f"Gamma at p=0.05: {result_sens.result.critical_value:.2f}")
# If Gamma > 2: Results robust to moderate confounding
# If Gamma < 1.5: Results fragile
```

---

## Survival Analysis

### Test Proportional Hazards Assumption

```python
from lifelines.statistics import proportional_hazard_test

result = suite.survival_analysis(
    method='cox',
    covariates=['draft_pick', 'injuries']
)

# Test PH assumption
ph_test = proportional_hazard_test(
    result.result,
    data,
    time_transform='rank'
)

if (ph_test.summary['p'] > 0.05).all():
    print("✓ Proportional hazards assumption met")
else:
    violated = ph_test.summary[ph_test.summary['p'] <= 0.05]
    print(f"✗ PH violated for: {list(violated.index)}")
    print("Try: Stratify by this variable or use time-varying model")
```

### Censoring Patterns

```python
# Check censoring rate
censoring_rate = 1 - data['retired'].mean()
print(f"Censoring rate: {censoring_rate:.1%}")

if censoring_rate > 0.5:
    print("⚠ High censoring - results may be unreliable")
    print("Consider: Longer follow-up or parametric models")
elif censoring_rate < 0.1:
    print("⚠ Low censoring - could use simpler methods")
```

---

## Panel Data

### Hausman Test (FE vs RE)

```python
# ALWAYS run Hausman test to choose between FE and RE
result_fe = suite.panel_analysis(
    method='fixed_effects',
    covariates=['minutes', 'usage_rate']
)

result_re = suite.panel_analysis(
    method='random_effects',
    covariates=['minutes', 'usage_rate']
)

# Compute Hausman statistic (manual)
from scipy.stats import chi2
diff = result_fe.result.params - result_re.result.params
var_diff = result_fe.result.cov_params() - result_re.result.cov_params()
hausman_stat = diff.T @ np.linalg.inv(var_diff) @ diff
p_value = 1 - chi2.cdf(hausman_stat, df=len(diff))

if p_value < 0.05:
    print("Use Fixed Effects (FE)")
else:
    print("Use Random Effects (RE)")
```

### Cluster Standard Errors

```python
# For panel data, ALWAYS cluster SEs by entity
result = suite.panel_analysis(
    method='fixed_effects',
    covariates=['minutes', 'usage_rate'],
    cluster_entity=True  # Cluster by player_id
)
```

---

## Performance Optimization

### 1. Data Sampling for Exploration

```python
# For large datasets (>100K rows), sample for exploration
data_large = pd.read_csv('all_games.csv')  # 500K rows

# Quick exploration
data_sample = data_large.sample(n=10000, random_state=42)
suite_sample = EconometricSuite(data=data_sample, target='points')
quick_result = suite_sample.analyze(method='auto')

# Use insights on full data
suite_full = EconometricSuite(data=data_large, target='points')
final_result = suite_full.time_series_analysis(
    method=quick_result.method_used,
    order=quick_result.result.arima_order
)
```

### 2. Parallel Model Comparison

```python
from joblib import Parallel, delayed

def fit_model(order):
    suite = EconometricSuite(data=data, target='points', time_col='date')
    result = suite.time_series_analysis(method='arima', order=order)
    return {'order': order, 'aic': result.aic}

# Compare multiple orders in parallel
orders = [(p,1,q) for p in range(3) for q in range(3)]
results = Parallel(n_jobs=-1)(
    delayed(fit_model)(order) for order in orders
)

best = min(results, key=lambda x: x['aic'])
print(f"Best order: {best['order']} (AIC={best['aic']:.2f})")
```

### 3. Caching Expensive Computations

```python
from functools import lru_cache
import pickle

@lru_cache(maxsize=128)
def cached_psm_analysis(data_hash, caliper):
    """Cache PSM results - expensive operation"""
    data = load_data(data_hash)
    suite = EconometricSuite(data=data, treatment_col='treatment', target='outcome')
    return suite.causal_analysis(method='psm', caliper=caliper)

# Persist to disk for longer sessions
def save_result(result, filename):
    with open(filename, 'wb') as f:
        pickle.dump(result, f)

def load_result(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
```

---

## Error Handling

### Defensive Programming

```python
from mcp_server.exceptions import *

def safe_analysis(data, method='arima'):
    """Robust analysis with graceful degradation"""

    try:
        # Primary analysis
        suite = EconometricSuite(data=data, target='points', time_col='date')
        result = suite.time_series_analysis(method=method, order='auto')
        return result, None

    except InsufficientDataError as e:
        print(f"Insufficient data: {e.message}")
        # Fallback: Simple moving average
        forecast = data['points'].rolling(window=5).mean().iloc[-1]
        return None, forecast

    except ModelFitError as e:
        print(f"Model fit failed: {e.reason}")
        # Fallback: Simpler model
        result = suite.time_series_analysis(method='arima', order=(1,0,1))
        return result, None

    except InvalidParameterError as e:
        print(f"Invalid parameter: {e.message}")
        # Fallback: Default parameters
        result = suite.time_series_analysis(method='arima', order=(1,1,1))
        return result, None

# Use it
result, fallback = safe_analysis(data)
if result:
    print(f"Model AIC: {result.aic}")
else:
    print(f"Using fallback forecast: {fallback}")
```

---

## Reporting Results

### Statistical vs Practical Significance

```python
# ❌ BAD: Only report p-value
print(f"p-value: {result.result.p_value}")  # p=0.001

# ✅ GOOD: Report effect size and confidence interval
print(f"Treatment effect: {result.result.att:.2f} points")
print(f"95% CI: [{result.result.confidence_interval[0]:.2f}, "
      f"{result.result.confidence_interval[1]:.2f}]")
print(f"p-value: {result.result.p_value:.3f}")

# Interpret practical significance
if abs(result.result.att) > 2.0:  # Domain-specific threshold
    print("✓ Practically significant (>2 points per game)")
else:
    print("○ Statistically significant but small effect")
```

### Complete Reporting Template

```markdown
## Analysis Results

**Research Question:** Does home court advantage affect win probability?

**Data:** 1,230 NBA games (2022-2023 season)

**Method:** Propensity Score Matching (PSM)
- Treatment: Home game (vs. away)
- Outcome: Win probability
- Covariates: Team strength, opponent strength, rest days, injuries

**Diagnostics:**
- Balance check: All SMD < 0.1 ✓
- Common support: 95% of observations ✓
- Matched pairs: 578 (94% match rate)

**Results:**
- ATT = 0.08 (95% CI: [0.04, 0.12])
- Standard Error = 0.02
- p-value < 0.001

**Interpretation:**
Home teams win 8% more often than away teams, holding team quality constant. This effect is both statistically significant (p<0.001) and practically meaningful (~4 additional wins per 50-game home schedule).

**Robustness:**
- Kernel matching: ATT = 0.09 (consistent)
- Radius matching (r=0.05): ATT = 0.07 (consistent)
- Rosenbaum bounds: Gamma = 2.1 (robust to moderate confounding)

**Limitations:**
- Observational study - cannot rule out all confounding
- Assumes no spillover effects between games
- Results specific to 2022-2023 season

**Conclusion:**
Strong evidence for home court advantage effect of ~8 percentage points.
```

---

## Testing & Validation

### Cross-Validation for Time Series

```python
from sklearn.model_selection import TimeSeriesSplit

# Use time-series CV (NOT random CV!)
tscv = TimeSeriesSplit(n_splits=5)
maes = []

for train_idx, test_idx in tscv.split(data):
    train = data.iloc[train_idx]
    test = data.iloc[test_idx]

    suite = EconometricSuite(data=train, target='points', time_col='date')
    result = suite.time_series_analysis(method='arima', order='auto')

    forecast = result.result.forecast(steps=len(test))
    mae = np.abs(forecast - test['points']).mean()
    maes.append(mae)

print(f"Cross-validated MAE: {np.mean(maes):.2f} ± {np.std(maes):.2f}")
```

---

**Last Updated:** 2025-11-04
**Version:** Phase 1 Week 4