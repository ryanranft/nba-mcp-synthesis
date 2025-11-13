# Automatic Task Tracking System
## NBA MCP Synthesis Project

**Status:** ✅ Fully Implemented
**Version:** 1.0
**Last Updated:** 2025-11-12

---

## Overview

The Automatic Task Tracking System provides persistent, cross-session task tracking for Claude Code. This system prevents context loss between sessions and ensures Claude always knows what work is in progress.

### Architecture

The system consists of 3 phases working together:

1. **Phase 1: CLAUDE.md Instructions** - Claude knows when and how to create tasks
2. **Phase 2: UserPromptSubmit Hook** - Automatically extracts tasks from user prompts
3. **Phase 3: Task Tracker MCP** - Persistent storage in PostgreSQL database

---

## Phase 1: Task Tracking Protocol

**File:** `.claude/CLAUDE.md`

Added comprehensive task tracking protocol that instructs Claude to:
- Create tasks immediately for multi-step work
- Update task status before starting and after completing
- Have exactly ONE task "in_progress" at a time
- Follow session start/during/end protocols

### Slash Command: `/resume`

**File:** `.claude/commands/resume.md`

Type `/resume` at session start to:
- Check for HANDOFF documents from previous sessions
- Check for pending tasks
- Display git status and recent commits
- Ask what to work on today

**Usage:**
```bash
/resume
```

---

## Phase 2: Automatic Task Extraction

**File:** `.claude/hooks/user_prompt_submit.py`
**Config:** `.claude/settings.local.json`

The UserPromptSubmit hook automatically:
- Parses user prompts for action verbs (research, analyze, build, etc.)
- Detects multi-step work (numbered lists, bullet points)
- Extracts potential tasks
- Injects task context before Claude processes the prompt
- Reminds Claude to use TodoWrite tool

### Action Verbs Detected

research, analyze, build, create, fix, implement, investigate, compare, test, deploy, update, refactor, add, remove, delete, modify, write, read, review, setup, configure, install, debug, optimize, migrate, integrate, document, verify, validate, monitor, track

### How It Works

1. User enters prompt
2. Hook parses prompt for task indicators
3. If tasks detected, injects reminder to use TodoWrite
4. Claude processes enhanced prompt with task context

---

## Phase 3: Persistent Task Storage

**Database:** `claude_tasks` (PostgreSQL)
**MCP Server:** `.claude/task_tracker/task_tracker_mcp.py`
**Config:** `.claude/mcp.json` + `.claude/settings.local.json`

### Database Schema

**Tables:**
- `tasks` - Main tasks table
- `task_tags` - Tags for categorization
- `task_history` - Audit trail of status changes
- `handoff_documents` - Complex multi-session work
- `sessions` - Track Claude Code sessions

**Views:**
- `active_tasks` - All pending/in_progress tasks
- `recent_completed_tasks` - Last 7 days completions
- `task_statistics` - Overall statistics

### MCP Tools Available

**Task Management:**
- `create_task` - Create new task
- `list_tasks` - List tasks with filtering
- `update_task_status` - Change task status
- `get_active_tasks` - Get all active tasks
- `search_tasks` - Search by content

**Analytics:**
- `get_task_statistics` - Overall stats
- `get_task_history` - Status change history

**Handoffs:**
- `create_handoff_document` - For complex multi-session work
- `get_active_handoffs` - List active handoffs

**Organization:**
- `add_task_tags` - Tag tasks for categorization

---

## Database Setup

### Initial Setup

The database is already created and initialized. To recreate:

```bash
python3 .claude/task_tracker/setup_database.py
```

**Output:**
```
✅ Database 'claude_tasks' created successfully
✅ Schema initialized successfully
✅ Tables created: tasks, task_tags, task_history, handoff_documents, sessions
✅ Views created: active_tasks, recent_completed_tasks, task_statistics
✅ Connection successful - 0 tasks in database
```

### Database Access

The Task Tracker MCP automatically uses the hierarchical secrets system:
- Production: `/Users/ryanranft/Desktop/++/big_cat_bets_assets/.../nba-mcp-synthesis/.env.nba_mcp_synthesis.production/`
- Same credentials as main NBA database
- Separate `claude_tasks` database for isolation

---

## Usage Guide

### Session Start

1. **Type `/resume` to check for existing work:**
   ```bash
   /resume
   ```

2. **Claude will:**
   - Check for HANDOFF documents
   - Show pending tasks (if any)
   - Display git status
   - Ask what to work on

3. **Respond with your goal:**
   ```
   "I want to implement the Fetch MCP from the MCP implementation guide"
   ```

4. **Claude will:**
   - Create TodoWrite tasks for the work
   - Mark first task as "in_progress"
   - Begin working

### During Work

Claude will automatically:
- Update task status before starting each task
- Mark tasks completed immediately after finishing
- Have exactly ONE task "in_progress" at a time
- Track progress with TodoWrite

### Session End

Before ending the session:
1. **Review tasks:** Claude verifies all statuses are accurate
2. **For incomplete work:** Claude may suggest creating HANDOFF document
3. **Summary:** Claude tells you what was completed and what remains

---

## Testing the System

### Test 1: Hook Activation

**Test the UserPromptSubmit hook:**

```bash
# The hook should automatically detect this as multi-step work
echo "Can you analyze the MCP implementation guide and create a summary?" | python3 .claude/hooks/user_prompt_submit.py
```

**Expected:** Hook outputs task extraction context to stderr

### Test 2: Database Connection

**Test database connection:**

```bash
python3 .claude/task_tracker/setup_database.py
```

**Expected:** ✅ All checks pass, 0 tasks in database

### Test 3: MCP Server Startup

**Test MCP server starts:**

```bash
timeout 5 python3 .claude/task_tracker/task_tracker_mcp.py 2>&1
```

**Expected:** Server waits for MCP protocol messages (timeout is normal)

### Test 4: MCP Tools (After Restart)

After restarting Claude Code:

1. **Check MCP connection:**
   ```bash
   /mcp
   ```
   **Expected:** "task-tracker" appears in list

2. **Create a test task:**
   ```
   Ask Claude: "Use the task-tracker MCP to create a task with content 'Test task tracking system' and active_form 'Testing task tracking system'"
   ```

3. **List active tasks:**
   ```
   Ask Claude: "Use task-tracker to get active tasks"
   ```

4. **Get statistics:**
   ```
   Ask Claude: "Use task-tracker to get task statistics"
   ```

### Test 5: End-to-End Workflow

**Complete workflow test:**

1. Type `/resume`
2. Say: "I need to implement GitHub MCP from the guide and test it"
3. **Expected:** Claude creates TodoWrite tasks for the work
4. Watch as Claude works through tasks, updating status
5. **Verify:** Exactly ONE task "in_progress" at a time
6. **Verify:** Tasks marked "completed" immediately after finishing

---

## Monitoring Tasks

### View Active Tasks (SQL)

```sql
-- Connect to claude_tasks database
psql -h [RDS_HOST] -U [USER] -d claude_tasks

-- View active tasks
SELECT * FROM active_tasks;

-- View statistics
SELECT * FROM task_statistics;

-- View recent completed tasks
SELECT * FROM recent_completed_tasks;

-- View all tasks for a project
SELECT id, content, status, priority, created_at
FROM tasks
WHERE project = 'nba-mcp-synthesis'
ORDER BY created_at DESC
LIMIT 20;
```

### Using Task Tracker MCP

**From Claude Code:**

```
"Show me all active tasks"
→ Claude uses get_active_tasks tool

"Show me task statistics"
→ Claude uses get_task_statistics tool

"Search for tasks related to MCP"
→ Claude uses search_tasks tool

"Create a handoff document for the MCP implementation work"
→ Claude uses create_handoff_document tool
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     User Prompt                          │
│  "Can you implement Fetch MCP and test it?"             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  UserPromptSubmit Hook        │
        │  (.claude/hooks/...)          │
        │                               │
        │  - Extracts: "implement",    │
        │    "test" (action verbs)     │
        │  - Detects: multi-step work  │
        │  - Injects: task context     │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Claude Code Processes        │
        │  (.claude/CLAUDE.md protocol) │
        │                               │
        │  - Reads task protocol        │
        │  - Creates TodoWrite tasks    │
        │  - Updates status as works    │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────┐              ┌─────────────────────┐
│  TodoWrite   │              │  Task Tracker MCP   │
│  (session)   │              │  (persistent)       │
│              │              │                     │
│  - Current   │              │  - PostgreSQL DB    │
│    session   │              │  - Cross-session    │
│  - Temporary │              │  - Audit trail      │
└──────────────┘              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  claude_tasks DB     │
                              │                      │
                              │  - tasks             │
                              │  - task_history      │
                              │  - handoff_documents │
                              │  - statistics        │
                              └──────────────────────┘
```

---

## File Structure

```
.claude/
├── CLAUDE.md                          # Task tracking protocol
├── commands/
│   └── resume.md                      # /resume slash command
├── hooks/
│   └── user_prompt_submit.py          # Automatic task extraction
├── settings.local.json                # Hook + MCP configuration
├── mcp.json                           # MCP server config
└── task_tracker/
    ├── README.md                      # This file
    ├── schema.sql                     # Database schema
    ├── setup_database.py              # Database setup script
    └── task_tracker_mcp.py            # Task Tracker MCP server
```

---

## Troubleshooting

### Hook Not Running

**Symptom:** Tasks not being extracted from prompts

**Solution:**
1. Check `.claude/settings.local.json` has hooks configured
2. Verify hook script is executable: `chmod +x .claude/hooks/user_prompt_submit.py`
3. Test hook manually: `echo "test prompt" | python3 .claude/hooks/user_prompt_submit.py`

### MCP Not Connecting

**Symptom:** task-tracker not in `/mcp` list

**Solution:**
1. Check `.claude/mcp.json` has task-tracker configured
2. Check `.claude/settings.local.json` has "task-tracker" in enabledMcpjsonServers
3. Restart Claude Code completely
4. Test MCP server: `python3 .claude/task_tracker/task_tracker_mcp.py`

### Database Connection Errors

**Symptom:** MCP tools fail with connection errors

**Solution:**
1. Verify database exists: `psql -h [HOST] -U [USER] -l | grep claude_tasks`
2. Run setup if needed: `python3 .claude/task_tracker/setup_database.py`
3. Check credentials loaded: `python3 -c "from mcp_server.unified_secrets_manager import load_secrets_hierarchical; load_secrets_hierarchical(); import os; print(os.getenv('RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW'))"`

### Tasks Not Persisting

**Symptom:** Tasks disappear between sessions

**Solution:**
- TodoWrite tasks are session-only (expected)
- For cross-session persistence, Claude must use Task Tracker MCP tools
- Verify task-tracker MCP is connected and enabled

---

## Future Enhancements

### Planned Improvements

1. **Automatic session detection** - Generate unique session_id automatically
2. **Task dependencies** - Track task dependencies and blockers
3. **Time tracking** - Automatic duration tracking for tasks
4. **Priority adjustments** - Auto-adjust priority based on age/context
5. **Handoff templates** - Pre-built templates for common handoff scenarios
6. **Task analytics** - Velocity, completion rates, time estimates
7. **Integration with TodoWrite** - Sync TodoWrite → Task Tracker MCP
8. **Slack/SMS notifications** - Alert on task completion/blockers
9. **Task templates** - Pre-defined task lists for common workflows
10. **Visual dashboard** - Web UI for task tracking

---

## Benefits

### Problem Solved

**Before:** Context lost between Claude Code sessions, work duplicated, progress forgotten

**After:**
- ✅ Persistent task tracking across sessions
- ✅ Automatic task extraction from prompts
- ✅ Clear progress visibility
- ✅ Audit trail of all work
- ✅ Handoff documents for complex work
- ✅ Statistical insights

### Key Features

1. **Automatic** - Tasks extracted and tracked without manual effort
2. **Persistent** - Cross-session continuity with PostgreSQL storage
3. **Auditable** - Complete history of all status changes
4. **Searchable** - Find tasks by content, tags, status
5. **Integrated** - Works seamlessly with existing workflow
6. **Secure** - Uses hierarchical secrets management

---

## Credits

**Implemented:** 2025-11-12
**System Components:**
- Phase 1: CLAUDE.md + /resume command
- Phase 2: UserPromptSubmit hook
- Phase 3: Task Tracker MCP + PostgreSQL

**Technologies:**
- FastMCP framework
- PostgreSQL database
- Python 3
- Claude Code hooks system
- Hierarchical secrets management

---

*For questions or issues, refer to project documentation or create an issue.*
