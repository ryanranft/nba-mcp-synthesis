# File Creation Decision Tree

**Purpose**: Complete visual guide for when to use scripts vs. manual file creation
**Audience**: Claude/AI sessions, developers
**Last Updated**: 2025-10-11
**Status**: Active reference

---

## 🎯 Quick Reference

**Before creating ANY file, follow these steps in order:**

1. ⚠️ **Check if AUTO-GENERATED** → Use script, don't edit manually
2. 🔧 **Check for script** → Use script if available
3. 📋 **Check canonical location** → Update existing if found
4. 🌳 **Follow decision tree** → 7 steps below

---

## 🔍 Complete Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│ STEP 0: Is this file AUTO-GENERATED?                   │
│         ⚠️ CRITICAL CHECK - DO THIS FIRST              │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Use the generator script
                         │         Examples:
                         │         • .ai/current-session.md → ./scripts/session_start.sh
                         │         • PROJECT_STATUS.md → ./scripts/update_status.sh
                         │         • Test results → Run test script
                         │         
                         │         ❌ NEVER manually edit these files
                         │         ✅ Regenerate with script instead
                         │
                         └─ NO → Continue to Step 1
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Is there a script that creates this type?      │
│         🔧 Script-Based Creation                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Use the script
                         │         Available Scripts:
                         │         • Start session: ./scripts/session_start.sh
                         │         • Create daily log: ./scripts/session_start.sh --new-session
                         │         • Archive files: ./scripts/auto_archive.sh
                         │         • Update status: ./scripts/update_status.sh
                         │         • Archive sessions: ./scripts/session_archive.sh --to-s3
                         │         • Create checkpoint: ./scripts/checkpoint_session.sh
                         │
                         └─ NO → Continue to Step 2
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 2: Does canonical location exist?                 │
│         📋 Check docs/DOCUMENTATION_MAP.md              │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Update existing file (don't create new)
                         │         How to check:
                         │         grep -i "topic" docs/DOCUMENTATION_MAP.md
                         │
                         │         Examples:
                         │         • Tool info → Update .ai/permanent/tool-registry.md
                         │         • Status → Update project/status/*.md
                         │         • Decision → Append to project/tracking/decisions.md
                         │
                         └─ NO → Continue to Step 3
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 3: Is this temporary/session-specific?            │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Use: .ai/daily/YYYY-MM-DD-session-N.md
                         │         Location: .ai/daily/ (gitignored)
                         │         Format: Use template.md
                         │         Create with: ./scripts/session_start.sh --new-session
                         │
                         │         Examples:
                         │         • Today's work notes
                         │         • Debugging session
                         │         • Experimental ideas
                         │         • Meeting notes
                         │
                         └─ NO → Continue to Step 4
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 4: Is this a progress update or log entry?        │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Append to: project/tracking/progress.log
                         │         Format: "YYYY-MM-DD: Action taken"
                         │         
                         │         ❌ NEVER read this file
                         │         ✅ ONLY append to it
                         │
                         │         Examples:
                         │         echo "2025-10-11: Completed Sprint 5" >> project/tracking/progress.log
                         │         echo "2025-10-11: Fixed bug in tool X" >> project/tracking/progress.log
                         │
                         │         Token cost: 10 tokens (vs 1,500 if read)
                         │
                         └─ NO → Continue to Step 5
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 5: Is this current status information?            │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Edit specific section in project/status/*.md
                         │         Available files:
                         │         • project/status/tools.md - Tool registration
                         │         • project/status/sprints.md - Sprint progress
                         │         • project/status/features.md - Feature status
                         │         • project/status/blockers.md - Current blockers
                         │
                         │         Best practice:
                         │         • Find line number first: grep -n "section" file.md
                         │         • Edit only that section: vim file.md +45
                         │         • Don't read entire file
                         │
                         │         Token cost: 50-100 tokens (vs 1,000+ reading full file)
                         │
                         └─ NO → Continue to Step 6
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 6: Is this permanent reference material?          │
│         (decisions, architecture, tools)                │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Add to appropriate file in .ai/permanent/
                         │         Available files:
                         │         • tool-registry.md - Tool documentation
                         │         • file-management-policy.md - This policy
                         │         • context_budget.json - Budget configuration
                         │         • [create new] - For new reference types
                         │
                         │         After creating:
                         │         1. Update .ai/permanent/index.md
                         │         2. Add to docs/DOCUMENTATION_MAP.md
                         │         3. Link from related documents
                         │
                         │         Examples:
                         │         • Architecture decision → Create ADR using template.md
                         │         • New tool category → Add to tool-registry.md
                         │         • Best practice → Create new reference doc
                         │
                         └─ NO → Continue to Step 7
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 7: Is this a user guide or documentation?         │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Create in docs/guides/
                         │         Naming: DESCRIPTIVE_TOPIC_GUIDE.md
                         │         
                         │         Required steps:
                         │         1. Create file: vim docs/guides/NEW_TOPIC_GUIDE.md
                         │         2. Update index: vim docs/guides/index.md
                         │         3. Add to map: vim docs/DOCUMENTATION_MAP.md
                         │         4. Link from related docs
                         │
                         │         Examples:
                         │         • Setup guide → FEATURE_SETUP_GUIDE.md
                         │         • Usage guide → TOOL_USAGE_GUIDE.md
                         │         • Best practices → BEST_PRACTICES_GUIDE.md
                         │
                         └─ NO → Continue to Step 8
                                   │
┌─────────────────────────────────────────────────────────┐
│ STEP 8: Is this historical/completed work?             │
└─────────────────────────────────────────────────────────┘
                         │
                         ├─ YES → Archive to: docs/archive/YYYY-MM/
                         │         Method: Use ./scripts/auto_archive.sh
                         │         
                         │         Automatic triggers:
                         │         • Files matching *_COMPLETE.md
                         │         • Files matching *_VERIFICATION*.md
                         │         • Files matching *_REPORT.md
                         │         • Files not modified in 30+ days
                         │
                         │         Manual archive:
                         │         ./scripts/auto_archive.sh --interactive
                         │
                         │         After archiving:
                         │         1. Update docs/archive/YYYY-MM/index.md
                         │         2. Commit changes
                         │
                         └─ NO → RECONSIDER IF FILE IS NECESSARY
                                   │
                                   ├─ Can this be added to existing file?
                                   │  └─> Check DOCUMENTATION_MAP.md again
                                   │
                                   ├─ Is this a comment/note?
                                   │  └─> Use .ai/daily/session.md instead
                                   │
                                   └─ Still need new file?
                                      └─> Consult with team or create with caution
                                          • Use descriptive name
                                          • Update all indexes
                                          • Add to DOCUMENTATION_MAP.md
```

---

## 📝 Common Scenarios

### Scenario 1: "I want to record what I did today"

**Decision Path**: Step 4 (Progress update)

**Action**:
```bash
echo "$(date +%Y-%m-%d): Completed task X" >> project/tracking/progress.log
```

**Why**: Append-only log, never read it. Saves 1,490 tokens.

---

### Scenario 2: "I completed a sprint"

**Decision Path**: Step 8 (Historical/completed)

**Action**:
```bash
# If you created SPRINT_X_COMPLETE.md
./scripts/auto_archive.sh --interactive
```

**Why**: Completion documents should be archived immediately.

---

### Scenario 3: "I need to update tool registration status"

**Decision Path**: Step 5 (Current status)

**Action**:
```bash
# Find the section
grep -n "Tool Registration" project/status/tools.md

# Edit that section only
vim project/status/tools.md +45
```

**Why**: Edit specific section, don't read entire file. Saves 900+ tokens.

---

### Scenario 4: "I want to create a new guide"

**Decision Path**: Step 2 → Step 7

**Action**:
```bash
# First check if it exists
grep -i "guide topic" docs/DOCUMENTATION_MAP.md

# If not found, create new guide
vim docs/guides/NEW_TOPIC_GUIDE.md
vim docs/guides/index.md  # Update index
vim docs/DOCUMENTATION_MAP.md  # Add to map
```

**Why**: Ensure it's not duplicate, properly index it.

---

### Scenario 5: "I'm starting a new session"

**Decision Path**: Step 0 → Step 1

**Action**:
```bash
./scripts/session_start.sh
cat .ai/current-session.md
```

**Why**: current-session.md is AUTO-GENERATED. Never edit manually.

---

## 🚨 Common Mistakes to Avoid

### Mistake 1: Manually Editing Auto-Generated Files

**❌ DON'T**:
```bash
vim .ai/current-session.md  # Edit manually
```

**✅ DO**:
```bash
./scripts/session_start.sh  # Regenerate
```

**Impact**: Breaking automation, increasing context 10x.

---

### Mistake 2: Reading Append-Only Logs

**❌ DON'T**:
```bash
cat project/tracking/progress.log  # 1,500 tokens!
echo "2025-10-11: Update" >> project/tracking/progress.log
```

**✅ DO**:
```bash
echo "$(date +%Y-%m-%d): Update" >> project/tracking/progress.log  # 10 tokens
```

**Impact**: Wasting 1,490 tokens on unnecessary reading.

---

### Mistake 3: Creating Standalone Documents

**❌ DON'T**:
```bash
vim STATUS_UPDATE_2025-10-11.md  # New standalone file
```

**✅ DO**:
```bash
vim project/status/tools.md +45  # Edit existing section
# OR
echo "2025-10-11: Update" >> project/tracking/progress.log
```

**Impact**: File proliferation, duplicate information.

---

### Mistake 4: Not Using Scripts When Available

**❌ DON'T**:
```bash
vim .ai/daily/2025-10-11-session-1.md  # Create manually
```

**✅ DO**:
```bash
./scripts/session_start.sh --new-session  # Use script
```

**Impact**: Inconsistent format, missing template structure.

---

## ✅ Best Practices Checklist

Before creating ANY file, verify:

- [ ] **Step 0**: Checked if AUTO-GENERATED (use script instead)
- [ ] **Step 1**: Checked for existing script (use if available)
- [ ] **Step 2**: Checked DOCUMENTATION_MAP.md (update existing if found)
- [ ] **Step 3-8**: Followed decision tree completely
- [ ] **After creation**: Updated relevant index files
- [ ] **After creation**: Added to DOCUMENTATION_MAP.md (if guide)
- [ ] **After creation**: Used descriptive, searchable filename
- [ ] **After creation**: No duplicate content (cross-referenced instead)

---

## 📊 Token Cost Summary

| Approach | Tokens | Savings |
|----------|--------|---------|
| Use auto-generated (Step 0) | 300 | 94% (vs 5,000) |
| Use script (Step 1) | 10-300 | 90-95% |
| Append-only log (Step 4) | 10 | 99% (vs 1,500) |
| Edit specific section (Step 5) | 50-100 | 90% (vs 1,000) |
| Archive completed (Step 8) | 0 | 100% (removed from context) |

**Overall impact**: 80-93% reduction in context usage when following this decision tree.

---

## 🔗 Related Documentation

- **[File Management Policy](.ai/permanent/file-management-policy.md)** - Complete policy
- **[Operations Guide](../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Daily operations
- **[Documentation Map](../DOCUMENTATION_MAP.md)** - Canonical locations
- **[START HERE](../../START_HERE_FOR_CLAUDE.md)** - Quick start guide

---

**Last Updated**: 2025-10-11
**Version**: 1.0
**Status**: Active Reference

**Remember**: When in doubt, check if there's a script first!

