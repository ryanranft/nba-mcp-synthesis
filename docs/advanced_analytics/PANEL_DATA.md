# Panel Data Analysis for NBA Performance

**Module:** `mcp_server.panel_data`
**Author:** Agent 8 Module 2
**Date:** October 2025
**Status:** Production Ready

---

## Overview

The `panel_data` module provides econometric panel data methods for analyzing NBA player and team performance across multiple time periods (seasons, games). Panel data combines cross-sectional (e.g., different players) and time-series (e.g., multiple seasons) dimensions, allowing control for entity-specific factors that don't change over time.

### Why Panel Data for NBA Analytics?

NBA data is naturally structured as panel data:
- **Entities:** Players, teams, coaches
- **Time periods:** Seasons, games, quarters
- **Applications:**
  - Player development over career
  - Team performance home vs. away
  - Impact of coaching changes
  - Injury effects on performance

### Key Features

- **Fixed Effects (FE):** Control for time-invariant player/team characteristics
- **Random Effects (RE):** Efficient estimation when effects are random
- **Pooled OLS:** Baseline comparison
- **Model Selection:** Hausman test, F-test for poolability
- **Robust Inference:** Clustered standard errors

---

## Quick Start

```python
import pandas as pd
from mcp_server.panel_data import PanelDataAnalyzer

# Load panel data (players × seasons)
df = pd.DataFrame({
    'player_id': ['LeBron', 'LeBron', 'Curry', 'Curry'],
    'season': [2022, 2023, 2022, 2023],
    'points': [30.3, 28.9, 29.4, 32.2],
    'minutes': [36.5, 35.8, 34.2, 34.7],
    'age': [37, 38, 34, 35]
})

# Initialize analyzer
analyzer = PanelDataAnalyzer(
    data=df,
    entity_col='player_id',
    time_col='season',
    target_col='points'
)

# Estimate fixed effects model
fe_result = analyzer.fixed_effects('points ~ minutes + age')

# View results
print(fe_result.summary())
```

---

## API Reference

### PanelDataAnalyzer

Main class for panel data analysis.

#### Initialization

```python
PanelDataAnalyzer(
    data: pd.DataFrame,
    entity_col: str,
    time_col: str,
    target_col: str
)
```

**Parameters:**
- `data`: DataFrame containing panel data
- `entity_col`: Column identifying entities (e.g., 'player_id', 'team_id')
- `time_col`: Column identifying time periods (e.g., 'season', 'game_number')
- `target_col`: Column containing dependent variable

**Raises:**
- `ValueError`: If columns not found or panel structure invalid

---

### Methods

#### balance_check()

Check if panel is balanced (equal observations per entity).

```python
def balance_check() -> Dict[str, Any]
```

**Returns:**
- `is_balanced`: Whether panel is balanced
- `min_periods`: Minimum observations per entity
- `max_periods`: Maximum observations per entity
- `mean_periods`: Average observations per entity
- `n_entities`: Number of entities
- `n_timeperiods`: Number of time periods

**Example:**
```python
balance = analyzer.balance_check()
print(f"Balanced: {balance['is_balanced']}")
print(f"Entities: {balance['n_entities']}")
```

---

#### pooled_ols()

Estimate pooled OLS model (ignores panel structure).

```python
def pooled_ols(formula: str) -> PanelModelResult
```

**Parameters:**
- `formula`: Model formula (e.g., 'points ~ minutes + age')

**Returns:**
- `PanelModelResult` with coefficients, standard errors, R², etc.

**Example:**
```python
pooled = analyzer.pooled_ols('points ~ minutes + age + usage_rate')
print(f"R-squared: {pooled.r_squared:.4f}")
print(f"Minutes coef: {pooled.coefficients['minutes']:.4f}")
```

---

#### fixed_effects()

Estimate fixed effects (within) model.

```python
def fixed_effects(
    formula: str,
    entity_effects: bool = True,
    time_effects: bool = False
) -> PanelModelResult
```

**Parameters:**
- `formula`: Model formula
- `entity_effects`: Include entity (player/team) fixed effects (default: True)
- `time_effects`: Include time (season) fixed effects (default: False)

**Returns:**
- `PanelModelResult` with within R², between R², etc.

**Example:**
```python
# One-way fixed effects (entity only)
fe = analyzer.fixed_effects('points ~ minutes + age', entity_effects=True)

# Two-way fixed effects (entity + time)
fe_twoway = analyzer.fixed_effects(
    'points ~ minutes + age',
    entity_effects=True,
    time_effects=True
)

print(f"Within R²: {fe.r_squared_within:.4f}")
```

**Note:** Fixed effects absorb time-invariant characteristics (e.g., player talent). Only time-varying regressors (minutes, age) identify coefficients.

---

#### random_effects()

Estimate random effects (GLS) model.

```python
def random_effects(formula: str) -> PanelModelResult
```

**Parameters:**
- `formula`: Model formula

**Returns:**
- `PanelModelResult` with overall, within, and between R²

**Example:**
```python
re = analyzer.random_effects('points ~ minutes + age')
print(f"Overall R²: {re.r_squared_overall:.4f}")
```

**Note:** RE is more efficient than FE when entity effects are uncorrelated with regressors (use Hausman test to check).

---

#### hausman_test()

Hausman test for choosing between FE and RE models.

```python
def hausman_test(
    formula: str,
    fe_result: Optional[PanelModelResult] = None,
    re_result: Optional[PanelModelResult] = None
) -> Dict[str, Any]
```

**Parameters:**
- `formula`: Model formula
- `fe_result`: Pre-computed FE result (optional)
- `re_result`: Pre-computed RE result (optional)

**Returns:**
- `h_statistic`: Hausman test statistic
- `p_value`: P-value
- `degrees_of_freedom`: Degrees of freedom
- `recommendation`: 'fixed_effects' or 'random_effects'

**Interpretation:**
- **H0:** Random effects is consistent and efficient
- **H1:** Fixed effects is consistent (reject RE)
- **Rule:** If p < 0.05, use fixed effects

**Example:**
```python
hausman = analyzer.hausman_test('points ~ minutes + age')
print(f"Test statistic: {hausman['h_statistic']:.4f}")
print(f"P-value: {hausman['p_value']:.4f}")
print(f"Recommendation: {hausman['recommendation']}")
```

---

#### f_test_effects()

F-test for presence of entity effects (pooled vs FE).

```python
def f_test_effects(formula: str) -> Dict[str, Any]
```

**Parameters:**
- `formula`: Model formula

**Returns:**
- `f_statistic`: F-test statistic
- `p_value`: P-value
- `df1`, `df2`: Degrees of freedom
- `recommendation`: 'fixed_effects' or 'pooled_ols'

**Interpretation:**
- **H0:** Pooled OLS is adequate (no entity effects)
- **H1:** Fixed effects needed
- **Rule:** If p < 0.05, use fixed effects

**Example:**
```python
f_test = analyzer.f_test_effects('points ~ minutes')
print(f"F-statistic: {f_test['f_statistic']:.4f}")
print(f"Recommendation: {f_test['recommendation']}")
```

---

#### clustered_standard_errors()

Estimate model with clustered standard errors.

```python
def clustered_standard_errors(
    formula: str,
    cluster_entity: bool = True
) -> PanelModelResult
```

**Parameters:**
- `formula`: Model formula
- `cluster_entity`: Cluster by entity (default: True)

**Returns:**
- `PanelModelResult` with clustered SE

**Example:**
```python
clustered = analyzer.clustered_standard_errors(
    'points ~ minutes + age',
    cluster_entity=True
)
```

**Note:** Use when errors are correlated within entities (common in panel data).

---

### PanelModelResult

Dataclass containing estimation results.

**Attributes:**
- `coefficients`: Estimated coefficients (pd.Series)
- `std_errors`: Standard errors (pd.Series)
- `t_stats`: T-statistics (pd.Series)
- `p_values`: P-values (pd.Series)
- `r_squared`: R-squared
- `r_squared_within`: Within R² (FE models)
- `r_squared_between`: Between R² (panel models)
- `r_squared_overall`: Overall R² (RE models)
- `f_statistic`: F-statistic
- `f_pvalue`: F-test p-value
- `n_obs`: Number of observations
- `n_entities`: Number of entities
- `n_timeperiods`: Number of time periods
- `model_type`: Model type string
- `entity_effects`: Estimated entity effects (if available)
- `time_effects`: Estimated time effects (if available)

**Methods:**
- `summary()`: Generate formatted summary string

---

## NBA Use Cases

### 1. Player Development Over Career

Track how a player's performance evolves over their career, controlling for player-specific talent.

```python
# Load player career data
career_df = pd.DataFrame({
    'player_id': ['Player1'] * 10,
    'season': range(2014, 2024),
    'points': [12.5, 15.2, 18.1, 21.3, 24.5, 25.1, 23.8, 22.1, 20.3, 18.5],
    'age': range(22, 32),
    'experience': range(1, 11)
})

analyzer = PanelDataAnalyzer(
    career_df,
    entity_col='player_id',
    time_col='season',
    target_col='points'
)

# Fixed effects control for player talent
fe = analyzer.fixed_effects('points ~ age + experience')

# Interpret: How does performance change with age/experience?
print(f"Age effect: {fe.coefficients['age']:.4f}")
print(f"Experience effect: {fe.coefficients['experience']:.4f}")
```

**Interpretation:**
- Negative age coefficient → decline with age
- Positive experience coefficient → learning effects

---

### 2. Team Performance: Home vs. Away

Analyze team performance differences between home and away games.

```python
# Load team game data
team_df = pd.DataFrame({
    'team_id': ['LAL'] * 82 + ['GSW'] * 82,
    'game_number': list(range(1, 83)) * 2,
    'points': np.random.normal(110, 10, 164),
    'home': [1]*41 + [0]*41 + [1]*41 + [0]*41,
    'rest_days': np.random.randint(0, 5, 164)
})

analyzer = PanelDataAnalyzer(
    team_df,
    entity_col='team_id',
    time_col='game_number',
    target_col='points'
})

# FE controls for team quality
fe = analyzer.fixed_effects('points ~ home + rest_days')

print(f"Home court advantage: {fe.coefficients['home']:.2f} points")
```

---

### 3. Impact of Coaching Change

Measure the effect of a coaching change on team performance.

```python
# Load team-season data
coach_df = pd.DataFrame({
    'team_id': ['MIA'] * 10,
    'season': range(2014, 2024),
    'wins': [44, 37, 41, 41, 39, 44, 53, 40, 44, 46],
    'new_coach': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
    'payroll_millions': [70, 75, 80, 85, 90, 95, 100, 105, 110, 115]
})

analyzer = PanelDataAnalyzer(
    coach_df,
    entity_col='team_id',
    time_col='season',
    target_col='wins'
)

# Control for team-specific factors
fe = analyzer.fixed_effects('wins ~ new_coach + payroll_millions')

print(f"Coaching change impact: {fe.coefficients['new_coach']:.2f} wins")
```

---

### 4. Injury Recovery Analysis

Track player recovery patterns after injury.

```python
# Load injury recovery data
injury_df = pd.DataFrame({
    'player_id': ['Kawhi', 'Kawhi', 'Kawhi'],
    'months_post_injury': [1, 2, 3],
    'minutes_per_game': [18.5, 24.3, 30.1],
    'efficiency': [0.85, 0.92, 0.98]
})

analyzer = PanelDataAnalyzer(
    injury_df,
    entity_col='player_id',
    time_col='months_post_injury',
    target_col='efficiency'
)

fe = analyzer.fixed_effects('efficiency ~ months_post_injury')

# Recovery rate
print(f"Monthly improvement: {fe.coefficients['months_post_injury']:.4f}")
```

---

## Integration with Other Modules

### With Time Series (Session 01)

Combine panel data and time series analysis:

```python
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.time_series import TimeSeriesAnalyzer

# 1. Use FE to extract within-player variation
panel_analyzer = PanelDataAnalyzer(data, 'player_id', 'season', 'points')
fe_result = panel_analyzer.fixed_effects('points ~ minutes')

# 2. Analyze time trends for specific player
player_data = data[data['player_id'] == 'LeBron']
ts_analyzer = TimeSeriesAnalyzer(
    player_data['points'].values,
    time_col=player_data['season'].values
)
trend = ts_analyzer.detect_trend()
```

### With Data Validation (Agent 4)

Validate panel structure before analysis:

```python
from mcp_server.data_validation import validate_panel_structure

# Validate panel data
validation_result = validate_panel_structure(
    data,
    entity_col='player_id',
    time_col='season'
)

if validation_result['is_valid']:
    analyzer = PanelDataAnalyzer(data, 'player_id', 'season', 'points')
else:
    print(f"Validation errors: {validation_result['errors']}")
```

### With ML Training Pipeline (Agent 5)

Generate panel-based features for ML:

```python
from mcp_server.training_pipeline import TrainingPipeline

# Extract entity fixed effects as features
panel_analyzer = PanelDataAnalyzer(data, 'player_id', 'season', 'points')
fe_result = panel_analyzer.fixed_effects('points ~ minutes')

# Use estimated entity effects as player quality feature
if fe_result.entity_effects is not None:
    data['player_quality'] = data['player_id'].map(fe_result.entity_effects)

# Train ML model with panel features
pipeline = TrainingPipeline(data, target='wins')
```

---

## Best Practices

### 1. Choose the Right Model

**Decision Tree:**

```
Start
  ↓
  Do you have panel data (entity × time)?
  ↓ Yes
  Are entity effects correlated with X?
  ↓ Yes → Use Fixed Effects
  ↓ No  → Use Random Effects (more efficient)
  ↓ Uncertain → Run Hausman test
```

**Rules of Thumb:**
- **Pooled OLS:** Entities are identical (rare in NBA)
- **Fixed Effects:** Default choice for NBA data (players/teams differ)
- **Random Effects:** When entities are random sample (e.g., college players)

### 2. Handle Unbalanced Panels

NBA data is often unbalanced (rookies, trades, injuries):

```python
# Check balance
balance = analyzer.balance_check()

if not balance['is_balanced']:
    print(f"Panel is unbalanced:")
    print(f"  Min periods: {balance['min_periods']}")
    print(f"  Max periods: {balance['max_periods']}")

# Panel methods handle unbalanced data automatically
fe = analyzer.fixed_effects('points ~ minutes')  # Works fine
```

### 3. Interpret Within vs. Between Variation

```python
fe = analyzer.fixed_effects('points ~ age')

print(f"Within R²: {fe.r_squared_within:.4f}")    # How well model explains within-player variation
print(f"Between R²: {fe.r_squared_between:.4f}")  # How well model explains between-player variation
```

**For FE models:**
- `r_squared_within` is most relevant (within-entity variation)
- `r_squared_between` can be low or negative (FE removes between variation)

### 4. Use Clustered Standard Errors

Always use clustered SE when errors may be correlated within entities:

```python
# Standard errors clustered by player
clustered = analyzer.clustered_standard_errors(
    'points ~ minutes + age',
    cluster_entity=True
)

# More conservative (wider) confidence intervals
print(f"Regular SE: {fe.std_errors['minutes']:.4f}")
print(f"Clustered SE: {clustered.std_errors['minutes']:.4f}")
```

### 5. Test for Entity Effects

Always test whether FE are needed:

```python
# F-test for entity effects
f_test = analyzer.f_test_effects('points ~ minutes')

if f_test['p_value'] < 0.05:
    print("Entity effects are significant → Use FE or RE")

    # Hausman test to choose between FE and RE
    hausman = analyzer.hausman_test('points ~ minutes')
    print(f"Use: {hausman['recommendation']}")
else:
    print("Entity effects not significant → Pooled OLS is fine")
```

---

## Common Pitfalls

### 1. Including Time-Invariant Variables in FE

**Problem:** FE removes all time-invariant variation.

```python
# ❌ BAD: Draft position doesn't vary over time
fe = analyzer.fixed_effects('points ~ minutes + draft_position')
# draft_position will be absorbed by entity FE

# ✅ GOOD: Only time-varying variables
fe = analyzer.fixed_effects('points ~ minutes + age')
```

### 2. Forgetting to Cluster Standard Errors

**Problem:** Underestimated standard errors → over-confident inference.

```python
# ❌ Might underestimate SE
fe = analyzer.fixed_effects('points ~ minutes')

# ✅ Better
fe_clustered = analyzer.clustered_standard_errors('points ~ minutes')
```

### 3. Using RE When Effects Are Correlated with X

**Problem:** RE is biased if entity effects correlate with regressors.

```python
# Test for correlation
hausman = analyzer.hausman_test('points ~ minutes')

if hausman['p_value'] < 0.05:
    print("⚠️ RE is biased, use FE instead")
```

---

## Technical Details

### Fixed Effects Estimation

FE uses within-transformation (demeaning):

```
y_it - ȳ_i = (x_it - x̄_i)β + (ε_it - ε̄_i)
```

Where:
- `y_it`: Outcome for entity i at time t
- `ȳ_i`: Average outcome for entity i
- `β`: Coefficient
- `ε_it`: Error term

**Advantages:**
- Eliminates entity-specific bias
- Consistent even if entity effects correlate with X

**Disadvantages:**
- Can't estimate time-invariant variables
- Less efficient than RE (if RE assumptions hold)

### Random Effects Estimation

RE uses GLS (Generalized Least Squares):

```
y_it = α + x_it β + (α_i + ε_it)
```

Where `α_i ~ N(0, σ²_α)` is random entity effect.

**Assumptions:**
- Entity effects uncorrelated with X: `Cov(α_i, x_it) = 0`
- If violated, RE is biased

### Hausman Test

Tests whether `Cov(α_i, x_it) = 0`:

```
H = (β_FE - β_RE)' [Var(β_FE) - Var(β_RE)]^(-1) (β_FE - β_RE) ~ χ²(K)
```

**Interpretation:**
- Small H, large p-value → RE is consistent (use RE for efficiency)
- Large H, small p-value → RE is biased (use FE)

---

## Performance Considerations

### Memory Usage

Panel data with large N (entities) or T (time periods):

```python
# For very large panels (e.g., 10K players × 100 games)
# Consider:

# 1. Use sparse matrices (automatically handled by linearmodels)
# 2. Limit to relevant subset
data_subset = data[data['season'] >= 2020]

# 3. Use low-memory option (for two-way FE)
# Note: Handled automatically by linearmodels when needed
```

### Computation Time

Typical performance:
- **Pooled OLS:** Fast (< 1 second for 100K observations)
- **Fixed Effects:** Moderate (1-5 seconds for 100K obs, 1K entities)
- **Random Effects:** Moderate (2-10 seconds for 100K obs)
- **Hausman Test:** Requires both FE and RE (sum of both)

---

## Troubleshooting

### "Singular matrix" Error

**Cause:** Perfect collinearity between variables.

**Solution:**
```python
# Check for collinearity
correlation_matrix = data[['x1', 'x2', 'x3']].corr()
print(correlation_matrix)

# Drop perfectly correlated variables
```

### Negative Within R-Squared

**Cause:** Model fits worse than mean (unusual but possible).

**Solution:**
- Check model specification
- Ensure variables are time-varying
- Try different model (RE, pooled)

### Very Large Standard Errors

**Cause:** Little within-entity variation, multicollinearity.

**Solution:**
```python
# Check within-entity variation
for col in ['minutes', 'age']:
    within_std = data.groupby('player_id')[col].std().mean()
    print(f"{col} within-SD: {within_std:.4f}")

# If very small, FE may not be appropriate
```

---

## References

### Econometrics Texts

- Wooldridge, J. (2010). *Econometric Analysis of Cross Section and Panel Data*. MIT Press.
- Cameron, A.C. & Trivedi, P.K. (2005). *Microeconometrics: Methods and Applications*. Cambridge.

### linearmodels Documentation

- [linearmodels Panel Models](https://bashtage.github.io/linearmodels/panel/index.html)

### NBA Analytics Applications

- Berri, D.J. & Schmidt, M.B. (2010). *Stumbling on Wins*. FT Press.
- Basketball Reference: [Advanced Stats](https://www.basketball-reference.com/)

---

## Changelog

**Version 1.0 (October 2025)**
- Initial release
- Fixed effects, random effects, pooled OLS
- Hausman test, F-test for poolability
- Clustered standard errors
- Comprehensive NBA examples

---

**For questions or issues, contact Agent 8 or see `mcp_server/panel_data.py` source code.**
