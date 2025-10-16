#!/bin/bash
"""
Immediate Self-Healing Workflow Launcher
Launches the self-healing workflow immediately.
"""

echo "🚀 LAUNCHING SELF-HEALING WORKFLOW"
echo "=================================="

# Set environment variables
export GOOGLE_API_KEY="${GOOGLE_API_KEY_REVOKED}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY_REVOKED}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY_REVOKED}"
export OPENAI_API_KEY="sk-proj-000000000000000000000000000000000000000000000000"

echo "🔑 API keys set"

# Step 1: Check current status
echo "📊 Step 1: Checking current status..."
python3 scripts/immediate_status_checker.py

# Step 2: Kill any stuck processes
echo "🛑 Step 2: Killing stuck processes..."
python3 scripts/deployment_manager.py --action kill

# Step 3: Test all models
echo "🧪 Step 3: Testing all models..."
python3 scripts/individual_model_tester.py

# Step 4: Launch self-healing workflow
echo "🚀 Step 4: Launching self-healing workflow..."
python3 scripts/master_self_healing_orchestrator.py &

# Get the PID of the background process
WORKFLOW_PID=$!

echo "🚀 Self-healing workflow launched (PID: $WORKFLOW_PID)"
echo "📄 Monitor logs in logs/ directory"
echo "🛑 To stop: kill $WORKFLOW_PID"

# Wait a bit and check status
sleep 10
echo "📊 Checking initial status..."
python3 scripts/immediate_status_checker.py

echo "✅ Self-healing workflow is running!"
echo "🔄 It will automatically detect issues, patch them, and redeploy until all models work correctly."
echo "📊 Check logs for detailed progress."

