You are helping the user view analytics and insights from the Task Tracker system.

## Command: /analytics

This command provides a comprehensive analytics dashboard showing:
- Velocity metrics (tasks per day/week, trends)
- Completion predictions (when will the project finish?)
- Bottleneck analysis (what's slowing you down?)
- Performance insights and recommendations

## User Intent Detection

Based on the user's input after `/analytics`, determine their intent:

1. **Full dashboard** - If user says:
   - `/analytics`
   - `/analytics dashboard`
   - `/analytics overview`

2. **Velocity only** - If user says:
   - `/analytics velocity`
   - `/analytics speed`
   - `/analytics performance`

3. **Predictions only** - If user says:
   - `/analytics predict`
   - `/analytics forecast`
   - `/analytics completion`

4. **Bottlenecks only** - If user says:
   - `/analytics bottlenecks`
   - `/analytics blocked`
   - `/analytics stuck`

5. **Project-specific** - If user provides project name:
   - `/analytics --project "NBA Analysis"`
   - `/analytics predict --project "Data Pipeline"`

## Instructions

### 1. Full Dashboard (Default)

When user requests full analytics or just types `/analytics`:

**Step 1:** Get all three metrics
```python
# Use all three MCP tools
velocity = mcp__task-tracker__get_velocity_metrics(days=30, project=project_if_specified)
prediction = mcp__task-tracker__predict_completion(project=project_if_specified)
bottlenecks = mcp__task-tracker__get_bottlenecks(project=project_if_specified)
```

**Step 2:** Format as interactive dashboard

```
📊 Task Tracker Analytics Dashboard
═══════════════════════════════════════════════════════════════

PROJECT: [Project Name or "All Projects"]
PERIOD: Last 30 days
GENERATED: 2025-11-12 10:30 AM

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 VELOCITY METRICS                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Tasks Completed: 45 tasks
Average Rate: 1.5 tasks/day | 10.5 tasks/week
Avg Completion Time: 12.3 hours
Trend: 📈 IMPROVING (+23.5%)

Breakdown by Priority:
  🔴 Critical: 5 tasks (avg 8.2 hrs)
  🟠 High: 15 tasks (avg 11.5 hrs)
  🟡 Medium: 20 tasks (avg 14.1 hrs)
  🟢 Low: 5 tasks (avg 18.7 hrs)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔮 COMPLETION PREDICTIONS                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Remaining Tasks: 32 (18 pending, 14 in progress)
  • Critical: 3 tasks
  • High: 10 tasks

Based on current velocity (1.5 tasks/day):

  🎯 Optimistic: Nov 28, 2025 (16 days)
     Assumes: +20% velocity improvement

  📊 Realistic: Dec 3, 2025 (21 days)
     Assumes: Current velocity maintained

  ⚠️  Pessimistic: Dec 10, 2025 (28 days)
     Assumes: -20% velocity decline

Confidence: HIGH (velocity trend is improving)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚧 BOTTLENECK ANALYSIS                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Severity: MEDIUM
Total Issues: 5 bottlenecks detected

Stale Tasks (3):
  • [#42] Fix authentication bug (stale 12 days)
  • [#45] Update documentation (stale 8 days)
  • [#48] Refactor database queries (stale 7 days)

Blocked Tasks (2):
  • [#50] Deploy to production (waiting for approval)
  • [#51] Run integration tests (waiting for test environment)

Common Blockers:
  1. "Waiting for test environment" (2 occurrences)
  2. "Waiting for approval" (1 occurrence)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 💡 RECOMMENDATIONS                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

1. Review 3 stale in-progress tasks - consider breaking down or reassigning
2. Unblock 2 tasks to improve flow
3. Address common blocker: 'Waiting for test environment'

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎯 QUICK ACTIONS                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  [1] View stale tasks         /tasks --view stale
  [2] View blocked tasks        /tasks --view blocked
  [3] Review critical tasks     /tasks --priority critical
  [4] Export analytics          /export --gantt
  [5] Detailed velocity         /analytics velocity
  [6] Update predictions        /analytics predict

═══════════════════════════════════════════════════════════════
```

### 2. Velocity Metrics Only

When user requests just velocity metrics:

**Use:** `mcp__task-tracker__get_velocity_metrics`

**Format output:**

```
🚀 Velocity Metrics - Last 30 Days

OVERALL PERFORMANCE
──────────────────────────────────────
Tasks Completed: 45
Daily Rate: 1.5 tasks/day
Weekly Rate: 10.5 tasks/week
Avg Completion Time: 12.3 hours

TREND ANALYSIS
──────────────────────────────────────
Direction: 📈 IMPROVING
Change: +23.5%
First Half: 18 tasks completed
Second Half: 27 tasks completed

BREAKDOWN BY PRIORITY
──────────────────────────────────────
🔴 Critical: 5 tasks | Avg 8.2 hrs
🟠 High: 15 tasks | Avg 11.5 hrs
🟡 Medium: 20 tasks | Avg 14.1 hrs
🟢 Low: 5 tasks | Avg 18.7 hrs

DAILY BREAKDOWN (Last 7 Days)
──────────────────────────────────────
Nov 5: ████░░░░░░ 2 tasks
Nov 6: ██████░░░░ 3 tasks
Nov 7: ████░░░░░░ 2 tasks
Nov 8: ████████░░ 4 tasks
Nov 9: ██░░░░░░░░ 1 task
Nov 10: ██████░░░░ 3 tasks
Nov 11: ████████░░ 4 tasks

💡 Insights:
• Your velocity is improving! Keep up the momentum.
• Critical tasks are completed fastest (8.2 hrs avg)
• Consider tackling more high-priority tasks for impact

Next: /analytics predict (see completion forecast)
```

### 3. Completion Predictions Only

When user requests predictions:

**Use:** `mcp__task-tracker__predict_completion`

**Format output:**

```
🔮 Project Completion Forecast

CURRENT STATUS
──────────────────────────────────────
Total Remaining: 32 tasks
  • Pending: 18 tasks
  • In Progress: 14 tasks
  • Critical: 3 tasks
  • High Priority: 10 tasks

CURRENT VELOCITY
──────────────────────────────────────
Tasks per Day: 1.5
Based on: Last 30 days
Trend: IMPROVING

COMPLETION SCENARIOS
──────────────────────────────────────

🎯 Optimistic Scenario
   Date: November 28, 2025
   Days: 16 days remaining
   Assumes: +20% velocity improvement
   Probability: If momentum continues

📊 Realistic Scenario  ⭐ RECOMMENDED
   Date: December 3, 2025
   Days: 21 days remaining
   Assumes: Current velocity maintained
   Probability: Most likely outcome

⚠️  Pessimistic Scenario
   Date: December 10, 2025
   Days: 28 days remaining
   Assumes: -20% velocity decline
   Probability: If obstacles arise

CONFIDENCE: HIGH
Reasoning: Velocity trend is improving, consistent completion rate

TIMELINE VISUALIZATION
──────────────────────────────────────
Today          Optimistic    Realistic    Pessimistic
  |──────────────|──────────────|──────────────|
 Nov 12       Nov 28         Dec 3         Dec 10

💡 Tips to Hit Optimistic Target:
1. Focus on unblocking 2 blocked tasks
2. Break down large tasks into smaller chunks
3. Maintain momentum on high-priority items

Next: /analytics bottlenecks (see what's slowing you down)
```

### 4. Bottleneck Analysis Only

When user requests bottleneck analysis:

**Use:** `mcp__task-tracker__get_bottlenecks`

**Format output:**

```
🚧 Bottleneck Analysis

OVERALL HEALTH
──────────────────────────────────────
Severity: MEDIUM
Total Bottlenecks: 5 issues detected
Analysis Date: 2025-11-12 10:30 AM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STALE TASKS (3 found)
Tasks in progress >7 days without updates

1. [#42] Fix authentication bug
   Priority: high | Stale: 12 days
   Project: NBA Auth
   Tags: bug, security
   💡 Action: Review status, consider help needed

2. [#45] Update documentation
   Priority: medium | Stale: 8 days
   Project: NBA Analysis
   Tags: documentation
   💡 Action: Break into smaller tasks

3. [#48] Refactor database queries
   Priority: low | Stale: 7 days
   Project: Data Pipeline
   Tags: optimization
   💡 Action: Re-evaluate priority

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCKED TASKS (2 found)
Tasks waiting on external dependencies

1. [#50] Deploy to production
   Priority: high | Blocked: 5 days
   Blocker: Waiting for test environment
   💡 Action: Setup test environment ASAP

2. [#51] Run integration tests
   Priority: high | Blocked: 5 days
   Blocker: Waiting for test environment
   💡 Action: Same blocker as above

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMMON BLOCKERS
──────────────────────────────────────
1. "Waiting for test environment" - 2 tasks
   → Critical blocker affecting multiple high-priority tasks
   → Recommend: Prioritize test environment setup

2. "Waiting for approval" - 1 task
   → Follow up with approvers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDATIONS
──────────────────────────────────────
1. ⚡ URGENT: Setup test environment (blocking 2 high-priority tasks)
2. 🔍 Review 3 stale tasks - update status or reassign
3. 📋 Consider breaking down task #45 into smaller subtasks
4. 🎯 Focus on unblocking high-priority items first

QUICK ACTIONS
──────────────────────────────────────
  /tasks --view stale        View all stale tasks
  /tasks --view blocked      View all blocked tasks
  /block 50 --unblock        Remove blocker from task
  /update 42 --priority high Increase priority if needed

Next: /analytics velocity (check your completion rate)
```

## Options and Flags

Support these optional parameters:

```
/analytics                          Full dashboard (all projects)
/analytics --project "NBA Analysis"  Dashboard for specific project
/analytics --days 14                Use 14-day window instead of 30
/analytics velocity                 Velocity metrics only
/analytics predict                  Completion predictions only
/analytics bottlenecks              Bottleneck analysis only
/analytics bottlenecks --stale 14   Flag tasks stale >14 days
```

## Error Handling

### No Data Available

If no completed tasks exist:

```
📊 Analytics Dashboard

❌ Insufficient data for analysis

No completed tasks found in the last 30 days.

💡 To get analytics insights:
1. Complete some tasks: /complete <task_id>
2. Try a longer time period: /analytics --days 90
3. Check if project name is correct

Current stats:
  • Total tasks: 25
  • Completed: 0
  • In progress: 5
  • Pending: 20

Get started: /tasks --view focus
```

### Project Not Found

If specified project has no data:

```
❌ Project 'XYZ' not found or has no data

Available projects:
  • NBA Analysis (15 tasks)
  • Data Pipeline (10 tasks)
  • Feature Development (8 tasks)

Try:
  /analytics --project "NBA Analysis"
  /analytics (all projects)
```

## Interactive Features

After showing analytics, provide an interactive menu:

```
What would you like to do?

  [1] View stale tasks
  [2] View blocked tasks
  [3] Export analytics report
  [4] See detailed velocity breakdown
  [5] Update completion predictions
  [6] Focus on critical tasks
  [7] Back to task list

Enter number or command:
```

## Tips for Claude

1. **Use emojis consistently** for visual clarity
2. **Color-code by severity** (🔴 critical, 🟠 high, 🟡 medium, 🟢 low)
3. **Provide actionable insights** not just data
4. **Include next steps** in every output
5. **Format dates clearly** (e.g., "Nov 28, 2025" not "2025-11-28")
6. **Show trends visually** with simple charts (bars, arrows)
7. **Calculate percentages** and trends automatically
8. **Be encouraging** when metrics are positive
9. **Be constructive** when showing bottlenecks

## Example Interactions

### Example 1: Full Dashboard Request
```
User: /analytics

Claude: [Calls all three MCP tools and displays full dashboard with all sections]
```

### Example 2: Project-Specific Analytics
```
User: /analytics --project "NBA Analysis"

Claude: [Shows dashboard filtered to NBA Analysis project only]
```

### Example 3: Quick Velocity Check
```
User: /analytics velocity

Claude: [Shows just velocity metrics with trend analysis]
```

### Example 4: Custom Time Range
```
User: /analytics --days 14

Claude: [Shows dashboard using last 14 days instead of 30]
```

## Integration with Other Commands

The `/analytics` command works well with:

- `/tasks --view stale` - View stale tasks identified
- `/tasks --view blocked` - View blocked tasks identified
- `/tasks --priority critical` - Focus on critical items
- `/export --gantt` - Export timeline visualization
- `/report` - Generate detailed written report
- `/bulk-complete` - Complete multiple stale tasks
- `/block` - Mark tasks as blocked/unblocked

## Success Metrics

A successful analytics session should:
1. ✅ Provide clear, actionable insights
2. ✅ Highlight both wins and concerns
3. ✅ Include specific task IDs for follow-up
4. ✅ Suggest next steps
5. ✅ Use visual formatting effectively
6. ✅ Load quickly (under 2 seconds)
7. ✅ Handle edge cases gracefully

---

**Remember:** Analytics should empower users to make better decisions, not overwhelm them with data!