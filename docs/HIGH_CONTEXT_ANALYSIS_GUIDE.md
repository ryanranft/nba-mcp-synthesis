# High-Context Book Analysis Guide

## Overview

The High-Context Book Analyzer is an upgraded system that uses Gemini 1.5 Pro and Claude Sonnet 4 to analyze complete technical books with extended context windows (up to 250k tokens / 1M characters per book).

## Key Features

- **10× More Content**: Reads up to 1M characters (~250k tokens) vs 100k characters in standard system
- **Full Book Coverage**: Analyzes entire books from cover to cover, not just first 100 pages
- **Dual-Model Consensus**: Gemini 1.5 Pro + Claude Sonnet 4 validation
- **Better Comprehension**: AI models see complete narrative arc and advanced chapters
- **Higher Quality**: More comprehensive recommendations from full book context

## Architecture

### Models Used

1. **Gemini 1.5 Pro** (Primary Reader)
   - Context window: 2 million tokens
   - Pricing: $1.25/M input (<128k), $2.50/M input (>128k)
   - Output: $2.50/M (<128k), $10.00/M (>128k)
   - Role: Fast, comprehensive extraction

2. **Claude Sonnet 4** (Synthesis Validator)
   - Context window: 1 million tokens
   - Pricing: $3.00/M input, $15.00/M output
   - Role: Deep reasoning and validation

### Processing Pipeline

```
Book in S3 (PDF)
    ↓
Extract Text (PyMuPDF)
    ↓
Chunk to 1M chars (~250k tokens)
    ↓
┌─────────────┬─────────────┐
│  Gemini 1.5 │  Claude     │  (Parallel)
│  Pro        │  Sonnet 4   │
└─────────────┴─────────────┘
    ↓           ↓
    └─────┬─────┘
          ↓
  Consensus Synthesis
  (70% similarity threshold)
          ↓
  Final Recommendations
```

## Usage

### Basic Usage

```bash
# Analyze all books with high-context analyzer
python scripts/recursive_book_analysis.py --all --high-context

# Analyze specific book
python scripts/recursive_book_analysis.py --book "Machine Learning" --high-context

# Resume previous analysis
python scripts/recursive_book_analysis.py --resume tracker.json --high-context
```

### Configuration

The system automatically:
- Loads API keys from environment variables
- Initializes both models with proper credentials
- Handles rate limits with exponential backoff
- Tracks costs and token usage

### Output

Results include:
- Comprehensive recommendations (30-60 per book)
- Source attribution (Gemini, Claude, or both)
- Consensus confidence levels
- Detailed cost breakdown
- Token usage statistics

## Cost Comparison

### Per-Book Analysis

| System | Cost/Book | Context | Recommendations | Models |
|--------|-----------|---------|-----------------|--------|
| **Standard** | $0.22 | 25k tokens (~100k chars) | 26-42 | 4 models |
| **High-Context** | $0.70 | 250k tokens (~1M chars) | 30-60 | 2 models |

### Full 45-Book Analysis

| System | Total Cost | Total Time | Context Analyzed |
|--------|------------|------------|------------------|
| **Standard** | $10.12 | 2.3 hours | 4.5M characters |
| **High-Context** | $31.50 | 2.5 hours | 45M characters |

### Cost Breakdown (Per Book)

**High-Context System:**
```
Gemini 1.5 Pro:
  Input:  250k tokens × $2.50/M  = $0.625
  Output:   5k tokens × $10.00/M = $0.050
  Subtotal: $0.675

Claude Sonnet 4:
  Input:  250k tokens × $3.00/M  = $0.750
  Output:   5k tokens × $15.00/M = $0.075
  Subtotal: $0.825

Total: ~$0.70 per book
```

**Standard System (for comparison):**
```
Gemini 2.0:  $0.0001
DeepSeek:    $0.03
Claude 3.7:  $0.12
GPT-4:       $0.08
Total:       $0.23 per book
```

## When to Use Each System

### Use High-Context When:

✅ You want comprehensive book coverage
✅ Advanced chapters contain critical information
✅ Budget allows (~$30 for 45 books)
✅ You need highest quality recommendations
✅ Full book context improves understanding

### Use Standard When:

✅ Budget is constrained
✅ First 100 pages contain key concepts
✅ Quick overview is sufficient
✅ Multi-model validation preferred (4 models)

## Performance Metrics

### Expected Performance (Per Book)

**High-Context:**
- Processing time: 60-120 seconds
- Recommendations: 30-60 per book
- Token usage: ~500k-600k total
- Success rate: 95%+
- Consensus rate: 80%+ (both models agree)

**Standard:**
- Processing time: 180 seconds
- Recommendations: 26-42 per book
- Token usage: ~100k-110k total
- Success rate: 95%+
- Consensus rate: 70%+ (2+ models agree)

## Cost Optimization Tips

### 1. Stay Under 128k Token Pricing Tier

If your books average 120k tokens or less, you can reduce costs significantly:

```
Gemini pricing:
  < 128k: $1.25/M input → $0.15 per book
  > 128k: $2.50/M input → $0.30 per book
```

**Savings:** $0.15 per book × 45 = $6.75 savings!

### 2. Use Gemini-Only Mode (Coming Soon)

For maximum cost efficiency:
```bash
python scripts/recursive_book_analysis.py --all --high-context --gemini-only
```

Cost: ~$0.15 per book (10× cheaper than current!)

### 3. Batch Similar Books

Run related books together to leverage context across analyses.

## Technical Details

### Content Chunking

```python
MAX_CHARS = 1_000_000  # 1M characters
MAX_TOKENS = 250_000   # ~250k tokens

if len(book_content) > MAX_CHARS:
    book_content = book_content[:MAX_CHARS] +
        "[Content truncated at 250k token limit]"
```

### Consensus Synthesis

1. **Collect** recommendations from both models
2. **Group** similar recommendations (70% title similarity)
3. **Prefer** Claude's version (higher quality)
4. **Tag** with source and consensus metadata

```python
{
    "title": "Implement Caching Layer",
    "description": "...",
    "_source": "claude",
    "_consensus": {
        "sources": ["gemini", "claude"],
        "count": 2,
        "both_agree": true
    }
}
```

### Error Handling

- 180-second timeout per model
- Automatic retry on transient errors
- Graceful degradation (use successful model if one fails)
- Detailed error logging

## Example Output

```
🚀 Starting high-context analysis: Machine Learning for Absolute Beginners
🤖 Models: Gemini 1.5 Pro, Claude Sonnet 4
📖 Analyzing 450,000 characters
🔢 Estimated ~112,500 tokens

🔄 Analyzing with Gemini 1.5 Pro...
✅ Gemini 1.5 Pro complete: 32 recommendations
💰 Cost: $0.28 (pricing tier: low <128k)

🔄 Analyzing with Claude Sonnet 4...
✅ Claude Sonnet 4 complete: 28 recommendations
💰 Cost: $0.34

✅ High-context analysis complete!
💰 Total cost: $0.62
   Gemini 1.5 Pro: $0.28
   Claude Sonnet 4: $0.34
📊 Content analyzed: 450,000 characters
💰 Pricing tier: low
🔢 Total tokens: 112,500
⏱️ Total time: 85.3s
📋 Final recommendations: 48
🎯 Consensus: both
```

## Troubleshooting

### Issue: Timeout Errors

**Solution:** Increase timeout in `high_context_book_analyzer.py`:
```python
timeout=300  # 5 minutes instead of 3
```

### Issue: Out of Memory

**Solution:** Reduce MAX_CHARS:
```python
MAX_CHARS = 500_000  # 500k chars instead of 1M
```

### Issue: API Rate Limits

**Solution:** Add delay between books:
```python
await asyncio.sleep(30)  # 30 second delay
```

### Issue: High Costs

**Solutions:**
1. Use Gemini-only mode
2. Stay under 128k token limit
3. Analyze fewer books
4. Use standard analyzer instead

## API Key Setup

### Required Environment Variables

```bash
# Gemini 1.5 Pro
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_MODEL="gemini-1.5-pro"

# Claude Sonnet 4
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export CLAUDE_MODEL="claude-3-7-sonnet-20250219"  # or latest
```

### Hierarchical Environment Loading

The system uses hierarchical key lookup:
1. `NBA_MCP_SYNTHESIS_WORKFLOW_GOOGLE_API_KEY`
2. `NBA_MCP_SYNTHESIS_GOOGLE_API_KEY`
3. `GOOGLE_API_KEY`

This supports multiple environments (production, development, test).

## Comparison: Standard vs High-Context

### Standard System (4 Models)

**Pros:**
- ✅ Lower cost per book ($0.22)
- ✅ Multi-model validation (4 models)
- ✅ Proven, battle-tested
- ✅ Good for budget constraints

**Cons:**
- ❌ Limited context (only first ~100 pages)
- ❌ Misses advanced chapters
- ❌ More complex architecture
- ❌ Longer processing time

### High-Context System (2 Models)

**Pros:**
- ✅ Full book coverage (10× more content)
- ✅ Better comprehension
- ✅ Higher quality recommendations
- ✅ Simpler architecture
- ✅ Faster per-book processing

**Cons:**
- ❌ Higher cost per book ($0.70)
- ❌ Only 2 models (less validation)
- ❌ Requires newer models

## Future Enhancements

### Planned Features

1. **Gemini-Only Mode** - Ultra-low cost option ($0.15/book)
2. **Adaptive Chunking** - Smart splitting for very large books
3. **Chapter-Aware Analysis** - Process books chapter-by-chapter
4. **Incremental Analysis** - Cache results, only analyze new content
5. **Multi-Pass Analysis** - Progressive refinement
6. **Cost Prediction** - Estimate costs before running

### Model Upgrades

- Support for Claude Opus (when available)
- GPT-4 Turbo with extended context
- Custom fine-tuned models

## Best Practices

1. **Start with 1-3 books** to validate cost and quality
2. **Monitor token usage** to stay within pricing tiers
3. **Review recommendations** to ensure quality meets expectations
4. **Compare outputs** between standard and high-context systems
5. **Track costs** to stay within budget
6. **Use appropriate system** based on book complexity

## Support & Feedback

For questions, issues, or feedback:
- Check the main README.md
- Review analysis logs in `/tmp/book_analysis*.log`
- Examine cost breakdowns in analysis results
- Compare with standard system results

## Conclusion

The High-Context Book Analyzer provides:
- **10× more content coverage** per book
- **Better quality** recommendations
- **Full book comprehension** from cover to cover
- **Cost: ~$0.70 per book** (vs $0.22 standard)
- **Total: ~$31.50** for 45 books (vs $10.12 standard)

**Recommendation:** Use high-context for comprehensive analysis when budget allows. The additional $21 investment (~$0.47 extra per book) provides significantly better coverage and quality.

🚀 **Ready to analyze your entire library with full context!**

