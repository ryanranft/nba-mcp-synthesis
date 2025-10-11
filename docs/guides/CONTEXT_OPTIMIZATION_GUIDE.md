# Context Optimization Guide

**Date**: 2025-10-11
**Purpose**: Strategies to optimize Claude Code resource usage and avoid auto context compaction

---

## 📋 Overview

This guide provides best practices for working efficiently with Claude Code to minimize context usage and avoid hitting context limits that trigger auto-compaction.

---

## ⚠️ Why Context Optimization Matters

**Context Limits**: Claude Code has a maximum context window (typically 200K tokens). When you approach this limit:
- Auto context compaction occurs, losing conversation history
- You lose continuity mid-task
- Progress tracking and todos may be lost
- Performance degrades

**Benefits of Optimization**:
- Longer, uninterrupted work sessions
- Better context retention across complex tasks
- Improved AI responses with full history available
- Smoother multi-file editing workflows

---

## 🎯 Key Strategies

### 1. Document Organization

#### ✅ DO:
- **Keep root directory clean** - Only essential files (README, CHANGELOG, PROJECT_MASTER_TRACKER)
- **Use docs/ hierarchy** - Organize into `/guides/`, `/sprints/`, `/tracking/`, `/planning/`
- **Remove duplicates** - Maintain single source of truth for each document
- **Archive old files** - Move completed sprint docs to `/docs/sprints/completed/`
- **Small, focused files** - Break large documents into smaller, logical sections

#### ❌ DON'T:
- Keep 50+ markdown files in root directory
- Duplicate files across root and docs/
- Create massive single-file documentation (10K+ lines)
- Leave temporary/session files in tracked locations

**Example Structure**:
```
project/
├── README.md (overview only, ~300 lines)
├── PROJECT_MASTER_TRACKER.md (current status, ~700 lines)
├── CHANGELOG.md (version history)
└── docs/
    ├── guides/ (user-facing docs)
    ├── sprints/completed/ (sprint history)
    ├── tracking/ (progress logs)
    └── plans/detailed/ (planning docs)
```

### 2. File Reading Strategy

#### ✅ DO:
- **Read selectively** - Only read files you need for current task
- **Use line limits** - Read first N lines of large files when exploring
- **Use grep/glob first** - Search before reading to find relevant files
- **Read incrementally** - Read sections of large files as needed

#### ❌ DON'T:
- Read entire codebase "just in case"
- Re-read files you've already examined
- Read large generated files (logs, test outputs, compiled assets)
- Read every file in a directory without filtering

**Example**:
```bash
# Good: Targeted search first
grep -l "nba_win_shares" mcp_server/**/*.py
# Then read only the relevant file

# Bad: Reading blindly
read mcp_server/**/*.py  # Reads everything!
```

### 3. Code Changes Strategy

#### ✅ DO:
- **Plan before editing** - Know what needs to change
- **Edit existing files** - Use Edit tool for modifications
- **Batch related changes** - Group logically related edits together
- **Test incrementally** - Verify small changes before proceeding

#### ❌ DON'T:
- Rewrite entire files when only small changes needed
- Create new files when editing existing ones would work
- Make changes without reading the file first
- Generate large code blocks in chat (use Write tool instead)

### 4. Test & Verification Strategy

#### ✅ DO:
- **Write focused tests** - Test only what you just implemented
- **Use existing test patterns** - Follow project conventions
- **Run specific tests** - `pytest tests/test_specific.py` not `pytest tests/`
- **Capture key outputs** - Save test results to files for reference

#### ❌ DON'T:
- Run entire test suite for every change
- Generate verbose test output to console
- Re-test unchanged functionality repeatedly
- Include full test outputs in conversation

**Example**:
```bash
# Good: Focused testing
python scripts/test_new_nba_metrics.py > test_results/nba_metrics_test.log
# Review log file later if needed

# Bad: Verbose output in chat
python scripts/test_all_features.py --verbose  # 1000s of lines of output
```

### 5. Documentation Strategy

#### ✅ DO:
- **Update in place** - Edit existing docs rather than creating new ones
- **Use references** - Link to detailed docs instead of duplicating content
- **Keep summaries concise** - 1-2 paragraphs, not pages
- **Version control** - Update "Last Updated" dates

#### ❌ DON'T:
- Create new summary docs for every session
- Duplicate information across multiple docs
- Include full code listings in documentation
- Generate massive "comprehensive" guides

**Example**:
```markdown
# Good: Concise with reference
## NBA Metrics Tools
15 NBA metrics tools available. See [ADVANCED_ANALYTICS_GUIDE.md](../ADVANCED_ANALYTICS_GUIDE.md) for details.

# Bad: Everything inline
## NBA Metrics Tools
[50 pages of detailed documentation...]
```

### 6. Planning & Tracking Strategy

#### ✅ DO:
- **Use TodoWrite tool** - Track progress with compact todo lists
- **Single master tracker** - One source of truth (PROJECT_MASTER_TRACKER.md)
- **Incremental updates** - Update progress as you go
- **Archive completed plans** - Move to archive/ when done

#### ❌ DON'T:
- Create separate tracking docs for each session
- Duplicate status across multiple trackers
- Keep all historical versions in active directories
- Write long prose updates (use bullet points)

### 7. Git Operations Strategy

#### ✅ DO:
- **Commit frequently** - Small, focused commits
- **Clear commit messages** - Describe what changed
- **Batch related changes** - Commit logically grouped changes together
- **Use git status wisely** - Check status before reading all changed files

#### ❌ DON'T:
- Wait to commit until end of session
- Commit unrelated changes together
- Generate full git diffs in conversation
- Read every modified file before committing

---

## 📊 Context Usage Estimates

Based on typical Claude Code operations:

| Operation | Approximate Token Cost | Notes |
|-----------|----------------------|-------|
| Read 100-line file | ~150 tokens | Efficient |
| Read 1000-line file | ~1500 tokens | Moderate |
| Read 5000-line file | ~7500 tokens | High |
| Edit file | ~200 tokens | Efficient (only changed section) |
| Write new file (500 lines) | ~750 tokens | Moderate |
| Run bash command | ~50 tokens | Very efficient |
| Grep search | ~100 tokens | Efficient |
| Git status | ~50-200 tokens | Depends on changes |
| Test output (verbose) | ~1000-5000 tokens | Can be very high |

**Target**: Keep per-task operations under 10K tokens to maintain good context headroom.

---

## 🔧 Practical Workflows

### Workflow 1: Registering New MCP Tools (Low Context)

1. **Plan** (TodoWrite) - ~100 tokens
2. **Read params.py** (relevant section) - ~300 tokens
3. **Edit params.py** (add param model) - ~200 tokens
4. **Read fastmcp_server.py** (relevant section) - ~500 tokens
5. **Edit fastmcp_server.py** (add tool) - ~300 tokens
6. **Test** (focused test script) - ~400 tokens
7. **Update tracker** - ~200 tokens
8. **Commit** - ~100 tokens

**Total**: ~2,100 tokens per tool ✅

### Workflow 2: Large Refactoring (High Context - Avoid if Possible)

1. **Read entire codebase** - ~50,000 tokens ❌
2. **Read all related files** - ~20,000 tokens ❌
3. **Generate new implementations** - ~10,000 tokens ❌
4. **Full test suite** - ~10,000 tokens ❌
5. **Comprehensive documentation** - ~5,000 tokens ❌

**Total**: ~95,000 tokens (half your context!) ❌

**Better Alternative**: Break into smaller tasks, each < 10K tokens ✅

---

## 💡 Emergency Context Management

If you're approaching context limits mid-session:

### Immediate Actions:
1. **Commit current work** - Save progress to git
2. **Summarize state** - Create brief summary document
3. **Archive outputs** - Save test results, logs to files
4. **Start fresh session** - Reference summary document

### Prevention:
- Monitor token usage (shown in tool results)
- Break large tasks into smaller subtasks
- Commit frequently (every 30 minutes of work)
- Use external files for large outputs

---

## 📈 Success Metrics

### Good Session (Low Context Usage):
- Completed 2-5 focused tasks
- Total context usage: 15K-30K tokens
- Clear history and continuity maintained
- No auto-compaction needed

### Concerning Session (High Context):
- Attempted 10+ tasks
- Total context usage: 80K+ tokens
- Multiple file rewrites
- Approaching compaction threshold

---

## 🎓 Best Practices Summary

1. **Think before reading** - What do you actually need to see?
2. **Edit, don't rewrite** - Preserve context with targeted changes
3. **Test selectively** - Verify only what changed
4. **Document concisely** - Use references, not repetition
5. **Commit frequently** - Save progress and free mental model
6. **Use tools wisely** - Grep/Glob before Read, Edit before Write
7. **Break down tasks** - Small, focused changes over large refactorings
8. **Archive aggressively** - Keep active workspace clean

---

## 📚 Related Documents

- [PROJECT_MASTER_TRACKER.md](../../PROJECT_MASTER_TRACKER.md) - Single source of truth for progress
- [MASTER_PLAN.md](../plans/MASTER_PLAN.md) - Planning guidelines
- [README.md](../../README.md) - Project overview

---

**Last Updated**: 2025-10-11
**Author**: NBA MCP Development Team
**Version**: 1.0