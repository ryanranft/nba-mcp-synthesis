# MCP Setup Summary

Complete guide to using MCP servers with Claude Code (CLI and Web).

---

## Quick Reference

### What Works Now ✅

**Claude Code CLI (on your Mac):**
```bash
claude
# MCP servers available:
# - nba-mcp-server ✓ Connected
# - nba-ddl-server ✓ Connected
# - filesystem ✓ Connected
```

**Configuration Location:** `~/.claude.json`

### What's Experimental 🧪

**Claude Code Web (claude.ai/code):**
- Custom MCP servers via HTTP transport
- Requires HTTP bridge + ngrok tunnel
- **Status:** Unknown if supported

---

## Architecture Comparison

### CLI Architecture
```
┌─────────────────────────┐
│ Your Mac                │
│                         │
│ ┌─────────────────┐    │
│ │ Claude CLI      │    │
│ └────────┬────────┘    │
│          │ stdio        │
│ ┌────────▼────────┐    │
│ │ MCP Servers     │    │
│ │ (local process) │    │
│ └─────────────────┘    │
│                         │
└─────────────────────────┘
```

**Pros:**
- Direct stdio communication
- Low latency
- Fully supported
- Works perfectly now

**Cons:**
- Terminal-only interface
- No browser UI

### Web Architecture (Current - Doesn't Work)
```
Your Mac                          Remote Container
┌──────────────┐                 ┌─────────────────┐
│ MCP Servers  │                 │ Web Claude Code │
│ (local)      │    ✗ Can't      │                 │
│              │    access       │                 │
└──────────────┘                 └─────────────────┘
```

**Problem:** Web runs in remote container, can't access your local processes.

### Web Architecture (HTTP Bridge - Experimental)
```
Your Mac                          Remote Container
┌──────────────┐                 ┌─────────────────┐
│ MCP Servers  │                 │ Web Claude Code │
│     ↓        │                 │        │        │
│ HTTP Wrapper │                 │        │        │
│     ↓        │                 │        │        │
│ ngrok Tunnel │◄────HTTPS───────┤        │        │
│ (public URL) │                 │        ▼        │
└──────────────┘                 │  Your MCP Tools │
                                 └─────────────────┘
```

**If supported:**
- Browser UI
- Remote access
- Shareable ngrok URL

**Unknown:**
- Does web support HTTP transport?
- Will it read .mcp.json?
- Security restrictions?

---

## Setup Status

### ✅ Completed

1. **CLI Configuration** (Working)
   - File: `~/.claude.json`
   - Servers: nba-mcp-server, nba-ddl-server, filesystem
   - Status: All connected

2. **Web Configuration Files** (Created)
   - `.claude/mcp.json` - Primary config
   - `.mcp.json` - Fallback config
   - Status: Committed to git

3. **HTTP Bridge Solution** (Ready to test)
   - `http_mcp_wrapper.py` - HTTP wrapper
   - `mcp_bridge.sh` - Automated setup
   - `HTTP_MCP_WORKAROUND_GUIDE.md` - Complete guide
   - Status: All files created, not tested yet

### ❓ Unknown

1. **Web Support for HTTP MCP**
   - Need to test in fresh session
   - May not be supported in web version
   - Waiting for confirmation

### ❌ Known Issues

1. **Missing Python Dependencies in Web Container**
   - `mcp` package not installed
   - Can't run stdio MCP servers directly in web
   - **Solution:** HTTP bridge bypasses this

2. **Missing DDL Server**
   - Config references `mcp_server.ddl_server`
   - File doesn't exist in repository
   - **Solution:** Remove from config or create file

---

## Files Created

### Configuration Files
```
.claude/mcp.json          # Primary MCP config for web
.mcp.json                 # Fallback MCP config for web
~/.claude.json            # CLI MCP config (on your Mac)
```

### HTTP Bridge Files
```
http_mcp_wrapper.py       # HTTP wrapper for stdio MCP servers
mcp_bridge.sh             # Automated bridge startup script
HTTP_MCP_WORKAROUND_GUIDE.md  # Complete setup guide
MCP_SETUP_SUMMARY.md      # This file
```

### Existing Config Files
```
.cursor/mcp.json                        # Cursor IDE config
config/cursor_mcp_config.json           # Cursor config backup
config/claude_desktop_config_fastmcp.json  # Desktop config
```

---

## Testing Checklist

### To Test HTTP Bridge:

- [ ] On Mac: Install ngrok (`brew install ngrok`)
- [ ] On Mac: Install Python deps (`pip install fastapi uvicorn`)
- [ ] On Mac: Run `./mcp_bridge.sh`
- [ ] On Mac: Get ngrok URL from http://localhost:4040
- [ ] Update `.mcp.json` with ngrok URL
- [ ] Close current web session
- [ ] Start fresh session at https://claude.ai/code
- [ ] Check available tools for custom MCP servers
- [ ] Report: Does it work? ✅ or ❌

### If HTTP Bridge Works:
- [ ] Document your exact config
- [ ] Test MCP tool functionality
- [ ] Consider ngrok security (paid tier for auth)
- [ ] Share findings with community

### If HTTP Bridge Doesn't Work:
- [ ] Use CLI version for MCP tasks
- [ ] Contact Claude Code support
- [ ] Request HTTP transport support
- [ ] Wait for official web MCP support

---

## Recommended Next Actions

### Immediate (5 minutes)
1. **Test the HTTP bridge** using `mcp_bridge.sh`
2. **Try in fresh web session**
3. **Determine if it works**

### If Works (15 minutes)
1. Document exact setup
2. Add authentication to ngrok
3. Create startup documentation
4. Use regularly

### If Doesn't Work (Now)
1. Continue using CLI version
2. Contact support for official guidance
3. Monitor for web MCP updates
4. Consider this closed for now

---

## Support and Resources

### Claude Code
- Documentation: https://docs.claude.com/claude-code
- Issues: https://github.com/anthropics/claude-code/issues
- Support: https://support.claude.com

### MCP Protocol
- Documentation: https://modelcontextprotocol.io
- Specification: https://spec.modelcontextprotocol.io
- Examples: https://github.com/modelcontextprotocol

### ngrok
- Documentation: https://ngrok.com/docs
- Dashboard: http://localhost:4040 (when running)
- Pricing: https://ngrok.com/pricing

---

## Key Insights

### Architecture Mismatch is Real
- CLI and Web run in fundamentally different environments
- Can't just copy CLI config to web
- Need bridge solution (HTTP) or different approach

### HTTP Transport is Standard
- MCP protocol supports multiple transports: stdio, HTTP, SSE
- HTTP is designed for remote access
- Should work in theory, needs testing in practice

### Web May Have Restrictions
- Sandboxed environment
- Security constraints
- May not allow custom MCP servers
- Unknown until tested

### CLI Already Works
- Don't need to solve this for immediate work
- Can use CLI for MCP-dependent tasks
- Web would be nice-to-have, not required

---

## Decision Matrix

| Scenario | Recommended Action |
|----------|-------------------|
| Need MCP now | Use CLI version |
| Want to experiment | Try HTTP bridge |
| HTTP bridge works | Document and use |
| HTTP bridge fails | Stay with CLI, contact support |
| Web adds official MCP | Switch to native config |

---

## Conclusion

**What we know:**
- ✅ CLI works perfectly
- ✅ HTTP bridge is ready to test
- ❓ Web support unknown

**What to do:**
1. Test HTTP bridge (quick experiment)
2. If works: Great! Use it.
3. If fails: Use CLI, it's already working.

**Time investment:**
- Testing: 5-10 minutes
- If works: 15-30 minutes to productionize
- If fails: 0 minutes (use CLI)

**Risk:**
- Low - worst case, use CLI
- Best case - get web UI + MCP servers

Worth trying! 🚀
