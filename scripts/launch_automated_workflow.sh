#!/bin/bash
# Launch automated workflow with all notifications

echo "🚀 Launching Automated Book Analysis Workflow"
echo "=============================================="

# Load workflow-specific environment
if [ -f .env.workflow ]; then
    echo "📋 Loading workflow environment from .env.workflow..."
    source .env.workflow
    export GOOGLE_API_KEY DEEPSEEK_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY
    export SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW LINEAR_API_KEY LINEAR_TEAM_ID LINEAR_PROJECT_ID
    echo "✅ Workflow environment loaded"
else
    echo "❌ Error: .env.workflow file not found"
    echo "Please create .env.workflow with your API keys and credentials"
    exit 1
fi

# Validate required variables
echo "🔑 Validating required variables..."
missing_vars=()


if [ -z "$SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW" ]; then
    missing_vars+=("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW")
fi

if [ -z "$LINEAR_API_KEY" ]; then
    missing_vars+=("LINEAR_API_KEY")
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    missing_vars+=("GOOGLE_API_KEY")
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    missing_vars+=("DEEPSEEK_API_KEY")
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    missing_vars+=("ANTHROPIC_API_KEY")
fi

if [ -z "$OPENAI_API_KEY" ]; then
    missing_vars+=("OPENAI_API_KEY")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing required variables: ${missing_vars[*]}"
    echo "Please add these to your .env.workflow file"
    exit 1
fi

echo "✅ All required variables validated"

# Send start notification
echo "📢 Sending start notification to Slack..."
curl -X POST "$SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW" \
    -H 'Content-Type: application/json' \
    -d '{"text": "🚀 Starting automated book analysis workflow..."}' \
    --silent --show-error

if [ $? -eq 0 ]; then
    echo "✅ Start notification sent"
else
    echo "⚠️  Failed to send start notification (continuing anyway)"
fi

# Create logs directory
mkdir -p logs

# Run workflow
echo "🔄 Starting workflow..."
echo "📊 Monitor progress in Slack: ${SLACK_CHANNEL:-#nba-simulator-notifications}"
echo "📋 Check Linear for created issues"
echo ""

python3 scripts/automated_workflow.py \
    --config config/books_to_analyze_all_ai_ml.json \
    --budget 410.0 \
    --slack-webhook "$SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW" \
    --linear-api-key "$LINEAR_API_KEY" \
    --linear-team-id "$LINEAR_TEAM_ID" \
    --linear-project-id "$LINEAR_PROJECT_ID" \
    --slack-channel "$SLACK_CHANNEL" \
    2>&1 | tee logs/automated_workflow_$(date +%Y%m%d_%H%M%S).log

# Capture exit code
EXIT_CODE=$?

# Send completion notification
echo ""
echo "📢 Sending completion notification..."

if [ $EXIT_CODE -eq 0 ]; then
    curl -X POST "$SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW" \
        -H 'Content-Type: application/json' \
        -d '{"text": "✅ Workflow completed successfully! Check Linear for issues and NBA Simulator AWS for implementation files."}' \
        --silent --show-error
    echo "✅ Workflow completed successfully!"
else
    curl -X POST "$SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW" \
        -H 'Content-Type: application/json' \
        -d '{"text": "❌ Workflow failed - check logs for details"}' \
        --silent --show-error
    echo "❌ Workflow failed - check logs"
fi

echo ""
echo "📁 Logs saved to: logs/automated_workflow_$(date +%Y%m%d_%H%M%S).log"
echo "📋 Check Linear project for created issues"
echo "📁 Check /Users/ryanranft/nba-simulator-aws/docs/phases/ for implementation files"

exit $EXIT_CODE
