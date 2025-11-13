# List Active Tasks

Show all currently active tasks across all projects with pagination support.

Usage:
- `/tasks` - Show active tasks (page 1)
- `/tasks 2` - Show page 2 of active tasks
- `/tasks all` - Show all tasks (including completed)
- `/tasks pending` - Show only pending tasks
- `/tasks high` - Show only high priority tasks

---

## Execution

Use the Task Tracker MCP `list_tasks` tool with pagination:

```python
# Parse arguments
args = user_args.split() if user_args else []
page = 1
status_filter = None
priority_filter = None
show_all = False

# Parse arguments
if args:
    if args[0] == 'all':
        show_all = True
    elif args[0].isdigit():
        page = int(args[0])
    elif args[0] in ['pending', 'in_progress', 'completed', 'blocked']:
        status_filter = args[0]
    elif args[0] in ['low', 'medium', 'high', 'critical']:
        priority_filter = args[0]

# Calculate pagination
limit = 20  # Tasks per page
offset = (page - 1) * limit

# Fetch tasks
if show_all:
    result = list_tasks(limit=limit, offset=offset)
elif status_filter:
    result = list_tasks(status=status_filter, limit=limit, offset=offset)
elif priority_filter:
    result = list_tasks(priority=priority_filter, limit=limit, offset=offset)
else:
    # Default: show in_progress + pending
    in_progress = list_tasks(status="in_progress", limit=50)
    pending = list_tasks(status="pending", limit=50)
```

## Display Format

Present results with pagination info:

```
================================================================================
                          ACTIVE TASKS (Page 1 of 3)
================================================================================

🔄 IN PROGRESS (X tasks):

1. [ID: 123] Fix authentication bug
   Priority: high | Created: 2 hours ago
   Project: Authentication System Overhaul (#45)

2. [ID: 456] Write integration tests
   Priority: medium | Created: 1 day ago
   Project: Testing Infrastructure (#52)

--------------------------------------------------------------------------------

⏸️  PENDING (Y tasks):

3. [ID: 789] Deploy to staging
   Priority: high | Created: 3 hours ago
   Project: Deployment Pipeline (#48)

4. [ID: 321] Update documentation
   Priority: low | Created: 2 days ago
   Project: Documentation Cleanup (#51)

================================================================================

Pagination:
  Showing 1-20 of 157 tasks

  Navigation:
    /tasks 2     - Next page
    /tasks 1     - Current page

  Filters:
    /tasks all         - Show all tasks (including completed)
    /tasks pending     - Only pending tasks
    /tasks in_progress - Only in-progress tasks
    /tasks high        - Only high priority tasks

Quick Actions:
  /complete <task_id>  - Mark task as complete
  /resume <project_id> - Jump to a specific project
  /archive             - Archive old completed tasks

================================================================================
```

## Pagination Logic

- **Default view**: First 20 active tasks (in_progress + pending)
- **Page size**: 20 tasks per page
- **Show "Next page" hint** if `pagination.has_more == true`
- **Show "Previous page" hint** if `pagination.has_previous == true`
- **Display range**: "Showing X-Y of Z tasks"

## Additional Filters (Optional)

If user specifies filters, apply them:
- By status: `/tasks pending`, `/tasks in_progress`, `/tasks completed`
- By priority: `/tasks high`, `/tasks critical`
- By page: `/tasks 2`, `/tasks 3`
- Show all: `/tasks all`

Multiple filters can be combined programmatically via MCP tools:
```python
list_tasks(status="pending", priority="high", limit=20, offset=0)
```

---

*Purpose:* Quick view of active tasks with pagination
*Updated:* 2025-11-12 (Phase 2.3 - Pagination System)
*Created:* 2025-11-12 (Phase 2.2 - Quick Actions)
