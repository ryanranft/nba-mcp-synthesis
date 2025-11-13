# Brave Search MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: AWS Knowledge MCP](AWS_KNOWLEDGE_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [Next: GitHub MCP →](GITHUB_MCP_IMPLEMENTATION.md)

---

**Purpose:** Real-time injury news, last-minute lineup changes, breaking team news affecting odds, weather conditions.

**Priority:** High (critical edge for betting)
**Estimated Time:** 20 minutes (including API signup)
**Credentials Required:** Yes (Brave Search API Key)

---

## Implementation Checklist

### Prerequisites
- [ ] Internet connection for API signup
- [ ] Email address for account creation
- [ ] Understand rate limits (2,000 queries/month free tier)

---

### Step 1: Get Brave Search API Key

- [ ] Navigate to https://brave.com/search/api/

- [ ] Click "Get Started" or "Sign Up"

- [ ] Create account:
  - [ ] Enter email address
  - [ ] Set password
  - [ ] Verify email

- [ ] Request API access:
  - [ ] Fill out application form
  - [ ] Select "Free" tier (2,000 queries/month)
  - [ ] Agree to terms of service

- [ ] Wait for approval (usually instant or within 24 hours)

- [ ] Navigate to API dashboard

- [ ] Generate API key:
  - [ ] Click "Create API Key"
  - [ ] Give it a name: `Claude Code - NBA MCP Synthesis`
  - [ ] Copy the API key immediately
  - [ ] **IMPORTANT:** Save API key securely - you won't see it again!

- [ ] Note rate limits:
  - Free tier: 2,000 queries/month
  - ~66 queries/day
  - Use sparingly for high-value searches only

---

### Step 2: Add API Key to Hierarchical Secrets System

#### Production Credentials

- [ ] Create production credential file:
  ```bash
  echo "your-brave-api-key-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```

- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
  ```

#### Development Credentials (Optional)

- [ ] Create development credential file:
  ```bash
  echo "your-brave-api-key-here" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

- [ ] Set proper permissions:
  ```bash
  chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/BRAVE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
  ```

---

### Step 3: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add Brave Search MCP configuration to `mcpServers` section:
  ```json
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "your-api-key-here-temporarily"
    }
  }
  ```

- [ ] Replace `"your-api-key-here-temporarily"` with actual API key

- [ ] Save file

**Note:** Future enhancement will integrate with hierarchical secrets system.

---

### Step 4: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add Brave Search MCP configuration to `mcpServers` section:
  ```json
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "your-api-key-here-temporarily"
    }
  }
  ```

- [ ] Replace with actual API key

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same Brave Search MCP configuration

- [ ] Save file

---

### Step 5: Test Brave Search MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "brave-search" appears in connected MCPs list

#### Test General Search

- [ ] **NBA injury report:**
  - Ask Claude: "Search Brave for: NBA injury report today"
  - Verify it returns current injury news

- [ ] **Team-specific search:**
  - Ask Claude: "Search Brave for: Lakers lineup changes November 2024"
  - Verify it returns relevant news articles

- [ ] **Player-specific search:**
  - Ask Claude: "Search Brave for: LeBron James injury status"
  - Verify it returns current status

---

### Step 6: Test Real-Time Betting Intel

- [ ] **Pre-game injury check:**
  - Search for today's game participants + "injury report"
  - Verify results show latest injury news

- [ ] **Lineup verification:**
  - Search for specific team + "starting lineup today"
  - Verify results show current lineup info

- [ ] **Breaking news:**
  - Search for player name + "news today"
  - Verify results show latest developments

- [ ] **Weather check (if applicable):**
  - Search for "NBA weather delay [today's date]"
  - Verify results show any weather-related news

---

### Step 7: Integration with Betting Workflow

#### Pre-Game Checklist (Run 1-2 hours before games)

- [ ] **Search for injuries:**
  ```
  "Search Brave for: [Team A] vs [Team B] injury report [today's date]"
  ```

- [ ] **Check lineup changes:**
  ```
  "Search Brave for: [Team A] starting lineup [today's date]"
  ```

- [ ] **Verify key players:**
  ```
  "Search Brave for: [Star Player Name] playing tonight?"
  ```

- [ ] **Check for breaking news:**
  ```
  "Search Brave for: [Team Name] news today"
  ```

#### Line Movement Investigation

When line moves significantly:

- [ ] **Search for cause:**
  ```
  "Search Brave for: [Team Name] news last hour"
  ```

- [ ] **Verify sharp action trigger:**
  ```
  "Search Brave for: [Team Name] lineup change"
  ```

#### Post-Game Analysis

- [ ] **Unexpected outcome investigation:**
  ```
  "Search Brave for: [Team Name] [unexpected event]"
  ```

---

### Step 8: Automated Integration (Future Enhancement)

#### Add to daily_betting_analysis.py

```python
# Before generating predictions
for game in today_games:
    team_a = game['home_team']
    team_b = game['away_team']

    # Search for injury news
    query = f"{team_a} vs {team_b} injury report {today_date}"
    # Call Brave Search API via MCP

    # Search for lineup changes
    query = f"{team_a} starting lineup {today_date}"
    # Call Brave Search API via MCP

    # Alert if breaking news found
    if injury_news_found or lineup_change:
        send_alert(f"Breaking news affects {team_a} vs {team_b}")
```

#### Add to alert_system.py

```python
# Monitor line movements
if line_move > 2.0:  # 2+ point move
    team = game['team']

    # Search for cause
    query = f"{team} news last 2 hours"
    # Call Brave Search API via MCP

    # Alert if news found
    if breaking_news:
        send_sms(f"Line move on {team} due to: {news_headline}")
```

---

## Rate Limit Management

### Free Tier Limits
- **2,000 queries/month** = ~66 queries/day
- Plan usage carefully for high-value searches only

### Cost-Effective Usage Strategy

#### HIGH Priority (Use Brave Search):
- ✅ Pre-game injury checks (15 games/day = 30 queries)
- ✅ Line movement investigation (5-10 significant moves = 10 queries)
- ✅ Breaking news verification (5 queries/day)
- ✅ Total: ~45 queries/day

#### LOW Priority (Use Alternative):
- ❌ General NBA news (use RSS feeds)
- ❌ Historical research (use databases)
- ❌ Statistics (use existing data sources)
- ❌ Routine checks (automate via web scraping)

### Upgrade Decision Point

**Consider upgrading to paid tier if:**
- Consistently using >60 queries/day
- Missing critical information due to rate limits
- ROI from betting edge > $50/month (cost of paid tier)
- Need faster/more comprehensive results

---

## Troubleshooting

### API Key Invalid

**Symptom:** "Invalid API key" or authentication errors

**Solution:**
1. Verify API key copied correctly (no extra spaces)
2. Check API key is active in Brave dashboard
3. Regenerate API key if needed
4. Update key in all 3 config files

### Rate Limit Exceeded

**Symptom:** "Rate limit exceeded" error

**Solution:**
1. Check usage in Brave dashboard
2. Wait for monthly reset
3. Prioritize high-value queries only
4. Consider upgrading to paid tier
5. Implement query caching to reduce duplicates

### No Results Returned

**Symptom:** Search returns empty or irrelevant results

**Solution:**
1. Refine search query (be more specific)
2. Try alternative keywords
3. Check if news is too recent (may not be indexed yet)
4. Verify player/team names spelled correctly

### Connection Failures

**Symptom:** Brave Search MCP not connecting

**Solution:**
1. Test npx installation:
   ```bash
   npx -y @modelcontextprotocol/server-brave-search --help
   ```
2. Verify API key is valid
3. Check internet connection
4. Restart Claude app completely

---

## Security Best Practices

1. **Never commit API key** to version control
2. **Use hierarchical secrets** for API key storage
3. **Set file permissions to 600** on credential files
4. **Rotate API key regularly** (every 6 months)
5. **Monitor usage** in Brave dashboard for anomalies
6. **Use separate keys** for development vs production
7. **Revoke key immediately** if compromised

---

## Verification Checklist

- [ ] Brave Search API account created
- [ ] API key generated
- [ ] API key stored in hierarchical secrets system
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] Brave Search MCP connects successfully
- [ ] Can search for NBA injury reports
- [ ] Can search for lineup changes
- [ ] Can search for player status
- [ ] Rate limit management strategy defined
- [ ] Integration with betting workflow documented

---

## Next Steps After Implementation

1. **Test with tonight's games** - Run pre-game checks
2. **Track query usage** - Monitor daily query count
3. **Build query templates** - Standardize common searches
4. **Integrate with alerts** - Auto-search on line movements
5. **Evaluate ROI** - Track betting edge gained from real-time intel

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
