# Causal Inference Methods for NBA Analytics

**Module:** `mcp_server.causal_inference`
**Author:** Agent 8 Module 4A
**Date:** October 2025
**Status:** Production Ready

---

## Overview

The Causal Inference module provides research-grade methods for answering "what-if" questions in NBA analytics. Unlike correlational analysis, these methods aim to identify **causal effects** of interventions, policies, or treatments on outcomes.

### Why Causal Inference?

Correlation ≠ Causation. Observational NBA data is riddled with confounding factors:
- **Selection bias**: Better players get more playing time
- **Reverse causality**: Does coaching improve performance, or do better teams hire better coaches?
- **Omitted variables**: Unobserved factors (motivation, chemistry) affect both treatment and outcome

Causal inference methods address these challenges through rigorous identification strategies.

### Key Features

- **Instrumental Variables (IV/2SLS)**: Address endogeneity with exogenous instruments
- **Regression Discontinuity (RDD)**: Exploit threshold-based treatment assignment
- **Propensity Score Matching (PSM)**: Match treated/control units on observables
- **Synthetic Control**: Create counterfactual from donor pool
- **Sensitivity Analysis**: Assess robustness to unobserved confounding

---

## Quick Start

### Example 1: IV - Coaching Change Impact on Wins

```python
import pandas as pd
from mcp_server.causal_inference import CausalInferenceAnalyzer

# Load team-season data
df = pd.DataFrame({
    'team_id': ['LAL', 'GSW', 'BOS', ...],
    'season': [2023, 2023, 2023, ...],
    'wins': [52, 44, 57, ...],
    'coaching_change': [1, 0, 1, ...],  # Treatment
    'coach_retirement': [1, 0, 0, ...],  # Instrument (exogenous)
    'team_salary': [150M, 180M, 140M, ...],
    'avg_age': [27.3, 25.8, 28.1, ...]
})

# Initialize analyzer
analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='coaching_change',
    outcome_col='wins',
    covariates=['team_salary', 'avg_age']
)

# Estimate causal effect using IV
# (coach retirement is exogenous, affects coaching change, not directly wins)
result = analyzer.instrumental_variables(
    instruments='coach_retirement',
    robust=True
)

print(f"Causal effect: {result.treatment_effect:.2f} wins")
print(f"95% CI: [{result.confidence_interval[0]:.2f}, {result.confidence_interval[1]:.2f}]")
print(f"First-stage F-stat: {result.first_stage_f_stat:.2f}")

# Check for weak instruments
if result.weak_instrument_test['is_weak']:
    print("WARNING: Weak instruments detected!")
```

**Output:**
```
Causal effect: 8.50 wins
95% CI: [3.20, 13.80]
First-stage F-stat: 35.20
```

---

### Example 2: RDD - Draft Position Effect on Career Success

```python
from mcp_server.causal_inference import CausalInferenceAnalyzer

# Load draft data
df = pd.DataFrame({
    'player_name': ['LeBron', 'Darko', 'Carmelo', ...],
    'draft_pick': [1, 2, 3, ..., 60],
    'career_win_shares': [250, 15, 120, ...],
    'lottery_pick': [1, 1, 1, ..., 0]  # Treatment (picks 1-14)
})

analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='lottery_pick',
    outcome_col='career_win_shares'
)

# RDD at cutoff = 14.5 (lottery vs non-lottery)
result = analyzer.regression_discontinuity(
    running_var='draft_pick',
    cutoff=14.5,
    bandwidth=None,  # Auto-select optimal bandwidth
    polynomial_order=1
)

print(f"Lottery effect: {result.treatment_effect:.2f} win shares")
print(f"Bandwidth: {result.bandwidth:.2f}")
print(f"n_left={result.n_left}, n_right={result.n_right}")

# Check continuity (no manipulation of draft position)
print(f"McCrary test p-value: {result.continuity_test['p_value']:.3f}")
```

---

### Example 3: PSM - Player Development Program Evaluation

```python
from mcp_server.causal_inference import CausalInferenceAnalyzer

# Load player data
df = pd.DataFrame({
    'player_id': [1, 2, 3, ...],
    'attended_program': [1, 0, 1, ...],  # Treatment
    'improvement': [5.2, 1.3, 6.8, ...],  # Outcome (PPG increase)
    'age': [22, 25, 21, ...],
    'experience': [2, 5, 1, ...],
    'draft_position': [15, 45, 8, ...],
    'baseline_ppg': [8.5, 12.3, 6.2, ...]
})

analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='attended_program',
    outcome_col='improvement',
    covariates=['age', 'experience', 'draft_position', 'baseline_ppg']
)

# Match treated players to similar controls
result = analyzer.propensity_score_matching(
    method='nearest',
    n_neighbors=3,
    caliper=0.1  # Max propensity score distance
)

print(f"Average Treatment Effect (ATE): {result.ate:.2f} PPG")
print(f"ATT (on treated): {result.att:.2f} PPG")
print(f"Matched: {result.n_matched}, Unmatched: {result.n_unmatched}")

# Check covariate balance
print("\nBalance Statistics:")
print(result.balance_statistics)
```

---

### Example 4: Synthetic Control - New Coach Impact on Lakers

```python
from mcp_server.causal_inference import CausalInferenceAnalyzer

# Load team-season panel data
df = pd.DataFrame({
    'team': ['LAL', 'LAL', 'GSW', 'GSW', 'BOS', 'BOS', ...],
    'season': [2018, 2019, 2018, 2019, 2018, 2019, ...],
    'wins': [35, 52, 58, 57, 55, 49, ...],
    'new_coach': [0, 1, 0, 0, 0, 0, ...]  # Lakers hire new coach in 2019
})

analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='new_coach',
    outcome_col='wins',
    entity_col='team',
    time_col='season'
)

# Create synthetic Lakers from other teams
result = analyzer.synthetic_control(
    treated_unit='LAL',
    outcome_periods=list(range(2015, 2024)),
    treatment_period=2019,  # New coach hired
    n_placebo=15  # Placebo inference
)

print(f"Average treatment effect: {result.average_effect:.2f} wins")
print(f"P-value (placebo): {result.p_value:.3f}")
print(f"Pre-treatment RMSE: {result.pre_treatment_fit:.2f}")

print("\nDonor weights:")
print(result.weights[result.weights > 0.05])
```

---

## API Reference

### CausalInferenceAnalyzer

Main class for causal inference analysis.

#### `__init__(data, treatment_col, outcome_col, covariates=None, entity_col=None, time_col=None, mlflow_experiment=None)`

Initialize causal inference analyzer.

**Parameters:**
- `data` (pd.DataFrame): Input data
- `treatment_col` (str): Treatment variable name
- `outcome_col` (str): Outcome variable name
- `covariates` (List[str], optional): Covariate names for adjustment
- `entity_col` (str, optional): Entity identifier for panel data
- `time_col` (str, optional): Time variable for panel data
- `mlflow_experiment` (str, optional): MLflow experiment name

---

### Instrumental Variables

#### `instrumental_variables(instruments, formula=None, robust=True, entity_effects=False)`

Estimate treatment effect using 2SLS instrumental variables.

**When to use:**
- Treatment is endogenous (confounded by unobservables)
- Have valid instrument: (1) correlated with treatment, (2) affects outcome only through treatment

**Parameters:**
- `instruments` (str or List[str]): Instrumental variable(s)
- `formula` (str, optional): Regression formula
- `robust` (bool): Use robust standard errors
- `entity_effects` (bool): Include entity fixed effects (panel IV)

**Returns:**
- `IVResult`: Contains treatment effect, diagnostics, weak instrument test

**Key Diagnostics:**
- **First-stage F-stat**: Should be > 10 (Stock-Yogo rule of thumb)
- **Overidentification test** (if multiple instruments): Tests instrument validity
- **Endogeneity test**: Tests if IV is needed

**NBA Examples:**
- **Instrument:** Coach retirement → **Treatment:** Coaching change → **Outcome:** Team wins
- **Instrument:** Injury of key opponent → **Treatment:** Playing time → **Outcome:** Player development

---

### Regression Discontinuity

#### `regression_discontinuity(running_var, cutoff, bandwidth=None, kernel='triangular', polynomial_order=1, fuzzy=False)`

Estimate treatment effect using RDD.

**When to use:**
- Treatment assignment determined by threshold in running variable
- Units just above/below cutoff are comparable (local randomization)

**Parameters:**
- `running_var` (str): Assignment variable
- `cutoff` (float): Treatment threshold
- `bandwidth` (float, optional): If None, optimal bandwidth computed (Imbens-Kalyanaraman)
- `kernel` (str): Kernel function ('triangular', 'uniform', 'epanechnikov')
- `polynomial_order` (int): Polynomial order (1=linear, 2=quadratic)
- `fuzzy` (bool): Fuzzy RDD (imperfect compliance)

**Returns:**
- `RDDResult`: Contains treatment effect, bandwidth, continuity tests

**Key Diagnostics:**
- **McCrary density test**: Tests for manipulation of running variable
- **Bandwidth robustness**: Try different bandwidths
- **Polynomial order**: Higher orders fit better but more variance

**NBA Examples:**
- **Cutoff:** Draft pick 14 (lottery vs non-lottery)
- **Cutoff:** Minutes threshold for qualifying statistics
- **Cutoff:** Salary cap threshold for luxury tax

---

### Propensity Score Matching

#### `propensity_score_matching(method='nearest', n_neighbors=1, caliper=None, replace=False, estimate_std_error=True)`

Estimate treatment effect using PSM.

**When to use:**
- Selection on observables (treatment determined by measured covariates)
- Want to match treated/control units with similar characteristics

**Parameters:**
- `method` (str): Matching method ('nearest', 'radius', 'kernel', 'stratification')
- `n_neighbors` (int): Number of matches per treated unit
- `caliper` (float, optional): Maximum propensity score distance
- `replace` (bool): Match with replacement
- `estimate_std_error` (bool): Compute bootstrap SE

**Returns:**
- `PSMResult`: Contains ATE, ATT, ATC, balance statistics

**Key Diagnostics:**
- **Covariate balance**: SMD (standardized mean difference) should be < 0.1 after matching
- **Common support**: Ensure overlap in propensity score distributions
- **Sensitivity analysis**: How much hidden bias to overturn results?

**NBA Examples:**
- **Treatment:** Participation in development program
- **Treatment:** Playing in high-altitude city
- **Treatment:** Having veteran mentor

---

### Synthetic Control

#### `synthetic_control(treated_unit, outcome_periods, treatment_period, donor_pool=None, n_placebo=0)`

Estimate treatment effect using synthetic control method.

**When to use:**
- Single treated unit (or few treated units)
- Panel data with pre-treatment periods
- Want to create counterfactual from control units

**Parameters:**
- `treated_unit` (Any): Treated entity (value in entity_col)
- `outcome_periods` (List[int]): Periods to analyze
- `treatment_period` (int): When treatment begins
- `donor_pool` (List[Any], optional): Control units for synthetic
- `n_placebo` (int): Number of placebo tests

**Returns:**
- `SyntheticControlResult`: Contains treatment effects, weights, placebo p-value

**Key Diagnostics:**
- **Pre-treatment fit**: RMSE should be small
- **Donor weights**: Check which control units matter
- **Placebo tests**: Inference from placebo distribution

**NBA Examples:**
- **Treatment:** Team relocates to new city
- **Treatment:** Star player acquisition
- **Treatment:** Rule change affects specific team

---

### Sensitivity Analysis

#### `sensitivity_analysis(method, effect_estimate, se_estimate=None, gamma_range=(1.0, 3.0))`

Assess robustness to unobserved confounding.

**When to use:**
- After obtaining causal estimate
- Want to know: "How strong would confounding need to be to overturn results?"

**Parameters:**
- `method` (str): 'rosenbaum', 'e_value', 'confounding_function'
- `effect_estimate` (float): Causal effect from main analysis
- `se_estimate` (float, optional): Standard error
- `gamma_range` (Tuple[float, float]): Range of sensitivity parameter

**Returns:**
- `SensitivityResult`: Contains bounds, critical values

**Methods:**
- **Rosenbaum bounds**: For matched data (PSM)
- **E-value**: Minimum confounding strength to explain away effect
- **Confounding function**: Partial R² approach

---

## Advanced Usage

### Combining Methods for Robustness

```python
# Compare multiple identification strategies
results = {}

# IV estimate
results['iv'] = analyzer.instrumental_variables(instruments='instrument')

# RDD estimate (if applicable)
results['rdd'] = analyzer.regression_discontinuity(
    running_var='assignment_var',
    cutoff=threshold
)

# PSM estimate
results['psm'] = analyzer.propensity_score_matching(method='nearest')

# Compare
print("Treatment Effect Estimates:")
print(f"IV:  {results['iv'].treatment_effect:.2f}")
print(f"RDD: {results['rdd'].treatment_effect:.2f}")
print(f"PSM: {results['psm'].att:.2f}")
```

### MLflow Integration

```python
analyzer = CausalInferenceAnalyzer(
    data=df,
    treatment_col='treatment',
    outcome_col='outcome',
    mlflow_experiment='causal_coaching_study'
)

# All methods automatically log to MLflow
result_iv = analyzer.instrumental_variables(instruments='instrument')
result_psm = analyzer.propensity_score_matching()

# Metrics logged:
# - iv_treatment_effect, iv_p_value, iv_first_stage_f
# - psm_ate, psm_att, psm_n_matched
```

---

## Best Practices

### 1. Identification Strategy

**Always state your identification assumption:**
- IV: "Instrument Z affects outcome Y only through treatment D"
- RDD: "Treatment assignment at cutoff is as-good-as-random"
- PSM: "Selection is only on observed covariates X"

### 2. Diagnostic Checks

**For IV:**
- First-stage F > 10 (avoid weak instruments)
- Test instrument exogeneity (overidentification test)
- Plot first-stage relationship

**For RDD:**
- Plot outcome vs running variable (visual inspection)
- McCrary density test (no manipulation)
- Try different bandwidths (robustness)

**For PSM:**
- Check covariate balance (SMD < 0.1)
- Assess common support
- Sensitivity analysis (Rosenbaum bounds)

**For Synthetic Control:**
- Good pre-treatment fit (low RMSE)
- Placebo tests for inference
- Check donor weights (sparse is better)

### 3. Robustness

- Use multiple methods if possible
- Bootstrap for uncertainty (when asymptotic SE unreliable)
- Sensitivity analysis for unobserved confounding

### 4. Interpretation

- **ATE** (Average Treatment Effect): Effect for random individual
- **ATT** (Effect on Treated): Effect for those who received treatment
- **LATE** (Local ATE): Effect for compliers (IV context)
- **RDD**: Effect at cutoff (local, may not generalize)

---

## Limitations & Caveats

### Instrumental Variables
- Finding valid instruments is hard
- Estimates LATE (local average treatment effect), not ATE
- Weak instruments → large standard errors, bias

### Regression Discontinuity
- Only local effect at cutoff (external validity concerns)
- Requires no manipulation of running variable
- Sensitive to bandwidth and polynomial order

### Propensity Score Matching
- Assumes selection on observables (no unobserved confounding)
- Common support required
- Sensitive to propensity score model specification

### Synthetic Control
- Requires good pre-treatment fit
- Inference via placebo tests (may lack power)
- Extrapolation if treated unit outside convex hull

---

## Dependencies

```bash
pip install linearmodels dowhy networkx scikit-learn scipy numpy pandas
```

**Optional:**
- `mlflow` for experiment tracking

---

## References

### Textbooks
- Angrist & Pischke (2009). *Mostly Harmless Econometrics*
- Angrist & Pischke (2015). *Mastering 'Metrics*
- Imbens & Rubin (2015). *Causal Inference for Statistics, Social, and Biomedical Sciences*

### Papers
- **IV**: Stock & Yogo (2005). Testing for weak instruments
- **RDD**: Imbens & Kalyanaraman (2012). Optimal bandwidth
- **PSM**: Rosenbaum & Rubin (1983). Propensity score matching
- **Synthetic Control**: Abadie et al. (2010). Synthetic control methods

---

## Support

For issues or questions:
- Check test suite: `tests/test_causal_inference.py`
- Review examples above
- Consult references for theoretical details

---

**Next Steps:**
- Module 4B: Survival Analysis for career longevity
- Module 4C: Advanced Time Series for dynamic modeling
- Module 4D: Unified Econometric Suite

