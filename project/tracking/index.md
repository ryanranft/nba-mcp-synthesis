# Tracking - Progress Over Time

**Purpose**: Historical progress tracking with append-only logs
**Last Updated**: 2025-10-11

---

## 📋 Tracking Files

| File | Purpose | Usage Pattern | Context Cost |
|------|---------|---------------|--------------|
| [progress.log](progress.log) | Daily progress updates | Append-only, never read | ~0 tokens |
| [decisions.md](decisions.md) | Key decisions log | Read-when-needed | ~100 tokens |
| [milestones.md](milestones.md) | Major milestone history | Read-when-needed | ~50 tokens |

---

## 🚀 Quick Start

### Append to Progress Log (Recommended)
```bash
# NEVER read progress.log, only append to it
echo "$(date +%Y-%m-%d): Registered 2 NBA tools" >> project/tracking/progress.log

# Or use helper script
./scripts/update_status.sh "Registered 2 NBA tools"
```

**Why Append-Only?**
- ❌ Old way: Read 1000-line file to find latest update (1500 tokens)
- ✅ New way: Append one line without reading (10 tokens)
- **Result**: 99% reduction in context usage

### Log a Decision
```bash
# Add to decisions.md (read only when reviewing history)
echo "## $(date +%Y-%m-%d): Adopted FastMCP framework" >> project/tracking/decisions.md
echo "Rationale: Better context injection and lifespan management" >> project/tracking/decisions.md
```

### Log a Milestone
```bash
# Add to milestones.md
echo "- **$(date +%Y-%m-%d)**: Phase 1 Complete - Session state management" >> project/tracking/milestones.md
```

---

## 📊 Append-Only Pattern

**Key Insight**: If you only need to record progress, you never need to read the file!

### Traditional Approach (High Context Cost)
1. Read PROJECT_MASTER_TRACKER.md (1000 tokens)
2. Find relevant section
3. Edit section
4. Write file back

**Total Cost**: 1000+ tokens

### Append-Only Approach (Minimal Context Cost)
1. Append one line to progress.log (10 tokens)

**Total Cost**: 10 tokens
**Savings**: 99% reduction

---

## 📝 File Formats

### progress.log
```
2025-10-11: Phase 1 Complete - Session state management (.ai/ directory)
2025-10-11: Registered 2 NBA metrics tools (nba_win_shares, nba_box_plus_minus)
2025-10-10: Sprint 7 Complete - 18 ML tools implemented and tested
2025-10-09: Tool count: 88 → 90 (registered 2 tools)
```

**Format**: `YYYY-MM-DD: Brief description`
**Never Read**: Only append, use git log for history

### decisions.md
```markdown
## 2025-10-11: Adopted hierarchical session storage
Rationale: Reduce context usage by organizing by access frequency
Impact: 80-93% reduction in session token usage

## 2025-10-09: Split PROJECT_MASTER_TRACKER.md
Rationale: Single 670-line file too expensive to read repeatedly
Impact: 85-93% reduction in status check token usage
```

**Format**: Markdown headers with date
**Read When**: Reviewing architectural history

### milestones.md
```markdown
# Major Milestones

- **2025-10-11**: Phase 1 Complete - Session state management
- **2025-10-09**: 90 tools registered (all implemented tools now tracked)
- **2025-10-05**: Sprint 7 Complete - ML evaluation tools
- **2025-10-01**: FastMCP migration Phase 1 complete
```

**Format**: Bullet list with dates
**Read When**: Creating summaries or reporting

---

## 🎯 Design Principles

1. **Append-Only Logs**: Never read progress.log, only append
2. **Structured History**: Use git log for full history, logs for quick notes
3. **Minimal Context**: Each append costs ~10 tokens vs 1000+ for full file read
4. **Searchable**: Use `grep` on logs if you need to find specific entries
5. **Persistent**: Logs are git-tracked for permanent record

---

## 🔍 When to Use What

### Use progress.log (append-only)
- ✅ Daily progress updates
- ✅ Quick wins
- ✅ Tool registrations
- ✅ Bug fixes

### Use decisions.md
- ✅ Architectural decisions
- ✅ Framework choices
- ✅ Major refactorings
- ✅ API design changes

### Use milestones.md
- ✅ Sprint completions
- ✅ Phase completions
- ✅ Major feature launches
- ✅ Production deployments

### Use .ai/permanent/ (for detailed ADRs)
- ✅ Detailed architecture decision records
- ✅ Multi-option analysis
- ✅ Performance benchmarks
- ✅ Migration strategies

---

## 📈 Context Savings

| Operation | Old Way | New Way | Savings |
|-----------|---------|---------|---------|
| Daily update | 1000 tokens (read tracker) | 10 tokens (append log) | 99% |
| Weekly review | 1000 tokens | 150 tokens (read decisions) | 85% |
| Milestone log | 1000 tokens | 10 tokens (append) | 99% |

---

**Navigation**: [Project](../) | [Status](../status/) | [Metrics](../metrics/) | [Root](../../)
