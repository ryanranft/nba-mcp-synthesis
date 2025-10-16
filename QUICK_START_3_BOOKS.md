# Quick Start: 3-Book Real Analysis

## Prerequisites

1. **API Keys Required:**
   - Google Gemini API key
   - DeepSeek API key
   - Anthropic Claude API key
   - OpenAI GPT-4 API key

2. **Budget:** $50 recommended (actual cost ~$25-30)

## Execution Steps

### 1. Set Environment Variables
```bash
export GOOGLE_API_KEY='your-google-api-key'
export DEEPSEEK_API_KEY='your-deepseek-api-key'
export ANTHROPIC_API_KEY='your-claude-api-key'
export OPENAI_API_KEY='your-gpt4-api-key'
```

### 2. Run Analysis
```bash
cd /Users/ryanranft/nba-mcp-synthesis

python scripts/launch_complete_workflow.py \
  --config config/books_test_3.json \
  --budget 50 \
  --output analysis_results/test_3_books/ \
  --generate-implementations
```

### 3. Monitor Progress
- Check logs for real-time progress
- Monitor cost tracking in `analysis_results/test_3_books/cost_tracking.json`
- Review recommendations as they're generated

## Expected Output

**Files Created:**
- `analysis_results/test_3_books/master_recommendations.json`
- `analysis_results/test_3_books/cost_tracking.json`
- `analysis_results/test_3_books/books/` (book-specific directories)
- `nba-simulator-aws/docs/phases/phase_X/` (implementation files)

**Timeline:** 30-60 minutes
**Cost:** $20-30
**Recommendations:** 8-15 detailed recommendations
**Implementation Files:** 32-60 files

## After Completion

1. **Review Results:**
   - Check `analysis_results/test_3_books/TEST_REPORT.md`
   - Review generated recommendations
   - Validate implementation files

2. **Scale to Full Run:**
   - If test successful, proceed with 20-book overnight analysis
   - Use `config/books_to_analyze_all_ai_ml.json`
   - Budget: $410 for full run

## Troubleshooting

**API Key Issues:**
- Verify keys are set: `echo $GOOGLE_API_KEY`
- Check API quotas and billing

**File Access Issues:**
- Verify book files exist locally
- Check file permissions

**Budget Exceeded:**
- Monitor cost tracking file
- Adjust budget parameter if needed




