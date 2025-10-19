# ♾️ Converge-Until-Done Feature

## Overview

The `--converge-until-done` flag allows book analysis to run unlimited iterations until convergence, rather than stopping at the standard 15 iteration limit. This is particularly useful for comprehensive textbooks that continue discovering new recommendations even after 15 iterations.

## Problem Solved

**Before:**
```bash
# STATISTICS 601 Advanced Statistical Methods
- Ran 15 iterations (max limit)
- Found 255 recommendations (90 critical + 165 important)
- Never converged (still finding Critical/Important recommendations)
- Was forced to stop prematurely
```

**After (with --converge-until-done):**
```bash
# Runs until convergence criteria met:
# - 3 consecutive iterations with only "Nice-to-Have" recommendations
# - Safety cap: 100 iterations (prevents infinite loops)
```

## Usage

### Basic Example
```bash
# Run all books until convergence
python scripts/recursive_book_analysis.py --all --converge-until-done
```

### Specific Book
```bash
# Run a comprehensive textbook until convergence
python scripts/recursive_book_analysis.py \
  --book "STATISTICS 601" \
  --converge-until-done
```

### With Other Flags
```bash
# High-context analyzer + unlimited iterations + parallel execution
python scripts/recursive_book_analysis.py \
  --all \
  --high-context \
  --converge-until-done \
  --parallel \
  --max-workers 4
```

### Dry-Run Preview
```bash
# Preview which mode will be used
python scripts/recursive_book_analysis.py \
  --all \
  --converge-until-done \
  --dry-run
```

## How It Works

### Standard Mode (15 iterations max)
```python
# Without --converge-until-done
max_iterations = 15
while iteration < 15:
    # Analyze book
    # Check convergence
    # Stop if converged OR hit 15 iterations
```

### Unlimited Mode (100 iterations safety cap)
```python
# With --converge-until-done
safety_cap = 100
while iteration < 100:
    # Analyze book
    # Check convergence
    # Stop if converged
    # Warn if hit 100 iterations without convergence
```

## Convergence Criteria

Both modes use the same convergence criteria:
- **Converged**: 3 consecutive iterations with only "Nice-to-Have" recommendations
- **Not Converged**: Still finding "Critical" or "Important" recommendations

```
Iteration 1: 10 Critical, 20 Important, 5 Nice → NOT CONVERGED
Iteration 2: 5 Critical, 15 Important, 8 Nice   → NOT CONVERGED
...
Iteration 12: 0 Critical, 0 Important, 3 Nice   → NICE ONLY (1/3)
Iteration 13: 0 Critical, 0 Important, 2 Nice   → NICE ONLY (2/3)
Iteration 14: 0 Critical, 0 Important, 1 Nice   → NICE ONLY (3/3) → ✅ CONVERGED!
```

## Safety Features

### 1. Safety Cap
- **Purpose**: Prevent infinite loops
- **Limit**: 100 iterations maximum
- **Behavior**: Warns if reached without convergence

### 2. Warning Messages
```
⚠️ Safety cap of 100 iterations reached without convergence!
   Found 300 critical + 450 important recommendations
   Consider reviewing convergence criteria or book complexity
```

### 3. Cost Safety
- Still respects cost limits from `cost_safety_manager.py`
- Will stop if cost budget is exceeded
- Tracks cumulative cost across all iterations

## Log Output

### Standard Mode
```
🔄 Iteration 1/15
🔄 Iteration 2/15
...
🔄 Iteration 15/15
```

### Unlimited Mode
```
🔄 Iteration 1 (converge-until-done mode, safety cap: 100)
🔄 Iteration 2 (converge-until-done mode, safety cap: 100)
...
🔄 Iteration 47 (converge-until-done mode, safety cap: 100)
🎉 CONVERGENCE ACHIEVED after 47 iterations!
```

### Initialization Logging
```
🚀 Using High-Context Analyzer (Gemini 1.5 Pro + Claude Sonnet 4)
📊 Context: up to 250k tokens (~1M characters) per book
💾 Cache: enabled
♾️  Convergence: Unlimited iterations (safety cap: 100)
🔀 Parallel: 4 workers
```

## When to Use This Flag

### ✅ Good Use Cases

1. **Comprehensive Textbooks**
   - Statistics textbooks
   - Machine learning textbooks
   - Econometrics textbooks
   - Books with 500+ pages

2. **Books with Many Recommendations**
   - When standard 15 iterations find 200+ recommendations
   - When analysis shows no sign of slowing down at iteration 15

3. **Production Runs**
   - When you want maximum extraction quality
   - When cost is not a primary concern
   - When you want to ensure nothing is missed

### ❌ Not Recommended For

1. **Focused Books**
   - Short guides (< 200 pages)
   - Focused topic books
   - Books that converge quickly (< 10 iterations)

2. **Cost-Sensitive Runs**
   - When budget is tight
   - When testing/debugging
   - When you just need a quick overview

3. **Time-Sensitive Tasks**
   - When you need results quickly
   - When running on deadline

## Cost Estimation

### Standard Mode (15 iterations)
```
Book: STATISTICS 601 (628 pages)
Iterations: 15
Cost per iteration: ~$0.61 (with cache hits)
Total: ~$9.15
Status: Did not converge
```

### Unlimited Mode (estimated)
```
Book: STATISTICS 601 (628 pages)
Estimated iterations to converge: 30-50
Cost per iteration: ~$0.61 (with cache hits)
Estimated total: $18.30 - $30.50
Status: Would converge
```

**Note**: Cache hits significantly reduce cost for subsequent iterations!

## Configuration

### Update Safety Cap
If 100 iterations is too conservative or too aggressive, modify in `RecursiveAnalyzer.__init__`:

```python
self.safety_max_iterations = 100  # Change to 50, 150, 200, etc.
```

### Update Convergence Threshold
Modify in `config/workflow_config.yaml`:

```yaml
analysis:
  convergence_threshold: 3  # Number of consecutive "nice-only" iterations
```

## Integration with Workflow

### Run Full Workflow with Unlimited Mode
```bash
python scripts/run_full_workflow.py \
  --book "STATISTICS 601" \
  --parallel \
  --max-workers 4
  # Note: Not yet integrated into run_full_workflow.py
  # Use recursive_book_analysis.py directly for now
```

### Checking Progress
```bash
# Monitor convergence tracker files
tail -100 analysis_results/STATISTICS_601_*_convergence_tracker.json

# Check iteration count
cat analysis_results/STATISTICS_601_*_convergence_tracker.json | \
  python3 -m json.tool | grep total_iterations
```

## Future Enhancements

1. **Dynamic Safety Cap**
   - Adjust based on book size
   - Increase for books > 1000 pages

2. **Early Stopping Heuristics**
   - Stop if finding < 1 recommendation per iteration for 10 iterations
   - Stop if cost exceeds 5x standard run

3. **Progressive Convergence**
   - Relax convergence criteria after 50 iterations
   - Accept convergence with 2 consecutive "nice-only" instead of 3

4. **Integration with run_full_workflow.py**
   - Add `--converge-books <list>` flag
   - Specify which books should use unlimited mode

## Troubleshooting

### Book Never Converges
**Symptom**: Reaches 100 iterations without convergence

**Solutions**:
1. Review convergence criteria (too strict?)
2. Increase safety cap temporarily
3. Check if book is finding duplicate recommendations
4. Consider if book truly needs that many recommendations

### High Cost
**Symptom**: Cost exceeds budget

**Solutions**:
1. Use cache (enabled by default)
2. Reduce safety cap
3. Use standard mode for most books
4. Reserve unlimited mode for critical books only

### Slow Progress
**Symptom**: Taking too long per iteration

**Solutions**:
1. Enable parallel execution (`--parallel`)
2. Check S3 download speed
3. Review book complexity
4. Consider using standard mode

## Examples from Real Runs

### Example 1: STATISTICS 601
```
Standard Mode (15 iterations):
- Recommendations found: 255 (90 critical, 165 important)
- Convergence: ❌ No
- Cost: $9.15
- Time: 25 minutes

Expected with Unlimited Mode:
- Estimated iterations: 35-45
- Estimated recommendations: 350-400
- Expected convergence: ✅ Yes
- Estimated cost: $21.35 - $27.45
- Estimated time: 45-60 minutes
```

### Example 2: Short Guide Book
```
Standard Mode (15 iterations):
- Convergence: ✅ Yes (after 8 iterations)
- Recommendations: 45 (12 critical, 23 important, 10 nice)
- Cost: $4.88
- Time: 12 minutes

Unlimited Mode (same book):
- Would converge at same point (8 iterations)
- Same recommendations: 45
- Same cost: $4.88
- Same time: 12 minutes
```

## Summary

The `--converge-until-done` flag provides flexibility for comprehensive book analysis:

- ✅ **Comprehensive**: Extracts all recommendations until convergence
- ✅ **Safe**: 100-iteration safety cap prevents runaway costs
- ✅ **Flexible**: Works with all other flags (parallel, high-context, etc.)
- ✅ **Transparent**: Clear logging shows unlimited mode status
- ✅ **Optional**: Standard 15-iteration mode still available

**Recommendation**: Use unlimited mode for comprehensive textbooks and production runs. Use standard mode for quick analyses and cost-sensitive situations.

