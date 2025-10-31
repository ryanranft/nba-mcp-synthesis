# NBA Econometric Analysis - Jupyter Notebooks

**Status**: ✅ Complete (5/5 notebooks)
**Purpose**: Practical examples demonstrating NBA MCP econometric tools
**Audience**: Data scientists, analysts, and developers using the framework

---

## Notebook Overview

### ✅ Completed Notebooks

#### 1. Player Performance Trend Analysis
**File**: `01_player_performance_trend_analysis.ipynb`
**Methods**: Time Series Analysis, ARIMA, Kalman Filter, Structural Decomposition
**Use Case**: Track player scoring trends, forecast future performance, detect regime changes

**What You'll Learn**:
- Stationarity testing (ADF)
- Time series decomposition (trend + seasonal + residual)
- ARIMA forecasting with confidence intervals
- Kalman filtering for real-time tracking
- Structural time series models
- EconometricSuite auto-detection and model comparison

**Key Insights**:
- How to handle non-stationary sports data
- Forecasting player performance 5-20 games ahead
- Identifying slumps vs. hot streaks algorithmically
- Comparing multiple time series methods

---

#### 2. Career Longevity Modeling
**File**: `02_career_longevity_modeling.ipynb`
**Methods**: Survival Analysis, Cox PH, Kaplan-Meier, Parametric Models
**Use Case**: Predict NBA career length, analyze factors affecting longevity

**What You'll Learn**:
- Kaplan-Meier survival curves by draft round/position
- Cox Proportional Hazards regression
- Hazard ratio interpretation (injury effects, draft position)
- Parametric survival models (Weibull, Log-Normal)
- Individual career predictions
- Testing proportional hazards assumption

**Key Insights**:
- Draft position impact on career length (quantified)
- Injury effects: 45% higher retirement risk
- Position differences: Guards vs. Centers longevity
- Business applications: Contract negotiation, player development

---

#### 3. Coaching Change Causal Impact
**File**: `03_coaching_change_causal_impact.ipynb`
**Methods**: Causal Inference, PSM, Instrumental Variables, Synthetic Control, RDD
**Use Case**: Measure true effect of coaching changes on team performance

**What You'll Learn**:
- Propensity score matching with balance diagnostics
- Instrumental variables (2SLS) with weak instrument tests
- Regression discontinuity design (RDD)
- Synthetic control for single-unit analysis
- Sensitivity analysis (Rosenbaum bounds)
- Method comparison and validation

**Key Insights**:
- Coaching changes have +5 to +8 point net rating effect
- PSM handles confounding from previous performance
- IV/2SLS addresses endogeneity in coaching decisions
- Sensitivity analysis quantifies hidden bias robustness
- Business applications: Cost-benefit of coaching changes

---

#### 4. Injury Recovery Tracking
**File**: `04_injury_recovery_tracking.ipynb`
**Methods**: Markov Switching, Kalman Filter, Structural Time Series
**Use Case**: Model recovery phases, predict return-to-form timeline

**What You'll Learn**:
- Markov switching regime detection (3 regimes: struggling, recovering, healthy)
- Regime probability tracking over time
- Transition probability matrices and expected regime durations
- Kalman filter for smoothed performance trajectory
- Structural decomposition (trend, seasonal, residual)
- Recovery timeline prediction

**Key Insights**:
- Distinct recovery phases can be automatically detected
- Regime probabilities provide objective return-to-play guidance
- Kalman filtering removes game-to-game noise
- Expected recovery times can be estimated from transition probabilities
- Business applications: Load management, medical decisions, roster planning

---

#### 5. Team Chemistry Factor Analysis
**File**: `05_team_chemistry_factor_analysis.ipynb`
**Methods**: Dynamic Factor Models, Panel Data, Hierarchical Models
**Use Case**: Quantify team chemistry, identify chemistry leaders

**What You'll Learn**:
- Dynamic factor models for latent chemistry extraction
- Factor loadings (how metrics respond to chemistry)
- Player-specific chemistry contributions
- Lineup-based chemistry estimation
- Chemistry vs. talent decomposition
- Win probability modeling with chemistry

**Key Insights**:
- Chemistry can be objectively quantified from performance metrics
- Chemistry adds 2-5 wins per season beyond talent
- "Chemistry guys" can be identified and ranked
- Trade impact can be assessed via chemistry change
- Business applications: Roster construction, trade evaluation, contract valuation

---

## Getting Started

### Prerequisites

```bash
# Install NBA MCP server with all dependencies
pip install -r requirements.txt

# Required packages for notebooks
pip install jupyter matplotlib seaborn pandas numpy
```

### Running Notebooks

```bash
# Launch Jupyter
cd examples/notebooks
jupyter notebook

# Or use JupyterLab
jupyter lab
```

### Data Requirements

**These notebooks use synthetic data for demonstration**. In production, you would connect to:

- **Player stats database**: Game-by-game performance data
- **Career database**: Draft info, retirement dates, injuries
- **Team database**: Coaching changes, roster composition
- **Injury database**: Injury dates, types, return dates

**See**: `mcp_server/database.py` for connection utilities

---

## Notebook Structure

Each notebook follows this pattern:

1. **Setup & Data Loading**
   - Import libraries
   - Load or generate data
   - Initial visualization

2. **Method Application**
   - Step-by-step analysis
   - Code + explanations
   - Visualizations

3. **Model Comparison**
   - Compare multiple approaches
   - Information criteria (AIC/BIC)
   - Select best model

4. **Business Insights**
   - Interpret results
   - Actionable recommendations
   - Production deployment tips

5. **Summary**
   - Key findings
   - Next steps
   - Related notebooks

---

## Advanced Usage

### Connecting to Real Data

Replace synthetic data generation with database queries:

```python
from mcp_server.database import NBADatabase

# Initialize database connection
db = NBADatabase(
    host=os.getenv('RDS_HOST'),
    database=os.getenv('RDS_DATABASE'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD')
)

# Query player data
player_df = db.query(\"\"\"
    SELECT game_date, player_id, points, assists, rebounds
    FROM player_stats
    WHERE player_id = 'lebron_james'
    AND season >= 2020
    ORDER BY game_date
\"\"\")
```

### Exporting Results

```python
# Export predictions to CSV
forecast_df.to_csv('player_forecast.csv', index=False)

# Save plots
fig.savefig('survival_curves.png', dpi=300, bbox_inches='tight')

# Export model to MLflow
import mlflow
mlflow.sklearn.log_model(cox_result.model, "cox_model")
```

### Automation

```python
# Run notebook programmatically
import papermill as pm

pm.execute_notebook(
    '01_player_performance_trend_analysis.ipynb',
    'output_lebron.ipynb',
    parameters={'player_id': 'lebron_james', 'seasons': 5}
)
```

---

## Troubleshooting

### Common Issues

**1. Module not found errors**
```bash
# Ensure mcp_server is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/nba-mcp-synthesis"
```

**2. Missing dependencies**
```bash
# Install optional dependencies
pip install linearmodels  # For panel data
pip install lifelines     # For survival analysis
pip install pymc          # For Bayesian methods
```

**3. ARIMA convergence warnings**
- Try different order (p, d, q)
- Check for outliers in data
- Ensure sufficient data points (>50 recommended)

**4. Survival analysis errors**
- Verify event indicator is 0/1
- Check for negative durations
- Ensure at least 10% event rate

**5. Markov Switching convergence issues**
- Increase `maxiter` parameter (try 2000+)
- Check for sufficient regime variation in data
- Try different starting values
- Simplify model (reduce number of regimes)

**6. Dynamic Factor Model issues**
- Ensure all series are standardized
- Check for multicollinearity in observed metrics
- Verify sufficient time periods (>50 recommended)
- Try different number of factors (k_factors parameter)

---

## Performance Tips

### For Large Datasets

```python
# Use sampling for exploration
sample_df = player_df.sample(frac=0.1, random_state=42)

# Chunk processing for forecasts
for chunk in pd.read_csv('player_stats.csv', chunksize=10000):
    process_chunk(chunk)

# Parallel execution
from joblib import Parallel, delayed
results = Parallel(n_jobs=4)(
    delayed(fit_model)(player) for player in players
)
```

### Memory Optimization

```python
# Use appropriate dtypes
player_df['player_id'] = player_df['player_id'].astype('category')
player_df['points'] = player_df['points'].astype('float32')

# Clear intermediate results
del intermediate_df
import gc; gc.collect()
```

---

## Contributing

To add new notebooks:

1. Follow naming convention: `0X_descriptive_name.ipynb`
2. Use consistent structure (see existing notebooks)
3. Include business context and recommendations
4. Add entry to this README
5. Test with clean kernel restart

---

## Resources

**Documentation**:
- [Time Series Methods](../../docs/advanced_analytics/TIME_SERIES.md)
- [Survival Analysis Guide](../../docs/advanced_analytics/SURVIVAL_ANALYSIS.md)
- [Causal Inference](../../docs/advanced_analytics/CAUSAL_INFERENCE.md)
- [Panel Data Methods](../../docs/advanced_analytics/PANEL_DATA.md)

**API Reference**:
- [TimeSeriesAnalyzer](../../mcp_server/time_series.py)
- [SurvivalAnalyzer](../../mcp_server/survival_analysis.py)
- [EconometricSuite](../../mcp_server/econometric_suite.py)

**External Resources**:
- [Statsmodels Documentation](https://www.statsmodels.org/)
- [Lifelines Documentation](https://lifelines.readthedocs.io/)
- [PyMC Documentation](https://www.pymc.io/)

---

## Citation

If you use these notebooks in research or publications:

```bibtex
@misc{nba_mcp_notebooks,
  title={NBA MCP Econometric Analysis Notebooks},
  author={NBA MCP Development Team},
  year={2025},
  publisher={GitHub},
  howpublished={\\url{https://github.com/your-org/nba-mcp-synthesis}}
}
```

---

## Additional Resources

**Best Practices Guide**: See [ECONOMETRIC_BEST_PRACTICES.md](./ECONOMETRIC_BEST_PRACTICES.md) for:
- Method selection decision tree
- Interpretation guidelines
- Common pitfalls and troubleshooting
- Production deployment strategies
- Data requirements and statistical power

---

**Status**: ✅ 5/5 notebooks complete (100%)
**Last Updated**: October 31, 2025
**Next**: Production deployment and testing (Option 4)
