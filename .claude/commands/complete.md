# Mark Task Complete

Quickly mark a task as completed by ID.

---

## Usage

```
/complete <task_id>
```

Examples:
- `/complete 123` - Mark task 123 as complete
- `/complete 456 789` - Mark multiple tasks (456, 789) as complete

---

## Execution

1. **Parse task ID(s)** from user input
2. **For each task ID:**
   - Use `update_task_status(task_id, "completed")` MCP tool
   - Record completion timestamp
3. **Display confirmation**

## Display Format

```
✅ Task Completed!

ID: 123
Title: Fix authentication bug
Status: pending → completed
Completed at: 2025-11-12 14:30:00

[If task has parent/master]
📊 Project Progress Updated:
- Project: Authentication System Overhaul
- Progress: 14/18 tasks (78% → 83%)
```

## Error Handling

If task ID not found:
```
❌ Error: Task 999 not found
```

If task already completed:
```
ℹ️  Task 123 is already completed (completed 2 days ago)
```

## Multiple Tasks

When completing multiple tasks:
```
✅ Completed 3 tasks:
- Task 123: Fix authentication bug
- Task 456: Write tests
- Task 789: Update docs

📊 Overall progress: 45/60 tasks (75%)
```

---

## Alternative: Complete by Pattern

```
/complete all pending in project <master_id>
```

This would complete all pending subtasks in a master project (use with caution!).

---

*Purpose:* Quick task completion without full MCP tool syntax
*Created:* 2025-11-12 (Phase 2.2 - Quick Actions)
*Safety:* Always confirm before batch operations