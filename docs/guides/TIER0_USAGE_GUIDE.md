# Tier 0 Usage Guide

## Quick Start

```bash
# Test the complete workflow with 1 book
python scripts/run_full_workflow.py --book "Machine Learning Systems"

# Preview without executing (dry-run)
python scripts/run_full_workflow.py --book "Machine Learning Systems" --dry-run

# Skip validation for faster testing
python scripts/run_full_workflow.py --book "Machine Learning Systems" --skip-validation
```

---

## What's Included in Tier 0

### ✅ Core Features
- **Phase 2**: Recursive book analysis with high-context models (Gemini + Claude)
- **Phase 3**: Basic recommendation consolidation
- **Phase 4**: Implementation file generation
- **Phase 8.5**: Pre-integration validation
- **Safety Systems**: Cost limits, rollback, error recovery

### 📊 Safety Features
- **Cost Tracking**: Automatic budget enforcement ($75 total limit)
- **Rollback Manager**: Automatic backups before each phase
- **Error Recovery**: Retry logic with exponential backoff
- **Validation**: Syntax checks, test discovery, SQL validation

### 🎯 Workflow Phases

#### Phase 2: Book Analysis
- Uses high-context analyzer (up to 250k tokens per book)
- Gemini 2.0 Flash (primary) + Claude Sonest 4 (backup)
- Cost: ~$5 per book
- Time: 60-120 seconds per book
- Output: `analysis_results/{book}_convergence_tracker.json`

#### Phase 3: Consolidation
- Consolidates recommendations from analysis
- Removes duplicates
- Calculates confidence scores
- Output: `implementation_plans/consolidated_recommendations.json`

#### Phase 4: File Generation
- Generates implementation files:
  - `README.md` - Usage guide
  - `STATUS.md` - Implementation status
  - `RECOMMENDATIONS_FROM_BOOKS.md` - Source references
  - `implement_*.py` - Python implementation
  - `test_*.py` - Test suite
  - `*.sql` - Database migrations (if needed)
- Output: `implementation_plans/phase_X/rec_Y_*/`

#### Phase 8.5: Validation
- Python syntax checks
- Test discovery (pytest --collect-only)
- Import conflict detection
- SQL migration validation
- Output: `VALIDATION_REPORT.md`

---

## Usage Examples

### Basic Workflow

```bash
# 1. Analyze a book
python scripts/run_full_workflow.py --book "Designing Machine Learning Systems"

# 2. Check generated files
ls -la implementation_plans/

# 3. Review validation report
cat VALIDATION_REPORT.md

# 4. Check cost tracking
cat cost_tracker/cost_report_*.json
```

### Dry-Run Mode

```bash
# Preview what would happen without executing
python scripts/run_full_workflow.py --book "Machine Learning Systems" --dry-run

# Output shows:
# - Which book would be analyzed
# - Estimated costs
# - What files would be generated
# - No actual changes made
```

### Individual Phase Execution

```bash
# Run only Phase 2 (book analysis)
python scripts/recursive_book_analysis.py \
  --book "Machine Learning Systems" \
  --high-context

# Run only Phase 3 (consolidation)
python scripts/phase3_consolidation_and_synthesis.py

# Run only Phase 4 (file generation)
python scripts/phase4_file_generation.py

# Run only Phase 8.5 (validation)
python scripts/phase8_5_validation.py
```

### Safety Features

#### Cost Limits
```python
# Automatic cost enforcement
# Phase 2: $30 limit
# Phase 3: $20 limit
# Total: $75 limit

# Check current spending
python -c "from scripts.cost_safety_manager import CostSafetyManager; \
  mgr = CostSafetyManager(); \
  print(f'Spent: ${mgr.get_total_cost():.2f}'); \
  print(f'Remaining: ${mgr.get_remaining_budget():.2f}')"
```

#### Rollback
```python
# Manual rollback to previous state
python -c "from scripts.rollback_manager import RollbackManager; \
  from pathlib import Path; \
  mgr = RollbackManager(); \
  backups = mgr.list_backups(); \
  print('Available backups:'); \
  for b in backups[:5]: print(f'  {b}')"

# Restore a backup
# mgr.restore_backup('backup_id', target_path)
```

#### Error Recovery
```python
# Automatic retry with exponential backoff
# - API timeouts: 3 retries, 2s backoff
# - Rate limits: 5 retries, 60s backoff
# - Network errors: 3 retries, 5s backoff
# Built into all API calls
```

---

## Directory Structure

```
nba-mcp-synthesis/
├── scripts/
│   ├── run_full_workflow.py           # ← Master orchestrator
│   ├── recursive_book_analysis.py      # Phase 2
│   ├── phase3_consolidation_and_synthesis.py  # Phase 3
│   ├── phase4_file_generation.py       # Phase 4
│   ├── phase8_5_validation.py          # Phase 8.5
│   ├── cost_safety_manager.py          # Safety
│   ├── rollback_manager.py             # Safety
│   └── error_recovery.py               # Safety
│
├── implementation_plans/               # Generated files
│   ├── consolidated_recommendations.json
│   ├── PHASE3_SUMMARY.md
│   ├── PHASE4_SUMMARY.json
│   └── phase_X/
│       └── rec_Y_title/
│           ├── README.md
│           ├── STATUS.md
│           ├── RECOMMENDATIONS_FROM_BOOKS.md
│           ├── implement_rec_Y.py
│           ├── test_rec_Y.py
│           └── rec_Y.sql (optional)
│
├── backups/                           # Automatic backups
│   └── phase_X_YYYYMMDD_HHMMSS/
│
├── cost_tracker/                      # Cost tracking
│   └── cost_report_YYYYMMDD_HHMMSS.json
│
└── VALIDATION_REPORT.md              # Validation results
```

---

## Troubleshooting

### "Cost limit exceeded"
```bash
# Check current spending
python -c "from scripts.cost_safety_manager import CostSafetyManager; \
  mgr = CostSafetyManager(); \
  report = mgr.get_cost_report(); \
  for phase, cost in report['by_phase'].items(): \
    print(f'{phase}: ${cost:.2f}')"

# If needed, manually reset (use with caution)
# rm -rf cost_tracker/
```

### "Phase X failed"
```bash
# Check logs for specific error
tail -n 50 /tmp/workflow_*.log

# Rollback to previous state
python -c "from scripts.rollback_manager import RollbackManager; \
  mgr = RollbackManager(); \
  latest = mgr.list_backups()[0]; \
  print(f'Latest backup: {latest}')"
```

### "Validation failed"
```bash
# Check validation report
cat VALIDATION_REPORT.md

# Run validation manually with details
python scripts/phase8_5_validation.py --verbose

# Skip validation if needed
python scripts/run_full_workflow.py \
  --book "Machine Learning Systems" \
  --skip-validation
```

### "Book not found"
```bash
# List available books
python scripts/recursive_book_analysis.py --dry-run

# Use partial match
python scripts/run_full_workflow.py --book "Machine"
# Matches: "Designing Machine Learning Systems"
```

---

## Next Steps After Tier 0

Once Tier 0 is working:

1. **Review generated files** in `implementation_plans/`
2. **Check validation report** - Fix any issues
3. **Verify cost tracking** - Ensure under budget
4. **Test rollback** - Verify backups work
5. **Ready for Tier 1**:
   - Parallel execution
   - Caching
   - Progress checkpoints
   - Full multi-book support

---

## Testing Checklist

- [ ] Dry-run mode works
- [ ] Single book analysis completes
- [ ] Phase 3 consolidation succeeds
- [ ] Phase 4 generates files
- [ ] Phase 8.5 validation passes
- [ ] Cost tracking is accurate
- [ ] Backups are created
- [ ] Error recovery works
- [ ] Total cost under $10
- [ ] Complete workflow under 5 minutes

---

## Support

### Common Issues

**Q: Why is it using Gemini 2.0 Flash instead of Gemini 1.5 Pro?**
A: Gemini 1.5 Pro returned 404. The system automatically switched to the available model.

**Q: Why did Claude fail with rate limit?**
A: Claude has a 20k tokens/minute limit. The system gracefully continues with Gemini only.

**Q: How do I reset everything?**
A: Delete `implementation_plans/`, `backups/`, `cost_tracker/` and `analysis_results/` for a fresh start.

**Q: Can I run multiple workflows simultaneously?**
A: Not in Tier 0. Tier 1 adds parallel execution support.

---

## Cost Breakdown (Typical)

**Single Book Workflow:**
- Phase 2 (Analysis): ~$4.85
- Phase 3 (Consolidation): ~$0.05
- Phase 4 (Generation): ~$0.05
- Phase 8.5 (Validation): ~$0.00
- **Total: ~$5.00**

**45 Books (Full Analysis):**
- Phase 2: ~$218.25
- Phase 3: ~$2.25
- Phase 4: ~$2.25
- Phase 8.5: ~$0.00
- **Total: ~$225.00**

(Exceeds Tier 0 budget - Tier 1 needed)

---

**Last Updated:** 2025-10-18
**Version:** Tier 0 Day 3
**Status:** ✅ Ready for Testing

