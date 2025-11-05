# Claude Desktop + NBA MCP Quick Reference

## 🚀 Quick Start Prompts

Copy and paste these into Claude Desktop after MCP is configured:

### 1. Test Connection
```
Can you check if you have access to the NBA MCP server?
Try listing the available tables.
```

### 2. Explore Database
```
Using the MCP, show me:
1. How many tables are available
2. The schema of the 'games' table
3. A count of total games in the database
```

### 3. Simple Query
```
Using the MCP, query the games table and show me the first 5 games.
```

---

## 📊 Common Queries

### Player Statistics
```
Using the MCP, query player statistics:
- Get top 10 scorers from the 2023 season
- Show their average points, rebounds, and assists
```

### Team Analysis
```
Using the MCP, analyze team performance:
- List all teams in the database
- Show win-loss records for the 2023 season
```

### Game Data
```
Using the MCP:
1. Count total games in the database
2. Show date range of available games
3. List games from the last 7 days
```

---

## 🧪 Testing Phase 2 Methods

### Time Series Analysis
```
I want to forecast player scoring using the new Phase 2 time series methods:

1. Use MCP to query scoring data for LeBron James (last 5 seasons)
2. Apply ARIMAX forecasting from the econometric suite
3. Show predictions with confidence intervals
```

### Dynamic Panel GMM
```
I want to analyze scoring persistence using Arellano-Bond GMM:

1. Query player-season panel data (at least 50 players, 5+ seasons each)
2. Use the difference_gmm() method from panel_data.py
3. Interpret the AR(2) test (should be > 0.05)
4. Interpret the Hansen J-test (should be 0.10 < p < 0.95)
5. Explain what the persistence coefficient means
```

### Survival Analysis
```
Using the MCP and Phase 2 survival methods:

1. Query player career data (debut year, retirement year, position)
2. Analyze career longevity using Fine-Gray competing risks model
3. Compare survival rates across positions (Guard vs Forward vs Center)
```

### Causal Inference
```
I want to estimate the causal effect of coaching changes:

1. Use MCP to identify teams with coaching changes
2. Apply doubly robust matching from causal_inference.py
3. Estimate the treatment effect on win percentage
4. Show confidence intervals
```

---

## 🎯 Phase 2 Method Cheat Sheet

### Available Methods via Econometric Suite

#### Causal Inference
- `kernel_matching` - Kernel propensity score matching
- `radius_matching` - Radius matching with caliper
- `doubly_robust` - Doubly robust estimation

#### Time Series
- `arimax` - ARIMA with exogenous variables
- `varmax` - Vector ARMA with exog
- `mstl` - Multiple seasonal decomposition
- `stl` - Enhanced STL decomposition
- `johansen` - Cointegration test
- `granger` - Granger causality
- `var` - Vector autoregression
- `vecm` - Vector error correction model

#### Survival Analysis
- `fine_gray` - Competing risks model
- `frailty` - Frailty (random effects) model
- `cure` - Cure rate model
- `recurrent` - Recurrent events model

#### Econometric Tests
- `structural_breaks` - CUSUM and Hansen tests
- `breusch_godfrey` - Autocorrelation test
- `heteroscedasticity` - Breusch-Pagan and White tests

#### Dynamic Panel GMM (NEW!)
- `first_diff` - First-difference OLS
- `diff_gmm` - Arellano-Bond Difference GMM
- `sys_gmm` - Blundell-Bond System GMM
- `gmm_diagnostics` - AR(1), AR(2), Hansen tests

---

## 💡 Pro Tips

### 1. Always Mention "MCP"
```
✅ "Using the MCP, query..."
✅ "Via MCP, show me..."
❌ "Query the database..."  (too vague)
```

### 2. Be Specific About Data Structure
```
✅ "Query player-season panel data with columns: player_id, season, points, minutes"
✅ "Get time series data for player X from 2018-2023"
❌ "Get some player data"
```

### 3. Request Step-by-Step
```
✅ "First query the data, then apply the GMM method, then interpret results"
❌ "Analyze everything at once"
```

### 4. Ask for Diagnostics
```
✅ "Show me the AR(2) test, Hansen test, and coefficient interpretation"
✅ "Include confidence intervals and statistical significance"
```

---

## 🔍 Debugging Prompts

### If MCP isn't working:
```
What tools do you currently have available?
Can you see any tools with 'database' or 'query' in the name?
```

### If queries fail:
```
Can you show me the exact SQL query you're trying to run?
Let's test with a simple COUNT(*) first.
```

### If methods aren't found:
```
Can you list what methods are available in the econometric_suite.py file?
Show me the panel_analysis() method signature.
```

---

## 📈 Example Workflows

### Workflow 1: Player Performance Analysis
```
Let's analyze LeBron James' scoring trends:

Step 1: Using MCP, query his season-by-season stats (points, games, minutes)
Step 2: Apply ARIMAX forecasting from the econometric suite
Step 3: Forecast next season's scoring
Step 4: Visualize the trend and predictions

Can you do this analysis?
```

### Workflow 2: Team Dynasty Detection
```
I want to identify team dynasties using survival analysis:

Step 1: Using MCP, query team win percentages by season
Step 2: Define "dynasty" as 5+ consecutive seasons above 0.600 win%
Step 3: Use survival analysis to model dynasty duration
Step 4: Identify factors that extend dynasty length

Can you help with this?
```

### Workflow 3: Coaching Impact Analysis
```
Let's estimate coaching change impacts:

Step 1: Using MCP, identify all coaching changes (2015-2023)
Step 2: Get team performance before/after each change
Step 3: Use doubly robust matching from causal_inference.py
Step 4: Estimate average treatment effect
Step 5: Test for heterogeneous effects (by team market size)

Can you walk through this analysis?
```

### Workflow 4: Scoring Persistence (GMM)
```
I want to measure scoring persistence using dynamic panel GMM:

Step 1: Using MCP, query player-season data:
   - player_id, season, points, minutes, age, position
   - Filter: players with 5+ seasons, 20+ minutes per game

Step 2: Use difference_gmm() method:
   - Formula: points ~ lag(points, 1) + minutes + age
   - GMM type: two_step
   - Max lags: 3
   - Collapse: True

Step 3: Interpret results:
   - Check AR(2) test (p > 0.05 indicates valid specification)
   - Check Hansen J-test (0.10 < p < 0.95 indicates valid instruments)
   - Interpret persistence coefficient

Can you execute this complete analysis?
```

---

## 🎓 Learning Path

### Level 1: Basic Queries
1. List tables
2. Get table schema
3. Simple SELECT queries
4. COUNT, AVG aggregations

### Level 2: Join Queries
1. Join players + teams
2. Join games + player_game_stats
3. Multi-table analysis

### Level 3: Time Series
1. Query time-ordered data
2. Apply ARIMA forecasting
3. Interpret predictions

### Level 4: Panel Data
1. Structure panel data (entity-time)
2. Apply fixed effects
3. Use GMM methods

### Level 5: Advanced Methods
1. Causal inference
2. Survival analysis
3. Spatial econometrics
4. Bayesian methods

---

## 📞 Getting Help

### In Claude Desktop, Ask:
```
Can you explain how to use the [METHOD_NAME] from the econometric suite?
What are the parameters for the difference_gmm() method?
Show me an example of querying panel data for GMM analysis.
```

### Check Documentation:
- Setup Guide: `CLAUDE_DESKTOP_MCP_SETUP.md`
- Method Docs: `mcp_server/panel_data.py` (docstrings)
- Examples: `examples/` directory

---

## 🚀 Ready to Go!

Once Claude Desktop is configured with MCP access:

1. ✅ Start with simple queries (list tables, count games)
2. ✅ Progress to joins and aggregations
3. ✅ Try Phase 2 methods (GMM, survival analysis)
4. ✅ Build complex workflows

**Have fun analyzing 44,828 NBA games!** 🏀
