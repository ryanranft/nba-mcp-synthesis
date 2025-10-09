# Claude Desktop - Next Steps

## ✅ Configuration Complete!

Your Claude Desktop has been configured with the NBA MCP Server.

### Configuration Details

**Location:** `~/Library/Application Support/Claude/config.json`

**MCP Server:** `nba-mcp-server`
- Command: `python3`
- Script: `/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py`
- Database: `nba_simulator` on AWS RDS
- S3 Bucket: `nba-sim-raw-data-lake`

## Next Steps

### 1. Restart Claude Desktop

**IMPORTANT:** You must restart Claude Desktop for the changes to take effect.

1. Quit Claude Desktop completely (Cmd+Q)
2. Reopen Claude Desktop

### 2. Verify Installation

Once Claude Desktop restarts, try these commands in a new conversation:

**Test 1: Check available tools**
```
What MCP tools are available?
```

You should see:
- `query_database` - Execute SQL queries
- `list_tables` - List database tables
- `get_table_schema` - Get table schemas
- `list_s3_files` - List S3 files

**Test 2: List tables**
```
Can you list all tables in the NBA database?
```

**Test 3: Query database**
```
What's the database version?
```

**Test 4: Get schema**
```
What's the schema for the players table?
```

**Test 5: Browse S3**
```
Show me 5 files from the S3 bucket
```

## Example Use Cases

### Player Analysis
```
Can you query the database to find the top 10 players by total points scored in the player_game_stats table?
```

### Team Statistics
```
What teams are in the database? Show me the teams table schema first, then query for all teams.
```

### Game Data
```
How many games are in the database? Query the games table.
```

### S3 Data Exploration
```
What basketball reference data files are available in S3? List files with prefix "basketball_reference/"
```

## Troubleshooting

### Tools Not Showing Up

1. **Verify restart:** Make sure you completely quit and reopened Claude Desktop
2. **Check logs:** Look for error messages in Claude Desktop
3. **Verify config:** Check that `config.json` is valid JSON
4. **Test manually:** Run `python scripts/test_mcp_client.py` to verify server works

### Connection Errors

1. **Test connections:**
   ```bash
   cd /Users/ryanranft/nba-mcp-synthesis
   python tests/test_connections.py
   ```

2. **Check server manually:**
   ```bash
   python mcp_server/server_simple.py
   ```

3. **Verify environment:** Make sure `.env` file has correct credentials

### Server Not Starting

1. **Check Python:**
   ```bash
   which python3
   # Should show: /Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3
   ```

2. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check file permissions:**
   ```bash
   chmod +x mcp_server/server_simple.py
   ```

## Advanced Usage

### Custom Queries

Once working, you can ask Claude to:
- Write complex SQL queries
- Analyze player performance trends
- Compare team statistics
- Find patterns in game data
- Export data for visualization

### Example Complex Request

```
I want to analyze which NBA teams have the best home court advantage.

1. First, show me the relevant tables
2. Then write a SQL query to calculate win percentage at home vs away
3. Identify the top 5 teams
4. Suggest visualizations for this data
```

Claude will use the MCP tools to:
1. List tables with `list_tables`
2. Get schemas with `get_table_schema`
3. Execute queries with `query_database`
4. Provide analysis and recommendations

## Security Notes

**IMPORTANT:** The config file contains your database credentials and API keys.

- Keep `config.json` secure
- Don't share screenshots showing credentials
- Rotate credentials periodically
- Use environment variables in production

## Support

If you encounter issues:

1. **Check documentation:**
   - `CLAUDE_DESKTOP_SETUP.md` - Full setup guide
   - `USAGE_GUIDE.md` - Complete usage guide
   - `README.md` - Project overview

2. **Run tests:**
   ```bash
   python scripts/test_mcp_client.py
   python scripts/test_synthesis_direct.py
   ```

3. **Check logs:**
   - Claude Desktop logs: `~/Library/Logs/Claude/`
   - Server output: Visible in Claude Desktop when tools are called

## What's Next?

Now that Claude Desktop is configured, you can:

1. **Explore your NBA data** - Ask Claude questions about your database
2. **Run analyses** - Use Claude to write and execute SQL queries
3. **Build workflows** - Create multi-step analysis workflows
4. **Export results** - Save queries and results for documentation

Have fun exploring your NBA database with Claude! 🏀