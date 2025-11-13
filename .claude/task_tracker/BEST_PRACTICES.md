# Task Tracker - Best Practices

**Proven patterns for effective task management in Claude Code.**

---

## Table of Contents

1. [When to Create Master Tasks](#when-to-create-master-tasks)
2. [Hierarchy Structure](#hierarchy-structure)
3. [Naming Conventions](#naming-conventions)
4. [Status Management](#status-management)
5. [Priority Guidelines](#priority-guidelines)
6. [Archive Strategies](#archive-strategies)
7. [Session Management](#session-management)
8. [Tag Organization](#tag-organization)
9. [Bulk Operations](#bulk-operations)
10. [Common Anti-Patterns](#common-anti-patterns)

---

## When to Create Master Tasks

### ✅ DO Create Master Tasks For:

**Multi-phase projects (3+ steps):**
```
Master Task: "User Authentication System"
├─ Design database schema
├─ Implement OAuth integration
├─ Write integration tests
├─ Deploy to staging
└─ Deploy to production
```

**Feature development:**
```
Master Task: "Dashboard with Analytics"
├─ Design wireframes
├─ Implement data visualization
├─ Add filters and search
├─ Export functionality
└─ Performance optimization
```

**Bug fix sprints:**
```
Master Task: "Q4 Critical Bugs"
├─ Fix login timeout issue
├─ Resolve dashboard crash
├─ Address export formatting
└─ Fix mobile responsiveness
```

**Research projects:**
```
Master Task: "Evaluate ML frameworks"
├─ Literature review
├─ Prototype with PyTorch
├─ Prototype with TensorFlow
├─ Benchmark performance
└─ Write recommendation report
```

### ❌ DON'T Create Master Tasks For:

**Single-step tasks:**
```
❌ Bad: Master Task "Fix typo in README"
✅ Good: Task "Fix typo in README" (no master needed)
```

**Unrelated tasks:**
```
❌ Bad: Master Task "Misc work"
     ├─ Fix login bug
     ├─ Update dashboard
     └─ Review PR #123

✅ Good: Create separate tasks or separate master tasks by theme
```

**Temporary experiments:**
```
❌ Bad: Master Task "Try different approaches"
✅ Good: Task "Spike: evaluate 3 approaches for caching"
```

---

## Hierarchy Structure

### Recommended Depth Levels

**Level 0: Individual tasks** (no parent)
- Use for standalone work
- Examples: "Fix typo", "Update dependency"

**Level 1: Master task with direct subtasks**
```
Master Task (depth 0)
├─ Subtask (depth 1)
├─ Subtask (depth 1)
└─ Subtask (depth 1)
```

**Level 2: Grouped subtasks** (best for complex projects)
```
Master Task: "E-commerce Platform" (depth 0)
├─ Phase 1: User Management (depth 1)
│   ├─ Registration flow (depth 2)
│   ├─ Login/logout (depth 2)
│   └─ Password reset (depth 2)
├─ Phase 2: Product Catalog (depth 1)
│   ├─ Product listing (depth 2)
│   ├─ Search and filters (depth 2)
│   └─ Product details (depth 2)
└─ Phase 3: Checkout (depth 1)
    ├─ Shopping cart (depth 2)
    ├─ Payment integration (depth 2)
    └─ Order confirmation (depth 2)
```

**Level 3+: Use sparingly**
- Only for very complex, long-running projects
- Consider splitting into multiple master tasks instead

### Structuring Guidelines

**Group by phase/stage:**
```
Master: "Launch MVP"
├─ Phase 1: Core Features
├─ Phase 2: Polish & Testing
└─ Phase 3: Deployment
```

**Group by component:**
```
Master: "Microservices Refactor"
├─ Frontend Service
├─ Backend API
├─ Database Layer
└─ Deployment Pipeline
```

**Group by functionality:**
```
Master: "Admin Dashboard"
├─ User Management
├─ Analytics & Reporting
├─ Settings & Configuration
└─ Audit Logging
```

---

## Naming Conventions

### Master Task Names

**Be specific and descriptive:**
```
✅ "Implement OAuth 2.0 authentication with Google"
✅ "Migrate PostgreSQL database to AWS RDS"
✅ "Build real-time chat feature with WebSockets"

❌ "Auth stuff"
❌ "Database work"
❌ "New feature"
```

**Use action verbs:**
```
✅ "Build", "Implement", "Migrate", "Refactor", "Optimize"
✅ "Design", "Research", "Evaluate", "Deploy", "Fix"

❌ "Auth", "Database", "Dashboard" (nouns without action)
```

**Include key technology/scope:**
```
✅ "Implement Redis caching for API endpoints"
✅ "Migrate from REST to GraphQL API"
✅ "Build CI/CD pipeline with GitHub Actions"
```

### Subtask Names

**Be concise but clear:**
```
✅ "Design database schema"
✅ "Write integration tests"
✅ "Deploy to staging environment"

❌ "Do the database thing"
❌ "Tests"
❌ "Deploy"
```

**Use consistent phrasing within a project:**
```
✅ Consistent:
   ├─ "Implement user registration"
   ├─ "Implement password reset"
   └─ "Implement email verification"

❌ Inconsistent:
   ├─ "Implement user registration"
   ├─ "Password reset feature"
   └─ "Email stuff"
```

---

## Status Management

### Status Lifecycle

```
pending → in_progress → completed
                    ↓
                 blocked
                    ↓
              (resolved) → in_progress → completed
```

### Status Guidelines

**pending**
- Default for new tasks
- Not yet started
- Waiting to be picked up

**in_progress**
- **IMPORTANT: Only one task in_progress at a time per project**
- Actively working on this task
- Update to in_progress when you start work

**completed**
- Task is 100% done
- Code merged, tests passing
- Deployed (if applicable)

**blocked**
- Cannot proceed without external input
- Always include blocker reason in notes
- Use `/block` command for clarity

**cancelled**
- Task no longer needed
- Requirements changed
- Decided not to pursue

### The "One In-Progress Rule"

**✅ GOOD: One active task per project**
```
Master: "Dashboard Feature"
├─ ✅ Design mockups (completed)
├─ 🔄 Implement charts (in_progress) ← Working on this
├─ ⏸️  Add filters (pending)
└─ ⏸️  Write tests (pending)
```

**❌ BAD: Multiple in-progress tasks**
```
Master: "Dashboard Feature"
├─ ✅ Design mockups (completed)
├─ 🔄 Implement charts (in_progress) ← Which one?
├─ 🔄 Add filters (in_progress) ← Are you working on?
└─ ⏸️  Write tests (pending)
```

**Why?**
- Clear session resumption
- Prevents context switching
- Shows exact progress
- Better velocity tracking

---

## Priority Guidelines

### Priority Levels

**critical** - Production outage, data loss, security issue
```
- Production API down
- Database corruption detected
- Security vulnerability disclosed
- User-facing crash affecting all users
```

**high** - Important for current sprint/milestone
```
- Sprint commitments
- Deadline-driven features
- High-impact bugs
- Customer-requested features
```

**medium** - Normal priority, default for most work
```
- Regular feature development
- Tech debt improvements
- Non-critical bugs
- Documentation updates
```

**low** - Nice to have, can be deferred
```
- Future enhancements
- Refactoring opportunities
- Experimental features
- Minor UI improvements
```

### Priority Assignment Best Practices

**Start with medium by default:**
```
When creating tasks, use medium unless there's a clear reason to change.
```

**Adjust during sprint planning:**
```bash
# Elevate this week's work
/bulk-priority high <this week's task IDs> confirm

# Lower priority for next sprint
/bulk-priority low <next sprint task IDs> confirm
```

**Re-prioritize when blockers resolve:**
```bash
# Blocker cleared, make it high priority
/bulk-priority high 45 46 47 confirm Blocker resolved, prioritizing
```

**Use critical sparingly:**
```
Only 5-10% of tasks should be critical.
If everything is critical, nothing is critical.
```

---

## Archive Strategies

### When to Archive

**After project completion:**
```bash
# Archive completed tasks older than 30 days
/archive 30
```

**Quarterly cleanup:**
```bash
# Archive tasks older than 90 days
/archive 90

# Review what will be archived first
/archive 90  # Preview mode
/archive confirm 90  # Execute
```

**Sprint end:**
```bash
# Archive completed tasks from sprint
/archive 14  # Two weeks ago
```

### What to Archive

**✅ DO Archive:**
- Completed tasks older than 30+ days
- Cancelled tasks
- Experiments that didn't pan out
- Old bug fixes (keep for history, not active view)

**❌ DON'T Archive:**
- Pending or in-progress tasks
- Recent completed work (<30 days)
- Master tasks with incomplete subtasks
- Tasks you reference frequently

### Archive Retention

**Recommended retention periods:**
- **Recent completed:** Keep 30 days
- **Normal completed:** Keep 90 days
- **Important projects:** Keep 180 days
- **Reference projects:** Never archive

**Custom retention by tag:**
```bash
# Archive by tag
/archive 60 tag:experiment    # Archive old experiments
/archive 180 tag:production   # Keep production work longer
```

---

## Session Management

### Start-of-Session Ritual

**Every session, do this:**

```bash
1. /resume                    # See all active projects
2. Choose what to work on     # Based on staleness/priority
3. Get task hierarchy         # Understand context
4. Mark task in_progress      # Signal you're working on it
```

**Example flow:**
```bash
User: /resume

Claude: Shows 3 projects:
  #1: Dashboard (78% complete, ✨ active)
  #2: OAuth (45% complete, 🟡 warning - 4 days stale)
  #3: Bug Fixes (12% complete, 🔴 STALE - 9 days)

User: "Continue OAuth work"

Claude: [Gets hierarchy, shows OAuth task #47 is in_progress]

User: /complete 47 OAuth integration finished
      /tasks by-project 2
      [Pick next task...]
```

### End-of-Session Practice

**Before ending your session:**

1. **Complete finished tasks:**
   ```bash
   /bulk-complete 45 46 47 confirm
   ```

2. **Update context if switching projects:**
   ```python
   # Update master task summary
   update_context_summary(
       task_id=50,
       context_summary="OAuth working, testing with Google provider next"
   )
   ```

3. **For complex multi-day work, consider a HANDOFF:**
   Create `HANDOFF_OAUTH.md` in project root with:
   - What you accomplished
   - What's next
   - Any blockers or decisions needed

### Switching Projects Mid-Session

**Best practice:**

```bash
# Mark current work with note
/complete 47 Switching to urgent bug fix, will resume later

# Switch to new project
/resume 3

# Work on new project
...

# Return to original project
/resume 2
```

---

## Tag Organization

### Tagging Strategy

**Use tags for cross-cutting concerns:**

**By category:**
```
bug, feature, enhancement, refactoring, documentation, test
```

**By component:**
```
frontend, backend, database, api, ui, infra
```

**By sprint/milestone:**
```
sprint-15, q4-2025, mvp, v2.0
```

**By technology:**
```
react, python, postgres, docker, aws
```

**By status:**
```
needs-review, blocked-external, waiting-qa, ready-to-deploy
```

### Bulk Tagging

**Tag related tasks:**
```bash
# Tag all sprint tasks
/bulk-add-tags [45, 46, 47, 48] ["sprint-15", "backend"]

# Tag by component
/bulk-add-tags [101, 102, 103] ["frontend", "react", "ui"]

# Tag blockers
/bulk-add-tags [50, 51] ["blocked", "waiting-api-keys"]
```

### Tag Naming Conventions

**Use lowercase with hyphens:**
```
✅ sprint-15, needs-review, ready-to-deploy
❌ Sprint_15, Needs Review, READY_TO_DEPLOY
```

**Be specific:**
```
✅ blocked-waiting-api-keys
✅ frontend-react-components
✅ q4-2025-deliverable

❌ blocked
❌ frontend
❌ important
```

---

## Bulk Operations

### When to Use Bulk Operations

**✅ Use bulk operations when:**
- Completing multiple related tasks (feature complete)
- Reprioritizing a sprint
- Marking dependencies as blocked
- Tagging related work
- Transitioning project phases

**❌ Don't use bulk when:**
- Tasks are unrelated
- You need different notes for each
- Some tasks have special handling
- You're unsure about including all tasks

### Bulk Completion Best Practices

**Preview first (safety):**
```bash
# See what will happen
/bulk-complete 45 46 47

# Review the preview

# Confirm if correct
/bulk-complete 45 46 47 confirm All tests passing
```

**Group by milestone:**
```bash
# Complete all Phase 1 tasks
/bulk-complete 45 46 47 48 confirm Phase 1 complete, moving to Phase 2
```

**Use descriptive notes:**
```bash
# Good notes
/bulk-complete 101 102 103 confirm Bug fixes deployed to production, ticket #1234

# Minimal notes (less useful)
/bulk-complete 101 102 103 confirm Done
```

### Bulk Priority Best Practices

**Sprint planning:**
```bash
# This week: high priority
/bulk-priority high 45 46 47 48 confirm Sprint 15 starts Monday

# Next week: medium
/bulk-priority medium 50 51 52 53 confirm Sprint 16 planned

# Backlog: low
/bulk-priority low 100 101 102 confirm Future enhancements
```

**Hotfix escalation:**
```bash
# Critical production issue
/bulk-priority critical 201 202 203 confirm Production API down
```

### Bulk Blocking Best Practices

**Include detailed blocker info:**
```bash
# Good: Specific blocker with context
/block 45 46 47 Waiting for API documentation, contacted john@partner.com, ETA Friday

# Better: Include ticket/person/ETA
/block 45 46 Blocked by DB migration issue, Ticket #5678, DBA team investigating, ETA 2 days

# Bad: Vague blocker
/block 45 46 Blocked
```

**Update when blocker status changes:**
```bash
# When partially unblocked
/bulk-complete 45 confirm Blocker resolved for this task
/block 46 47 Still blocked, waiting for final approval
```

---

## Common Anti-Patterns

### ❌ Anti-Pattern #1: "Kitchen Sink" Master Tasks

**Bad:**
```
Master Task: "Stuff to do"
├─ Fix login bug
├─ Update dashboard colors
├─ Review PR #123
├─ Research caching options
└─ Update documentation
```

**Why it's bad:**
- Unrelated work grouped together
- No clear completion criteria
- Hard to track progress
- Loses context

**Better:**
```
Separate master tasks:
- "Login Bug Fix" (single task or small master)
- "Dashboard UI Improvements" (master if multi-step)
- Review PR #123 (standalone task)
- "Caching Strategy Research" (master task)
- Update docs (standalone task)
```

### ❌ Anti-Pattern #2: Too Many Nested Levels

**Bad:**
```
Master: "Platform"
├─ Frontend
│   ├─ Components
│   │   ├─ User Components
│   │   │   ├─ Login
│   │   │   │   ├─ Form
│   │   │   │   │   ├─ Email Field  ← Depth 6!
```

**Why it's bad:**
- Overly complex
- Hard to navigate
- Loses big picture
- Micromanagement

**Better:**
```
Master: "Frontend Components"
├─ User Authentication UI
├─ Dashboard Components
└─ Settings Components

(Each can have 1-2 levels of subtasks, not 6)
```

### ❌ Anti-Pattern #3: Neglecting Status Updates

**Bad:**
```
# Last week
Started task #45

# This week
[Never marked #45 as complete, started #46]

# Next week
[Working on #47, #45 and #46 still show "in_progress"]
```

**Why it's bad:**
- Inaccurate progress tracking
- Can't tell what's really in progress
- Velocity calculations are wrong
- Confusing session resumption

**Better:**
```
# Complete tasks as you finish them
/complete 45 Finished authentication
/complete 46 Tests passing

# Always have accurate status
/resume  # Shows real progress
```

### ❌ Anti-Pattern #4: Ignoring Staleness Warnings

**Bad:**
```
/resume
# Shows project stale for 14 days: 🔴 STALE
[User ignores it and starts new work]
```

**Why it's bad:**
- Unfinished work accumulates
- Context is lost
- Hard to resume later
- Reduces completion rate

**Better:**
```
/resume
# See stale project

# Either:
1. Resume it: "Let's finish that OAuth project"
2. Or explicitly cancel: /block 50 51 52 Project deprioritized, will revisit Q2

# Don't ignore stale work
```

### ❌ Anti-Pattern #5: No Blocker Documentation

**Bad:**
```bash
/block 45 46 Blocked
```

**Why it's bad:**
- No context for future sessions
- Can't track down blocker
- Don't know when to unblock
- Loses accountability

**Better:**
```bash
/block 45 46 Waiting for API keys from IT department, Ticket #1234, contacted Sarah, ETA Wednesday
```

---

## Summary: Golden Rules

1. **One in-progress task per project** - Prevents context switching
2. **Start every session with `/resume`** - Never lose track
3. **Use master tasks for 3+ related steps** - Group cohesive work
4. **Complete tasks as you finish them** - Keep status accurate
5. **Document blockers with details** - Include person, ticket, ETA
6. **Archive regularly (90 days)** - Keep active list clean
7. **Tag for discovery** - Cross-cutting concerns, not hierarchy
8. **Use bulk operations for efficiency** - Don't repeat yourself
9. **Preview before bulk changes** - Safety first
10. **Update context summaries** - Help future you

---

**Follow these practices to maximize productivity and never lose track of work!**

*Last updated: 2025-11-12 (Phase 3)*
*Version: 3.0*
