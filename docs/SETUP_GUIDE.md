# NBA MCP Synthesis System - Setup Guide

## 📋 Overview

This guide will help you set up the MCP-Enhanced Multi-Model Synthesis System for your NBA simulator project. The system combines:
- **MCP Server**: Provides real-time context from your NBA project
- **Multi-Model Synthesis**: Queries Claude, GPT-4o, Gemini, and Ollama
- **PyCharm Integration**: One-click synthesis from your IDE

## 🚀 Quick Start

```bash
# 1. Clone and navigate to repository
cd nba-mcp-synthesis

# 2. Run automated setup
python scripts/setup.py

# 3. Test connections
python scripts/test_mcp_connection.py

# 4. Start MCP server
python -m mcp_server.server
```

## 📁 Files Created

Your repository now contains:

```
nba-mcp-synthesis/
├── README.md                    # Project overview
├── LICENSE                      # MIT License  
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore patterns
├── requirements.txt             # Python dependencies
│
├── mcp_server/                  # MCP Server implementation
│   ├── server.py               # Main MCP server
│   ├── config.py               # Configuration handler
│   └── connectors/             # Data source connectors
│       ├── rds_connector.py   # PostgreSQL connector
│       ├── s3_connector.py     # S3 data lake connector
│       └── slack_notifier.py  # Slack notifications
│
├── pycharm_integration/         # PyCharm external tool
│   └── external_tool_wrapper.py # Entry point for PyCharm
│
└── scripts/                     # Utility scripts
    ├── setup.py                # Automated setup
    └── test_mcp_connection.py  # Connection tester
```

## 🔧 Manual Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required AWS credentials
RDS_HOST=your-rds-host.amazonaws.com
RDS_USERNAME=postgres
RDS_PASSWORD=your_password
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Required API keys (at least one)
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

# Project path
PROJECT_ROOT=/Users/ryanranft/nba-simulator-aws
```

### 2. PyCharm External Tool Setup

1. Open PyCharm Settings → Tools → External Tools
2. Click '+' to add new tool
3. Configure:
   - **Name**: Multi-Model Synthesis (MCP)
   - **Program**: `/path/to/python`
   - **Arguments**: `"/path/to/external_tool_wrapper.py" "$FilePath$" "$SelectedText$" "$Prompt$"`
   - **Working directory**: `$ProjectFileDir$`

### 3. Install Dependencies

```bash
# Create virtual environment
conda create -n mcp-synthesis python=3.11
conda activate mcp-synthesis

# Install requirements
pip install -r requirements.txt
```

## 🧪 Testing Your Setup

### Test Connections
```bash
python scripts/test_mcp_connection.py
```

Expected output:
```
🔧 MCP Server Connection Test

Test Results:
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Service       ┃ Status         ┃ Details               ┃ Info   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ API Keys      │ ✅ All configured │ Anthropic, OpenAI... │ 4/4    │
│ Project Path  │ ✅ Found         │ /Users/ryanranft/... │ 156 .py│
│ RDS Database  │ ✅ Connected     │ PostgreSQL 15.4      │ 12     │
│ S3 Bucket     │ ✅ Connected     │ nba-sim-raw-data-lake│ 5      │
│ Slack Webhook │ ⏭️ Skipped       │ No webhook configured │ N/A    │
└───────────────┴────────────────┴───────────────────────┴────────┘
```

## 💡 Usage Examples

### From PyCharm

1. Select code in editor
2. Run: Tools → External Tools → Multi-Model Synthesis (MCP)
3. View synthesized result in output window

### Example: Optimize SQL Query

Select in PyCharm:
```sql
SELECT * FROM player_game_stats WHERE player_id = 123
```

Add comment above:
```python
# Optimize this query for performance
```

Run tool → Get optimized query with:
- EXPLAIN plan analysis
- Index recommendations  
- Rewritten query
- Performance metrics

## 🔌 Connector Integration Status

Based on your connector plans:

| Connector | Status | Used in MCP | Purpose |
|-----------|---------|-------------|---------|
| **AWS S3** | ✅ Integrated | Yes | Fetch data samples from lake |
| **GitHub** | ✅ Ready | No | Version control (use git) |
| **Slack** | ✅ Integrated | Optional | Send notifications |
| **PostgreSQL** | ✅ Integrated | Yes | Query NBA database |
| Great Expectations | ⏳ Not needed | No | Data quality (separate project) |
| Basketball-Reference | ⏳ Not needed | No | Data ingestion (separate) |
| Streamlit | ⏳ Not needed | No | UI (MCP is backend) |
| Jupyter | ⏳ Not needed | No | MCP runs from PyCharm |
| Notion | ⏳ Not needed | No | Documentation (use markdown) |
| Airflow | ⏳ Not needed | No | Orchestration (MCP is on-demand) |
| Google Sheets | ⏳ Optional | No | Could add as MCP tool later |

## 🚨 Troubleshooting

### Connection Errors

```bash
# Check AWS credentials
aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 1

# Test RDS connection
psql -h your-host.amazonaws.com -U postgres -d nba_simulator -c "SELECT 1"
```

### MCP Server Won't Start

1. Check all required env vars are set
2. Verify Python 3.11+ is installed
3. Check port 3000 is available
4. Review logs in `logs/mcp_synthesis.log`

### PyCharm Tool Not Working

1. Verify Python path in tool configuration
2. Check wrapper script path is correct
3. Ensure code is selected before running
4. Check PyCharm console for errors

## 📊 Next Steps

1. **Start using it!** Select code and run synthesis
2. **Add more MCP tools** as needed (see `mcp_server/tools/`)
3. **Configure Slack** for notifications (optional)
4. **Implement synthesis logic** (currently stubbed)
5. **Add Glue connector** when needed

## 📚 Additional Resources

- [MCP Protocol Docs](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP SDK](https://github.com/anthropics/anthropic-mcp-python)
- [Your NBA Project Docs](file:///Users/ryanranft/nba-simulator-aws)

## ✅ Checklist

Complete these to verify setup:

- [ ] `.env` file created with credentials
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Connection test passes (`python scripts/test_mcp_connection.py`)
- [ ] MCP server starts (`python -m mcp_server.server`)
- [ ] PyCharm external tool configured
- [ ] First synthesis run successful

---

**Ready to synthesize!** 🚀

For help: Review this guide or check the test script output for specific issues.
