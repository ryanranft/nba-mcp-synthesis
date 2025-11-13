# Puppeteer MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: Fetch MCP](FETCH_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md)

---

**Purpose:** Scrape live betting odds from sites without APIs, monitor line movements visually, capture arbitrage opportunities, screenshot odds for records.

**Priority:** Medium (useful but not critical)
**Estimated Time:** 30 minutes
**Credentials Required:** No
**Warning:** Use responsibly and legally

---

## Implementation Checklist

### Prerequisites
- [ ] Node.js and npx available (already installed)
- [ ] Understanding of web scraping ethics
- [ ] Understanding of legal considerations
- [ ] Chromium will be downloaded automatically (first run may take time)

---

### Step 1: Install System Dependencies (macOS)

- [ ] Check if Chromium dependencies exist:
  ```bash
  which chromium || echo "Chromium not found (will be auto-installed)"
  ```

- [ ] Verify disk space available (Chromium ~300MB):
  ```bash
  df -h /Users/ryanranft
  ```

- [ ] Note: Puppeteer usually handles Chromium installation automatically

---

### Step 2: Test Puppeteer MCP Installation

- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-puppeteer --help
  ```

- [ ] Verify command completes (may download Chromium on first run)

- [ ] Wait for download to complete if needed (~2-5 minutes)

- [ ] Confirm Chromium installed successfully

---

### Step 3: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add Puppeteer MCP configuration to `mcpServers` section:
  ```json
  "puppeteer": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    "env": {}
  }
  ```

- [ ] Save file

---

### Step 4: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add Puppeteer MCP configuration to `mcpServers` section:
  ```json
  "puppeteer": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    "env": {}
  }
  ```

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same Puppeteer MCP configuration

- [ ] Save file

---

### Step 5: Test Puppeteer MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "puppeteer" appears in connected MCPs list

#### Test Basic Scraping

- [ ] **Navigate to public page:**
  - Ask Claude: "Use Puppeteer to navigate to https://www.nba.com/stats"
  - Verify page loads

- [ ] **Extract text content:**
  - Ask Claude: "Extract the page title from https://www.nba.com"
  - Verify it returns the title

- [ ] **Take screenshot:**
  - Ask Claude: "Take a screenshot of https://www.nba.com/scores"
  - Verify screenshot is generated

- [ ] **Extract table data:**
  - Ask Claude: "Extract table data from https://www.nba.com/stats/leaders"
  - Verify it returns structured data

---

### Step 6: Create Scraping Utilities

#### Document Common Selectors

Create reference document for betting site selectors:

- [ ] **DraftKings selectors** (if using):
  - Game container: `.sportsbook-event-accordion__wrapper`
  - Odds values: `.sportsbook-odds`
  - Team names: `.event-cell__name-text`

- [ ] **FanDuel selectors** (if using):
  - Game rows: `[data-test-id="game-row"]`
  - Odds: `.odds-button`
  - Teams: `.team-name`

- [ ] **Generic patterns:**
  - Odds format: Look for decimal or American odds patterns
  - Team names: Usually in `h3`, `span`, or `div` with team classes
  - Timestamps: Look for `time` tags or timestamp attributes

#### Rate Limiting Strategy

- [ ] **Implement delays:**
  - Minimum 2-3 seconds between requests
  - Random jitter: +/- 1 second

- [ ] **Respect crawl-delay:**
  - Check robots.txt for delay guidance
  - Honor site-specific requirements

- [ ] **Limit concurrent requests:**
  - Max 1-2 concurrent browser instances
  - Sequential scraping preferred

#### User-Agent Configuration

- [ ] **Set realistic user-agent:**
  ```javascript
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  ```

- [ ] **Rotate user-agents occasionally:**
  - Keep pool of 3-5 common user-agents
  - Change every 10-20 requests

---

### Step 7: Legal and Ethical Considerations

#### Review Terms of Service

- [ ] **Check each betting site's TOS:**
  - Look for scraping prohibitions
  - Understand account termination risks
  - Note any API alternatives offered

- [ ] **Document findings:**
  - Sites that allow scraping
  - Sites that prohibit scraping
  - Sites with API alternatives

#### Check robots.txt

- [ ] **Review robots.txt for each site:**
  ```bash
  curl https://[betting-site].com/robots.txt
  ```

- [ ] **Honor disallow directives:**
  - Don't scrape disallowed paths
  - Respect crawl-delay settings

- [ ] **Document robots.txt findings**

#### Implement Respectful Scraping

- [ ] **Rate limiting implemented** (2-3 seconds between requests)
- [ ] **User-agent identification** (accurate user-agent string)
- [ ] **Error handling** (don't retry aggressively on errors)
- [ ] **Peak hour avoidance** (scrape during off-peak times)
- [ ] **Data usage** (only scrape what you need)

#### Legal Risk Assessment

- [ ] **Understand legal risks:**
  - Computer Fraud and Abuse Act (CFAA) considerations
  - Terms of Service violations
  - Copyright/database rights
  - State-specific laws

- [ ] **Mitigation strategies:**
  - Use only publicly accessible data
  - Don't bypass authentication
  - Don't circumvent technical protections
  - Consider API alternatives first

---

### Step 8: Scraping Use Cases

#### Live Odds Monitoring

**Use Case:** Scrape current odds every 5-15 minutes

- [ ] **Implementation approach:**
  - Target specific games only
  - Extract odds for ML, spread, total
  - Store in database with timestamp
  - Compare to previous values

- [ ] **Sample query:**
  ```
  "Use Puppeteer to scrape odds for Lakers vs Warriors from [site]"
  ```

#### Arbitrage Detection

**Use Case:** Compare odds across multiple books

- [ ] **Implementation approach:**
  - Scrape same game from 3+ books
  - Compare odds for arbitrage opportunities
  - Alert when >1% arbitrage found

- [ ] **Sample query:**
  ```
  "Scrape Lakers ML odds from DraftKings, FanDuel, and BetMGM"
  ```

#### Line Movement Tracking

**Use Case:** Screenshot odds for historical records

- [ ] **Implementation approach:**
  - Take screenshot every hour
  - Save with timestamp filename
  - Compare visually for movements

- [ ] **Sample query:**
  ```
  "Screenshot the Lakers game odds page and save with timestamp"
  ```

#### Odds Verification

**Use Case:** Verify model predictions against actual odds

- [ ] **Implementation approach:**
  - Scrape pre-game odds
  - Compare to model predictions
  - Calculate difference for calibration

---

### Step 9: Automation (Future Enhancement)

#### Scheduled Scraping Script

```python
# scripts/scrape_odds_puppeteer.py

import schedule
import time
from datetime import datetime

def scrape_todays_games():
    """Scrape odds for today's games"""
    # Get today's games from database
    games = get_todays_games()

    for game in games:
        # Use Puppeteer via MCP to scrape
        # Store odds in database
        pass

    log_scraping_activity(datetime.now())

# Run every 15 minutes during game hours
schedule.every(15).minutes.do(scrape_todays_games)

while True:
    schedule.run_pending()
    time.sleep(60)
```

#### Integration with Alert System

```python
# Add to mcp_server/betting/alert_system.py

def check_arbitrage_opportunities():
    """Check for arbitrage across books"""
    games = get_todays_games()

    for game in games:
        # Scrape odds from multiple books
        odds_book_a = scrape_via_puppeteer(book_a_url)
        odds_book_b = scrape_via_puppeteer(book_b_url)

        # Calculate arbitrage
        arb_pct = calculate_arbitrage(odds_book_a, odds_book_b)

        if arb_pct > 1.0:  # >1% arbitrage
            send_alert(f"Arbitrage: {game} - {arb_pct}%")
```

---

## Troubleshooting

### Chromium Download Fails

**Symptom:** Puppeteer can't download Chromium

**Solution:**
1. Check internet connection
2. Verify disk space available
3. Check firewall/proxy settings
4. Manual Chromium installation if needed
5. Set PUPPETEER_SKIP_CHROMIUM_DOWNLOAD and point to existing Chrome

### Scraping Fails/Timeouts

**Symptom:** Page won't load or times out

**Solution:**
1. Increase timeout (default is usually 30s)
2. Check if site is blocking headless browsers
3. Try with headful mode (set headless: false)
4. Check if site requires JavaScript to render
5. Verify selectors are still correct (sites change layouts)

### Selectors Not Found

**Symptom:** Can't extract data - selectors don't match

**Solution:**
1. Inspect page manually in browser
2. Update selectors to match current layout
3. Use more robust selectors (avoid IDs, prefer data attributes)
4. Check if page structure changed
5. Try alternative selector strategies (XPath, text content)

### Anti-Scraping Detection

**Symptom:** Site blocks or captchas appear

**Solution:**
1. Reduce request frequency
2. Rotate user-agents
3. Add realistic delays and jitter
4. Consider using residential proxies
5. Respect robots.txt and TOS
6. Use API if available

---

## Best Practices

### What TO Scrape

✅ **Public odds displays** (no login required)
✅ **Limited frequency** (every 15+ minutes)
✅ **Specific games only** (not entire site)
✅ **Off-peak hours** (late night preferred)
✅ **Fallback to API** if available

### What NOT to Scrape

❌ **Login-protected content**
❌ **High frequency** (< 5 minutes apart)
❌ **Entire odds boards** (excessive data)
❌ **Peak traffic hours** (avoid impacting site)
❌ **Sites with API alternatives**

---

## Verification Checklist

- [ ] Puppeteer MCP installed
- [ ] Chromium downloaded successfully
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] Puppeteer MCP connects successfully
- [ ] Can navigate to pages
- [ ] Can extract text content
- [ ] Can take screenshots
- [ ] Can extract table data
- [ ] Documented selectors for target sites
- [ ] Rate limiting strategy implemented
- [ ] Legal/ethical considerations reviewed
- [ ] Terms of service checked
- [ ] robots.txt reviewed

---

## Next Steps After Implementation

1. **Test on target sites** - Verify selectors work
2. **Document selectors** - Keep reference of working selectors
3. **Implement rate limiting** - Add delays to respect sites
4. **Build scraping utilities** - Create reusable scraping functions
5. **Monitor for blocks** - Watch for anti-scraping measures
6. **Evaluate ROI** - Determine if scraping adds value vs API cost

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
