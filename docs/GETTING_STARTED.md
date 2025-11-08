# Getting Started with NBA MCP Synthesis

**Welcome!** This guide will help you get up and running with the NBA MCP Synthesis platform in minutes.

---

## 🎯 What is NBA MCP Synthesis?

NBA MCP Synthesis is a comprehensive analytics platform providing **100+ econometric and statistical methods** for NBA data analysis:

- **Time Series Analysis** - ARIMA, VAR, structural models, forecasting
- **Panel Data Methods** - Fixed/random effects, GMM, hierarchical models
- **Causal Inference** - Propensity score matching, RDD, IV, synthetic control
- **Survival Analysis** - Cox models, Kaplan-Meier, competing risks
- **Bayesian Methods** - MCMC, hierarchical models, uncertainty quantification
- **Real-time Analytics** - Particle filters, streaming analytics, live predictions
- **Ensemble Methods** - Model averaging, stacking, dynamic selection

---

## 📦 Installation

### Requirements
- Python 3.11+
- 4GB+ RAM recommended
- Optional: PostgreSQL (for database features)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/your-org/nba-mcp-synthesis.git
cd nba-mcp-synthesis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -r requirements-dev.txt
```

### Verify Installation

```python
from mcp_server.econometric_suite import EconometricSuite
print("✅ NBA MCP Synthesis installed successfully!")
```

---

## 🚀 Quick Start: Your First Analysis

Let's analyze player scoring patterns using time series analysis.

### Example 1: Time Series Forecasting

```python
import pandas as pd
import numpy as np
from mcp_server.time_series import TimeSeriesAnalyzer

# Sample player scoring data
dates = pd.date_range('2024-01-01', periods=50, freq='D')
points = pd.DataFrame({
    'date': dates,
    'points': 20 + np.random.randn(50) * 5  # ~20 PPG with variance
})

# Create analyzer
analyzer = TimeSeriesAnalyzer(
    data=points,
    target_column='points',
    time_column='date'
)

# Fit ARIMA model
result = analyzer.fit_arima(order=(1, 1, 1))
print(f"AIC: {result.aic:.2f}")

# Forecast next 10 games
forecast = analyzer.forecast(steps=10)
print(f"Next game prediction: {forecast.forecast.iloc[0]:.1f} points")
```

**Output:**
```
AIC: 245.32
Next game prediction: 21.3 points
```

**⚡ Performance:** <50ms for forecasting

---

### Example 2: Panel Data Analysis

Compare multiple players across multiple seasons.

```python
from mcp_server.panel_data import PanelDataAnalyzer

# Multi-player data
panel_data = pd.DataFrame({
    'player_id': ['LBJ', 'LBJ', 'KD', 'KD'] * 10,
    'season': list(range(10)) * 4,
    'points': np.random.normal(25, 5, 40),
    'age': [30, 31, 28, 29] * 10,
    'minutes': np.random.normal(35, 3, 40)
})

# Analyze with fixed effects
analyzer = PanelDataAnalyzer(
    data=panel_data,
    entity_col='player_id',
    time_col='season'
)

# Fixed effects model
result = analyzer.fixed_effects(formula='points ~ age + minutes')
print(result.summary())
```

**⚡ Performance:** <100ms for panel regression

---

### Example 3: Real-time Win Probability

Track win probability during a live game using particle filters.

```python
from mcp_server.particle_filters import LiveGameProbabilityFilter

# Create filter
game_filter = LiveGameProbabilityFilter(
    n_particles=1000,
    home_strength=5.0,  # Home team net rating
    away_strength=3.0   # Away team net rating
)

# Score updates: (time_minutes, home_score, away_score)
score_updates = [
    (12.0, 28, 24),  # End of Q1
    (24.0, 52, 48),  # Halftime
    (36.0, 78, 72),  # End of Q3
    (48.0, 105, 98)  # Final
]

# Track game
result = game_filter.track_game(score_updates)

print(f"Final win probability: {result.final_win_prob:.1%}")
print(f"Win prob at halftime: {result.win_probabilities[1]:.1%}")
```

**Output:**
```
Final win probability: 89.3%
Win prob at halftime: 67.2%
```

**⚡ Performance:** <5ms per update (real-time capable)

---

## 🎓 Common Workflows

### Workflow 1: Player Performance Analysis

```python
from mcp_server.econometric_suite import EconometricSuite

# Load player game logs
player_data = pd.read_csv('lebron_2024_gamelogs.csv')

# Create suite
suite = EconometricSuite(
    data=player_data,
    target='points',
    time_column='game_date'
)

# Comprehensive analysis
results = {
    'trend': suite.time_series_analysis(method='trend_detection'),
    'stationarity': suite.time_series_analysis(method='adf_test'),
    'forecast': suite.time_series_analysis(method='arima', forecast_steps=5)
}

# Print summary
for analysis, result in results.items():
    print(f"{analysis}: {result}")
```

---

### Workflow 2: Team Comparison (Causal Inference)

```python
from mcp_server.causal_inference import CausalInferenceAnalyzer

# Compare teams that changed coaches vs. those that didn't
team_data = pd.DataFrame({
    'team_id': range(30),
    'coach_change': [1]*15 + [0]*15,  # Treatment: coach change
    'wins': np.random.poisson(41, 30),
    'payroll': np.random.normal(120, 20, 30),
    'win_pct_prev': np.random.uniform(0.3, 0.7, 30)
})

# Propensity score matching
analyzer = CausalInferenceAnalyzer(
    data=team_data,
    treatment_col='coach_change',
    outcome_col='wins',
    covariates=['payroll', 'win_pct_prev']
)

result = analyzer.propensity_score_matching()
print(f"Average treatment effect: {result.ate:.2f} wins")
print(f"P-value: {result.p_value:.4f}")
```

**⚡ Performance:** <200ms for matching

---

### Workflow 3: Career Trajectory (Survival Analysis)

```python
from mcp_server.survival_analysis import SurvivalAnalyzer

# Player career data
career_data = pd.DataFrame({
    'player_id': range(100),
    'years_in_league': np.random.exponential(5, 100),
    'retired': np.random.binomial(1, 0.4, 100),
    'draft_position': np.random.randint(1, 60, 100),
    'peak_ppg': np.random.normal(15, 5, 100)
})

# Cox proportional hazards
analyzer = SurvivalAnalyzer(
    data=career_data,
    duration_col='years_in_league',
    event_col='retired',
    covariates=['draft_position', 'peak_ppg']
)

result = analyzer.cox_proportional_hazards()
print(result.summary())
```

**⚡ Performance:** <50ms for Cox model

---

## 📊 Performance Guide

Based on comprehensive benchmarking of 100+ methods:

| Method Category | Typical Time | Use Case |
|----------------|--------------|----------|
| **Streaming Analytics** | <1ms | Real-time event processing |
| **Particle Filters** | <10ms | Live game tracking |
| **Ensemble Methods** | <100ms | Model predictions |
| **Time Series** | <200ms | Forecasting |
| **Panel Data** | <300ms | Multi-entity analysis |
| **Causal Inference** | <500ms | Treatment effects |
| **Bayesian MCMC** | 2-10s | Uncertainty quantification |

💡 **Tip:** All methods <100ms are suitable for real-time/interactive applications.

---

## 🗺️ Next Steps

### Learn More

1. **[API Reference](API_REFERENCE.md)** - Complete documentation of all 100+ methods
2. **[Workflow Tutorials](tutorials/)** - Step-by-step guides for common analyses
3. **[Jupyter Notebooks](notebooks/)** - Interactive examples you can run
4. **[Performance Benchmarks](docs/plans/BENCHMARKING_COMPLETION_SUMMARY.md)** - Detailed performance data

### Example Notebooks

- `notebooks/01_time_series_forecasting.ipynb` - Player scoring predictions
- `notebooks/02_panel_data_analysis.ipynb` - Multi-player comparisons
- `notebooks/03_causal_inference.ipynb` - Treatment effect estimation
- `notebooks/04_survival_analysis.ipynb` - Career trajectory modeling
- `notebooks/05_real_time_analytics.ipynb` - Live game tracking

### Common Patterns

```python
# Pattern 1: Quick Analysis
from mcp_server.econometric_suite import EconometricSuite
suite = EconometricSuite(data=df, target='outcome')
result = suite.analyze(method='arima')

# Pattern 2: Detailed Control
from mcp_server.time_series import TimeSeriesAnalyzer
analyzer = TimeSeriesAnalyzer(data=df, target_column='points')
result = analyzer.fit_arima(order=(2,1,2), seasonal_order=(1,0,1,7))

# Pattern 3: Real-time Streaming
from mcp_server.streaming_analytics import StreamingAnalyzer
stream = StreamingAnalyzer(buffer_size=1000, window_seconds=300)
result = stream.process_event(event)
```

---

## 🔧 Configuration

### Database Connection (Optional)

```python
# Set environment variables
export NBA_DB_HOST=localhost
export NBA_DB_PORT=5432
export NBA_DB_NAME=nba_analytics
export NBA_DB_USER=your_user
export NBA_DB_PASSWORD=your_password
```

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)

# Detailed logs
logging.getLogger('mcp_server').setLevel(logging.DEBUG)
```

### Performance Tuning

```python
# For large datasets, use chunking
analyzer = TimeSeriesAnalyzer(data=df, chunk_size=10000)

# For MCMC methods, adjust sampling
result = bayesian.sample_posterior(draws=2000, tune=1000, chains=4)

# For particle filters, tune particles vs. speed
pf = ParticleFilter(n_particles=500)  # Fast: 500, Accurate: 5000
```

---

## 💡 Tips & Best Practices

### Data Preparation

```python
# Tip 1: Ensure datetime columns are parsed
df['date'] = pd.to_datetime(df['date'])

# Tip 2: Handle missing values before analysis
df = df.dropna(subset=['points', 'minutes'])

# Tip 3: Check data types
print(df.dtypes)

# Tip 4: Sort time series data
df = df.sort_values('date')
```

### Method Selection

- **Time Series**: Use ARIMA for univariate, VAR for multivariate
- **Panel Data**: Start with fixed effects, test with Hausman
- **Causal**: PSM for observational, RDD for discontinuities
- **Survival**: Cox for proportional hazards, Kaplan-Meier for non-parametric
- **Real-time**: Particle filters for state tracking, streaming for events

### Error Handling

```python
from mcp_server.exceptions import InsufficientDataError, InvalidParameterError

try:
    result = analyzer.fit_arima(order=(1,1,1))
except InsufficientDataError:
    print("Need more data points for ARIMA")
except InvalidParameterError as e:
    print(f"Invalid parameter: {e}")
```

---

## 🆘 Troubleshooting

### Common Issues

**Issue 1: ImportError for PyMC**
```bash
# Bayesian methods require PyMC
pip install pymc arviz
```

**Issue 2: Convergence Warnings**
```python
# Increase MCMC samples
result = analyzer.sample_posterior(draws=2000, tune=1000)
```

**Issue 3: Slow Performance**
```python
# Check data size
print(len(df))  # If >10K rows, consider chunking

# Use faster methods first
result = analyzer.fit_arima()  # Fast
# vs
result = analyzer.fit_bvar()  # Slower (MCMC)
```

**Issue 4: Missing Dependencies**
```bash
# Check installation
pip list | grep -E "pandas|numpy|statsmodels|pymc"

# Reinstall if needed
pip install --upgrade -r requirements.txt
```

---

## 🤝 Getting Help

- **Documentation**: [Full API Reference](API_REFERENCE.md)
- **Examples**: [Notebook Gallery](notebooks/)
- **Issues**: [GitHub Issues](https://github.com/your-org/nba-mcp-synthesis/issues)
- **Performance**: [Benchmark Report](docs/plans/BENCHMARKING_COMPLETION_SUMMARY.md)

---

## 📚 Additional Resources

### Academic References

- **Time Series**: Box & Jenkins (1970), Hamilton (1994)
- **Panel Data**: Wooldridge (2010), Baltagi (2013)
- **Causal Inference**: Angrist & Pischke (2009), Imbens & Rubin (2015)
- **Survival Analysis**: Cox (1972), Klein & Moeschberger (2003)
- **Bayesian**: Gelman et al. (2013), McElreath (2020)

### NBA Analytics Papers

- Predicting NBA Player Performance Using Advanced Metrics
- Real-Time Win Probability Models for Basketball
- Causal Effects of Coaching Changes on Team Performance
- Career Trajectory Modeling with Survival Analysis

---

## ✨ What's Next?

Now that you've completed the quick start:

1. **Try the Examples** - Run the code above with your own data
2. **Explore Notebooks** - Open `notebooks/` for interactive tutorials
3. **Read API Docs** - Dive deep into specific methods
4. **Build Your Analysis** - Combine methods for custom workflows

---

**Happy Analyzing! 🏀📊**

*NBA MCP Synthesis - Comprehensive Analytics for Basketball Intelligence*
