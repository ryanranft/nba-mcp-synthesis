# 🚀 Using Ollama with NBA MCP Tools in Cursor

**Goal**: Use local Ollama models (like Qwen2.5-Coder 32B) to interact with your 90 NBA MCP tools directly in Cursor chat.

---

## ✅ Your Current Setup

- **Ollama Version**: 0.12.5
- **Installed Model**: `qwen2.5-coder:32b` (19 GB)
- **MCP Server**: 90 NBA tools ready
- **MCP Config**: `/Users/ryanranft/.cursor/mcp.json` ✅

---

## 🎯 Architecture Overview

```
┌─────────────────┐
│  Cursor Chat    │
│  (This Window)  │
└────────┬────────┘
         │ Can use different AI models
         ├─────────────┬─────────────┐
         │             │             │
    ┌────▼────┐   ┌───▼────┐   ┌───▼──────┐
    │ Claude  │   │ GPT-4  │   │ Ollama   │
    │ Sonnet  │   │        │   │ (Local)  │
    └────┬────┘   └───┬────┘   └───┬──────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
              ┌────────▼────────┐
              │   MCP Server    │
              │  (90 NBA Tools) │
              └─────────────────┘
```

---

## 📋 Step-by-Step Setup

### Step 1: Ensure Ollama is Running

```bash
# Check if Ollama service is running
ollama list

# If not running, start it
ollama serve &
```

**Your Status**: ✅ Ollama is installed and has `qwen2.5-coder:32b`

---

### Step 2: Update Ollama (Optional but Recommended)

Your client version (0.11.6) is older than server (0.12.5). Update:

```bash
# Update Ollama via Homebrew
brew upgrade ollama

# Or download from: https://ollama.ai/download
```

---

### Step 3: Configure Cursor to Use Ollama

#### Option A: Via Cursor Settings (Recommended)

1. **Open Cursor Settings**:
   - Press `Cmd+,` (or `File` → `Settings`)

2. **Find "Language Model" or "AI Model" Settings**:
   - Look for sections like:
     - "Cursor AI"
     - "Language Model Provider"
     - "OpenAI Compatible"

3. **Add Ollama as a Provider**:
   - **Provider Type**: OpenAI Compatible / Custom
   - **Base URL**: `http://localhost:11434/v1`
   - **API Key**: `ollama` (or leave blank)
   - **Model**: `qwen2.5-coder:32b`

#### Option B: Via Cursor Configuration File

1. **Locate Cursor Settings File**:
   ```bash
   # Usually at:
   ~/.cursor/settings.json
   # Or
   ~/Library/Application Support/Cursor/User/settings.json
   ```

2. **Add Ollama Configuration**:
   ```json
   {
     "cursor.chat.models": [
       {
         "id": "ollama-qwen2.5-coder",
         "provider": "openai-compatible",
         "baseURL": "http://localhost:11434/v1",
         "apiKey": "ollama",
         "model": "qwen2.5-coder:32b"
       }
     ]
   }
   ```

---

### Step 4: Verify MCP Configuration

Your MCP configuration should already be set (we did this earlier):

```bash
cat ~/.cursor/mcp.json
```

Should show:
```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
      "args": ["-m", "mcp_server.fastmcp_server"],
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

**Status**: ✅ Already configured

---

### Step 5: Start Ollama Server

```bash
# Make sure Ollama is running
ollama serve
```

Or run it in the background:
```bash
# Check if already running
ps aux | grep ollama

# If not running, start it
nohup ollama serve > /tmp/ollama.log 2>&1 &
```

---

### Step 6: Reload Cursor

1. **Reload Cursor Window**:
   - Press `Cmd+Shift+P`
   - Type "Reload Window"
   - Press Enter

2. **Or Restart Cursor**:
   - Quit: `Cmd+Q`
   - Reopen Cursor

---

### Step 7: Select Ollama Model in Chat

1. **In Cursor Chat** (this window):
   - Look for model selector dropdown (usually top-right or near chat input)
   - Click it and select your Ollama model: `ollama-qwen2.5-coder` or `qwen2.5-coder:32b`

2. **Alternative Method**:
   - Click on the model name in the chat interface
   - Switch from "Claude Sonnet" to your Ollama model

---

## 🧪 Testing the Setup

### Test 1: Basic Ollama Response
After switching to Ollama model, ask:
```
Hello! Can you confirm you're running on Ollama?
```

### Test 2: List MCP Tools
```
What MCP tools are available to you?
```

Expected: Should list 90 NBA MCP tools

### Test 3: Use an MCP Tool
```
Use the list_tables MCP tool to show me all available NBA database tables.
```

### Test 4: Query Database
```
Use the query_database MCP tool to SELECT * FROM players LIMIT 5
```

---

## 🎨 Recommended Ollama Models for MCP

If you want to try other models optimized for tool use:

```bash
# Mistral models (good for function calling)
ollama pull mistral:7b-instruct

# Llama 3.1 (excellent for tool use)
ollama pull llama3.1:8b

# Qwen2.5-Coder (you already have this - great for code & tools)
ollama pull qwen2.5-coder:32b

# DeepSeek Coder (specialized for coding tasks)
ollama pull deepseek-coder:33b
```

---

## 🔧 Troubleshooting

### Issue 1: Ollama Not Appearing in Cursor

**Solution**:
1. Check if Cursor has OpenAI-compatible provider support
2. Try updating Cursor to latest version
3. Use Cursor's built-in Ollama integration if available

### Issue 2: MCP Tools Not Available

**Solution**:
```bash
# Test MCP server manually
cd /Users/ryanranft/nba-mcp-synthesis
python3 test_mcp_tools.py

# Check Cursor logs
ls -la ~/.cursor/logs/
cat ~/.cursor/logs/main.log | grep -i mcp
```

### Issue 3: Ollama Connection Refused

**Solution**:
```bash
# Restart Ollama
pkill ollama
ollama serve

# Check if port 11434 is in use
lsof -i :11434
```

### Issue 4: Model Too Slow

**Solution**:
- Use smaller models: `ollama pull llama3.1:8b`
- Check GPU/CPU usage: `ollama ps`
- Consider using quantized models (Q4, Q5)

---

## 🚀 Advanced: Direct MCP Integration

If Cursor doesn't support Ollama directly, you can create a bridge:

### Option 1: Use OpenAI-Compatible Endpoint

Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1`:

```python
# Example: Connect via OpenAI SDK
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # dummy key
)

response = client.chat.completions.create(
    model="qwen2.5-coder:32b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Option 2: MCP Client with Ollama

Create a custom MCP client that uses Ollama:

```python
# File: ollama_mcp_client.py
import asyncio
from synthesis.mcp_client import MCPClient
from openai import OpenAI

async def main():
    # Connect to Ollama
    ollama_client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )

    # Connect to MCP server
    mcp_client = MCPClient()

    # List available tools
    tools = await mcp_client.list_tools()
    print(f"Available tools: {len(tools)}")

    # Query with Ollama
    response = ollama_client.chat.completions.create(
        model="qwen2.5-coder:32b",
        messages=[{
            "role": "user",
            "content": "List NBA tables"
        }],
        tools=[tool.to_dict() for tool in tools]
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Performance Expectations

### Qwen2.5-Coder 32B
- **Pros**: Excellent code understanding, good tool usage
- **Cons**: 19GB size, slower inference
- **Best for**: Complex coding tasks, detailed analysis

### Recommended Alternatives
- **Llama 3.1 8B**: Faster, good tool use (5GB)
- **Mistral 7B**: Fast inference, decent tools (4GB)
- **Qwen2.5-Coder 7B**: Smaller version, faster (4.7GB)

---

## 🎯 Quick Start Commands

```bash
# 1. Ensure Ollama is running
ollama serve &

# 2. Test MCP server
cd /Users/ryanranft/nba-mcp-synthesis
python3 test_mcp_tools.py

# 3. Reload Cursor
# Press Cmd+Shift+P → "Reload Window"

# 4. Switch to Ollama model in chat

# 5. Test: "What MCP tools are available?"
```

---

## 📚 Resources

- **Ollama**: https://ollama.ai/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Cursor Docs**: https://cursor.sh/docs
- **Your MCP Server**: `/Users/ryanranft/nba-mcp-synthesis/mcp_server/`

---

## ✅ Checklist

- [ ] Ollama is running (`ollama serve`)
- [ ] Ollama model is downloaded (`qwen2.5-coder:32b`)
- [ ] Cursor is configured with Ollama endpoint
- [ ] MCP configuration is at `~/.cursor/mcp.json`
- [ ] Cursor window reloaded
- [ ] Ollama model selected in chat
- [ ] MCP tools visible in chat
- [ ] Test query executed successfully

---

**Status**: Ready to test! Just reload Cursor and switch to the Ollama model in the chat interface. 🚀




