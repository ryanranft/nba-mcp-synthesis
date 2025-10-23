# Overnight Convergence Enhancement - Quick Start Guide

## Overview

This guide helps you launch the overnight convergence enhancement run that will:
- Re-analyze all 51 books with deep convergence (up to 200 iterations)
- Run through all 9 workflow phases
- Extract 300-400 total recommendations (up from current 218)
- Cost approximately $150-250
- Take 10-15 hours to complete

## Prerequisites

### 1. Verify API Keys
```bash
echo $GEMINI_API_KEY  # Should show your key
echo $CLAUDE_API_KEY  # Should show your key
```

If not set:
```bash
export GEMINI_API_KEY="your-gemini-key"
export CLAUDE_API_KEY="your-claude-key"
```

### 2. Check System Resources
```bash
# Check disk space (need 10GB+ free)
df -h .

# Check if ports available
lsof -i :8080  # Should be empty
```

### 3. Verify Current State
```bash
# Current recommendation count
python3 -c "import json; d=json.load(open('synthesis_results/synthesis_output_gemini_claude.json')); print(f'Current: {len(d[\"consensus_recommendations\"])} recommendations')"

# Expected output: Current: 218 recommendations
```

---

## Launch Methods

### Method 1: Interactive Launch (Recommended)

```bash
./launch_overnight_convergence.sh
```

This will:
1. Check all prerequisites
2. Create pre-convergence backup
3. Ask for confirmation (type `START`)
4. Launch dashboard at http://localhost:8080
5. Run full workflow with convergence enhancement
6. Generate comparison report when complete

**Confirmation prompt:**
```
Type 'START' to begin overnight run: START
```

---

### Method 2: Background Launch (Advanced)

```bash
# Launch in background with nohup
nohup ./launch_overnight_convergence.sh > overnight_launch.log 2>&1 &

# Get process ID
echo $! > overnight_pid.txt

# The script will prompt for 'START' - you'll need to interact with it initially
```

---

### Method 3: Screen Session (Server)

```bash
# Start screen session
screen -S convergence

# Launch script
./launch_overnight_convergence.sh

# Type START when prompted

# Detach: Ctrl+A, then D
# Reattach later: screen -r convergence
```

---

## Monitoring Progress

### Real-Time Dashboard
```bash
# Open in browser
open http://localhost:8080

# Or visit manually:
# http://localhost:8080
```

Dashboard shows:
- Phase progress
- Books processed
- Cost tracking
- System health
- Recent alerts

### Command-Line Monitoring
```bash
# Run progress checker (safe, non-invasive)
./check_progress.sh

# Or watch it continuously
watch -n 30 ./check_progress.sh
```

### Log Tailing
```bash
# View real-time logs
tail -f logs/overnight_convergence_*.log

# Last 50 lines
tail -50 logs/overnight_convergence_*.log
```

### System Resources
```bash
# Check resource monitor
python3 scripts/resource_monitor.py

# Continuous monitoring
python3 scripts/resource_monitor.py --watch --interval 10
```

---

## What Happens During the Run

### Timeline (10-15 hours total)

**Hour 0-1: Startup**
- Dashboard starts
- Configuration loaded
- Workers initialized
- Cache loaded (fast!)

**Hours 1-12: Book Analysis (Phase 2)**
- First 12 iterations: Use cache (very fast)
- Iterations 13-200: Fresh analysis (slower)
- Books converge at different rates
- Most time spent here

**Hours 12-13: Synthesis (Phase 3)**
- Deduplicate recommendations
- Merge with existing 218
- Quality scoring
- Consensus generation

**Hour 13: AI Modifications (Phase 3.5)**
- Gap detection
- Duplicate removal
- Plan optimization

**Hours 13-14: File Generation (Phase 4)**
- Generate implementation files
- Add version headers
- Create tests

**Hour 14-15: Finalization (Phases 5-9)**
- Update indexes
- Generate reports
- Create dependency graphs
- Status updates

---

## Expected Results

### Recommendations
- **Before:** 218 unique recommendations
- **Target:** 300-400 unique recommendations
- **Gain:** 80-180 additional recommendations (+40-85%)

### By Priority
- **Critical:** ~100-120 (up from 65)
- **Important:** ~120-150 (up from 88)
- **Nice-to-have:** ~80-130 (up from 65)

### Cost
- **Target:** $150-250
- **Budget:** $400 (safety limit)
- **Per book:** ~$3-5

### Convergence
- **Before:** 0/51 books converged
- **Target:** 51/51 books converged
- **Iterations:** Varies by book (15-200)

---

## Safety Features

### Cost Limits
- Hard limit: $400 total
- Alert at $320 (80%)
- Workflow pauses if exceeded

### API Rate Limits
- Resource monitor tracks quotas
- Automatic throttling
- Prevents rate limit errors

### Checkpoints
- Saves every 10 books
- Resume if interrupted
- No data loss

### Disk Space
- Monitors available space
- Alerts if < 10GB
- Prevents disk full errors

---

## Troubleshooting

### Phase Execution Behavior

The workflow automatically **skips manual phases 5-8** during autonomous runs:

- **Phase 5: Dry-Run Validation** - Skipped (manual review phase)
- **Phase 6: Conflict Resolution** - Skipped (manual intervention phase)
- **Phase 7: Manual Review** - Skipped (human review phase)
- **Phase 8: Implementation** - Skipped (manual deployment phase)

These phases are designed for human oversight and don't apply to autonomous overnight convergence runs. The workflow proceeds directly from Phase 4 to Phase 8.5.

**This is expected behavior** - you'll see log messages like:
```
⏭️ Skipped phase_5: Dry-run validation - manual phase, skipped in autonomous mode
```

### Problem: Script Won't Start

**Check API keys:**
```bash
echo $GEMINI_API_KEY
echo $CLAUDE_API_KEY
```

**Check disk space:**
```bash
df -h .
```

**Check port availability:**
```bash
lsof -i :8080
```

---

### Problem: High Costs

**Check current cost:**
```bash
python3 -c "import json; d=json.load(open('cost_tracker/cost_summary.json')); print(f\"\${d['total_cost']:.2f}\")"
```

**Stop if needed:**
```bash
# Gracefully stop (saves checkpoint)
pkill -SIGTERM -f run_full_workflow.py

# Or force stop
pkill -9 -f run_full_workflow.py
```

---

### Problem: Slow Progress

**Check system resources:**
```bash
python3 scripts/resource_monitor.py
```

**Check for bottlenecks:**
```bash
# CPU usage
top

# Network connectivity
ping google.com

# API response times (in logs)
grep "API response time" logs/overnight_convergence_*.log
```

---

### Problem: Process Dies

**Check if still running:**
```bash
pgrep -f run_full_workflow.py
```

**Resume from checkpoint:**
```bash
python3 scripts/run_full_workflow.py \
    --book "All Books" \
    --parallel \
    --max-workers 4 \
    --resume-from-checkpoint \
    --converge-until-done
```

---

## Stopping the Run

### Graceful Stop (Saves Progress)
```bash
# Send TERM signal (saves checkpoint)
pkill -SIGTERM -f run_full_workflow.py

# Wait for graceful shutdown (may take 1-2 minutes)
```

### Force Stop
```bash
# Force kill (may lose progress since last checkpoint)
pkill -9 -f run_full_workflow.py
```

### Stop Dashboard
```bash
# Find dashboard PID
pgrep -f workflow_monitor.py

# Stop it
pkill -f workflow_monitor.py
```

---

## After Completion

### 1. Review Results

```bash
# Read comparison report
cat CONVERGENCE_ENHANCEMENT_RESULTS.md

# Check recommendation count
python3 -c "import json; d=json.load(open('synthesis_results/synthesis_output_gemini_claude.json')); print(f'Total: {len(d[\"consensus_recommendations\"])} recommendations')"
```

### 2. Verify Quality

```bash
# Check by priority
python3 << 'EOF'
import json
data = json.load(open('synthesis_results/synthesis_output_gemini_claude.json'))
recs = data['consensus_recommendations']
critical = sum(1 for r in recs if r.get('priority') == 'critical')
important = sum(1 for r in recs if r.get('priority') == 'important')
nice = sum(1 for r in recs if r.get('priority') == 'nice-to-have')
print(f"Critical: {critical}")
print(f"Important: {important}")
print(f"Nice-to-have: {nice}")
EOF
```

### 3. Regenerate Files

```bash
# Update implementation files with new recommendations
python3 scripts/phase4_file_generation.py

# Update indexes
python3 scripts/update_indexes.py

# Generate dependency graph
python3 scripts/generate_dependency_graph.py
```

### 4. Archive Results

```bash
# Create timestamped archive
timestamp=$(date +%Y%m%d_%H%M%S)
tar -czf convergence_results_$timestamp.tar.gz \
    analysis_results/ \
    synthesis_results/ \
    CONVERGENCE_ENHANCEMENT_RESULTS.md
```

---

## Next Steps

After convergence enhancement completes, you can:

### Option 1: Implement Recommendations
```bash
cd /Users/ryanranft/nba-simulator-aws
# Follow BACKGROUND_AGENT_INSTRUCTIONS.md
# Start with Tier 1 from PRIORITY_ACTION_LIST.md
```

### Option 2: Run A/B Tests
```bash
python3 scripts/ab_testing_framework.py \
    --test gemini-vs-claude \
    --books 5
```

### Option 3: Continuous Monitoring
```bash
# Keep dashboard running
python3 scripts/workflow_monitor.py

# Setup cron for periodic analysis
# Add to crontab: 0 0 * * 0 cd /Users/ryanranft/nba-mcp-synthesis && ./launch_overnight_convergence.sh
```

---

## FAQ

**Q: Can I pause and resume?**
A: Yes, use `pkill -SIGTERM` to stop gracefully, then resume with `--resume-from-checkpoint`

**Q: What if I run out of budget?**
A: Workflow will automatically pause. Increase limits in `config/workflow_config.yaml` or stop.

**Q: How do I know it's working?**
A: Check dashboard at http://localhost:8080 or run `./check_progress.sh`

**Q: Can I run this multiple times?**
A: Yes, but diminishing returns. Each run extracts fewer new insights.

**Q: What if my internet drops?**
A: Workflow will retry failed API calls automatically. If offline too long, it will checkpoint and exit.

**Q: How long does each book take?**
A: Varies widely. First 12 iterations use cache (seconds). New iterations take 5-10 minutes each.

---

## Quick Reference

```bash
# Launch
./launch_overnight_convergence.sh

# Monitor
./check_progress.sh
open http://localhost:8080

# Logs
tail -f logs/overnight_convergence_*.log

# Stop
pkill -SIGTERM -f run_full_workflow.py

# Resume
python3 scripts/run_full_workflow.py --resume-from-checkpoint
```

---

**Ready to Launch?**

```bash
./launch_overnight_convergence.sh
# Type START when prompted
```

**Expected Result:** 300-400 recommendations, all 51 books converged, $150-250 cost, 10-15 hours

Good luck! 🌙

