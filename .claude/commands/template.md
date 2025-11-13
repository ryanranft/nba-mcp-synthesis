You are helping the user work with task templates in the Task Tracker system.

## Command: /template

This command provides a user-friendly interface to task templates, allowing users to:
- List available templates
- Create tasks from templates
- Save existing tasks as templates
- View template details

## User Intent Detection

Based on the user's input after `/template`, determine their intent:

1. **List templates** - If user says:
   - `/template`
   - `/template list`
   - `/template show`
   - `/template available`

2. **Create from template** - If user says:
   - `/template create <template_name> <task_title>`
   - `/template new <template_name> <task_title>`
   - `/template use <template_name> <task_title>`

3. **Save as template** - If user says:
   - `/template save <task_id> <template_name>`
   - `/template create-template <task_id> <template_name>`

4. **View details** - If user says:
   - `/template details <template_name>`
   - `/template info <template_name>`
   - `/template show <template_name>`

## Instructions

### 1. List Templates (Default)

When user requests template list or just types `/template`:

```
Use the MCP tool: mcp__task-tracker__list_templates
```

Format the output as:

```
📋 Available Task Templates

BUILT-IN TEMPLATES (8)
──────────────────────────────────────
🐛 bug_fix
   Standard bug fix workflow (5 subtasks)
   Category: Development

🚀 feature_development
   Full feature development lifecycle (8 subtasks)
   Category: Development

👀 code_review
   Code review checklist (5 subtasks)
   Category: Development

📊 data_analysis
   Data analysis workflow (8 subtasks)
   Category: Analytics

🚢 deployment
   Production deployment checklist (8 subtasks)
   Category: Operations

📝 documentation
   Documentation writing workflow (6 subtasks)
   Category: Documentation

🤖 ml_training
   ML model training pipeline (9 subtasks)
   Category: ML/AI

📅 sprint_planning
   Sprint planning workflow (7 subtasks)
   Category: Planning

CUSTOM TEMPLATES (X)
──────────────────────────────────────
[List any custom templates created by user]

───────────────────────────────────────
💡 Usage:
  /template create <name> <title>     Create task from template
  /template save <id> <name>          Save task as template
  /template details <name>            View template details
```

### 2. Create from Template

When user requests creating a task from a template:

```
Use the MCP tool: mcp__task-tracker__create_from_template

Parameters:
- template_name: The template name specified by user
- title: The task title specified by user
- project: Ask user if not specified
- overrides: Ask user about priority, due_date, additional tags if they want to customize
```

**Workflow:**

1. **Parse user input:**
   - Extract template name (first argument after `create`)
   - Extract task title (remaining arguments)
   - Example: `/template create bug_fix Fix login issue` → template="bug_fix", title="Fix login issue"

2. **Validate template exists:**
   - If template not found, show error with suggestions
   - Use `list_templates` to get available templates

3. **Ask for customization (optional):**
   ```
   Creating task from template 'bug_fix': "Fix login issue"

   Would you like to customize? (optional)
   - Project: [current project or specify]
   - Priority: [template default or high/medium/low]
   - Due date: [none or YYYY-MM-DD]
   - Additional tags: [comma-separated]

   Press Enter to use defaults or provide values.
   ```

4. **Create the task:**
   - Call `create_from_template` with parameters

5. **Display result:**
   ```
   ✅ Task created from template 'bug_fix'

   📋 Parent Task:
      [#100] Fix login issue
      Status: pending | Priority: high | Project: NBA Auth

   📝 Subtasks Created (5):
      [#101] Reproduce bug
      [#102] Identify root cause
      [#103] Implement fix
      [#104] Add regression test
      [#105] Deploy to production

   💡 Next steps:
      • /update 100 --status in_progress (start working)
      • /tasks --parent 100 (view all subtasks)
      • /complete 101 (complete first subtask)
   ```

### 3. Save as Template

When user requests saving a task as a template:

```
Use the MCP tool: mcp__task-tracker__save_as_template

Parameters:
- task_id: The task ID to save
- template_name: Name for the new template
- description: Ask user for description
- category: Ask user for category (optional)
```

**Workflow:**

1. **Parse user input:**
   - Extract task ID (first argument after `save`)
   - Extract template name (second argument)
   - Example: `/template save 42 my_workflow` → task_id=42, template_name="my_workflow"

2. **Validate task exists:**
   - Call `get_task` to verify task exists
   - Show task details and ask for confirmation

3. **Ask for metadata:**
   ```
   Saving task #42 as template 'my_workflow'

   Current task:
   • Title: Deploy new model
   • Subtasks: 5
   • Tags: deployment, ml, production

   Template details:
   - Description: [Brief description of this workflow]
   - Category: [development/analytics/operations/documentation/ml/planning/other]
   ```

4. **Save the template:**
   - Call `save_as_template` with parameters

5. **Display result:**
   ```
   ✅ Template 'my_workflow' created successfully

   📋 Template Details:
      Name: my_workflow
      Description: Custom deployment workflow for ML models
      Category: Operations
      Subtasks: 5

   💡 Use it:
      /template create my_workflow "Deploy recommendation engine"
   ```

### 4. View Template Details

When user requests template details:

```
Use the MCP tool: mcp__task-tracker__get_template_details

Parameters:
- template_name: The template name specified by user
```

**Workflow:**

1. **Parse user input:**
   - Extract template name
   - Example: `/template details bug_fix` → template_name="bug_fix"

2. **Get template details:**
   - Call `get_template_details` with template name

3. **Display detailed information:**
   ```
   📋 Template: bug_fix

   OVERVIEW
   ──────────────────────────────────────
   Description: Standard bug fix workflow
   Category: Development
   Type: Built-in
   Created: 2025-11-12

   DEFAULT SETTINGS
   ──────────────────────────────────────
   Priority: high
   Tags: bug, needs-investigation

   WORKFLOW STEPS (5)
   ──────────────────────────────────────
   1. Reproduce bug
   2. Identify root cause
   3. Implement fix
   4. Add regression test
   5. Deploy to production

   ADDITIONAL METADATA
   ──────────────────────────────────────
   Estimated completion: 3-5 days
   Best for: Production bugs, regression issues

   💡 Usage:
      /template create bug_fix "Fix authentication timeout"
   ```

## Error Handling

### Template Not Found

If template doesn't exist, show helpful error:

```
❌ Template 'bug_fixx' not found

Did you mean one of these?
• bug_fix
• feature_development
• deployment

Use '/template list' to see all available templates.
```

### Invalid Task ID

If task ID doesn't exist when saving:

```
❌ Task #999 not found

💡 Tips:
• Use /tasks to see your active tasks
• Verify the task ID is correct
• Make sure the task hasn't been deleted
```

### Missing Arguments

If user doesn't provide required arguments:

```
❌ Missing required arguments

Usage:
  /template create <template_name> <task_title>

Example:
  /template create bug_fix "Fix login authentication issue"

Use '/template list' to see available templates.
```

## Smart Suggestions

Based on user's recent activity, suggest relevant templates:

- If user recently worked on bugs → suggest `bug_fix`
- If user is starting a sprint → suggest `sprint_planning`
- If user is working on ML tasks → suggest `ml_training` or `data_analysis`
- If user is deploying → suggest `deployment`

## Examples

### Example 1: List Templates
```
User: /template
or
User: /template list

Claude: Shows formatted list of all available templates with descriptions
```

### Example 2: Create from Template (Simple)
```
User: /template create bug_fix "Fix authentication timeout"

Claude:
1. Verifies 'bug_fix' template exists
2. Creates parent task with title "Fix authentication timeout"
3. Creates 5 subtasks from template
4. Shows success message with task IDs and next steps
```

### Example 3: Create from Template (with Customization)
```
User: /template create feature_development "Add dark mode support"

Claude: Creating task from template 'feature_development': "Add dark mode support"

Would you like to customize? (optional)
- Project: [NBA Analysis or specify]
- Priority: [medium or high/low]
- Due date: [none or YYYY-MM-DD]
- Additional tags: [comma-separated]

User: Project: UI Improvements, Priority: high, Due: 2025-11-20, Tags: ui, feature

Claude: ✅ Creates task with custom parameters and template subtasks
```

### Example 4: Save Task as Template
```
User: /template save 42 custom_ml_pipeline

Claude:
1. Retrieves task #42
2. Shows task details
3. Asks for description and category
4. Saves as new template
5. Confirms with usage example
```

### Example 5: View Template Details
```
User: /template details ml_training

Claude: Shows complete template details including:
- Description and category
- Default settings (priority, tags)
- All subtask steps
- Metadata and best use cases
- Usage example
```

## Tips for Claude

1. **Always validate input** before making MCP calls
2. **Provide helpful suggestions** when errors occur
3. **Show examples** in success messages
4. **Format output consistently** with emojis and structure
5. **Ask for clarification** when user input is ambiguous
6. **Suggest next steps** after creating tasks
7. **Be proactive** - suggest templates based on context

## Integration with Other Commands

The `/template` command works well with:

- `/tasks` - View tasks created from templates
- `/update` - Modify template-created tasks
- `/complete` - Mark template subtasks complete
- `/resume` - See template tasks in progress
- `/export` - Export projects with template usage data

## Success Criteria

A successful `/template` interaction should:
1. ✅ Clearly understand user intent
2. ✅ Validate all inputs
3. ✅ Provide helpful error messages
4. ✅ Show formatted, easy-to-read output
5. ✅ Suggest logical next steps
6. ✅ Maintain consistent formatting

---

**Remember:** This command makes task creation 10x faster. Help users discover and use templates effectively!