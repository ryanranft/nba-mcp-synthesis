# HTTP MCP Bridge - Complete Setup

**Bridge your Mac-based MCP servers to web-based Claude Code**

---

## 📋 Quick Status

| Component | Status | Location |
|-----------|--------|----------|
| HTTP Wrapper | ✅ Ready | `http_mcp_wrapper.py` |
| Config Auto-loading | ✅ Implemented | Reads `.claude/mcp.json` |
| Path Adaptation | ✅ Implemented | Linux → Mac automatic |
| Bridge Script | ✅ Ready | `mcp_bridge.sh` |
| Setup Script | ✅ Ready | `run_git_mcp_bridge.sh` (Desktop) |
| Documentation | ✅ Complete | Multiple guides |
| Git Branch | ✅ Pushed | `claude/test-mcp-web-support-011CUwNJLpgkaPqzGDzNar7v` |

---

## 🎯 What This Solves

**Problem:**
- CLI Claude Code: Runs on Mac, can access local MCP servers ✅
- Web Claude Code: Runs in remote container, can't access Mac ❌

**Solution:**
```
Mac MCP Servers → HTTP Wrapper → ngrok → Web Container
     (stdio)         (HTTP)      (HTTPS)    (connects!)
```

---

## 🚀 30-Second Start

On your Mac:

```bash
cd ~/nba-mcp-synthesis
git pull origin claude/test-mcp-web-support-011CUwNJLpgkaPqzGDzNar7v
./mcp_bridge.sh
```

Then follow the prompts!

---

## 📚 Documentation Files

Choose your style:

1. **QUICKSTART_MAC.md** ⭐
   - Mac-specific instructions
   - 3-command setup
   - Troubleshooting

2. **HTTP_MCP_WORKAROUND_GUIDE.md**
   - Detailed technical guide
   - 3 different approaches
   - Security considerations

3. **MCP_SETUP_SUMMARY.md**
   - High-level overview
   - Architecture diagrams
   - Decision matrix

4. **README_HTTP_MCP_BRIDGE.md** (this file)
   - Quick reference
   - Links to everything

---

## 🔧 How It Works

### Step 1: HTTP Wrapper Loads Your Config

```python
# http_mcp_wrapper.py automatically:
1. Finds .claude/mcp.json
2. Loads MCP server configurations
3. Adapts paths: /home/user/ → /Users/yourname/
4. Exposes servers via HTTP endpoints
```

### Step 2: ngrok Creates Public URL

```bash
ngrok http 8080
# Creates: https://abc123.ngrok.io
```

### Step 3: Web Claude Code Connects

```json
// .mcp.json
{
  "mcpServers": {
    "nba-mcp-server": {
      "transport": "http",
      "url": "https://abc123.ngrok.io/mcp/nba-mcp-server/message"
    }
  }
}
```

---

## 🎨 Architecture

```
┌──────────────────────────────────────────────────────┐
│ Your Mac (ryanranft)                                 │
│                                                      │
│  ~/.claude.json  OR  .claude/mcp.json               │
│  ┌────────────────────────────────────────┐         │
│  │ {                                      │         │
│  │   "mcpServers": {                      │         │
│  │     "nba-mcp-server": {                │         │
│  │       "command": "python3",            │         │
│  │       "args": ["-m", "..."],           │         │
│  │       "cwd": "/Users/..."  ◄─── Auto-adapted     │
│  │     }                                  │         │
│  │   }                                    │         │
│  │ }                                      │         │
│  └────────────────┬───────────────────────┘         │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────┐         │
│  │ http_mcp_wrapper.py                    │         │
│  │ - Reads config                         │         │
│  │ - Starts MCP servers (stdio)           │         │
│  │ - Wraps with HTTP/JSON-RPC             │         │
│  │ - FastAPI server on :8080              │         │
│  └────────────────┬───────────────────────┘         │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────┐         │
│  │ ngrok                                  │         │
│  │ https://abc123.ngrok.io → :8080       │         │
│  └────────────────┬───────────────────────┘         │
│                   │                                  │
└───────────────────┼──────────────────────────────────┘
                    │
                    │ HTTPS (public internet)
                    │
        ┌───────────▼──────────────────────────┐
        │ Web Container (claude.ai/code)       │
        │                                      │
        │  .mcp.json:                          │
        │  {                                   │
        │    "transport": "http",              │
        │    "url": "https://abc123.ngrok.io"  │
        │  }                                   │
        │                                      │
        │  ✨ Your MCP tools now available!   │
        └──────────────────────────────────────┘
```

---

## 🛠 Features

### Auto-Configuration ✨
- No hardcoded paths
- Reads from your existing MCP config
- Automatically converts Linux paths to Mac paths

### Multi-Server Support
- `nba-mcp-server` ✅
- `nba-ddl-server` ✅
- `filesystem` ✅
- Add more by updating `.claude/mcp.json`

### Monitoring Endpoints
```bash
# Health check
curl http://localhost:8080/health

# List all servers
curl http://localhost:8080/servers
```

### Clean Shutdown
- Gracefully stops all MCP servers
- No orphaned processes

---

## 📦 What You Get

After pulling the git branch:

```
nba-mcp-synthesis/
├── http_mcp_wrapper.py          # Main HTTP wrapper
├── mcp_bridge.sh                # Automated startup
├── QUICKSTART_MAC.md            # Quick start guide
├── HTTP_MCP_WORKAROUND_GUIDE.md # Detailed guide
├── MCP_SETUP_SUMMARY.md         # Overview
├── README_HTTP_MCP_BRIDGE.md    # This file
├── .claude/
│   └── mcp.json                 # Your MCP config (stdio)
└── .mcp.json                    # Will add HTTP config here
```

Plus from Claude Desktop:
```
nba-simulator-aws/
└── run_git_mcp_bridge.sh        # Automated git setup
```

---

## ⚡ Testing Checklist

### Phase 1: Local Testing (Mac)
- [ ] Pull git branch
- [ ] Install dependencies (`pip install fastapi uvicorn`)
- [ ] Start HTTP wrapper (`python3 http_mcp_wrapper.py`)
- [ ] Verify config loaded (check logs)
- [ ] Test `/health` endpoint
- [ ] Test `/servers` endpoint

### Phase 2: Tunnel Testing
- [ ] Install ngrok (`brew install ngrok`)
- [ ] Start ngrok (`ngrok http 8080`)
- [ ] Get public URL from http://localhost:4040
- [ ] Test public health endpoint

### Phase 3: Web Claude Code Testing
- [ ] Update `.mcp.json` with ngrok URL
- [ ] Commit and push config
- [ ] Close current web session
- [ ] Start fresh web session
- [ ] Check available tools
- [ ] Test MCP tool functionality

---

## 🎯 Expected Results

### If It Works ✅
You'll see custom MCP tools in web Claude Code:
- `query_database`
- `list_tables`
- `get_table_schema`
- `list_s3_files`
- And more!

### If It Doesn't Work ❌
Web interface may not support HTTP transport MCP yet.

**Fallback:**
- Use CLI Claude Code (already working perfectly)
- Contact support
- Wait for official web MCP support

---

## 🔒 Security Notes

### Current Setup (ngrok free):
- ⚠️ Public URLs (anyone with URL can access)
- ⚠️ No authentication
- ⚠️ URLs change on restart

### Recommended Improvements:
1. **Use ngrok paid tier**
   - Custom domains
   - Password protection
   - Persistent URLs

2. **Add authentication headers**
   ```json
   {
     "transport": "http",
     "url": "https://...",
     "headers": {
       "Authorization": "Bearer YOUR-SECRET-TOKEN"
     }
   }
   ```

3. **Stop bridge when not in use**
   ```bash
   # Ctrl+C to stop
   # Or kill processes manually
   ```

---

## 🐛 Troubleshooting

### "No MCP config file found"
**Fix:** Ensure `.claude/mcp.json` exists
```bash
ls -la .claude/mcp.json
```

### "Unknown server: xyz"
**Fix:** Check available servers
```bash
curl http://localhost:8080/servers
```

### Web Claude Code doesn't see tools
**Possible causes:**
1. Web doesn't support HTTP transport (likely)
2. `.mcp.json` not committed/pushed
3. Wrong ngrok URL in config
4. ngrok tunnel down

**Debug:**
```bash
# Check ngrok is running
curl https://YOUR-NGROK-URL.ngrok.io/health

# Should return: {"status": "healthy", ...}
```

---

## 📞 Support

### HTTP Bridge Issues:
- Check logs: Console output from `http_mcp_wrapper.py`
- Check ngrok: http://localhost:4040

### MCP Server Issues:
- Verify CLI works: `claude` (on Mac)
- Check config: `cat ~/.claude.json` or `.claude/mcp.json`

### Web Claude Code Issues:
- Documentation: https://docs.claude.com/claude-code
- Support: https://support.claude.com
- Issues: https://github.com/anthropics/claude-code/issues

---

## 🎓 Learn More

### MCP Protocol:
- https://modelcontextprotocol.io
- https://spec.modelcontextprotocol.io

### FastAPI (HTTP framework used):
- https://fastapi.tiangolo.com

### ngrok (tunneling):
- https://ngrok.com/docs

---

## 🚦 Current Status

**Ready to test!** 🎉

All code is:
- ✅ Committed to git
- ✅ Pushed to remote
- ✅ Documented
- ✅ Tested locally (logic)
- ❓ Needs testing on Mac
- ❓ Needs testing in web Claude Code

---

## 🎬 Next Actions

**For You:**
1. Pull git branch on Mac
2. Run `./mcp_bridge.sh` or `./run_git_mcp_bridge.sh`
3. Get ngrok URL
4. Update `.mcp.json`
5. Test in web session
6. Report findings!

**For Support (if needed):**
- Report whether HTTP transport works in web
- Share findings with community
- Help improve documentation

---

## 🙏 Credits

- **Architecture**: Identified Mac/Web environment mismatch
- **Solution**: HTTP transport + ngrok tunnel
- **Implementation**: FastAPI wrapper with auto-config
- **Testing**: Pending your results!

---

**Let's make this work!** 🚀

Start with: `./mcp_bridge.sh`
