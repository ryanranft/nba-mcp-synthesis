#!/bin/bash
# Check progress of overnight convergence enhancement
# Use this to monitor without interrupting the process

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

clear
echo "============================================================"
echo "📊 Convergence Enhancement - Progress Check"
echo "============================================================"
echo ""
echo "Current Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if workflow is running
if pgrep -f "run_full_workflow.py" > /dev/null; then
    echo "Status: 🔄 RUNNING"
else
    echo "Status: ⏸️  NOT RUNNING (completed or not started)"
fi

echo ""
echo "============================================================"
echo "📚 Books Progress"
echo "============================================================"
echo ""

# Count converged books
if [ -d "analysis_results" ]; then
    total_books=$(ls -1 analysis_results/*_convergence_tracker.json 2>/dev/null | wc -l | tr -d ' ')
    converged_books=0
    not_converged_books=0

    if [ "$total_books" -gt 0 ]; then
        for tracker in analysis_results/*_convergence_tracker.json; do
            if [ -f "$tracker" ]; then
                is_converged=$(python3 -c "import json; d=json.load(open('$tracker')); print('1' if d.get('convergence_achieved', False) else '0')" 2>/dev/null || echo "0")
                if [ "$is_converged" = "1" ]; then
                    converged_books=$((converged_books + 1))
                else
                    not_converged_books=$((not_converged_books + 1))
                fi
            fi
        done

        percent=$((converged_books * 100 / total_books))
        echo "  Total Books: $total_books"
        echo "  ✅ Converged: $converged_books ($percent%)"
        echo "  ⏳ Not Converged: $not_converged_books"
    else
        echo "  No convergence trackers found yet"
    fi
else
    echo "  Analysis results directory not found"
fi

echo ""
echo "============================================================"
echo "💰 Cost Tracking"
echo "============================================================"
echo ""

if [ -f "cost_tracker/cost_summary.json" ]; then
    python3 << 'PYTHON_SCRIPT'
import json
try:
    with open('cost_tracker/cost_summary.json') as f:
        cost_data = json.load(f)

    total = cost_data.get('total_cost', 0)
    budget = cost_data.get('budget', 400)
    percent = (total / budget * 100) if budget > 0 else 0
    remaining = budget - total

    print(f"  Total Cost: ${total:.2f}")
    print(f"  Budget: ${budget:.2f}")
    print(f"  Remaining: ${remaining:.2f}")
    print(f"  Used: {percent:.1f}%")

    if percent > 95:
        print("  ⚠️  WARNING: Near budget limit!")
    elif percent > 80:
        print("  ⚠️  Approaching budget limit")
    else:
        print("  ✅ Within budget")

except Exception as e:
    print(f"  Unable to read cost data: {e}")
PYTHON_SCRIPT
else
    echo "  Cost tracking data not available yet"
fi

echo ""
echo "============================================================"
echo "📝 Recommendations"
echo "============================================================"
echo ""

if [ -f "synthesis_results/synthesis_output_gemini_claude.json" ]; then
    total_recs=$(python3 -c "import json; d=json.load(open('synthesis_results/synthesis_output_gemini_claude.json')); print(len(d.get('consensus_recommendations', [])))" 2>/dev/null || echo "?")

    if [ "$total_recs" != "?" ]; then
        echo "  Total Recommendations: $total_recs"

        # Count by priority
        python3 << 'PYTHON_SCRIPT'
import json
try:
    with open('synthesis_results/synthesis_output_gemini_claude.json') as f:
        data = json.load(f)

    recs = data.get('consensus_recommendations', [])
    critical = sum(1 for r in recs if r.get('priority') == 'critical')
    important = sum(1 for r in recs if r.get('priority') == 'important')
    nice = sum(1 for r in recs if r.get('priority') == 'nice-to-have')

    print(f"    • Critical: {critical}")
    print(f"    • Important: {important}")
    print(f"    • Nice-to-have: {nice}")
except:
    pass
PYTHON_SCRIPT
    fi
else
    echo "  Synthesis not completed yet"
fi

echo ""
echo "============================================================"
echo "🖥️  System Health"
echo "============================================================"
echo ""

# Check disk space
available_gb=$(df -g . | awk 'NR==2 {print $4}')
echo "  Disk Space: ${available_gb}GB available"
if [ "$available_gb" -lt 5 ]; then
    echo "  ⚠️  WARNING: Low disk space!"
fi

# Check memory
if command -v free >/dev/null 2>&1; then
    free -h | grep "Mem:" | awk '{print "  Memory: " $3 " used / " $2 " total"}'
elif command -v vm_stat >/dev/null 2>&1; then
    echo "  Memory: (use Activity Monitor for details)"
fi

# Check if dashboard is running
if pgrep -f "workflow_monitor.py" > /dev/null; then
    echo "  Dashboard: 🟢 Running at http://localhost:8080"
else
    echo "  Dashboard: ⚪ Not running"
fi

echo ""
echo "============================================================"
echo "📊 Recent Activity"
echo "============================================================"
echo ""

# Show last 10 lines of latest log
latest_log=$(ls -t logs/overnight_convergence_*.log 2>/dev/null | head -1)
if [ -n "$latest_log" ] && [ -f "$latest_log" ]; then
    echo "Last 10 lines from: $latest_log"
    echo ""
    tail -10 "$latest_log" | sed 's/^/  /'
else
    echo "  No log file found yet"
fi

echo ""
echo "============================================================"
echo "📌 Quick Actions"
echo "============================================================"
echo ""
echo "  • View full log: tail -f logs/overnight_convergence_*.log"
echo "  • Monitor dashboard: open http://localhost:8080"
echo "  • Check system: python3 scripts/resource_monitor.py"
echo "  • Stop workflow: pkill -f run_full_workflow.py"
echo ""
echo "This check completed at: $(date '+%H:%M:%S')"
echo "============================================================"
echo ""







