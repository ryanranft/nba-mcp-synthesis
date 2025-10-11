# File Management Complete Guide

**Purpose**: Comprehensive guide for file creation, organization, and management
**Audience**: Claude/AI sessions, developers
**Last Updated**: 2025-10-11
**Status**: Active reference
**Consolidates**: FILE_CREATION_DECISION_TREE.md + FILE_MANAGEMENT_ANTI_PATTERNS.md

---

## 📚 Table of Contents

1. [Quick Reference](#quick-reference)
2. [Decision Tree](#decision-tree)
3. [Anti-Patterns & Solutions](#anti-patterns--solutions)
4. [Common Tasks](#common-tasks)
5. [File Management Policy](#file-management-policy)

---

## 🎯 Quick Reference

### Before Creating ANY File

**Follow these 4 checks in order:**

1. ⚠️ **Is it AUTO-GENERATED?** → Use script, don't edit manually
2. 🔧 **Is there a script?** → Use script if available
3. 📋 **Does canonical location exist?** → Update existing file
4. 🌳 **Follow decision tree** → See below

### Golden Rules

- ✅ **Use scripts** for automation
- ✅ **Update existing** files when possible
- ✅ **Check DOCUMENTATION_MAP** before creating
- ✅ **Append to logs**, never read them
- ✅ **Cross-reference**, don't duplicate
- ❌ **Never edit** auto-generated files
- ❌ **Never create** standalone status updates
- ❌ **Never duplicate** information

---

## 🌳 Decision Tree

### Complete File Creation Flow

```
┌──────────────────────────────────────────────────┐
│ STEP 0: Is this file AUTO-GENERATED?            │
│         ⚠️ CRITICAL - CHECK FIRST                │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → Use generator script
              │        Examples:
              │        • .ai/current-session.md → ./scripts/session_start.sh
              │        • PROJECT_STATUS.md → ./scripts/update_status.sh
              │        • Test results → Run test script
              │        ❌ NEVER manually edit
              │
              └─ NO → Continue to Step 1
                        │
┌──────────────────────────────────────────────────┐
│ STEP 1: Is there a script for this?             │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → Use the script
              │        Available:
              │        • ./scripts/session_start.sh --new-session
              │        • ./scripts/auto_archive.sh
              │        • ./scripts/checkpoint_session.sh
              │
              └─ NO → Continue to Step 2
                        │
┌──────────────────────────────────────────────────┐
│ STEP 2: Does canonical location exist?          │
│         Check docs/DOCUMENTATION_MAP.md          │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → Update existing file
              │        Examples:
              │        • Tool info → .ai/permanent/tool-registry.md
              │        • Status → project/status/*.md
              │        • Decision → project/tracking/decisions.md
              │
              └─ NO → Continue to Step 3
                        │
┌──────────────────────────────────────────────────┐
│ STEP 3: Is this temporary/session-specific?     │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → .ai/daily/YYYY-MM-DD-session-N.md
              │        (gitignored, detailed notes)
              │
              └─ NO → Continue to Step 4
                        │
┌──────────────────────────────────────────────────┐
│ STEP 4: Is this permanent reference?            │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → .ai/permanent/*.md
              │        Examples:
              │        • tool-registry.md (tool catalog)
              │        • phases.md (implementation phases)
              │        • file-management-policy.md (policies)
              │
              └─ NO → Continue to Step 5
                        │
┌──────────────────────────────────────────────────┐
│ STEP 5: Is this current project status?         │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → project/status/*.md
              │        Examples:
              │        • tools.md (tool registration)
              │        • sprints.md (sprint progress)
              │        • blockers.md (current issues)
              │
              └─ NO → Continue to Step 6
                        │
┌──────────────────────────────────────────────────┐
│ STEP 6: Is this documentation/guide?            │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → docs/guides/*.md
              │        • Create guide file
              │        • Update docs/guides/index.md
              │        • Add to DOCUMENTATION_MAP.md
              │
              └─ NO → Continue to Step 7
                        │
┌──────────────────────────────────────────────────┐
│ STEP 7: Is this historical/completed?           │
└──────────────────────────────────────────────────┘
              │
              ├─ YES → docs/archive/YYYY-MM/*.md
              │        (gitignored, searchable)
              │
              └─ NO → Root directory (rarely)
                       • Only for essential project files
                       • README, CHANGELOG, STATUS
```

---

## 🚨 Anti-Patterns & Solutions

### Critical Anti-Pattern #1: Editing Auto-Generated Files

**❌ WRONG**:
```bash
vim .ai/current-session.md
echo "Task: New feature" >> .ai/current-session.md
```

**✅ CORRECT**:
```bash
./scripts/session_start.sh  # Regenerates with latest state
```

**Why bad**: Breaks automation, manual edits overwritten, 10-20x token cost

**Auto-generated files** (NEVER edit):
- `.ai/current-session.md`
- `PROJECT_STATUS.md` (if using update script)
- Test/benchmark results
- Session checkpoints

---

### Critical Anti-Pattern #2: Standalone Status Updates

**❌ WRONG**:
```bash
vim STATUS_UPDATE_2025-10-11.md
vim TOOLS_REGISTRATION_UPDATE.md
vim PROGRESS_REPORT_2025-10-11.md
```

**✅ CORRECT**:
```bash
# Option 1: Append to log (simple updates)
echo "$(date +%Y-%m-%d): Registered 5 tools" >> project/tracking/progress.log

# Option 2: Edit specific section
vim project/status/tools.md +67

# Option 3: Use existing status file
vim project/status/sprints.md
```

**Why bad**: File proliferation, context bloat, poor discoverability

---

### Critical Anti-Pattern #3: Creating Completion Documents in Root

**❌ WRONG**:
```bash
# Root directory gets cluttered
vim SPRINT_5_COMPLETE.md
vim FEATURE_X_VERIFICATION.md
vim SESSION_COMPLETE.md
```

**✅ CORRECT**:
```bash
# Create in appropriate location
vim docs/sprints/completed/SPRINT_5_COMPLETE.md

# Then archive when done reviewing
./scripts/auto_archive.sh --interactive
```

**Why bad**: Root clutter, 15+ files in root directory

---

### Anti-Pattern #4: Duplicating Information

**❌ WRONG**:
```markdown
## Tool Registration Process
1. Create tool in mcp_server/tools/
2. Register in fastmcp_server.py
... (repeated in 5 different files)
```

**✅ CORRECT**:
```markdown
## Tool Registration
See [Tool Registration Guide](project/status/tools.md) for complete process.
```

**Why bad**: Maintenance nightmare, inconsistencies, context bloat

---

### Anti-Pattern #5: Reading Append-Only Logs

**❌ WRONG**:
```bash
cat project/tracking/progress.log  # 1500 tokens!
echo "$(date +%Y-%m-%d): Update" >> project/tracking/progress.log
```

**✅ CORRECT**:
```bash
# Just append, never read
echo "$(date +%Y-%m-%d): Update" >> project/tracking/progress.log  # 10 tokens
```

**Why bad**: Massive token cost, no benefit

---

### Anti-Pattern #6: Creating Files Without Index Updates

**❌ WRONG**:
```bash
vim docs/guides/NEW_FEATURE_GUIDE.md
# Forget to update indexes
```

**✅ CORRECT**:
```bash
# 1. Create guide
vim docs/guides/NEW_FEATURE_GUIDE.md

# 2. Update guide index
vim docs/guides/index.md

# 3. Add to documentation map
vim docs/DOCUMENTATION_MAP.md
```

**Why bad**: File not discoverable, broken navigation

---

### Anti-Pattern #7: Bypassing Scripts

**❌ WRONG**:
```bash
# Manual session file creation
vim .ai/daily/2025-10-11-session-1.md
# Copy template manually
# Fill in fields manually
```

**✅ CORRECT**:
```bash
./scripts/session_start.sh --new-session
# Template auto-populated
# Git status auto-included
# Project state auto-included
```

**Why bad**: Missing automation benefits, inconsistent format

---

### Anti-Pattern #8: Forgetting to Archive

**❌ WRONG**:
```bash
# Leaving old completion docs in active workspace
ls *.md  # Shows 30+ files
```

**✅ CORRECT**:
```bash
# Regular archiving
./scripts/auto_archive.sh --interactive
# Or automatic
./scripts/auto_archive.sh --age=30
```

**Why bad**: Root clutter, context bloat, hard to find current work

---

### Anti-Pattern #9: Large Monolithic Files

**❌ WRONG**:
```bash
# Single 2000-line tracker file
vim PROJECT_MEGA_TRACKER.md  # Everything in one file
```

**✅ CORRECT**:
```bash
# Split into focused files
project/status/tools.md (150 lines)
project/status/sprints.md (100 lines)
project/tracking/progress.log (append-only)
```

**Why bad**: 1000+ tokens to read, hard to navigate, merge conflicts

---

### Anti-Pattern #10: Not Using .gitignore

**❌ WRONG**:
```bash
# Tracking temporary files
git add .ai/daily/2025-10-11-session-1.md
git add test_results/temp_output.txt
```

**✅ CORRECT**:
```bash
# .gitignore patterns
.ai/daily/*
.ai/monthly/*
test_results/
*.log (except important ones)
```

**Why bad**: Repo bloat, merge conflicts, exposed sensitive data

---

## 📋 Common Tasks

### Starting a New Session

```bash
# 1. Generate session context
./scripts/session_start.sh

# 2. Read compact summary
cat .ai/current-session.md  # ~300 tokens

# 3. (Optional) Create detailed notes
./scripts/session_start.sh --new-session
```

### Recording Progress

```bash
# Simple update (10 tokens)
echo "$(date +%Y-%m-%d): Action taken" >> project/tracking/progress.log

# Important decision (30 tokens)
echo "$(date +%Y-%m-%d): Decision - Rationale" >> project/tracking/decisions.md

# Detailed notes (use daily session file)
vim .ai/daily/2025-10-11-session-1.md
```

### Updating Status

```bash
# 1. Find specific section
grep -n "Sprint 5" project/status/sprints.md

# 2. Edit that section only
vim project/status/sprints.md +67

# 3. Update overall status (optional)
./scripts/update_status.sh
```

### Creating New Guide

```bash
# 1. Check if topic exists
grep -i "feature name" docs/DOCUMENTATION_MAP.md

# 2. Create guide
vim docs/guides/NEW_FEATURE_GUIDE.md

# 3. Update index
vim docs/guides/index.md

# 4. Add to documentation map
vim docs/DOCUMENTATION_MAP.md
```

### Archiving Old Files

```bash
# Check what would be archived
./scripts/auto_archive.sh --dry-run

# Archive interactively
./scripts/auto_archive.sh --interactive

# Archive automatically (age-based)
./scripts/auto_archive.sh --age=30
```

### Creating Checkpoint

```bash
# Save current session state
./scripts/checkpoint_session.sh --name=before-major-change

# List checkpoints
./scripts/checkpoint_session.sh --list

# Restore if needed
./scripts/session_start.sh --restore=checkpoint-name
```

---

## 📊 File Organization Reference

### Directory Structure

```
project/
├── .ai/                          # Session management
│   ├── current-session.md        # Auto-generated (<80 lines)
│   ├── index.md                  # Session guide
│   ├── daily/                    # Gitignored session notes
│   ├── monthly/                  # Gitignored summaries
│   ├── permanent/                # Tracked references
│   └── monitoring/               # Context monitoring
│
├── project/                      # Project status & tracking
│   ├── status/                   # Current state
│   │   ├── tools.md             # Tool registration
│   │   ├── sprints.md           # Sprint progress
│   │   ├── remaining-work.md    # Pending features
│   │   └── blockers.md          # Current issues
│   ├── tracking/                 # Progress tracking
│   │   ├── progress.log         # Append-only log
│   │   ├── decisions.md         # Key decisions
│   │   └── milestones.md        # Major achievements
│   └── metrics/                  # Metrics tracking
│
├── docs/                         # Documentation
│   ├── guides/                   # How-to guides
│   ├── plans/                    # Strategic plans
│   ├── sprints/                  # Sprint documentation
│   ├── analysis/                 # Research & analysis
│   └── archive/                  # Historical (gitignored)
│       └── YYYY-MM/             # Organized by month
│
├── scripts/                      # Automation
│   ├── session_start.sh         # Session initialization
│   ├── auto_archive.sh          # Automatic archiving
│   ├── rotate_progress_log.sh   # Log rotation
│   └── ...
│
└── Root (essential files only)
    ├── README.md
    ├── PROJECT_STATUS.md
    ├── PROJECT_MASTER_TRACKER.md
    ├── CHANGELOG.md
    └── ...
```

### File Size Targets

| File Type | Target | Warning | Critical |
|-----------|--------|---------|----------|
| Index files | <80 lines | 80-100 | >100 |
| Status files | <200 lines | 160-200 | >200 |
| Guide files | <300 lines | 240-300 | >300 |
| Daily sessions | <500 lines | 400-500 | >500 |
| Plans | <3000 lines | 2400-3000 | >3000 |

### Token Budgets

| Operation | Budget | How |
|-----------|--------|-----|
| Session start | 300 | Use session_start.sh |
| Status check | 150 | Read PROJECT_STATUS.md |
| Progress update | 10 | Append to progress.log |
| Status update | 50 | Edit specific section |
| Tool lookup | 100 | grep tool-registry.md |

---

## 🔗 Related Resources

### Core Documentation
- **[File Management Policy](.ai/permanent/file-management-policy.md)** - Complete policy document
- **[Context Management Guide](CONTEXT_MANAGEMENT_COMPLETE.md)** - Context optimization
- **[Documentation Map](../DOCUMENTATION_MAP.md)** - Canonical locations
- **[Operations Guide](../../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Daily operations

### Automation Scripts
- **session_start.sh** - Session initialization
- **auto_archive.sh** - Automatic archiving
- **checkpoint_session.sh** - Session checkpointing
- **update_status.sh** - Status updates
- **rotate_progress_log.sh** - Log rotation

### Monitoring Tools
- **monitor_file_sizes.sh** - File size monitoring
- **context_dashboard.sh** - Context budget dashboard
- **weekly_health_check.sh** - Comprehensive health check

---

## ✅ Quick Checklist

### Before Creating a File
- [ ] Is it auto-generated? (Use script)
- [ ] Is there a script? (Use it)
- [ ] Does canonical location exist? (Update it)
- [ ] Have I checked DOCUMENTATION_MAP? (Find location)
- [ ] Is this temporary? (.ai/daily/)
- [ ] Is this permanent reference? (.ai/permanent/)
- [ ] Is this status update? (project/status/)
- [ ] Is this a guide? (docs/guides/)
- [ ] Will I update indexes? (index.md, DOCUMENTATION_MAP.md)

### After Creating a File
- [ ] Updated relevant index
- [ ] Added to DOCUMENTATION_MAP (if new topic)
- [ ] Committed with descriptive message
- [ ] Tested that links work

### Regular Maintenance
- [ ] Weekly: Run auto_archive.sh
- [ ] Weekly: Check file sizes
- [ ] Monthly: Rotate progress log
- [ ] Monthly: Archive old sessions
- [ ] Quarterly: Review and consolidate

---

## 💡 Best Practices

### DO ✅
- **Use automation** - Scripts over manual work
- **Update existing** - Don't create new unless necessary
- **Cross-reference** - Link to canonical sources
- **Append to logs** - Never read append-only logs
- **Archive regularly** - Keep workspace clean
- **Check indexes** - Use DOCUMENTATION_MAP.md
- **Follow structure** - Respect directory hierarchy
- **Monitor sizes** - Keep files under targets

### DON'T ❌
- **Edit auto-generated files** - Use scripts instead
- **Create standalone updates** - Use existing files
- **Duplicate information** - Cross-reference instead
- **Skip index updates** - Maintain discoverability
- **Bypass scripts** - Lose automation benefits
- **Forget to archive** - Workspace gets cluttered
- **Create mega-files** - Split into focused files
- **Track temporary files** - Use .gitignore

---

## 🎯 Success Criteria

You're doing it right if:
- ✅ Root directory has <15 markdown files
- ✅ Using scripts for automation
- ✅ No auto-generated files manually edited
- ✅ Progress log is append-only (never read)
- ✅ Files stay within size targets
- ✅ Indexes are up to date
- ✅ Archive process runs regularly
- ✅ No duplicate information
- ✅ DOCUMENTATION_MAP is accurate

---

**Last Updated**: 2025-10-11
**Version**: 1.0 (Consolidated from 2 guides)
**Status**: Active reference guide

**Replaces**:
- FILE_CREATION_DECISION_TREE.md (399 lines)
- FILE_MANAGEMENT_ANTI_PATTERNS.md (528 lines)

**Total**: 927 lines → 450 lines (51% reduction)

