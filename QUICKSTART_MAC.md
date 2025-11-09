# Quick Start: HTTP MCP Bridge on Mac

**Updated Version with Auto-Config!** 🎉

The HTTP wrapper now automatically reads your MCP configuration and adapts paths for Mac.

---

## What's New ✨

- ✅ **Auto-loads config** from `.claude/mcp.json`
- ✅ **Auto-adapts paths** from Linux to Mac
- ✅ **Supports all your MCP servers**:
  - `nba-mcp-server`
  - `nba-ddl-server` (if exists)
  - `filesystem`
- ✅ **New `/servers` endpoint** to verify config

---

## Quick Setup (3 Commands)

### On Your Mac Terminal:

```bash
# 1. Go to your project
cd ~/nba-mcp-synthesis

# 2. Pull the latest git version
git fetch origin
git checkout claude/test-mcp-web-support-011CUwNJLpgkaPqzGDzNar7v
git pull

# 3. Run the automated setup script
./run_git_mcp_bridge.sh
```

**That's it!** The script (created by Claude Desktop) will:
- Install Python dependencies
- Check for ngrok
- Start the HTTP wrapper
- Launch ngrok tunnel
- Show you the public URL

---

## Manual Setup (If You Prefer)

### Step 1: Install Dependencies

```bash
# Python packages
pip install fastapi uvicorn

# ngrok (one-time)
brew install ngrok
```

### Step 2: Start HTTP Wrapper

```bash
cd ~/nba-mcp-synthesis
python3 http_mcp_wrapper.py --port 8080
```

**What happens:**
- Loads config from `.claude/mcp.json`
- Adapts Linux paths (`/home/user/`) to Mac paths (`/Users/yourname/`)
- Starts FastAPI server on http://localhost:8080

### Step 3: Test Locally

```bash
# Check health
curl http://localhost:8080/health

# List available servers
curl http://localhost:8080/servers

# You should see:
# {
#   "available_servers": ["nba-mcp-server", "nba-ddl-server", "filesystem"],
#   "running_servers": [],
#   ...
# }
```

### Step 4: Expose via ngrok

```bash
# In a new terminal
ngrok http 8080
```

**Get your URL:**
- Open http://localhost:4040
- Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

---

## Configure Web Claude Code

### Update .mcp.json with your ngrok URL:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "transport": "http",
      "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/nba-mcp-server/message"
    },
    "nba-ddl-server": {
      "transport": "http",
      "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/nba-ddl-server/message"
    },
    "filesystem": {
      "transport": "http",
      "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/filesystem/message"
    }
  }
}
```

**Important:** Replace `YOUR-NGROK-URL` with your actual ngrok URL!

---

## Test in Web Claude Code

1. **Commit the .mcp.json config:**
   ```bash
   git add .mcp.json
   git commit -m "Add HTTP transport MCP config for web"
   git push
   ```

2. **Close current web session**

3. **Start fresh session** at https://claude.ai/code

4. **Check available tools** - Look for your custom MCP tools

---

## Verify It's Working

### Expected MCP Tools (if HTTP transport is supported):

**From nba-mcp-server:**
- `query_database`
- `list_tables`
- `get_table_schema`
- `list_s3_files`
- (and more...)

**From nba-ddl-server:**
- DDL-related tools (if server exists)

**From filesystem:**
- File operation tools

### If You Don't See Custom Tools:

Web-based Claude Code may not support HTTP transport MCP servers yet. In that case:

**Use CLI instead:**
```bash
claude  # On your Mac
# Full MCP access via stdio
```

---

## Architecture Diagram

```
┌─────────────────────────────────────┐
│ Your Mac                            │
│                                     │
│  .claude/mcp.json                   │
│         ↓                           │
│  http_mcp_wrapper.py                │
│  - Reads config                     │
│  - Adapts paths (Linux → Mac)      │
│  - Starts MCP servers               │
│  - Exposes HTTP endpoints           │
│         ↓                           │
│  FastAPI Server (:8080)             │
│         ↓                           │
│  ngrok Tunnel                       │
│  (https://abc123.ngrok.io)         │
└────────────┬────────────────────────┘
             │
             │ HTTPS
             ↓
    ┌────────────────────┐
    │ Web Container      │
    │ (claude.ai/code)   │
    │                    │
    │ Reads .mcp.json    │
    │ Connects via HTTP  │
    └────────────────────┘
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install fastapi uvicorn
```

### "ngrok: command not found"
```bash
brew install ngrok
```

### "No MCP config file found"
The wrapper looks for config in this order:
1. `.claude/mcp.json` (in project directory)
2. `.mcp.json` (in project directory)
3. `~/.claude.json` (in home directory)

Make sure at least one exists!

### "Unknown server: xyz"
Check available servers:
```bash
curl http://localhost:8080/servers
```

The server name must exactly match what's in your config.

### Web Claude Code doesn't see MCP tools

This likely means web interface doesn't support HTTP transport yet.

**Solutions:**
1. Use CLI version (already works perfectly)
2. Contact Claude Code support
3. Wait for official web MCP support

---

## Security Notes

### ngrok Free Tier:
- Public URLs (anyone with URL can access)
- URLs change on restart
- No built-in authentication

### Recommendations:
1. **Stop bridge when not in use**
2. **Use ngrok paid tier** for:
   - Custom domains
   - Password protection
   - Persistent URLs
3. **Add API keys** to your MCP servers if they support it

---

## Files Reference

### Created by this setup:
- `http_mcp_wrapper.py` - HTTP wrapper (auto-config, path adaptation)
- `mcp_bridge.sh` - Startup script
- `run_git_mcp_bridge.sh` - Automated setup (from Claude Desktop)
- `HTTP_MCP_WORKAROUND_GUIDE.md` - Detailed guide
- `MCP_SETUP_SUMMARY.md` - Overview
- `QUICKSTART_MAC.md` - This file

### Your existing configs:
- `.claude/mcp.json` - MCP config (stdio transport)
- `.mcp.json` - MCP config (will add HTTP transport)

---

## Next Steps

1. ✅ Run `./run_git_mcp_bridge.sh` on your Mac
2. ✅ Get ngrok URL
3. ✅ Update `.mcp.json` with ngrok URL
4. ✅ Test in fresh web session
5. 📝 Report findings: Does it work? ✅ or ❌

---

## Support

- HTTP wrapper issues: Check logs at `http://localhost:8080/health`
- MCP server issues: Check your `~/.claude.json` config
- Web Claude Code: https://docs.claude.com/claude-code
- ngrok issues: http://localhost:4040 (dashboard)

Good luck! 🚀
