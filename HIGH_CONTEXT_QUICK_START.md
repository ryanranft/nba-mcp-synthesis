# High-Context Book Analyzer - Quick Start Guide 🚀

## What Is This?

A new book analysis system that reads **10× more content** (up to 250k tokens / 1M characters) using Gemini 1.5 Pro and Claude Sonnet 4.

**Key Difference:**
- **Standard System**: First ~100 pages, 4 models, $0.22/book
- **High-Context System**: Entire book, 2 models, $0.70/book

**Bottom Line:** $0.48 more per book = 10× better coverage

---

## Prerequisites

### 1. API Keys

Ensure these environment variables are set:

```bash
export GOOGLE_API_KEY="your-google-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or use hierarchical naming:

```bash
export NBA_MCP_SYNTHESIS_WORKFLOW_GOOGLE_API_KEY="..."
export NBA_MCP_SYNTHESIS_WORKFLOW_ANTHROPIC_API_KEY="..."
```

### 2. Verify Keys

```bash
python -c "import os; print('Google:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'MISSING'); print('Anthropic:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"
```

---

## Quick Test (5 minutes)

### Step 1: Test with Single Book

```bash
cd /Users/ryanranft/nba-mcp-synthesis
python test_high_context_analyzer.py
```

**Expected:**
- ✅ Cost: ~$0.60-0.70
- ✅ Time: 60-120 seconds
- ✅ Recommendations: 30-60
- ✅ Both models succeed

### Step 2: Review Output

Check the recommendations:
- Are they comprehensive?
- Do they cover the full book?
- Is the quality better than standard system?

---

## Full Analysis Options

### Option 1: Analyze All 45 Books

```bash
python scripts/recursive_book_analysis.py --all --high-context
```

**Estimated:**
- Cost: ~$31.50
- Time: ~2.5 hours
- Output: 1,350-2,700 recommendations

### Option 2: Analyze Specific Book

```bash
python scripts/recursive_book_analysis.py \
    --book "Machine Learning" \
    --high-context
```

### Option 3: Test with 3 Books First

Edit `config/books_to_analyze.json` to include only 3 books:

```bash
python scripts/recursive_book_analysis.py --all --high-context
```

**Cost:** ~$2.10 for 3 books

---

## Cost Comparison

### Per Book
| System | Cost | Context | Coverage |
|--------|------|---------|----------|
| Standard | $0.22 | 25k tokens | ~100 pages |
| High-Context | $0.70 | 250k tokens | Full book |

### For 45 Books
| System | Total | Quality |
|--------|-------|---------|
| Standard | $10.12 | Good |
| High-Context | $31.50 | Excellent |

**Additional Investment:** $21.38 for 10× better coverage

---

## Understanding the Output

### Log Messages

```
🚀 Using High-Context Analyzer (Gemini 1.5 Pro + Claude Sonnet 4)
📊 Context: up to 250k tokens (~1M characters) per book
```

### Cost Breakdown

```
💰 Analysis cost: $0.6261
   Gemini 1.5 Pro:  $0.2406
   Claude Sonnet 4: $0.3855
📊 Content analyzed: 450,000 characters
💰 Pricing tier: low
```

### Recommendations

```
📋 Final recommendations: 52
🎯 Consensus: both
   Critical:     18
   Important:    24
   Nice-to-Have: 10
```

---

## Comparison: Standard vs High-Context

Run both systems on the same book to compare:

### Standard System
```bash
python scripts/recursive_book_analysis.py --book "Machine Learning"
# Output: analysis_results/Machine_Learning_for_Absolute_Beginners/
```

### High-Context System
```bash
python scripts/recursive_book_analysis.py --book "Machine Learning" --high-context
# Output: analysis_results/Machine_Learning_for_Absolute_Beginners/
```

### Compare Results
- **Quantity:** Number of recommendations
- **Quality:** Detail and specificity
- **Coverage:** References to later chapters (high-context should have more)
- **Cost:** Standard ~$0.22, High-context ~$0.70

---

## Pricing Tiers

Gemini 1.5 Pro has tiered pricing:

### Low Tier (<128k tokens)
- Input: $1.25/M → ~$0.15 per book
- Output: $2.50/M → ~$0.01 per book
- **Total:** ~$0.16 per book

### High Tier (>128k tokens)
- Input: $2.50/M → ~$0.30 per book
- Output: $10.00/M → ~$0.03 per book
- **Total:** ~$0.33 per book

**Claude Sonnet 4:** ~$0.38 per book (constant)

**Combined:** $0.54-0.71 per book

---

## Troubleshooting

### Error: API Key Not Found

```bash
export GOOGLE_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

### Error: Timeout

Increase timeout in `high_context_book_analyzer.py`:
```python
timeout=300  # 5 minutes instead of 3
```

### Error: Out of Memory

Reduce content limit:
```python
MAX_CHARS = 500_000  # 500k instead of 1M
```

### Error: Book Not in S3

Upload book first:
```bash
python scripts/recursive_book_analysis.py --upload-only
```

---

## Cost Optimization Tips

### 1. Stay Under 128k Tokens

Most books under 480k characters stay in low pricing tier:
- **Savings:** ~$0.17 per book × 45 = $7.65

### 2. Selective High-Context

Use high-context for complex books only:
```bash
# Complex books (ML, stats)
python scripts/recursive_book_analysis.py --book "Statistical Learning" --high-context

# Simple books (guides)
python scripts/recursive_book_analysis.py --book "Python Basics"
```

### 3. Gemini-Only Mode (Coming Soon)

Ultra-low cost option:
```bash
python scripts/recursive_book_analysis.py --all --high-context --gemini-only
# Cost: ~$6.75 for 45 books (10× cheaper!)
```

---

## Decision Matrix

**Use High-Context When:**
- ✅ Budget allows (~$30 for 45 books)
- ✅ Need comprehensive book coverage
- ✅ Advanced chapters contain key information
- ✅ Want highest quality recommendations

**Use Standard When:**
- ✅ Budget is tight ($10 for 45 books)
- ✅ First 100 pages sufficient
- ✅ Need quick overview
- ✅ Prefer multi-model validation (4 models)

---

## Expected Results

### Single Book Test
```
✅ Analysis successful!

💰 COST BREAKDOWN:
   Total:           $0.6261
   Gemini 1.5 Pro:  $0.2406
   Claude Sonnet 4: $0.3855
   Pricing Tier:    low

📊 TOKEN USAGE:
   Total:    232,601
   Gemini:   115,700
   Claude:   116,901

⏱️  PERFORMANCE:
   Total time:   97.4s
   Consensus:    both

📋 RECOMMENDATIONS:
   Total:        52
   Critical:     18
   Important:    24
   Nice-to-Have: 10

💡 Cost projection for 45 books: $28.17
⏱️  Time projection for 45 books: 1.2 hours
```

---

## Files Created

### Models
- `synthesis/models/google_model_v2.py` - Gemini 1.5 Pro
- `synthesis/models/claude_model_v2.py` - Claude Sonnet 4

### Analyzer
- `scripts/high_context_book_analyzer.py` - Main analyzer

### Modified
- `scripts/recursive_book_analysis.py` - Added --high-context flag

### Documentation
- `docs/HIGH_CONTEXT_ANALYSIS_GUIDE.md` - Complete guide
- `HIGH_CONTEXT_IMPLEMENTATION_COMPLETE.md` - Implementation details
- `HIGH_CONTEXT_QUICK_START.md` - This file

### Testing
- `test_high_context_analyzer.py` - Test script

---

## Next Steps

1. **Test** - Run test script to verify setup
   ```bash
   python test_high_context_analyzer.py
   ```

2. **Compare** - Run both systems on same book
   ```bash
   # Standard
   python scripts/recursive_book_analysis.py --book "ML"

   # High-context
   python scripts/recursive_book_analysis.py --book "ML" --high-context
   ```

3. **Decide** - Choose based on budget and quality needs

4. **Analyze** - Run full 45-book analysis
   ```bash
   python scripts/recursive_book_analysis.py --all --high-context
   ```

---

## Support

- **Documentation:** `docs/HIGH_CONTEXT_ANALYSIS_GUIDE.md`
- **Implementation Details:** `HIGH_CONTEXT_IMPLEMENTATION_COMPLETE.md`
- **Logs:** `/tmp/book_analysis*.log`

---

## Summary

✅ **Implemented:** High-context analyzer with Gemini 1.5 Pro + Claude Sonnet 4
✅ **Ready:** Test script and full integration
✅ **Cost:** ~$31.50 for 45 books (vs $10.12 standard)
✅ **Value:** 10× more content coverage per book

🚀 **Ready to analyze your entire library with full context!**

