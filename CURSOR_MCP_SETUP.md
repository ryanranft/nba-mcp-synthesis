# Cursor MCP Integration Setup

**Purpose**: Configure NBA MCP Server to work with Cursor AI
**Last Updated**: 2025-10-11
**Status**: Ready to use

---

## 🎯 Quick Setup (2 minutes)

### Option 1: Using Cursor's MCP Settings UI (Recommended)

1. **Open Cursor Settings**
   - Press `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux)
   - Or go to `Cursor > Settings`

2. **Navigate to MCP**
   - Search for "MCP" in settings
   - Or go to `Features > Model Context Protocol`

3. **Add NBA MCP Server**
   - Click "Edit Config" or "Add Server"
   - Use the configuration below

4. **Configuration to Add**:
```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
      "args": [
        "-m",
        "mcp_server.fastmcp_server"
      ],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "PYTHONPATH": "/Users/ryanranft/nba-mcp-synthesis",
        "NBA_MCP_DEBUG": "false",
        "NBA_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

5. **Save and Restart**
   - Save the configuration
   - Restart Cursor (`Cmd+Q` then reopen)
   - Or use `Cmd+Shift+P` > "Reload Window"

---

### Option 2: Manual Config File (Alternative)

If the UI method doesn't work, you can manually create the config:

1. **Create Cursor MCP Config Directory** (if it doesn't exist):
```bash
mkdir -p ~/.cursor
```

2. **Copy Config File**:
```bash
cp /Users/ryanranft/nba-mcp-synthesis/cursor_mcp_config.json ~/.cursor/mcp.json
```

3. **Restart Cursor**:
```bash
# Close Cursor completely
pkill Cursor
# Reopen Cursor
open -a Cursor
```

---

## ✅ Verify Installation

### Test 1: Check MCP Status

1. Open a new chat in Cursor
2. Type: "What MCP tools are available?"
3. You should see a list of 90+ tools

### Test 2: Try a Simple Tool

Ask in chat:
```
Can you list all tables in my NBA database using the MCP tools?
```

Expected: The AI should call `list_tables` tool and show results.

### Test 3: Try an NBA Metric

Ask in chat:
```
Calculate the player efficiency rating (PER) for a player with:
- 25 points, 8 rebounds, 5 assists, 2 steals, 1 block
- 10 FGA, 6 FGM, 5 FTA, 4 FTM
- 40 minutes played in a 240 minute game
```

Expected: The AI should call `nba_player_efficiency_rating` tool.

---

## 🔧 Troubleshooting

### Problem: "MCP server not found"

**Solution**: Check Python path
```bash
# Verify Python path
which python3

# Update cursor_mcp_config.json with correct path
# Replace "command" value with output from above
```

### Problem: "Module not found: mcp_server"

**Solution**: Install dependencies
```bash
cd /Users/ryanranft/nba-mcp-synthesis
pip install -r requirements.txt
```

### Problem: "Connection refused"

**Solution**: Check if server starts manually
```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 -m mcp_server.fastmcp_server
```

If you see errors, check your `.env` file has correct credentials.

### Problem: Tools not showing up

**Solutions**:
1. **Restart Cursor completely** - Not just reload window
2. **Check MCP logs**:
   ```bash
   tail -f ~/.cursor/logs/mcp-*.log
   ```
3. **Verify config syntax**:
   ```bash
   cat ~/.cursor/mcp.json | python3 -m json.tool
   ```

---

## 📊 Available Tools (90 registered)

Once configured, you'll have access to:

### Database Tools (15)
- `query_database` - Execute SQL queries
- `list_tables` - List all tables
- `get_table_schema` - Get table structure
- And 12 more...

### S3 Tools (10)
- `list_s3_files` - List S3 objects
- `get_s3_file` - Download from S3
- And 8 more...

### NBA Metrics (13)
- `nba_player_efficiency_rating` - Calculate PER
- `nba_true_shooting_percentage` - Calculate TS%
- `nba_usage_rate` - Calculate usage rate
- `nba_offensive_rating` - Calculate ORtg
- `nba_four_factors` - Four Factors analysis
- And 8 more...

### ML Tools (33)
- `ml_kmeans` - K-Means clustering
- `ml_logistic_regression` - Logistic regression
- `ml_accuracy_score` - Model accuracy
- And 30 more...

### Math & Stats Tools (13)
- `stats_mean`, `stats_median`, `stats_mode`
- `stats_correlation`, `stats_linear_regression`
- `stats_moving_average`, `stats_trend_detection`
- And 6 more...

### Book Tools (9)
- `list_books` - List book library
- `read_book` - Read books in chunks
- `search_books` - Search book content
- And 6 more...

### AWS/Action Tools (22)
- Action tools for player analysis
- Glue ETL tools
- And 20 more...

**Total**: 90+ tools ready to use!

---

## 💡 Usage Examples

### Example 1: Database Query

**You ask in chat**:
> "Query the database to show me the top 5 scorers from last season"

**AI will**:
1. Call `list_tables` to see available tables
2. Call `get_table_schema` to understand structure
3. Call `query_database` with SQL query
4. Return formatted results

### Example 2: NBA Analytics

**You ask**:
> "Calculate advanced metrics for Stephen Curry's performance"

**AI will**:
1. Query player stats from database
2. Call `nba_true_shooting_percentage`
3. Call `nba_player_efficiency_rating`
4. Call `nba_usage_rate`
5. Present comprehensive analysis

### Example 3: ML Analysis

**You ask**:
> "Cluster NBA players by their performance stats"

**AI will**:
1. Query player statistics
2. Call `ml_normalize_features` to prep data
3. Call `ml_kmeans` to cluster
4. Call `ml_silhouette_score` to evaluate
5. Present cluster analysis

---

## 🔐 Security Notes

- **Local Only**: MCP server runs locally on your machine
- **No External Access**: Tools only access your local database/S3
- **Environment Variables**: Credentials stored in `.env` (gitignored)
- **API Keys**: Only you have access to your API keys

---

## 📈 Performance

- **Startup Time**: ~2-3 seconds
- **Tool Response**: <1 second for most tools
- **Database Queries**: Depends on query complexity
- **Cost**: Free (all computation is local)

---

## 🎓 Best Practices

### DO ✅
- **Be specific** in your requests
- **Ask for multiple tools** - AI can chain them
- **Verify results** - Always check the output
- **Use natural language** - No need for exact syntax

### DON'T ❌
- **Don't worry about syntax** - AI handles it
- **Don't call tools directly** - Just ask naturally
- **Don't repeat questions** - AI remembers context

---

## 🔄 Updating the Server

If you update the MCP server code:

1. **No restart needed** for most changes
2. **Restart Cursor** if you add new tools
3. **Check logs** if something breaks:
   ```bash
   tail -f ~/.cursor/logs/mcp-*.log
   ```

---

## 📞 Support

### If Something Doesn't Work

1. **Check this guide** - Most issues covered above
2. **Check logs**:
   ```bash
   tail -f ~/.cursor/logs/mcp-*.log
   tail -f /Users/ryanranft/nba-mcp-synthesis/logs/application.log
   ```
3. **Test manually**:
   ```bash
   cd /Users/ryanranft/nba-mcp-synthesis
   python3 -m mcp_server.fastmcp_server
   ```

### Common Issues

| Problem | Solution |
|---------|----------|
| Tools not showing | Restart Cursor completely |
| Python not found | Update config with correct Python path |
| Module not found | Run `pip install -r requirements.txt` |
| Connection refused | Check `.env` file exists with credentials |
| Slow responses | Check database connection |

---

## 🎉 You're Ready!

Once configured, you can:
- Query your NBA database naturally
- Calculate advanced NBA metrics
- Run ML analyses
- Access S3 data
- Read technical books
- And much more!

**Just ask in chat** - the AI will use the appropriate tools automatically.

---

## 📝 Quick Reference

**Config File Location**: `~/.cursor/mcp.json`
**Server Module**: `mcp_server.fastmcp_server`
**Working Directory**: `/Users/ryanranft/nba-mcp-synthesis`
**Python Path**: `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`
**Total Tools**: 90+ registered tools

**Test Command**:
```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 -m mcp_server.fastmcp_server
```

**Verify in Chat**:
```
What MCP tools are available?
```

---

**Last Updated**: 2025-10-11
**Status**: Ready to use
**Compatibility**: Cursor AI with MCP support
**Version**: FastMCP server (90 tools)

