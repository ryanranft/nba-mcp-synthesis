# NBA MCP Synthesis - Tutorial Notebooks

Comprehensive tutorials demonstrating the NBA MCP Analytics platform's 50+ econometric and ML methods.

---

## Overview

These notebooks provide hands-on tutorials for:
- Time series forecasting (ARIMA, Prophet, state space models)
- Panel data econometrics (fixed effects, random effects)
- Causal inference (PSM, DiD, IV, RDD)
- Real-time analytics (particle filters, streaming)
- Survival analysis (Kaplan-Meier, Cox regression)
- Model ensembles and pipeline orchestration

**Total Content:** ~2 hours of guided tutorials
**Difficulty:** Beginner to Advanced
**Prerequisites:** Basic Python and pandas knowledge

---

## Tutorial Notebooks

### 01. Quick Start: Player Performance Analysis
**File:** `01_quick_start_player_analysis.ipynb`
**Duration:** 10-15 minutes
**Level:** Beginner

**Topics:**
- Time series analysis (ADF test, trend detection)
- ARIMA forecasting with confidence intervals
- Particle filters for skill and form tracking
- Model validation techniques

**What You'll Learn:**
- Load and visualize player performance data
- Detect trends and test for stationarity
- Generate forecasts with uncertainty quantification
- Separate persistent skill from temporary form

**Key Methods:** `TimeSeriesAnalyzer`, `ARIMAForecaster`, `PlayerPerformanceParticleFilter`

---

### 02. Panel Data: Multi-Player Comparison
**File:** `02_panel_data_multi_player_comparison.ipynb`
**Duration:** 15-20 minutes
**Level:** Intermediate

**Topics:**
- Panel data fixed effects regression
- Panel data random effects regression
- Hausman test for model selection
- Player rankings controlling for observables

**What You'll Learn:**
- Compare multiple players across seasons
- Control for time-invariant player characteristics
- Identify which factors drive performance
- Make statistically rigorous comparisons

**Key Methods:** `PanelDataAnalyzer`, `fixed_effects()`, `random_effects()`, `hausman_test()`

**Business Question:** Which players have the highest intrinsic ability after controlling for age, minutes, and usage?

---

### 03. Real-Time Analytics with Particle Filters
**File:** `03_real_time_analytics.ipynb`
**Duration:** 15-20 minutes
**Level:** Advanced

**Topics:**
- Live win probability tracking during games
- Real-time player performance monitoring
- Streaming event processing
- Momentum detection and alerts

**What You'll Learn:**
- Update win probability after each possession
- Track player skill and form states in real-time
- Process streaming events with <10ms latency
- Detect hot/cold streaks automatically

**Key Methods:** `LiveGameProbabilityFilter`, `PlayerPerformanceParticleFilter`, `StreamingAnalyzer`

**Use Case:** In-game coaching decisions and live broadcast graphics

---

### 04. Causal Inference: Measuring Coaching Impact
**File:** `04_causal_inference_coaching_impact.ipynb`
**Duration:** 20-25 minutes
**Level:** Advanced

**Topics:**
- Propensity Score Matching (PSM)
- Difference-in-Differences (DiD)
- Instrumental Variables (IV / 2SLS)
- Regression Discontinuity Design (RDD)

**What You'll Learn:**
- Separate causation from correlation
- Control for selection bias and confounders
- Estimate treatment effects rigorously
- Choose the right causal inference method

**Key Methods:** `CausalInferenceAnalyzer`, `propensity_score_matching()`, `difference_in_differences()`

**Business Question:** Did hiring a new coach actually improve team performance, or was it just chance?

---

### 05. Survival Analysis: Career Longevity Prediction
**File:** `05_survival_analysis_career_longevity.ipynb`
**Duration:** 20-25 minutes
**Level:** Advanced

**Topics:**
- Kaplan-Meier survival curves
- Cox proportional hazards regression
- Accelerated failure time (AFT) models
- Competing risks analysis (retirement vs. injury)

**What You'll Learn:**
- Handle censored data (active players)
- Estimate career survival probabilities
- Identify risk factors for early retirement
- Model different career exit routes

**Key Methods:** `SurvivalAnalyzer`, `kaplan_meier()`, `cox_regression()`, `competing_risks()`

**Business Question:** How long will a player's career last? When should we offer multi-year vs. one-year contracts?

---

### 06. Ensemble Methods & Integration Workflows
**File:** `06_ensemble_and_integration_workflows.ipynb`
**Duration:** 20-25 minutes
**Level:** All Levels

**Topics:**
- Multi-model ensembles (simple, weighted, median)
- End-to-end pipeline orchestration
- System health validation
- Production deployment best practices

**What You'll Learn:**
- Combine multiple models for better predictions
- Build automated analytics workflows
- Validate system health before execution
- Deploy production-ready pipelines

**Key Methods:** `ModelEnsemble`, `Pipeline`, `IntegrationValidator`, `check_system_health()`

**Key Insight:** Ensembles typically improve accuracy by 5-15% over individual models

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install jupyter notebook
```

### 2. Start Jupyter
```bash
cd notebooks
jupyter notebook
```

### 3. Open First Tutorial
- Open `01_quick_start_player_analysis.ipynb`
- Run cells sequentially (Shift+Enter)
- Follow the guided explanations

---

## Learning Path

### For Beginners
1. Start with **Notebook 01** (Quick Start)
2. Move to **Notebook 06** (Ensembles & Integration)
3. Explore **Notebook 02** (Panel Data) when ready

### For Data Scientists
1. Review **Notebook 01** for syntax familiarity
2. Dive into **Notebooks 02-05** based on your use case:
   - Panel data econometrics → **02**
   - Real-time systems → **03**
   - Causal inference → **04**
   - Predictive modeling → **05**
3. Master **Notebook 06** for production workflows

### For Specific Use Cases
- **Forecasting:** Notebooks 01, 06
- **Player Comparison:** Notebooks 02, 05
- **Live Analytics:** Notebook 03
- **Treatment Effects:** Notebook 04
- **Contract Decisions:** Notebook 05
- **Production Deployment:** Notebook 06

---

## Common Code Patterns

### Load and Analyze Time Series
```python
from mcp_server.time_series import TimeSeriesAnalyzer

# Create analyzer
analyzer = TimeSeriesAnalyzer(data=df, target_column='points')

# Test for stationarity
adf_result = analyzer.adf_test()

# Detect trend
trend = analyzer.detect_trend()

# Forecast
forecast = analyzer.forecast(steps=20)
```

### Panel Data Analysis
```python
from mcp_server.panel_data import PanelDataAnalyzer

# Create analyzer
panel = PanelDataAnalyzer(
    data=df,
    entity_col='player_id',
    time_col='season'
)

# Fixed effects regression
fe_result = panel.fixed_effects(formula='points ~ age + minutes')

# Hausman test
hausman = panel.hausman_test(formula='points ~ age + minutes')
```

### Create Model Ensemble
```python
from mcp_server.integration import create_ensemble, EnsembleMethod

# Train individual models
arima_model = ARIMAForecaster().fit(data)
prophet_model = ProphetForecaster().fit(data)

# Create weighted ensemble
ensemble = create_ensemble(
    models={'ARIMA': arima_model, 'Prophet': prophet_model},
    method=EnsembleMethod.WEIGHTED_AVERAGE
)

# Generate predictions
predictions = ensemble.predict(X, return_details=True)
```

### Build Analytics Pipeline
```python
from mcp_server.integration import Pipeline

# Create pipeline
pipeline = Pipeline("Forecast Workflow")

# Add stages
pipeline.add_stage('load', load_data, outputs=['data'])
pipeline.add_stage('model', train_model, inputs=['data'], depends_on=['load'])
pipeline.add_stage('eval', evaluate, inputs=['model'], depends_on=['model'])

# Execute
result = pipeline.execute()
print(result.summary())
```

---

## Performance

All methods are optimized for production use:

| Operation | Latency | Notes |
|-----------|---------|-------|
| ARIMA forecast | ~50-100ms | Per model |
| Panel data regression | ~100-200ms | Fixed/random effects |
| Causal inference (PSM) | ~200-400ms | Depends on sample size |
| Particle filter update | ~5-10ms | Per observation |
| Survival analysis | ~150-300ms | Cox/AFT models |
| Ensemble prediction | ~5-10ms | Per ensemble |
| Pipeline execution | ~50-100ms | Overhead per pipeline |

**Real-time capable:** Most operations complete in <100ms

---

## Troubleshooting

### Import Errors
```python
# If you get ImportError, add project root to path:
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

# Now imports should work:
from mcp_server.time_series import TimeSeriesAnalyzer
```

### Missing Dependencies
```bash
# Install optional dependencies for specific notebooks:
pip install prophet  # For Prophet forecasting
pip install statsmodels  # For advanced econometrics
pip install scikit-learn  # For ML integration
```

### Kernel Crashes
```bash
# If kernel crashes, increase memory:
jupyter notebook --NotebookApp.max_buffer_size=1000000000

# Or restart kernel: Kernel → Restart & Run All
```

### Visualization Issues
```python
# If plots don't render, try:
%matplotlib inline
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (14, 6)
```

---

## Additional Documentation

### Core Documentation
- **[Getting Started](../docs/GETTING_STARTED.md)** - Installation and setup guide
- **[Quick Reference](../docs/QUICK_REFERENCE.md)** - API cheat sheet for all 50+ methods
- **[API Reference](../docs/API_REFERENCE.md)** - Complete API documentation
- **[Tutorial](../docs/tutorials/COMPLETE_WORKFLOW_TUTORIAL.md)** - Comprehensive workflow guide

### Technical Documentation
- **[Agent 19 Summary](../docs/plans/AGENT19_FINAL_COMPLETION.md)** - Integration framework details
- **[Phase 10B Summary](../docs/plans/PHASE10B_COMPLETION_SUMMARY.md)** - Full system overview

---

## Tips for Best Results

### Data Preparation
- Clean data before analysis (handle missing values, outliers)
- Use consistent date formats for time series
- Ensure entity IDs are unique for panel data
- Verify data types match method expectations

### Model Selection
- Start with simple methods (ARIMA, fixed effects)
- Use diagnostic tests to guide model choice
- Try ensembles when single models underperform
- Validate results with out-of-sample testing

### Production Deployment
- Test on sample data first
- Run health checks before execution
- Monitor performance over time
- Re-train models periodically

### Getting Help
- Check notebook cell outputs for error messages
- Review method docstrings: `help(TimeSeriesAnalyzer)`
- Consult quick reference guide for syntax
- Run integration tests to verify setup

---

## Notebook Execution Tips

### Running All Cells
```bash
# Run entire notebook from command line:
jupyter nbconvert --execute --to notebook --inplace notebook.ipynb
```

### Exporting Results
```bash
# Export to HTML for sharing:
jupyter nbconvert --to html notebook.ipynb

# Export to PDF (requires pandoc + LaTeX):
jupyter nbconvert --to pdf notebook.ipynb
```

### Clearing Outputs
```bash
# Clear all outputs before committing:
jupyter nbconvert --clear-output --inplace notebook.ipynb
```

---

## What's Next?

After completing these tutorials:

1. **Apply to Real Data:** Use actual NBA statistics from your database
2. **Build Custom Pipelines:** Combine methods for your specific use case
3. **Deploy to Production:** Set up automated workflows
4. **Extend the Platform:** Add new methods or customize existing ones

---

## Feedback & Support

### Found an Issue?
- Check the troubleshooting section above
- Review the documentation in `../docs/`
- Open an issue on GitHub with:
  - Notebook name and cell number
  - Error message and stack trace
  - Your Python environment details

### Want to Contribute?
Contributions welcome! See project repository for guidelines.

---

**Last Updated:** January 2025
**Total Notebooks:** 6
**Total Tutorial Time:** ~2 hours
**Difficulty Range:** Beginner to Advanced

---

**NBA MCP Analytics Platform - Making Advanced Analytics Accessible** ✅
