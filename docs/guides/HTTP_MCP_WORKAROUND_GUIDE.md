# HTTP MCP Workaround Guide

## Problem Statement

**Architecture Mismatch:**
- **CLI Version**: Runs on your Mac, can access local MCP servers via stdio
- **Web Version**: Runs in remote Linux container, cannot access your Mac's processes

**Solution:** Expose your Mac-based MCP servers via HTTP so the web container can connect to them remotely.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Your Mac                                                    │
│                                                             │
│  ┌─────────────────┐                                       │
│  │ MCP Server      │                                       │
│  │ (stdio process) │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│  ┌────────▼────────┐                                       │
│  │ HTTP Wrapper    │                                       │
│  │ (FastAPI/uvicorn)│                                      │
│  └────────┬────────┘                                       │
│           │                                                 │
│  ┌────────▼────────┐                                       │
│  │ ngrok Tunnel    │                                       │
│  │ (HTTPS public)  │◄──────────────┐                      │
│  └─────────────────┘                │                      │
└─────────────────────────────────────┼──────────────────────┘
                                      │
                                      │ HTTPS
                                      │
                         ┌────────────▼─────────────┐
                         │ Web Container            │
                         │ (claude.ai/code)         │
                         │                          │
                         │ Connects to ngrok URL    │
                         └──────────────────────────┘
```

---

## Approach 1: Automated Bridge Script (Easiest)

### Prerequisites
```bash
# Install ngrok (one-time setup)
brew install ngrok

# Ensure Python dependencies
pip install fastapi uvicorn
```

### Steps

1. **Start the bridge:**
   ```bash
   cd ~/nba-mcp-synthesis
   ./mcp_bridge.sh
   ```

2. **Get your ngrok URL:**
   - Open http://localhost:4040 in your browser
   - Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)

3. **Configure web-based Claude Code:**

   Create `.mcp.json` in your project:
   ```json
   {
     "mcpServers": {
       "nba-mcp-server": {
         "transport": "http",
         "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/nba-mcp-server/message"
       },
       "filesystem": {
         "transport": "http",
         "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/filesystem/message"
       }
     }
   }
   ```

4. **Test in web-based Claude Code:**
   - Close current session
   - Start fresh session at https://claude.ai/code
   - Check available tools for MCP server tools

---

## Approach 2: Manual HTTP Wrapper (More Control)

### Start the HTTP wrapper manually:

```bash
cd ~/nba-mcp-synthesis
python3 http_mcp_wrapper.py --host 0.0.0.0 --port 8080
```

### Expose via ngrok:

```bash
ngrok http 8080
```

### Configure as in Approach 1

---

## Approach 3: Use Existing MCP HTTP Servers (If Available)

Some MCP servers natively support HTTP transport. Check your server documentation:

```bash
# Example: If your server supports HTTP directly
python3 -m mcp_server.fastmcp_server --transport http --port 8080
```

Then expose via ngrok as above.

---

## Testing the Connection

### 1. Test HTTP wrapper locally:

```bash
# Health check
curl http://localhost:8080/health

# Test MCP request
curl -X POST http://localhost:8080/mcp/nba-mcp-server/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### 2. Test ngrok tunnel:

```bash
# Replace with your ngrok URL
curl https://YOUR-NGROK-URL.ngrok.io/health
```

### 3. Test in web-based Claude Code:

Start a fresh session and check available tools.

---

## Configuration Reference

### .mcp.json for HTTP Transport

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "transport": "http",
      "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/nba-mcp-server/message",
      "headers": {
        "Authorization": "Bearer YOUR-TOKEN"
      }
    }
  }
}
```

### .mcp.json for stdio Transport (CLI only)

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "python3",
      "args": ["-m", "mcp_server.fastmcp_server"],
      "cwd": "/path/to/project",
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

---

## Troubleshooting

### Problem: "Connection refused"
**Solution:** Ensure HTTP wrapper is running:
```bash
ps aux | grep http_mcp_wrapper
```

### Problem: "ngrok tunnel not found"
**Solution:** Check ngrok dashboard at http://localhost:4040

### Problem: "MCP server not responding"
**Solution:** Check server logs:
```bash
# Check if MCP server process is running
ps aux | grep mcp_server

# Test directly
python3 -m mcp_server.fastmcp_server
```

### Problem: "Web Claude Code doesn't see custom MCP tools"
**Possible causes:**
1. Web interface may not support HTTP transport MCP servers
2. `.mcp.json` config not being read
3. Security restrictions in web container
4. ngrok URL not accessible from web container

**Solution:** Verify with support or use CLI version which definitely works.

---

## Security Considerations

### ngrok Free Tier
- URLs are public but randomized
- Anyone with the URL can access your MCP servers
- URLs change on restart

### Recommendations:
1. **Use authentication headers** in `.mcp.json` config
2. **Use ngrok paid tier** for custom domains and password protection
3. **Only expose necessary servers**
4. **Monitor ngrok dashboard** for unexpected traffic
5. **Stop bridge when not in use**

---

## Alternative: Use Claude Code CLI

If the HTTP workaround doesn't work (web interface may not support HTTP transport), your CLI setup already works perfectly:

```bash
# On your Mac
cd ~/nba-mcp-synthesis
claude

# Then use MCP tools:
# "Use nba-mcp-server to query player stats"
# "Use filesystem to analyze project files"
```

---

## Expected Outcome

### If HTTP Transport Works ✅
- You'll see custom MCP tools in web-based Claude Code
- Can use MCP servers from web interface
- Best of both worlds!

### If HTTP Transport Doesn't Work ❌
- Web interface may not support custom MCP servers
- Use CLI version for MCP-dependent tasks
- Contact support to request feature

---

## Next Steps

1. **Try the automated script** (`./mcp_bridge.sh`)
2. **Test in fresh web session**
3. **Report findings** (does it work or not?)
4. **If works:** Document your setup
5. **If fails:** Use CLI version or contact support

---

## Files Reference

- `http_mcp_wrapper.py` - HTTP wrapper for stdio MCP servers
- `mcp_bridge.sh` - Automated setup script
- `.mcp.json` - MCP server configuration for web
- `.claude/mcp.json` - Alternative config location

---

## Support Resources

- MCP Documentation: https://modelcontextprotocol.io
- ngrok Documentation: https://ngrok.com/docs
- Claude Code Documentation: https://docs.claude.com/claude-code
- Report Issues: https://github.com/anthropics/claude-code/issues
