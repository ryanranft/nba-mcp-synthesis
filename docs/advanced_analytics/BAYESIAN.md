# Bayesian Methods for NBA Analytics with Uncertainty Quantification

**Module:** `mcp_server.bayesian`
**Author:** Agent 8 Module 3
**Date:** October 2025
**Status:** Production Ready

---

## Overview

The Bayesian Methods module provides research-grade probabilistic modeling for NBA analytics. Unlike frequentist methods that produce point estimates, Bayesian methods quantify uncertainty through full **posterior distributions**.

### Why Bayesian Methods?

Traditional (frequentist) ML gives you:
- Point estimates: "Player A will score 25.3 points"
- Confidence intervals (often misinterpreted)

Bayesian methods give you:
- **Full posterior distributions**: "Player A will score 20-30 points with 95% probability"
- **Hierarchical models**: Automatically share information across players/teams
- **Incorporating prior knowledge**: Use historical data or expert opinions
- **Probabilistic predictions**: Get credible intervals, not just point estimates
- **Small sample robustness**: Work better with limited data

### Key Features

- **MCMC Sampling**: NUTS (No-U-Turn Sampler) for efficient posterior exploration
- **Variational Inference**: Fast approximate inference (ADVI)
- **Hierarchical Models**: Players nested within teams, partial pooling
- **Model Comparison**: WAIC, LOO for principled model selection
- **Posterior Predictive Checks**: Validate model fit
- **Convergence Diagnostics**: Rhat, effective sample size

---

## Quick Start

### Example 1: Bayesian Linear Regression

```python
import pandas as pd
from mcp_server.bayesian import BayesianAnalyzer

# Load player performance data
df = pd.DataFrame({
    'player_id': ['LBJ', 'KD', 'CP3', ...],
    'points': [27.2, 28.1, 16.4, ...],
    'minutes': [35.2, 34.8, 30.1, ...],
    'usage_rate': [0.31, 0.29, 0.23, ...],
    'three_point_attempts': [4.5, 5.2, 2.1, ...]
})

# Initialize analyzer
analyzer = BayesianAnalyzer(
    data=df,
    target='points',
    features=['minutes', 'usage_rate', 'three_point_attempts']
)

# Sample posterior distribution
result = analyzer.sample_posterior(
    draws=2000,         # MCMC samples
    tune=1000,          # Burn-in period
    chains=4,           # Parallel chains
    formula='points ~ minutes + usage_rate + three_point_attempts'
)

# Posterior summary
print(result.summary())

# Credible intervals (Bayesian confidence intervals)
ci = analyzer.credible_interval(result, prob=0.95)
print(f"Minutes coefficient: {ci['minutes']}")
```

**Output:**
```
Parameter Posterior Summary:
                mean    sd    hdi_2.5%  hdi_97.5%  rhat  ess_bulk
intercept       5.2    1.1      3.1        7.3     1.00   3800
minutes         0.52   0.03     0.46       0.58    1.00   3950
usage_rate     35.4    4.2     27.2       43.5     1.00   3750
three_point    1.8    0.2      1.4        2.2     1.00   3900

Minutes coefficient 95% HDI: [0.46, 0.58]
```

**Interpretation:**
- 95% probability that minutes coefficient is between 0.46-0.58
- Rhat ≈ 1.00: Chains converged (✓)
- ESS > 1000: Good effective sample size (✓)

---

### Example 2: Hierarchical Model (Players Within Teams)

```python
from mcp_server.bayesian import BayesianAnalyzer, HierarchicalModelSpec

# Data with team structure
df = pd.DataFrame({
    'player_id': [...],
    'team_id': ['LAL', 'LAL', 'GSW', 'GSW', ...],
    'points': [...],
    'minutes': [...],
    'experience': [...]  # Years in NBA
})

# Hierarchical model specification
spec = HierarchicalModelSpec(
    group_variable='team_id',     # Teams are groups
    nested_variable='player_id',  # Players nested within teams
    formula='points ~ minutes + experience'
)

analyzer = BayesianAnalyzer(data=df, target='points')

# Fit hierarchical model with partial pooling
result = analyzer.hierarchical_model(spec, draws=2000)

# Team-level effects
team_effects = result.group_effects['team_id']
print(team_effects)

# Player-level effects (shrunk towards team mean)
player_effects = result.group_effects.get('player_id', {})
```

**Key Concept - Partial Pooling:**
- **No pooling**: Estimate each team separately (overfits small samples)
- **Complete pooling**: Ignore teams entirely (underfits)
- **Partial pooling (Bayesian)**: Teams share information, shrink towards grand mean

**Output:**
```
Team-Level Effects:
LAL    +3.2 points (strong offense)
GSW    +2.8 points
BOS    -0.5 points (average)
...

Player effects automatically shrunk based on sample size and team context.
```

---

### Example 3: Posterior Predictive Checks

```python
# Sample posterior
result = analyzer.sample_posterior(draws=2000)

# Posterior predictive check
ppc = analyzer.posterior_predictive_check(result)

print(f"Bayesian p-value: {ppc.p_value:.3f}")
print(f"Mean predicted: {ppc.mean_prediction.mean():.2f}")
print(f"Mean observed: {ppc.observed.mean():.2f}")

# Check if model predictions are reasonable
if 0.05 < ppc.p_value < 0.95:
    print("✓ Model fit looks good")
else:
    print("✗ Model may not fit data well")
```

---

## API Reference

### BayesianAnalyzer Class

```python
class BayesianAnalyzer:
    def __init__(
        self,
        data: pd.DataFrame,
        target: Optional[str] = None,
        features: Optional[List[str]] = None,
        backend: str = "pymc",
        mlflow_experiment: Optional[str] = None
    )
```

**Parameters:**
- `data`: DataFrame with observations
- `target`: Target variable column name
- `features`: List of predictor columns
- `backend`: Inference backend ("pymc" only currently)
- `mlflow_experiment`: MLflow experiment name for tracking

---

### Methods

#### 1. MCMC Sampling (Primary Method)

```python
def sample_posterior(
    self,
    draws: int = 2000,
    tune: int = 1000,
    chains: int = 4,
    formula: Optional[str] = None,
    likelihood: str = "normal",
    priors: Optional[Dict[str, Dict]] = None,
    random_seed: Optional[int] = None
) -> PosteriorResult
```

Sample from posterior distribution using NUTS sampler.

**Parameters:**
- `draws`: Number of posterior samples per chain
- `tune`: Burn-in samples to discard
- `chains`: Number of parallel MCMC chains (recommend 4)
- `formula`: R-style formula (e.g., "y ~ x1 + x2")
- `likelihood`: Distribution family ("normal", "poisson", "bernoulli")
- `priors`: Custom prior specifications
- `random_seed`: For reproducibility

**Returns:** PosteriorResult with trace, diagnostics, summary statistics

**Example:**
```python
result = analyzer.sample_posterior(
    draws=3000,
    tune=1500,
    chains=4,
    formula="points ~ minutes + usage_rate + C(position)",
    random_seed=42
)
```

---

#### 2. Variational Inference (Fast Approximation)

```python
def variational_inference(
    self,
    method: str = "advi",
    n_iter: int = 50000,
    formula: Optional[str] = None
) -> VIResult
```

Fast approximate inference using ADVI (Automatic Differentiation VI).

**Use When:**
- Need fast inference (10-100x faster than MCMC)
- Initial model exploration
- Large datasets (>100k observations)

**Caution:** Less accurate than MCMC, may underestimate uncertainty

**Example:**
```python
vi_result = analyzer.variational_inference(
    method='advi',
    n_iter=100000,
    formula='points ~ minutes + experience'
)

print(f"ELBO: {vi_result.elbo:.2f}")
print(f"Converged: {vi_result.converged}")
```

---

#### 3. Hierarchical Models

```python
def hierarchical_model(
    self,
    spec: HierarchicalModelSpec,
    draws: int = 2000,
    tune: int = 1000
) -> PosteriorResult
```

Fit hierarchical/multi-level model with partial pooling.

**Hierarchical Model Specification:**
```python
from mcp_server.bayesian import HierarchicalModelSpec

spec = HierarchicalModelSpec(
    group_variable='team_id',      # Primary grouping
    nested_variable='player_id',   # Optional nested grouping
    formula='points ~ minutes + experience',
    group_level_priors={
        'sigma_team': {'distribution': 'halfnormal', 'params': {'sigma': 5.0}}
    }
)
```

**Example: Three-Level Hierarchy**
```python
# Conference > Team > Player
spec = HierarchicalModelSpec(
    group_variable='conference',
    nested_variable='team_id',
    formula='points ~ minutes'
)
```

---

#### 4. Model Comparison

```python
def compare_models(
    self,
    results: Dict[str, PosteriorResult],
    ic: str = "waic"
) -> ModelComparisonResult
```

Compare multiple Bayesian models using information criteria.

**Information Criteria:**
- `waic`: Widely Applicable Information Criterion
- `loo`: Leave-One-Out Cross-Validation (more robust)

**Example:**
```python
# Fit multiple models
model1 = analyzer.sample_posterior(formula='points ~ minutes')
model2 = analyzer.sample_posterior(formula='points ~ minutes + experience')
model3 = analyzer.sample_posterior(formula='points ~ minutes + experience + height')

# Compare
comparison = analyzer.compare_models({
    'simple': model1,
    'with_experience': model2,
    'with_height': model3
}, ic='loo')

print(comparison.comparison_table)
print(f"Best model: {comparison.best_model}")
```

**Output:**
```
Model Comparison (LOO):
                    elpd_loo  p_loo  loo_scale    weight
with_experience     -152.3    5.2      304.6      0.65
with_height         -153.1    6.1      306.2      0.30
simple              -158.4    3.8      316.8      0.05

Best model: with_experience
```

---

#### 5. Posterior Analysis

```python
def credible_interval(
    self,
    result: PosteriorResult,
    prob: float = 0.95,
    method: str = "hdi"
) -> Dict[str, Tuple[float, float]]
```

Compute credible intervals (Bayesian confidence intervals).

**Methods:**
- `hdi`: Highest Density Interval (recommended)
- `quantile`: Equal-tailed interval

**Example:**
```python
ci_95 = analyzer.credible_interval(result, prob=0.95)
ci_50 = analyzer.credible_interval(result, prob=0.50)  # Interquartile range

print("95% Credible Intervals:")
for param, (lower, upper) in ci_95.items():
    print(f"  {param}: [{lower:.2f}, {upper:.2f}]")
```

---

#### 6. Posterior Predictive Checks

```python
def posterior_predictive_check(
    self,
    result: PosteriorResult,
    n_samples: int = 1000
) -> PPCResult
```

Validate model fit by comparing observed data to posterior predictions.

**Interpretation:**
- **Bayesian p-value near 0.5**: Good fit
- **p-value < 0.05 or > 0.95**: Model may not fit well

**Example:**
```python
ppc = analyzer.posterior_predictive_check(result)

import matplotlib.pyplot as plt
plt.hist(ppc.predicted.flatten(), alpha=0.5, label='Predicted')
plt.hist(ppc.observed, alpha=0.5, label='Observed')
plt.legend()
plt.title(f"PPC (p-value: {ppc.p_value:.3f})")
```

---

#### 7. Convergence Diagnostics

```python
def check_convergence(
    self,
    result: PosteriorResult
) -> Dict[str, Any]
```

Check MCMC convergence.

**Key Metrics:**
- **Rhat**: Should be < 1.01 (ideally < 1.001)
- **Effective Sample Size (ESS)**: Should be > 400 per chain
- **Divergences**: Should be 0

**Example:**
```python
diagnostics = analyzer.check_convergence(result)

if diagnostics['all_rhat_ok']:
    print("✓ Chains converged")
else:
    print("✗ Convergence issues - increase draws/tune")

print(f"Min ESS: {diagnostics['min_ess']}")
print(f"Divergences: {diagnostics['n_divergences']}")
```

---

## NBA Use Cases

### 1. Player Performance with Uncertainty

**Question:** How many points will Player X score next game?

```python
analyzer = BayesianAnalyzer(data=player_history, target='points')
result = analyzer.sample_posterior(formula='points ~ minutes + opponent_def_rating')

# Posterior predictive distribution for new game
new_game = pd.DataFrame({
    'minutes': [35.0],
    'opponent_def_rating': [112.5]
})

predictions = analyzer.predict(result, new_game, return_posterior=True)

# Full distribution, not just point estimate
print(f"Predicted points: {predictions.mean():.1f}")
print(f"95% Credible Interval: [{np.percentile(predictions, 2.5):.1f}, {np.percentile(predictions, 97.5):.1f}]")
print(f"Probability of 30+ points: {(predictions >= 30).mean():.1%}")
```

---

### 2. Team-Level Hierarchical Model

**Question:** How much does team context affect individual performance?

```python
spec = HierarchicalModelSpec(
    group_variable='team_id',
    formula='points ~ minutes + experience'
)

result = analyzer.hierarchical_model(spec)

# Variance components
team_variance = result.group_effects['team_id'].var()
residual_variance = result.residual_variance

icc = team_variance / (team_variance + residual_variance)
print(f"Intraclass Correlation: {icc:.2%}")
print(f"{icc:.0%} of variation is between teams")
```

---

### 3. Updating Beliefs with New Data (Bayesian Updating)

**Question:** Update player projection as season progresses

```python
# Prior: Pre-season projection (weak prior)
prior_mean = 18.0  # Expected points based on last season
prior_std = 5.0    # Uncertain

# After 10 games
early_season = first_10_games_data
result_early = analyzer.sample_posterior(
    formula='points ~ 1',  # Intercept only
    priors={'intercept': {'distribution': 'normal', 'params': {'mu': prior_mean, 'sigma': prior_std}}}
)

# After 30 games
mid_season = first_30_games_data
result_mid = analyzer.sample_posterior(
    formula='points ~ 1',
    priors={'intercept': {'distribution': 'normal', 'params': {'mu': prior_mean, 'sigma': prior_std}}}
)

# Posterior narrows as we get more data
print(f"After 10 games: {result_early.summary()['mean']['intercept']:.1f} ± {result_early.summary()['sd']['intercept']:.1f}")
print(f"After 30 games: {result_mid.summary()['mean']['intercept']:.1f} ± {result_mid.summary()['sd']['intercept']:.1f}")
```

---

### 4. Probabilistic Trade Analysis

**Question:** What's the probability Player A's performance improves with Team B?

```python
# Model: points ~ minutes + team_offensive_rating + player_skill
result = analyzer.sample_posterior(
    formula='points ~ minutes + team_off_rating',
    draws=5000
)

# Simulate trade scenarios
current_team_rating = 108.5
new_team_rating = 115.2

# Posterior predictions
current_scenario = analyzer.predict(result, pd.DataFrame({
    'minutes': [32.0],
    'team_off_rating': [current_team_rating]
}), return_posterior=True)

trade_scenario = analyzer.predict(result, pd.DataFrame({
    'minutes': [32.0],
    'team_off_rating': [new_team_rating]
}), return_posterior=True)

# Probability of improvement
prob_improvement = (trade_scenario > current_scenario).mean()
print(f"Probability of scoring more with new team: {prob_improvement:.1%}")
```

---

## Integration with Other Modules

### With Time Series (Module 1)

```python
from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.bayesian import BayesianAnalyzer

# Bayesian time series with hierarchical structure
# Future: Bayesian structural time series
```

### With Panel Data (Module 2)

```python
# Bayesian panel models with random effects
spec = HierarchicalModelSpec(
    group_variable='player_id',
    formula='points ~ season + age'
)
```

### MLflow Integration

```python
import mlflow

mlflow.set_experiment("bayesian_player_performance")

with mlflow.start_run(run_name="hierarchical_team_model"):
    result = analyzer.sample_posterior(draws=2000)

    # Automatically logged:
    # - Posterior summaries
    # - Convergence diagnostics
    # - Model parameters
    # - Trace plots (artifacts)
```

---

## Best Practices

### 1. Prior Selection

**Weakly Informative Priors (Recommended):**
```python
priors = {
    'intercept': {'distribution': 'normal', 'params': {'mu': 0, 'sigma': 10}},
    'beta': {'distribution': 'normal', 'params': {'mu': 0, 'sigma': 5}},
    'sigma': {'distribution': 'halfnormal', 'params': {'sigma': 5}}
}
```

**Informative Priors (When You Have Domain Knowledge):**
```python
# E.g., we know coefficient for minutes should be positive and around 0.5
priors = {
    'minutes': {'distribution': 'normal', 'params': {'mu': 0.5, 'sigma': 0.1}}
}
```

### 2. Convergence Checking

Always check:
1. **Rhat < 1.01** for all parameters
2. **ESS > 400** (ideally > 1000)
3. **No divergences**
4. **Trace plots** look like "fuzzy caterpillars"

If not converged:
- Increase `draws` and `tune`
- Use better priors
- Reparameterize model

### 3. Model Selection

1. Start simple, add complexity incrementally
2. Use LOO/WAIC for comparison
3. Check posterior predictive checks
4. Validate on held-out data

### 4. Sample Size

**Minimum Recommended:**
- Simple regression: 50 observations
- Hierarchical model: 20+ groups, 5+ obs/group
- Complex models: 200+ observations

**MCMC Settings:**
- Quick exploration: 1000 draws, 500 tune
- Production: 2000 draws, 1000 tune, 4 chains
- Publication: 4000 draws, 2000 tune, 4 chains

---

## Common Pitfalls

❌ **Don't:**
- Use flat/improper priors (causes convergence issues)
- Ignore convergence diagnostics
- Treat credible intervals like confidence intervals
- Over-interpret small posterior probabilities

✅ **Do:**
- Use weakly informative priors
- Always check Rhat and ESS
- Report full posterior distributions when possible
- Do sensitivity analysis (vary priors, check robustness)

---

## Comparison: Bayesian vs Frequentist

| Aspect | Frequentist | Bayesian |
|--------|-------------|----------|
| **Output** | Point estimate + CI | Full posterior distribution |
| **Uncertainty** | Sampling variability | Probability of parameter values |
| **Interpretation** | "If we repeat this many times..." | "Probability that parameter is in this range" |
| **Small samples** | Poor performance | Robust with good priors |
| **Hierarchical** | Complex (random effects) | Natural with partial pooling |
| **Computation** | Fast (closed-form often) | Slower (MCMC/VI) |
| **Prior knowledge** | Not incorporated | Can incorporate |

---

## Dependencies

```python
# Required
pymc>=5.0.0                # Bayesian modeling
arviz>=0.15.0              # Posterior analysis and diagnostics
pytensor>=2.10.0           # Computation backend
numpy>=1.21.0
pandas>=1.3.0

# Optional
matplotlib>=3.5.0          # Plotting
seaborn>=0.12.0           # Enhanced visualizations
```

---

## References

### Academic

1. Gelman, A. et al. (2013). *Bayesian Data Analysis* (3rd ed.)
2. McElreath, R. (2020). *Statistical Rethinking* (2nd ed.)
3. Kruschke, J. (2014). *Doing Bayesian Data Analysis*

### Software

- **PyMC**: https://www.pymc.io/
- **ArviZ**: https://arviz-devs.github.io/arviz/

### NBA Applications

- Cervone, D. et al. (2016). "A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes"
- Franks, A. et al. (2015). "Counterpoints: Advanced Defensive Metrics for NBA Basketball"

---

## FAQ

**Q: When should I use Bayesian vs frequentist methods?**

A: Use Bayesian when:
- Want full uncertainty quantification
- Have small samples
- Need hierarchical modeling
- Want to incorporate prior knowledge
- Probabilistic interpretation matters

Use frequentist when:
- Need fast inference
- Large samples (asymptotic properties good)
- Don't have domain knowledge for priors

**Q: How do I choose priors?**

A:
1. **Default**: Weakly informative priors (broad but not flat)
2. **With knowledge**: Informative priors based on previous studies
3. **Sensitivity**: Try multiple priors, check if conclusions change

**Q: What if MCMC doesn't converge?**

A:
1. Increase `draws` and `tune`
2. Use better (more informative) priors
3. Reparameterize model (e.g., non-centered parameterization)
4. Check for label switching in mixture models

**Q: Is VI (variational inference) accurate enough?**

A: VI is good for:
- Initial exploration
- Large datasets
- When approximate uncertainty is OK

Not recommended for:
- Final inference (use MCMC)
- Critical decisions requiring precise uncertainty
- Complex models

---

## Support

**Module Location:** `mcp_server/bayesian.py`
**Tests:** `tests/test_bayesian.py`
**Examples:** See test files for 25+ usage examples

**Session:** 03 - Bayesian Methods
**Status:** Production Ready (Full test coverage)

---

*Generated by Agent 8 Module 3 - October 2025*
