#!/bin/bash
# Run Convergence Enhancement on All 51 Books
# This script runs the full workflow with enhanced convergence settings

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "🚀 NBA MCP Synthesis - Convergence Enhancement"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  - Max iterations: 200"
echo "  - Books: All 51 books"
echo "  - Parallel: Yes (4 workers)"
echo "  - Cost limit: \$400"
echo "  - Expected runtime: 10-15 hours"
echo ""
echo "============================================================"
echo ""

# Check if pre-convergence backup exists
if [ ! -f "$PROJECT_ROOT/analysis_results/pre_convergence_summary.json" ]; then
    echo "📸 Creating pre-convergence backup..."
    python3 "$SCRIPT_DIR/generate_summary.py" \
        --output "$PROJECT_ROOT/analysis_results/pre_convergence_summary.json"
    echo "✅ Pre-convergence backup created"
    echo ""
fi

# Confirm with user
read -p "⚠️  This will run for 10-15 hours and cost ~\$150-250. Continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Convergence enhancement cancelled"
    exit 1
fi

echo "🚀 Starting convergence enhancement..."
echo ""

# Run convergence enhancement
python3 "$PROJECT_ROOT/scripts/run_full_workflow.py" \
    --book "All Books" \
    --parallel \
    --max-workers 4 \
    --converge-until-done \
    --max-iterations 200 \
    --config "$PROJECT_ROOT/config/workflow_config.yaml"

echo ""
echo "============================================================"
echo "✅ Convergence Enhancement Complete"
echo "============================================================"
echo ""

# Generate post-convergence summary
echo "📊 Generating post-convergence summary..."
python3 "$SCRIPT_DIR/generate_summary.py" \
    --output "$PROJECT_ROOT/analysis_results/post_convergence_summary.json"
echo "✅ Post-convergence summary created"
echo ""

# Generate comparison report
echo "📈 Generating convergence comparison report..."
python3 "$SCRIPT_DIR/generate_convergence_comparison.py" \
    --before "$PROJECT_ROOT/analysis_results/pre_convergence_summary.json" \
    --after "$PROJECT_ROOT/analysis_results/post_convergence_summary.json" \
    --output "$PROJECT_ROOT/CONVERGENCE_ENHANCEMENT_RESULTS.md"
echo "✅ Comparison report generated"
echo ""

echo "============================================================"
echo "📄 Results:"
echo "  - Summary: analysis_results/post_convergence_summary.json"
echo "  - Report: CONVERGENCE_ENHANCEMENT_RESULTS.md"
echo "============================================================"





