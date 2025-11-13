# Block Tasks

**Mark multiple tasks as blocked with a reason.**

Phase 3 UX Enhancement: Efficiently track blockers and dependencies.

---

## Usage

```
/block <task_ids> <reason>
/block <task_ids> <reason> confirm
```

**Arguments:**
- `task_ids` - Space-separated list of task IDs (e.g., "45 46 47")
- `reason` - Description of why tasks are blocked (required)
- `confirm` - Include this keyword to execute without preview

---

## How It Works

### Step 1: Parse Arguments

Extract task IDs and blocker reason from the command:

```
Examples:
/block 45 46 47 Waiting for API documentation
/block 101 102 Blocked by database migration issue confirm
/block 50 51 52 Dependency on external team, ETA unknown
```

Parse the arguments:
- Task IDs are the numeric arguments
- Everything after last task ID is the reason (required)
- If "confirm" is last word → Execute immediately, reason is everything before "confirm"
- Otherwise → Show preview and ask for confirmation

### Step 2: Preview Mode (Default)

If "confirm" is NOT provided, show a preview:

```
Use the task-tracker MCP tool list_tasks to fetch details for the task IDs
```

Display:
```
================================================================================
                    BLOCK TASKS - PREVIEW MODE
================================================================================

You are about to mark the following tasks as BLOCKED:

1. Task #45: "Implement OAuth integration"
   Status: in_progress → blocked
   Priority: high
   Last worked: 2 hours ago

2. Task #46: "Test OAuth flow"
   Status: pending → blocked
   Priority: medium
   Depends on: Task #45

3. Task #47: "Deploy OAuth to staging"
   Status: pending → blocked
   Priority: high
   Depends on: Task #46

--------------------------------------------------------------------------------
Blocker Reason: "Waiting for API documentation from external team"
Total tasks to block: 3
Current status distribution:
  - in_progress → blocked: 1 task
  - pending → blocked: 2 tasks
--------------------------------------------------------------------------------

⚠️  CONFIRMATION REQUIRED

This will:
✓ Mark 3 tasks as blocked
✓ Add blocker reason to task notes
✓ Update master task status (may show as blocked)
✓ Record status changes in task_history
✓ Make tasks visible in /tasks blocked view

To proceed, run:
/block 45 46 47 Waiting for API documentation from external team confirm

To cancel, ignore this message.
================================================================================
```

### Step 3: Execute Mode (with 'confirm')

If "confirm" keyword is provided, execute the bulk update:

```
Use the task-tracker MCP tool bulk_update_status with:
- task_ids: [list of IDs]
- status: "blocked"
- notes: "BLOCKED: [reason]"
```

Display results:
```
================================================================================
                    BLOCK TASKS - RESULTS
================================================================================

🚫 Successfully blocked 3 tasks

Blocked Tasks:
1. 🚫 Task #45: "Implement OAuth integration"
2. 🚫 Task #46: "Test OAuth flow"
3. 🚫 Task #47: "Deploy OAuth to staging"

Blocker reason added to notes:
"BLOCKED: Waiting for API documentation from external team"

Master Task Impact:
- Master Task #12 "OAuth Integration": Status → blocked (3 of 5 tasks blocked)

Next Steps:
1. Use /tasks blocked to see all blocked tasks
2. Update blocker status when resolved
3. Unblock tasks with: /bulk-complete 45 46 47 Blocker resolved
================================================================================
```

---

## Common Blocker Reasons

**External Dependencies:**
```
/block 45 46 Waiting for API keys from IT department
/block 50 51 52 Blocked by legal review, ETA 2 weeks
/block 101 External team dependency, contact: john@example.com
```

**Technical Issues:**
```
/block 45 46 47 Database migration failed, investigating
/block 100 101 Build system issue, ticket #1234 opened
/block 50 CI/CD pipeline down, DevOps notified
```

**Information Needed:**
```
/block 45 46 Need requirements clarification from product
/block 101 102 103 Waiting for design mockups
/block 50 Missing test data, requested from QA
```

**Resource Constraints:**
```
/block 45 46 Waiting for staging environment access
/block 101 102 No available test devices
/block 50 51 AWS quota limit reached, ticket submitted
```

---

## Unblocking Tasks

When blocker is resolved, update task status:

**Individual unblock:**
```
/complete 45 Blocker resolved, API docs received
```

**Bulk unblock:**
```
/bulk-complete 45 46 47 confirm Blocker resolved
```

Or resume work:
```
/bulk-priority high 45 46 47 confirm Blocker cleared, prioritizing
```

---

## Viewing Blocked Tasks

**See all blocked tasks:**
```
/tasks blocked
```

**Filter blocked tasks by project:**
```
/tasks by-project 12 blocked
```

**Analytics on blockers:**
```
/analytics blockers
```

---

## Best Practices

1. **Be specific** - Include ticket numbers, contact names, ETAs
   ✅ Good: "Waiting for API docs, Ticket #1234, ETA Friday"
   ❌ Bad: "Blocked"

2. **Track dependencies** - Note which task is blocking
   ✅ "Blocked by Task #45 - OAuth implementation"

3. **Include contact info** - Who can unblock?
   ✅ "Waiting for review from jane@example.com"

4. **Add ETA if known** - When do you expect resolution?
   ✅ "Blocked until database migration completes (ETA: 2 days)"

5. **Update regularly** - Keep blocker status current
   - Check blocked tasks weekly
   - Unblock when resolved
   - Update notes if ETA changes

---

## Examples

**Preview before blocking:**
```
/block 45 46 47 Waiting for API documentation
```

**Block immediately with detailed reason:**
```
/block 101 102 Database migration issue ticket #5678, DBA team investigating confirm
```

**Block with ETA:**
```
/block 50 51 Waiting for legal approval, ETA 1 week confirm
```

**Block with contact:**
```
/block 45 Blocked by external dependency, contact: john@partner.com for status confirm
```

---

## Safety Features

- **Preview by default** - Shows impact before executing
- **Required reason** - Forces documentation of blocker
- **Task validation** - Verifies all task IDs exist
- **Master task updates** - Automatically marks project as blocked if threshold reached
- **History tracking** - Records when task was blocked and why
- **Notes preservation** - Appends blocker reason to existing notes

---

## Master Task Impact

When tasks are blocked, the master task status may automatically update:

- **<33% blocked** - Master stays in_progress
- **33-66% blocked** - Warning shown, but master stays current status
- **>66% blocked** - Master task automatically marked as blocked

This helps surface blockers at the project level.

---

## Related Commands

- `/tasks blocked` - View all blocked tasks
- `/bulk-complete <ids>` - Unblock and complete tasks
- `/bulk-priority <level> <ids>` - Adjust priority after unblocking
- `/analytics blockers` - See blocker statistics

---

*Command Purpose:* Track blockers and dependencies across multiple tasks efficiently
*Created:* 2025-11-12 (Phase 3)
*Enhancement:* Bulk operations for improved blocker management