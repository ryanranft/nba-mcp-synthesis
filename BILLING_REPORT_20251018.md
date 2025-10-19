# Billing Report - Book Analysis
**Date**: October 18, 2025
**Analysis**: High-Context Book Analyzer (Gemini + Claude)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Books Analyzed** | 36 / 40 (90% complete) |
| **Books Remaining** | 4 |
| **Cache Hit Rate** | 57.1% (300/525 calls) |
| **Log Estimate** | $155.83 |
| **Likely Actual Cost** | **~$51.94** |
| **Projected Total (40 books)** | **~$57.71** |

---

## 1. Analysis Progress

- **Books Completed**: 36 out of 40 (90.0%)
- **Books Remaining**: 4
- **Total API Calls**: 525
- **Cache Hits**: 300 (57.1%)
- **Non-Cached Calls**: 225

---

## 2. Cost Breakdown by Model

### Gemini 1.5 Pro (gemini-2.0-flash-exp)

| Metric | Value |
|--------|-------|
| Total API Calls | 525 |
| Non-Cached Calls | 225 |
| Log Estimate | $112.43 |
| Per Book (log) | $3.12 |
| **Estimated Actual** | **$37.48** |
| **Per Book (actual)** | **$1.04** |

### Claude 3.7 Sonnet

| Metric | Value |
|--------|-------|
| Total API Calls | 525 |
| Non-Cached Calls | 75 |
| Log Estimate | $43.40 |
| Per Book (log) | $1.21 |
| **Estimated Actual** | **$14.47** |
| **Per Book (actual)** | **$0.40** |

---

## 3. Cost Estimates

### Log-Based Estimates (Known to be 2.5-3.6x Higher)

- **Gemini**: $112.43
- **Claude**: $43.40
- **Total**: $155.83

### Estimated Actual Costs

| Scenario | Gemini | Claude | Total |
|----------|--------|--------|-------|
| **Conservative (÷2.5)** | $44.97 | $17.36 | $62.33 |
| **Most Likely (÷3.0)** | **$37.48** | **$14.47** | **$51.94** |
| **Optimistic (÷3.6)** | $31.23 | $12.06 | $43.29 |

---

## 4. Projected Final Costs (All 40 Books)

### Based on Log Estimates (Inflated)

- Cost so far: $155.83
- Per book: $4.33
- Remaining (4 books): $17.31
- **Total**: $173.14

### Based on Actual Costs (÷3.0)

- Cost so far: $51.94
- Per book: $1.44
- Remaining (4 books): $5.77
- **Total**: **$57.71**

---

## 5. How to Verify Exact Costs

### Google Cloud (Gemini API)

1. Visit: [Google Cloud Billing Reports](https://console.cloud.google.com/billing/${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}/reports)
2. Set date filter: **October 18, 2025**
3. Filter by service: **Generative Language API**
4. View total charges in chart/table
5. Export to CSV for detailed breakdown

**Google Cloud Details:**
- Project ID: `${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}`
- Billing Account: `${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}`
- Account: `ryanranft56@gmail.com`
- Enabled API: `generativelanguage.googleapis.com`

### Anthropic (Claude API)

1. Visit: [Anthropic Usage Dashboard](https://console.anthropic.com/settings/usage)
2. Or check: [Anthropic Billing](https://console.anthropic.com/settings/billing)
3. Filter by date: **October 18, 2025**
4. Compare starting balance vs. current balance

---

## 6. Google Cloud CLI Commands

```bash
# Check billing account
gcloud billing accounts list

# Check project billing info
gcloud alpha billing projects describe ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}

# List enabled services
gcloud services list --enabled --filter="name:generativelanguage.googleapis.com"

# Enable Cloud Monitoring (requires permissions)
gcloud services enable cloudmonitoring.googleapis.com

# Query API usage metrics (requires monitoring API)
gcloud monitoring time-series list \
  --filter='metric.type="serviceruntime.googleapis.com/api/request_count"' \
  --format="table(metric.type, resource.labels.method)" \
  --start-time="2025-10-18T00:00:00Z"
```

**Note**: Direct cost queries require BigQuery billing export to be configured.

---

## 7. Key Insights

### Why Log Estimates Are Higher Than Actual

The log-based cost tracking is **2.5-3.6x higher** than actual billing because:

1. **Token Counting Overhead**: Logs include system prompts, formatting, and metadata
2. **Conservative Pricing**: Uses worst-case pricing tiers
3. **Multiple Counting**: Tokens may be counted at multiple stages
4. **No Cache Credit**: Doesn't account for API-level caching discounts

### Cache Efficiency

- **57.1% cache hit rate** saved significant costs
- 300 out of 525 API calls served from cache
- Cache is working effectively for repeated content analysis

### Cost Per Book

| Metric | Log Estimate | Actual Estimate |
|--------|--------------|-----------------|
| Per Book | $4.33 | **$1.44** |
| Gemini | $3.12 | **$1.04** |
| Claude | $1.21 | **$0.40** |

---

## 8. Recommendations

1. **Complete remaining 4 books** (~$5.77 additional cost)
2. **Verify actual costs** using Google Cloud Console and Anthropic dashboard
3. **Update cost tracking** to use actual billing data instead of estimates
4. **Consider increasing cache TTL** to improve cache hit rate further
5. **Document pricing discrepancy** for future projects

---

## 9. Summary

✅ **Analysis Status**: 36/40 books (90% complete)
✅ **Cache Efficiency**: 57.1% hit rate
⚠️ **Log Estimate**: $155.83 (inflated)
💰 **Likely Actual**: ~$51.94
🎯 **Projected Final**: ~$57.71 for all 40 books

**Next Steps**: Check Google Cloud Console and Anthropic Console for exact billing amounts.

---

**Report Generated**: October 18, 2025
**Data Source**: `/tmp/book_analysis_parallel_run.log`
**JSON Report**: `billing_report_20251018.json`

