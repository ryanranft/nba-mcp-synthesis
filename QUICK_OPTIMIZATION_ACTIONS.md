# Quick Optimization Actions

**Purpose**: One-page reference for immediate token optimization
**Time**: 2-4 hours for quick wins, 31 hours for complete implementation
**Expected Benefit**: 30-40% additional token reduction (2-6K tokens per session)

---

## 🚀 Do These Today (2 hours → 800 tokens saved)

### 1. Archive Completion Documents (15 min)
```bash
cd /Users/ryanranft/nba-mcp-synthesis
./scripts/auto_archive.sh --dry-run      # Preview
./scripts/auto_archive.sh --interactive  # Archive with confirmation
```
**Saves**: ~500 tokens (reduced search space)

---

### 2. Create Remaining Work File (30 min)
```bash
# Extract pending features from PROJECT_MASTER_TRACKER.md
vim project/status/remaining-work.md
```

**Content**:
```markdown
# Remaining Work (16 Features)

## Web Scraping - 3 Tools ❌
- [ ] scrape_nba_webpage
- [ ] search_webpage_for_text
- [ ] extract_structured_data

## MCP Prompts - 7 Templates ❌
- [ ] analyze_player
- [ ] compare_players
- [ ] predict_game
- [ ] team_analysis
- [ ] injury_impact
- [ ] draft_analysis
- [ ] trade_evaluation

## MCP Resources - 6 URIs ❌
- [ ] nba://games/{date}
- [ ] nba://standings/{conference}
- [ ] nba://players/{player_id}
- [ ] nba://teams/{team_id}
- [ ] nba://injuries
- [ ] nba://players/top-scorers
```

**Update PROJECT_STATUS.md**:
```markdown
**Pending Features**: 16 → [Remaining Work](project/status/remaining-work.md)
```

**Saves**: ~100 tokens (smaller status file)

---

### 3. Implement Progress Log Rotation (30 min)
```bash
vim scripts/rotate_progress_log.sh
```

**Content**:
```bash
#!/bin/bash
# Rotate progress log monthly

MONTH=$(date +%Y-%m)
LOG_FILE="project/tracking/progress.log"
ARCHIVE_FILE=".ai/monthly/${MONTH}-progress.log"

if [ -f "$LOG_FILE" ]; then
    # Copy to archive
    cp "$LOG_FILE" "$ARCHIVE_FILE"

    # Keep only last 30 days in active log
    CUTOFF_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d)
    awk -v cutoff="$CUTOFF_DATE" '$0 >= cutoff' "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"

    echo "Progress log rotated. Archive: $ARCHIVE_FILE"
fi
```

```bash
chmod +x scripts/rotate_progress_log.sh
./scripts/rotate_progress_log.sh  # Test run
```

**Saves**: Prevents future bloat (keeps log <100 lines)

---

### 4. Split Tracker - Phase 1 (45 min)
```bash
# Create completion criteria file
vim project/tracking/completion-criteria.md
```

**Content** (extract from PROJECT_MASTER_TRACKER.md lines ~386-413):
```markdown
# Definition of "Done"

A feature is considered complete when ALL of the following are satisfied:

## 1. Implementation ✅
- Helper module created with all functions
- Pydantic parameter models defined
- MCP tool registration in fastmcp_server.py ⭐ **MUST BE REGISTERED**
- Error handling and logging implemented

## 2. Testing ✅
- Unit tests written (100% coverage target)
- All tests passing
- Edge cases covered
- NBA use cases tested

## 3. Documentation ✅
- Tool documentation with parameters/returns
- NBA-specific examples provided
- Integration guide written
- Sprint completion document created

## 4. Integration ✅
- Tool registered in MCP server
- Accessible via Claude Desktop/API
- Works with existing tools
- No breaking changes
```

**Update PROJECT_MASTER_TRACKER.md**:
Replace that section with:
```markdown
See [Completion Criteria](project/tracking/completion-criteria.md) for definition of "Done".
```

**Saves**: ~200 tokens per tracker read

---

## 📅 This Week (11 hours → 1,500 tokens saved)

### Day 1: Split PROJECT_MASTER_TRACKER.md (4 hours)

1. **Create project/tracking/phase-9-status.md** (extract lines ~417-433)
2. **Move historical context to .ai/permanent/historical-context.md** (lines ~527-551)
3. **Convert PROJECT_MASTER_TRACKER.md to index** (reduce from 672 → 150 lines)
4. **Update all references**

### Day 2: Update Cross-References (2 hours)

```bash
vim docs/DOCUMENTATION_MAP.md  # Add new file locations
vim PROJECT_STATUS.md          # Link to new files
./scripts/audit_cross_references.sh  # Verify links
```

### Day 3: Consolidate Context Guides (3 hours)

Merge these 3 files:
- `docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md`
- `docs/guides/CONTEXT_BUDGET_GUIDE.md`
- `docs/guides/CONTEXT_EMERGENCY_PROCEDURES.md`

Into:
- `docs/guides/CONTEXT_MANAGEMENT_COMPLETE.md`

### Day 4: Archive & Test (1 hour)

```bash
# Move old guides to archive
mv docs/guides/CONTEXT_*_GUIDE.md docs/archive/2025-10/guides/

# Update guide index
vim docs/guides/index.md

# Test
./scripts/audit_cross_references.sh
```

### Day 5: Verify Savings (1 hour)

```bash
# Measure token usage
wc -l PROJECT_MASTER_TRACKER.md  # Should be ~150 lines
wc -l docs/guides/*.md            # Should be fewer files

# Check status file
cat PROJECT_STATUS.md             # Should be <110 lines
```

---

## 📈 Next 2 Weeks (22 hours → 2,000+ tokens saved)

### Week 2: Consolidate Guides (11 hours)
- File management guides (2 → 1)
- Claude Desktop guides (5 → 1)
- Create topic-based navigation
- Create comprehensive tool reference

### Week 3: Polish & Automate (9 hours)
- Update all cross-references
- Enhance automation scripts
- Documentation review
- Testing and metrics

---

## 📊 Expected Results

### Token Usage
| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| Session start | 300 | 250 | 50 (17%) |
| Status check | 150 | 75 | 75 (50%) |
| Tool lookup | 100 | 50 | 50 (50%) |
| Tracker read | 1000 | 200 | 800 (80%) |
| **Daily session** | **3-10K** | **2-6K** | **30-40%** |

### File Counts
| Category | Before | After | Reduction |
|----------|--------|-------|-----------|
| Root .md | 11 | 9 | 18% |
| Active docs | 61 | 45 | 26% |
| Guides | 19 | 12-13 | 32-37% |

---

## ✅ Quick Checklist

**Today** (2 hours):
- [ ] Run auto_archive.sh
- [ ] Create remaining-work.md
- [ ] Create rotate_progress_log.sh
- [ ] Split tracker - phase 1
- [ ] Test changes

**This Week** (11 hours):
- [ ] Complete tracker split
- [ ] Update cross-references
- [ ] Consolidate context guides
- [ ] Archive old guides
- [ ] Verify savings

**Next 2 Weeks** (22 hours):
- [ ] Consolidate file management guides
- [ ] Consolidate Claude Desktop guides
- [ ] Create topic navigation
- [ ] Create comprehensive tool reference
- [ ] Final testing and metrics

---

## 🔗 Full Documentation

For detailed implementation:
- **[ORGANIZATION_RECOMMENDATIONS.md](ORGANIZATION_RECOMMENDATIONS.md)** - Complete plan
- **[ORGANIZATION_VISUAL_SUMMARY.md](ORGANIZATION_VISUAL_SUMMARY.md)** - Visual comparison
- **[CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md](CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Operations guide

---

## 💡 Key Principles

1. **Archive completed work** - Use scripts/auto_archive.sh
2. **Split large files** - Keep files <300 lines when possible
3. **Consolidate related content** - Merge overlapping guides
4. **Rotate growing logs** - Prevent unbounded growth
5. **Measure results** - Track token usage improvements

---

**Last Updated**: 2025-10-11
**Status**: Ready to implement
**Time Required**: 2 hours today, 31 hours total for complete optimization

