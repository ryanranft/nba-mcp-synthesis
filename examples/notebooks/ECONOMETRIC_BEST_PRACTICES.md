# Econometric Analysis Best Practices Guide

**Purpose**: Method selection, interpretation, and troubleshooting for NBA analytics
**Audience**: Data scientists, analysts, and developers using the econometric framework
**Last Updated**: October 31, 2025

---

## Table of Contents

1. [Method Selection Decision Tree](#method-selection-decision-tree)
2. [Interpretation Guidelines](#interpretation-guidelines)
3. [Common Pitfalls](#common-pitfalls)
4. [Troubleshooting](#troubleshooting)
5. [Production Deployment](#production-deployment)
6. [Data Requirements](#data-requirements)
7. [Statistical Power](#statistical-power)

---

## Method Selection Decision Tree

### Step 1: Identify Your Data Structure

**Time Series** (observations over time for one or few units)
- Single player's game-by-game stats
- Team performance across seasons
- League-wide trends over years

**Panel Data** (multiple entities observed over time)
- All players across multiple seasons
- Team stats for 30 teams over 10 years
- Position-specific performance trends

**Cross-Section** (one time point, many units)
- Draft class analysis (single year)
- Single season player comparison
- Snapshot of league at one moment

**Survival/Duration Data** (time until event occurs)
- Career length analysis
- Time to injury
- Contract renewal timing

---

### Step 2: Identify Your Question Type

#### **Prediction Questions** → Time Series or ML
- "What will LeBron score next game?"
- "How many wins will Lakers have?"
- "Forecast league-wide scoring trends"

**Methods**:
- ARIMA for short-term forecasts
- Kalman Filter for real-time tracking
- Structural Time Series for decomposition
- Ensemble methods for accuracy

---

#### **Causal Questions** → Causal Inference
- "Does coaching change improve performance?"
- "Effect of injury on career trajectory?"
- "Impact of new training program?"

**Methods**:
- Propensity Score Matching (observed confounders)
- Instrumental Variables (unobserved confounders)
- Regression Discontinuity (cutoff rules)
- Synthetic Control (single treated unit)
- Difference-in-Differences (pre/post comparison)

---

#### **Risk/Duration Questions** → Survival Analysis
- "How long will player's career last?"
- "Time until re-injury?"
- "Factors affecting retirement timing?"

**Methods**:
- Kaplan-Meier (non-parametric survival curves)
- Cox Proportional Hazards (covariate effects)
- Parametric Models (Weibull, Log-Normal)
- Competing Risks (multiple failure types)

---

#### **Relationship Questions** → Regression/Panel Data
- "Association between minutes and performance?"
- "Team effects on player stats?"
- "Position-specific salary determinants?"

**Methods**:
- Fixed Effects (control for entity heterogeneity)
- Random Effects (random variation across entities)
- Pooled OLS (assuming no entity effects)
- First Difference (eliminate fixed effects)

---

#### **Regime Detection Questions** → Advanced Time Series
- "When did player enter decline phase?"
- "Detect hot streaks and slumps?"
- "Identify market regime shifts?"

**Methods**:
- Markov Switching (discrete regimes)
- Structural Break Tests (detect changepoints)
- Kalman Filter (smooth state transitions)

---

### Step 3: Method Selection Matrix

| Data Structure | Question Type | Recommended Method | Alternative |
|----------------|---------------|-------------------|-------------|
| Time Series | Forecast | ARIMA | Prophet, Exponential Smoothing |
| Time Series | Regime Change | Markov Switching | Structural Breaks |
| Time Series | Real-Time | Kalman Filter | EWMA |
| Panel Data | Fixed Effects? | Hausman Test → FE/RE | First Difference |
| Panel Data | Dynamics | GMM (Arellano-Bond) | System GMM |
| Cross-Section | Causal | PSM, IV | RDD if cutoff exists |
| Survival | Covariate Effects | Cox PH | Parametric (AFT) |
| Survival | Non-Parametric | Kaplan-Meier | Life Tables |

---

## Interpretation Guidelines

### Coefficients vs. Effects

**Linear Regression Coefficient**:
```
β = 0.5 → One unit increase in X → 0.5 unit increase in Y
```
**Example**: β = 0.5 for minutes → +1 minute → +0.5 points

**Interpretation**: Direct, linear relationship

---

**Hazard Ratio (Survival Analysis)**:
```
HR = 1.5 → 50% higher instantaneous risk of event
HR = 0.7 → 30% lower risk
HR = 1.0 → No effect
```
**Example**: HR = 1.45 for injury → 45% higher retirement risk

**Interpretation**: Multiplicative effect on hazard rate

---

**Treatment Effect (Causal Inference)**:
```
ATE = 3.0 → Treatment increases outcome by 3 units on average
```
**Example**: ATE = 3 wins → Coaching change adds 3 wins

**Interpretation**: Average causal effect for population

---

**Odds Ratio (Logistic Regression)**:
```
OR = 2.0 → 2x higher odds of event
OR = 0.5 → 50% lower odds
```
**Example**: OR = 2.0 for draft round 1 → 2x odds of All-Star

**Interpretation**: Multiplicative effect on odds (not probability!)

---

### Statistical vs. Practical Significance

**Statistical Significance** (p < 0.05):
- Indicates effect is unlikely due to chance
- **Does NOT mean effect is large or important**
- Can detect tiny effects with large samples

**Practical Significance**:
- Effect size matters for decisions
- Consider: Is the effect big enough to act on?

**Example**:
```python
# Statistically significant but tiny effect
coefficient = 0.001
p_value = 0.001  # Highly significant!

# But...
effect_size = 0.001 * 10  # +0.01 points per game
# Too small to matter in practice
```

**Rule of Thumb**:
- **Significant + Large Effect** → Act on it
- **Significant + Small Effect** → Probably ignore
- **Not Significant** → No evidence of effect (doesn't prove no effect!)

---

### Confidence Intervals

**95% CI**: We're 95% confident true effect is in this range

**Interpretation**:
```
ATE = 3.0, 95% CI [1.5, 4.5]
```
- Best estimate: +3 wins
- Plausible range: +1.5 to +4.5 wins
- Lower bound still positive → confident effect is real

**Wide CI** → Uncertain estimate (need more data)
**Narrow CI** → Precise estimate (sufficient data)

**Action Rule**:
- If CI includes 0 → No evidence of effect
- If CI excludes 0 → Statistically significant
- If CI is narrow → Precise estimate

---

### Effect Size Guidelines (Cohen's d)

| Effect Size | Cohen's d | Interpretation |
|-------------|-----------|----------------|
| Trivial | < 0.2 | Negligible |
| Small | 0.2 - 0.5 | Noticeable |
| Medium | 0.5 - 0.8 | Meaningful |
| Large | > 0.8 | Substantial |

**For NBA Analytics**:
- +0.5 PPG → Small but meaningful
- +3 wins → Medium effect (practical significance)
- +10 wins → Large effect (transformative)

---

## Common Pitfalls

### 1. Non-Stationarity in Time Series

**Problem**: Mean/variance changes over time → ARIMA assumptions violated

**Symptoms**:
- Predictions diverge
- Residuals show patterns
- ADF test fails (p > 0.05)

**Solutions**:
```python
# Test for stationarity
from statsmodels.tsa.stattools import adfuller
result = adfuller(series)
if result[1] > 0.05:
    # Non-stationary! Apply differencing
    series_diff = series.diff().dropna()

# Or use seasonal decomposition
from statsmodels.tsa.seasonal import seasonal_decompose
decomp = seasonal_decompose(series, period=82)
detrended = series - decomp.trend
```

**Prevention**:
- Always test stationarity before ARIMA
- Plot data to visually inspect trends
- Use appropriate differencing order (d parameter)

---

### 2. Endogeneity in Causal Inference

**Problem**: Treatment correlated with unobserved factors → biased estimates

**Example**:
- Bad teams fire coaches → coaching change correlated with poor performance
- Comparing winners vs. losers biased

**Symptoms**:
- Results change dramatically with different control variables
- Implausibly large effects
- Fails placebo tests

**Solutions**:
```python
# Use causal methods, not naive regression
# Option 1: PSM (control for observed confounders)
psm_result = analyzer.propensity_score_matching(...)

# Option 2: IV (control for unobserved confounders)
iv_result = analyzer.instrumental_variables(instrument='...')

# Option 3: RDD (exploit cutoff)
rdd_result = analyzer.regression_discontinuity(cutoff=41)
```

**Prevention**:
- Never claim causality from correlation
- Use causal methods (PSM, IV, RDD)
- Run sensitivity analysis
- Check covariate balance

---

### 3. Proportional Hazards Assumption Violations

**Problem**: Cox model assumes constant hazard ratios over time

**Symptoms**:
- Schoenfeld residuals show patterns
- Test p-value < 0.05

**Solutions**:
```python
# Test assumption
ph_test = analyzer.test_proportional_hazards()

# If violated:
# Option 1: Stratified Cox model
strat_result = analyzer.cox_ph(strata='position')

# Option 2: Time-varying coefficients
time_varying = analyzer.cox_ph(time_varying='injury')

# Option 3: Parametric model (no PH assumption)
weibull = analyzer.parametric_survival(distribution='weibull')
```

**Prevention**:
- Always test PH assumption
- Stratify by variables that violate
- Consider parametric alternatives

---

### 4. Convergence Issues in Complex Models

**Problem**: Bayesian MCMC, GMM, or MLE won't converge

**Symptoms**:
- Warnings about convergence
- Rhat > 1.1 (Bayesian)
- Very wide confidence intervals
- Unrealistic parameter estimates

**Solutions**:
```python
# For Bayesian:
# Increase iterations
result = analyzer.sample_posterior(draws=5000, tune=2000)

# Better priors
priors = {'mu': Normal(0, 10), 'sigma': HalfNormal(5)}

# For GMM:
# Reduce instruments
result = analyzer.difference_gmm(max_lags=2, collapse=True)

# For MLE:
# Better starting values
result = analyzer.fit_model(start_params=[0.1, 0.5, ...])
```

**Prevention**:
- Start with simple models
- Check for multicollinearity
- Ensure sufficient data
- Use informative priors (Bayesian)

---

### 5. Sample Size Issues

**Minimum Sample Sizes** (Rules of Thumb):

| Method | Minimum N | Recommended N |
|--------|-----------|---------------|
| ARIMA | 50 | 100+ |
| Cox PH | 50 events | 100+ events |
| PSM | 100 (50 treated, 50 control) | 200+ |
| Panel FE | 30 entities, 5 time periods | 50+ entities, 10+ periods |
| GMM | 100 | 200+ |
| Bayesian | 50 | 100+ |

**Symptoms of Insufficient Data**:
- Very wide confidence intervals
- Model won't converge
- Unstable estimates across samples

**Solutions**:
```python
# Check sample size
print(f"N = {len(data)}")
print(f"Events = {data['event'].sum()}")

# If too small:
# - Pool data across seasons
# - Use simpler models
# - Bayesian methods with priors
# - Don't over-interpret results
```

---

### 6. Multiple Testing Problem

**Problem**: Testing many hypotheses → false discoveries

**Example**:
```python
# Testing 20 predictors
# At α=0.05, expect 1 false positive even if all null
```

**Solutions**:
```python
# Bonferroni correction
alpha_corrected = 0.05 / n_tests

# False Discovery Rate (FDR)
from statsmodels.stats.multitest import fdrcorrection
reject, pvals_corrected = fdrcorrection(pvals, alpha=0.05)

# Or: Use regularization (LASSO)
from sklearn.linear_model import LassoCV
lasso = LassoCV(cv=5)
lasso.fit(X, y)
# Coefficients shrunk to 0 for unimportant variables
```

**Prevention**:
- Pre-specify hypotheses
- Use domain knowledge
- Apply corrections when testing many variables

---

## Troubleshooting

### Model Won't Converge

**Checklist**:

1. **Check for multicollinearity**
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif = pd.DataFrame()
vif['Variable'] = X.columns
vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif)

# VIF > 10 → serious multicollinearity
# Solution: Remove correlated variables
```

2. **Scale variables**
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

3. **Check for perfect separation** (logistic regression)
```python
# If any predictor perfectly predicts outcome → separation
# Solution: Remove that variable or use penalized regression
```

4. **Simplify model**
```python
# Start with simple model, add complexity gradually
# Model 1: outcome ~ key_variable
# Model 2: outcome ~ key_variable + control1
# Model 3: outcome ~ key_variable + control1 + control2
```

---

### Tests Failing

**ADF Test Fails (Non-Stationary)**:
```python
# Try differencing
df['value_diff'] = df['value'].diff()

# Or seasonal differencing
df['value_seasonal_diff'] = df['value'].diff(82)  # 82-game season
```

**Hausman Test Fails**:
```python
# Reject RE, use FE instead
result = analyzer.fixed_effects(...)
```

**Weak Instrument (F < 10)**:
```python
# Find stronger instrument
# Or use reduced form instead of IV
```

---

### Unexpected Results

**Checklist**:

1. **Plot the data**
```python
plt.scatter(X, y)
plt.show()
# Visual inspection catches obvious issues
```

2. **Check for outliers**
```python
# Z-score method
from scipy import stats
z_scores = np.abs(stats.zscore(df))
outliers = (z_scores > 3).any(axis=1)
print(f"Outliers: {outliers.sum()}")
```

3. **Validate data quality**
```python
# Missing values
print(df.isnull().sum())

# Duplicates
print(df.duplicated().sum())

# Invalid values (negative wins, etc.)
assert (df['wins'] >= 0).all()
```

4. **Cross-validate**
```python
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5)
print(f"CV Score: {scores.mean():.3f} ± {scores.std():.3f}")
```

---

### Performance Issues

**Slow Execution**:

1. **Profile code**
```python
import cProfile
cProfile.run('analyzer.fit_model()')
```

2. **Optimize hot spots**
```python
# Use vectorized operations
# BAD
for i in range(len(df)):
    df.loc[i, 'new_col'] = df.loc[i, 'col1'] * 2

# GOOD
df['new_col'] = df['col1'] * 2
```

3. **Parallel processing**
```python
from joblib import Parallel, delayed

results = Parallel(n_jobs=4)(
    delayed(fit_model)(player) for player in players
)
```

4. **Sample for exploration**
```python
# Use 10% sample for model development
df_sample = df.sample(frac=0.1, random_state=42)

# Fit on full data after finalizing
```

---

## Production Deployment

### Automated Retraining

**Schedule**:
- **Weekly**: Real-time models (Kalman, ARIMA forecasts)
- **Monthly**: Player performance models
- **Quarterly**: Causal effect estimates
- **Annually**: Survival models, long-term trends

**Implementation**:
```python
# cron job or Airflow DAG
def retrain_player_model(player_id):
    # Load latest data
    data = fetch_player_data(player_id, last_n_games=100)

    # Fit model
    analyzer = TimeSeriesAnalyzer(data, target='ppg')
    model = analyzer.fit_arima(order=(1,1,1))

    # Save model
    model.save(f'models/{player_id}_latest.pkl')

    # Log metrics
    mlflow.log_metric('aic', model.aic)

    return model

# Run daily at 2 AM
schedule.every().day.at("02:00").do(retrain_all_models)
```

---

### Model Monitoring

**Key Metrics to Track**:

1. **Prediction Accuracy**
```python
# Track MAE over time
mae = np.abs(y_true - y_pred).mean()
mlflow.log_metric('mae', mae, step=week)

# Alert if degrades
if mae > threshold:
    send_alert("Model accuracy degraded!")
```

2. **Data Drift**
```python
# Monitor input distributions
current_mean = X_new.mean()
training_mean = X_train.mean()
drift = abs(current_mean - training_mean) / training_mean

if drift > 0.20:  # 20% shift
    send_alert("Data drift detected!")
```

3. **Concept Drift**
```python
# Relationship between X and y changed
current_r2 = model.score(X_recent, y_recent)
if current_r2 < baseline_r2 - 0.10:
    trigger_retraining()
```

---

### A/B Testing Framework

**Comparing Model Versions**:
```python
def ab_test_models(model_a, model_b, test_data, metric='mae'):
    # Predictions
    preds_a = model_a.predict(test_data)
    preds_b = model_b.predict(test_data)

    # Calculate metric
    score_a = calculate_metric(test_data.y, preds_a, metric)
    score_b = calculate_metric(test_data.y, preds_b, metric)

    # Statistical test
    from scipy import stats
    t_stat, p_value = stats.ttest_rel(
        abs(test_data.y - preds_a),
        abs(test_data.y - preds_b)
    )

    # Decision
    if p_value < 0.05 and score_b < score_a:
        return "Deploy Model B"
    else:
        return "Keep Model A"
```

---

### Rollback Procedures

**Version Control for Models**:
```python
import mlflow

# Save model with version
with mlflow.start_run():
    mlflow.sklearn.log_model(model, "arima_model")
    mlflow.log_param("order", (1,1,1))
    mlflow.log_metric("aic", model.aic)
    version = mlflow.active_run().info.run_id

# Rollback if needed
def rollback_to_version(version_id):
    model = mlflow.sklearn.load_model(f"runs:/{version_id}/arima_model")
    deploy_model(model)
```

---

## Data Requirements

### Minimum Data Quality Standards

**Time Series**:
- ✅ At least 50 observations
- ✅ Regular time intervals (no large gaps)
- ✅ < 10% missing values
- ✅ Outliers identified and handled

**Panel Data**:
- ✅ Balanced panels preferred (all entities, all times)
- ✅ At least 30 entities
- ✅ At least 5 time periods per entity
- ✅ Entity and time identifiers clean

**Survival Data**:
- ✅ At least 50 observations
- ✅ At least 10 events (not censored)
- ✅ Event time > 0 for all observations
- ✅ No negative durations

**Causal Inference**:
- ✅ Sufficient overlap in propensity scores
- ✅ Balanced covariates after matching
- ✅ No perfect predictors of treatment
- ✅ At least 50 treated, 50 control

---

## Statistical Power

### Sample Size Calculations

**For detecting effect size d with 80% power**:

| Effect Size (Cohen's d) | Required N per Group |
|------------------------|----------------------|
| 0.2 (small) | 393 |
| 0.5 (medium) | 64 |
| 0.8 (large) | 26 |

**Example**:
```python
from statsmodels.stats.power import TTestIndPower

power_analysis = TTestIndPower()
n = power_analysis.solve_power(
    effect_size=0.5,  # Medium effect
    alpha=0.05,
    power=0.80,
    alternative='two-sided'
)
print(f"Need {n:.0f} observations per group")
```

---

## Quick Reference

### Method Cheat Sheet

| Question | Method | Key Assumption |
|----------|--------|----------------|
| Future values? | ARIMA | Stationarity |
| Treatment effect? | PSM/IV/RDD | No hidden confounding (PSM) |
| Risk factors? | Cox PH | Proportional hazards |
| Entity effects? | FE/RE | Exogeneity (RE) |
| Regime change? | Markov Switching | Discrete states |

### Diagnostic Checklist

Before reporting results:
- [ ] Sample size adequate?
- [ ] Assumptions tested and met?
- [ ] Model diagnostics clean?
- [ ] Cross-validation performed?
- [ ] Results robust to specification?
- [ ] Effect size meaningful?
- [ ] Confidence intervals reported?
- [ ] Limitations acknowledged?

---

## Resources

**Statistical Methods**:
- Wooldridge - Econometric Analysis of Cross Section and Panel Data
- Greene - Econometric Analysis
- Hamilton - Time Series Analysis
- Cox & Oakes - Analysis of Survival Data

**Python Libraries**:
- statsmodels: Time series, regression, survival
- linearmodels: Panel data, IV
- lifelines: Survival analysis
- causalml: Causal inference

**NBA MCP Documentation**:
- [Time Series Guide](../../docs/advanced_analytics/TIME_SERIES.md)
- [Survival Analysis](../../docs/advanced_analytics/SURVIVAL_ANALYSIS.md)
- [Causal Inference](../../docs/advanced_analytics/CAUSAL_INFERENCE.md)
- [Panel Data Methods](../../docs/advanced_analytics/PANEL_DATA.md)

---

**Version**: 1.0
**Last Updated**: October 31, 2025
**Feedback**: Report issues or suggestions to the development team
