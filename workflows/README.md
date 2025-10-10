# Workflow Definitions

This directory contains YAML workflow definitions for the NBA MCP Synthesis automated workflow system.

## Available Workflows

### 1. Automated Testing Pipeline (`automated_testing_pipeline.yaml`)

**Purpose:** Automate the complete testing and deployment cycle

**Steps:**
1. Run unit tests with pytest
2. Run integration tests
3. Generate test report
4. **[Approval Required]** Request deployment approval
5. Deploy to production
6. Verify deployment health
7. Send success notification

**Use Case:** Triggered when code changes are pushed. Runs tests, waits for approval, then deploys if all tests pass and approval is granted.

**Example:**
```python
from workflow.engine import WorkflowEngine

engine = WorkflowEngine()
workflow = engine.load_workflow_from_yaml("workflows/automated_testing_pipeline.yaml")
success = await engine.execute_workflow(workflow)
```

---

### 2. NBA Data Synthesis (`nba_data_synthesis.yaml`)

**Purpose:** Automated NBA data extraction, analysis, and report generation

**Steps:**
1. Extract recent game data from RDS
2. Fetch player statistics
3. Load advanced stats from S3
4. Run DeepSeek analysis
5. Run Claude synthesis
6. Generate markdown report
7. Send report to Slack

**Use Case:** Scheduled daily or triggered manually to generate comprehensive NBA analysis reports combining data from multiple sources.

**Example:**
```python
from workflow.engine import WorkflowEngine

engine = WorkflowEngine()

# Register custom actions
engine.register_action("deepseek_synthesis", deepseek_analyze)
engine.register_action("claude_synthesis", claude_synthesize)
engine.register_action("mcp_query_database", mcp_query)

# Load and execute
workflow = engine.load_workflow_from_yaml("workflows/nba_data_synthesis.yaml")
success = await engine.execute_workflow(workflow)
```

---

### 3. Cross-Chat Coordination (`cross_chat_coordination.yaml`)

**Purpose:** Coordinate work across multiple chat sessions (Claude Code, PyCharm, MCP, Web)

**Steps:**
1. Initialize workflow and notify all channels
2. Wait for Claude Code task completion
3. Process Claude Code results
4. Trigger PyCharm analysis
5. Wait for PyCharm results
6. Gather context from MCP server
7. Synthesize all results with Claude
8. Notify all channels of completion

**Use Case:** When a task requires coordination across multiple tools/chats. For example, Claude Code does initial implementation, PyCharm runs tests, MCP gathers data, and results are synthesized.

**Slack Integration:**
- Sends notifications to multiple channels (#claude-code, #pycharm-integration, #mcp-server)
- Each channel can respond to trigger next steps
- Final results distributed to all participating channels

---

## Workflow YAML Format

### Basic Structure

```yaml
workflow_id: unique-workflow-id
name: "Human Readable Name"
description: "What this workflow does"
source: workflow_engine  # or claude_code, pycharm, etc.
notify_slack: true
save_state: true

steps:
  - name: "Step Name"
    description: "What this step does"
    action: action_name
    params:
      key: value
    timeout_seconds: 300
    retry_count: 1
    retry_delay_seconds: 5
    continue_on_failure: false
    requires_approval: false
```

### Field Descriptions

**Top Level:**
- `workflow_id`: Unique identifier for the workflow
- `name`: Human-readable workflow name
- `description`: Brief description of workflow purpose
- `source`: Source that initiated the workflow (workflow_engine, claude_code, pycharm, mcp_server, web_chat, api)
- `notify_slack`: Whether to send Slack notifications (true/false)
- `save_state`: Whether to persist workflow state to disk (true/false)

**Step Fields:**
- `name`: Step name (unique within workflow)
- `description`: What this step does
- `action`: Action to execute (must be registered with WorkflowEngine)
- `params`: Dictionary of parameters passed to action
- `timeout_seconds`: Maximum execution time (default: 300)
- `retry_count`: Number of retries on failure (default: 0)
- `retry_delay_seconds`: Delay between retries (default: 5)
- `continue_on_failure`: Whether to continue workflow if step fails (default: false)
- `requires_approval`: Whether step requires manual approval (default: false)

---

## Registering Custom Actions

Actions are Python functions that workflows can execute. Register them with the WorkflowEngine:

```python
from workflow.engine import get_engine

engine = get_engine()

# Async function
async def my_custom_action(param1: str, param2: int) -> Dict:
    # Do something
    return {"result": "success", "data": result}

# Register it
engine.register_action("my_custom_action", my_custom_action)
```

### Built-in Actions

The following actions are built-in:

- `delay` - Pause for N seconds
- `log` - Log a message
- `notify` - Send Slack notification

---

## Slack Integration

### Notifications

Workflows automatically send Slack notifications at key points:

1. **Workflow Started** - Sent when workflow begins
2. **Step Progress** - Sent for each step (configurable)
3. **Workflow Complete** - Sent when all steps succeed
4. **Workflow Failed** - Sent if any step fails (and continue_on_failure is false)

### Approval Steps

Steps with `requires_approval: true` will:
1. Pause workflow execution
2. Send Slack notification requesting approval
3. Wait for response (default: 60 minutes)
4. Resume when approved or timeout/reject

**Approval Format:**
Reply to the Slack thread with:
- `approve` - Continue workflow
- `reject` - Halt workflow
- `retry` - Retry the step

---

## Cross-Chat Coordination

### How It Works

1. **Workflow starts in any chat** (Claude Code, PyCharm, Web, API)
2. **Slack is the message bus** - All events published to Slack
3. **Other chats listen** for relevant events
4. **Automatic triggering** - When a task completes, next chat can auto-start

### Example Scenario

```
┌─────────────────┐
│  Claude Code    │ - Writes initial implementation
│  (Chat 1)       │ - Notifies Slack: "Code ready for testing"
└────────┬────────┘
         │
         ▼ (Slack notification)
┌─────────────────┐
│  PyCharm        │ - Detects "Code ready" event
│  (IDE)          │ - Runs tests automatically
└────────┬────────┘ - Notifies Slack: "Tests complete (71 passed)"
         │
         ▼ (Slack notification)
┌─────────────────┐
│  MCP Server     │ - Detects "Tests complete" event
│  (Background)   │ - Gathers deployment metrics
└────────┬────────┘ - Notifies Slack: "Metrics collected"
         │
         ▼ (Slack notification)
┌─────────────────┐
│  Claude Web     │ - Detects "All tasks complete"
│  (Chat 2)       │ - Synthesizes final report
└─────────────────┘ - Notifies Slack: "Report ready"
```

### Configuration

Set up Slack webhook in environment:

```bash
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

---

## Running Workflows

### From Python

```python
import asyncio
from workflow.engine import WorkflowEngine

async def main():
    engine = WorkflowEngine()

    # Load workflow from YAML
    workflow = engine.load_workflow_from_yaml(
        "workflows/automated_testing_pipeline.yaml"
    )

    # Execute
    success = await engine.execute_workflow(workflow)

    if success:
        print("✅ Workflow completed successfully")
    else:
        print("❌ Workflow failed")

asyncio.run(main())
```

### From Command Line

```bash
# Run workflow
python -m workflow.cli run workflows/automated_testing_pipeline.yaml

# Check workflow status
python -m workflow.cli status <workflow-id>

# Resume paused workflow
python -m workflow.cli resume <workflow-id>

# Cancel running workflow
python -m workflow.cli cancel <workflow-id>
```

---

## Workflow State

Workflows with `save_state: true` persist their state to `workflow_state/`:

```
workflow_state/
  ├── automated-testing-pipeline.json
  ├── nba-data-synthesis.json
  └── cross-chat-coordination.json
```

This allows workflows to:
- Resume after system restart
- Track progress over time
- Audit workflow history

---

## Best Practices

### 1. Timeouts

Always set realistic timeouts:
- Database queries: 30-60s
- API calls: 60-120s
- AI synthesis: 180-300s
- Tests: 300-600s

### 2. Retries

Use retries for transient failures:
- Network errors: 2-3 retries
- Database timeouts: 1-2 retries
- AI API rate limits: 1 retry with longer delay

### 3. continue_on_failure

Set to `true` for non-critical steps:
- Generating reports
- Sending notifications
- Collecting optional metrics

Set to `false` for critical steps:
- Running tests
- Database migrations
- Deployments

### 4. Approval Gates

Use `requires_approval: true` for:
- Production deployments
- Data migrations
- High-cost operations
- Irreversible actions

---

## Troubleshooting

### Workflow Not Starting

Check:
1. YAML syntax is valid: `yamllint workflows/your_workflow.yaml`
2. All referenced actions are registered
3. Workflow engine is initialized: `engine = WorkflowEngine()`

### Slack Notifications Not Sending

Check:
1. `SLACK_WEBHOOK_URL` environment variable is set
2. Webhook URL is valid
3. Network connectivity to Slack
4. `notify_slack: true` in workflow YAML

### Workflow Stuck on Approval

- Default timeout: 60 minutes
- Reply to Slack thread with: `approve`, `reject`, or `retry`
- Or manually resume: `python -m workflow.cli resume <workflow-id>`

### Action Failed

Check logs:
```bash
tail -f logs/application.log | grep -A 5 "Step failed"
```

Common issues:
- Missing parameters in `params`
- Action not registered
- Timeout too short
- Network/API errors

---

## Examples

See `examples/` directory for complete working examples:
- `examples/simple_workflow.py` - Basic workflow execution
- `examples/custom_actions.py` - Registering custom actions
- `examples/cross_chat_demo.py` - Cross-chat coordination demo
- `examples/slack_integration.py` - Slack notification examples

---

## Next Steps

1. **Create your own workflows** - Copy and modify existing YAML files
2. **Register custom actions** - Add your own action functions
3. **Set up Slack** - Configure webhook for notifications
4. **Test workflows** - Run in development before production
5. **Monitor** - Use Grafana dashboards to track workflow metrics
