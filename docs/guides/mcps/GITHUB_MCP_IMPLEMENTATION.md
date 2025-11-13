# GitHub MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: Brave Search MCP](BRAVE_SEARCH_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [Next: Time/Everything MCP →](TIME_EVERYTHING_MCP_IMPLEMENTATION.md)

---

**Purpose:** Automate PR creation, track betting outcomes as issues, search code across repos, manage deployment workflows.

**Priority:** High
**Estimated Time:** 15 minutes
**Credentials Required:** Yes (GitHub Personal Access Token)

---

## Implementation Checklist

### Prerequisites
- [ ] GitHub account exists
- [ ] Decide on token scope requirements

---

### Step 1: Create GitHub Personal Access Token

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
- [ ] **IMPORTANT:** Save token securely - you won't see it again!

---

### Step 2: Add Token to Hierarchical Secrets System

#### Production Credentials

- [ ] Create production credential file:
  ```bash
  echo "your-github-token-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```

- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```

#### Development Credentials (Optional)

- [ ] Create development credential file:
  ```bash
  echo "your-github-token-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/GITHUB_PERSONAL_ACCESS_TOKEN_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

---

### Step 3: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add GitHub MCP configuration to `mcpServers` section:
  ```json
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here-temporarily"
    }
  }
  ```

- [ ] Replace `"your-token-here-temporarily"` with actual token

- [ ] Save file

**Note:** Future enhancement will integrate with hierarchical secrets system.

---

### Step 4: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add GitHub MCP configuration to `mcpServers` section:
  ```json
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here-temporarily"
    }
  }
  ```

- [ ] Replace with actual token

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same GitHub MCP configuration

- [ ] Save file

---

### Step 5: Test GitHub MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "github" appears in connected MCPs list

#### Test Basic Commands

- [ ] **List repositories:**
  - Ask Claude: "List my GitHub repositories"
  - Verify it shows your repos

- [ ] **Search code:**
  - Ask Claude: "Search for 'kelly_criterion' in my nba-mcp-synthesis repo"
  - Verify it finds the code

- [ ] **View recent issues:**
  - Ask Claude: "Show recent issues in nba-mcp-synthesis"
  - Verify it displays issues

- [ ] **Create test issue:**
  - Ask Claude: "Create a test issue in nba-mcp-synthesis titled 'MCP Test' with body 'Testing GitHub MCP integration'"
  - Verify issue is created
  - Close the test issue

---

### Step 6: Document Common Usage Patterns

#### For PR Creation

- [ ] **Model updates:**
  - "Create a PR for the latest model training results"
  - "Update calibration model and create PR"

- [ ] **Feature additions:**
  - "Create PR for new Kelly criterion enhancement"
  - "Add feature extraction improvements and create PR"

#### For Issue Tracking

- [ ] **Betting outcomes:**
  - "Create issue tracking today's betting outcomes"
  - "Log failed bet prediction as issue"

- [ ] **Model performance:**
  - "Create issue for model performance degradation"
  - "Track calibration drift as issue"

#### For Code Search

- [ ] **Strategy implementations:**
  - "Find all uses of arbitrage detection"
  - "Search for probability calibration implementations"

- [ ] **Feature debugging:**
  - "Find where player_features are extracted"
  - "Show me all line_movement feature calculations"

#### For Deployment

- [ ] **Workflow automation:**
  - "Update GitHub Actions workflow for daily training"
  - "Add deployment step to production workflow"

---

### Step 7: Integration with NBA Betting Workflow

#### Daily Operations

- [ ] Create issues for bet outcomes:
  ```python
  # Add to paper_trade_today.py
  # After each bet closes:
  # - If >10% edge: create issue with outcome
  # - If failed prediction: create issue with analysis
  ```

- [ ] Track model versions:
  ```python
  # When retraining model:
  # - Create PR with new model artifacts
  # - Link to training metrics
  # - Auto-tag with version number
  ```

#### Weekly Reviews

- [ ] Search for patterns:
  - "Find all 'underdog' betting strategies"
  - "Show spread betting feature implementations"

- [ ] Review issues:
  - "Summarize betting issues from last week"
  - "Show failed predictions grouped by team"

---

## Troubleshooting

### Token Permission Errors

**Symptom:** "Resource not accessible by personal access token"

**Solution:**
1. Regenerate token with correct scopes
2. Ensure `repo` and `workflow` are selected
3. Update token in all 3 config files

### Connection Failures

**Symptom:** GitHub MCP not appearing in `/mcp` list

**Solution:**
1. Check npx can install package:
   ```bash
   npx -y @modelcontextprotocol/server-github --help
   ```
2. Verify token is valid (check GitHub settings)
3. Restart Claude app completely
4. Check Claude logs for errors

### Rate Limiting

**Symptom:** "API rate limit exceeded"

**Solution:**
- Personal access tokens have higher rate limits than anonymous
- Wait for rate limit to reset (shown in error message)
- Consider using GitHub Apps for higher limits

---

## Security Best Practices

1. **Never commit token** to version control
2. **Use hierarchical secrets** for token storage
3. **Set file permissions to 600** on credential files
4. **Rotate token every 90 days**
5. **Use minimal scopes** required for functionality
6. **Revoke token immediately** if compromised
7. **Use separate tokens** for development vs production

---

## Verification Checklist

- [ ] Token created with correct scopes
- [ ] Token stored in hierarchical secrets system
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] GitHub MCP connects successfully
- [ ] Can list repositories
- [ ] Can search code
- [ ] Can view issues
- [ ] Can create/close test issue
- [ ] Documented usage patterns
- [ ] Integrated with workflow

---

## Next Steps After Implementation

1. **Remove token from config files** and implement hierarchical secrets wrapper
2. **Create GitHub Actions workflow** for automated model training
3. **Setup issue templates** for betting outcomes and model performance
4. **Configure branch protection** rules for production deployments
5. **Enable GitHub Projects** for tracking betting experiments

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
