# Task Tracker - Real-World Examples

**Practical scenarios demonstrating task tracker usage.**

---

## Table of Contents

1. [Feature Development](#feature-development)
2. [Bug Fix Sprint](#bug-fix-sprint)
3. [Research Project](#research-project)
4. [System Integration](#system-integration)
5. [Production Hotfix](#production-hotfix)
6. [Multi-Week Project](#multi-week-project)
7. [Switching Between Projects](#switching-between-projects)
8. [Managing Technical Debt](#managing-technical-debt)

---

## Feature Development

### Scenario: Build Real-Time Chat Feature

**Initial prompt:**
```
I need to build a real-time chat feature for our application. It should support:
1. User-to-user messaging
2. Group chats
3. Message history
4. Read receipts
5. File attachments
```

**System automatically detects master task:**

```
🔍 Detected large initiative! Creating master task...

Master Task #45: "Real-Time Chat Feature" created

Subtasks:
├─ #46: Design database schema for messages
├─ #47: Implement WebSocket connection
├─ #48: Build chat UI components
├─ #49: Add group chat functionality
├─ #50: Implement message history
├─ #51: Add read receipts
├─ #52: File attachment support
└─ #53: Write integration tests

Status: 0/8 tasks complete (0%)
```

**Day 1: Start work**

```bash
/resume
```

```
================================================================================
#1  PROJECT: Real-Time Chat Feature              🔴 [░░░░░░░░░░] 0%
================================================================================
Status: PENDING ⏸️  | Activity: ✨ ACTIVE | Velocity: ➡️  NEW
Last Worked: Just created | Created: Today

Suggested Action: ✅ Start working on pending tasks

Progress:
├─ ⏸️  #46: Design database schema for messages
├─ ⏸️  #47: Implement WebSocket connection
├─ ⏸️  #48: Build chat UI components
├─ ⏸️  #49: Add group chat functionality
├─ ⏸️  #50: Implement message history
├─ ⏸️  #51: Add read receipts
├─ ⏸️  #52: File attachment support
└─ ⏸️  #53: Write integration tests

Subtasks: 8 total, 0 completed, 0 in progress, 8 pending
```

**User:** "Let's start with the database schema"

**Claude marks task #46 as in_progress and begins work**

```python
# Work on database schema...
# After completing the schema design:
```

**User:** "That looks good, let's move on"

```bash
/complete 46 Database schema designed and documented
```

```
✅ Task #46 completed
Master Task #45: 0% → 12.5% (+12.5%)
```

**Day 2: Resume**

```bash
/resume
```

```
================================================================================
#1  PROJECT: Real-Time Chat Feature              🟡 [█░░░░░░░░░] 12.5%
================================================================================
Status: IN PROGRESS 🔄 | Activity: ✨ ACTIVE | Velocity: 📈 TRENDING UP (6.3%/day)
Last Worked: 18 hours ago | Created: Yesterday

Suggested Action: ✅ Continue current work

Progress:
├─ ✅ #46: Design database schema for messages
├─ 🔄 #47: Implement WebSocket connection ← Currently Here
├─ ⏸️  #48: Build chat UI components
...
```

**User continues working, completes tasks #47 and #48**

```bash
/bulk-complete 47 48 confirm WebSocket and UI components complete
```

```
✅ Successfully completed 2 tasks
Master Task #45: 12.5% → 37.5% (+25%)
```

**Week End: Final push**

```bash
# Complete remaining tasks
/bulk-complete 49 50 51 52 53 confirm All chat features implemented and tested

Master Task #45: 100% complete ✅
```

**Final result:**
```
================================================================================
#1  PROJECT: Real-Time Chat Feature              🟢 [██████████] 100%
================================================================================
Status: COMPLETED ✅ | Duration: 5 days | Velocity: 20%/day

All tasks completed successfully!
```

---

## Bug Fix Sprint

### Scenario: Q4 Critical Bugs

**Create bug tracking master task:**

```python
create_master_task(
    title="Q4 Critical Bug Fixes",
    description="Production bugs identified in Q4 planning",
    subtasks=[
        "Login timeout on mobile devices",
        "Dashboard crash with large datasets",
        "Export CSV formatting issues",
        "Profile image upload failing on Safari",
        "Email notification delays"
    ]
)
```

**Prioritize bugs:**

```bash
# Get bug task IDs from creation
/tasks by-project 60

# Assign priorities
/bulk-priority critical 61 62  # Login and dashboard (production impact)
/bulk-priority high 63         # Export (customer complaint)
/bulk-priority medium 64 65    # Image upload and notifications
```

**Work through bugs in priority order:**

**Day 1: Critical bugs**

```bash
/tasks critical

# Shows tasks #61 and #62

# Start with login issue
# ... work on fix ...
/complete 61 Fixed session timeout, increased from 30min to 2hr, deployed hotfix
```

**Encounter blocker on dashboard bug:**

```bash
/block 62 Cannot reproduce locally, need production database dump, requested from DBA team, Ticket #5678
```

**Day 2: Resume work**

```bash
/resume
```

```
#1  PROJECT: Q4 Critical Bug Fixes                🟡 [██░░░░░░░░] 20%
Status: BLOCKED 🚫 | Activity: ✨ ACTIVE | Velocity: 📈 TRENDING UP

Blocked tasks: 1
- #62: Dashboard crash (waiting for DB dump)

Available tasks: 3
- #63: Export CSV (high priority)
- #64: Image upload (medium priority)
- #65: Notifications (medium priority)

Suggested Action: 🚨 Resolve blockers or work on available tasks
```

**User:** "Work on export bug while waiting for DB dump"

```bash
# Fix export issue
/complete 63 Fixed CSV formatting, quotes now properly escaped

# DB dump arrives
/bulk-complete 62 confirm DB dump received, reproduced and fixed issue
```

**Week end: Complete remaining bugs**

```bash
/bulk-complete 64 65 confirm Safari upload fixed, notification queue processed

Master Task #60: 100% complete ✅
Total bugs fixed: 5
Average time per bug: 1.2 days
```

---

## Research Project

### Scenario: Evaluate ML Frameworks

**User:** "I need to evaluate machine learning frameworks for our prediction system. Compare PyTorch, TensorFlow, and JAX."

**System creates research master task:**

```
Master Task #70: "Evaluate ML Frameworks for Prediction System"
├─ #71: Literature review - framework comparison
├─ #72: Setup development environment for all three
├─ #73: Implement prototype with PyTorch
├─ #74: Implement prototype with TensorFlow
├─ #75: Implement prototype with JAX
├─ #76: Benchmark performance (speed, memory, accuracy)
├─ #77: Evaluate developer experience and documentation
└─ #78: Write recommendation report

Tags: research, ml, evaluation
```

**Phase 1: Background research**

```bash
# Week 1: Literature review and setup
/complete 71 Completed literature review, summarized in docs/ml_frameworks_review.md
/complete 72 All frameworks installed, test environments working

Progress: 25% complete
```

**Phase 2: Prototyping (with challenges)**

```bash
# Week 2: Start PyTorch
# ... work ...
/complete 73 PyTorch prototype complete, 94% accuracy, fast training

# Start TensorFlow but hit issues
/block 74 TensorFlow installation conflicts with PyTorch, need separate venv, creating now
```

**Resolve blocker:**

```bash
# After creating isolated environment
/bulk-complete 74 confirm TensorFlow prototype complete, 93% accuracy, setup took extra time

# Continue with JAX
/complete 75 JAX prototype complete, 95% accuracy, very fast
```

**Phase 3: Analysis and reporting**

```bash
# Week 3: Benchmarking
/complete 76 Benchmarks complete, JAX fastest, PyTorch best documentation

# Developer experience evaluation
/complete 77 Developer experience evaluated, PyTorch most intuitive

# Final report
/complete 78 Recommendation report complete: suggest PyTorch for team familiarity, JAX for performance-critical paths

Master Task #70: 100% complete ✅
```

**Update context summary:**

```python
update_context_summary(
    task_id=70,
    context_summary="""
    Evaluated PyTorch, TensorFlow, and JAX for prediction system.

    Recommendation: Use PyTorch for main development (best docs, team familiarity)
    with JAX for performance-critical inference (2x faster).

    TensorFlow not recommended due to setup complexity and similar performance to PyTorch.

    Full report: docs/ml_frameworks_evaluation_report.md
    """
)
```

---

## System Integration

### Scenario: Integrate OAuth with Existing Auth System

**User:** "We need to add OAuth support to our authentication system without breaking existing username/password login"

**Master task creation:**

```
Master Task #80: "OAuth Integration with Backward Compatibility"
├─ Phase 1: Design & Planning
│   ├─ #81: Review existing auth architecture
│   ├─ #82: Design OAuth integration approach
│   └─ #83: Plan migration strategy
├─ Phase 2: Implementation
│   ├─ #84: Implement OAuth provider interface
│   ├─ #85: Add Google OAuth integration
│   ├─ #86: Add GitHub OAuth integration
│   └─ #87: Maintain existing username/password flow
├─ Phase 3: Testing & Deployment
│   ├─ #88: Write integration tests
│   ├─ #89: Test backward compatibility
│   ├─ #90: Deploy to staging
│   └─ #91: Deploy to production

Tags: oauth, authentication, integration, critical
```

**Week 1: Planning phase**

```bash
/resume

# Work through planning tasks
/complete 81 82 83 Planning complete, documented in docs/oauth_integration_plan.md

Progress: 27% (3/11 tasks)
```

**Week 2: Implementation (with dependencies)**

```bash
# Start OAuth interface
/complete 84 OAuth provider interface complete with abstract base class

# Google OAuth depends on #84
/complete 85 Google OAuth provider implemented, tested with test app

# GitHub OAuth
/complete 86 GitHub OAuth provider implemented

# Critical: ensure backward compatibility
/complete 87 Existing username/password auth working, tested with regression suite

Progress: 64% (7/11 tasks)
```

**Week 3: Testing discovered issues**

```bash
# Start integration tests
# ... discover issue ...

# Block tasks due to discovered bug
/block 88 89 Found session management issue with OAuth, fixing in separate bug ticket #9012

# Fix bug
/complete 88 89 Bug fixed, all integration tests passing

# Deploy to staging
/complete 90 Deployed to staging, tested with real OAuth providers

# Production deployment blocked
/block 91 Waiting for security review approval, submitted to SecOps team Tue, ETA Friday
```

**Week 4: Production deployment**

```bash
# Security review complete
/complete 91 confirm Security review approved, deployed to production, monitoring metrics

Master Task #80: 100% complete ✅
Duration: 23 days
OAuth integration successful with zero backward compatibility issues
```

---

## Production Hotfix

### Scenario: Critical API Outage

**User:** "Production API is down! Authentication service failing with 500 errors"

**Create critical master task:**

```python
create_master_task(
    title="HOTFIX: Production API Authentication Failure",
    description="Critical outage - auth service returning 500 errors, all users impacted",
    subtasks=[
        "Investigate error logs and identify root cause",
        "Implement fix for authentication issue",
        "Test fix in staging environment",
        "Deploy hotfix to production",
        "Monitor and verify fix",
        "Post-mortem: document incident and prevention"
    ],
    priority="critical"
)
```

**Immediate priority elevation:**

```bash
# All tasks critical priority
/bulk-priority critical 95 96 97 98 99 100 confirm PRODUCTION OUTAGE
```

**Hour 1: Investigation**

```bash
# Investigate
# ... Claude finds root cause: database connection pool exhausted ...

/complete 95 Root cause identified: DB connection pool exhausted due to connection leak in auth service
```

**Hour 2: Fix implementation**

```bash
# Implement fix
# ... Claude fixes connection leak ...

/complete 96 Fix implemented: properly close connections in finally block, increased pool size
```

**Hour 3: Testing and deployment**

```bash
# Test in staging
/complete 97 Tested in staging, monitoring shows connections properly released

# Deploy to production
/complete 98 Hotfix deployed to production at 14:35 UTC

# Monitor
/complete 99 Monitoring for 30 minutes, no errors, connection pool stable, auth success rate back to 100%

# Mark incident as resolved
```

**Day 2: Post-mortem**

```bash
/complete 100 Post-mortem complete, documented in docs/incidents/2025-11-12-auth-outage.md

Master Task #95: 100% complete ✅
Total duration: 4 hours from outage to full resolution
Impact: 45 minutes of user-facing downtime
```

**Add detailed notes:**

```python
update_context_summary(
    task_id=95,
    context_summary="""
    INCIDENT: Production auth service outage

    Root Cause: Database connection leak in auth service
    Impact: 45 minutes downtime, all users affected
    Resolution Time: 4 hours (investigation to full recovery)

    Fix: Added proper connection cleanup, increased pool size
    Prevention: Added connection leak detection, improved monitoring

    Post-mortem: docs/incidents/2025-11-12-auth-outage.md
    """
)
```

---

## Multi-Week Project

### Scenario: Microservices Migration

**User:** "We need to migrate our monolithic application to microservices architecture over the next 2 months"

**Large-scale master task with phases:**

```
Master Task #110: "Microservices Migration - Monolith to Services"

├─ Phase 1: Planning & Architecture (Week 1-2)
│   ├─ #111: Analyze monolith dependencies
│   ├─ #112: Design microservices architecture
│   ├─ #113: Define service boundaries
│   └─ #114: Create migration roadmap
│
├─ Phase 2: Infrastructure Setup (Week 3)
│   ├─ #115: Setup Kubernetes cluster
│   ├─ #116: Configure service mesh
│   ├─ #117: Setup API gateway
│   └─ #118: Configure monitoring and logging
│
├─ Phase 3: Service Extraction (Week 4-7)
│   ├─ Service 1: User Management
│   │   ├─ #119: Extract user service
│   │   ├─ #120: Migrate database tables
│   │   └─ #121: Deploy and test
│   ├─ Service 2: Product Catalog
│   │   ├─ #122: Extract catalog service
│   │   ├─ #123: Migrate database tables
│   │   └─ #124: Deploy and test
│   └─ Service 3: Order Processing
│       ├─ #125: Extract order service
│       ├─ #126: Migrate database tables
│       └─ #127: Deploy and test
│
└─ Phase 4: Cutover & Monitoring (Week 8)
    ├─ #128: Gradual traffic migration
    ├─ #129: Monitor performance and errors
    ├─ #130: Decommission monolith
    └─ #131: Documentation and handoff

Tags: migration, microservices, infrastructure, multi-week
```

**Week 1-2: Planning**

```bash
/resume

# Work through planning phase
/bulk-complete 111 112 113 114 confirm Planning phase complete, architecture documented

Progress: 19% (4/21 tasks)
```

**Week 3: Infrastructure**

```bash
# Setup infrastructure
/complete 115 116 117 118 Infrastructure ready, K8s cluster operational

Progress: 38% (8/21 tasks)
```

**Week 4: First service migration**

```bash
# User service extraction
/complete 119 User service extracted from monolith
/complete 120 User database migrated successfully

# Blocker encountered
/block 121 Integration tests failing, investigating API compatibility issue
```

**Resolve blocker:**

```bash
# Fix compatibility issue
/bulk-complete 121 confirm Tests passing, user service deployed to production

Progress: 52% (11/21 tasks)
```

**Week 5-6: Continue service extraction (staleness warning)**

```bash
/resume
```

```
#1  PROJECT: Microservices Migration              🟡 [█████░░░░░] 52%
Status: IN PROGRESS 🔄 | Activity: 🟡 WARNING | Velocity: 📉 TRENDING DOWN (4.3%/day)
Last Worked: 5 days ago | Created: 35 days ago

⚠️  Warning: Progress has slowed. Project at risk of becoming stale.

Suggested Action: ⚠️  Resume work to avoid staleness
```

**User:** "Let's get back on track"

```bash
# Complete catalog service
/bulk-complete 122 123 124 confirm Catalog service migrated and deployed

# Complete order service
/bulk-complete 125 126 127 confirm Order service migrated and deployed

Progress: 81% (17/21 tasks)
```

**Week 7-8: Cutover**

```bash
# Gradual migration
/complete 128 Traffic gradually migrated, 100% on microservices

# Monitor for issues
/complete 129 Monitored for 72 hours, performance improved 40%, no errors

# Decommission monolith
/complete 130 Monolith decommissioned, infrastructure cleaned up

# Final documentation
/complete 131 Migration documentation complete, team trained

Master Task #110: 100% complete ✅
Total duration: 56 days (8 weeks)
Outcome: Successful migration, 40% performance improvement
```

---

## Switching Between Projects

### Scenario: Juggling Multiple Initiatives

**User has 3 active projects:**

```bash
/resume
```

```
================================================================================
                    PROJECT RESUME - ACTIVE WORK (Enhanced v3.0)
================================================================================

Active Projects: 3
Overall Completion: 42/75 (56%)

📊 Project Health Score: 65/100
   ├─ Stale Projects: 1 🔴
   ├─ Blocked Projects: 0 🚫
   └─ Active Projects: 3 ✨

💡 Recommended Next: #3 "API Documentation" (stale, needs attention)

--------------------------------------------------------------------------------
#1  PROJECT: Dashboard Redesign                  🟢 [████████░░] 78%
--------------------------------------------------------------------------------
Status: IN PROGRESS 🔄 | Activity: ✨ ACTIVE | Velocity: 📈 TRENDING UP (9.2%/day)
Last Worked: 2 hours ago | Created: 15 days ago

Suggested Action: ✅ Continue current work

Progress: 14/18 tasks complete
Currently on: Task #47 "Implement dark mode"
...

--------------------------------------------------------------------------------
#2  PROJECT: Mobile App MVP                      🟡 [████░░░░░░] 45%
--------------------------------------------------------------------------------
Status: IN PROGRESS 🔄 | Activity: 🟡 WARNING | Velocity: ➡️  STEADY (3.2%/day)
Last Worked: 4 days ago | Created: 14 days ago

Suggested Action: ⚠️  Resume work to avoid staleness

Progress: 9/20 tasks complete
Currently on: Task #68 "User authentication flow"
...

--------------------------------------------------------------------------------
#3  PROJECT: API Documentation                   🔴 [█░░░░░░░░░] 12%
--------------------------------------------------------------------------------
Status: PENDING ⏸️  | Activity: 🔴 STALE | Velocity: 📉 TRENDING DOWN (0.8%/day)
Last Worked: 9 days ago | Created: 15 days ago

Suggested Action: 🚨 Resume this stale project immediately

Progress: 4/37 tasks complete
Last task: #92 "Document user endpoints"
...
```

**Strategy 1: Focus on one project at a time**

```bash
# User: "Finish dashboard first"
/resume 1

# Work on dashboard until complete
/bulk-complete 47 48 49 confirm Dashboard redesign complete

# Then move to mobile app
/resume 2
```

**Strategy 2: Context switching with notes**

```bash
# User: "Urgent mobile app work came up"

# Save dashboard context
# (Add note to current in_progress task)

# Switch to mobile app
/resume 2

# Work on mobile app
/complete 68 User auth flow complete

# Return to dashboard later
/resume 1
```

**Strategy 3: Time-boxed work**

```bash
# User: "Spend 2 hours on each project daily"

# Morning: Dashboard
/resume 1
# ... 2 hours of work ...
/complete 47 Dark mode 80% complete, will finish tomorrow

# Midday: Mobile app
/resume 2
# ... 2 hours of work ...
/complete 68 69 Auth complete, profile screen done

# Afternoon: API docs (clearing staleness)
/resume 3
# ... 2 hours of work ...
/bulk-complete 92 93 94 confirm User and product endpoints documented

# Next day: repeat
```

---

## Managing Technical Debt

### Scenario: Technical Debt Reduction Sprint

**Create tech debt master task:**

```python
create_master_task(
    title="Q4 Technical Debt Reduction",
    description="Address accumulated technical debt across codebase",
    subtasks=[
        "Upgrade deprecated dependencies",
        "Refactor user service (too complex)",
        "Add missing unit tests for payment module",
        "Remove unused code and dead routes",
        "Document undocumented APIs",
        "Improve error handling in background jobs",
        "Optimize slow database queries",
        "Update outdated documentation"
    ],
    priority="medium",
    tags=["tech-debt", "refactoring", "maintenance"]
)
```

**Prioritize tech debt items:**

```bash
/tasks by-project 150

# Prioritize by impact
/bulk-priority high 151 157     # Security (deprecated deps, error handling)
/bulk-priority medium 152 153   # Code quality (refactoring, tests)
/bulk-priority low 154 155 156 158  # Nice to have (cleanup, docs)
```

**Work through high priority first:**

```bash
# Security updates
/complete 151 All dependencies updated to latest stable versions, 0 vulnerabilities

# Error handling
/complete 157 Background jobs now have proper error handling and retry logic

Progress: 25% (2/8 tasks)
```

**Incremental progress over weeks:**

```bash
# Week 2
/complete 152 User service refactored, complexity reduced from 250 to 80 lines

# Week 3
/complete 153 Payment module test coverage increased from 45% to 92%

Progress: 50% (4/8 tasks)
```

**Finish remaining items:**

```bash
/bulk-complete 154 155 156 158 confirm Tech debt cleanup complete

Master Task #150: 100% complete ✅
Code quality improved significantly:
- Test coverage: 45% → 87%
- Technical debt score: 62 → 89
- Documentation completeness: 40% → 95%
```

---

## Key Takeaways from Examples

### What Works Well

1. **Automatic master task detection** - Let the system detect large initiatives
2. **Regular /resume checks** - Start every session with resume view
3. **Bulk operations** - Use for related tasks
4. **Detailed blocker notes** - Include ticket, person, ETA
5. **Context summaries** - Update for long-running projects
6. **Priority management** - Adjust as priorities shift
7. **Staleness attention** - Address stale projects promptly

### Common Patterns

- **Feature development**: 5-15 tasks, 1-3 weeks
- **Bug sprints**: 3-10 bugs, 1-2 weeks
- **Research projects**: 6-10 tasks, 2-4 weeks
- **Large migrations**: 15-30 tasks, 4-8 weeks
- **Hotfixes**: 3-6 tasks, 2-8 hours

### Success Metrics

- **Completion rate**: 80-95% of started tasks completed
- **Staleness**: <10% of projects stale (>7 days)
- **Velocity**: Consistent progress (5-15%/day for active projects)
- **Health score**: 70-100 (minimal stale/blocked projects)

---

*Last updated: 2025-11-12 (Phase 3)*
*Version: 3.0*
