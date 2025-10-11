# Sprint 6: Advanced Analytics Tools - Planning Document

**Created**: October 10, 2025
**Status**: PLANNING
**Estimated Effort**: 2-3 hours
**Dependencies**: Sprint 5 Complete ✅

---

## 🎯 Sprint Objectives

Build on Sprint 5's foundation to add **15-20 advanced analytical tools** enabling:
- Correlation and regression analysis
- Time series trend detection
- Advanced NBA metrics (Four Factors, adjusted ratings)
- Predictive capabilities

### Success Criteria
- [ ] 15-20 new tools implemented
- [ ] 100% test coverage
- [ ] Comprehensive documentation
- [ ] Real-world workflow examples
- [ ] Performance < 0.01s per operation

---

## 📊 Proposed Tools (18 total)

### Category 1: Correlation & Regression (6 tools)

#### 1. `stats_correlation` - Pearson Correlation
**Purpose**: Measure linear relationship between two variables

**Formula**: `r = Σ[(x - x̄)(y - ȳ)] / √[Σ(x - x̄)² × Σ(y - ȳ)²]`

**Parameters**:
- `x` (list): First variable
- `y` (list): Second variable

**Returns**: Correlation coefficient (-1 to 1)

**Use Case**: "Does usage rate correlate with efficiency?"
```python
usage_rates = [20, 25, 28, 22, 30]
per_values = [18, 20, 19, 17, 21]
correlation = stats_correlation(usage_rates, per_values)
# Returns: 0.72 (moderate positive correlation)
```

#### 2. `stats_covariance` - Covariance
**Purpose**: Measure how two variables vary together

**Formula**: `Cov(X,Y) = Σ[(x - x̄)(y - ȳ)] / (n-1)`

**Parameters**:
- `x` (list): First variable
- `y` (list): Second variable
- `sample` (bool): Sample vs population (default: True)

**Returns**: Covariance value

**Use Case**: "How do points and assists vary together?"

#### 3. `stats_linear_regression` - Simple Linear Regression
**Purpose**: Fit y = mx + b model to data

**Returns**:
```python
{
    "slope": float,
    "intercept": float,
    "r_squared": float,
    "equation": str
}
```

**Use Case**: "Predict points based on minutes played"
```python
minutes = [20, 25, 30, 35, 40]
points = [12, 15, 18, 21, 24]
model = stats_linear_regression(minutes, points)
# Returns: {"slope": 0.6, "intercept": 0, "r_squared": 0.99}
```

#### 4. `stats_predict` - Make Predictions
**Purpose**: Use regression model to predict new values

**Parameters**:
- `slope` (float): Model slope
- `intercept` (float): Model intercept
- `x_values` (list): New x values to predict

**Returns**: List of predicted y values

**Use Case**: "If player plays 32 minutes, predicted points?"

#### 5. `stats_r_squared` - Coefficient of Determination
**Purpose**: Measure how well regression fits data

**Returns**: R² value (0 to 1)

**Use Case**: "How well does minutes predict points?"

#### 6. `stats_correlation_matrix` - Correlation Matrix
**Purpose**: Calculate correlations between multiple variables

**Parameters**:
- `data` (dict): Dictionary of variable name → list of values

**Returns**: Matrix of correlations

**Use Case**: "Correlations between points, rebounds, assists"

---

### Category 2: Time Series Analysis (6 tools)

#### 7. `stats_moving_average` - Moving Average
**Purpose**: Smooth out short-term fluctuations

**Parameters**:
- `data` (list): Time series data
- `window` (int): Window size (default: 3)

**Returns**: Smoothed data

**Use Case**: "3-game moving average of points"
```python
game_points = [18, 22, 19, 25, 21, 24]
smoothed = stats_moving_average(game_points, window=3)
# Returns: [None, None, 19.67, 22.0, 21.67, 23.33]
```

#### 8. `stats_exponential_moving_average` - EMA
**Purpose**: Weighted moving average (recent data more important)

**Parameters**:
- `data` (list): Time series data
- `alpha` (float): Smoothing factor (0-1, default: 0.3)

**Returns**: Exponentially smoothed data

**Use Case**: "Detect if player is heating up"

#### 9. `stats_trend_detection` - Trend Analysis
**Purpose**: Identify if data is trending up, down, or stable

**Returns**:
```python
{
    "trend": "increasing|decreasing|stable",
    "slope": float,
    "confidence": float
}
```

**Use Case**: "Is player improving over season?"
```python
ppg_by_month = [18, 19, 21, 23, 25]
trend = stats_trend_detection(ppg_by_month)
# Returns: {"trend": "increasing", "slope": 1.8, "confidence": 0.95}
```

#### 10. `stats_percent_change` - Percentage Change
**Purpose**: Calculate period-over-period change

**Parameters**:
- `current` (float): Current value
- `previous` (float): Previous value

**Returns**: Percentage change

**Use Case**: "How much did PPG improve this month?"

#### 11. `stats_growth_rate` - Compound Growth Rate
**Purpose**: Calculate average growth rate over time

**Parameters**:
- `start_value` (float): Initial value
- `end_value` (float): Final value
- `periods` (int): Number of periods

**Returns**: Growth rate per period

**Use Case**: "Player's scoring growth rate over 4 years"

#### 12. `stats_volatility` - Volatility/Stability
**Purpose**: Measure consistency over time (lower = more consistent)

**Formula**: `Volatility = Std Dev / Mean × 100`

**Returns**: Coefficient of variation

**Use Case**: "Which player is more consistent game-to-game?"

---

### Category 3: Advanced NBA Metrics (6 tools)

#### 13. `nba_four_factors` - Four Factors
**Purpose**: Complete offensive and defensive Four Factors

**Four Factors**:
1. Shooting (eFG%)
2. Turnovers (TOV%)
3. Rebounding (ORB% / DRB%)
4. Free Throws (FTR)

**Returns**:
```python
{
    "offensive": {
        "efg_pct": float,
        "tov_pct": float,
        "orb_pct": float,
        "ftr": float
    },
    "defensive": {
        "efg_pct": float,
        "tov_pct": float,
        "drb_pct": float,
        "ftr": float
    }
}
```

**Use Case**: "What's driving team's offensive success?"

#### 14. `nba_turnover_percentage` - TOV%
**Purpose**: Turnovers per 100 possessions

**Formula**: `TOV% = 100 × TOV / (FGA + 0.44 × FTA + TOV)`

**Use Case**: "How careful is player with the ball?"

#### 15. `nba_rebound_percentage` - REB%
**Purpose**: Percentage of rebounds grabbed while on court

**Formula**: `REB% = 100 × (Player REB × Team MP) / (Player MP × (Team REB + Opp REB))`

**Use Case**: "Player's rebounding impact"

#### 16. `nba_assist_percentage` - AST%
**Purpose**: Percentage of teammate FGs assisted

**Formula**: `AST% = 100 × AST / [(MP / 5 × Team FGM) - FGM]`

**Use Case**: "How much does player facilitate?"

#### 17. `nba_steal_percentage` - STL%
**Purpose**: Steals per 100 opponent possessions

**Use Case**: "Player's defensive pressure"

#### 18. `nba_block_percentage` - BLK%
**Purpose**: Block percentage of 2-point attempts

**Use Case**: "Rim protection ability"

---

## 🏗️ Implementation Plan

### Phase 1: Correlation & Regression (1 hour)

**Files to Create**:
1. `mcp_server/tools/correlation_helper.py` (~400 lines)
   - 6 correlation/regression functions
   - Uses numpy-style calculations (pure Python)

2. `mcp_server/tools/params.py` (add ~150 lines)
   - `CorrelationParams` - x, y lists
   - `RegressionParams` - x, y lists
   - `PredictParams` - model params + new x values

3. `mcp_server/responses.py` (add ~30 lines)
   - `CorrelationResult` - correlation coefficient
   - `RegressionResult` - slope, intercept, r²

**Tools to Register**:
- stats_correlation
- stats_covariance
- stats_linear_regression
- stats_predict
- stats_r_squared
- stats_correlation_matrix

### Phase 2: Time Series Analysis (1 hour)

**Files to Create**:
1. `mcp_server/tools/timeseries_helper.py` (~350 lines)
   - 6 time series functions
   - Moving averages, trend detection

2. `mcp_server/tools/params.py` (add ~100 lines)
   - `MovingAverageParams` - data, window
   - `TrendDetectionParams` - data
   - `PercentChangeParams` - current, previous

3. `mcp_server/responses.py` (add ~20 lines)
   - `TimeSeriesResult` - smoothed data
   - `TrendResult` - trend direction, slope

**Tools to Register**:
- stats_moving_average
- stats_exponential_moving_average
- stats_trend_detection
- stats_percent_change
- stats_growth_rate
- stats_volatility

### Phase 3: Advanced NBA Metrics (45 min)

**Files to Modify**:
1. `mcp_server/tools/nba_metrics_helper.py` (add ~250 lines)
   - 6 advanced NBA metric functions
   - Four Factors, advanced percentages

2. `mcp_server/tools/params.py` (add ~120 lines)
   - `FourFactorsParams` - complete team stats
   - `AdvancedPercentageParams` - player + team stats

3. `mcp_server/responses.py` (add ~15 lines)
   - `FourFactorsResult` - offensive & defensive factors

**Tools to Register**:
- nba_four_factors
- nba_turnover_percentage
- nba_rebound_percentage
- nba_assist_percentage
- nba_steal_percentage
- nba_block_percentage

### Phase 4: Testing & Documentation (30 min)

**Files to Create**:
1. `scripts/test_sprint6_features.py` (~600 lines)
   - 50+ automated tests
   - Interactive demo mode

2. `SPRINT_6_GUIDE.md` (~800 lines)
   - Complete tool documentation
   - Formula explanations
   - Usage examples

3. Update `README.md`
   - Add Sprint 6 tools section
   - Update tool count (38 total)

---

## 📐 Technical Specifications

### Dependencies
- **Zero external dependencies** (Python stdlib only)
- Use built-in `math`, `statistics` modules
- Implement numpy-style calculations manually

### Performance Targets
- Correlation: < 0.005s (for 100 data points)
- Regression: < 0.01s (for 100 data points)
- Time series: < 0.01s (for 100 data points)
- NBA metrics: < 0.001s per calculation

### Error Handling
- Validate list lengths match for correlation
- Check for division by zero
- Require minimum data points (e.g., 3 for regression)
- Handle empty lists gracefully

### Logging
- All functions use `@log_operation` decorator
- Structured JSON logging
- Track operation duration

---

## 🎯 Use Cases & Examples

### Use Case 1: Player Development Analysis
```python
# Track player's season progression
season_ppg = [18, 19, 20, 21, 23, 24, 25, 26]

# Detect trend
trend = stats_trend_detection(season_ppg)
# {"trend": "increasing", "slope": 1.2, "confidence": 0.98}

# Smooth with moving average
smoothed = stats_moving_average(season_ppg, window=3)

# Calculate growth rate
growth = stats_growth_rate(18, 26, 8)
# Returns: 5.4% per game
```

### Use Case 2: Identify Shooting Efficiency Predictors
```python
# Does 3-point volume correlate with efficiency?
three_pa_per_game = [6, 8, 10, 7, 9]
ts_pct = [0.55, 0.58, 0.56, 0.54, 0.57]

correlation = stats_correlation(three_pa_per_game, ts_pct)
# Returns: 0.42 (weak positive correlation)

# Build regression model
model = stats_linear_regression(three_pa_per_game, ts_pct)
# Predict TS% for 12 3PA
predicted_ts = stats_predict(model['slope'], model['intercept'], [12])
```

### Use Case 3: Team Four Factors Analysis
```python
# What's driving team's success?
team_stats = {
    "fgm": 3200, "fga": 7000, "three_pm": 1000,
    "tov": 1100, "orb": 900, "drb": 2800,
    "fta": 1800, "opp_fgm": 2900, "opp_fga": 6800,
    ...
}

factors = nba_four_factors(team_stats)

print("Offensive Four Factors:")
print(f"  Shooting (eFG%): {factors['offensive']['efg_pct']:.1%}")
print(f"  Turnovers: {factors['offensive']['tov_pct']:.1%}")
print(f"  Rebounding: {factors['offensive']['orb_pct']:.1%}")
print(f"  Free Throws: {factors['offensive']['ftr']:.3f}")

# Compare to league average
# Identify strengths and weaknesses
```

### Use Case 4: Player Comparison with Correlation Matrix
```python
# Compare multiple stats
player_data = {
    "usage_rate": [20, 25, 22, 28, 24],
    "per": [18, 22, 19, 25, 21],
    "ts_pct": [0.55, 0.58, 0.56, 0.60, 0.57]
}

corr_matrix = stats_correlation_matrix(player_data)
# Shows which stats are related
```

---

## 🧪 Testing Strategy

### Unit Tests (50+ tests)
- Test each function with known inputs/outputs
- Edge cases (empty lists, single values, negative numbers)
- Performance benchmarks

### Integration Tests
- Test tools via MCP server
- Validate parameter models
- Test response models

### Real-World Tests
- Use actual NBA season data
- Compare with Basketball Reference
- Validate formulas produce reasonable results

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Tools Implemented | 18 |
| Test Coverage | 100% |
| Tests Passing | 50+ |
| Documentation | 800+ lines |
| Performance | < 0.01s |
| Dependencies | 0 |

---

## 🚀 Rollout Plan

### Day 1: Implementation
1. Create helper modules (2 hours)
2. Register MCP tools (30 min)
3. Add parameter/response models (30 min)

### Day 2: Testing & Documentation
1. Write test suite (30 min)
2. Create documentation (30 min)
3. Real-world validation (30 min)

### Day 3: Deployment
1. Run all tests
2. Update README
3. Create workflow examples

---

## 🎓 Learning Resources

### Correlation & Regression
- Pearson correlation coefficient
- Simple linear regression (OLS)
- R² interpretation

### Time Series
- Moving averages (SMA, EMA)
- Trend detection algorithms
- Volatility measures

### NBA Metrics
- Dean Oliver's Four Factors
- Basketball Reference formulas
- Advanced percentage calculations

---

## 📝 Open Questions

1. **Correlation Matrix Format**: Return as dict of dicts or 2D array?
2. **Regression**: Support multiple regression or just simple?
3. **Time Series**: Add seasonal decomposition?
4. **NBA Metrics**: Include Win Shares or save for Sprint 7?

---

## 🔄 Next Steps (After Sprint 6)

### Sprint 7: Machine Learning Integration
- Player performance prediction
- Game outcome models
- Player similarity clustering
- Anomaly detection

### Sprint 8: Data Visualization
- Chart generation for trends
- Correlation heatmaps
- Player comparison visualizations
- Export to PNG/PDF

---

## 📋 Checklist

**Before Starting**:
- [x] Sprint 5 complete and validated
- [x] Sprint 6 plan reviewed
- [ ] Confirm 18 tools scope
- [ ] Review formula implementations

**During Implementation**:
- [ ] Create correlation_helper.py
- [ ] Create timeseries_helper.py
- [ ] Update nba_metrics_helper.py
- [ ] Add parameter models
- [ ] Add response models
- [ ] Register 18 tools in fastmcp_server.py
- [ ] Write 50+ tests
- [ ] Create documentation

**After Implementation**:
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Real-world validation
- [ ] Update README
- [ ] Create workflow examples

---

**Document Version**: 1.0
**Status**: PLANNING
**Ready to Implement**: YES
**Estimated Time**: 2-3 hours
**Expected Completion**: October 10, 2025
