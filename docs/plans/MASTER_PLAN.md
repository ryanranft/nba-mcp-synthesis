# Master Plan Index

**Last Updated**: 2025-10-11
**Version**: 1.0

---

## 📋 Purpose

This master plan index serves as the **single source of truth** for all project planning. It references detailed plans stored in the `detailed/` subdirectory and provides instructions for managing plans consistently.

---

## 🎯 Current Active Plans

### 1. NBA MCP Server Improvement Plan
- **File**: [`detailed/NBA_MCP_IMPROVEMENT_PLAN.md`](detailed/NBA_MCP_IMPROVEMENT_PLAN.md)
- **Status**: Active
- **Version**: 3.0
- **Last Verified**: 2025-10-11
- **Purpose**: Comprehensive improvement plan for NBA MCP server based on analysis of 8 MCP repositories
- **Scope**: Sprints 5-8 (completed) + Phase 9 (pending)

**Current Progress**:
- ✅ 90 MCP tools registered (all implemented tools now registered)
- ✅ 20/20 Sprint 5 NBA metrics tools registered (Phase 9A complete)
- ❌ 0/3 Sprint 6 web scraping tools
- ⚠️ 2/7 Sprint 7 prompts + 3 additional prompts (5 total)
- ❌ 0/6 Sprint 7 resources (4 other resources exist)
- **Overall**: 86% complete (90/104 tools/features)

---

## 📁 Plan Organization

All detailed plans are stored in the `detailed/` subdirectory. This master index provides:
1. **Quick Reference**: Summary of each plan's status
2. **Links**: Direct links to detailed plans
3. **Progress Tracking**: High-level completion metrics
4. **Update History**: When plans were last verified

---

## 📝 How to Create a New Plan

When creating a new plan document, follow these steps:

### Step 1: Create the Detailed Plan File

Create your plan in the `detailed/` subdirectory:

```bash
# Example
touch docs/plans/detailed/NEW_FEATURE_PLAN.md
```

### Step 2: Use the Plan Template

Every plan should include these sections:

```markdown
# [Feature/Project Name] - Plan

**Date**: YYYY-MM-DD
**Version**: 1.0
**Status**: Active | Draft | Completed | Archived

---

## Executive Summary

Brief overview (2-3 paragraphs) of what this plan covers.

## Objectives

- Objective 1
- Objective 2
- Objective 3

## Current Status

What has been completed, what's pending, what's blocked.

## Detailed Plan

### Phase 1: [Name]
- Tasks
- Timeline
- Dependencies

### Phase 2: [Name]
- Tasks
- Timeline
- Dependencies

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Testing Strategy

How will we verify this works?

## Deployment Plan

How will this be rolled out?

## Rollback Plan

What if something goes wrong?

## Verification Checklist

Use this to verify completion:
- [ ] Feature 1 implemented
- [ ] Feature 2 tested
- [ ] Documentation updated
- [ ] Tests passing
```

### Step 3: Add Entry to Master Index

Add a new section to this master index under "Current Active Plans":

```markdown
### [N]. [Plan Name]
- **File**: [`detailed/FILENAME.md`](detailed/FILENAME.md)
- **Status**: Active | Draft | Completed | Archived
- **Version**: X.Y
- **Last Verified**: YYYY-MM-DD
- **Purpose**: Brief description
- **Scope**: What it covers

**Current Progress**:
- ✅ Completed item 1
- ⚠️ In progress item 2
- ❌ Not started item 3
- **Overall**: X% complete (Y/Z items)
```

### Step 4: Commit the Changes

```bash
git add docs/plans/MASTER_PLAN.md docs/plans/detailed/NEW_FEATURE_PLAN.md
git commit -m "docs: Add [Feature Name] plan"
```

---

## 🔄 How to Update a Plan

When updating an existing plan:

### Step 1: Update the Detailed Plan

Edit the plan file in `detailed/` subdirectory:

```bash
# Example
vim docs/plans/detailed/NBA_MCP_IMPROVEMENT_PLAN.md
```

Make your changes:
1. Update the **Version** number (increment patch for corrections, minor for new sections, major for complete rewrites)
2. Update the **Date** to today's date
3. Update the **Status** section with current progress
4. Add changes to relevant sections

### Step 2: Update This Master Index

Update the corresponding entry in this file:
1. Update **Last Verified** date
2. Update **Version** number
3. Update **Current Progress** metrics
4. Update **Status** if changed (Active → Completed, etc.)

### Step 3: Commit the Changes

```bash
git add docs/plans/MASTER_PLAN.md docs/plans/detailed/[FILENAME].md
git commit -m "docs: Update [Plan Name] - [brief description of changes]"
```

---

## ✅ How to Mark Tasks as Complete

When marking tasks as complete, **always verify first**:

### Verification Requirements

**DO NOT** mark a task as complete unless you have:

1. **Verified the implementation exists** - Check actual code files
2. **Verified it's registered/deployed** - Not just implemented but accessible
3. **Verified it works** - Run tests or manual verification
4. **Checked for edge cases** - Is it production-ready?

### Verification Process

```bash
# 1. Find the actual implementation
grep -r "function_name\|class_name" mcp_server/

# 2. Check if it's registered (for MCP tools)
grep "@mcp.tool()" mcp_server/fastmcp_server.py | grep -i "function_name"

# 3. Verify tests exist and pass
pytest tests/test_feature.py -v

# 4. Check documentation
grep -r "feature_name" docs/
```

### Update Process

1. **Update the detailed plan** - Mark checkboxes as `- [x]` and add verification notes
2. **Update this master index** - Update progress metrics
3. **Create verification report** - Document what was verified and how
4. **Commit all changes** together

Example commit:
```bash
git commit -m "docs: Mark [Feature] as complete with verification

- Verified implementation in [file:line]
- Confirmed registration in [file:line]
- Tests passing: [test files]
- Documentation updated: [doc files]"
```

---

## 🔍 Verification Best Practices

### For MCP Tools

```bash
# Count registered tools
grep -c "@mcp.tool()" mcp_server/fastmcp_server.py

# List all tool names
grep -B 1 "@mcp.tool()" mcp_server/fastmcp_server.py | grep "^async def " | sed 's/async def //' | sed 's/(.*$//'

# Verify specific tool
grep -A 10 "@mcp.tool()" mcp_server/fastmcp_server.py | grep -A 10 "async def tool_name"
```

### For Features

```bash
# Check if file exists
ls -la mcp_server/tools/feature_helper.py

# Check if feature is imported
grep "from mcp_server.tools.feature_helper import" mcp_server/

# Check test coverage
pytest tests/ -v | grep feature

# Check documentation
find docs/ -name "*.md" -exec grep -l "feature_name" {} \;
```

### For Dependencies

```bash
# Check if dependency is installed
pip show package-name

# Check if dependency is in requirements
grep "package-name" requirements.txt

# Check if dependency is imported
grep "import package_name\|from package_name" mcp_server/
```

---

## 📊 Plan Status Definitions

- **Draft**: Plan is being written, not yet approved
- **Active**: Plan is approved and work is in progress
- **Completed**: All tasks from the plan are done and verified
- **Archived**: Plan is no longer relevant (superseded or cancelled)
- **On Hold**: Plan is paused, waiting for dependencies or decisions

---

## 🗄️ Archived Plans

Completed or superseded plans should be moved to `detailed/archive/`:

```bash
mv docs/plans/detailed/OLD_PLAN.md docs/plans/detailed/archive/
```

Update this master index to reflect the archival:

```markdown
### [Plan Name] (ARCHIVED)
- **File**: [`detailed/archive/FILENAME.md`](detailed/archive/FILENAME.md)
- **Status**: Archived
- **Archived Date**: YYYY-MM-DD
- **Reason**: Completed | Superseded by [other plan] | Cancelled
```

---

## 🎯 Current Sprint Status

See [`PROJECT_MASTER_TRACKER.md`](../../PROJECT_MASTER_TRACKER.md) for real-time progress tracking.

---

## 📝 Change Log

### Version 1.0 - 2025-10-11
- Initial master plan index created
- Added NBA MCP Improvement Plan (v3.0)
- Established plan management procedures
- Created verification guidelines

---

## 🤝 Contributing

When adding or updating plans:

1. **Always verify before marking complete** - No assumptions!
2. **Keep the master index updated** - It's the single source of truth
3. **Use semantic versioning** - Major.Minor.Patch
4. **Document verification steps** - How did you confirm it works?
5. **Link to evidence** - File names, line numbers, test results
6. **Update progress metrics** - Keep percentages accurate
7. **Commit changes together** - Master index + detailed plan + verification report

---

**Remember**: This master index exists to prevent confusion about what's been done. Always verify, never assume!