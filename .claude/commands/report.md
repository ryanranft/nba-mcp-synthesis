# Generate Summary Report

**Generate weekly/monthly summary reports of task activity.**

Phase 3 UX Enhancement: Regular reporting for productivity tracking.

---

## Usage

```
/report [period]
/report [period] [save]
```

**Arguments:**
- `period` - Report period: weekly (default), monthly, all
- `save` - Optional: save report to file

---

## Report Periods

### Weekly (Default)

Last 7 days of activity.

**Example:**
```
/report
/report weekly
```

### Monthly

Last 30 days of activity.

**Example:**
```
/report monthly
```

### All Time

Complete task history (limited to last 100 completed tasks).

**Example:**
```
/report all
```

---

## Report Contents

### Statistics Section

```
📊 STATISTICS
--------------------------------------------------------------------------------
Tasks Completed: 45
Tasks In Progress: 12
Tasks Pending: 28
Tasks Blocked: 3
Critical Priority: 2
High Priority: 15
Velocity: 6.4 tasks/day
```

### Active Projects Section

```
🏗️  ACTIVE PROJECTS
--------------------------------------------------------------------------------
🔄 User Authentication System - 78% (14/18 tasks)
🔄 Dashboard Redesign - 45% (9/20 tasks)
⏸️  API Documentation - 12% (4/37 tasks)
✅ Bug Fix Sprint - 100% (8/8 tasks)
```

### Recently Completed Tasks Section

```
✅ RECENTLY COMPLETED TASKS
--------------------------------------------------------------------------------
• Implement OAuth integration [HIGH] - 2025-11-12
• Write integration tests - 2025-11-12
• Deploy to staging - 2025-11-11
• Fix login timeout issue [CRITICAL] - 2025-11-11
• Update documentation - 2025-11-10
...
```

---

## How It Works

### Step 1: Parse Arguments

```
Examples:
/report                   # Weekly report
/report monthly           # Monthly report
/report weekly save       # Save weekly report to file
/report all              # All-time report
```

### Step 2: Generate Report

```
Use the task-tracker MCP tool generate_summary_report with:
- period: [weekly/monthly/all]
- include_projects: true
- include_statistics: true
```

### Step 3: Display Report

```
================================================================================
TASK TRACKER SUMMARY REPORT - Last 7 Days
================================================================================
Generated: 2025-11-12 14:30:00

📊 STATISTICS
--------------------------------------------------------------------------------
Tasks Completed: 45
Tasks In Progress: 12
Tasks Pending: 28
Tasks Blocked: 3
Critical Priority: 2
High Priority: 15
Velocity: 6.4 tasks/day

🏗️  ACTIVE PROJECTS
--------------------------------------------------------------------------------
🔄 User Authentication System - 78% (14/18 tasks)
🔄 Dashboard Redesign - 45% (9/20 tasks)
⏸️  API Documentation - 12% (4/37 tasks)
✅ Bug Fix Sprint - 100% (8/8 tasks)

✅ RECENTLY COMPLETED TASKS
--------------------------------------------------------------------------------
• Implement OAuth integration [HIGH] - 2025-11-12
• Write integration tests - 2025-11-12
• Deploy to staging - 2025-11-11
• Fix login timeout issue [CRITICAL] - 2025-11-11
• Update documentation - 2025-11-10
• Refactor user service - 2025-11-10
• Add missing unit tests - 2025-11-09
• Optimize database queries - 2025-11-09
• Update outdated documentation - 2025-11-08
• Remove unused code - 2025-11-08

================================================================================
```

### Step 4: Save to File (Optional)

If `save` option provided:
```
File saved to: TASK_REPORT_{period}_{timestamp}.txt
Example: TASK_REPORT_weekly_20251112_143000.txt
```

---

## Examples

**Weekly report (default):**
```
/report
/report weekly
```

**Monthly report:**
```
/report monthly
```

**All-time summary:**
```
/report all
```

**Save weekly report:**
```
/report weekly save
```

**Save monthly report:**
```
/report monthly save
```

---

## Use Cases

### 1. Weekly Standup/Planning

Review last week's progress:
```
/report weekly
```

Use output for:
- Team standup meetings
- Sprint retrospectives
- Personal productivity tracking

### 2. Monthly Reviews

End-of-month summary:
```
/report monthly save
```

Use for:
- Performance reviews
- Project status updates
- Stakeholder reporting

### 3. Velocity Tracking

Monitor productivity trends:
```
/report weekly
# Check velocity: 6.4 tasks/day

# Next week:
/report weekly
# Compare velocity: 7.2 tasks/day (improved!)
```

### 4. Project Health Check

Identify stale or blocked projects:
```
/report monthly
```

Review active projects section:
- Which projects are stuck at low %?
- Are there too many blocked tasks?
- Which projects need attention?

### 5. Completion Tracking

See what you've accomplished:
```
/report monthly
```

Review completed tasks section:
- Celebrate wins
- Track deliverables
- Report to stakeholders

---

## Report Metrics Explained

### Velocity

**Tasks completed per day** in the period.

```
Example: 45 tasks completed / 7 days = 6.4 tasks/day
```

**Good velocity:**
- 5-10 tasks/day for individual work
- 3-5 tasks/day for complex projects
- 10+ tasks/day for bug fix sprints

**Low velocity (<3 tasks/day):**
- Tasks may be too large (break down)
- Blockers impacting progress
- Need to focus efforts

### Completion Rate

**Percentage of tasks completed** vs total active.

```
Example: 45 completed / (45 completed + 12 in progress + 28 pending) = 53%
```

**Healthy completion rate:**
- 60-80% for ongoing work
- 90%+ for sprint-based work

### Project Progress

**Completion percentage** for each master task.

```
🔄 User Authentication - 78% (14/18 tasks)
```

**On track:** >50% for active projects
**At risk:** <30% and multiple weeks old
**Stale:** <20% and no recent activity

---

## Customization Options

### Statistics Only

```
/report weekly stats-only
```

Excludes projects and completed task lists.

### Projects Only

```
/report weekly projects-only
```

Excludes statistics and task lists.

### Completed Tasks Only

```
/report weekly completed-only
```

Shows only completed tasks list.

---

## Saving Reports

### Auto-Generated Filenames

```
TASK_REPORT_weekly_20251112_143000.txt
TASK_REPORT_monthly_20251112_143000.txt
TASK_REPORT_all_20251112_143000.txt
```

Format: `TASK_REPORT_{period}_{date}_{time}.txt`

### Custom Filenames

```
/report weekly save path:~/Documents/weekly_standup_2025-11-12.txt
/report monthly save path:/Users/user/reports/november_2025.txt
```

---

## Regular Reporting Workflow

### End of Week

```bash
# Friday afternoon
/report weekly save

# Review velocity and completion rate
# Plan next week based on blocked/pending tasks
```

### End of Month

```bash
# Last day of month
/report monthly save

# Review overall progress
# Share with team/stakeholders
# Identify trends and improvements
```

### Sprint Retrospective

```bash
# End of 2-week sprint
/report weekly
/report weekly

# Compare both weeks
# Discuss velocity changes
# Identify blockers
```

---

## Interpreting Reports

### Green Flags 🟢

- Velocity >5 tasks/day
- Completion rate >60%
- Projects progressing (>50% complete)
- Few blocked tasks (<5% of total)
- High priority tasks being completed

### Yellow Flags 🟡

- Velocity 3-5 tasks/day (could improve)
- Completion rate 40-60%
- Some projects stalled (<30% but old)
- 5-10% tasks blocked
- High priority tasks pending

### Red Flags 🔴

- Velocity <3 tasks/day
- Completion rate <40%
- Multiple stale projects (>7 days no activity)
- >10% tasks blocked
- Critical tasks pending/blocked

**Action items for red flags:**
1. Review task sizes (too large?)
2. Identify and resolve blockers
3. Reprioritize work
4. Consider archiving stale projects
5. Focus on fewer projects

---

## Related Commands

- `/export <id>` - Export specific project
- `/resume` - View all active projects
- `/tasks stale` - See stale tasks
- `/tasks blocked` - See blocked tasks
- `/analytics` - Detailed analytics dashboard

---

*Command Purpose:* Regular reporting for productivity tracking and stakeholder updates
*Created:* 2025-11-12 (Phase 3)
*Enhancement:* Summary reports for improved visibility and accountability