# Time/Everything MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: GitHub MCP](GITHUB_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [Next: Fetch MCP →](FETCH_MCP_IMPLEMENTATION.md)

---

**Purpose:** Time-aware queries for game schedules, calculate rest days automatically, schedule daily pipelines, timezone conversions.

**Priority:** Medium
**Estimated Time:** 10 minutes
**Credentials Required:** No

---

## Implementation Checklist

### Prerequisites
- [ ] Node.js and npx available (already installed)
- [ ] No credentials required
- [ ] No API keys needed

---

### Step 1: Test Time/Everything MCP Installation

- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-everything --help
  ```

- [ ] Verify command completes without errors

- [ ] Check output shows Time/Everything MCP help/version info

---

### Step 2: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add Time/Everything MCP configuration to `mcpServers` section:
  ```json
  "everything": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {}
  }
  ```

- [ ] Save file

---

### Step 3: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add Time/Everything MCP configuration to `mcpServers` section:
  ```json
  "everything": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"],
    "env": {}
  }
  ```

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same Time/Everything MCP configuration

- [ ] Save file

---

### Step 4: Test Time/Everything MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "everything" appears in connected MCPs list

#### Test Time Queries

- [ ] **Current time in game location:**
  - Ask Claude: "What time is it in Los Angeles?"
  - Verify it returns accurate Pacific time

- [ ] **Timezone conversion:**
  - Ask Claude: "Convert 7:30 PM EST to PST"
  - Verify correct conversion (4:30 PM PST)

- [ ] **Date calculations:**
  - Ask Claude: "How many days until next Monday?"
  - Verify accurate calculation

- [ ] **Day of week:**
  - Ask Claude: "What day of week is 3 days from now?"
  - Verify correct day

---

### Step 5: Test NBA-Specific Time Queries

#### Game Time Queries

- [ ] **Game time in your timezone:**
  - Ask Claude: "Lakers play at 10:30 PM EST tonight, what time is that in my timezone?"
  - Verify correct conversion

- [ ] **Multi-timezone game start:**
  - Ask Claude: "If a game starts at 7 PM Pacific, what time is that in Mountain, Central, and Eastern?"
  - Verify all conversions correct

#### Rest Day Calculations

- [ ] **Days between games:**
  - Ask Claude: "If Lakers played on November 10 and play again on November 14, how many rest days?"
  - Verify correct calculation (3 days between = 2 rest days)

- [ ] **Back-to-back games:**
  - Ask Claude: "Is November 12 to November 13 a back-to-back?"
  - Verify it identifies as back-to-back (0 rest days)

#### Schedule Planning

- [ ] **Pipeline scheduling:**
  - Ask Claude: "If I run daily pipeline at 2 AM EST, what time is that Pacific?"
  - Verify correct conversion (11 PM PST previous day)

- [ ] **Betting window:**
  - Ask Claude: "Game starts at 8 PM EST, I need 2 hours before for analysis. What's my deadline in Central time?"
  - Verify correct calculation (5 PM CT)

---

### Step 6: Integration with Betting Workflow

#### Pre-Game Time Validation

Add to `daily_betting_analysis.py`:

```python
# Validate game times and calculate deadlines
for game in today_games:
    game_time_est = game['start_time']  # e.g., "2024-11-12 20:00:00 EST"

    # Ask Claude via MCP:
    # "Convert {game_time_est} to my local timezone"
    local_time = get_local_time_via_mcp(game_time_est)

    # Ask Claude:
    # "Calculate time 2 hours before {local_time}"
    analysis_deadline = calculate_deadline_via_mcp(local_time, hours=2)

    print(f"Game: {game['matchup']}")
    print(f"Start: {local_time}")
    print(f"Analysis deadline: {analysis_deadline}")
```

#### Rest Day Feature Engineering

Add to `prepare_game_features.py`:

```python
def calculate_rest_days(team, last_game_date, current_game_date):
    """Calculate rest days between games"""

    # Ask Claude via MCP:
    # "How many days between {last_game_date} and {current_game_date}?"
    days_between = get_days_between_via_mcp(last_game_date, current_game_date)

    rest_days = days_between - 1  # Days between games

    return rest_days

# Add rest_days feature to model
features['rest_days_home'] = calculate_rest_days(home_team, last_game, current_game)
features['rest_days_away'] = calculate_rest_days(away_team, last_game, current_game)
```

#### Schedule Pipeline Runs

Add to `scripts/schedule_daily_tasks.sh`:

```bash
#!/bin/bash

# Ask Claude via MCP:
# "If games typically start at 7 PM EST, what's the optimal time to run
# data sync to have fresh data 4 hours before first game?"

# Claude calculates: 3 PM EST = 12 PM PST

# Schedule cron job accordingly
# 0 15 * * * /path/to/daily_data_sync.py  # 3 PM EST
```

#### Timezone-Aware Betting Windows

Add to `paper_trade_today.py`:

```python
def check_betting_window(game):
    """Check if we're within betting window"""

    game_start = game['start_time_utc']

    # Ask Claude via MCP:
    # "How many hours until {game_start} from now?"
    hours_until_game = get_hours_until_via_mcp(game_start)

    # Betting rules:
    # - Need 2 hours before game for analysis
    # - No betting within 30 minutes of game start

    if hours_until_game < 0.5:
        return False, "Too close to game start"
    elif hours_until_game > 24:
        return False, "Too far from game start"
    else:
        return True, f"{hours_until_game:.1f} hours until game"
```

---

### Step 7: Common Time Queries for NBA Betting

#### Timezone Conversions

```
"Convert 7:30 PM EST to PST"  # Lakers game time
"Convert 8:00 PM MST to EST"  # Nuggets game time
"Convert 6:30 PM CST to EST"  # Mavericks game time
```

#### Rest Day Calculations

```
"How many days between November 10 and November 14?"  # For rest days
"Is December 25 to December 26 a back-to-back?"  # Christmas games
"Calculate rest days: last game Nov 8, next game Nov 12"  # 3 days between = 2 rest days
```

#### Schedule Planning

```
"If I need results by 6 PM EST, what time should I start a 4-hour process?"  # 2 PM EST
"Game at 10 PM EST, I need 3 hours prep. Deadline in PST?"  # 4 PM PST
"Daily sync at 3 AM PST. What time is that EST?"  # 6 AM EST
```

#### Relative Time

```
"What day is 3 days from now?"  # For future game dates
"How many hours until 8 PM EST tomorrow?"  # For countdown timers
"Is today a game day?"  # Based on schedule
```

---

## Troubleshooting

### Incorrect Timezone Conversions

**Symptom:** Time conversions are off by an hour

**Solution:**
1. Check if Daylight Saving Time is in effect
2. Verify timezone abbreviations (EST vs EDT)
3. Use full timezone names (America/New_York vs EST)
4. Consider using UTC for consistency

### Date Calculation Errors

**Symptom:** Rest day calculations don't match expected

**Solution:**
1. Verify date format is consistent
2. Check if counting days between vs days apart
3. Remember: 2 days between = 1 rest day
4. Account for timezone differences (game times may span midnight)

### Connection Issues

**Symptom:** Time/Everything MCP not connecting

**Solution:**
1. Test npx installation:
   ```bash
   npx -y @modelcontextprotocol/server-everything --help
   ```
2. Verify internet connection
3. Restart Claude app completely
4. Check Claude logs for errors

---

## Best Practices

### Use Cases for Time/Everything MCP

✅ **Timezone conversions** (game times across timezones)
✅ **Rest day calculations** (feature engineering)
✅ **Schedule planning** (pipeline runs, deadlines)
✅ **Relative time queries** ("how many days until...")
✅ **Time arithmetic** (adding/subtracting hours/days)

### When NOT to Use

❌ **Simple current time** (use Python `datetime.now()`)
❌ **Known timezone conversions** (use `pytz` directly)
❌ **High-frequency calculations** (cache results instead)
❌ **Historical date parsing** (use date parsing libraries)

### Optimization Tips

1. **Cache common conversions:**
   - "7:30 PM EST to PST" → Store result
   - "8:00 PM MST to EST" → Store result

2. **Batch queries:**
   - Convert multiple game times in one query
   - Calculate rest days for all teams at once

3. **Use UTC for storage:**
   - Store all times in UTC in database
   - Convert to local timezone only for display

---

## Verification Checklist

- [ ] Time/Everything MCP installed successfully
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] Time/Everything MCP connects successfully
- [ ] Can query current time in different timezones
- [ ] Can convert game times (EST/PST/MST/CST)
- [ ] Can calculate rest days between games
- [ ] Can perform relative time queries
- [ ] Integration with betting workflow documented
- [ ] Common queries documented

---

## Next Steps After Implementation

1. **Create query templates** - Standardize common time queries
2. **Build helper functions** - Wrap MCP calls in Python functions
3. **Integrate with features** - Add rest days to model
4. **Schedule pipelines** - Use timezone-aware scheduling
5. **Test with real games** - Verify timezone conversions for tonight's games

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
