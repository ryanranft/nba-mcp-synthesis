# Fetch MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: Time/Everything MCP](TIME_EVERYTHING_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [Next: Puppeteer MCP →](PUPPETEER_MCP_IMPLEMENTATION.md)

---

**Purpose:** Hit external betting odds APIs, fetch real-time NBA data, integration testing for APIs, webhook testing.

**Priority:** Medium
**Estimated Time:** 10 minutes
**Credentials Required:** No (credentials passed per-request)

---

## Implementation Checklist

### Prerequisites
- [ ] Node.js and npx available (already installed)
- [ ] No credentials required (passed per-request in headers)
- [ ] API endpoints to test with

---

### Step 1: Test Fetch MCP Installation

- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-fetch --help
  ```

- [ ] Verify command completes without errors

- [ ] Check output shows Fetch MCP help/version info

---

### Step 2: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add Fetch MCP configuration to `mcpServers` section:
  ```json
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "env": {}
  }
  ```

- [ ] Save file

---

### Step 3: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add Fetch MCP configuration to `mcpServers` section:
  ```json
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "env": {}
  }
  ```

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same Fetch MCP configuration

- [ ] Save file

---

### Step 4: Test Fetch MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "fetch" appears in connected MCPs list

#### Test Basic GET Request

- [ ] **Fetch public NBA API:**
  - Ask Claude: "Use fetch to GET https://www.balldontlie.io/api/v1/games?per_page=5"
  - Verify it returns game data

- [ ] **Check response structure:**
  - Verify JSON response is parsed correctly
  - Check status code (should be 200)
  - Verify response headers present

---

### Step 5: Test API Calls with Authentication

#### Test with API Key in Header

- [ ] **NBA Stats API (example):**
  ```
  "Use fetch to GET https://api.example.com/nba/games with header Authorization: Bearer YOUR_API_KEY"
  ```

- [ ] Verify authentication works

- [ ] Check response contains authenticated data

#### Test with Query Parameters

- [ ] **API with query params:**
  ```
  "Use fetch to GET https://api.example.com/games?date=2024-11-12&team=Lakers"
  ```

- [ ] Verify query parameters are encoded correctly

- [ ] Check response filters data correctly

---

### Step 6: Test POST Requests

#### Test Webhook

- [ ] **POST to webhook endpoint:**
  ```
  "Use fetch to POST to https://webhook.site/YOUR-UNIQUE-URL with JSON body {\"event\": \"test\", \"data\": \"NBA betting alert\"}"
  ```

- [ ] Verify POST request succeeds

- [ ] Check webhook receives data

#### Test API Write Operation

- [ ] **POST to create resource:**
  ```
  "Use fetch to POST to https://api.example.com/predictions with JSON body {\"game_id\": 123, \"prediction\": \"LAL win\", \"confidence\": 0.72}"
  ```

- [ ] Verify resource created

- [ ] Check response contains created object

---

### Step 7: Document Common API Endpoints

#### NBA Stats APIs

- [ ] **BallDontLie API** (free, no auth):
  ```
  GET https://www.balldontlie.io/api/v1/games
  GET https://www.balldontlie.io/api/v1/players
  GET https://www.balldontlie.io/api/v1/stats
  ```

- [ ] **NBA Official API** (if accessible):
  ```
  GET https://stats.nba.com/stats/scoreboardV2?GameDate=2024-11-12&LeagueID=00
  ```

#### Odds API Providers

- [ ] **The Odds API** (requires API key):
  ```
  GET https://api.the-odds-api.com/v4/sports/basketball_nba/odds
  Headers: X-Api-Key: YOUR_KEY
  ```

- [ ] **Odds Shark** (if API available):
  ```
  GET https://api.oddsshark.com/v1/nba/odds
  ```

#### Weather APIs (if needed)

- [ ] **OpenWeather API** (requires API key):
  ```
  GET https://api.openweathermap.org/data/2.5/weather?q=LosAngeles&appid=YOUR_KEY
  ```

#### News APIs

- [ ] **NewsAPI** (requires API key):
  ```
  GET https://newsapi.org/v2/everything?q=NBA+Lakers&apiKey=YOUR_KEY
  ```

---

### Step 8: Integration with Betting Workflow

#### Real-Time Odds Fetching

Add to `daily_betting_analysis.py`:

```python
def fetch_live_odds(game_id):
    """Fetch live odds via Fetch MCP"""

    # Ask Claude via MCP:
    # "Use fetch to GET https://api.the-odds-api.com/v4/sports/basketball_nba/events/{game_id}/odds
    #  with header X-Api-Key: {API_KEY}"

    odds_data = fetch_via_mcp(f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{game_id}/odds",
                              headers={"X-Api-Key": API_KEY})

    return parse_odds(odds_data)
```

#### API Health Checks

Add to `scripts/monitor_apis.py`:

```python
def check_api_health():
    """Monitor API endpoint health"""

    endpoints = [
        "https://www.balldontlie.io/api/v1/games",
        "https://api.the-odds-api.com/v4/sports",
        # ... more endpoints
    ]

    for endpoint in endpoints:
        try:
            # Ask Claude via MCP:
            # "Use fetch to GET {endpoint}"
            response = fetch_via_mcp(endpoint)

            if response.status_code == 200:
                log_health(endpoint, "healthy")
            else:
                alert_unhealthy(endpoint, response.status_code)

        except Exception as e:
            alert_error(endpoint, str(e))
```

#### Webhook Testing

Add to `scripts/test_notifications.py`:

```python
def test_sms_webhook():
    """Test SMS notification webhook"""

    test_payload = {
        "event": "high_confidence_bet",
        "game": "Lakers vs Warriors",
        "edge": 12.5,
        "bet_type": "ML"
    }

    # Ask Claude via MCP:
    # "Use fetch to POST to {WEBHOOK_URL} with JSON body {test_payload}"
    response = fetch_post_via_mcp(WEBHOOK_URL, json=test_payload)

    if response.status_code == 200:
        print("✅ Webhook test successful")
    else:
        print(f"❌ Webhook test failed: {response.status_code}")
```

#### Integration Testing

Add to `tests/integration/test_external_apis.py`:

```python
def test_odds_api_integration():
    """Test integration with odds API"""

    # Fetch test data via MCP
    # "Use fetch to GET {ODDS_API_URL}/test"
    response = fetch_via_mcp(f"{ODDS_API_URL}/test")

    assert response.status_code == 200
    assert 'data' in response.json()

def test_nba_stats_api():
    """Test NBA stats API integration"""

    # Fetch recent games via MCP
    response = fetch_via_mcp("https://www.balldontlie.io/api/v1/games?per_page=5")

    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert len(data['data']) == 5
```

---

## Common Use Cases

### 1. Fetch Live Odds

```
"Use fetch to GET https://api.the-odds-api.com/v4/sports/basketball_nba/odds
 with header X-Api-Key: sk-abc123...
 and parse the moneyline odds for Lakers vs Warriors"
```

### 2. Test Webhook Delivery

```
"Use fetch to POST to https://webhook.site/unique-url-here
 with JSON body {\"alert\": \"12% edge on LAL ML\", \"timestamp\": \"2024-11-12T20:00:00Z\"}
 and show me the response"
```

### 3. Validate API Credentials

```
"Use fetch to GET https://api.example.com/auth/verify
 with header Authorization: Bearer my-token-here
 and check if authentication is successful"
```

### 4. Fetch Game Schedule

```
"Use fetch to GET https://www.balldontlie.io/api/v1/games?dates[]=2024-11-12
 and extract all matchups for today"
```

### 5. Monitor API Rate Limits

```
"Use fetch to GET https://api.the-odds-api.com/v4/sports
 with header X-Api-Key: my-key
 and check the X-RateLimit-Remaining header"
```

---

## Troubleshooting

### CORS Errors

**Symptom:** "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution:**
- Fetch MCP runs server-side, so CORS usually not an issue
- If error persists, API may be blocking server requests
- Try adding Origin header or User-Agent
- Contact API provider if consistently blocked

### Authentication Failures

**Symptom:** 401 Unauthorized or 403 Forbidden

**Solution:**
1. Verify API key is correct (no extra spaces)
2. Check header format (Authorization: Bearer vs X-Api-Key)
3. Verify API key has required permissions
4. Check if API key is expired
5. Review API documentation for auth requirements

### Rate Limiting

**Symptom:** 429 Too Many Requests

**Solution:**
1. Check rate limit headers in response
2. Implement exponential backoff
3. Reduce request frequency
4. Upgrade API tier if needed
5. Cache responses to reduce requests

### Connection Timeouts

**Symptom:** Request times out with no response

**Solution:**
1. Check API endpoint is correct
2. Verify internet connection
3. Try increasing timeout (if Fetch MCP supports it)
4. Check if API is down (use status page)
5. Try alternative endpoint/region

---

## Best Practices

### When to Use Fetch MCP

✅ **API integration testing** - Verify endpoints work
✅ **Webhook testing** - Test notification delivery
✅ **Quick API exploration** - Try endpoints without writing code
✅ **Error debugging** - Isolate API issues
✅ **One-off requests** - Manual data fetching

### When to Use Direct API Calls (boto3/requests)

❌ **Production workflows** - Use robust error handling
❌ **High-frequency requests** - Optimize with connection pooling
❌ **Complex auth** - OAuth flows, token refresh
❌ **Large data transfers** - Streaming, pagination
❌ **Rate limit management** - Custom retry logic

### Security Tips

1. **Never log API keys** in requests/responses
2. **Use environment variables** for sensitive data
3. **Rotate API keys regularly** (every 6 months)
4. **Monitor for unauthorized usage** (check API dashboards)
5. **Use read-only keys** when possible

---

## Verification Checklist

- [ ] Fetch MCP installed successfully
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] Fetch MCP connects successfully
- [ ] Can perform GET requests
- [ ] Can perform POST requests
- [ ] Can add authentication headers
- [ ] Can handle JSON responses
- [ ] Documented common API endpoints
- [ ] Integration examples created
- [ ] Webhook testing working

---

## Next Steps After Implementation

1. **Document all API endpoints** - Create API inventory
2. **Test authentication** - Verify all API keys work
3. **Build integration tests** - Automate API validation
4. **Monitor API health** - Setup monitoring dashboard
5. **Create API wrappers** - Build Python functions around common calls

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
