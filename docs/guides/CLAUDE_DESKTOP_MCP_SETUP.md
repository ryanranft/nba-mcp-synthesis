# Claude Desktop MCP Setup Guide

## 📋 Overview

This guide will help you configure Claude Desktop to connect to the NBA MCP Server, giving it access to 40 database tables and 44,828 NBA games.

**Current Status:**
- ✅ Claude Code (CLI): Has full MCP access
- ❌ Claude Desktop: No MCP access (needs configuration)
- ✅ NBA MCP Server: Running (PIDs 1218, 11532)

---

## 🔧 Step 1: Create Configuration File

### File Location (macOS)
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Configuration Template

Create or edit the file with this content:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
      "args": [
        "-m",
        "mcp_server.server_simple"
      ],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "RDS_HOST": "YOUR_RDS_HOST",
        "RDS_PORT": "5432",
        "RDS_DATABASE": "YOUR_DATABASE_NAME",
        "RDS_USERNAME": "YOUR_USERNAME",
        "RDS_PASSWORD": "YOUR_PASSWORD",
        "AWS_REGION": "us-east-1",
        "S3_BUCKET_NAME": "nba-sim-raw-data-lake"
      }
    }
  }
}
```

### 📝 Fill in Your Values

Replace these placeholders with your actual credentials:
- `YOUR_RDS_HOST` - Your PostgreSQL database host
- `YOUR_DATABASE_NAME` - Database name (likely `nba_stats` or similar)
- `YOUR_USERNAME` - Database username
- `YOUR_PASSWORD` - Database password

**Note**: If you're using local PostgreSQL, use:
```json
"RDS_HOST": "localhost",
"RDS_PORT": "5432",
"RDS_DATABASE": "nba_stats",
"RDS_USERNAME": "postgres",
"RDS_PASSWORD": ""
```

---

## 🔐 Alternative: Use Environment Variables (More Secure)

Instead of hardcoding credentials, you can reference environment variables:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
      "args": ["-m", "mcp_server.server_simple"],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {}
    }
  }
}
```

Then set environment variables in your shell profile (`~/.zshrc` or `~/.bash_profile`):
```bash
export RDS_HOST="your_host"
export RDS_PORT="5432"
export RDS_DATABASE="your_database"
export RDS_USERNAME="your_username"
export RDS_PASSWORD="your_password"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="nba-sim-raw-data-lake"
```

---

## 🔄 Step 2: Restart Claude Desktop

1. **Quit Claude Desktop completely** (not just close the window)
   - macOS: Right-click icon in Dock → Quit
   - Or: Cmd+Q when Claude Desktop is active

2. **Relaunch Claude Desktop**

3. **Wait 10-15 seconds** for MCP server to initialize

---

## ✅ Step 3: Verify MCP Connection

### Test 1: Check Available Tools

In Claude Desktop, ask:
```
Can you list your available tools? Do you see any MCP tools?
```

**Expected Response:**
Claude Desktop should now see:
- ✅ `query_database` - Execute SQL queries
- ✅ `list_tables` - List all database tables
- ✅ `get_table_schema` - Get table structure
- ✅ `list_s3_files` - Access S3 bucket

### Test 2: List Tables

Ask Claude Desktop:
```
Using the MCP, can you list all available tables in the NBA database?
```

**Expected Response:**
Should return 40 tables including:
- `games` (44,828 games)
- `players`
- `teams`
- `play_by_play`
- `player_game_stats`
- And 35 more...

### Test 3: Query Data

Ask Claude Desktop:
```
Using the MCP, query the games table and show me the total count of games in the database.
```

**Expected Response:**
```
Total games: 44,828
```

---

## 🚨 Troubleshooting

### Issue: "No MCP tools available"

**Solutions:**
1. Check config file syntax (valid JSON)
2. Verify Python path: `/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3`
3. Ensure MCP server is running: `ps aux | grep mcp`
4. Check Claude Desktop logs (if available)
5. Try restarting computer

### Issue: "Connection refused" or "Database error"

**Solutions:**
1. Verify database credentials in config
2. Check if database is running
3. Test connection manually:
   ```bash
   python3 -c "from mcp_server.connectors.rds_connector import RDSConnector; print('OK')"
   ```
4. Ensure network access to database

### Issue: MCP server starts but Claude Desktop can't connect

**Solutions:**
1. Check `cwd` path is correct in config
2. Verify conda environment is activated
3. Try absolute path for Python interpreter
4. Check file permissions on project directory

---

## 📊 What Claude Desktop Can Now Do

Once configured, Claude Desktop will have full access to:

### Database Operations (40 Tables)
- Query 44,828 games
- Access player statistics
- Analyze play-by-play data
- Get team performance metrics
- Run advanced SQL queries

### S3 Storage
- List files in `nba-sim-raw-data-lake`
- Access raw data exports
- Read Athena query results

### Advanced Analytics (Phase 2 Methods)
With database access, Claude Desktop can now use all 23 Phase 2 econometric methods:
- Causal inference (kernel matching, doubly robust)
- Time series (ARIMAX, VAR, Johansen cointegration)
- Survival analysis (Fine-Gray competing risks)
- Econometric tests (VECM, structural breaks)
- **Dynamic Panel GMM (Arellano-Bond, Blundell-Bond)** ← New!

---

## 🎯 Example Usage

### Simple Query
```
Using the MCP, show me the schema for the players table.
```

### Complex Analysis
```
Using the MCP:
1. Query player scoring data for the top 10 scorers in the 2023 season
2. Calculate their average points per game
3. Show any interesting trends
```

### Using Phase 2 GMM Methods
```
I want to analyze scoring persistence using the new GMM methods:

1. Query player-season panel data (player_id, season, points, minutes)
2. Use the econometric suite's difference_gmm() method
3. Interpret the Arellano-Bond test results
```

---

## 📚 Additional Resources

- **MCP Server Code**: `/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py`
- **Database Tables**: 40 tables with NBA data
- **Phase 2 Methods**: `mcp_server/panel_data.py` (GMM methods)
- **Econometric Suite**: `mcp_server/econometric_suite.py`

---

## ✨ Quick Tips

1. **Always mention "MCP"** in your questions to Claude Desktop
2. **Start simple** - test with `list_tables` before complex queries
3. **Use SQL** - Claude Desktop can write and execute SQL queries
4. **Iterate** - Start with basic queries, then build more complex analysis

---

## 🔐 Security Notes

- **Never commit** the config file with credentials to git
- **Use environment variables** for production
- **Rotate passwords** regularly
- **Limit database permissions** to read-only if possible

---

**Status**: Ready to configure ✅
**Next Step**: Create the config file and restart Claude Desktop!
