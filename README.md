# NBA MCP Synthesis System

Multi-Model AI Synthesis with Model Context Protocol (MCP) for NBA Game Simulator

## Overview

This system combines:
- **MCP Server**: Provides real-time NBA project context (RDS, S3, Glue data)
- **Multi-Model Synthesis**: Queries 4 AI models (Claude, GPT-4o, Gemini, Ollama)
- **PyCharm Integration**: One-click synthesis from IDE
- **Smart Context**: Automatically gathers relevant data for better AI responses

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-username/nba-mcp-synthesis.git
cd nba-mcp-synthesis

# 2. Create virtual environment
conda create -n mcp-synthesis python=3.11
conda activate mcp-synthesis

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your AWS and API credentials

# 5. Start MCP server
python -m mcp_server.server

# 6. Test the system
python scripts/test_mcp_connection.py

# 7. Run synthesis example
python scripts/quick_start.py
```

## Features

### MCP Tools Available
- `query_rds_database` - Query NBA PostgreSQL database
- `fetch_s3_sample` - Get sample data from S3 bucket
- `get_glue_schema` - Retrieve table schemas
- `read_project_file` - Access project files
- `get_table_statistics` - Get DB performance stats
- `save_to_project` - Save synthesis results
- `log_synthesis_result` - Track operations

### Supported Models
- Claude Sonnet 4
- GPT-4o
- Gemini 2.0
- Ollama (local)

## Architecture

```
PyCharm → Multi-Model Synthesis → MCP Server → NBA Infrastructure
                ↓                      ↓              ↓
         [4 AI Models]          [Context Tools]   [RDS/S3/Glue]
                ↓                      ↓              
         [Synthesized Result] ← [Rich Context]
```

## Configuration

See `.env.example` for required environment variables:
- AWS credentials (RDS, S3, Glue)
- API keys (Anthropic, OpenAI, Google)
- MCP server settings
- Project paths

## PyCharm Integration

1. Open PyCharm Settings → Tools → External Tools
2. Add new tool with configuration from `docs/PYCHARM_SETUP.md`
3. Select code and run: Tools → Multi-Model Synthesis (MCP)

## Development

```bash
# Run tests
pytest tests/

# Start MCP server in development
python -m mcp_server.server --debug

# Monitor logs
tail -f logs/mcp_synthesis.log
```

## Project Structure

```
nba-mcp-synthesis/
├── mcp_server/         # MCP server implementation
├── synthesis/          # Multi-model synthesis system
├── connectors/         # AWS and data connectors
├── pycharm_integration/# IDE integration
├── scripts/           # Utility scripts
├── tests/             # Test suite
└── docs/              # Documentation
```

## License

MIT License - See LICENSE file

## Author

Ryan Ranft (2025)
