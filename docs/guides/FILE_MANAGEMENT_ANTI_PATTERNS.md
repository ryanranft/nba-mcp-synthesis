# File Management Anti-Patterns

**Purpose**: Common mistakes in file creation and management with correct alternatives
**Audience**: Claude/AI sessions, developers
**Last Updated**: 2025-10-11
**Status**: Active reference

---

## 🎯 Overview

This guide documents common file management mistakes and shows correct alternatives. Following these patterns prevents:
- File proliferation (too many standalone files)
- Context bloat (duplicate information)
- Broken automation (editing auto-generated files)
- Poor discoverability (files not indexed)

**Golden Rule**: Always check [FILE_CREATION_DECISION_TREE.md](FILE_CREATION_DECISION_TREE.md) before creating any file.

---

## 🚨 Critical Anti-Patterns

### Anti-Pattern 1: Manually Editing Auto-Generated Files

**❌ WRONG**:
```bash
# Directly editing auto-generated file
vim .ai/current-session.md

# Making manual changes
echo "New task: Implement feature X" >> .ai/current-session.md
```

**✅ CORRECT**:
```bash
# Regenerate with script
./scripts/session_start.sh

# The script automatically includes latest git status, commits, and project state
```

**Why this is bad**:
- Breaks automation
- Manual edits get overwritten on next script run
- Loses optimization (scripts generate minimal context)
- Increases token cost 10-20x

**Auto-generated files to NEVER edit**:
- `.ai/current-session.md`
- `PROJECT_STATUS.md` (if using update_status.sh)
- Test/benchmark results
- Session checkpoints

**Token impact**: Manual edits can increase from 300 → 3,000+ tokens

---

### Anti-Pattern 2: Creating Standalone Status Update Files

**❌ WRONG**:
```bash
# Creating new status file for each update
vim STATUS_UPDATE_2025-10-11.md
vim TOOLS_REGISTRATION_UPDATE.md
vim PROGRESS_REPORT_2025-10-11.md
```

**✅ CORRECT**:
```bash
# Option 1: Append to progress log (for simple updates)
echo "2025-10-11: Registered 5 new tools in Sprint 5" >> project/tracking/progress.log

# Option 2: Edit specific section in status file
grep -n "Sprint 5" project/status/sprints.md  # Find line number
vim project/status/sprints.md +67  # Edit that section only

# Option 3: Update canonical location
vim project/status/tools.md  # Edit tool registration section
```

**Why this is bad**:
- File proliferation (1 file per day = 365 files/year)
- Duplicate information scattered across files
- Hard to find latest status
- Breaks canonical location principle

**Token impact**: 
- Wrong way: 100-500 tokens per standalone file × many files = thousands of tokens
- Right way: 10 tokens (append) or 50-100 tokens (edit section)

---

### Anti-Pattern 3: Reading Append-Only Logs

**❌ WRONG**:
```bash
# Reading the entire progress log before appending
cat project/tracking/progress.log  # 1,500 tokens!

# Then appending
echo "2025-10-11: New update" >> project/tracking/progress.log
```

**✅ CORRECT**:
```bash
# ONLY append, NEVER read
echo "$(date +%Y-%m-%d): New update" >> project/tracking/progress.log  # 10 tokens

# If you need to find something specific:
grep "Sprint 5" project/tracking/progress.log  # Search only
```

**Why this is bad**:
- Wastes 1,490 tokens reading what you don't need
- Log files grow continuously
- No benefit to reading before appending

**Append-only files**:
- `project/tracking/progress.log` - Daily progress
- `project/tracking/decisions.md` - Key decisions
- `project/tracking/milestones.md` - Major achievements

**Token impact**: 1,490 tokens wasted per unnecessary read

---

### Anti-Pattern 4: Creating Files Without Checking Canonical Location

**❌ WRONG**:
```bash
# Just creating a new file without checking
vim TOOL_REGISTRY_UPDATES.md

# Duplicating content that already exists elsewhere
vim NBA_METRICS_LIST.md  # When .ai/permanent/tool-registry.md already has this
```

**✅ CORRECT**:
```bash
# Step 1: Check if canonical location exists
grep -i "tool registry" docs/DOCUMENTATION_MAP.md

# Result shows: .ai/permanent/tool-registry.md is canonical location

# Step 2: Update existing file
vim .ai/permanent/tool-registry.md

# Step 3: If truly new content, check decision tree
# Follow all 8 steps before creating new file
```

**Why this is bad**:
- Duplicate information
- Multiple sources of truth
- Information becomes outdated in one place
- Hard to maintain consistency

**Always check first**:
1. `docs/DOCUMENTATION_MAP.md` - Canonical locations
2. `docs/guides/index.md` - Existing guides
3. `.ai/permanent/index.md` - Permanent references
4. `project/status/index.md` - Status files

**Token impact**: Duplicate content doubles token usage

---

### Anti-Pattern 5: Not Using Scripts When Available

**❌ WRONG**:
```bash
# Manually creating daily session file
vim .ai/daily/2025-10-11-session-1.md

# Manually writing structure
echo "# Session 2025-10-11" > .ai/daily/2025-10-11-session-1.md
echo "## Goals" >> .ai/daily/2025-10-11-session-1.md
# ... manually creating entire structure
```

**✅ CORRECT**:
```bash
# Use the script that creates from template
./scripts/session_start.sh --new-session

# Script automatically:
# - Uses template.md
# - Fills in date/session number
# - Creates proper structure
# - Ensures consistency
```

**Why this is bad**:
- Inconsistent format
- Miss template fields
- More work for same result
- Breaks patterns

**Scripts available**:
| Task | Script | Purpose |
|------|--------|---------|
| Start session | `./scripts/session_start.sh` | Generate current-session.md |
| Create daily log | `./scripts/session_start.sh --new-session` | From template |
| Archive files | `./scripts/auto_archive.sh` | Move completed docs |
| Update status | `./scripts/update_status.sh` | Regenerate STATUS |
| Create checkpoint | `./scripts/checkpoint_session.sh` | Save state |

**Token impact**: Manual creation = inconsistent format = harder to parse = more tokens

---

### Anti-Pattern 6: Generic or Unclear Filenames

**❌ WRONG**:
```bash
vim NOTES.md
vim TEMP.md
vim NEW_FILE.md
vim TODO.md
vim STUFF.md
vim MY_NOTES.md
```

**✅ CORRECT**:
```bash
# Use descriptive, searchable names
vim SPRINT_5_TOOL_REGISTRATION_NOTES.md
vim CONTEXT_OPTIMIZATION_TEMP_ANALYSIS.md
vim NBA_METRICS_IMPLEMENTATION_CHECKLIST.md

# Or better yet, use appropriate canonical location
vim .ai/daily/2025-10-11-session-1.md  # For temporary notes
echo "2025-10-11: Sprint 5 notes" >> project/tracking/progress.log  # For quick notes
```

**Why this is bad**:
- Can't find files later
- Can't search for content
- Unclear purpose
- Gets lost in clutter

**Naming conventions**:
- Use UPPER_CASE_WITH_UNDERSCORES.md
- Include topic: `TOPIC_SUBTOPIC_TYPE.md`
- Include dates if time-sensitive: `2025-10-11-session-1.md`
- Be specific: `NBA_PLAYER_EFFICIENCY_RATING.md` not `STATS.md`

---

### Anti-Pattern 7: Keeping Completion Documents in Root

**❌ WRONG**:
```bash
# Leaving completion documents in root directory
ls -la *.md
# Shows:
# SPRINT_5_COMPLETE.md
# SPRINT_6_COMPLETE.md
# VERIFICATION_COMPLETE.md
# IMPLEMENTATION_FINISHED.md
# ...20+ files in root
```

**✅ CORRECT**:
```bash
# Archive immediately after completion
./scripts/auto_archive.sh --interactive

# Or let weekly health check do it automatically
./scripts/weekly_health_check.sh

# Files move to: docs/archive/2025-10/completion/
```

**Why this is bad**:
- Clutters root directory
- Adds noise to searches
- Increases context usage
- Makes finding active docs harder

**Archive triggers** (automatic):
- Files matching `*_COMPLETE.md`
- Files matching `*_VERIFICATION*.md`
- Files matching `*_REPORT.md`
- Files matching `*_SUCCESS.md`, `*_DONE.md`, `*_FINISHED.md`

**Target**: Root directory should have <15 markdown files

---

### Anti-Pattern 8: Duplicating Content Instead of Cross-Referencing

**❌ WRONG**:
```markdown
<!-- In SPRINT_5_GUIDE.md -->
## Tool Registration Process
1. Create tool in mcp_server/tools/
2. Add Pydantic model in params.py
3. Register in fastmcp_server.py
4. Write tests
5. Update documentation
... (full 50-line process)

<!-- In SPRINT_6_GUIDE.md -->
## Tool Registration Process
1. Create tool in mcp_server/tools/
2. Add Pydantic model in params.py
... (same 50 lines repeated)

<!-- In DEVELOPER_GUIDE.md -->
## Tool Registration Process
... (same content again)
```

**✅ CORRECT**:
```markdown
<!-- In project/status/tools.md - CANONICAL LOCATION -->
## Tool Registration Process
1. Create tool in mcp_server/tools/
2. Add Pydantic model in params.py
3. Register in fastmcp_server.py
4. Write tests
5. Update documentation
... (full detailed process ONCE)

<!-- In SPRINT_5_GUIDE.md - CROSS-REFERENCE -->
## Tool Registration
See [Tool Registration Process](../project/status/tools.md#tool-registration-process) for complete steps.

<!-- In SPRINT_6_GUIDE.md - CROSS-REFERENCE -->
## Tool Registration
Follow the [Tool Registration Process](../project/status/tools.md#tool-registration-process).

<!-- In DEVELOPER_GUIDE.md - CROSS-REFERENCE -->
## Registering New Tools
Complete process: [Tool Registration](../../project/status/tools.md#tool-registration-process)
```

**Why this is bad**:
- Content gets out of sync
- Must update in multiple places
- Increases context 3-5x
- Maintenance nightmare

**Cross-reference patterns**:
```markdown
# Brief reference
See [Topic](path/to/canonical.md) for details.

# With context
For complete [Topic Name](path.md), including examples and troubleshooting.

# Inline reference
Follow the [Complete Guide](path.md) for step-by-step instructions.
```

**Token impact**: Duplicate content multiplies token usage by number of copies

---

### Anti-Pattern 9: Not Updating Index Files

**❌ WRONG**:
```bash
# Create new guide
vim docs/guides/NEW_FEATURE_GUIDE.md

# Commit and forget
git add docs/guides/NEW_FEATURE_GUIDE.md
git commit -m "Add new feature guide"

# Guide is now invisible to index navigation!
```

**✅ CORRECT**:
```bash
# Create new guide
vim docs/guides/NEW_FEATURE_GUIDE.md

# Update index
vim docs/guides/index.md
# Add: - **[New Feature Guide](NEW_FEATURE_GUIDE.md)** - Description

# Add to documentation map
vim docs/DOCUMENTATION_MAP.md
# Add canonical location entry

# Now properly discoverable
git add docs/guides/NEW_FEATURE_GUIDE.md docs/guides/index.md docs/DOCUMENTATION_MAP.md
git commit -m "docs: Add new feature guide with proper indexing"
```

**Why this is bad**:
- File is orphaned
- Not discoverable via indexes
- Breaks navigation system
- Defeats purpose of index-based approach

**Required updates when creating new file**:
1. Directory index (e.g., `docs/guides/index.md`)
2. `docs/DOCUMENTATION_MAP.md` (if guide or permanent reference)
3. Related documents (cross-references)
4. Parent indexes if nested

---

### Anti-Pattern 10: Reading Entire Files to Update Small Sections

**❌ WRONG**:
```bash
# Read entire 500-line file to update one section
cat project/status/tools.md  # 500 lines = 10,000 tokens

# Then edit one section
vim project/status/tools.md

# Wasted 9,900 tokens reading what you didn't need
```

**✅ CORRECT**:
```bash
# Find the specific section first
grep -n "Sprint 5 Tools" project/status/tools.md
# Output: 145:## Sprint 5 Tools

# Edit only that section
vim project/status/tools.md +145

# Or read just that section if needed
sed -n '145,175p' project/status/tools.md  # Read 30 lines only = 600 tokens
```

**Why this is bad**:
- Wastes context on unneeded content
- Slower to find what you need
- Increases token usage 10-20x

**Best practices**:
1. Use grep to find section: `grep -n "search term" file.md`
2. Jump to line: `vim file.md +LineNumber`
3. Read section only: `sed -n 'START,ENDp' file.md`
4. Never read full file unless necessary

**Token impact**: 
- Reading full 500-line file: ~10,000 tokens
- Reading 30-line section: ~600 tokens
- Savings: 94%

---

## ✅ Best Practices Summary

### Always DO ✅

1. **Check decision tree first** - Before creating any file
2. **Use scripts when available** - session_start.sh, auto_archive.sh, etc.
3. **Check canonical locations** - docs/DOCUMENTATION_MAP.md
4. **Cross-reference, don't duplicate** - Link to canonical source
5. **Update indexes** - Always update relevant index.md files
6. **Use descriptive names** - Clear, searchable filenames
7. **Append to logs** - Never read append-only files
8. **Archive completed work** - Keep root directory clean
9. **Edit specific sections** - Don't read entire files
10. **Follow naming conventions** - Consistent patterns

### Never DON'T ❌

1. ❌ **Never edit auto-generated files** - Use scripts instead
2. ❌ **Never read append-only logs** - Just append
3. ❌ **Never create standalone status files** - Use canonical locations
4. ❌ **Never skip index updates** - Always update indexes
5. ❌ **Never use generic filenames** - Be specific and descriptive
6. ❌ **Never duplicate content** - Cross-reference instead
7. ❌ **Never skip archive check** - Run auto_archive.sh regularly
8. ❌ **Never read full files** - Use grep/sed for sections
9. ❌ **Never create files without checking** - Follow decision tree
10. ❌ **Never ignore scripts** - Use automation when available

---

## 🎓 Learning Checklist

Before committing any changes, verify:

- [ ] Did I check if file is auto-generated?
- [ ] Did I use a script if available?
- [ ] Did I check for canonical location?
- [ ] Did I follow the 8-step decision tree?
- [ ] Did I use a descriptive filename?
- [ ] Did I update relevant indexes?
- [ ] Did I cross-reference instead of duplicate?
- [ ] Did I archive completed work?
- [ ] Did I avoid reading append-only logs?
- [ ] Did I edit only specific sections needed?

---

## 📊 Impact Summary

| Anti-Pattern | Token Cost | Correct Approach | Token Cost | Savings |
|--------------|------------|------------------|------------|---------|
| Edit auto-generated | 3,000+ | Use script | 300 | 90% |
| Read append-only log | 1,500 | Just append | 10 | 99% |
| Read full file | 10,000 | Read section | 600 | 94% |
| Duplicate content | 5,000 × N | Cross-reference | 50 | 99% |
| Create standalone | 500 × many | Use canonical | 50 | 90% |
| Skip archiving | +100/month | Auto-archive | 0 | 100% |

**Overall impact**: Following correct patterns saves 80-99% of token usage.

---

## 🔗 Related Documentation

- **[File Creation Decision Tree](FILE_CREATION_DECISION_TREE.md)** - When to create files
- **[File Management Policy](../.ai/permanent/file-management-policy.md)** - Complete policy
- **[Operations Guide](../../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Daily operations
- **[START HERE](../../START_HERE_FOR_CLAUDE.md)** - Quick start guide

---

**Last Updated**: 2025-10-11
**Version**: 1.0
**Status**: Active Reference

**Remember**: When in doubt, check the decision tree and use scripts first!

