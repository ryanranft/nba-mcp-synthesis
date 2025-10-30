# NBA Analytics Examples

This directory contains demonstration notebooks and scripts showcasing the econometric methods implemented in the NBA MCP Synthesis project.

## Available Demos

### Phase 2 NBA Analytics Demo

**File**: `phase2_nba_analytics_demo.ipynb`

**Description**: Comprehensive demonstration of all 23 Phase 2 econometric methods using NBA data.

**Methods Demonstrated**:

#### Day 1 - Causal Inference (3 methods)
1. **Kernel Matching** - Weighted matching with kernel smoothing
2. **Radius Matching** - Caliper matching within distance threshold
3. **Doubly Robust Estimation** - Combined propensity score and outcome modeling

#### Day 2 - Time Series (4 methods)
4. **ARIMAX** - ARIMA with exogenous variables
5. **VARMAX** - Vector ARMA with exogenous variables
6. **MSTL** - Multiple Seasonal-Trend decomposition
7. **STL** - Enhanced STL decomposition

#### Day 3 - Survival Analysis (4 methods)
8. **Fine-Gray** - Competing risks regression
9. **Frailty Models** - Shared frailty by team
10. **Cure Models** - Mixture cure model
11. **Recurrent Events** - PWP/AG/WLW models

#### Day 4 - Advanced Time Series (4 methods)
12. **Johansen Cointegration Test** - Test for long-run equilibrium
13. **Granger Causality Test** - Test for temporal causation
14. **VAR** - Vector Autoregression
15. **Time Series Diagnostics** - Residual analysis

#### Day 5 - Econometric Tests (4 methods)
16. **VECM** - Vector Error Correction Model
17. **Structural Breaks** - Change point detection
18. **Breusch-Godfrey Test** - Autocorrelation testing
19. **Heteroscedasticity Tests** - Variance stability testing

#### Day 6 - Dynamic Panel GMM (4 methods)
20. **First-Difference OLS** - Basic difference-in-difference
21. **Difference GMM** - Arellano-Bond estimator
22. **System GMM** - Blundell-Bond estimator
23. **GMM Diagnostics** - AR(2), Hansen J-tests

**Total**: 23 methods across 6 categories

## Running the Notebooks

### Prerequisites

1. Install required packages:
```bash
pip install -r ../requirements.txt
```

2. Ensure MCP server is configured (for real data):
```bash
# Check MCP connection
python -c "from mcp_server import query_database; print('MCP OK')"
```

### Launch Jupyter

```bash
jupyter notebook phase2_nba_analytics_demo.ipynb
```

Or use JupyterLab:
```bash
jupyter lab phase2_nba_analytics_demo.ipynb
```

### Running All Cells

In Jupyter:
1. Click "Kernel" → "Restart & Run All"
2. Wait for all cells to execute
3. Review results and visualizations

### Demo vs Production

**Current State**: The notebook uses synthetic NBA-like data for demonstration.

**For Production**: Replace the `load_demo_data()` function with actual MCP queries:

```python
# Replace synthetic data with:
def load_real_data():
    from mcp_server.cli import query_database

    sql = """
    SELECT
        h.game_id,
        h.game_date,
        h.athlete_id as player_id,
        h.team_id,
        h.minutes,
        h.points,
        h.assists,
        h.rebounds
    FROM hoopr_player_box h
    WHERE h.game_date >= '2018-01-01'
    ORDER BY h.game_date
    """

    return query_database(sql)
```

## Key Research Questions

Each section addresses real NBA analytics questions:

1. **Causal Inference**: Does draft position cause better performance?
2. **Time Series**: Can we forecast player scoring with context?
3. **Survival Analysis**: What affects NBA career length?
4. **Advanced Time Series**: How do team stats interact over time?
5. **Econometric Tests**: How can we validate our models?
6. **Dynamic Panel GMM**: Does past performance predict future performance?

## Interpreting Results

### Causal Methods
- **ATE (Average Treatment Effect)**: The causal impact of treatment
- **Std Error**: Uncertainty in the estimate
- **Confidence**: Lower standard errors indicate more precise estimates

### Time Series
- **AIC/BIC**: Lower values indicate better model fit
- **Residuals**: Should be random (white noise) if model is correctly specified
- **Forecasts**: Include uncertainty intervals

### Survival Analysis
- **Hazard Ratios**: >1 means higher risk, <1 means lower risk
- **P-values**: <0.05 indicates statistical significance
- **Survival Curves**: Visual representation of time-to-event

### Panel GMM
- **AR(2) Test**: Should NOT reject (p > 0.05)
- **Hansen J**: Should be 0.10 < p < 0.95
- **Coefficients**: Estimate persistence/momentum effects

## Visualizations

The notebook includes:
- Treatment effect comparisons
- Time series decompositions
- Survival curves
- Model diagnostic plots
- Method comparison charts

## Performance Notes

**Computation Time**:
- Full notebook: ~5-10 minutes (synthetic data)
- With real MCP data: ~15-30 minutes (depending on query size)

**Memory Requirements**:
- Synthetic data: ~100 MB
- Real data: ~500 MB - 2 GB

**Recommended Setup**:
- RAM: 8 GB minimum, 16 GB preferred
- CPU: Multi-core processor (4+ cores)
- Python: 3.9+

## Troubleshooting

### MCP Connection Issues
```python
# Test MCP connectivity
from mcp_server import list_tables
tables = list_tables()
print(f"Found {len(tables)} tables")
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r ../requirements.txt --force-reinstall
```

### pydynpd Issues (GMM methods)
```bash
# Check if pydynpd is installed
pip show pydynpd

# If needed, reinstall
pip install pydynpd>=0.2.1
```

### NumPy 2.0 Compatibility
If you see `np.NaN` errors with pydynpd, apply the patch:
```bash
# See PHASE2_DAY6_SUMMARY.md for patch instructions
sed -i '' 's/np\.NaN/np.nan/g' [pydynpd files]
```

## Next Steps

After running the demo:

1. **Customize for Your Analysis**:
   - Modify research questions
   - Adjust model parameters
   - Add specific visualizations

2. **Integrate Real Data**:
   - Replace synthetic data with MCP queries
   - Validate results with domain knowledge
   - Add data quality checks

3. **Extend Methods**:
   - Combine multiple approaches
   - Add cross-validation
   - Implement model averaging

4. **Production Deployment**:
   - Create automated pipelines
   - Add logging and monitoring
   - Implement result caching

## References

- **Phase 2 Summary**: `../PHASE2_DAY6_SUMMARY.md`
- **Method Documentation**: `../mcp_server/econometric_suite.py`
- **Installation Guide**: `../README.md`
- **MCP Setup**: `../README_CLAUDE_DESKTOP_MCP.md`

## Support

For issues or questions:
1. Check the main project README
2. Review method docstrings in source code
3. Consult Phase 2 summary documentation

---

**Created**: October 26, 2025
**Phase**: 2 Complete (23 methods)
**Status**: Production ready with real MCP data integration
