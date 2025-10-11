# Context Budget Guide

**Purpose**: Comprehensive guide to managing context token budgets
**Last Updated**: 2025-10-11
**Status**: Active operational guide

---

## 🎯 Overview

Context budget management ensures AI sessions stay within optimal token limits by:
1. Defining token budgets for different operation types
2. Tracking actual usage against budgets
3. Providing alerts when budgets are exceeded
4. Offering optimization strategies

**Goal**: Maintain 3-10K tokens per session (vs 30-50K before optimization)

---

## 📊 Budget Allocation

### Core Operations

| Operation | Token Budget | File/Source | Target |
|-----------|--------------|-------------|---------|
| **Session Start** | 300 | `.ai/current-session.md` | <80 lines |
| **Status Check** | 150 | `PROJECT_STATUS.md` | <8 lines |
| **Tool Lookup** | 100 | `.ai/permanent/tool-registry.md` | grep search |
| **Progress Update** | 10 | `project/tracking/progress.log` | append only |
| **Status Update** | 50 | `project/status/*.md` | edit section |
| **Decision Recording** | 30 | `project/tracking/decisions.md` | append only |

**Subtotal**: 640 tokens for core operations

### Extended Operations

| Operation | Token Budget | File/Source | When Needed |
|-----------|--------------|-------------|-------------|
| **Read Guide** | 300 | `docs/guides/*.md` | Learning/reference |
| **Read Plan** | 500 | `docs/plans/*.md` | Planning phase |
| **Review Sprint** | 200 | `docs/sprints/*.md` | Sprint review |
| **Check Analysis** | 250 | `docs/analysis/*.md` | Research phase |
| **Tool Implementation** | 400 | `mcp_server/tools/*.py` | Development |

### Session Budget Targets

| Session Type | Token Budget | Description |
|--------------|--------------|-------------|
| **Quick Update** | 500-1K | Status update, simple fix |
| **Standard Session** | 3-5K | Feature work, debugging |
| **Deep Work** | 5-10K | Complex implementation, planning |
| **Planning Session** | 2-4K | Strategy, architecture decisions |
| **Review Session** | 1-3K | Code review, testing |

---

## 💰 Token Estimation

### Quick Estimation Formula

```
Tokens ≈ Lines × 20
```

**Examples**:
- 50-line file ≈ 1,000 tokens
- 100-line file ≈ 2,000 tokens
- 150-line file ≈ 3,000 tokens

### Accurate Calculation

For more accurate estimation:
```bash
# Word count method
cat file.md | wc -w
# Tokens ≈ Words × 1.3

# Character count method
cat file.md | wc -c
# Tokens ≈ Characters / 4
```

---

## 📈 Budget Tracking

### Daily Tracking

```bash
# Check current session budget
./scripts/context_dashboard.sh

# View detailed breakdown
./scripts/track_context_budget.sh --session

# Export for analysis
./scripts/context_dashboard.sh --export=daily_metrics.json
```

### Weekly Review

```bash
# Run weekly health check
./scripts/weekly_health_check.sh

# Review baseline trends
cat .ai/monitoring/baselines.json | jq .

# Compare week over week
./scripts/track_context_budget.sh --weekly-report
```

### Monthly Analysis

```bash
# Update baselines
./scripts/establish_baselines.sh --force

# Generate monthly report
./scripts/track_context_budget.sh --monthly-report

# Export historical data
./scripts/track_context_budget.sh --export-history
```

---

## 🚨 Budget Alerts

### Warning Levels

**Green** (0-80% of budget):
- Normal operations
- No action needed

**Yellow** (80-100% of budget):
- Approaching budget limit
- Consider optimization
- Review next operation carefully

**Red** (>100% of budget):
- Budget exceeded
- Immediate optimization needed
- Review session strategy

### Alert Triggers

1. **Session Start >300 tokens**
   - Trigger: current-session.md >80 lines
   - Action: Regenerate with less detail

2. **Status Check >150 tokens**
   - Trigger: PROJECT_STATUS.md >8 lines
   - Action: Split into focused files

3. **File Read >500 tokens**
   - Trigger: Reading full file instead of section
   - Action: Use grep or edit specific lines

4. **Overall Session >10K tokens**
   - Trigger: Cumulative operations exceed limit
   - Action: Archive session, start fresh

---

## 🎯 Optimization Strategies

### Strategy 1: Index-Based Navigation

**Problem**: Reading multiple files to find information (2-5K tokens)

**Solution**: Use index files to locate exact content
```bash
# Bad: Read 5 files (5K tokens)
cat docs/guides/guide1.md
cat docs/guides/guide2.md
cat docs/guides/guide3.md
...

# Good: Use index (100 tokens)
cat docs/guides/index.md
# Then read only the specific file needed
cat docs/guides/guide2.md
```

**Savings**: 90-95%

---

### Strategy 2: Grep Before Read

**Problem**: Reading entire file when only need specific section (1K tokens)

**Solution**: Use grep to locate content first
```bash
# Bad: Read entire file
cat mcp_server/tools/database_tools.py  # 1000 tokens

# Good: Grep then read specific section
grep -n "query_database" mcp_server/tools/database_tools.py
# Returns: 45:def query_database(...)
vim mcp_server/tools/database_tools.py +45  # 100 tokens
```

**Savings**: 90%

---

### Strategy 3: Append-Only Logs

**Problem**: Reading progress log before appending (1.5K tokens)

**Solution**: Never read, only append
```bash
# Bad: Read then append
cat project/tracking/progress.log  # 1500 tokens
echo "Update" >> project/tracking/progress.log

# Good: Just append
echo "$(date +%Y-%m-%d): Update" >> project/tracking/progress.log  # 10 tokens
```

**Savings**: 99%

---

### Strategy 4: Section-Based Editing

**Problem**: Reading entire tracker to update one section (1K tokens)

**Solution**: Edit only the specific section
```bash
# Bad: Read full file
cat PROJECT_MASTER_TRACKER.md  # 1000 tokens

# Good: Use index to find section
grep -n "Tool Registration" project/index.md
# Returns: "See project/status/tools.md:45-67"
vim project/status/tools.md +45  # 50 tokens
```

**Savings**: 95%

---

### Strategy 5: Cross-Reference Instead of Duplicate

**Problem**: Repeating information in multiple files (3K tokens)

**Solution**: Link to canonical source
```bash
# Bad: Full content repeated 5 times (5K tokens total)
# File 1, 2, 3, 4, 5: Full tool registration process

# Good: Brief reference (500 tokens total)
# Files 1-4: "See [Tool Registration](project/status/tools.md) for details"
# File 5 (canonical): Full tool registration process
```

**Savings**: 90%

---

### Strategy 6: Template Usage

**Problem**: Creating similar files from scratch (500 tokens each)

**Solution**: Use templates
```bash
# Create from template (50 tokens)
cp .ai/daily/template.md .ai/daily/2025-10-11-session-1.md
vim .ai/daily/2025-10-11-session-1.md  # Fill in specifics
```

**Savings**: 90%

---

### Strategy 7: Proactive File Management

**Problem**: Cluttered workspace with many large files (10-20K extra tokens per session)

**Solution**: Regular archiving and proper file organization

#### Impact Analysis

| File Management Practice | Token Impact | Example |
|-------------------------|--------------|---------|
| **Completion docs in root** | +500-1,500 per file | `SPRINT_5_COMPLETE.md` (500 lines) |
| **Reading append-only logs** | +1,500 per read | `progress.log` (unnecessary context) |
| **Duplicate content** | +2,000-5,000 | Same info in 5 files instead of linking |
| **No archiving (30 days)** | +10,000-20,000 | Accumulation of completed work |
| **Editing auto-generated files** | +3,000 | Manual edits break optimization |

#### Correct Approach

**Do This** ✅:
```bash
# Archive completion documents immediately
./scripts/auto_archive.sh --interactive

# Check for archival candidates
./scripts/session_start.sh --health-check

# Use scripts for auto-generated files
./scripts/session_start.sh  # Regenerates current-session.md

# Follow decision tree before creating files
# See: docs/guides/FILE_CREATION_DECISION_TREE.md

# Weekly archive check
./scripts/weekly_health_check.sh
```

**Don't Do This** ❌:
```bash
# Manually edit auto-generated files
vim .ai/current-session.md  # WRONG - use script instead

# Read append-only logs
cat project/tracking/progress.log  # WRONG - just append

# Create standalone status files
vim STATUS_UPDATE_2025-10-11.md  # WRONG - use canonical location

# Leave completion documents in root
# (accumulates 5-10 files = 5,000-10,000 tokens)
```

#### Token Savings from Proper File Management

| Practice | Before | After | Savings |
|----------|--------|-------|---------|
| Archive old docs (weekly) | 10,000 | 0 | 10,000 (100%) |
| Use scripts for session start | 5,000 | 300 | 4,700 (94%) |
| Never read append-only logs | 1,500 | 10 | 1,490 (99%) |
| Cross-reference vs duplicate | 5,000 | 500 | 4,500 (90%) |
| Follow decision tree | 2,000 | 200 | 1,800 (90%) |
| **Total Session Impact** | **23,500** | **1,010** | **21,490 (91%)** |

#### File Management Rules

1. **Check decision tree first**: [FILE_CREATION_DECISION_TREE.md](FILE_CREATION_DECISION_TREE.md)
2. **Use scripts when available**: `session_start.sh`, `auto_archive.sh`
3. **Archive regularly**: Weekly or when >15 files in root
4. **Never edit auto-generated**: Use regeneration scripts
5. **Cross-reference, don't duplicate**: Link to canonical source

#### Quick File Management Checks

```bash
# How many files in root?
ls -1 *.md 2>/dev/null | wc -l
# Target: <15, Warning: >15, Critical: >20

# Any completion documents?
ls -1 *_COMPLETE.md *_VERIFICATION*.md 2>/dev/null | wc -l
# Target: 0 (all archived)

# Run archive check
./scripts/auto_archive.sh --dry-run
# Shows what would be archived and token savings
```

**Savings**: 80-93% session token reduction

---

## 📋 Budget Compliance Checklist

### Before Starting Session

- [ ] Run session start script: `./scripts/session_start.sh`
- [ ] Read compact context: `cat .ai/current-session.md` (~300 tokens)
- [ ] Check dashboard: `./scripts/context_dashboard.sh`
- [ ] Verify budget: Current session <10K tokens available

### During Session

- [ ] Use append-only logs for progress (never read)
- [ ] Edit specific sections in status files (not full files)
- [ ] Use grep before reading implementation files
- [ ] Check budget periodically: `./scripts/track_context_budget.sh --session`

### Before Committing

- [ ] Run file size check: `./scripts/monitor_file_sizes.sh`
- [ ] Verify no files exceed thresholds
- [ ] Update status: `./scripts/update_status.sh`
- [ ] Check budget: `./scripts/context_dashboard.sh`

### End of Session

- [ ] Archive if needed: `./scripts/session_archive.sh`
- [ ] Update baselines: `./scripts/establish_baselines.sh` (monthly)
- [ ] Commit changes with proper message
- [ ] Review session budget: Did we stay under 10K?

---

## 🔍 Budget Analysis

### Identifying Budget Leaks

**Common sources of excess token usage**:

1. **Reading append-only logs**
   - Cost: 1,500 tokens per read
   - Fix: Never read, only append

2. **Reading full trackers**
   - Cost: 1,000 tokens per read
   - Fix: Use indexes, edit sections only

3. **Browsing directory trees**
   - Cost: 500-1,000 tokens per browse
   - Fix: Use index files for navigation

4. **Reading implementation files fully**
   - Cost: 1,000-2,000 tokens per file
   - Fix: Use grep to locate, read specific sections

5. **Duplicate information**
   - Cost: 3,000+ tokens across files
   - Fix: Cross-reference canonical sources

### Budget Optimization Audit

Run comprehensive audit:
```bash
# 1. Check file sizes
./scripts/monitor_file_sizes.sh

# 2. Find duplicate content
./scripts/audit_cross_references.sh

# 3. Review session patterns
./scripts/track_context_budget.sh --analyze

# 4. Generate optimization report
./scripts/track_context_budget.sh --recommendations
```

---

## 📊 Budget Metrics

### Key Performance Indicators

1. **Session Start Cost**
   - Target: <300 tokens
   - Measure: Lines in current-session.md × 20
   - Status: ✅ Within budget / ⚠️ Approaching / ❌ Exceeded

2. **Average Session Cost**
   - Target: 3-10K tokens
   - Measure: Sum of all operations
   - Trend: ⬇️ Decreasing / ➡️ Stable / ⬆️ Increasing

3. **Budget Compliance Rate**
   - Target: 95%+ sessions within budget
   - Measure: (Compliant sessions / Total sessions) × 100
   - Goal: 100%

4. **Overhead Reduction**
   - Baseline: 30-50K tokens per session
   - Current: 3-10K tokens per session
   - Savings: 80-93%

### Tracking Metrics

```bash
# View current metrics
cat .ai/monitoring/baselines.json | jq .

# Track weekly trends
./scripts/track_context_budget.sh --weekly-report

# Export for analysis
./scripts/track_context_budget.sh --export-history > metrics.csv
```

---

## 🛠️ Budget Tools Reference

### Core Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `session_start.sh` | Initialize session with budget check | `./scripts/session_start.sh` |
| `context_dashboard.sh` | Visual budget overview | `./scripts/context_dashboard.sh` |
| `monitor_file_sizes.sh` | Check file size compliance | `./scripts/monitor_file_sizes.sh` |
| `track_context_budget.sh` | Detailed budget tracking | `./scripts/track_context_budget.sh` |
| `establish_baselines.sh` | Set/update budget baselines | `./scripts/establish_baselines.sh` |

### Monitoring Tools

| Tool | Purpose | Frequency |
|------|---------|-----------|
| `weekly_health_check.sh` | Comprehensive health check | Weekly |
| `auto_archive.sh` | Archive old files | Weekly |
| `auto_generate_indexes.sh` | Update indexes | As needed |
| `auto_update_doc_map.sh` | Update documentation map | As needed |

---

## 📚 Best Practices

### DO ✅

1. **Use session start script** - Generates optimal context (~300 tokens)
2. **Check dashboard regularly** - Monitor budget throughout session
3. **Use append-only logs** - Never read progress.log
4. **Edit specific sections** - Don't read full trackers
5. **Use indexes for navigation** - Find content efficiently
6. **Cross-reference canonical sources** - Avoid duplication
7. **Run monitoring tools** - Catch issues early

### DON'T ❌

1. ❌ **Read append-only logs** - Wastes 1,500 tokens
2. ❌ **Browse without indexes** - Inefficient navigation
3. ❌ **Read full files** - Use grep/sections instead
4. ❌ **Duplicate information** - Link to canonical source
5. ❌ **Skip session start** - Miss optimized context
6. ❌ **Ignore budget warnings** - Leads to exceeded limits
7. ❌ **Commit without checks** - May commit oversized files

---

## 🎓 Training Examples

### Example 1: Efficient Session Start

```bash
# START: Budget = 10,000 tokens available

# ✅ Good: Use session script (300 tokens)
./scripts/session_start.sh
cat .ai/current-session.md

# ❌ Bad: Manual context gathering (5,000 tokens)
cat PROJECT_STATUS.md
cat .ai/permanent/tool-registry.md
cat project/status/tools.md
cat project/tracking/progress.log
...

# Budget remaining: 9,700 tokens (good) vs 5,000 tokens (bad)
```

### Example 2: Efficient Progress Update

```bash
# ✅ Good: Append only (10 tokens)
echo "$(date +%Y-%m-%d): Implemented feature X" >> project/tracking/progress.log

# ❌ Bad: Read then append (1,510 tokens)
cat project/tracking/progress.log  # 1500 tokens
echo "2025-10-11: Implemented feature X" >> project/tracking/progress.log  # 10 tokens
```

### Example 3: Efficient Tool Lookup

```bash
# ✅ Good: Grep tool registry (100 tokens)
grep "calculate_correlation" .ai/permanent/tool-registry.md

# ❌ Bad: Read implementation files (2,000 tokens)
cat mcp_server/tools/stats_helper.py  # 1000 tokens
cat mcp_server/fastmcp_server.py  # 1000 tokens
```

---

## 🚀 Advanced Techniques

### Technique 1: Budget Checkpoints

Create budget checkpoints during long sessions:

```bash
# Checkpoint 1: After planning (2K tokens)
echo "Checkpoint 1: Planning complete, budget used: ~2K" >> .ai/daily/session.md

# Checkpoint 2: After implementation (5K tokens)
echo "Checkpoint 2: Implementation complete, budget used: ~5K" >> .ai/daily/session.md

# Checkpoint 3: Before testing (7K tokens)
echo "Checkpoint 3: Ready for testing, budget used: ~7K" >> .ai/daily/session.md
```

### Technique 2: Budget-Aware Task Planning

Break large tasks into budget-friendly subtasks:

```bash
# Instead of: "Implement entire feature" (15K tokens)

# Do: Break into phases
# Phase 1: Plan and design (2K tokens) - Session 1
# Phase 2: Core implementation (4K tokens) - Session 2
# Phase 3: Testing and docs (3K tokens) - Session 3
```

### Technique 3: Emergency Budget Reduction

If approaching limit (>9K tokens):

```bash
# 1. Archive current session
./scripts/session_archive.sh

# 2. Start fresh session
./scripts/session_start.sh

# 3. Use emergency context reduction
echo "Continue from: <brief state description>" > .ai/current-session.md
```

---

## 📞 Support

### If Budget Consistently Exceeded

1. **Audit current practices**:
   ```bash
   ./scripts/track_context_budget.sh --analyze
   ```

2. **Review common mistakes**:
   - Are you reading append-only logs?
   - Are you browsing without indexes?
   - Are you reading full files unnecessarily?

3. **Update baselines if needed**:
   ```bash
   ./scripts/establish_baselines.sh --force
   ```

4. **Review this guide**: Re-read optimization strategies section

---

**Last Updated**: 2025-10-11
**Version**: 1.0
**Status**: Active operational guide

**Remember**: The goal is sustainable context usage, not strict enforcement. Use these budgets as guidelines to maintain efficient, focused sessions.
