# NBA MCP Synthesis - Usage Guide

This guide covers three ways to use the NBA MCP Synthesis system:
1. **Claude Desktop Integration** - Use via Claude Desktop app
2. **Direct Synthesis** - Run synthesis directly without MCP
3. **MCP Client** - Test MCP server communication

---

## Method 1: Claude Desktop Integration

### Overview
Integrate the MCP server with Claude Desktop to give Claude access to your NBA database, S3 bucket, and synthesis tools.

### Setup

1. **Install Dependencies**
   ```bash
   cd /Users/ryanranft/nba-mcp-synthesis
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Configure Claude Desktop**

   See `CLAUDE_DESKTOP_SETUP.md` for detailed instructions.

   Quick version:
   - Locate your Claude Desktop config file:
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
     - Linux: `~/.config/Claude/claude_desktop_config.json`

   - Copy settings from `claude_desktop_config.json` template
   - Replace `${VARIABLE}` placeholders with actual values from `.env`
   - Restart Claude Desktop

4. **Verify Installation**

   In Claude Desktop, ask:
   ```
   What MCP tools are available?
   ```

   You should see:
   - `query_database` - Execute SQL queries
   - `list_tables` - List database tables
   - `get_table_schema` - Get table schemas
   - `list_s3_files` - List S3 files

### Usage Examples

**List Tables:**
```
What tables are available in the NBA database?
```

**Query Database:**
```
Can you query the database to find the top 10 players by points?
```

**Get Schema:**
```
What's the schema for the player_stats table?
```

**Browse S3:**
```
Show me game JSON files in the S3 bucket
```

### Troubleshooting

See `CLAUDE_DESKTOP_SETUP.md` for detailed troubleshooting.

---

## Method 2: Direct Synthesis Testing

### Overview
Test the synthesis system directly without MCP server overhead. Great for development and debugging.

### Usage

```bash
cd /Users/ryanranft/nba-mcp-synthesis
python scripts/test_synthesis_direct.py
```

### What It Tests

1. **Simple SQL Query Generation**
   - Tests DeepSeek's SQL generation
   - Tests Claude's synthesis
   - Shows cost breakdown

2. **Code Debugging**
   - Tests DeepSeek's code debugging capabilities
   - Provides fixed code with explanation

3. **Statistical Analysis**
   - Tests mathematical reasoning
   - Correlation analysis
   - Statistical test recommendations

4. **SQL Optimization**
   - Analyzes slow queries
   - Suggests optimizations
   - Provides performance tips

5. **Full Synthesis Workflow**
   - Complete multi-model orchestration
   - Context gathering
   - Final synthesized solution

### Output

The script provides:
- Rich console output with colors and formatting
- Progress indicators
- Cost tracking per test
- Success/failure status
- Total summary with metrics

### Example Output

```
NBA MCP Synthesis - Direct Testing Suite
Testing synthesis system without MCP server

Test 1: Simple SQL Query Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running synthesis...

Results:
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Metric         ┃ Value          ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Success        │ True           │
│ Total Cost     │ $0.015234      │
│ Execution Time │ 38.45s         │
│ Models Used    │ deepseek,claude│
└────────────────┴────────────────┘

...

Test Summary
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric        ┃ Value       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Tests Run     │ 5           │
│ Successful    │ 5           │
│ Failed        │ 0           │
│ Total Cost    │ $0.042156   │
│ Total Time    │ 124.32s     │
│ Avg Cost/Test │ $0.008431   │
└───────────────┴─────────────┘

✅ All tests passed!
```

### Customization

You can modify the test script to:
- Add your own test cases
- Change temperature settings
- Adjust context
- Test different prompts

---

## Method 3: MCP Client Testing

### Overview
Test the MCP server communication directly. Useful for debugging server issues and verifying tool functionality.

### Usage

```bash
cd /Users/ryanranft/nba-mcp-synthesis
python scripts/test_mcp_client.py
```

### What It Tests

1. **Server Connection**
   - Establishes stdio connection
   - Verifies server startup

2. **Tool Discovery**
   - Lists available tools
   - Shows tool descriptions

3. **Database Operations**
   - List tables
   - Get table schemas
   - Execute queries

4. **S3 Operations**
   - List files in bucket
   - Filter by prefix

5. **Complex Queries**
   - Multi-table queries
   - Schema introspection

### Example Output

```
NBA MCP Server - Client Testing Suite
Testing MCP server communication via stdio

Server script: /Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py
Connecting to MCP server...
✅ Connected to MCP server

Listing available tools...

Available MCP Tools
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name             ┃ Description                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ query_database        │ Execute SQL query on NBA database    │
│ list_tables           │ List all tables in the NBA database  │
│ get_table_schema      │ Get schema for a database table      │
│ list_s3_files         │ List files in S3 bucket              │
└───────────────────────┴──────────────────────────────────────┘

Found 4 tools

...

Test Summary
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Test                  ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ list_tables           │ ✅ PASS     │
│ get_table_schema      │ ✅ PASS     │
│ query_database        │ ✅ PASS     │
│ list_s3_files         │ ✅ PASS     │
│ complex_query         │ ✅ PASS     │
└───────────────────────┴─────────────┘

Passed: 5/5
✅ All tests passed!
```

### Debugging

If tests fail:

1. **Check server script path**
   ```bash
   ls -la mcp_server/server_simple.py
   ```

2. **Verify environment variables**
   ```bash
   cat .env
   ```

3. **Test connections manually**
   ```bash
   python tests/test_connections.py
   ```

4. **Check server logs**
   - The client shows server stderr output
   - Look for error messages during startup

---

## Comparison Matrix

| Feature | Claude Desktop | Direct Synthesis | MCP Client |
|---------|---------------|------------------|------------|
| **Use Case** | Production use | Development/Testing | Server Testing |
| **Setup Complexity** | Medium | Low | Low |
| **Interactive** | Yes | No | No |
| **Cost Tracking** | No | Yes | No |
| **Real Database** | Yes | No | Yes |
| **Real S3** | Yes | No | Yes |
| **Full Synthesis** | Yes | Yes | No |
| **Debugging** | Hard | Easy | Easy |

---

## Cost Estimates

Based on testing:

### Direct Synthesis
- Simple query: ~$0.008 (DeepSeek + Claude)
- Complex query: ~$0.015
- Full workflow: ~$0.020
- Average: ~$0.012 per synthesis

### Claude Desktop
- Depends on usage
- Each tool call uses DeepSeek/Claude
- Estimate: $0.01-0.05 per conversation
- 93% cheaper than GPT-4 only approach

### MCP Client
- No AI costs (just testing server)
- Only AWS costs (RDS queries, S3 reads)
- Negligible for testing

---

## Best Practices

### 1. Development Workflow

```bash
# 1. Test connections first
python tests/test_connections.py

# 2. Test synthesis directly
python scripts/test_synthesis_direct.py

# 3. Test MCP server
python scripts/test_mcp_client.py

# 4. Configure Claude Desktop (optional)
# See CLAUDE_DESKTOP_SETUP.md
```

### 2. Cost Optimization

- Use Direct Synthesis for testing (better cost visibility)
- Set lower temperature for deterministic tasks (0.2-0.3)
- Use Claude sparingly (more expensive than DeepSeek)
- Cache common queries in your code

### 3. Error Handling

- Always check `.env` configuration first
- Test connections before running synthesis
- Monitor costs with Direct Synthesis mode
- Use MCP Client for debugging server issues

### 4. Security

- Never commit `.env` to git
- Use `.env.example` as template
- Keep Claude Desktop config local
- Rotate credentials regularly

---

## Next Steps

1. **Start Simple**
   ```bash
   python scripts/test_synthesis_direct.py
   ```

2. **Test MCP Server**
   ```bash
   python scripts/test_mcp_client.py
   ```

3. **Configure Claude Desktop**
   - See `CLAUDE_DESKTOP_SETUP.md`
   - Copy from `claude_desktop_config.json` template

4. **Build Your Own**
   - Use `synthesis/orchestrator.py` as reference
   - Customize for your use case
   - Add new tools as needed

---

## Support

### Documentation
- `README.md` - Project overview
- `CLAUDE_DESKTOP_SETUP.md` - Claude Desktop integration
- `USAGE_GUIDE.md` - This file
- `.env.example` - Environment template

### Testing
- `tests/test_connections.py` - Connection testing
- `tests/test_deepseek_integration.py` - DeepSeek testing
- `scripts/test_synthesis_direct.py` - Direct synthesis
- `scripts/test_mcp_client.py` - MCP client

### Scripts
- `scripts/start_mcp_server.sh` - Start MCP server
- `scripts/test_synthesis.py` - Original synthesis test
- `scripts/diagnose_performance.py` - Network diagnostics

---

## FAQ

**Q: Which method should I use?**
- For production: Claude Desktop
- For development: Direct Synthesis
- For debugging: MCP Client

**Q: How much does it cost?**
- DeepSeek: $0.14/1M input tokens, $0.28/1M output
- Claude: $3/1M input, $15/1M output
- Average synthesis: ~$0.012 (93% cheaper than GPT-4)

**Q: Can I use without Claude Desktop?**
- Yes! Use Direct Synthesis method
- Full functionality without MCP server

**Q: How do I add new tools?**
- Edit `mcp_server/server_simple.py`
- Add new `@mcp.tool()` decorated functions
- Restart server or Claude Desktop

**Q: Is my data secure?**
- All processing is local or via your APIs
- No data sent to third parties
- MCP uses stdio (no network exposure)

**Q: Can I use other AI models?**
- Yes! See `synthesis/models/ollama_model.py`
- Add new model interfaces as needed
- Update orchestrator to use them

---

## License

See LICENSE file in project root.

## Contributing

Contributions welcome! Please:
1. Test your changes
2. Update documentation
3. Follow existing code style
4. Add tests for new features