# Claude Desktop MCP Testing Instructions

## 🧪 Step-by-Step Testing Guide

After configuring Claude Desktop with the MCP server, follow these tests in order:

---

## ✅ Test 1: Check Tool Availability

### What to Ask Claude Desktop:
```
What tools do you currently have available?
Do you see any MCP tools related to databases or NBA data?
```

### Expected Response:
Claude Desktop should list these MCP tools:
- ✅ `mcp__nba-mcp-server__query_database`
- ✅ `mcp__nba-mcp-server__list_tables`
- ✅ `mcp__nba-mcp-server__get_table_schema`
- ✅ `mcp__nba-mcp-server__list_s3_files`

### ✅ Pass Criteria:
- All 4 MCP tools are visible
- Tools have the `mcp__nba-mcp-server__` prefix

### ❌ If Test Fails:
1. Verify config file location: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Check JSON syntax (no trailing commas, proper quotes)
3. Restart Claude Desktop completely (Cmd+Q, then relaunch)
4. Wait 15 seconds after relaunch

---

## ✅ Test 2: List Database Tables

### What to Ask Claude Desktop:
```
Using the MCP, can you list all available tables in the NBA database?
```

### Expected Response:
Should return **40 tables** including:
- `games`
- `players`
- `teams`
- `play_by_play`
- `player_game_stats`
- `box_score_players`
- `nba_api_comprehensive`
- ... and 33 more

### ✅ Pass Criteria:
- Returns 40 tables
- No connection errors
- Query completes in < 5 seconds

### ❌ If Test Fails:
1. Check database credentials in config
2. Verify database is running: `pg_isready -h YOUR_HOST`
3. Test network connectivity to database
4. Check if Python path is correct in config

---

## ✅ Test 3: Get Table Schema

### What to Ask Claude Desktop:
```
Using the MCP, show me the schema for the 'players' table.
```

### Expected Response:
Should return **7 columns**:
- `player_id` (varchar, NOT NULL)
- `player_name` (varchar, NOT NULL)
- `position` (varchar)
- `jersey_number` (varchar)
- `team_id` (varchar)
- `created_at` (timestamp)
- `updated_at` (timestamp)

### ✅ Pass Criteria:
- Returns complete schema
- Shows data types
- Shows nullable constraints

### ❌ If Test Fails:
1. Check if table name is correct (case-sensitive)
2. Verify database permissions (need SELECT on information_schema)

---

## ✅ Test 4: Query Game Count

### What to Ask Claude Desktop:
```
Using the MCP, query the games table and tell me how many total games are in the database.
```

### Expected Response:
```
Total games: 44,828
```

### ✅ Pass Criteria:
- Returns count close to 44,828
- Query executes successfully
- No timeout errors

### ❌ If Test Fails:
1. Check if `games` table exists: `list_tables`
2. Verify query permissions (SELECT on games table)
3. Check query syntax in MCP logs

---

## ✅ Test 5: List S3 Files

### What to Ask Claude Desktop:
```
Using the MCP, can you list the first 5 files in the S3 bucket?
```

### Expected Response:
Should return files from `nba-sim-raw-data-lake` bucket:
- Various `.txt`, `.csv`, `.metadata` files
- Files in `athena-results/` prefix
- File sizes and last modified dates

### ✅ Pass Criteria:
- Returns at least 5 files
- Shows file metadata (size, last_modified)
- No AWS credential errors

### ❌ If Test Fails:
1. Check AWS credentials in config or environment
2. Verify S3 bucket name: `nba-sim-raw-data-lake`
3. Check IAM permissions (s3:ListBucket)
4. Test AWS CLI: `aws s3 ls s3://nba-sim-raw-data-lake --max-items 5`

---

## ✅ Test 6: Simple Data Query

### What to Ask Claude Desktop:
```
Using the MCP, query the games table and show me:
- The first 3 games (any 3 games)
- Include columns: game_id, home_team, away_team, game_date
```

### Expected Response:
Should return a result with 3 rows showing actual game data.

### ✅ Pass Criteria:
- Returns 3 rows of data
- All requested columns present
- Data looks reasonable (team names, dates)

### ❌ If Test Fails:
1. Check column names match actual schema: `get_table_schema('games')`
2. Adjust query to use actual column names
3. Verify table has data: `SELECT COUNT(*) FROM games`

---

## ✅ Test 7: Complex Query (Join)

### What to Ask Claude Desktop:
```
Using the MCP, write and execute a query that:
1. Joins the players and teams tables
2. Shows player names and their team names
3. Limits to 5 results
```

### Expected Response:
Should return players with their associated team names.

### ✅ Pass Criteria:
- Join query works correctly
- Returns player and team data together
- No syntax errors

### ❌ If Test Fails:
1. Check foreign key relationship between tables
2. Verify both tables exist and have data
3. Review schema: are join keys compatible?

---

## ✅ Test 8: Use Econometric Method (GMM)

### What to Ask Claude Desktop:
```
Can you help me use the new Arellano-Bond GMM method?

First, explain what data structure it needs (player-season panel data).
Then, show me what parameters I need to provide to the difference_gmm() method.
```

### Expected Response:
Claude Desktop should:
1. Explain panel data structure (player_id, season, dependent variable)
2. List parameters: formula, gmm_type, max_lags, collapse
3. Mention AR(2) and Hansen diagnostic tests

### ✅ Pass Criteria:
- Understands GMM method exists
- Can describe required data structure
- Knows about diagnostic tests

### ❌ If Test Fails:
1. Ask Claude Desktop to read the panel_data.py file
2. Check if file is accessible from Claude Desktop
3. Provide documentation directly

---

## 🎯 All Tests Passed?

If all 8 tests pass, **congratulations!** 🎉

Claude Desktop now has full access to:
- ✅ 40 database tables
- ✅ 44,828 NBA games
- ✅ S3 raw data storage
- ✅ All Phase 2 econometric methods

### Next Steps:

1. **Try Advanced Queries**
   - Multi-table joins
   - Aggregations by season
   - Time series data extraction

2. **Use Phase 2 Methods**
   - Dynamic Panel GMM analysis
   - Survival analysis for careers
   - Time series forecasting

3. **Build Workflows**
   - Player performance analysis
   - Team strategy evolution
   - Causal inference studies

---

## 📊 Performance Benchmarks

### Expected Query Times:
- `list_tables`: < 1 second
- `get_table_schema`: < 1 second
- `COUNT(*)` query: < 2 seconds
- Simple SELECT: < 3 seconds
- Complex JOIN: < 5 seconds
- S3 file listing: < 3 seconds

### If queries are slower:
1. Check network latency to database
2. Verify database has proper indexes
3. Consider query optimization
4. Check database server load

---

## 🚨 Common Issues & Solutions

### Issue: "MCP server not found"
**Solution**:
1. Check Python path in config
2. Verify conda environment exists
3. Try absolute path: `/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3`

### Issue: "Connection refused"
**Solution**:
1. Check if database is running
2. Verify firewall rules
3. Test connection manually: `psql -h HOST -U USER -d DATABASE`

### Issue: "Authentication failed"
**Solution**:
1. Verify database credentials
2. Check if password contains special characters (escape in JSON)
3. Test with psql client first

### Issue: "Table not found"
**Solution**:
1. Check table name spelling (case-sensitive)
2. Verify schema: some tables might be in different schemas
3. Use `list_tables` to see all available tables

### Issue: "S3 access denied"
**Solution**:
1. Check AWS credentials
2. Verify IAM role has s3:ListBucket permission
3. Test with AWS CLI: `aws s3 ls s3://nba-sim-raw-data-lake`

---

## 📝 Testing Checklist

Copy this checklist and mark off as you complete each test:

```
[ ] Test 1: Tool availability check
[ ] Test 2: List database tables (40 tables)
[ ] Test 3: Get table schema (players table)
[ ] Test 4: Query game count (44,828 games)
[ ] Test 5: List S3 files (5 files)
[ ] Test 6: Simple data query (3 games)
[ ] Test 7: Complex join query (players + teams)
[ ] Test 8: Use GMM method (explain parameters)
```

**All tests passed?** You're ready to analyze NBA data! 🏀📊

---

## 🎓 What to Do Next

### Beginner
- Practice simple SQL queries
- Explore different tables
- Try aggregations (AVG, SUM, COUNT)

### Intermediate
- Join multiple tables
- Extract time series data
- Calculate advanced statistics

### Advanced
- Use Phase 2 econometric methods
- Build complete analysis workflows
- Create reproducible research pipelines

---

**Happy analyzing!** 🚀
