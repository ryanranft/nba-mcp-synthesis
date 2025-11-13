# Resume Session - Hierarchical Project View

**Check for existing work and resume where we left off.**

---

## Session Resumption Protocol with Master Task Tracking

You are resuming a Claude Code session. Follow this protocol to display ALL active projects with hierarchical tracking:

### Step 1: Get Enhanced Resume View from Task Tracker MCP

Use the Task Tracker MCP's `get_resume_view_enhanced` tool to get comprehensive project status with visual enhancements:

```
Use the task-tracker MCP tool get_resume_view_enhanced to show all active projects
```

This will return ALL master tasks with **Phase 3 UX Enhancements**:
- 🟢🟡🔴 Color-coded progress bars (Green >75%, Yellow 25-75%, Red <25%)
- 🔴🟡✨ Staleness warnings (Stale >7 days, Warning >3 days, Active <3 days)
- 📈📉➡️  Velocity indicators (Trending up/down/steady)
- Completion percentages (X/Y tasks, N%)
- Last worked-on timestamps
- Time since last worked (hours/days ago)
- Context summaries for each project
- Suggested next actions based on project state
- Health metrics and priority recommendations

### Step 2: Check for HANDOFF Documents

Look for HANDOFF documents in the project root:

```bash
ls -la /Users/ryanranft/nba-mcp-synthesis/HANDOFF*.md 2>/dev/null
```

If any exist, read them to understand previous session context.

### Step 3: Check Git Status

Show current branch and recent commits:

```bash
cd /Users/ryanranft/nba-mcp-synthesis
git status --short
git log --oneline -5
```

### Step 4: Format and Display Enhanced Resume View

Present the information in this format with **Phase 3 visual enhancements**:

```
================================================================================
                    PROJECT RESUME - ACTIVE WORK (Enhanced v3.0)
================================================================================

Last Updated: [timestamp]
Active Projects: [count]
Total Tasks Across All Projects: [total]
Overall Completion: [completed]/[total] ([percentage]%)

📊 Project Health Score: [health_score]/100
   ├─ Stale Projects: [stale_count] 🔴
   ├─ Blocked Projects: [blocked_count] 🚫
   └─ Active Projects: [total_active] ✨

💡 Recommended Next: [recommended_project_title]

--------------------------------------------------------------------------------
#1  PROJECT: [Master Task Title]                 🟢 [████████░░] 78%
--------------------------------------------------------------------------------
Status: [IN PROGRESS] 🔄 | Activity: ✨ ACTIVE | Velocity: 📈 TRENDING UP (5.2%/day)
Last Worked: 2 hours ago | Created: 15 days ago

Suggested Action: ✅ Continue current work

Context:
[context_summary from master task - first 2-3 lines]

Progress:
├─ ✅ Subtask 1 name (COMPLETED)
├─ 🔄 Subtask 2 name (IN PROGRESS) ← Currently Here
├─ ⏸️  Subtask 3 name (PENDING)
└─ ⏸️  Subtask N name (PENDING)

Subtasks: 10 total, 7 completed, 1 in progress, 2 pending

Tags: [tag1, tag2, tag3]

--------------------------------------------------------------------------------
#2  PROJECT: [Second Master Task]                🟡 [███░░░░░░░] 29%
--------------------------------------------------------------------------------
Status: [PAUSED] ⏸️  | Activity: 🟡 WARNING | Velocity: 📉 TRENDING DOWN (2.1%/day)
Last Worked: 4 days ago | Created: 14 days ago

Suggested Action: ⚠️  Resume work to avoid staleness

[Same format continues for all projects...]

--------------------------------------------------------------------------------
#3  PROJECT: [Stale Project]                     🔴 [█░░░░░░░░░] 12%
--------------------------------------------------------------------------------
Status: [PENDING] ⏸️  | Activity: 🔴 STALE | Velocity: 📉 TRENDING DOWN (0.8%/day)
Last Worked: 9 days ago | Created: 15 days ago

Suggested Action: 🚨 Resume this stale project immediately

[... repeat for all active master tasks ...]

================================================================================
                              HANDOFF DOCUMENTS
================================================================================

[List any HANDOFF*.md files found, or "None"]

================================================================================
                                GIT STATUS
================================================================================

Current Branch: [branch name]
Uncommitted Changes:
[list modified files if any, or "Working directory clean"]

Recent Commits:
[last 3-5 commits]

================================================================================
                          QUICK ACTIONS (Enhanced)
================================================================================

What would you like to work on today?

🎯 RECOMMENDED (based on priorities):
   → #[N] "[Recommended project title]" - [suggested_action]

📋 ALL PROJECTS (jump to any):
1. Continue "#1 [Project 1]" (78% complete, ✨ active, 📈 trending up)
2. Resume "#2 [Project 2]" (29% complete, 🟡 warning, 📉 trending down)
3. Restart "#3 [Project 3]" (12% complete, 🔴 STALE, needs immediate attention)
4. Create new master task / project
5. View detailed hierarchy for a specific project
6. Show analytics dashboard

Type your choice (1-6), project number (#1, #2, etc), or describe what you want to work on.
================================================================================
```

### Legend for Enhanced Visual Indicators

**Progress Colors:**
- 🟢 = Excellent progress (>75% complete)
- 🟡 = Moderate progress (25-75% complete)
- 🔴 = Needs attention (<25% complete or stale)

**Activity Status:**
- ✨ ACTIVE = Worked on within 3 days
- 🟡 WARNING = Not worked on for 3-7 days
- 🔴 STALE = Not worked on for >7 days

**Velocity Indicators:**
- 📈 TRENDING UP = Active with high completion rate
- ➡️  STEADY = Moderate progress and activity
- 📉 TRENDING DOWN = Slow progress or stale
- ⏸️  NOT STARTED = No activity yet

**Project Numbers:**
- Use #1, #2, #3 etc for quick jumping
- User can type "/resume 1" or "/resume #1" to jump directly

### Emoji Legend for Task Status

- ✅ = Completed
- 🔄 = In Progress (mark with arrow: ← Currently Here)
- ⏸️ = Pending
- 🚫 = Blocked
- ❌ = Cancelled

### Progress Bar Format

10-character bar: `[█████████░]` where:
- █ = 10% completed
- ░ = 10% remaining

Examples:
- `[██████████]` = 100% (10/10 filled)
- `[█████░░░░░]` = 50% (5/10 filled)
- `[███░░░░░░░]` = 30% (3/10 filled)

### Step 5: Hierarchical Task Display

If the user asks to see detailed hierarchy for a specific project, use:

```
Use the task-tracker MCP tool get_task_hierarchy with task_id=[master_task_id]
```

Display the full nested structure:

```
Master Task: [Title]
├─ Task 1: [name] (status)
│  ├─ Subtask 1.1: [name] (status)
│  ├─ Subtask 1.2: [name] (status)
│  └─ Subtask 1.3: [name] (status)
├─ Task 2: [name] (status)
│  ├─ Subtask 2.1: [name] (status)
│  │  ├─ Sub-subtask 2.1.1: [name] (status)
│  │  └─ Sub-subtask 2.1.2: [name] (status)
│  └─ Subtask 2.2: [name] (status)
└─ Task 3: [name] (status)
```

### Step 6: Ask User What to Continue

After displaying the resume view, ask:

**"What would you like to work on today?"**

Options to offer:
1. Continue specific project (show which task is in_progress)
2. Switch to different project (show last_worked time)
3. Start new work (create new master task)
4. Review completed work
5. Other (let user specify)

### Step 7: Resume Work Based on Choice

**If user chooses to continue a project:**
1. Get the task hierarchy for that master task
2. Find the task marked 'in_progress'
3. Show context and next steps
4. Begin working

**If user chooses to switch projects:**
1. Ask which project to switch to
2. Mark current in_progress task (if any) with note about switching
3. Get hierarchy for new project
4. Ask which task to start
5. Mark that task as 'in_progress'
6. Begin working

**If user starts new work:**
1. Follow normal task creation flow
2. Check if it should be a master task (large initiative)
3. Create appropriately with MCP tools

---

## Important Notes

- **Use Task Tracker MCP:** All task data comes from the `task-tracker` MCP server
- **Show ALL projects:** Display every active master task, not just the most recent
- **Highlight bouncing:** If user has bounced between projects, show ALL of them clearly
- **Time context:** Always show "last worked" times so user knows what's stale
- **Context summaries:** Show enough context that user remembers what each project is about
- **Progress percentages:** Show exact completion (e.g., "14/18 tasks, 78%")

---

## Tools to Use

**Primary tool:**
- `get_resume_view` from task-tracker MCP

**Supporting tools (as needed):**
- `get_task_hierarchy` - Show full nested structure
- `get_master_tasks_with_progress` - Alternative view of just masters
- `calculate_completion_percentage` - Recalculate progress for specific task
- `update_context_summary` - Update project description
- `get_active_handoffs` - Show handoff documents from database

---

## Example Session Start

```
You: /resume

Claude: Let me check what you've been working on...

[Calls get_resume_view MCP tool]

================================================================================
                    PROJECT RESUME - ACTIVE WORK
================================================================================

Last Updated: 2025-11-12 14:30:00
Active Projects: 3
Total Tasks Across All Projects: 47
Overall Completion: 28/47 (59.6%)

--------------------------------------------------------------------------------
 PROJECT 1: Build Kelly Criterion Betting System              [████████░░] 78%
--------------------------------------------------------------------------------
Status: IN PROGRESS (🔄)
Last Worked: 2 hours ago
Created: 5 days ago

Context:
Building a calibrated Kelly Criterion betting system for NBA games that
corrects simulation bias. Train Bayesian calibrator on historical pred...

Progress:
├─ ✅ Phase 1: Feature Engineering (COMPLETED)
├─ ✅ Phase 2: Ensemble Model Training (COMPLETED)
├─ ✅ Phase 3: Historical Backtesting (COMPLETED)
├─ 🔄 Phase 4: Bayesian Calibrator Training (IN PROGRESS) ← Currently Here
├─ ⏸️ Phase 5: Production Deployment (PENDING)
└─ ⏸️ Phase 6: Monitoring & Alerting (PENDING)

Subtasks: 18 total, 14 completed, 1 in progress, 3 pending
Tags: betting, calibration, production, ml

--------------------------------------------------------------------------------
 PROJECT 2: Implement 7 MCPs for Betting System               [███░░░░░░░] 29%
--------------------------------------------------------------------------------
Status: PAUSED (⏸️)
Last Worked: 3 days ago
Created: 1 week ago

Context:
Implement 7 MCP servers (GitHub, Memory, Brave Search, Puppeteer, Time,
Fetch, AWS Knowledge) to enhance Claude Code capabilities for NBA bet...

Progress:
├─ ✅ Research and create master guide (COMPLETED)
├─ ✅ Create individual implementation docs (COMPLETED)
├─ ⏸️ Implement GitHub MCP (PENDING)
├─ ⏸️ Implement Memory MCP (PENDING)
├─ ⏸️ Implement Brave Search MCP (PENDING)
├─ ⏸️ Implement Puppeteer MCP (PENDING)
├─ ⏸️ Implement Time/Everything MCP (PENDING)
├─ ⏸️ Implement Fetch MCP (PENDING)
└─ ⏸️ Implement AWS Knowledge MCP (PENDING)

Subtasks: 17 total, 5 completed, 0 in progress, 12 pending
Tags: mcp, infrastructure, tooling

--------------------------------------------------------------------------------
 PROJECT 3: Hierarchical Task Tracking System                 [██████████] 100%
--------------------------------------------------------------------------------
Status: COMPLETED (✅)
Last Worked: Just now
Created: Today

Context:
Build hierarchical master task tracking with automatic detection, unlimited
nesting, completion percentages, and comprehensive resume view.

Progress:
├─ ✅ Create database migration (COMPLETED)
├─ ✅ Add 6 new MCP tools (COMPLETED)
├─ ✅ Enhance UserPromptSubmit hook (COMPLETED)
└─ ✅ Update /resume command (COMPLETED)

Subtasks: 10 total, 10 completed, 0 in progress, 0 pending
Tags: task-tracking, infrastructure, automation

================================================================================

What would you like to work on today?

1. Resume "Build Kelly Criterion Betting System" (continue Phase 4: Calibrator Training)
2. Switch to "Implement 7 MCPs" (implement GitHub MCP)
3. Create new project/master task
4. Other
```

---

## Quick Resume - Jump to Specific Project

**New in Phase 2.2:** Support for `/resume <project_id>` to jump directly to a project.

### Usage

```
/resume          - Show all projects (default behavior above)
/resume 1        - Jump to project #1 from the list
/resume <id>     - Jump to master task by ID
```

### Behavior for `/resume <N>`

When user provides a number:

1. **Get resume view** (same as above)
2. **If N is 1-9:** Treat as position in project list
   - `/resume 1` → Jump to first project in resume view
   - `/resume 2` → Jump to second project
3. **If N is > 10:** Treat as master_task_id
   - `/resume 123` → Jump to master task ID 123

**Display for direct jump:**

```
================================================================================
                    RESUMING: <Project Title>
================================================================================

Status: IN PROGRESS (🔄)
Last Worked: 2 hours ago
Progress: [████████░░] 78% (14/18 tasks)

Context:
<context_summary from master task>

Current Task:
🔄 Phase 4: Bayesian Calibrator Training ← You are here

Next Steps:
1. Complete current task
2. Move to Phase 5: Production Deployment

Full Task List:
├─ ✅ Phase 1: Feature Engineering (COMPLETED)
├─ ✅ Phase 2: Ensemble Model Training (COMPLETED)
├─ ✅ Phase 3: Historical Backtesting (COMPLETED)
├─ 🔄 Phase 4: Bayesian Calibrator Training (IN PROGRESS)
├─ ⏸️ Phase 5: Production Deployment (PENDING)
└─ ⏸️ Phase 6: Monitoring & Alerting (PENDING)

================================================================================

Ready to continue? Let's pick up where we left off.
```

### Implementation

```
1. Parse argument: /resume <arg>
2. If no arg: execute default resume (show all projects)
3. If arg is digit:
   - Get resume view to get project list
   - If arg <= len(projects): use projects[arg-1]['master_id']
   - Else: use arg as master_task_id directly
4. Call: get_task_hierarchy(master_task_id)
5. Display focused view for that project only
```

---

*Command Purpose:* Start each session with complete visibility into ALL active projects, never lose track when bouncing between work.
*Created:* 2025-11-12
*Enhanced:* Hierarchical Master Task Tracking (Phase 4)
*Enhanced:* Quick Resume with Direct Jump (Phase 2.2)