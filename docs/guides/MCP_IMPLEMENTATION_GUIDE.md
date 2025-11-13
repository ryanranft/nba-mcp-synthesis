# MCP Implementation Guide
## NBA MCP Synthesis Project

This guide provides step-by-step instructions for implementing all 7 recommended MCP servers for the NBA betting analytics project.

---

## Implementation Status Overview

**Overall Progress:** 0/7 MCPs Implemented (0%)

| MCP | Status | Guide |
|-----|--------|-------|
| 1. Memory MCP | ⬜ Not Started | [📄 Implement](mcps/MEMORY_MCP_IMPLEMENTATION.md) |
| 2. AWS Knowledge MCP | ⬜ Not Started | [📄 Implement](mcps/AWS_KNOWLEDGE_MCP_IMPLEMENTATION.md) |
| 3. Brave Search MCP | ⬜ Not Started | [📄 Implement](mcps/BRAVE_SEARCH_MCP_IMPLEMENTATION.md) |
| 4. GitHub MCP | ⬜ Not Started | [📄 Implement](mcps/GITHUB_MCP_IMPLEMENTATION.md) |
| 5. Time/Everything MCP | ⬜ Not Started | [📄 Implement](mcps/TIME_EVERYTHING_MCP_IMPLEMENTATION.md) |
| 6. Fetch MCP | ⬜ Not Started | [📄 Implement](mcps/FETCH_MCP_IMPLEMENTATION.md) |
| 7. Puppeteer MCP | ⬜ Not Started | [📄 Implement](mcps/PUPPETEER_MCP_IMPLEMENTATION.md) |

**Legend:** ⬜ Not Started | 🔄 In Progress | ✅ Completed

**Estimated Total Time:** ~100 minutes

---

## Quick Navigation

📊 **[MCP Progress Tracker](mcps/README.md)** - Detailed status and notes for all MCPs

---

## Table of Contents

1. [GitHub MCP](#1-github-mcp) - PR automation and issue tracking ([📄 Full Guide](mcps/GITHUB_MCP_IMPLEMENTATION.md))
2. [Memory MCP](#2-memory-mcp) - Betting strategy insights ([📄 Full Guide](mcps/MEMORY_MCP_IMPLEMENTATION.md))
3. [Brave Search MCP](#3-brave-search-mcp) - Real-time injury/news intel ([📄 Full Guide](mcps/BRAVE_SEARCH_MCP_IMPLEMENTATION.md))
4. [Puppeteer MCP](#4-puppeteer-mcp) - Odds scraping ([📄 Full Guide](mcps/PUPPETEER_MCP_IMPLEMENTATION.md))
5. [Time/Everything MCP](#5-timeeverything-mcp) - Scheduling and time awareness ([📄 Full Guide](mcps/TIME_EVERYTHING_MCP_IMPLEMENTATION.md))
6. [Fetch MCP](#6-fetch-mcp) - External API integration ([📄 Full Guide](mcps/FETCH_MCP_IMPLEMENTATION.md))
7. [AWS Knowledge MCP](#7-aws-knowledge-mcp) - Real-time AWS documentation access ([📄 Full Guide](mcps/AWS_KNOWLEDGE_MCP_IMPLEMENTATION.md))

---

## 1. GitHub MCP

**Purpose:** Automate PR creation, track betting outcomes as issues, search code across repos, manage deployment workflows.

### Implementation Checklist

#### Prerequisites
- [ ] GitHub account exists
- [ ] Decide on token scope requirements

#### Step 1: Create GitHub Personal Access Token
- [ ] Navigate to https://github.com/settings/tokens
- [ ] Click "Generate new token" → "Generate new token (classic)"
- [ ] Set token name: `Claude Code - NBA MCP Synthesis`
- [ ] Set expiration: 90 days (or custom)
- [ ] Select required scopes:
  - [ ] `repo` (Full control of private repositories)
  - [ ] `workflow` (Update GitHub Action workflows)
  - [ ] `read:org` (Read org and team membership)
  - [ ] `read:user` (Read user profile data)
- [ ] Generate token and copy it immediately

#### Step 2: Add Token to Hierarchical Secrets System
- [ ] Create production credential file:
  ```bash
  echo "your-github-token-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```
- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```
- [ ] Create development credential file (optional):
  ```bash
  echo "your-github-token-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

#### Step 3: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add GitHub MCP configuration:
  ```json
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here-temporarily"
    }
  }
  ```
  **Note:** We'll update this to use hierarchical secrets in a future enhancement.

#### Step 4: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here-temporarily"
    }
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 5: Test GitHub MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test commands:
  - [ ] List repositories
  - [ ] Search code for "kelly_criterion"
  - [ ] View recent issues
  - [ ] Create a test issue (then close it)

#### Step 6: Document Common Usage Patterns
- [ ] Create PR for model updates
- [ ] Track betting outcomes as issues
- [ ] Search betting strategy implementations
- [ ] Automate deployment workflows

**Priority:** High
**Estimated Time:** 15 minutes
**Dependencies:** None

---

## 2. Memory MCP

**Purpose:** Remember betting strategies that worked/failed, track model performance insights across sessions, store team patterns and betting edge observations.

### Implementation Checklist

#### Prerequisites
- [ ] Node.js and npx available (already verified)
- [ ] No credentials required

#### Step 1: Test Memory MCP Installation
- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-memory --help
  ```
- [ ] Verify installation successful

#### Step 2: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add Memory MCP configuration:
  ```json
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
  ```

#### Step 3: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 4: Test Memory MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test memory storage:
  - [ ] Store: "Lakers tend to exceed expected win probability when playing back-to-back home games"
  - [ ] Store: "Model consistently underestimates underdogs with +7.5 spread or greater"
  - [ ] Query: "What patterns have we observed about Lakers?"
  - [ ] Query: "What spread betting insights do we have?"

#### Step 5: Define Memory Categories
- [ ] Betting strategy learnings
- [ ] Model performance patterns
- [ ] Team-specific observations
- [ ] Line movement insights
- [ ] Feature importance discoveries
- [ ] Failed approaches to avoid

#### Step 6: Integration with Betting Workflow
- [ ] Add memory logging to `paper_trade_today.py`
- [ ] Store outcomes of high-confidence bets
- [ ] Track Kelly criterion adjustments
- [ ] Document edge decay observations

**Priority:** High (critical for learning over time)
**Estimated Time:** 10 minutes
**Dependencies:** None

---

## 3. Brave Search MCP

**Purpose:** Real-time injury news, last-minute lineup changes, breaking team news affecting odds, weather conditions.

### Implementation Checklist

#### Prerequisites
- [ ] Brave Search API account
- [ ] API key

#### Step 1: Get Brave Search API Key
- [ ] Navigate to https://brave.com/search/api/
- [ ] Sign up for account (free tier available)
- [ ] Request API access
- [ ] Navigate to API dashboard
- [ ] Generate API key
- [ ] Note rate limits: 2,000 queries/month (free tier)

#### Step 2: Add API Key to Hierarchical Secrets System
- [ ] Create production credential file:
  ```bash
  echo "your-brave-api-key-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```
- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```
- [ ] Create development credential file (optional):
  ```bash
  echo "your-brave-api-key-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

#### Step 3: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add Brave Search MCP configuration:
  ```json
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "your-api-key-here-temporarily"
    }
  }
  ```

#### Step 4: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "your-api-key-here-temporarily"
    }
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 5: Test Brave Search MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test searches:
  - [ ] "NBA injury report today"
  - [ ] "Lakers lineup changes [today's date]"
  - [ ] "Giannis Antetokounmpo injury status"
  - [ ] "NBA weather delay [today's date]"

#### Step 6: Integration with Betting Workflow
- [ ] Add pre-game news check to `daily_betting_analysis.py`
- [ ] Alert on late injury news
- [ ] Monitor line movement triggers
- [ ] Check weather for outdoor events (if applicable)

**Priority:** High (critical edge for betting)
**Estimated Time:** 20 minutes (including API signup)
**Dependencies:** None

---

## 4. Puppeteer MCP

**Purpose:** Scrape live betting odds from sites without APIs, monitor line movements visually, capture arbitrage opportunities, screenshot odds for records.

### Implementation Checklist

#### Prerequisites
- [ ] Node.js and npx available
- [ ] Chromium dependencies installed
- [ ] Understanding of web scraping ethics and legality

#### Step 1: Install System Dependencies (macOS)
- [ ] Check if Chromium dependencies exist:
  ```bash
  which chromium || echo "Chromium not found"
  ```
- [ ] Install if needed (Puppeteer usually handles this automatically)

#### Step 2: Test Puppeteer MCP Installation
- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-puppeteer --help
  ```
- [ ] Verify installation successful

#### Step 3: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add Puppeteer MCP configuration:
  ```json
  "puppeteer": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    "env": {}
  }
  ```

#### Step 4: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "puppeteer": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    "env": {}
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 5: Test Puppeteer MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test basic scraping:
  - [ ] Navigate to a public NBA stats page
  - [ ] Extract table data
  - [ ] Take screenshot
  - [ ] Extract text content

#### Step 6: Create Scraping Utilities
- [ ] Document common selectors for betting sites
- [ ] Create rate limiting strategy
- [ ] Setup user-agent rotation
- [ ] Respect robots.txt

#### Step 7: Legal and Ethical Considerations
- [ ] Review terms of service for target sites
- [ ] Implement respectful rate limiting
- [ ] Add proper user-agent identification
- [ ] Document usage policies

**Priority:** Medium (useful but not critical)
**Estimated Time:** 30 minutes
**Dependencies:** None
**Warning:** Use responsibly and legally

---

## 5. Time/Everything MCP

**Purpose:** Time-aware queries for game schedules, calculate rest days automatically, schedule daily pipelines, timezone conversions.

### Implementation Checklist

#### Prerequisites
- [ ] Node.js and npx available
- [ ] No credentials required

#### Step 1: Test Time/Everything MCP Installation
- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-everything --help
  ```
- [ ] Verify installation successful

#### Step 2: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add Time/Everything MCP configuration:
  ```json
  "everything": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {}
  }
  ```

#### Step 3: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "everything": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {}
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 4: Test Time/Everything MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test time queries:
  - [ ] "What time is it in Los Angeles?" (game location)
  - [ ] "How many days until next Monday?" (schedule planning)
  - [ ] "Convert 7:30 PM EST to PST" (game time conversions)
  - [ ] "What day of week is 3 days from now?" (rest day calculations)

#### Step 5: Integration with Betting Workflow
- [ ] Add game time validation to `daily_betting_analysis.py`
- [ ] Calculate rest days automatically
- [ ] Schedule pipeline runs relative to game times
- [ ] Alert on timezone-specific betting windows

**Priority:** Medium
**Estimated Time:** 10 minutes
**Dependencies:** None

---

## 6. Fetch MCP

**Purpose:** Hit external betting odds APIs, fetch real-time NBA data, integration testing for APIs, webhook testing.

### Implementation Checklist

#### Prerequisites
- [ ] Node.js and npx available
- [ ] No credentials required (credentials passed per-request)

#### Step 1: Test Fetch MCP Installation
- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-fetch --help
  ```
- [ ] Verify installation successful

#### Step 2: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add Fetch MCP configuration:
  ```json
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "env": {}
  }
  ```

#### Step 3: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "env": {}
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 4: Test Fetch MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test API calls:
  - [ ] Fetch public NBA API endpoint (e.g., `https://www.balldontlie.io/api/v1/games`)
  - [ ] Test with authentication header
  - [ ] Test POST request
  - [ ] Test error handling

#### Step 5: Document Common API Endpoints
- [ ] NBA stats APIs
- [ ] Odds API providers
- [ ] Weather APIs
- [ ] News APIs

#### Step 6: Integration with Betting Workflow
- [ ] Real-time odds fetching during games
- [ ] API health checks
- [ ] Webhook testing for notifications
- [ ] Integration testing for external services

**Priority:** Medium
**Estimated Time:** 10 minutes
**Dependencies:** None

---

## 7. AWS Knowledge MCP

**Purpose:** Real-time AWS documentation access for accurate boto3/AWS code generation. Reduces hallucinations when working with AWS services.

**Note:** This MCP complements (not replaces) your existing boto3/psycopg2 connectors. It provides documentation context to help Claude generate better AWS code.

### Implementation Checklist

#### Prerequisites
- [ ] None (remote AWS-managed service)
- [ ] No credentials required
- [ ] Internet connection for remote service access

#### Step 1: Test AWS Knowledge MCP Installation
- [ ] Run test command:
  ```bash
  uvx awslabs.aws-knowledge-mcp-server@latest --help
  ```
- [ ] Verify installation successful (will download on first run)

#### Step 2: Update MCP Configuration - Desktop App
- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Add AWS Knowledge MCP configuration:
  ```json
  "aws-knowledge": {
    "command": "uvx",
    "args": ["-y", "awslabs.aws-knowledge-mcp-server@latest"],
    "env": {
      "AWS_REGION": "us-east-1"
    }
  }
  ```

#### Step 3: Update MCP Configuration - CLI
- [ ] Update `.claude/mcp.json`:
  ```json
  "aws-knowledge": {
    "command": "uvx",
    "args": ["-y", "awslabs.aws-knowledge-mcp-server@latest"],
    "env": {
      "AWS_REGION": "us-east-1"
    }
  }
  ```
- [ ] Update `.mcp.json` with same configuration

#### Step 4: Test AWS Knowledge MCP
- [ ] Restart Claude desktop app
- [ ] Run `/mcp` in CLI to reconnect
- [ ] Test documentation queries:
  - [ ] "What's the latest boto3 API for S3 PutObject with metadata?"
  - [ ] "How do I configure RDS PostgreSQL connection pooling best practices?"
  - [ ] "What are the IAM permissions needed for Lambda execution role?"
  - [ ] "Show me AWS best practices for S3 lifecycle policies"

#### Step 5: Integration with Development Workflow
- [ ] Use for boto3 code generation
- [ ] Query AWS best practices during development
- [ ] Get up-to-date API references for new AWS features
- [ ] Validate existing AWS code against latest recommendations

#### Step 6: Document Use Cases
- [ ] Generating boto3 code for S3 operations
- [ ] Troubleshooting RDS connection issues
- [ ] Understanding AWS Lambda event schemas
- [ ] Querying CloudWatch metrics API
- [ ] Validating IAM policy syntax

**Priority:** Medium-High (valuable for AWS development)
**Estimated Time:** 5 minutes
**Dependencies:** None
**Cost:** Free (remote AWS-managed service)

**Benefits:**
- ✅ No credential management required
- ✅ Always up-to-date with latest AWS APIs
- ✅ Reduces AI hallucinations for AWS code
- ✅ Complements your existing AWS infrastructure
- ✅ Zero maintenance overhead

**Important Notes:**
- This does NOT replace your existing boto3/psycopg2 connectors
- It provides documentation only, not execution capabilities
- Your direct SDK approach remains superior for actual AWS operations
- Use this to help Claude generate better AWS code

---

## Implementation Order Recommendation

Based on priority and dependencies:

1. **Memory MCP** (10 min) - Start learning immediately
2. **AWS Knowledge MCP** (5 min) - Improve AWS code generation (no credentials!)
3. **Brave Search MCP** (20 min) - Critical for real-time intel
4. **GitHub MCP** (15 min) - Workflow automation
5. **Time/Everything MCP** (10 min) - Scheduling support
6. **Fetch MCP** (10 min) - API integration
7. **Puppeteer MCP** (30 min) - Advanced scraping (optional)

**Total Estimated Time:** ~100 minutes

---

## Post-Implementation Verification

After all MCPs are configured:

- [ ] All MCPs listed in desktop app config
- [ ] All MCPs listed in CLI configs (`.claude/mcp.json` and `.mcp.json`)
- [ ] All credentials stored in hierarchical secrets system
- [ ] Desktop app connects to all MCPs
- [ ] CLI connects to all MCPs via `/mcp` command
- [ ] Test each MCP with sample queries
- [ ] Document common usage patterns for each MCP
- [ ] Update project README with MCP capabilities

---

## Troubleshooting

### MCP Not Connecting
1. Check MCP server logs in Claude app
2. Verify npx can run the package: `npx -y @modelcontextprotocol/server-[name]`
3. Check credentials are loaded correctly
4. Restart Claude app completely

### Rate Limiting (Brave Search)
- Free tier: 2,000 queries/month
- Use sparingly for high-value queries only
- Consider upgrading if needed for production

### Puppeteer Issues
- Chromium download may take time on first run
- Check disk space for Chromium installation
- Verify network can download Chromium dependencies

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Always use hierarchical secrets** for API keys
3. **Set file permissions to 600** on credential files
4. **Rotate tokens regularly** (every 90 days recommended)
5. **Use separate keys** for development vs production
6. **Monitor API usage** to detect anomalies
7. **Respect rate limits** to avoid account suspension

---

## Future Enhancements

- [ ] Update GitHub MCP to use hierarchical secrets via wrapper script
- [ ] Update Brave Search MCP to use hierarchical secrets via wrapper script
- [ ] Create unified MCP credential management system
- [ ] Add MCP health monitoring dashboard
- [ ] Automate MCP configuration synchronization
- [ ] Add MCP usage analytics

---

## Future Improvements

**Purpose:** Track improvements discovered during MCP implementation that can be added after core setup is complete. This prevents losing track of good ideas while maintaining focus on getting MCPs operational.

**When to add items here:**
- During implementation, discover a better approach but want to finish current setup first
- Find integration opportunities between MCPs
- Identify optimization or automation possibilities
- Notice missing documentation or examples
- Discover security or performance enhancements

**Implementation Priority:** Tackle these after all 7 MCPs are successfully implemented and tested.

---

### Credential Management

- [ ] Create wrapper scripts to load credentials from hierarchical secrets for GitHub MCP
- [ ] Create wrapper scripts to load credentials from hierarchical secrets for Brave Search MCP
- [ ] Build unified credential loader that works across all MCPs
- [ ] Add credential rotation automation (90-day reminder)
- [ ] Create credential health check script
- [ ] Document credential migration from config files to hierarchical secrets
- [ ] **Create credential setup helper scripts** (`scripts/setup_github_mcp_credentials.sh`, `scripts/setup_brave_search_credentials.sh`) - Interactive prompts for API keys with auto-validation, hierarchical secrets integration, permission setting (60 min, Medium Priority)

### Automation & Integration

- [ ] Auto-log high-confidence bet outcomes to Memory MCP
- [ ] Auto-search Brave for injury news when line moves >2 points
- [ ] Auto-create GitHub issues for failed model predictions
- [ ] Auto-fetch live odds via Fetch MCP before each game
- [ ] Schedule Puppeteer scraping for arbitrage detection
- [ ] Integrate Time/Everything MCP for automated rest day calculations
- [ ] Build unified MCP query interface for Python scripts
- [ ] **Build automated MCP verification script** (`scripts/verify_mcp_setup.py`) - Check if MCPs are in configs, test server startup, validate credentials exist, report working vs broken MCPs, auto-update Progress Tracker status (45 min, High Priority)
- [ ] **Create MCP configuration backup script** (`scripts/backup_mcp_configs.sh`) - Timestamped backups of all configs (desktop + CLI), restore capability, version history (30 min, Medium Priority)
- [ ] **Create Claude Code slash commands** (`.claude/commands/mcp-status.md`, `/mcp-test`, `/mcp-update`) - Quick MCP status checks, run verification tests, update progress tracker without leaving Claude (30 min, High Priority)

### Documentation & Training

- [ ] Create video tutorials for each MCP
- [ ] Build searchable knowledge base of successful queries
- [ ] Document common error patterns and solutions
- [ ] Create cheat sheet of most-used queries per MCP
- [ ] Write best practices guide based on real usage
- [ ] Document MCP performance benchmarks
- [ ] **Create Quick Reference Card** (`docs/guides/mcps/QUICK_REFERENCE.md`) - One-page cheat sheet with all MCP capabilities, common queries (copy-paste ready), credential locations, troubleshooting flowchart (15 min, High Priority)
- [ ] **Create MCP Query Template Library** (`docs/guides/mcps/QUERY_TEMPLATES.md`) - Pre-written queries for each MCP organized by use case (betting, development, monitoring), with placeholders and example outputs (30 min, Medium Priority)
- [ ] **Update Project README** with MCP overview - Add section explaining MCP capabilities, link to implementation guide, link to progress tracker, quick start for new developers (10 min, High Priority)
- [ ] **Create Visual MCP Architecture Diagram** (`docs/guides/mcps/ARCHITECTURE.md`) - Show how MCPs connect to Claude, data flow visualization, integration points with NBA betting workflow, credential flow (1 hour, Low Priority)
- [ ] **Create Task Dependency Visualizer** (`docs/guides/mcps/TASK_DEPENDENCIES.md`) - Show which tasks must be done before others, which can be done in parallel, which are blocked, critical path to completion (30 min, Medium Priority)

### Monitoring & Observability

- [ ] Build MCP health monitoring dashboard
- [ ] Track MCP query success/failure rates
- [ ] Monitor API rate limit usage (Brave Search, GitHub)
- [ ] Alert on MCP connection failures
- [ ] Log MCP response times for performance tracking
- [ ] Create weekly MCP usage report
- [ ] **Build MCP usage analytics script** (`scripts/analyze_mcp_usage.py`) - Track which MCPs used most, monitor API rate limits, report query patterns, identify optimization opportunities, generate weekly reports (1 hour, Medium Priority)
- [ ] **Add Completion Milestone Markers** to Progress Tracker - Celebrate progress at 1/7, 3/7, 5/7, 7/7 MCPs complete with motivational messages and momentum tracking (5 min, Low Priority)
- [ ] **Create Task Estimation Accuracy Tracker** - Track actual vs estimated time for each task, identify where estimates are off, improve future planning, show complexity patterns (20 min, Medium Priority)

### Performance & Optimization

- [ ] Cache common Brave Search queries to reduce API usage
- [ ] Implement query batching for Fetch MCP
- [ ] Optimize Puppeteer scraping frequency
- [ ] Profile MCP query latencies
- [ ] Reduce Time/Everything MCP query frequency via caching
- [ ] Optimize Memory MCP storage size

### Security Enhancements

- [ ] Audit all MCP configurations for security issues
- [ ] Implement API key rotation automation
- [ ] Add rate limiting for automated MCP queries
- [ ] Review Puppeteer scraping legal compliance
- [ ] Encrypt local MCP credential storage
- [ ] Add MCP access logging for security monitoring

### Developer Experience

- [ ] Create CLI tool for common MCP operations
- [ ] Build Python wrapper library for MCP queries
- [ ] Add type hints for MCP function calls
- [ ] Create IDE snippets for common MCP queries
- [ ] Build test suite for MCP integrations
- [ ] Add MCP query examples to each Python script
- [ ] **Create Task Execution Template** (`docs/guides/mcps/TASK_EXECUTION_TEMPLATE.md`) - Standardized workflow for each task: pre-task checklist, during task steps, post-task verification, time tracking, issues documentation (15 min, High Priority)
- [ ] **Build Smart Task Picker Script** (`scripts/pick_next_task.py`) - Suggests next task based on time available, credentials ready, priority level, dependencies completed, shows expected outcome (45 min, High Priority)
- [ ] **Create Checkpoint Save System** (`scripts/save_checkpoint.sh`, `restore_checkpoint.sh`) - Save/restore current state at any point, includes configs/tracker/notes, timestamped snapshots for fearless experimentation (30 min, High Priority)
- [ ] **Create Daily Task Planner Template** (`docs/guides/mcps/DAILY_PLAN_TEMPLATE.md`) - Daily goal setting, time budgeting, success criteria, notes section for discoveries (10 min, High Priority)
- [ ] **Create Task Context Switcher** (`scripts/switch_task.sh`) - Save current task context, open relevant docs, update tracker, restore context later for clean switching (45 min, Medium Priority)
- [ ] **Create Pomodoro Timer Integration** (`scripts/mcp_pomodoro.sh`) - Track actual time spent, auto-update Progress Tracker, break reminders, compare actual vs estimated (30 min, Medium Priority)
- [ ] **Create Task Blocker Resolution Guide** (`docs/guides/mcps/BLOCKER_RESOLUTION.md`) - Common blockers with immediate actions, workarounds, unblocking steps, alternative tasks (30 min, Medium Priority)

### Cost Optimization

- [ ] Track Brave Search API usage vs free tier
- [ ] Identify opportunities to reduce API calls
- [ ] Evaluate ROI of paid API tiers
- [ ] Optimize query patterns to minimize costs
- [ ] Build cost dashboard for all MCP services

### Integration with NBA Betting Workflow

- [ ] Add Memory MCP logging to `paper_trade_today.py`
- [ ] Integrate Brave Search pre-game checks into `daily_betting_analysis.py`
- [ ] Add GitHub issue creation to `train_game_outcome_model.py`
- [ ] Use Time/Everything MCP in `prepare_game_features.py` for rest days
- [ ] Add Fetch MCP for live odds in `daily_betting_analysis.py`
- [ ] Build unified betting intelligence dashboard using all MCPs

### Testing & Validation

- [ ] Create integration tests for each MCP
- [ ] Build end-to-end test suite for MCP workflows
- [ ] Add error injection tests for MCP failure scenarios
- [ ] Create load tests for high-frequency MCP usage
- [ ] Validate MCP outputs against expected formats
- [ ] Build regression test suite for MCP queries
- [ ] **Create comprehensive MCP integration test suite** (`tests/mcp_integration/test_memory_mcp.py`, `test_github_mcp.py`, etc.) - Automated tests for all 7 MCPs, verify basic operations, test authentication, check rate limits, report failures (2-3 hours, Medium Priority)

---

**How to use this section:**
1. Add items as you discover them during implementation
2. Don't implement improvements immediately - stay focused on core setup
3. After all 7 MCPs are working, review this list
4. Prioritize by impact and effort
5. Tackle improvements incrementally
6. Remove items as they're completed
7. Add new discoveries continuously

---

*Last updated: 2025-11-12*
*Document version: 1.1 - Added AWS Knowledge MCP*
