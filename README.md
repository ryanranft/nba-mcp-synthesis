
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

> Using PyCharm? See PyCharm AI Playground setup: docs/guides/PYCHARM_AI_PLAYGROUND_SETUP.md

## 🎯 Project Vision: AI-Powered Sports Analytics Platform

This system represents a complete AI-powered platform for reading technical books, analyzing GitHub repositories, and automatically implementing best practices in production NBA analytics systems.

### The Complete Pipeline

```
📚 Knowledge Sources (88+ items in S3)
    ├── 45+ Technical Books (ML, Econometrics, Basketball Analytics, AI/LLMs)
    ├── 16+ GitHub Repos (MCP servers, Enterprise tools, Official SDKs)
    └── 30+ Textbook Code Implementations
            ↓
    🔍 12-Phase Analysis Workflow
            ↓
    🤖 Multi-Model AI Synthesis (Gemini + Claude + GPT-4)
            ↓
    📋 1000+ Implementation Recommendations
            ↓
    🚀 Automated Deployment → /nba-simulator-aws
```

### Knowledge Library (S3 Storage)

**Basketball Analytics (4 books):**
- Basketball on Paper (Oliver) - Statistical analysis
- Basketball Beyond Paper - Advanced metrics
- Sports Analytics - Comprehensive overview
- The Midrange Theory - Shot selection analytics

**Machine Learning (18 books):**
- Hands-On ML (Géron) - Practical scikit-learn & TensorFlow
- Elements of Statistical Learning (Hastie) - Theory & algorithms
- Pattern Recognition (Bishop) - Bayesian approaches
- Deep Learning (Goodfellow) - Neural networks bible
- Probabilistic ML (Murphy) - Advanced topics

**Econometrics (9 books):**
- Greene, Wooldridge (3 books) - Panel data & methods
- Stock & Watson - Introduction
- Angrist & Pischke (MHE) - Causal inference
- Microeconometrics - Methods & applications

**AI & LLMs (8 books):**
- AI Modern Approach (Norvig) - Foundations
- LLM Engineers Handbook - Production LLMs
- Hands-On LLMs - Practical implementations
- NLP with Transformers - State-of-the-art NLP

**MLOps & Production (6 books):**
- Designing ML Systems (Chip Huyen) - System design
- Practical MLOps - Operations & deployment
- ML-Powered Applications - Building products

**GitHub Repositories (16+ repos):**
- MCP servers (web scraping, ebook, firecrawl, math)
- Official MCP SDK (Python, TypeScript)
- Enterprise tools (Grafana, Redis, Cloudflare)
- Graph neural networks (PyTorch Geometric)

**Textbook Code (30+ implementations):**
- Econometrics companion code (Angrist, Wooldridge)
- ML implementations (ISLR, PRML, ESL)
- Deep learning notebooks
- LLM & NLP examples

### 12-Phase Book Analysis Workflow

**Foundation Phases (0-9)** - Core workflow for all analysis:
- **Phase 0:** Environment discovery and validation
- **Phase 1:** Book/repo discovery from S3
- **Phase 2:** High-context analysis with convergence enhancement (up to 200 iterations/book)
- **Phase 3:** Multi-model synthesis (Gemini + Claude consensus)
- **Phase 3.5:** AI-powered plan modification (autonomous improvements)
- **Phase 4:** Implementation file generation
- **Phase 5:** Index and documentation updates
- **Phase 6:** Status tracking and reporting
- **Phase 7:** Dependency optimization
- **Phase 8:** Progress monitoring
- **Phase 9:** Integration planning

**MCP Enhancement Phases (10A-12A)** - Improve MCP server:
- **Phase 10A:** MCP tool validation
- **Phase 11A:** Tool optimization
- **Phase 12A:** MCP deployment

**Simulator Enhancement Phases (10B-12B)** - Improve nba-simulator-aws:
- **Phase 10B:** nba-simulator-aws structure analysis
- **Phase 11B:** Model ensemble improvements
- **Phase 12B:** Production deployment

### Key Capabilities

**Multi-Model AI Synthesis:**
- Primary: Gemini 2.0 Flash ($0.075/1M tokens) - High-context book analysis
- Synthesis: Claude 3.7 Sonnet - Quality assurance & consensus
- Validation: GPT-4 Turbo (optional) - Third-party verification
- Legacy: DeepSeek V3 - Mathematical reasoning

**High-Context Book Analysis:**
- Process entire books (up to 250K tokens)
- Iterative convergence enhancement
- Extract formulas, code, and best practices
- Math content preservation (LaTeX support)

**Intelligent Plan Management:**
- Automatic duplicate detection
- Smart plan merging
- AI-powered modifications (ADD/MODIFY/DELETE)
- Context-aware recommendations

**Smart Integration:**
- Analyze nba-simulator-aws structure
- Generate optimal placement decisions
- Detect integration conflicts
- Estimate implementation impact

### Implementation Tiers

**Tier 0: Safety First** (~$25, 5 days)
- Cost limits & budget tracking
- Automatic rollback on failure
- Pre-integration validation
- Dry-run mode for all operations
- **Status:** ✅ Complete (Oct 2024)

**Tier 1: Performance** (~$5, 5 days)
- Result caching (100% savings on re-runs)
- Checkpoint/resume capability
- Parallel execution (4-8 workers)
- Configuration management (YAML)
- **Status:** ✅ Complete (Oct 2024)

**Tier 2: AI Intelligence** (~$25-45, 5 days)
- Phase 3.5 autonomous modifications
- Smart integrator for nba-simulator-aws
- Conflict resolution between models
- Comprehensive phase tracking
- **Status:** 🚧 In Progress

**Tier 3: Observability** (~$15-30, 7 days)
- Real-time dashboard (http://localhost:8080)
- A/B testing framework
- GitHub book auto-discovery
- Resource monitoring
- Dependency visualization
- **Status:** ⏸️ Planned

### Cost Economics

**One-Time Investment:**
- Tier 0 Implementation & Testing: $25
- Full 45-Book Analysis (Tier 1): $20-30
- AI Enhancements (Tier 2): $25-45
- Observability (Tier 3): $15-30
- **Total First Run:** $75-110

**Ongoing Costs:**
- Re-runs with caching: **$0** (100% cached)
- New AI modifications only: $0-15
- **Sustainable:** Near-zero cost after initial run

### Current Achievements

✅ **88 MCP Tools Deployed** - Complete ML pipeline operational
✅ **45+ Books Accessible** - Comprehensive technical library in S3
✅ **Multi-Model Synthesis** - Gemini + Claude + GPT-4 consensus
✅ **High-Context Analysis** - Up to 250K tokens per book
✅ **GitHub Repo Analysis** - 16+ repos including MCP servers
✅ **Textbook Code Integration** - 30+ implementations available
✅ **Hierarchical Secrets** - Production-grade security
✅ **Cost Optimization** - 93% cheaper than GPT-4 only

### Roadmap

**Q4 2024:**
- ✅ Tier 0-1 Complete (Safety + Performance)
- 🚧 Tier 2 In Progress (AI Intelligence)
- 🚧 Full 45-book overnight analysis
- ⏸️ Automated deployment to nba-simulator-aws

**Q1 2025:**
- ⏸️ Tier 3 Complete (Observability)
- ⏸️ GitHub book auto-discovery
- ⏸️ Continuous learning pipeline
- ⏸️ A/B testing framework

**Q2 2025:**
- ⏸️ Real-time recommendation monitoring
- ⏸️ Automated book updates
- ⏸️ Community contribution framework

### Quick Start: Book Analysis

```bash
# Analyze a single book (test)
python3 scripts/run_overnight_with_secrets.py --book "Hands-On ML"

# Analyze all 45+ books (overnight run)
python3 scripts/run_overnight_with_secrets.py

# Monitor progress
open http://localhost:8080  # Real-time dashboard

# Review results
cat CONVERGENCE_ENHANCEMENT_RESULTS.md
```

**See [high-context-book-analyzer.plan.md](high-context-book-analyzer.plan.md) for complete workflow documentation.**

## AI Playground Adapter (New)

A lightweight adapter exposes MCP capabilities and data-inventory-aware context to any UI.

Quick start:

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

## Security & Secrets Management

This project implements comprehensive security scanning and hierarchical secrets management:

### 🔐 Hierarchical Secrets (UPDATED 2025-10-22)

Secrets are stored in a hierarchical structure outside the repository for maximum security:

```bash
# 1. Test secrets loading (quickest way to verify setup)
python test_secrets_hierarchical.py

# 2. Secrets are automatically loaded from:
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/
  ├── nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
  │   ├── ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
  │   ├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
  │   └── ... (other secrets)
  └── nba-simulator-aws/.env.nba_simulator_aws.production/
      └── ... (AWS project secrets)

# 3. For detailed setup instructions:
# See: SECRETS_MIGRATION_COMPLETE.md
# See: /Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md
```

**Key Benefits:**
- ✅ **Auto-loading**: Scripts automatically load secrets on startup
- ✅ **Context-aware**: Separate secrets for WORKFLOW/DEVELOPMENT/TEST
- ✅ **Fallback support**: Hierarchical loading with context fallback
- ✅ **No manual exports**: No need to `export ANTHROPIC_API_KEY=...`

### Security Scanning

- ✅ **Pre-commit Hooks**: detect-secrets + git-secrets + bandit (local protection)
- ✅ **CI/CD Scanning**: Bandit + Trivy + trufflehog (automated pipeline)
- ✅ **S3 Public Access Validation**: Automated bucket/object privacy checks
- ✅ **Permission Auditing**: Automated file permission checks

### Setup Security Tools

```bash
# Install all security scanning tools
./scripts/setup_security_scanning.sh

# Test installation
python scripts/test_security_scanning.py

# Run validation
python scripts/validate_secrets_security.py
```

### What Gets Scanned

**Pre-commit (local)**:
- API key patterns (AWS, Google, OpenAI, Anthropic, DeepSeek)
- Hardcoded passwords and tokens
- Python security issues (bandit)
- Code formatting (black)

**CI/CD (GitHub Actions)**:
- Full git history scanning (trufflehog)
- Dependency vulnerabilities (Trivy)
- Custom pattern matching (git-secrets)
- S3 bucket and object public access (boto3)

**S3 Security (automated)**:
- Bucket PublicAccessBlock configuration
- Bucket ACLs (no public grants)
- Bucket policies (no wildcard principals)
- Object ACLs for all books/datasets

### Quick Security Check

```bash
# Before committing
pre-commit run --all-files

# Check for hardcoded secrets
python scripts/validate_secrets_security.py

# Check for hardcoded secrets AND S3 public access
python scripts/validate_secrets_security.py --check-s3

# Check S3 buckets only
python scripts/validate_s3_public_access.py --fail-on-public

# Audit permissions
./scripts/audit_secret_permissions.sh
```

See [Security Scanning Guide](docs/SECURITY_SCANNING_GUIDE.md) for detailed documentation.

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

### 🎉 What's New: Phase 3 UX Enhancements (November 2025)

**Task Tracker System - Major Productivity Upgrade!**

Phase 3 transforms the Task Tracker from a basic task manager into a powerful productivity suite:

**✨ New Slash Commands:**
- `/template` - Work with task templates (list, create, save, get details)
- `/analytics` - Interactive analytics dashboard (velocity, predictions, bottlenecks)
- `/bulk-complete` - Complete multiple tasks at once
- `/bulk-priority` - Update priorities in bulk
- `/block` - Mark tasks as blocked with reasons
- `/export` - Export project data (JSON, CSV, Markdown)
- `/report` - Generate summary reports
- `/resume` - Enhanced visual view with color-coding and staleness warnings

**📊 Analytics Tools (3 new MCP tools):**
- `get_velocity_metrics` - Track tasks/day, completion trends, performance by priority
- `predict_completion` - Forecast project completion (optimistic/realistic/pessimistic)
- `get_bottlenecks` - Identify stale tasks, blockers, and workflow issues

**📋 Task Templates (8 built-in + custom):**
- Bug Fix, Feature Development, Code Review
- Data Analysis, Deployment, Documentation
- ML Training, Sprint Planning
- Save your own workflows as templates

**🎯 Smart Filtering:**
- Filter by: stale (>7 days), blocked, tags, project, priority, date range, due soon
- Sort by: priority, created, updated, due date, title
- Saved views: focus, blocked, stale, overview

**📈 Impact:**
- 95% reduction in task management overhead
- New users productive in <5 minutes
- Complete documentation (QUICKSTART, BEST_PRACTICES, EXAMPLES)

See full details: [Phase 3 Completion Summary](docs/archive/summaries/PHASE3_COMPLETION_SUMMARY.md)

---

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

## 🎓 Learning Path: Interactive Tutorials

**NEW!** Complete tutorial series covering 27+ econometric methods with real NBA applications.

### Tutorial Notebooks

Located in `examples/`, these Jupyter notebooks provide hands-on learning from beginner to expert level:

| Notebook | Level | Topics Covered | Time |
|----------|-------|---------------|------|
| **[01 - NBA 101 Getting Started](examples/01_nba_101_getting_started.ipynb)** | Beginner | Data loading, EDA, basic stats (correlation, regression, t-tests) | 30 min |
| **[02 - Player Valuation & Performance](examples/02_player_valuation_performance.ipynb)** | Intermediate | Time series (ARIMA), panel data, causal inference (PSM), player comparison | 45 min |
| **[03 - Team Strategy & Game Outcomes](examples/03_team_strategy_game_outcomes.ipynb)** | Advanced | Game theory (Nash equilibrium), win probability (logistic), DiD, network analysis | 60 min |
| **[04 - Contract Analytics & Salary Cap](examples/04_contract_analytics_salary_cap.ipynb)** | Advanced | Contract valuation, salary cap optimization, trade evaluation, RDD | 60 min |
| **[05 - Live Game Analytics Dashboard](examples/05_live_game_analytics_dashboard.ipynb)** | Expert | Real-time win probability, player tracking (particle filters), in-game decisions | 60 min |

### Supporting Documentation

- **[Best Practices Guide](examples/BEST_PRACTICES.md)** - Comprehensive guide to using the framework effectively
  - Method selection decision tree
  - Data preparation guidelines
  - Model validation checklist
  - Performance optimization tips
  - Common pitfalls and solutions

- **[Quick Reference Card](examples/QUICK_REFERENCE.md)** - One-page cheat sheet
  - All 27+ methods with code examples
  - Parameter quick reference
  - Error messages and solutions
  - Performance guidelines

### What You'll Learn

**Econometric Methods (23 methods)**:
- Basic Analysis: OLS, Logistic Regression, T-Tests
- Time Series: ARIMA, BVAR, BSTS, Kalman Filters
- Panel Data: Fixed Effects, Random Effects, Hierarchical Bayesian
- Causal Inference: PSM, DiD, RDD, Instrumental Variables

**Advanced Methods (4 Bayesian methods)**:
- Bayesian VAR with Minnesota Prior (IRF, FEVD)
- Bayesian Structural Time Series (component decomposition)
- Hierarchical Bayesian TS (shrinkage, partial pooling)
- Particle Filters (real-time state estimation)

**Real-World Applications**:
- Player performance forecasting
- Contract valuation and salary cap optimization
- Win probability modeling
- Trade scenario evaluation
- Draft value analysis (regression discontinuity)
- Live game analytics dashboard

### Quick Start with Tutorials

```bash
# Navigate to examples directory
cd examples/

# Start with beginner notebook
jupyter notebook 01_nba_101_getting_started.ipynb

# Or run all notebooks in order
jupyter notebook
```

**Requirements**: All notebooks use synthetic data by default (no database required). To use real NBA data, connect to MCP server.

### Tutorial Features

- ✅ **Progressive Learning**: Builds from basic to advanced concepts
- ✅ **Real NBA Scenarios**: Contract negotiations, draft picks, live games
- ✅ **Code + Explanation**: Every analysis explained with interpretation
- ✅ **Practice Exercises**: Test your understanding
- ✅ **Production-Ready**: All code works with real data
- ✅ **<5 min Runtime**: Fast execution on any laptop

### Performance Benchmarks

From actual testing (see `BAYESIAN_METHODS_PERFORMANCE_REPORT.md`):

| Method | Execution Time | Memory | Use Case |
|--------|---------------|--------|----------|
| Particle Filter (Game) | 0.03s | <100 MB | ⚡ Real-time win probability |
| Particle Filter (Player) | 0.08s | <100 MB | ⚡ Live player tracking |
| ARIMA | ~5s | ~200 MB | Forecasting (10 games) |
| BSTS | ~40s | ~300 MB | Career trajectory analysis |
| BVAR | ~60s | ~500 MB | Multi-stat forecasting + IRF |
| Hierarchical TS | ~120s | ~800 MB | Team-wide player comparison |

**Conclusion**: All methods production-ready, particle filters real-time capable! ✅

---

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

### 📊 Examples & Demonstrations
- **examples/phase2_nba_analytics_demo.ipynb** - Comprehensive demo of all 23 Phase 2 econometric methods
- **examples/README.md** - Examples documentation and usage guide
- **PHASE2_DAY6_SUMMARY.md** - Complete Phase 2 implementation summary

### 📖 Reference
- **.env.example** - Environment variable template
- **tests/** - Connection and integration tests (100% pass rate for ML)
- **scripts/** - Test and diagnostic scripts
- **SECRETS_MANAGEMENT_GUIDE.md** - Complete secrets management documentation
- **TEAM_MIGRATION_GUIDE.md** - Migration guide for team members

## Configuration

### 🔐 Secrets Management System

This project uses a **hierarchical secrets management system** for secure, organized credential storage:

**Directory Structure:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/
├── sports_assets/
│   └── big_cat_bets_simulators/
│       └── NBA/
│           ├── nba-mcp-synthesis/
│           │   ├── .env.nba_mcp_synthesis.production/
│           │   ├── .env.nba_mcp_synthesis.development/
│           │   └── .env.nba_mcp_synthesis.test/
│           ├── nba-simulator-aws/
│           │   ├── .env.nba_simulator_aws.production/
│           │   ├── .env.nba_simulator_aws.development/
│           │   └── .env.nba_simulator_aws.test/
│           └── nba_mcp_synthesis_global/
│               ├── .env.nba_mcp_synthesis_global.production/
│               ├── .env.nba_mcp_synthesis_global.development/
│               └── .env.nba_mcp_synthesis_global.test/
```

**Key Features:**
- **Context-Aware Loading**: Automatically loads secrets based on project, sport, and environment
- **Secure Permissions**: All secret files have 600 permissions, directories have 700
- **Naming Convention**: `SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT` (e.g., `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`)
- **Health Monitoring**: Continuous validation and API connectivity checks
- **Docker Integration**: Seamless container deployment with secret injection

**Quick Setup:**
```bash
# 1. Load secrets for current project
source /Users/ryanranft/load_env_hierarchical.py

# 2. Or use the unified loader directly
python3 /Users/ryanranft/load_env_hierarchical.py

# 3. Verify secrets are loaded
python3 mcp_server/secrets_health_monitor.py --once
```

**See [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md) for complete documentation.**

### Environment Variables

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
