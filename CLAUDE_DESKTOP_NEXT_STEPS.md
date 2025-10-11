# Claude Desktop Integration - Next Steps

**Status:** ✅ MCP Server Ready | Configuration Files Created

---

## Quick Setup (2 Minutes)

### Option 1: Automatic Setup (Recommended)

```bash
# Run the setup script
./setup_claude_desktop.sh

# Restart Claude Desktop
# The MCP server will auto-start when you open Claude
```

### Option 2: Manual Setup

```bash
# Copy config to Claude Desktop
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
```

---

## What Was Configured

The NBA MCP Server is now configured to run via stdio (standard input/output) protocol, which is how Claude Desktop communicates with MCP servers.

**Configuration Details:**
- **Server Name:** `nba-mcp-synthesis`
- **Command:** `python -m mcp_server.server`
- **Working Directory:** `/Users/ryanranft/nba-mcp-synthesis`
- **Protocol:** stdio (no HTTP server needed)

**Environment Variables:**
Claude Desktop will inherit environment variables from your shell. Make sure these are set:
- `RDS_HOST`, `RDS_DATABASE`, `RDS_USERNAME`, `RDS_PASSWORD`
- `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `GLUE_DATABASE`
- `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY` (optional)
- `SLACK_WEBHOOK_URL` (optional)

---

## Testing the Integration

### 1. Check MCP Server Availability

After restarting Claude Desktop:
1. Look for the MCP tools indicator (usually a 🔌 icon or tools panel)
2. You should see "nba-mcp-synthesis" in the available servers
3. The server should show as "Connected" or "Active"

### 2. Test Queries

Try these test queries in Claude Desktop:

**Test 1: List Available Tools**
```
What MCP tools do you have available?
```

Expected: Claude should list NBA MCP tools including database queries, S3 access, etc.

**Test 2: Simple Database Query**
```
Using the NBA MCP tools, query the database and tell me how many tables are available.
```

Expected: Claude will call `list_tables` tool and return count.

**Test 3: Data Retrieval**
```
Using the NBA MCP tools, query the database for the first 5 games in the database.
SELECT * FROM games LIMIT 5;
```

Expected: Claude will execute the query and show game data.

**Test 4: S3 Data Access**
```
Using the NBA MCP tools, list some files in the S3 bucket. Show me what's available.
```

Expected: Claude will call `list_s3_files` and show file listings.

---

## Troubleshooting

### MCP Server Not Showing Up

**Check 1: Config File Location**
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Should show the NBA MCP server configuration.

**Check 2: Restart Claude Desktop**
- Completely quit Claude Desktop (Cmd+Q)
- Reopen it
- Wait 5-10 seconds for MCP servers to initialize

**Check 3: View Claude Desktop Logs**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

Look for error messages about the MCP server startup.

### Environment Variables Not Available

If Claude says "database connection failed" or similar:

**Solution:** Set environment variables system-wide

Create `~/.zshrc` (or `~/.bash_profile`) with:
```bash
# NBA MCP Environment
export RDS_HOST="your-rds-host"
export RDS_DATABASE="nba_simulator"
export RDS_USERNAME="your-username"
export RDS_PASSWORD="your-password"
export S3_BUCKET="your-bucket"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export GLUE_DATABASE="nba_raw_data"
```

Then:
```bash
source ~/.zshrc  # Apply changes
# Restart Claude Desktop
```

### MCP Server Crashes on Startup

**Check Server Logs:**
```bash
python -m mcp_server.server --test
```

If this fails, check:
- Python dependencies installed: `pip list | grep mcp`
- Database connectivity: Run `scripts/validate_environment.py`
- AWS credentials: `aws sts get-caller-identity`

---

## Advanced Configuration

### Enable Debug Logging

Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nba-mcp-synthesis": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "PYTHONPATH": "/Users/ryanranft/nba-mcp-synthesis",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_LOG_JSON": "true"
      }
    }
  }
}
```

### Add Additional MCP Servers

You can run multiple MCP servers. Edit the config:
```json
{
  "mcpServers": {
    "nba-mcp-synthesis": { ... },
    "another-server": { ... }
  }
}
```

---

## What You Can Do Now

With the MCP server integrated into Claude Desktop, you can:

1. **Natural Language Database Queries**
   - "Show me the top 10 teams by wins"
   - "What players scored over 30 points in their last game?"

2. **S3 Data Exploration**
   - "List game files for the Lakers from 2023"
   - "Show me what data is available in the S3 bucket"

3. **Schema Discovery**
   - "What tables are in the database?"
   - "Show me the schema for the games table"

4. **Complex Analysis**
   - "Analyze Stephen Curry's shooting performance this season"
   - "Compare Warriors vs Lakers head-to-head stats"

5. **Multi-Source Synthesis**
   - Claude can combine database queries, S3 data, and Glue metadata
   - Example: "Get player stats from the database and detailed game logs from S3"

---

## Next: Production Deployment

Once Claude Desktop integration is working, you're ready for production!

See: `PRODUCTION_DEPLOYMENT_GUIDE.md` for full deployment instructions.

---

**🎉 You're ready to use NBA data with Claude Desktop!**

After I help you test this integration, you mentioned wanting to read MCP books and repos for additional recommendations. I'm ready to review those once this is working!
