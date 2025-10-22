# Quick Reference: Autonomous Overnight Run

## Pre-Launch (Do Once)

### 1. Set API Keys (REQUIRED)
```bash
export GEMINI_API_KEY="your-key-here"
export CLAUDE_API_KEY="your-key-here"
```

### 2. Clear Port 8080 (if in use)
```bash
kill 15409  # Or check with: lsof -i :8080
```

### 3. Verify Ready
```bash
python3 scripts/pre_flight_check.py
# Should show: ✅ ALL CHECKS PASSED
```

---

## Launch (Single Command)

```bash
./launch_overnight_convergence.sh
# Type "START" when prompted
```

**Expected Runtime:** 10-15 hours
**Expected Cost:** $150-250

---

## Monitor (While Running)

### Option 1: Dashboard
```bash
open http://localhost:8080
```

### Option 2: Quick Status
```bash
./check_progress.sh
```

### Option 3: Live Logs
```bash
tail -f logs/overnight_convergence_*.log
```

---

## Stop (Emergency Only)

```bash
# Graceful stop (saves checkpoint)
pkill -SIGTERM -f run_full_workflow.py

# Resume later
python3 scripts/run_full_workflow.py --resume-from-checkpoint --converge-until-done
```

---

## Results (After Completion)

Files created:
- `CONVERGENCE_ENHANCEMENT_RESULTS.md` - Full comparison report
- `analysis_results/post_convergence_summary.json` - Final state
- Updated synthesis results with 300-400 recommendations

---

## Expected Outcome

**Before:**
- 0/51 books converged
- 0 recommendations tracked

**After:**
- 51/51 books converged ✅
- 300-400 recommendations extracted
- Ready for implementation in nba-simulator-aws

**ROI:** ~31,000-64,000% (estimated $78K-96K value from recommendations)

---

## Troubleshooting

**"API Keys not set"**
```bash
# Add to ~/.zshrc permanently
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc
echo 'export CLAUDE_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

**"Port 8080 in use"**
```bash
# Find and kill process
lsof -i :8080
kill [PID]
```

**"Out of disk space"**
```bash
# Check space
df -h .
# Clean old caches if needed
rm -rf .cache/old_*
```

---

## Contact & Support

- **Pre-flight check:** `python3 scripts/pre_flight_check.py`
- **Full guide:** `OVERNIGHT_CONVERGENCE_GUIDE.md`
- **Ready checklist:** `READY_TO_LAUNCH.md`
- **System architecture:** `SYSTEM_ARCHITECTURE_v3.md`

---

Last updated: October 19, 2025





