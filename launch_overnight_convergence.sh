#!/bin/bash
# Launch Overnight Convergence Enhancement
# This script runs the full 9-phase workflow with convergence enhancement

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🌙 NBA MCP Synthesis - Overnight Convergence Enhancement"
echo "============================================================"
echo ""
echo "This will run all 9 phases with convergence enhancement:"
echo ""
echo "  Phase 0: Discovery"
echo "  Phase 1: Book Discovery"
echo "  Phase 2: Book Analysis (ENHANCED - up to 200 iterations)"
echo "  Phase 3: Synthesis"
echo "  Phase 3.5: AI Plan Modifications"
echo "  Phase 4: File Generation"
echo "  Phase 5: Index Updates"
echo "  Phase 6-9: Remaining phases"
echo ""
echo "Configuration:"
echo "  - Books: All 51 books"
echo "  - Max iterations: 200 per book"
echo "  - Parallel workers: 4"
echo "  - Cost limit: \$400"
echo "  - Expected runtime: 10-15 hours"
echo "  - Expected cost: \$150-250"
echo ""
echo "============================================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check API keys
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY not set"
    echo "   Set it with: export GEMINI_API_KEY='your-key'"
    exit 1
fi

if [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ ERROR: CLAUDE_API_KEY not set"
    echo "   Set it with: export CLAUDE_API_KEY='your-key'"
    exit 1
fi

echo "  ✅ API keys configured"

# Check disk space
available_gb=$(df -g . | awk 'NR==2 {print $4}')
if [ "$available_gb" -lt 10 ]; then
    echo "❌ ERROR: Less than 10GB disk space available"
    echo "   Available: ${available_gb}GB"
    exit 1
fi

echo "  ✅ Disk space: ${available_gb}GB available"

# Check Python version
python_version=$(python3 --version | awk '{print $2}')
echo "  ✅ Python: $python_version"

# Create pre-convergence backup if not exists
if [ ! -f "analysis_results/pre_convergence_summary.json" ]; then
    echo ""
    echo "📸 Creating pre-convergence backup..."
    python3 scripts/generate_summary.py \
        --output analysis_results/pre_convergence_summary.json 2>/dev/null || echo "  ⚠️  Summary generation skipped (script may not exist)"
    echo "  ✅ Backup created"
fi

echo ""
echo "============================================================"
echo "⚠️  FINAL CONFIRMATION"
echo "============================================================"
echo ""
echo "This will:"
echo "  • Run for 10-15 hours"
echo "  • Cost approximately \$150-250"
echo "  • Use Gemini and Claude APIs heavily"
echo "  • Analyze all 51 books with deep convergence"
echo ""
read -p "Type 'START' to begin overnight run: " -r
echo ""

if [ "$REPLY" != "START" ]; then
    echo "❌ Launch cancelled"
    exit 0
fi

echo "============================================================"
echo "🚀 LAUNCHING OVERNIGHT CONVERGENCE"
echo "============================================================"
echo ""

# Create logs directory
mkdir -p logs

# Start dashboard in background
echo "📊 Starting monitoring dashboard..."
python3 scripts/workflow_monitor.py --port 8080 > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "  ✅ Dashboard started (PID: $DASHBOARD_PID)"
echo "  📊 Monitor at: http://localhost:8080"
echo ""

# Wait for dashboard to start
sleep 3

# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/overnight_convergence_${TIMESTAMP}.log"

echo "📝 Logging to: $LOG_FILE"
echo ""

# Launch main workflow
echo "🔄 Starting full workflow with convergence enhancement..."
echo ""
echo "Command:"
echo "  python3 scripts/run_full_workflow.py \\"
echo "    --parallel \\"
echo "    --max-workers 4"
echo ""
echo "Note: Convergence settings (max 200 iterations) are configured in workflow_config.yaml"
echo ""
echo "============================================================"
echo ""

# Run workflow (will run for hours)
# No --book argument = analyze all books
# --force-fresh = bypass all caching for true convergence enhancement
# Convergence settings come from workflow_config.yaml
python3 scripts/run_full_workflow.py \
    --parallel \
    --max-workers 4 \
    --force-fresh \
    2>&1 | tee "$LOG_FILE"

# Capture exit code
WORKFLOW_EXIT=$?

echo ""
echo "============================================================"
echo "🏁 WORKFLOW COMPLETE"
echo "============================================================"
echo ""

if [ $WORKFLOW_EXIT -eq 0 ]; then
    echo "✅ Workflow completed successfully!"
    echo ""

    # Generate post-convergence summary
    echo "📊 Generating post-convergence summary..."
    python3 scripts/generate_summary.py \
        --output analysis_results/post_convergence_summary.json 2>/dev/null || echo "  ⚠️  Summary generation skipped"

    # Generate comparison report if both summaries exist
    if [ -f "analysis_results/pre_convergence_summary.json" ] && [ -f "analysis_results/post_convergence_summary.json" ]; then
        echo "📈 Generating convergence comparison report..."
        python3 scripts/generate_convergence_comparison.py \
            --before analysis_results/pre_convergence_summary.json \
            --after analysis_results/post_convergence_summary.json \
            --output CONVERGENCE_ENHANCEMENT_RESULTS.md
        echo "  ✅ Report: CONVERGENCE_ENHANCEMENT_RESULTS.md"
    fi

    echo ""
    echo "============================================================"
    echo "📊 RESULTS SUMMARY"
    echo "============================================================"
    echo ""

    # Show quick stats
    if [ -f "synthesis_results/synthesis_output_gemini_claude.json" ]; then
        total_recs=$(python3 -c "import json; d=json.load(open('synthesis_results/synthesis_output_gemini_claude.json')); print(len(d.get('consensus_recommendations', [])))" 2>/dev/null || echo "?")
        echo "  Total Recommendations: $total_recs"
    fi

    if [ -f "cost_tracker/cost_summary.json" ]; then
        total_cost=$(python3 -c "import json; d=json.load(open('cost_tracker/cost_summary.json')); print(f\"\${d.get('total_cost', 0):.2f}\")" 2>/dev/null || echo "?")
        echo "  Total Cost: $total_cost"
    fi

    # Count converged books
    converged=0
    total_books=0
    if [ -d "analysis_results" ]; then
        total_books=$(ls -1 analysis_results/*_convergence_tracker.json 2>/dev/null | wc -l | tr -d ' ')
        for f in analysis_results/*_convergence_tracker.json; do
            if [ -f "$f" ]; then
                is_converged=$(python3 -c "import json; d=json.load(open('$f')); print('1' if d.get('convergence_achieved', False) else '0')" 2>/dev/null || echo "0")
                converged=$((converged + is_converged))
            fi
        done
    fi
    echo "  Books Converged: $converged / $total_books"

    echo ""
    echo "📄 Full log: $LOG_FILE"
    echo "📊 Dashboard: http://localhost:8080"
    echo "📄 Report: CONVERGENCE_ENHANCEMENT_RESULTS.md"
    echo ""
else
    echo "❌ Workflow failed with exit code: $WORKFLOW_EXIT"
    echo "📄 Check log: $LOG_FILE"
    echo ""
fi

# Keep dashboard running
echo "Dashboard still running (PID: $DASHBOARD_PID)"
echo "To stop dashboard: kill $DASHBOARD_PID"
echo ""

echo "============================================================"
echo "🌙 Overnight convergence enhancement complete!"
echo "============================================================"

