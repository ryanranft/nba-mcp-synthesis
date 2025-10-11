# Context Management Complete Guide

**Purpose**: Comprehensive guide to context optimization, budget management, and emergency procedures
**Last Updated**: 2025-10-11
**Status**: Active operational guide  
**Consolidates**: CONTEXT_OPTIMIZATION_GUIDE.md + CONTEXT_BUDGET_GUIDE.md + CONTEXT_EMERGENCY_PROCEDURES.md

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Best Practices](#best-practices)
3. [Budget Management](#budget-management)
4. [Emergency Procedures](#emergency-procedures)
5. [Advanced Techniques](#advanced-techniques)
6. [Quick Reference](#quick-reference)

---

## 🎯 Overview

### Why Context Optimization Matters

**Context Limits**: AI systems have maximum context windows. When approaching limits:
- Auto context compaction may occur, losing history
- Performance degrades
- Continuity is lost mid-task
- Progress tracking may be affected

**Benefits of Optimization**:
- ✅ Longer, uninterrupted work sessions
- ✅ Better context retention across complex tasks
- ✅ Improved AI responses with full history
- ✅ Smoother multi-file editing workflows

### Target Budget

**Goal**: Maintain **3-10K tokens per session** (vs 30-50K before optimization)

**Achievement**: This project has achieved **80-93% context reduction** through systematic optimization.

---

## 🎯 Best Practices

### 1. Document Organization

#### ✅ DO:
- **Keep root directory clean** - Only essential files (README, STATUS, TRACKER)
- **Use directory hierarchy** - Organize into `/project/`, `/docs/`, `/.ai/`
- **Remove duplicates** - Maintain single source of truth
- **Archive old files** - Move completed work to `/docs/archive/YYYY-MM/`
- **Small, focused files** - Target <300 lines per file

#### ❌ DON'T:
- Keep 50+ markdown files in root
- Duplicate files across directories
- Create massive single-file documentation (>1000 lines)
- Leave temporary/session files in tracked locations

**Example Structure**:
```
project/
├── README.md (overview, ~300 lines)
├── PROJECT_STATUS.md (quick status, <150 lines)
├── .ai/
│   ├── current-session.md (auto-generated, <80 lines)
│   ├── permanent/ (tracked references)
│   └── daily/ (gitignored session notes)
├── project/
│   ├── status/ (current state)
│   └── tracking/ (progress logs)
└── docs/
    ├── guides/ (how-to documentation)
    ├── plans/ (strategic planning)
    └── archive/ (completed work, gitignored)
```

### 2. Reading Strategies

#### Append-Only Logs (NEVER Read)
```bash
# ❌ DON'T: Read the entire log
cat project/tracking/progress.log  # 1500 tokens!

# ✅ DO: Only append, never read
echo "$(date +%Y-%m-%d): Action" >> project/tracking/progress.log  # 10 tokens
```

#### Index-Based Navigation
```bash
# ❌ DON'T: Read entire tracker
cat PROJECT_MASTER_TRACKER.md  # 1000+ tokens

# ✅ DO: Use index to find specific section
grep -n "Tool Registration" project/index.md
vim project/status/tools.md +45  # Jump to specific line, 50 tokens
```

#### Cross-References Over Duplication
```markdown
# ❌ DON'T: Duplicate content
## Tool Registration Process
1. Create tool in mcp_server/tools/
2. Register in fastmcp_server.py
... (repeated in multiple files)

# ✅ DO: Use cross-references
## Tool Registration
See [Tool Registration Guide](project/status/tools.md) for complete process.
```

### 3. Session Management

#### Every Session Should Start With:
```bash
# 1. Generate compact session context
./scripts/session_start.sh

# 2. Review compact summary
cat .ai/current-session.md  # ~300 tokens

# 3. Check specific status if needed
cat PROJECT_STATUS.md  # ~150 tokens
```

**Cost**: ~450 tokens (vs 5,000+ reading multiple files)

#### During Session:
```bash
# Progress updates (10 tokens)
echo "$(date +%Y-%m-%d): Action" >> project/tracking/progress.log

# Status updates (50 tokens)
vim project/status/tools.md  # Edit specific section only

# Decisions (30 tokens)
echo "$(date +%Y-%m-%d): Decision" >> project/tracking/decisions.md
```

#### At Session End:
```bash
# Update status
./scripts/update_status.sh

# Commit changes
git add . && git commit -m "feat: Session summary"

# Archive if needed
./scripts/auto_archive.sh --interactive
```

---

## 📊 Budget Management

### Token Budgets by Operation

| Operation | Budget | File/Source | Target |
|-----------|--------|-------------|--------|
| **Session Start** | 300 | `.ai/current-session.md` | <80 lines |
| **Status Check** | 150 | `PROJECT_STATUS.md` | <150 lines |
| **Tool Lookup** | 100 | `.ai/permanent/tool-registry.md` | grep search |
| **Progress Update** | 10 | `project/tracking/progress.log` | append only |
| **Status Update** | 50 | `project/status/*.md` | edit section |
| **Decision Recording** | 30 | `project/tracking/decisions.md` | append only |

**Core Operations Subtotal**: ~640 tokens

### Session Type Budgets

| Session Type | Token Budget | Description |
|--------------|--------------|-------------|
| **Quick Update** | 500-1K | Status update, simple fix |
| **Feature Development** | 2-4K | New feature, multiple files |
| **Major Refactor** | 5-8K | Large changes, testing |
| **Sprint Planning** | 3-6K | Review plans, set goals |
| **Emergency Limit** | 10K | Absolute maximum |

### Budget Tracking

#### Check Current Budget
```bash
# View dashboard
./scripts/context_dashboard.sh

# Track session budget
./scripts/track_context_budget.sh --session

# Monitor file sizes
./scripts/monitor_file_sizes.sh

# Get recommendations
./scripts/track_context_budget.sh --recommendations
```

#### File Size Thresholds

| File Type | Warning | Critical | Action |
|-----------|---------|----------|--------|
| Index files | 80 lines | 100 lines | Split or consolidate |
| Status files | 160 lines | 200 lines | Move completed to archive |
| Guide files | 240 lines | 300 lines | Split into topics |
| Daily sessions | 400 lines | 500 lines | Archive to monthly |
| Plan files | 2400 lines | 3000 lines | Split or archive sections |

### Budget Alerts

**Green** (< 7K tokens): Continue normally  
**Yellow** (7-8K tokens): Monitor closely, consider quick wins  
**Orange** (8-9K tokens): Apply preventive optimizations  
**Red** (9-10K tokens): Emergency procedures required  
**Critical** (>10K tokens): Immediate action required

---

## 🚨 Emergency Procedures

### Emergency Levels

#### Level 1: Warning (8-9K tokens)

**Status**: Approaching limit, preventive action recommended

**Actions**:
1. Check current budget: `./scripts/track_context_budget.sh --session`
2. Review dashboard: `./scripts/context_dashboard.sh`
3. Identify largest contributors: `./scripts/monitor_file_sizes.sh`
4. Apply quick optimizations (see below)

**Time to Act**: Within next 1-2 operations

---

#### Level 2: Critical (9-10K tokens)

**Status**: At limit, immediate action required

**Actions**:
1. **Stop reading new files** - Work with what's in context
2. **Create checkpoint** - Save current state
   ```bash
   ./scripts/checkpoint_session.sh --name=before-optimization
   ```
3. **Run emergency reduction**
   ```bash
   ./scripts/emergency_context_reduce.sh --level=2
   ```
4. **Archive completion docs**
   ```bash
   ./scripts/auto_archive.sh --interactive
   ```
5. **Focus on critical files only**

**Time to Act**: Immediately (before next operation)

---

#### Level 3: Emergency (>10K tokens)

**Status**: Exceeded limit, data loss risk

**Actions**:
1. **STOP immediately** - No new file reads
2. **Save critical work**
   ```bash
   git add -A
   git commit -m "emergency: Save work before context reset"
   ```
3. **Archive session**
   ```bash
   ./scripts/checkpoint_session.sh --name=emergency-$(date +%Y%m%d%H%M%S)
   ```
4. **Start fresh session**
   ```bash
   # In new session
   ./scripts/session_start.sh --restore=emergency-XXXXXXXXXX
   ```

**Time to Act**: NOW

### Quick Optimization Actions

When approaching limits, use these quick wins:

**1. Archive Completion Documents** (30 sec, ~500 tokens)
```bash
./scripts/auto_archive.sh --interactive
```

**2. Close Unnecessary Files** (manual, ~200-500 tokens)
- Close files not actively being edited
- Keep only 2-3 essential files open

**3. Use Grep Instead of Reading** (~80% reduction)
```bash
# Instead of: cat large_file.md
grep -n "specific_term" large_file.md  # Much smaller
```

**4. Reference Instead of Read** (~90% reduction)
```markdown
# Instead of reading full file, just note:
"See PROJECT_MASTER_TRACKER.md lines 45-67 for details"
```

**5. Checkpoint and Restart** (if nothing else works)
```bash
./scripts/checkpoint_session.sh
# Start fresh, restore checkpoint info as needed
```

### Emergency Contact Reduction Script

```bash
# Level 1: Quick optimizations (30% reduction)
./scripts/emergency_context_reduce.sh --level=1 --dry-run
./scripts/emergency_context_reduce.sh --level=1

# Level 2: Aggressive reduction (50% reduction)  
./scripts/emergency_context_reduce.sh --level=2 --dry-run
./scripts/emergency_context_reduce.sh --level=2

# Level 3: Maximum reduction (70% reduction)
./scripts/emergency_context_reduce.sh --level=3 --dry-run
./scripts/emergency_context_reduce.sh --level=3
```

**What it does**:
- Level 1: Archives completion docs, closes unused files
- Level 2: Level 1 + archives old sessions, clears caches
- Level 3: Level 2 + moves plans to archive, aggressive cleanup

---

## 🔧 Advanced Techniques

### 1. Symbolic Links for Large Files

For large reference files that rarely change:

```bash
# Move to external storage
mv docs/plans/LARGE_PLAN.md ~/external/nba-mcp/

# Create symlink
ln -s ~/external/nba-mcp/LARGE_PLAN.md docs/plans/LARGE_PLAN.md

# Reference in doc
echo "See external: ~/external/nba-mcp/LARGE_PLAN.md" > docs/plans/LARGE_PLAN_ref.md
```

**Savings**: File not loaded into context unless explicitly read

### 2. Differential Updates

Instead of reading/writing entire files:

```bash
# Read only changed lines
git diff --unified=0 file.md | head -20

# Update specific line range
sed -i.bak '45,67s/old/new/' file.md
```

**Savings**: 80-90% reduction for large files

### 3. Context-Aware File Reading

```python
# Instead of: read entire file
with open('file.md') as f:
    content = f.read()  # 10K tokens

# Do: read specific section
with open('file.md') as f:
    lines = f.readlines()[45:67]  # 500 tokens
```

### 4. Minimal Templates

Create minimal versions for common operations:

```bash
# Full guide: 1000 lines
docs/guides/FULL_GUIDE.md

# Minimal template: 50 lines
.ai/templates/guide-minimal.md

# Use minimal for quick reference, full only when needed
```

### 5. Progressive Disclosure

Structure docs with summaries first:

```markdown
# Topic Name

## Quick Summary (50 lines)
- Key point 1
- Key point 2
- Key point 3

For details, see sections below or [detailed guide](link).

## Detailed Section 1 (200 lines)
...

## Detailed Section 2 (200 lines)
...
```

**Usage**: Read summary first (50 tokens), dive into details only if needed

---

## 📋 Quick Reference

### Daily Operations

```bash
# Session start (~300 tokens)
./scripts/session_start.sh
cat .ai/current-session.md

# Status check (~150 tokens)
cat PROJECT_STATUS.md

# Tool lookup (~100 tokens)
grep "tool_name" .ai/permanent/tool-registry.md

# Progress update (~10 tokens)
echo "$(date +%Y-%m-%d): Action" >> project/tracking/progress.log

# Session end
./scripts/update_status.sh
git commit -m "feat: Work summary"
```

### Weekly Maintenance

```bash
# Run health check
./scripts/weekly_health_check.sh

# Archive if needed
./scripts/auto_archive.sh --interactive

# Rotate logs
./scripts/rotate_progress_log.sh

# Check dashboard
./scripts/context_dashboard.sh
```

### Monthly Maintenance

```bash
# Update baselines
./scripts/establish_baselines.sh --force

# Create monthly summary
vim .ai/monthly/$(date +%Y-%m)-summary.md

# Comprehensive archive
./scripts/auto_archive.sh --age=60

# Update metrics
vim project/metrics/context_usage.md
```

### Emergency Actions

```bash
# Level 1: Warning (8-9K)
./scripts/context_dashboard.sh
./scripts/auto_archive.sh --interactive

# Level 2: Critical (9-10K)
./scripts/checkpoint_session.sh --name=emergency
./scripts/emergency_context_reduce.sh --level=2

# Level 3: Emergency (>10K)
git commit -m "emergency: Save work"
./scripts/checkpoint_session.sh
# Start fresh session
```

### File Size Checks

```bash
# Monitor sizes
./scripts/monitor_file_sizes.sh

# Check specific file
wc -l filename.md

# Check directory
find docs/ -name "*.md" -exec wc -l {} \; | sort -rn | head -10
```

### Budget Tracking

```bash
# Session budget
./scripts/track_context_budget.sh --session

# Weekly report
./scripts/track_context_budget.sh --weekly-report

# Get recommendations
./scripts/track_context_budget.sh --recommendations

# Export metrics
./scripts/context_dashboard.sh --export=metrics.json
```

---

## 🎓 Training & Onboarding

### For New Team Members

**Read these in order** (60 minutes):
1. This guide - Overview (10 min)
2. Best Practices section (15 min)
3. Budget Management section (15 min)
4. Quick Reference (10 min)
5. Practice with tools (10 min)

### For AI Sessions

**Every session**:
1. Run `./scripts/session_start.sh`
2. Read `.ai/current-session.md` (300 tokens)
3. Follow best practices from this guide
4. Monitor budget via dashboard
5. Apply emergency procedures if needed

---

## 📊 Success Metrics

You're doing it right if:
- ✅ Session start <400 tokens
- ✅ Status checks <200 tokens
- ✅ Tool lookups <150 tokens
- ✅ Overall session 3-10K tokens
- ✅ Never hit emergency level 3
- ✅ Green/yellow dashboard status
- ✅ Files stay within size targets

---

## 🔗 Related Documents

### Core Documentation
- **[Operations Guide](../../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Daily operations, decision tree
- **[Session Management](.ai/index.md)** - Complete session management guide
- **[Documentation Map](../DOCUMENTATION_MAP.md)** - Where to find everything

### Automation Scripts
- `scripts/session_start.sh` - Session initialization
- `scripts/auto_archive.sh` - Automatic archiving
- `scripts/rotate_progress_log.sh` - Log rotation
- `scripts/context_dashboard.sh` - Budget monitoring
- `scripts/emergency_context_reduce.sh` - Emergency optimization

### Configuration
- `.ai/permanent/context_budget.json` - Budget configuration
- `.ai/permanent/file-management-policy.md` - File policies
- `.gitignore` - Gitignore patterns for sessions

---

## 💡 Remember

**The Goal**: Maintain 3-10K tokens per session through:
1. Reading only what you need
2. Using indexes for navigation
3. Appending to logs without reading them
4. Editing specific sections, not entire files
5. Following the established structure
6. Monitoring budget proactively
7. Taking emergency action when needed

**When in doubt**: Check the dashboard, consult this guide, or run health checks.

---

**Last Updated**: 2025-10-11
**Version**: 1.0 (Consolidated from 3 guides)
**Status**: Active operational guide
**Next Review**: Quarterly or when patterns change

**Replaces**: 
- CONTEXT_OPTIMIZATION_GUIDE.md (282 lines)
- CONTEXT_BUDGET_GUIDE.md (652 lines)
- CONTEXT_EMERGENCY_PROCEDURES.md (548 lines)

**Total**: 1,482 lines → 600 lines (60% reduction)

