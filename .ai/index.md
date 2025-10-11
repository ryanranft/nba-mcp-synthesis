# AI Session State Directory

**Purpose**: Optimized session state management for Claude Code to minimize context usage

**Last Updated**: 2025-10-11

---

## 📁 Directory Structure

### `current-session.md` (Auto-Generated)
**Purpose**: Compact summary of current work state (50-100 lines)
**Updated**: At session start by `scripts/session_start.sh`
**Contains**:
- Active todos from last session
- Recent commits (last 5)
- Open files/changes
- Next immediate action

**Context Cost**: ~100 tokens (vs 5000+ tokens reading multiple files)

### `daily/` (Gitignored)
**Purpose**: Session notes from today's work
**Naming**: `YYYY-MM-DD-session-N.md` (e.g., `2025-10-11-session-1.md`)
**Retention**: 7 days, then moved to monthly/ or deleted
**Contains**:
- Detailed work log for each session
- Decisions made
- Problems encountered
- Code changes summary

**When to Create**: Use `scripts/session_start.sh --new-session`

### `monthly/` (Gitignored)
**Purpose**: Aggregated summaries from completed work periods
**Naming**: `YYYY-MM-summary.md` (e.g., `2025-10-summary.md`)
**Retention**: 90 days, then archived to S3 or deleted
**Contains**:
- Major milestones achieved
- Sprint completions
- Significant refactorings
- Monthly metrics

**When to Create**: End of month, or use `scripts/session_archive.sh --monthly`

### `permanent/` (Git Tracked)
**Purpose**: Critical decisions and architectural patterns that must persist
**Naming**: Descriptive names (e.g., `fastmcp-migration-decisions.md`)
**Retention**: Forever (git tracked)
**Contains**:
- Architecture decisions (ADRs)
- API design choices
- Breaking changes log
- Migration strategies

**When to Create**: When making significant architectural decisions

### `archive/` (Gitignored)
**Purpose**: Old session files before archiving to S3
**Naming**: Organized by date/sprint
**Retention**: Until uploaded to S3
**Contains**: Historical daily/monthly files awaiting backup

---

## 🚀 Quick Start

### Starting a New Session
```bash
# Generate compact current-session.md from git + recent work
scripts/session_start.sh

# Read the compact summary (100 tokens vs 5000+ tokens)
cat .ai/current-session.md
```

### During a Session
```bash
# Append quick note to today's session file
echo "Implemented Feature X - see commit abc123" >> .ai/daily/$(date +%Y-%m-%d)-session-1.md

# Update current session summary
scripts/update_current_session.sh
```

### Ending a Session
```bash
# Archive today's work to S3 (optional)
scripts/session_archive.sh

# Or just commit current-session.md updates
git add .ai/current-session.md .ai/permanent/
git commit -m "chore: Update session state"
```

---

## 📊 Context Optimization

| Operation | Without .ai/ | With .ai/ | Savings |
|-----------|--------------|-----------|---------|
| Session start | 5,000 tokens | 100 tokens | 98% |
| Status check | 1,000 tokens | 150 tokens | 85% |
| Resume work | 10,000 tokens | 200 tokens | 98% |

**Target**: Keep current-session.md under 100 lines for optimal context usage

---

## 🔧 File Templates

See templates in each subdirectory:
- `daily/template.md` - Daily session template
- `monthly/template.md` - Monthly summary template
- `permanent/template.md` - Architecture decision template

---

## 🔐 Security & Privacy

**Git Tracking**:
- ✅ `current-session.md` - Tracked (compact summary)
- ✅ `permanent/` - Tracked (architectural decisions)
- ❌ `daily/` - Gitignored (detailed work logs)
- ❌ `monthly/` - Gitignored (aggregated summaries)
- ❌ `archive/` - Gitignored (pre-S3 backup)

**S3 Backup**: Optional long-term storage for full session history (~$0.0005/month)

---

## 📚 Related Documents

- [CONTEXT_OPTIMIZATION_PLAN.md](../docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md) - Full implementation plan
- [CONTEXT_OPTIMIZATION_GUIDE.md](../docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md) - Best practices guide
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - Quick project overview (when implemented)

---

**Navigation**: [Root](../) | [Docs](../docs/) | [Project Status](../project/) | [Scripts](../scripts/)
