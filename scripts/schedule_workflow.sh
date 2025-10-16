#!/bin/bash
# Schedule automated workflow for overnight execution
# Schedule: 0 2 * * * (2 AM daily)

echo "🕐 Scheduled Workflow Execution"
echo "==============================="
echo "Time: $(date)"
echo ""

# Change to project directory
cd /Users/ryanranft/nba-mcp-synthesis

# Load workflow-specific environment
if [ -f .env.workflow ]; then
    source .env.workflow
    export GOOGLE_API_KEY DEEPSEEK_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY
    export SLACK_WEBHOOK_URL LINEAR_API_KEY LINEAR_TEAM_ID LINEAR_PROJECT_ID
    echo "✅ Workflow environment loaded"
else
    echo "❌ Error: .env.workflow file not found"
    exit 1
fi

# Validate required environment variables
if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "❌ Error: SLACK_WEBHOOK_URL not set"
    exit 1
fi

if [ -z "$LINEAR_API_KEY" ]; then
    echo "❌ Error: LINEAR_API_KEY not set"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Run workflow
echo "🚀 Starting scheduled workflow..."
python3 scripts/automated_workflow.py \
    --config config/books_to_analyze_all_ai_ml.json \
    --budget 410.0 \
    --slack-webhook "$SLACK_WEBHOOK_URL" \
    --linear-api-key "$LINEAR_API_KEY" \
    --linear-team-id "$LINEAR_TEAM_ID" \
    --linear-project-id "$LINEAR_PROJECT_ID" \
    --slack-channel "$SLACK_CHANNEL" \
    >> logs/automated_workflow_$(date +%Y%m%d).log 2>&1

# Capture exit code
EXIT_CODE=$?

# Send completion notification
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Scheduled workflow completed successfully"

    # Send success notification
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d '{"text": "✅ Scheduled workflow completed successfully! Check Linear for issues and NBA Simulator AWS for implementation files."}' \
        --silent --show-error
else
    echo "❌ Scheduled workflow failed"

    # Send failure notification
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d '{"text": "❌ Scheduled workflow failed - check logs for details"}' \
        --silent --show-error
fi

echo "📁 Logs saved to: logs/automated_workflow_$(date +%Y%m%d).log"
echo "🕐 Execution completed at: $(date)"

exit $EXIT_CODE
