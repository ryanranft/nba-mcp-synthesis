# Claude Desktop Integration - Quick Start Guide

**Get all 55 NBA MCP tools working in Claude Desktop in 5 minutes!**

---

## 🎯 What You'll Get

Once configured, you can ask Claude in Claude Desktop:

```
"What are the Lakers' Four Factors this season?"
"Calculate correlation between usage rate and efficiency"
"Detect trend in player's PPG over last 10 games"
"Query the database for top scorers"
"Read the basketball analytics book"
```

Claude will automatically use the 55 MCP tools to answer!

---

## ⚡ 5-Minute Setup

### Step 1: Install Claude Desktop

**Download**: https://claude.ai/download

**Platforms**: macOS, Windows, Linux

---

### Step 2: Configure MCP Server

**Location of config file**:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Create/edit the file** with this configuration:

```json
{
  "mcpServers": {
    "nba-analytics": {
      "command": "python",
      "args": [
        "/FULL/PATH/TO/nba-mcp-synthesis/mcp_server/fastmcp_server.py"
      ],
      "env": {
        "RDS_HOST": "your-db-host.rds.amazonaws.com",
        "RDS_PORT": "5432",
        "RDS_DATABASE": "nba_simulator",
        "RDS_USERNAME": "your-username",
        "RDS_PASSWORD": "your-password",
        "S3_BUCKET": "your-nba-data-bucket",
        "S3_REGION": "us-east-1",
        "GLUE_DATABASE": "nba_data_catalog",
        "GLUE_REGION": "us-east-1"
      }
    }
  }
}
```

**⚠️ Important**:
- Replace `/FULL/PATH/TO/` with your actual path
- Replace all credentials with your actual values
- Use forward slashes `/` even on Windows

---

### Step 3: Find Your Path

**macOS/Linux**:
```bash
cd /path/to/nba-mcp-synthesis
pwd
# Copy this full path
```

**Windows**:
```cmd
cd C:\path\to\nba-mcp-synthesis
cd
# Copy this full path, replace \ with /
```

**Example paths**:
- macOS: `/Users/yourname/projects/nba-mcp-synthesis/mcp_server/fastmcp_server.py`
- Windows: `C:/Users/yourname/projects/nba-mcp-synthesis/mcp_server/fastmcp_server.py`
- Linux: `/home/yourname/projects/nba-mcp-synthesis/mcp_server/fastmcp_server.py`

---

### Step 4: Set Credentials

**Option A: Environment Variables** (Recommended)
```bash
# In your shell config (~/.bashrc, ~/.zshrc, etc.)
export RDS_HOST="your-db-host.rds.amazonaws.com"
export RDS_PORT="5432"
export RDS_DATABASE="nba_simulator"
export RDS_USERNAME="your-username"
export RDS_PASSWORD="your-password"
export S3_BUCKET="your-nba-data-bucket"
export S3_REGION="us-east-1"
```

Then simplify config.json:
```json
{
  "mcpServers": {
    "nba-analytics": {
      "command": "python",
      "args": [
        "/FULL/PATH/TO/nba-mcp-synthesis/mcp_server/fastmcp_server.py"
      ]
    }
  }
}
```

**Option B: Direct in Config** (Simpler but less secure)
- Put credentials directly in `claude_desktop_config.json` "env" section
- Good for testing, not for production

---

### Step 5: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. Look for MCP tools indicator (🔌 icon)

---

## ✅ Verification

### Test 1: List Available Tools

In Claude Desktop, type:
```
What MCP tools are available?
```

**Expected response**: List of 55 tools including database, analytics, and NBA metrics tools

---

### Test 2: Simple Query

```
List the database tables
```

**Expected**: Claude uses `list_tables` tool and shows all NBA database tables

---

### Test 3: Math Calculation

```
Calculate the sum of 10, 20, 30, 40, 50
```

**Expected**: Claude uses `math_sum` tool → Result: 150

---

### Test 4: Stats Analysis

```
Calculate the mean of these points per game: 25, 28, 22, 30, 26
```

**Expected**: Claude uses `stats_mean` tool → Result: 26.2

---

### Test 5: Advanced Analytics

```
Calculate correlation between these two variables:
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]
```

**Expected**: Claude uses `stats_correlation` tool → Result: 1.0 (perfect positive correlation)

---

## 🚀 What You Can Do

### Database Queries

```
"Query the database for top 10 scorers this season"
"Show me all games for the Lakers in 2024"
"What's the schema of the player_stats table?"
```

### Math & Statistics

```
"Calculate mean, median, and standard deviation of: 10, 20, 15, 25, 18"
"What's the variance of these efficiency ratings?"
"Calculate summary statistics for these PPG numbers"
```

### NBA Metrics

```
"Calculate PER for a player with these stats: [provide stats]"
"What's the True Shooting percentage if points=250, FGA=200, FTA=75?"
"Calculate usage rate for these team stats"
```

### Advanced Analytics (Sprint 6!)

**Correlation**:
```
"Find correlation between usage rate and PER"
"Build a regression model predicting points from minutes"
"Calculate correlation matrix for points, assists, rebounds"
```

**Time Series**:
```
"Calculate 3-game moving average for: 18, 22, 19, 25, 21, 24"
"Detect trend in player PPG: 18, 19, 21, 23, 25"
"Calculate growth rate from 15 PPG to 25 PPG over 4 years"
"Measure volatility of game scores: 20, 21, 19, 20, 21"
```

**Advanced NBA Metrics**:
```
"Calculate Four Factors for these team stats"
"What's the turnover percentage with 250 TOV, 1800 FGA, 600 FTA?"
"Calculate assist percentage for a point guard"
"What's the steal percentage for 120 steals?"
```

### File Access

```
"List books available in the system"
"Read the basketball analytics book"
"Search for 'regression' in all books"
```

---

## 📊 All 55 Tools Reference

### Database Tools (3)
- `query_database` - SQL queries
- `list_tables` - Show tables
- `get_table_schema` - Table structure

### File & S3 Tools (4)
- `list_s3_files` - Browse S3
- `list_books` - Available books
- `read_book` - Read books
- `search_books` - Search content

### Pagination Tools (2)
- `list_games` - Browse games
- `list_players` - Browse players

### Math Tools (7 - Sprint 5)
- `math_add`, `math_subtract`, `math_multiply`, `math_divide`
- `math_sum`, `math_round`, `math_modulo`

### Stats Tools (6 - Sprint 5)
- `stats_mean`, `stats_median`, `stats_mode`
- `stats_min_max`, `stats_variance`, `stats_summary`

### NBA Metrics (7 - Sprint 5)
- `nba_player_efficiency_rating` (PER)
- `nba_true_shooting_percentage` (TS%)
- `nba_effective_field_goal_percentage` (eFG%)
- `nba_usage_rate` (USG%)
- `nba_offensive_rating`, `nba_defensive_rating`
- `nba_pace`

### Correlation & Regression (6 - Sprint 6)
- `stats_correlation` - Pearson correlation
- `stats_covariance` - Covariance
- `stats_linear_regression` - Build model
- `stats_predict` - Make predictions
- `stats_correlation_matrix` - Multi-variable

### Time Series (6 - Sprint 6)
- `stats_moving_average` - SMA
- `stats_exponential_moving_average` - EMA
- `stats_trend_detection` - Find trends
- `stats_percent_change` - % change
- `stats_growth_rate` - CAGR
- `stats_volatility` - Consistency

### Advanced NBA (6 - Sprint 6)
- `nba_four_factors` - Four Factors
- `nba_turnover_percentage` - TOV%
- `nba_rebound_percentage` - REB%
- `nba_assist_percentage` - AST%
- `nba_steal_percentage` - STL%
- `nba_block_percentage` - BLK%

---

## 🛠️ Troubleshooting

### Tools Not Showing

**Problem**: Claude says "no tools available"

**Solutions**:
1. Check config file location is correct
2. Verify JSON syntax (use jsonlint.com)
3. Ensure path uses forward slashes `/`
4. Restart Claude Desktop completely

### Connection Errors

**Problem**: "Failed to connect to database"

**Solutions**:
1. Verify credentials in config
2. Check network connectivity
3. Test connection manually:
   ```bash
   python tests/test_connections.py
   ```

### Python Not Found

**Problem**: "python: command not found"

**Solutions**:
1. Use full Python path:
   ```json
   "command": "/usr/bin/python3"
   ```
2. Or use Python 3 explicitly:
   ```json
   "command": "python3"
   ```

### Import Errors

**Problem**: "ModuleNotFoundError"

**Solutions**:
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Use virtual environment Python:
   ```json
   "command": "/path/to/venv/bin/python"
   ```

---

## 💡 Pro Tips

### 1. Save Common Queries

Create a "prompts" file with your frequent queries:
```
# Analytics Queries
- Calculate Four Factors for team stats
- Find correlation between X and Y
- Detect trend in performance data
```

### 2. Use Tool Chaining

Claude can chain multiple tools:
```
"Query the database for Lakers stats, then calculate their Four Factors"
```

### 3. Complex Analysis

Combine tools for deep analysis:
```
"Get top 10 scorers, calculate correlation between their PPG and TS%,
then build a regression model and predict TS% for 30 PPG"
```

### 4. Batch Operations

Process multiple items:
```
"For each team in the database, calculate their Four Factors
and rank by offensive efficiency"
```

---

## 📚 Learn More

### Documentation
- **ADVANCED_ANALYTICS_GUIDE.md** - Quick reference for all tools
- **SPRINT_6_COMPLETE.md** - Sprint 6 implementation details
- **MATH_TOOLS_GUIDE.md** - Math/stats/NBA tools (Sprint 5)
- **USAGE_GUIDE.md** - Comprehensive system guide

### Example Workflows
- **Player scouting**: Database → Stats → Metrics → Analysis
- **Team analysis**: Query data → Four Factors → Trend detection
- **Prediction models**: Historical data → Regression → Forecasting

---

## 🎯 Quick Reference

### Config File Template

```json
{
  "mcpServers": {
    "nba-analytics": {
      "command": "python",
      "args": ["/FULL/PATH/TO/nba-mcp-synthesis/mcp_server/fastmcp_server.py"],
      "env": {
        "RDS_HOST": "your-db-host",
        "RDS_PORT": "5432",
        "RDS_DATABASE": "nba_simulator",
        "RDS_USERNAME": "your-username",
        "RDS_PASSWORD": "your-password",
        "S3_BUCKET": "your-bucket",
        "S3_REGION": "us-east-1"
      }
    }
  }
}
```

### Verification Commands

```bash
# Test your config
python mcp_server/fastmcp_server.py

# Test connections
python tests/test_connections.py

# Test all tools
python scripts/test_math_stats_features.py
python scripts/test_sprint6_features.py
```

---

## ✅ Success Checklist

- [ ] Claude Desktop installed
- [ ] Config file created at correct location
- [ ] Full path to fastmcp_server.py set
- [ ] All credentials configured
- [ ] Claude Desktop restarted
- [ ] MCP tools indicator (🔌) visible
- [ ] Test query returns results
- [ ] Math tools working
- [ ] Stats tools working
- [ ] Advanced analytics working

---

**You're all set!** 🎉

Ask Claude anything about NBA analytics, and it will use the appropriate tools from your 55-tool arsenal!

**Questions?** Check the troubleshooting section or see USAGE_GUIDE.md for detailed help.

---

**Last Updated**: October 10, 2025
**Total Tools**: 55
**System Version**: Sprint 6 Complete
