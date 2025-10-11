
# NBA MCP Synthesis System

Multi-Model AI Synthesis with Model Context Protocol (MCP) for NBA Game Simulator

## Overview

This system combines:
- **MCP Server**: Provides real-time NBA project context (RDS, S3, Glue data)
- **Multi-Model Synthesis**: DeepSeek V3 (primary) + Claude 3.7 Sonnet (synthesis)
- **55 MCP Tools**: Database, analytics, NBA metrics, advanced analytics
- **Cost Optimized**: 93% cheaper than GPT-4 only approach (~$0.012 per synthesis)
- **Claude Desktop Integration**: Use via Claude Desktop app
- **Smart Context**: Automatically gathers relevant data for better AI responses

### 🎯 What's New

**Version 1.0 - Production Ready** (October 10, 2025):
- ✅ **88 MCP tools** complete (Sprints 5-8)
- ✅ **Complete ML Pipeline**: Training → Evaluation → Deployment
- ✅ **18 ML Core Tools**: Clustering, Classification, Anomaly Detection, Feature Engineering
- ✅ **15 ML Evaluation Tools**: Metrics, Cross-Validation, Model Comparison
- ✅ **33 Infrastructure Tools**: Database, S3, File operations
- ✅ **22 AWS Integration Tools**: Action tools, Glue ETL
- ✅ **100% test coverage** for ML components
- ✅ **Pure Python ML** (no scikit-learn dependency)

**📊 Project Tracking**: See [PROJECT_MASTER_TRACKER.md](PROJECT_MASTER_TRACKER.md) for complete progress tracking
**📝 Changelog**: See [CHANGELOG.md](CHANGELOG.md) for detailed version history

**Phase 9 Upcoming** (36 additional features planned):
- Math/Stats Tools (20 tools)
- Web Scraping (3 tools)
- MCP Prompts & Resources (13 features)

## Key Features

- **DeepSeek V3 Primary Model**: $0.14/1M input tokens (fast, accurate, cheap)
- **Claude 3.7 Sonnet**: Synthesis, verification, explanation
- **Three Usage Modes**: Claude Desktop, Direct Synthesis, MCP Client
- **Real-time Database Access**: Query NBA PostgreSQL via MCP
- **S3 Integration**: Access 146K+ game JSON files + Book library
- **Book Reading**: Read technical books with math-mcp integration
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

**Database Tools:**
- `query_database` - Execute SQL queries on NBA PostgreSQL database
- `list_tables` - List all database tables
- `get_table_schema` - Get schema for specific tables

**S3 & File Tools:**
- `list_s3_files` - List files in S3 bucket
- `list_books` - List books with math content detection
- `read_book` - Read books in chunks with LaTeX preservation
- `search_books` - Full-text search across book library

**Pagination Tools:**
- `list_games` - List games with cursor-based pagination
- `list_players` - List players with cursor-based pagination

**Math & Stats Tools (NEW!):**
- `math_add`, `math_subtract`, `math_multiply`, `math_divide` - Basic arithmetic
- `math_sum`, `math_round`, `math_modulo` - Advanced operations
- `stats_mean`, `stats_median`, `stats_mode` - Central tendency
- `stats_min_max`, `stats_variance`, `stats_summary` - Statistical analysis

**NBA Metrics Tools (Sprint 5):**
- `nba_player_efficiency_rating` - Calculate PER (Player Efficiency Rating)
- `nba_true_shooting_percentage` - Calculate TS% (True Shooting %)
- `nba_effective_field_goal_percentage` - Calculate eFG% (Effective FG%)
- `nba_usage_rate` - Calculate USG% (Usage Rate)
- `nba_offensive_rating` - Calculate ORtg (Offensive Rating)
- `nba_defensive_rating` - Calculate DRtg (Defensive Rating)
- `nba_pace` - Calculate pace (possessions per 48 minutes)

**Advanced Analytics Tools (Sprint 6 - NEW!):**

*Correlation & Regression (6 tools):*
- `stats_correlation` - Pearson correlation coefficient
- `stats_covariance` - Covariance analysis
- `stats_linear_regression` - Simple linear regression (y = mx + b)
- `stats_predict` - Make predictions with regression model
- `stats_correlation_matrix` - Multi-variable correlation matrix

*Time Series Analysis (6 tools):*
- `stats_moving_average` - Simple moving average (SMA)
- `stats_exponential_moving_average` - Exponential moving average (EMA)
- `stats_trend_detection` - Trend analysis (increasing/decreasing/stable)
- `stats_percent_change` - Period-over-period change
- `stats_growth_rate` - Compound annual growth rate (CAGR)
- `stats_volatility` - Coefficient of variation (consistency)

*Advanced NBA Metrics (6 tools):*
- `nba_four_factors` - Dean Oliver's Four Factors (offensive & defensive)
- `nba_turnover_percentage` - TOV% per 100 possessions
- `nba_rebound_percentage` - REB% of available rebounds
- `nba_assist_percentage` - AST% of teammate FGs assisted
- `nba_steal_percentage` - STL% per 100 opponent possessions
- `nba_block_percentage` - BLK% of opponent 2PA blocked

**See MATH_TOOLS_GUIDE.md and ADVANCED_ANALYTICS_GUIDE.md for detailed usage examples and formulas.**

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

### 📊 Project Management & Progress
- **[PROJECT_MASTER_TRACKER.md](PROJECT_MASTER_TRACKER.md)** - **Single source of truth** for project progress (90/104 tools)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history following Keep a Changelog format
- **[Master Plan System](docs/plans/MASTER_PLAN.md)** - **Central index** for all project plans with management guidelines
  - See [NBA MCP Improvement Plan](docs/plans/detailed/NBA_MCP_IMPROVEMENT_PLAN.md) for detailed roadmap (v3.0, 86% complete)
  - See [Verification Report](docs/plans/VERIFICATION_REPORT_2025-10-11.md) for latest verification (Oct 11, 2025)
- **[GitHub Issue Templates](.github/ISSUE_TEMPLATE/)** - Feature requests, bug reports, sprint tasks

### 🚀 Getting Started
- **README.md** (this file) - Quick start and overview
- **USAGE_GUIDE.md** - Comprehensive usage guide for all three methods
- **CLAUDE_DESKTOP_SETUP.md** - Claude Desktop integration setup
- **DEPLOYMENT.md** - Production deployment guide

### 📚 Sprint Documentation (Completed)
Located in `docs/sprints/completed/`:
- **SPRINT_5_COMPLETE.md** - Core Infrastructure (33 tools)
- **SPRINT_6_COMPLETE.md** - AWS Integration (22 tools)
- **SPRINT_7_COMPLETED.md** - ML Core (18 tools)
- **SPRINT_8_COMPLETED.md** - ML Evaluation & Validation (15 tools)
- **SPRINT_8_FINAL_SUMMARY.md** - Sprint 8 executive summary

### 📈 System Status & Tracking
Located in `docs/tracking/`:
- **NBA_MCP_SYSTEM_STATUS.md** - Current system overview (88 tools operational)
- **SPRINTS_COMPLETION_STATUS.md** - Planned vs. actual work comparison
- **SPRINT_5_PROGRESS.md**, **SPRINT_8_PROGRESS.md** - Sprint progress logs

### 🎓 Book Integration
- **BOOK_INTEGRATION_GUIDE.md** - Complete book integration guide
- **MATH_INTEGRATION.md** - Math book reading with math-mcp server

### 🏀 Analytics & Tools Guides
- **ADVANCED_ANALYTICS_GUIDE.md** - Advanced analytics quick reference
- **MATH_TOOLS_GUIDE.md** - Math/stats/NBA metrics guide
- **SPRINT_5_FINAL_SUMMARY.md** - Sprint 5 practical guide

### 📖 Reference
- **.env.example** - Environment variable template
- **tests/** - Connection and integration tests (100% pass rate for ML)
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

# Test book integration (NEW!)
python scripts/test_book_features.py
python scripts/test_book_features.py --demo  # Interactive demo

# Test math/stats/NBA tools (Sprint 5)
python scripts/test_math_stats_features.py
python scripts/test_math_stats_features.py --demo  # Interactive demo

# Test advanced analytics tools (Sprint 6 - NEW!)
python scripts/test_sprint6_features.py
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
