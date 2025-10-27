# Claude API Credits - Requirements & Setup Guide

**Date:** October 25, 2025
**Status:** CRITICAL - Required for Phase 9+
**Priority:** HIGH

---

## Current Situation

Your **Claude API credits are exhausted**, causing all Claude Sonnet 4 API calls to fail with:

```
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error',
'message': 'Your credit balance is too low to access the Anthropic API.
Please go to Plans & Billing to upgrade or purchase credits.'}}
```

**Impact:**
- Phase 2 completed with **Gemini-only analysis** (single-model instead of dual-model)
- Phase 9+ **cannot proceed** without Claude API access
- Reduced recommendation quality (no multi-model consensus)

---

## Why Claude API is Critical

### Phase 2 (Book Analysis) - Partially Completed
- **Gemini 1.5 Pro:** Analyzes book content, extracts recommendations
- **Claude Sonnet 4:** Validates, synthesizes, adds project context
- **Without Claude:** Generic recommendations, no consensus validation

### Phase 9 (Integration Analysis) - BLOCKED
- **Gemini 1.5 Pro:** Analyzes codebase structure
- **Claude Sonnet 4:** Generates integration strategies, placement decisions
- **Without Claude:** Cannot determine WHERE to implement recommendations

### Phase 10-12 (Implementation, Testing, Deployment) - BLOCKED
- **Both models:** Code generation, testing strategies, deployment plans
- **Without Claude:** Severely limited AI assistance

---

## Credit Requirements

### Immediate Need (Phase 9)
- **Minimum:** $50
- **Recommended:** $100
- **Usage:** ~1,643 integration analyses

**Cost Breakdown:**
- Input: ~1,643 × 10,000 tokens = 16.4M tokens × $3/M = $49.20
- Output: ~1,643 × 5,000 tokens = 8.2M tokens × $15/M = $123.00
- **Total estimated:** $172.20
- **With caching:** ~$100-125 (30% savings on repeated content)

### Phase 10-12 Estimate
- **Implementation code generation:** $50-75
- **Testing and validation:** $25-50
- **Deployment strategies:** $25-40
- **Total:** $100-165

### Recommended Total Purchase
- **Conservative:** $150 (covers Phase 9 + some Phase 10)
- **Recommended:** $250 (covers all remaining phases)
- **Generous:** $500 (covers everything + future iterations)

---

## How to Add Credits

### Step 1: Access Anthropic Console
1. Go to: https://console.anthropic.com
2. Log in with your account
3. Navigate to: **Settings → Plans & Billing**

### Step 2: Purchase Credits
1. Click **"Add Credits"** or **"Purchase Credits"**
2. Select amount:
   - **$50** (minimum for Phase 9)
   - **$100** (recommended for Phase 9)
   - **$250** (recommended for all phases)
   - **$500** (generous, covers future work)
3. Enter payment information
4. Confirm purchase

### Step 3: Verify Credits Added
```bash
# Option 1: Test with simple API call
python3 -c "
import anthropic
client = anthropic.Anthropic()
message = client.messages.create(
    model='claude-sonnet-4-20250514',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print('✅ Claude API working!')
print(f'Response: {message.content[0].text}')
"

# Option 2: Check via web console
# Go to console.anthropic.com → Settings → Usage
# Should show updated credit balance
```

### Step 4: Resume Work
Once credits are verified:
1. Run Phase 9 preparation checks (see PHASE9_PREPARATION_PLAN.md)
2. Execute Phase 9 integration analysis
3. Continue with Phases 10-12

---

## Alternative: Use GPT-4 as Backup

If you cannot add Claude credits immediately, you can **temporarily use GPT-4** as a backup model.

### Prerequisites
- OpenAI API key with GPT-4 access
- Sufficient OpenAI credits

### Configuration
```bash
# 1. Set OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# 2. Update workflow config to use GPT-4
# Edit: config/workflow_config.yaml
# Change: secondary_model: "claude-sonnet-4"
# To: secondary_model: "gpt-4-turbo"
```

### Cost Comparison
| Model | Input ($/1M) | Output ($/1M) | Phase 9 Est. |
|-------|--------------|---------------|--------------|
| Claude Sonnet 4 | $3 | $15 | $172 |
| GPT-4 Turbo | $10 | $30 | $410 |
| GPT-4o | $5 | $15 | $205 |

**Recommendation:** Claude is **2-2.4x cheaper** than GPT-4. Worth adding credits.

---

## Cost Optimization Tips

### 1. Use Prompt Caching (Anthropic)
- Saves 30-40% on repeated content
- Automatically enabled in our scripts
- Works best for project context (READMEs, file structures)

**Example savings:**
- Without caching: $172
- With caching: $100-120
- **Savings: $52-72** (30-42%)

### 2. Batch Processing
- Process recommendations in batches of 100
- Reuse context across batch
- Reduces API calls

### 3. Smart Model Selection
- Use Gemini for initial analysis (cheaper)
- Use Claude for synthesis and strategies (better quality)
- Use both for validation (best results)

### 4. Set Budget Limits
```python
# In config/workflow_config.yaml
cost_controls:
  max_cost_per_book: 5.00  # Stop if book costs exceed $5
  max_total_cost: 250.00   # Stop if total exceeds $250
  alert_threshold: 200.00  # Alert at $200
```

---

## Monitoring Costs

### Real-Time Tracking
```bash
# Watch cost accumulation in logs
tail -f logs/phase9_*.log | grep "💰"

# Check cumulative cost
grep "💰 Total cost:" logs/phase9_*.log | tail -1

# Get cost breakdown
python3 scripts/cost_summary.py
```

### Daily Budget Alert
```bash
# Set up cron job to alert if daily cost exceeds threshold
echo "0 18 * * * python3 scripts/cost_alert.py --threshold 50" | crontab -
```

### Cost Reports
After each phase:
```bash
# Generate cost report
python3 scripts/generate_cost_report.py \
  --phase phase_9 \
  --output implementation_plans/COST_REPORT_PHASE9.md
```

---

## FAQ

### Q: How much do I really need?
**A:** Minimum $50 for Phase 9 only. Recommended $250 for all remaining work.

### Q: Can I use a cheaper model?
**A:** Yes, but quality may suffer. Claude Sonnet 4 is already the best cost/quality balance.

### Q: What if I run out mid-phase?
**A:** Phase 9 will save progress. You can add credits and resume where it left off.

### Q: Can I get a discount?
**A:** Contact Anthropic sales for volume pricing if planning extensive use.

### Q: Is there a free tier?
**A:** Anthropic offers trial credits for new users. Check console.anthropic.com.

### Q: Can I use Claude 3.5 Sonnet instead?
**A:** Yes, it's cheaper but slightly lower quality. Edit `config/workflow_config.yaml`:
```yaml
secondary_model: "claude-3-5-sonnet-20241022"  # Instead of claude-sonnet-4
```

---

## Current API Key Status

### Check Your Keys
```bash
# 1. Claude API key
echo $CLAUDE_API_KEY | cut -c1-20
# Should output: sk-ant-...

# 2. Gemini API key
echo $GEMINI_API_KEY | cut -c1-20
# Should output: AIza...

# 3. Test Claude access
python3 -c "
import os
print('Claude key set:', 'CLAUDE_API_KEY' in os.environ)
print('Gemini key set:', 'GEMINI_API_KEY' in os.environ)
"
```

### Load from Secrets
```bash
# If keys not set, load from secrets directory
source setup_secrets_and_launch.sh

# Or manually:
export CLAUDE_API_KEY=$(cat /Users/ryanranft/.secrets/claude/api_key)
export GEMINI_API_KEY=$(cat /Users/ryanranft/.secrets/google-cloud/gemini_api_key)
```

---

## Troubleshooting

### Issue: Still getting 400 error after adding credits
**Solutions:**
1. Wait 5-10 minutes for credit update to propagate
2. Check credit balance at console.anthropic.com
3. Verify API key is correct: `echo $CLAUDE_API_KEY`
4. Try test call (see Step 3 above)

### Issue: "Rate limit exceeded" error
**Solutions:**
1. Wait 60 seconds and retry
2. Reduce parallel_workers in config (current: 4 → try: 2)
3. Add delays between API calls
4. Contact Anthropic to increase rate limits

### Issue: Credits deducted but no response
**Solutions:**
1. Check API logs for errors
2. Verify response isn't truncated (check max_tokens)
3. Try with smaller input
4. Contact Anthropic support if persistent

### Issue: Cost exceeding estimates
**Solutions:**
1. Check if caching is enabled
2. Review input token counts (may be larger than expected)
3. Reduce max_tokens in prompts
4. Use cost controls (set max_cost limits)

---

## Next Steps

### Immediate (Today)
1. **Add $100-250 Claude API credits**
2. Verify credits with test call
3. Review Phase 9 preparation plan
4. Run Phase 9 integration analysis

### Short-Term (This Week)
1. Complete Phase 9 (4-6 hours)
2. Review Phase 9 outputs
3. Plan Phase 10A/B execution
4. Begin implementing top recommendations

### Long-Term (This Month)
1. Complete Phases 10-12
2. Deploy MCP enhancements
3. Deploy simulator improvements
4. Monitor costs and optimize

---

## Summary

**Action Required:** Add Claude API credits to continue
**Minimum Amount:** $50 (Phase 9 only)
**Recommended Amount:** $250 (all phases)
**Where to Add:** https://console.anthropic.com → Settings → Plans & Billing
**Urgency:** HIGH - Blocking progress on Phase 9+

Once credits are added, you can immediately proceed with Phase 9 integration analysis.

---

**Status:** ⚠️ BLOCKED - Claude API credits needed
**Next Action:** Add credits at console.anthropic.com
**Time to Resolve:** 10-15 minutes (credit addition + verification)

---

*Guide created: October 25, 2025*
*Last updated: October 25, 2025*
*Related: PHASE9_PREPARATION_PLAN.md, TIER1_RUN_STATUS_REPORT.md*
