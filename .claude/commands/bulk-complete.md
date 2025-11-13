# Bulk Complete Tasks

**Complete multiple tasks at once with confirmation.**

Phase 3 UX Enhancement: Efficient bulk status updates.

---

## Usage

```
/bulk-complete <task_ids> [notes]
/bulk-complete <task_ids> confirm [notes]
```

**Arguments:**
- `task_ids` - Space-separated list of task IDs (e.g., "45 46 47 48")
- `confirm` - Include this keyword to execute without preview
- `notes` - Optional notes to add to all tasks

---

## How It Works

### Step 1: Parse Arguments

Extract task IDs and optional notes from the command:

```
Examples:
/bulk-complete 45 46 47
/bulk-complete 45 46 47 Finished all database migrations
/bulk-complete 45 46 47 confirm
/bulk-complete 45 46 47 confirm All tests passing
```

Parse the arguments:
- If "confirm" is present → Execute immediately
- Otherwise → Show preview and ask for confirmation

### Step 2: Preview Mode (Default)

If "confirm" is NOT provided, show a preview:

```
Use the task-tracker MCP tool list_tasks to fetch details for the task IDs
```

Display:
```
================================================================================
                    BULK COMPLETE - PREVIEW MODE
================================================================================

You are about to mark the following tasks as COMPLETED:

1. Task #45: "Implement user authentication"
   Status: in_progress → completed
   Priority: high
   Last worked: 2 hours ago

2. Task #46: "Write authentication tests"
   Status: in_progress → completed
   Priority: medium
   Last worked: 1 hour ago

3. Task #47: "Deploy authentication to staging"
   Status: pending → completed
   Priority: high
   Last worked: Never

--------------------------------------------------------------------------------
Total tasks to complete: 3
Notes to add: [notes if provided, otherwise "None"]
--------------------------------------------------------------------------------

⚠️  CONFIRMATION REQUIRED

This will:
✓ Mark 3 tasks as completed
✓ Update master task progress percentages
✓ Trigger last_worked_at updates
✓ Record status changes in task_history

To proceed, run:
/bulk-complete 45 46 47 confirm [notes]

To cancel, ignore this message.
================================================================================
```

### Step 3: Execute Mode (with 'confirm')

If "confirm" keyword is provided, execute the bulk update:

```
Use the task-tracker MCP tool bulk_update_status with:
- task_ids: [list of IDs]
- status: "completed"
- notes: [optional notes]
```

Display results:
```
================================================================================
                    BULK COMPLETE - RESULTS
================================================================================

✅ Successfully completed 3 tasks

Updated Tasks:
1. ✅ Task #45: "Implement user authentication"
2. ✅ Task #46: "Write authentication tests"
3. ✅ Task #47: "Deploy authentication to staging"

Master Task Progress Updates:
- Master Task #12 "User Authentication System": 78% → 92% (+14%)
- Master Task #8 "Q4 Sprint Goals": 45% → 48% (+3%)

Notes added: "All tests passing"

Last worked timestamps updated for all tasks.
================================================================================
```

---

## Examples

**Preview before completing:**
```
/bulk-complete 45 46 47
```

**Complete immediately with notes:**
```
/bulk-complete 45 46 47 confirm Finished all related tasks
```

**Complete many tasks:**
```
/bulk-complete 101 102 103 104 105 106 confirm Migration completed successfully
```

---

## Safety Features

- **Preview by default** - Shows what will happen before executing
- **Task validation** - Verifies all task IDs exist
- **Progress calculation** - Automatically updates master task percentages
- **History tracking** - Records all status changes
- **Notes preservation** - Appends to existing notes rather than replacing

---

## Related Commands

- `/complete <id>` - Complete a single task
- `/tasks` - View active tasks
- `/bulk-priority <ids> <level>` - Change priority for multiple tasks
- `/block <ids> <reason>` - Mark multiple tasks as blocked

---

*Command Purpose:* Efficiently complete multiple related tasks at once
*Created:* 2025-11-12 (Phase 3)
*Enhancement:* Bulk operations for improved efficiency
