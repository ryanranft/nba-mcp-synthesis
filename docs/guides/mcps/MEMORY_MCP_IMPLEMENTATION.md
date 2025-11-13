# Memory MCP Implementation Guide
## NBA MCP Synthesis Project

[← Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [📊 Progress Tracker](README.md) | [Next: AWS Knowledge MCP →](AWS_KNOWLEDGE_MCP_IMPLEMENTATION.md)

---

**Purpose:** Remember betting strategies that worked/failed, track model performance insights across sessions, store team patterns and betting edge observations.

**Priority:** High (critical for learning over time)
**Estimated Time:** 10 minutes
**Credentials Required:** No

---

## Implementation Checklist

### Prerequisites
- [ ] Node.js and npx available (already installed)
- [ ] No credentials required
- [ ] No API keys needed

---

### Step 1: Test Memory MCP Installation

- [ ] Run test command:
  ```bash
  npx -y @modelcontextprotocol/server-memory --help
  ```

- [ ] Verify command completes without errors

- [ ] Check output shows Memory MCP help/version info

---

### Step 2: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add Memory MCP configuration to `mcpServers` section:
  ```json
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
  ```

- [ ] Save file

---

### Step 3: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add Memory MCP configuration to `mcpServers` section:
  ```json
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
  ```

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same Memory MCP configuration

- [ ] Save file

---

### Step 4: Test Memory MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "memory" appears in connected MCPs list

#### Test Memory Storage

- [ ] **Store betting insight:**
  - Ask Claude: "Remember: Lakers tend to exceed expected win probability when playing back-to-back home games"
  - Verify Claude confirms storage

- [ ] **Store model observation:**
  - Ask Claude: "Remember: Model consistently underestimates underdogs with +7.5 spread or greater"
  - Verify storage confirmed

- [ ] **Store team pattern:**
  - Ask Claude: "Remember: Warriors shooting percentage drops 3% in altitude above 5000 feet"
  - Verify storage confirmed

---

### Step 5: Test Memory Retrieval

- [ ] **Query Lakers patterns:**
  - Ask Claude: "What patterns have we observed about Lakers?"
  - Verify it recalls the back-to-back home games insight

- [ ] **Query spread betting:**
  - Ask Claude: "What spread betting insights do we have?"
  - Verify it recalls the +7.5 underdog pattern

- [ ] **Query Warriors:**
  - Ask Claude: "Tell me what we know about Warriors shooting"
  - Verify it recalls the altitude observation

- [ ] **General query:**
  - Ask Claude: "What betting patterns should I be aware of?"
  - Verify it summarizes stored insights

---

### Step 6: Define Memory Categories

Create a mental framework (or document) for what to store in memory:

#### Betting Strategy Learnings
- [ ] Strategies that consistently win
- [ ] Strategies that consistently fail
- [ ] Edge decay patterns
- [ ] Arbitrage opportunities discovered
- [ ] Kelly criterion adjustments that worked

#### Model Performance Patterns
- [ ] Systematic under/over predictions
- [ ] Feature importance discoveries
- [ ] Calibration drift observations
- [ ] Prediction accuracy by bet type
- [ ] Time-of-season performance changes

#### Team-Specific Observations
- [ ] Home/away performance patterns
- [ ] Rest day impacts
- [ ] Lineup change effects
- [ ] Altitude/travel impacts
- [ ] Coaching tendency patterns

#### Line Movement Insights
- [ ] Sharp money indicators
- [ ] Public betting patterns
- [ ] Line movement timing
- [ ] Reverse line movement triggers
- [ ] Steam move observations

#### Feature Importance Discoveries
- [ ] Features that predict better than expected
- [ ] Features that became less predictive
- [ ] Feature interactions discovered
- [ ] Data quality insights
- [ ] Feature engineering ideas that worked

#### Failed Approaches to Avoid
- [ ] Strategies that seemed promising but failed
- [ ] Data sources that were unreliable
- [ ] Feature combinations that didn't work
- [ ] Model architectures that underperformed
- [ ] Betting systems that lost money

---

### Step 7: Integration with Betting Workflow

#### Manual Memory Updates (Start Here)

After each betting session:

- [ ] **High-confidence wins:**
  ```
  "Remember: [Date] - 15% edge bet on Lakers ML won. Key factors: rest advantage, home game, opponent on back-to-back"
  ```

- [ ] **Unexpected losses:**
  ```
  "Remember: [Date] - 12% edge bet on Warriors spread lost. Model missed: key player ruled out 1 hour before game"
  ```

- [ ] **Pattern discoveries:**
  ```
  "Remember: Discovered pattern - Teams coming off 3+ game road trip underperform spread by 2 points on average"
  ```

#### Automated Memory Logging (Future Enhancement)

- [ ] Add to `paper_trade_today.py`:
  ```python
  # After high-confidence bet closes:
  if edge > 10% and outcome_known:
      memory_msg = f"Remember: {date} - {edge}% edge bet on {team} {bet_type}"
      memory_msg += f" {'won' if won else 'lost'}. Key factors: {factors}"
      # Log to memory via MCP
  ```

- [ ] Add to `daily_betting_analysis.py`:
  ```python
  # After analyzing day's results:
  if new_pattern_discovered:
      memory_msg = f"Remember: Discovered pattern - {pattern_description}"
      # Log to memory via MCP
  ```

- [ ] Add to `train_game_outcome_model.py`:
  ```python
  # After model training:
  if significant_feature_change:
      memory_msg = f"Remember: Feature importance shift - {feature_name} importance changed from {old} to {new}"
      # Log to memory via MCP
  ```

#### Weekly Memory Review

- [ ] Every Monday, ask Claude:
  - "Summarize all betting insights from last week"
  - "What patterns did we discover last week?"
  - "What failed strategies should we avoid?"

- [ ] Document findings in weekly report

---

## Example Memory Entries

### Good Betting Insights to Store

```
"Remember: Lakers at home on 2+ days rest beat spread 68% of time (sample size: 45 games)"

"Remember: Model overestimates home underdogs by average 2.1 points when spread is +10 or higher"

"Remember: Line movements of 2+ points within 2 hours of game time correctly predict outcome 73% of time"

"Remember: 76ers performance drops 12% when Embiid sits - model only adjusts 8%, creating betting edge"

"Remember: Back-to-back road games in different time zones: teams underperform by 3.2 points on average"
```

### Model Performance to Store

```
"Remember: Calibration curve shows overconfidence in 65-75% probability range - apply 0.92 adjustment factor"

"Remember: Feature 'rest_days_opponent' became 2x more predictive after All-Star break in 2024 season"

"Remember: Ensemble model outperforms single models by 4.2% ROI when player props are included"

"Remember: Model accuracy drops 8% in first 2 weeks of season - avoid betting during this period"
```

### Failed Strategies to Remember

```
"Remember: AVOID - Betting all games with 5-8% edge resulted in -2.3% ROI (sample: 150 bets, Q1 2024)"

"Remember: AVOID - Lineup prediction from Twitter/social media had 34% false positive rate"

"Remember: AVOID - Weather data for indoor games added no predictive value, increased noise"

"Remember: AVOID - Betting against public heavy favorites (>75% bets) only worked 48% of time"
```

---

## Troubleshooting

### Memory Not Persisting

**Symptom:** Stored memories don't recall in new sessions

**Solution:**
1. Memory MCP stores data locally in its database
2. Check if Claude app has file system permissions
3. Verify Memory MCP is connecting on each restart
4. Check for multiple Claude instances (memory stored in one, queried in another)

### Memory Retrieval Issues

**Symptom:** Claude doesn't recall stored information

**Solution:**
1. Be specific in queries (use keywords from stored memories)
2. Try: "Search your memory for [keyword]"
3. Memory may need semantic similarity - rephrase query
4. Check if memory was actually stored (ask Claude to confirm)

### Memory Limit Reached

**Symptom:** Warning about memory storage limits

**Solution:**
1. Periodically review and remove outdated memories
2. Consolidate similar memories into summaries
3. Focus on high-value insights only
4. Consider exporting memories to external document

---

## Best Practices

### What TO Store

✅ **High-value patterns** (statistical significance)
✅ **Repeated observations** (seen 3+ times)
✅ **Counterintuitive findings** (surprise discoveries)
✅ **Failed strategies** (to avoid repeating)
✅ **Model performance shifts** (calibration changes)
✅ **Team-specific edges** (persistent advantages)

### What NOT to Store

❌ **One-off results** (single game outcomes)
❌ **Obvious information** (common knowledge)
❌ **Temporary events** (short-term injuries)
❌ **Unverified hunches** (no statistical backing)
❌ **Duplicate information** (already stored)
❌ **Low-value details** (minor observations)

### Memory Organization Tips

1. **Use consistent prefixes:**
   - "PATTERN:" for discovered patterns
   - "MODEL:" for model performance
   - "AVOID:" for failed strategies
   - "TEAM:" for team-specific insights

2. **Include dates and sample sizes:**
   - "Lakers pattern (verified 2024-11-01, n=45 games)"
   - "Model calibration drift detected 2024-11-12"

3. **Be specific and actionable:**
   - Good: "Lakers home games after 2+ rest days: +5.2 pts vs spread (n=45, p<0.05)"
   - Bad: "Lakers play better at home"

4. **Update memories when new data emerges:**
   - "UPDATE: Lakers home rest pattern now n=60 games, +4.8 pts vs spread"

---

## Verification Checklist

- [ ] Memory MCP installed successfully
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] Memory MCP connects successfully
- [ ] Can store memories
- [ ] Can retrieve memories
- [ ] Defined memory categories
- [ ] Created memory organization system
- [ ] Documented integration plan
- [ ] Tested with real betting insights

---

## Next Steps After Implementation

1. **Start storing insights immediately** - Begin with 5-10 key patterns
2. **Review weekly** - Summarize and consolidate memories
3. **Integrate with workflows** - Add memory logging to scripts
4. **Export important memories** - Backup to markdown document monthly
5. **Build memory index** - Create searchable index of key insights

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
