# Archive Old Tasks

Archive old completed tasks to keep your task list clean and performant.

Usage:
- `/archive` - Preview tasks to archive (30 days old by default)
- `/archive <days>` - Preview tasks older than specified days
- `/archive confirm` - Actually archive based on last preview
- `/archive confirm <days>` - Archive tasks older than specified days
- `/archive stats` - Show archive statistics
- `/archive list` - List archived tasks

---

## Execution

Use the Task Tracker MCP `archive_tasks` tool:

```python
# Parse arguments
args = user_args.split() if user_args else []

if not args or (len(args) == 1 and args[0].isdigit()):
    # Preview mode (dry run)
    days = int(args[0]) if args else 30
    result = archive_tasks(days_old=days, dry_run=True)

    # Display preview
    if result['success'] and result['would_archive'] > 0:
        print(f"📦 ARCHIVE PREVIEW")
        print(f"\nWould archive {result['would_archive']} completed tasks older than {days} days:\n")

        for task in result['tasks'][:10]:  # Show first 10
            days_old = task['days_since_completed']
            print(f"  [{task['id']}] {task['content']}")
            print(f"        Completed {days_old:.1f} days ago\n")

        if result['would_archive'] > 10:
            print(f"  ... and {result['would_archive'] - 10} more tasks\n")

        print(f"\n✅ Run `/archive confirm {days}` to proceed with archiving")
    else:
        print(f"✅ No tasks to archive (completed <{days} days ago)")

elif args[0] == 'confirm':
    # Actually archive
    days = int(args[1]) if len(args) > 1 else 30
    result = archive_tasks(days_old=days, dry_run=False)

    if result['success']:
        print(f"✅ Archived {result['archived']} completed tasks older than {days} days")
        print(f"\nTask IDs archived: {result['task_ids'][:10]}")
        if len(result['task_ids']) > 10:
            print(f"... and {len(result['task_ids']) - 10} more")
    else:
        print(f"❌ Archive failed: {result.get('error', 'Unknown error')}")

elif args[0] == 'stats':
    # Show archive statistics
    stats_result = get_archive_stats()

    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"📊 ARCHIVE STATISTICS")
        print(f"\nTotal archived: {stats['total_archived']}")
        print(f"Archived this week: {stats['archived_this_week']}")
        print(f"Archived this month: {stats['archived_this_month']}")

        if stats['oldest_archived_date']:
            print(f"\nOldest archive: {stats['oldest_archived_date']}")
        if stats['newest_archived_date']:
            print(f"Newest archive: {stats['newest_archived_date']}")

        print(f"\nEstimated size: {stats['total_size_estimate_mb']} MB")
    else:
        print(f"❌ Failed to get stats: {stats_result.get('error')}")

elif args[0] == 'list':
    # List archived tasks
    page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    limit = 20
    offset = (page - 1) * limit

    result = list_archived_tasks(limit=limit, offset=offset)

    if result['success']:
        tasks = result['tasks']
        pagination = result['pagination']

        print(f"📦 ARCHIVED TASKS (Page {pagination['current_page']} of {pagination['total_pages']})")
        print(f"\nTotal archived: {pagination['total_count']}\n")

        for task in tasks:
            print(f"[ID: {task['id']}] {task['content']}")
            print(f"  Status: {task['status']} | Priority: {task['priority']}")
            print(f"  Archived: {task['days_archived']:.1f} days ago\n")

        # Navigation hints
        if pagination['has_more']:
            print(f"Next page: /archive list {pagination['current_page'] + 1}")
        if pagination['has_previous']:
            print(f"Previous page: /archive list {pagination['current_page'] - 1}")
    else:
        print(f"❌ Failed to list archived tasks: {result.get('error')}")

else:
    print("Usage:")
    print("  /archive              - Preview archive (30 days)")
    print("  /archive <days>       - Preview archive (custom days)")
    print("  /archive confirm      - Archive with confirmation")
    print("  /archive confirm <days> - Archive custom days")
    print("  /archive stats        - Show archive statistics")
    print("  /archive list [page]  - List archived tasks")
```

## Display Format (Preview)

```
================================================================================
                          📦 ARCHIVE PREVIEW
================================================================================

Would archive 47 completed tasks older than 30 days:

  [ID: 123] Fix authentication bug in login flow
        Completed 45.2 days ago

  [ID: 156] Write unit tests for API endpoints
        Completed 42.8 days ago

  [ID: 189] Deploy to staging environment
        Completed 38.1 days ago

  ... and 44 more tasks

================================================================================

✅ Run `/archive confirm 30` to proceed with archiving

Benefits of archiving:
  • Keeps active task list clean and fast
  • Preserves task history for later reference
  • Improves database query performance
  • Tasks can be restored with unarchive_tasks() tool

================================================================================
```

## Safety Features

1. **Dry run by default**: Preview before archiving
2. **Explicit confirmation**: Must use `confirm` to actually archive
3. **Restoreable**: Archived tasks can be restored with `unarchive_tasks()` MCP tool
4. **Logged**: All archival operations logged to task_history table
5. **Soft delete**: Tasks remain in database, just marked as archived

## Restore Archived Tasks (via MCP)

To restore archived tasks, use the MCP tool directly:

```python
# Restore specific tasks
unarchive_tasks(task_ids=[123, 456, 789])
```

---

*Purpose:* Keep task list manageable by archiving old completed work
*Updated:* 2025-11-12 (Phase 2.4 - Archive System Complete)
*Created:* 2025-11-12 (Phase 2.2 - Quick Actions)
*Phase:* 2.4 - Complete