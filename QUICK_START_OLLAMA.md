# 🚀 Quick Start: Ollama + NBA MCP

**Your Setup**: ✅ Ollama running + 90 NBA MCP tools ready

---

## 🎯 Two Ways to Use Ollama with MCP

### **Method 1: In Cursor Chat** (Recommended)

1. **Configure Cursor Settings**:
   - Open `Cmd+Shift+P` → "Preferences: Open Settings (JSON)"
   - Add this:
   ```json
   {
     "cursor.chat.models": [
       {
         "id": "ollama-qwen-coder",
         "provider": "openai-compatible",
         "name": "Ollama Qwen2.5-Coder 32B",
         "baseURL": "http://localhost:11434/v1",
         "apiKey": "ollama",
         "model": "qwen2.5-coder:32b"
       }
     ]
   }
   ```

2. **Reload Cursor**: `Cmd+Shift+P` → "Reload Window"

3. **Switch Model**: Click model selector → Choose "Ollama Qwen2.5-Coder 32B"

4. **Test**: Ask "What MCP tools are available?"

---

### **Method 2: Standalone Chat Interface**

If Cursor doesn't support custom models, use the standalone chat:

```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 ollama_mcp_chat.py
```

**Features**:
- Interactive chat with Ollama
- Full access to 90 NBA MCP tools
- Streaming responses
- Commands:
  - `tools` - List all MCP tools
  - `clear` - Clear conversation
  - `exit` - Quit

**Example Session**:
```
You: What kinds of data can you help me with?

🤖 Ollama: I have access to 90 NBA tools! I can help you with:
- Database queries (query_database)
- Listing games and players (list_games, list_players)
- Table schemas (get_table_schema, list_tables)
- S3 data access (list_s3_files)
- And much more!

You: Show me the first 5 players

🤖 Ollama: I would use the query_database tool with:
SELECT * FROM players LIMIT 5
...
```

---

## 📊 Test Your Setup

Run this quick test:
```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 test_ollama_mcp.py
```

Should show:
```
✅ Ollama Connection: PASS
✅ MCP Server: PASS
✅ Integration: PASS
```

---

## 🔧 Your Configuration

**Ollama**:
- ✅ Version: 0.12.5
- ✅ Model: qwen2.5-coder:32b (19GB)
- ✅ Running on: http://localhost:11434

**MCP Server**:
- ✅ Tools: 90 NBA tools
- ✅ Config: ~/.cursor/mcp.json
- ✅ Server: mcp_server.fastmcp_server

**Python**:
- ✅ Path: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
- ✅ Project: /Users/ryanranft/nba-mcp-synthesis

---

## 🎯 Quick Commands

```bash
# Start Ollama (if not running)
ollama serve &

# Test MCP server
cd /Users/ryanranft/nba-mcp-synthesis
python3 test_mcp_tools.py

# Test Ollama + MCP integration
python3 test_ollama_mcp.py

# Launch standalone chat
python3 ollama_mcp_chat.py

# List Ollama models
ollama list

# Download more models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct
```

---

## 💡 Example Prompts for Testing

Once connected, try:

1. **List Tools**:
   - "What MCP tools are available?"
   - "Show me all database-related tools"

2. **Query Data**:
   - "Use the list_tables tool to show all tables"
   - "Query the players table for the top 5 scorers"

3. **Explore**:
   - "What kinds of NBA data can you access?"
   - "Show me the schema for the games table"

---

## 📚 Files Created

- `OLLAMA_MCP_SETUP_GUIDE.md` - Complete setup guide
- `test_ollama_mcp.py` - Integration test script
- `ollama_mcp_chat.py` - Standalone chat interface
- `test_mcp_tools.py` - MCP server test
- `QUICK_START_OLLAMA.md` - This file

---

## ✅ Status

- [✅] Ollama installed and running
- [✅] Qwen2.5-Coder 32B model ready
- [✅] MCP server working (90 tools)
- [✅] Integration tested and verified
- [⏳] Cursor configuration (user action needed)
- [⏳] Ready to chat!

---

**Next Step**: Choose Method 1 or Method 2 above and start chatting! 🚀




