# Dual Workflow Quick Start Guide

## Overview

Two specialized workflows for continuous improvement:
- **Workflow A:** Improve MCP tools using AI/ML books
- **Workflow B:** Improve predictions using sports/stats books

Both share Phases 0-9, then diverge at Phase 10.

---

## Quick Decision: Which Workflow?

### Use Workflow A if:
- Reading: AI, ML, algorithms, programming books
- Goal: Better MCP tools
- Output: New tools, faster performance, better APIs

### Use Workflow B if:
- Reading: Sports analytics, econometrics, statistics books
- Goal: Better predictions
- Output: Higher accuracy, better models, lower RMSE

### Use Both if:
- Reading: Mixed book library
- Goal: Improve everything
- Output: Better tools AND better predictions

---

## Quick Start Commands

### Workflow A (MCP Improvement)
```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Analyze AI/ML books for MCP improvements
python3 scripts/recursive_book_analysis.py \
    --category "machine_learning,ai,programming" \
    --workflow A \
    --output analysis_results/workflow_a/

# Monitor progress
tail -f analysis_results/workflow_a/progress.log
```

### Workflow B (Simulator Improvement)
```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Analyze sports/stats books for prediction improvements
python3 scripts/recursive_book_analysis.py \
    --category "sports_analytics,econometrics,statistics" \
    --workflow B \
    --output analysis_results/workflow_b/

# Monitor progress
tail -f analysis_results/workflow_b/progress.log
```

### Both Workflows (Parallel)
```bash
# Run Workflow A in background
python3 scripts/recursive_book_analysis.py \
    --category "machine_learning,ai" \
    --workflow A \
    > workflow_a.log 2>&1 &

# Run Workflow B in foreground
python3 scripts/recursive_book_analysis.py \
    --category "sports_analytics,econometrics" \
    --workflow B
```

---

## Phase Overview

### Shared Foundation (Phases 0-9)
Both workflows execute these phases identically:

| Phase | Name | Duration | Output |
|-------|------|----------|--------|
| 0 | Project Discovery | 30-60 min | Project understanding |
| 1 | Book Discovery | 5 min | Book inventory |
| 2 | Recursive Analysis | 15-40 hrs | Recommendations |
| 3 | Phase Integration | 30 min | Organized recommendations |
| 4 | Implementation Files | 2-4 hrs | Code files |
| 5 | Phase Index Updates | 30 min | Documentation |
| 6 | Cross-Project Status | 15 min | Status reports |
| 7 | Sequence Optimization | 1 hr | Optimal order |
| 8 | Progress Tracking | 30 min | Dashboard setup |
| 9 | Overnight Execution | 8-12 hrs | Automated implementation |

**Total Shared: 27-59 hours**

---

### Workflow A Divergence (Phases 10A-12A)

| Phase | Name | Duration | Output |
|-------|------|----------|--------|
| 10A | MCP Tool Validation | 2-4 hrs | Validation reports |
| 11A | Tool Optimization | 4-8 hrs | Optimized tools |
| 12A | MCP Production Deploy | 2 hrs | Live deployment |

**Total Workflow A: 8-14 hours**

---

### Workflow B Divergence (Phases 10B-12B)

| Phase | Name | Duration | Output |
|-------|------|----------|--------|
| 10B | Model Validation | 4-8 hrs | Accuracy reports |
| 11B | Model Ensemble | 8-16 hrs | Optimized ensemble |
| 12B | Simulator Deploy | 2 hrs | Live deployment |

**Total Workflow B: 14-26 hours**

---

## Book Categorization

### Workflow A Books (MCP Improvement)

**Machine Learning:**
- Machine Learning for Absolute Beginners
- Hands-On Machine Learning with Scikit-Learn
- Pattern Recognition and Machine Learning
- Applied Machine Learning and AI for Engineers
- Designing Machine Learning Systems
- Machine Learning: A Probabilistic Perspective

**AI Engineering:**
- AI Engineering
- Generative AI in Action
- Hands-On Large Language Models
- LLM Engineers Handbook
- NLP with Transformer Models

**Programming & Performance:**
- Python performance guides
- Algorithm optimization books
- Data structure references

---

### Workflow B Books (Simulator Improvement)

**Sports Analytics:**
- Basketball on Paper
- Basketball Beyond Paper
- Sports Analytics
- The Midrange Theory

**Econometrics:**
- Mostly Harmless Econometrics
- Econometrics: A Modern Approach
- Introductory Econometrics (Wooldridge)
- Introduction to Econometrics (Stock & Watson)
- Cross-section and Panel Data (Wooldridge)
- Econometric Analysis (Greene)
- Microeconometrics: Methods and Applications

**Statistics:**
- Applied Predictive Modeling
- The Elements of Statistical Learning
- STATISTICS 601 Advanced Statistical Methods

**Special:**
- BeyondMLR_complete.txt (Chapter 8: Multi-level models)

---

## Success Metrics

### Workflow A Success
- ✅ 10+ new MCP tools deployed
- ✅ Tool performance improved by 30-50%
- ✅ Developer productivity increased by 30%
- ✅ Tool usage increased by 50%

### Workflow B Success
- ✅ Prediction accuracy improved by 15-20%
- ✅ Box score RMSE < 7.0 points
- ✅ Player stats MAE < 3.5 points
- ✅ Win/loss accuracy > 65%

---

## Typical Execution Timeline

### Weekend (48 hours)
**Friday Evening (6 PM - 10 PM):**
- Start Phase 0-1 (Project Discovery, Book Discovery)
- Begin Phase 2 (Book Analysis)

**Saturday (All Day):**
- Phase 2 continues (Book Analysis - largest phase)
- Multiple books analyzed section-by-section

**Sunday Morning:**
- Phase 2 completes
- Phases 3-6 execute (Integration, Files, Updates, Status)

**Sunday Afternoon:**
- Phases 7-9 execute (Optimization, Tracking, Implementation)

**Sunday Evening:**
- Phase 10A/B begins (Validation)
- Phase 11A/B if time permits (Optimization)

**Monday Morning:**
- Review overnight execution results
- Complete Phase 11A/B and 12A/B (if not done)
- Deploy to production

---

## Monitoring Progress

### Real-Time Monitoring
```bash
# Watch analysis progress
tail -f /tmp/book_analysis.log

# Check current phase
grep "Phase" /tmp/book_analysis.log | tail -5

# Monitor costs
grep "💰" /tmp/book_analysis.log | tail -10

# Check convergence
grep "Iteration" /tmp/book_analysis.log | tail -20
```

### Key Progress Indicators
```
🔄 Iteration X/15 - Still analyzing
✅ Tracker saved - Section complete
📊 UPLOAD SUMMARY - Phase complete
💰 Analysis cost - Track spending
🎯 Consensus: majority - Models agreeing
```

---

## Common Issues & Solutions

### Issue 1: Analysis Too Slow
**Symptom:** > 60 min per book
**Solution:**
```bash
# Use parallel processing
python3 scripts/recursive_book_analysis.py \
    --parallel 3 \
    --workflow A
```

### Issue 2: Quota Exceeded
**Symptom:** `Quota exceeded` errors
**Solution:**
- Google Gemini: Wait 60 seconds, auto-recovers
- Claude/GPT-4: Check API quotas
- Switch to lower-cost model temporarily

### Issue 3: Out of Memory
**Symptom:** Memory errors during large book processing
**Solution:**
```bash
# Process in smaller chunks
python3 scripts/recursive_book_analysis.py \
    --chunk-size 50000 \
    --workflow B
```

---

## Advanced Usage

### Selective Book Analysis
```bash
# Analyze specific books only
python3 scripts/recursive_book_analysis.py \
    --books "Basketball on Paper,Econometrics" \
    --workflow B

# Analyze by category
python3 scripts/recursive_book_analysis.py \
    --category "sports_analytics" \
    --workflow B
```

### Resume After Interruption
```bash
# System saves progress automatically
# Just re-run the same command
python3 scripts/recursive_book_analysis.py \
    --workflow B \
    --resume
```

### Dry Run (No Changes)
```bash
# Test workflow without making changes
python3 scripts/recursive_book_analysis.py \
    --workflow A \
    --dry-run
```

---

## Next Steps After Completion

### After Workflow A
1. Test new MCP tools
2. Update tool documentation
3. Announce new tools to users
4. Monitor tool usage
5. Collect feedback
6. Plan next book batch

### After Workflow B
1. Validate prediction improvements
2. Monitor production accuracy
3. Compare vs. previous baseline
4. Identify remaining error sources
5. Plan next model enhancements
6. Schedule retraining

---

## Complete Documentation

**For full details, see:**
- `complete_recursive_book_analysis_command.md` - Complete technical specification
- `WORKFLOW_A_MCP_IMPROVEMENT.md` - Full Workflow A documentation
- `WORKFLOW_B_SIMULATOR_IMPROVEMENT.md` - Full Workflow B documentation

**For implementation details, see:**
- `scripts/recursive_book_analysis.py` - Main analysis script
- `scripts/resilient_book_analyzer.py` - Multi-model AI analysis
- `config/books_to_analyze.json` - Book configuration

---

## Questions?

### Which workflow should I use?
- **Improving tools?** → Workflow A
- **Improving predictions?** → Workflow B
- **Both?** → Run both in parallel

### Can I switch workflows mid-analysis?
- No - complete Phases 0-9, then commit to A or B
- Or run both workflows separately on different book sets

### How often should I run each workflow?
- **Workflow A:** Monthly (new AI/ML techniques emerge frequently)
- **Workflow B:** Quarterly (sports analytics evolves slower, but model drift requires updates)
- **Both:** Whenever you acquire significant new books

### What's the ROI?
- **Workflow A:** 30% developer productivity increase
- **Workflow B:** 15-20% prediction accuracy improvement
- **Cost:** ~$50-100 in API costs per full workflow run
- **Time:** 2-3 days of automated execution

---

**Ready to start? Pick your workflow and run the command! 🚀**

