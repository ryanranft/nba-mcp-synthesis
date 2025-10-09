
# NBA MCP Synthesis System

Multi-Model AI Synthesis with Model Context Protocol (MCP) for NBA Game Simulator

## Overview

This system combines:
- **MCP Server**: Provides real-time NBA project context (RDS, S3, Glue data)
- **Multi-Model Synthesis**: DeepSeek V3 (primary) + Claude 3.7 Sonnet (synthesis)
- **Cost Optimized**: 93% cheaper than GPT-4 only approach (~$0.012 per synthesis)
- **Claude Desktop Integration**: Use via Claude Desktop app
- **Smart Context**: Automatically gathers relevant data for better AI responses

## Key Features

- **DeepSeek V3 Primary Model**: $0.14/1M input tokens (fast, accurate, cheap)
- **Claude 3.7 Sonnet**: Synthesis, verification, explanation
- **Three Usage Modes**: Claude Desktop, Direct Synthesis, MCP Client
- **Real-time Database Access**: Query NBA PostgreSQL via MCP
- **S3 Integration**: Access 146K+ game JSON files
- **Cost Tracking**: Monitor AI spending per operation

## Quick Start

### Option 1: Direct Synthesis (Easiest)

```bash
# 1. Setup environment
cd nba-mcp-synthesis
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

# 2. Test connections
python tests/test_connections.py

# 3. Run synthesis tests
python scripts/test_synthesis_direct.py
```

This runs 5 comprehensive tests showing:
- SQL query generation
- Code debugging
- Statistical analysis
- Query optimization
- Full synthesis workflow

**Cost:** ~$0.04 total for all tests

### Option 2: Claude Desktop Integration

```bash
# 1. Setup (same as above)
pip install -r requirements.txt
cp .env.example .env

# 2. Configure Claude Desktop
# See CLAUDE_DESKTOP_SETUP.md for details

# 3. Use in Claude Desktop
# Ask: "What MCP tools are available?"
```

This integrates MCP server with Claude Desktop app.

### Option 3: MCP Client Testing

```bash
# 1. Setup (same as above)
pip install -r requirements.txt
cp .env.example .env

# 2. Test MCP server
python scripts/test_mcp_client.py
```

This tests MCP server communication directly.

**See USAGE_GUIDE.md for detailed instructions on all three methods.**

## Features

### MCP Tools Available
- `query_database` - Execute SQL queries on NBA PostgreSQL database
- `list_tables` - List all database tables
- `get_table_schema` - Get schema for specific tables
- `list_s3_files` - List files in S3 bucket

### AI Models
- **DeepSeek V3** (Primary) - Mathematical reasoning, SQL optimization, code debugging
- **Claude 3.7 Sonnet** - Synthesis, verification, explanation
- **Ollama** (Optional) - Local verification model

## Architecture

```
User Request
    ↓
DeepSeek V3 (Primary) ← MCP Context (RDS, S3, Glue schemas)
    ↓
Claude 3.7 (Synthesis & Verification)
    ↓
Final Solution with Explanation
```

**Data Flow:**
1. User submits request
2. MCP client gathers relevant context (table schemas, sample data)
3. DeepSeek V3 generates initial solution (cheap, fast)
4. Claude 3.7 synthesizes and verifies (quality assurance)
5. Return final solution with cost breakdown

## Documentation

- **USAGE_GUIDE.md** - Comprehensive usage guide for all three methods
- **CLAUDE_DESKTOP_SETUP.md** - Claude Desktop integration setup
- **.env.example** - Environment variable template
- **tests/** - Connection and integration tests
- **scripts/** - Test and diagnostic scripts

## Configuration

Required environment variables (see `.env.example`):

```bash
# AWS Infrastructure
RDS_HOST=your-db-host.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=nba_simulator
RDS_USERNAME=your-username
RDS_PASSWORD=your-password
S3_BUCKET=your-nba-data-bucket
S3_REGION=us-east-1

# AI Model APIs
DEEPSEEK_API_KEY=your-deepseek-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional
GLUE_DATABASE=nba_data_catalog
GLUE_REGION=us-east-1
```

## Testing

```bash
# Test all connections
python tests/test_connections.py

# Test DeepSeek integration
python tests/test_deepseek_integration.py

# Test direct synthesis (comprehensive)
python scripts/test_synthesis_direct.py

# Test MCP server
python scripts/test_mcp_client.py
```

## Project Structure

```
nba-mcp-synthesis/
├── mcp_server/              # MCP server implementation
│   ├── server.py            # Full MCP server
│   ├── server_simple.py     # Simple FastMCP server
│   ├── connectors/          # RDS, S3, Glue connectors
│   ├── tools/               # MCP tool implementations
│   └── config.py            # Configuration management
├── synthesis/               # Multi-model synthesis
│   ├── orchestrator.py      # Main synthesis orchestrator
│   ├── models/              # Model interfaces (DeepSeek, Claude, Ollama)
│   └── mcp_client.py        # MCP context gathering client
├── scripts/                 # Utility scripts
│   ├── test_synthesis_direct.py     # Direct synthesis testing
│   ├── test_mcp_client.py           # MCP server testing
│   ├── test_connections.py          # Connection verification
│   └── diagnose_performance.py      # Network diagnostics
├── tests/                   # Test suite
│   ├── test_connections.py          # Connection tests
│   └── test_deepseek_integration.py # DeepSeek tests
├── USAGE_GUIDE.md           # Comprehensive usage guide
├── CLAUDE_DESKTOP_SETUP.md  # Claude Desktop setup
├── .env.example             # Environment template
└── README.md                # This file
```

## License

MIT License - See LICENSE file

## Author

Ryan Ranft (2025)
