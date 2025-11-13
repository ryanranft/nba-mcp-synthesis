# Bulk Update Priority

**Change priority for multiple tasks at once.**

Phase 3 UX Enhancement: Efficient bulk priority management.

---

## Usage

```
/bulk-priority <priority> <task_ids>
/bulk-priority <priority> <task_ids> confirm
```

**Arguments:**
- `priority` - New priority level: low, medium, high, critical
- `task_ids` - Space-separated list of task IDs (e.g., "45 46 47 48")
- `confirm` - Include this keyword to execute without preview

---

## How It Works

### Step 1: Parse Arguments

Extract priority level and task IDs from the command:

```
Examples:
/bulk-priority high 45 46 47
/bulk-priority critical 101 102 103 confirm
/bulk-priority low 50 51 52 53
```

Parse the arguments:
- First argument must be a valid priority: low, medium, high, critical
- Remaining arguments are task IDs
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
                    BULK PRIORITY UPDATE - PREVIEW MODE
================================================================================

You are about to change priority to HIGH for the following tasks:

1. Task #45: "Implement user authentication"
   Current priority: medium → high
   Status: in_progress
   Last worked: 2 hours ago

2. Task #46: "Write authentication tests"
   Current priority: low → high
   Status: pending
   Last worked: Never

3. Task #47: "Deploy authentication to staging"
   Current priority: medium → high
   Status: pending
   Last worked: Never

--------------------------------------------------------------------------------
Total tasks to update: 3
New priority level: HIGH
Priority changes:
  - medium → high: 2 tasks
  - low → high: 1 task
--------------------------------------------------------------------------------

⚠️  CONFIRMATION REQUIRED

This will:
✓ Update priority for 3 tasks to 'high'
✓ Record changes in task_history
✓ Affect task ordering in /tasks view

To proceed, run:
/bulk-priority high 45 46 47 confirm

To cancel, ignore this message.
================================================================================
```

### Step 3: Execute Mode (with 'confirm')

If "confirm" keyword is provided, execute the bulk update:

```
Use the task-tracker MCP tool bulk_update_priority with:
- task_ids: [list of IDs]
- priority: [new priority level]
```

Display results:
```
================================================================================
                    BULK PRIORITY UPDATE - RESULTS
================================================================================

✅ Successfully updated priority for 3 tasks to HIGH

Updated Tasks:
1. Task #45: "Implement user authentication" (medium → high)
2. Task #46: "Write authentication tests" (low → high)
3. Task #47: "Deploy authentication to staging" (medium → high)

Priority changes applied:
- 3 tasks now have HIGH priority
- Tasks will appear higher in /tasks list
- Use /tasks sort-by-priority to see updated ordering
================================================================================
```

---

## Priority Levels

**low** - Nice to have, can be deferred
**medium** - Normal priority, default for most tasks
**high** - Important, should be addressed soon
**critical** - Urgent, needs immediate attention

---

## Examples

**Preview before updating:**
```
/bulk-priority high 45 46 47
```

**Update immediately:**
```
/bulk-priority critical 101 102 103 confirm
```

**Downgrade priority for completed sprint:**
```
/bulk-priority low 200 201 202 203 204 confirm
```

**Mark entire project as critical:**
```
/bulk-priority critical 50 51 52 53 54 55 56 confirm Production hotfix
```

---

## Use Cases

**Urgent Hotfix:**
```
/bulk-priority critical <all hotfix task IDs> confirm
```

**Sprint Reprioritization:**
```
# Downgrade old sprint
/bulk-priority low <old sprint IDs> confirm

# Elevate new sprint
/bulk-priority high <new sprint IDs> confirm
```

**Weekly Planning:**
```
# Mark this week's focus areas
/bulk-priority high <this week's IDs> confirm
```

---

## Safety Features

- **Preview by default** - Shows what will change before executing
- **Priority validation** - Ensures priority is one of: low, medium, high, critical
- **Task validation** - Verifies all task IDs exist
- **Change summary** - Shows before/after priority distribution
- **History tracking** - Records all priority changes

---

## Related Commands

- `/tasks sort-by-priority` - View tasks by priority order
- `/bulk-complete <ids>` - Complete multiple tasks
- `/block <ids> <reason>` - Mark multiple tasks as blocked
- `/tasks high priority` - Filter by high priority tasks

---

*Command Purpose:* Efficiently reprioritize multiple tasks for sprint planning and urgent changes
*Created:* 2025-11-12 (Phase 3)
*Enhancement:* Bulk operations for improved efficiency
