# Advanced Analytics Tools - Quick Reference Guide

**NBA MCP Synthesis System - Sprint 6 Tools**
**55 Total Tools | 18 Advanced Analytics Tools**

---

## 📊 Tool Categories

### 1. Correlation & Regression (6 tools)
- Analyze relationships between variables
- Build predictive models
- Make forecasts

### 2. Time Series Analysis (6 tools)
- Detect trends and patterns
- Smooth data fluctuations
- Measure consistency

### 3. Advanced NBA Metrics (6 tools)
- Four Factors analysis
- Advanced percentage stats
- Professional-grade metrics

---

## 🔍 Correlation & Regression Tools

### `stats_correlation` - Pearson Correlation

**What it does**: Measures how strongly two variables are related

**When to use**:
- "Does usage rate affect efficiency?"
- "Are points and assists correlated?"
- "Do 3PA and TS% move together?"

**Returns**: Number from -1 to 1
- `1.0` = Perfect positive (both increase together)
- `0.0` = No relationship
- `-1.0` = Perfect negative (one increases, other decreases)

**Example**:
```
Usage Rate: [20, 25, 28, 22, 30]
PER:        [18, 20, 19, 17, 21]
Correlation: 0.72 (moderate positive)
```

---

### `stats_linear_regression` - Build Prediction Model

**What it does**: Finds the best-fit line through your data

**When to use**:
- "Predict points based on minutes"
- "Forecast future performance"
- "Model relationships"

**Returns**:
```
{
  "slope": 0.6,           # Points per minute
  "intercept": 0.0,       # Starting point
  "r_squared": 0.99,      # How well it fits (0-1)
  "equation": "y = 0.6x + 0.0"
}
```

**Interpretation**:
- R² > 0.7 = Strong relationship
- R² 0.4-0.7 = Moderate
- R² < 0.4 = Weak

---

### `stats_predict` - Make Predictions

**What it does**: Uses your model to predict new values

**Example**:
```
Model: y = 0.6x + 0.0
If x = 32 minutes
Prediction: 19.2 points
```

---

### `stats_correlation_matrix` - Multi-Variable Analysis

**What it does**: Shows correlations between all pairs of variables

**When to use**:
- "Which stats are related?"
- "Find hidden patterns"
- "Multivariate analysis"

**Example**:
```
Variables: points, assists, rebounds
Matrix shows correlation between each pair
```

---

## 📈 Time Series Tools

### `stats_moving_average` - Smooth Data

**What it does**: Averages recent values to remove noise

**When to use**:
- "Remove game-to-game volatility"
- "See underlying trends"
- "Smooth erratic data"

**Example**:
```
Game Points: [18, 22, 19, 25, 21, 24]
3-Game MA:   [None, None, 19.67, 22.0, 21.67, 23.33]
```

**Window Size**:
- 3 games = Responsive to changes
- 5 games = Smoother, less responsive
- 10 games = Very smooth

---

### `stats_trend_detection` - Find Patterns

**What it does**: Identifies if performance is improving, declining, or stable

**When to use**:
- "Is player improving?"
- "Are we declining?"
- "What's the trajectory?"

**Returns**:
```
{
  "trend": "increasing",    # or "decreasing" or "stable"
  "slope": 1.8,             # Points per game change
  "confidence": 0.95        # How sure (R²)
}
```

**Confidence Guide**:
- > 0.9 = Very confident
- 0.7-0.9 = Moderately confident
- < 0.7 = Low confidence

---

### `stats_percent_change` - Period Change

**What it does**: Calculates % change from one period to another

**Examples**:
```
Last month: 22 PPG
This month: 24.5 PPG
Change: +11.36%

Last season: 18 PER
This season: 22 PER
Change: +22.22%
```

---

### `stats_growth_rate` - Compound Growth (CAGR)

**What it does**: Average growth rate over multiple periods

**When to use**:
- "Average improvement per year?"
- "Sustained growth rate?"
- "Career progression?"

**Example**:
```
Year 1: 15.0 PPG
Year 4: 25.0 PPG
CAGR: 13.57% per year
```

---

### `stats_volatility` - Consistency Measure

**What it does**: Measures how consistent performance is

**Returns**: Percentage (lower = more consistent)
- < 15% = Very consistent
- 15-30% = Moderate volatility
- > 30% = Highly volatile

**Example**:
```
Consistent player: [20, 21, 19, 20, 21] → 5% volatility
Streaky player:    [15, 28, 12, 25, 18] → 35% volatility
```

---

## 🏀 Advanced NBA Metrics

### `nba_four_factors` - Complete Team Analysis

**Dean Oliver's Four Factors** (in order of importance):

1. **Shooting (eFG%)** - Most important (40%)
   - Good: > 52%
   - Average: 48-52%
   - Poor: < 48%

2. **Turnovers (TOV%)** - Very important (25%)
   - Good: < 12%
   - Average: 12-16%
   - Poor: > 16%

3. **Rebounding (ORB%/DRB%)** - Important (20%)
   - ORB%: > 25% good
   - DRB%: > 75% good

4. **Free Throws (FTR)** - Moderately important (15%)
   - FTR = FTA/FGA
   - Good: > 0.25

**When to use**:
- "Why are we winning/losing?"
- "What's our biggest weakness?"
- "Compare team strengths"

---

### `nba_turnover_percentage` - Ball Security

**Formula**: TOV% = 100 × TOV / (FGA + 0.44×FTA + TOV)

**Benchmarks**:
- < 12% = Excellent (elite ball handlers)
- 12-14% = Good
- 14-16% = Average
- > 16% = Poor (turnover prone)

**NBA Leaders**: Usually 10-11%

---

### `nba_assist_percentage` - Playmaking

**What it measures**: % of teammate FGs assisted while on court

**Benchmarks**:
- > 30% = Elite playmaker (CP3, Harden)
- 20-30% = Good playmaker
- 15-20% = Average
- < 15% = Low assist rate

**Use for**: Evaluating playmaking ability

---

### `nba_steal_percentage` - Defensive Pressure

**What it measures**: Steals per 100 opponent possessions

**Benchmarks**:
- > 3% = Elite (All-Defensive level)
- 2-3% = Good
- 1-2% = Average
- < 1% = Low

**Top defenders**: 3-4% STL%

---

### `nba_block_percentage` - Rim Protection

**What it measures**: % of opponent 2PA blocked while on court

**Benchmarks**:
- > 6% = Elite rim protector
- 4-6% = Good rim protector
- 2-4% = Average
- < 2% = Low

**Top centers**: 6-8% BLK%

---

## 🎯 Common Workflows

### Workflow 1: Player Scouting

```
1. Get player season stats
2. Calculate correlation between usage and efficiency
3. Run trend detection on monthly performance
4. Calculate volatility (consistency)
5. Compare AST%, STL%, BLK% to position averages
```

### Workflow 2: Team Analysis

```
1. Calculate Four Factors (offensive & defensive)
2. Compare to league averages
3. Identify biggest strength/weakness
4. Track improvement trend over season
5. Build regression model for wins
```

### Workflow 3: Performance Prediction

```
1. Get historical performance data
2. Detect trend (improving/declining)
3. Build regression model
4. Make predictions for next period
5. Calculate confidence (R²)
```

### Workflow 4: Consistency Analysis

```
1. Get game-by-game stats
2. Calculate moving average (smooth data)
3. Calculate volatility (consistency score)
4. Compare to peer group
5. Identify streaky vs consistent players
```

---

## 📊 Formula Reference

### Correlation
```
r = Σ[(x - x̄)(y - ȳ)] / √[Σ(x - x̄)² × Σ(y - ȳ)²]
```

### Linear Regression
```
Slope (m) = Σ[(x - x̄)(y - ȳ)] / Σ[(x - x̄)²]
Intercept (b) = ȳ - m × x̄
```

### R² (Goodness of Fit)
```
R² = 1 - (SS_residual / SS_total)
```

### Exponential Moving Average
```
EMA[t] = α × data[t] + (1-α) × EMA[t-1]
```

### Compound Growth Rate
```
CAGR = ((end_value / start_value)^(1/periods) - 1) × 100
```

### Volatility (Coefficient of Variation)
```
CV = (Std Dev / Mean) × 100
```

### Four Factors

**eFG%** (Effective Field Goal %):
```
eFG% = (FGM + 0.5 × 3PM) / FGA
```

**TOV%** (Turnover %):
```
TOV% = 100 × TOV / (FGA + 0.44×FTA + TOV)
```

**ORB%** (Offensive Rebound %):
```
ORB% = 100 × ORB / (Team ORB + Opp DRB)
```

**FTR** (Free Throw Rate):
```
FTR = FTA / FGA
```

---

## 💡 Pro Tips

### Correlation Analysis
- Always visualize (scatterplot) before assuming linear
- Correlation ≠ causation
- Check for outliers that skew results
- Use correlation matrix for multivariate

### Trend Detection
- Need at least 5-10 data points
- Higher confidence (R²) = more reliable trend
- Consider external factors (injuries, trades)
- Combine with domain knowledge

### Prediction
- R² > 0.7 needed for reliable predictions
- Don't extrapolate too far beyond data
- Update model with new data regularly
- Consider confidence intervals

### Time Series
- Larger window = smoother but less responsive
- EMA better for detecting recent changes
- MA better for identifying long-term trends
- Always check for seasonality

### NBA Metrics
- Compare to position averages, not league
- Context matters (pace, era, role)
- Use multiple metrics together
- Four Factors weight: Shoot > TO > Reb > FT

---

## 🔗 Related Tools

### Basic Stats (from Sprint 5)
- `stats_mean` - Average
- `stats_median` - Middle value
- `stats_variance` - Spread
- `stats_summary` - Complete stats

### NBA Metrics (from Sprint 5)
- `nba_player_efficiency_rating` - PER
- `nba_true_shooting_percentage` - TS%
- `nba_effective_field_goal_percentage` - eFG%
- `nba_usage_rate` - USG%

---

## 📚 Learn More

### Correlation & Regression
- Understand R² and p-values
- Know when to use linear vs non-linear
- Learn about multivariate regression

### Time Series
- Moving average types (SMA, EMA, WMA)
- Trend decomposition
- Seasonal patterns

### NBA Analytics
- Dean Oliver's "Basketball on Paper"
- Basketball Reference glossary
- NBA.com/stats methodology

---

**Total Analytics Tools**: 18 (Sprint 6) + 20 (Sprint 5) = 38 analytics tools
**System Total**: 55 MCP tools

**Ready to use!** All tools tested and validated. See `SPRINT_6_COMPLETE.md` for implementation details.
