# Claude Desktop + NBA MCP Integration Guide

## 📚 Documentation Overview

This folder contains everything you need to connect Claude Desktop to the NBA MCP Server and start analyzing 44,828 games!

### 📖 Documents

1. **`CLAUDE_DESKTOP_MCP_SETUP.md`** ⭐ START HERE
   - Complete setup instructions
   - Configuration file creation
   - Environment variable setup
   - Troubleshooting guide

2. **`claude_desktop_config_TEMPLATE.json`**
   - Ready-to-use config template
   - Copy to: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Fill in your database credentials

3. **`CLAUDE_DESKTOP_QUICK_REFERENCE.md`**
   - Quick start prompts for Claude Desktop
   - Common queries and workflows
   - Phase 2 method examples
   - Pro tips for asking questions

4. **`CLAUDE_DESKTOP_TESTING.md`**
   - 8 comprehensive tests
   - Step-by-step validation
   - Troubleshooting for each test
   - Performance benchmarks

---

## 🚀 Quick Start (3 Steps)

### Step 1: Create Config File (5 min)

```bash
# 1. Create config directory if it doesn't exist
mkdir -p ~/Library/Application\ Support/Claude/

# 2. Copy template
cp claude_desktop_config_TEMPLATE.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. Edit with your database credentials
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Fill in these values:**
- `RDS_HOST` - Your database host (or `localhost`)
- `RDS_DATABASE` - Database name (likely `nba_stats`)
- `RDS_USERNAME` - Your username
- `RDS_PASSWORD` - Your password

### Step 2: Restart Claude Desktop (1 min)

1. Quit Claude Desktop completely (Cmd+Q)
2. Relaunch Claude Desktop
3. Wait 15 seconds for MCP server to start

### Step 3: Test Connection (2 min)

Ask Claude Desktop:
```
Can you list the available tables in the NBA database using the MCP?
```

**Expected**: Should return 40 tables ✅

---

## ✅ Current Status

### Claude Code (CLI) - ✅ WORKING
- Has full MCP access
- Connected to NBA database
- 40 tables available
- 44,828 games accessible
- All Phase 2 methods working

### Claude Desktop - ❌ NEEDS SETUP
- Currently no MCP access
- Will have same access after configuration
- Estimated setup time: 10 minutes

---

## 🎯 What You'll Get

Once configured, Claude Desktop can:

### Database Access
- ✅ Query 40 tables with NBA data
- ✅ Access 44,828 games
- ✅ Run complex SQL queries
- ✅ Join multiple tables
- ✅ Aggregate and analyze data

### S3 Storage Access
- ✅ List files in `nba-sim-raw-data-lake`
- ✅ Access raw data exports
- ✅ Read Athena query results

### Phase 2 Econometric Methods (23 Methods)
- ✅ Causal inference (3 methods)
- ✅ Time series (8 methods)
- ✅ Survival analysis (4 methods)
- ✅ Econometric tests (4 methods)
- ✅ **Dynamic Panel GMM (4 methods)** ← Just added!

---

## 📊 Available Data

### Tables (40)
- `games` - 44,828 games
- `players` - Player information
- `teams` - Team data
- `play_by_play` - Play-by-play data
- `player_game_stats` - Player statistics
- `box_score_players` - Box score data
- `nba_api_comprehensive` - Comprehensive NBA API data
- ... and 33 more

### Time Range
- Historical NBA data
- Multiple seasons
- Regular season + playoffs

---

## 🔧 Tools Available via MCP

1. **`query_database`**
   - Execute SQL queries (SELECT only)
   - Returns structured results
   - Fast query execution

2. **`list_tables`**
   - List all 40 available tables
   - Get table counts

3. **`get_table_schema`**
   - View table structure
   - See column types and constraints
   - Check nullable fields

4. **`list_s3_files`**
   - Browse S3 bucket contents
   - Get file metadata
   - Access raw data

---

## 💡 Example Use Cases

### 1. Player Performance Analysis
```
Using the MCP, analyze LeBron James' scoring trends:
1. Query his season-by-season stats
2. Apply ARIMAX forecasting
3. Predict next season performance
```

### 2. Team Dynasty Detection
```
Using survival analysis methods:
1. Query team win percentages
2. Define "dynasty" criteria
3. Model dynasty duration
4. Identify success factors
```

### 3. Coaching Impact (Causal Inference)
```
Using doubly robust matching:
1. Identify coaching changes
2. Match treated/control teams
3. Estimate treatment effect
4. Test for heterogeneity
```

### 4. Scoring Persistence (GMM)
```
Using Arellano-Bond GMM:
1. Query player-season panel data
2. Estimate dynamic model
3. Check AR(2) and Hansen tests
4. Interpret persistence coefficient
```

---

## 📁 File Structure

```
nba-mcp-synthesis/
├── CLAUDE_DESKTOP_MCP_SETUP.md          ← Setup instructions
├── CLAUDE_DESKTOP_QUICK_REFERENCE.md    ← Usage examples
├── CLAUDE_DESKTOP_TESTING.md            ← Testing guide
├── claude_desktop_config_TEMPLATE.json  ← Config template
├── README_CLAUDE_DESKTOP_MCP.md         ← This file
│
├── mcp_server/
│   ├── server_simple.py                 ← MCP server (running)
│   ├── panel_data.py                    ← GMM methods
│   └── econometric_suite.py             ← All Phase 2 methods
│
├── examples/                             ← Usage examples
└── tests/                                ← Test suite
```

---

## 🚨 Troubleshooting

### MCP Tools Not Showing?
1. Check config file location
2. Verify JSON syntax
3. Restart Claude Desktop
4. Wait 15 seconds

### Database Connection Failed?
1. Verify credentials
2. Check if database is running
3. Test connection manually with psql
4. Check firewall rules

### Queries Timing Out?
1. Check network latency
2. Simplify query
3. Verify database indexes
4. Check server load

**See `CLAUDE_DESKTOP_MCP_SETUP.md` for detailed troubleshooting**

---

## 🎓 Learning Path

### Level 1: Setup & Basics
- [ ] Complete configuration
- [ ] Pass all 8 tests
- [ ] Run simple queries

### Level 2: Data Exploration
- [ ] Explore all 40 tables
- [ ] Join multiple tables
- [ ] Calculate aggregations

### Level 3: Time Series
- [ ] Extract time-ordered data
- [ ] Apply ARIMA/VAR methods
- [ ] Generate forecasts

### Level 4: Panel Methods
- [ ] Structure panel data
- [ ] Use fixed effects
- [ ] Apply GMM methods

### Level 5: Advanced Analysis
- [ ] Causal inference
- [ ] Survival analysis
- [ ] Build complete workflows

---

## 🌟 Phase 2 Methods (Just Added!)

### Dynamic Panel GMM (Day 6)
1. **First-Difference OLS** - Remove fixed effects
2. **Difference GMM** - Arellano-Bond (1991)
3. **System GMM** - Blundell-Bond (1998)
4. **GMM Diagnostics** - AR(2), Hansen tests

### Previous Days (19 Methods)
- Day 1: Causal inference (3 methods)
- Day 2: Time series (4 methods)
- Day 3: Survival analysis (4 methods)
- Day 4: Advanced time series (4 methods)
- Day 5: Econometric tests (4 methods)

**Total: 23 methods across 6 days!**

---

## 📞 Support

### Documentation
- Setup: `CLAUDE_DESKTOP_MCP_SETUP.md`
- Usage: `CLAUDE_DESKTOP_QUICK_REFERENCE.md`
- Testing: `CLAUDE_DESKTOP_TESTING.md`

### Code
- MCP Server: `mcp_server/server_simple.py`
- GMM Methods: `mcp_server/panel_data.py`
- All Methods: `mcp_server/econometric_suite.py`

### Testing
- Test script: `test_gmm_methods.py`
- Test suite: `tests/test_panel_data.py`

---

## ✨ Ready to Start?

1. **Read**: `CLAUDE_DESKTOP_MCP_SETUP.md`
2. **Configure**: Edit `claude_desktop_config_TEMPLATE.json`
3. **Test**: Follow `CLAUDE_DESKTOP_TESTING.md`
4. **Use**: Reference `CLAUDE_DESKTOP_QUICK_REFERENCE.md`

**You're 10 minutes away from analyzing 44,828 NBA games!** 🏀📊🚀
