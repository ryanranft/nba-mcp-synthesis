# Billing Cost Query - Quick Reference

**TL;DR**: Query actual Gemini API costs via terminal using BigQuery billing export.

---

## Current Status

❌ **BigQuery billing export is NOT yet configured**

**What you can do now:**
- ✅ Check log-based estimates (3x inflated)
- ✅ Manually check Google Cloud Console
- ✅ Manually check Anthropic Console

**What you need to enable terminal queries:**
- ⏳ Configure BigQuery billing export (see full guide below)

---

## Quick Commands (Once BigQuery is Set Up)

### Check if BigQuery is configured:
```bash
python3 scripts/check_gemini_costs.py --check-setup
```

### Today's Gemini costs:
```bash
python3 scripts/check_gemini_costs.py --today
```

### Yesterday's costs:
```bash
python3 scripts/check_gemini_costs.py --yesterday
```

### Last 7 days:
```bash
python3 scripts/check_gemini_costs.py --last-7-days
```

### Specific date with details:
```bash
python3 scripts/check_gemini_costs.py --date 2025-10-18 --detailed
```

---

## Setup BigQuery Billing Export (One-Time)

**5-Minute Setup via Web Console:**

1. **Go to**: https://console.cloud.google.com/billing/${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
2. **Click**: "Billing export" → "BigQuery export"
3. **Click**: "EDIT SETTINGS" under "Standard usage cost data"
4. **Select**:
   - Project: `${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}`
   - Dataset: `billing_export` (create if needed)
   - Location: `US`
5. **Click**: "SAVE"

⏰ **Wait 24 hours** for initial data to populate

**Full instructions**: `docs/BIGQUERY_BILLING_SETUP.md`

---

## Current Workarounds

### Option 1: Log-Based Estimates (Inflated 3x)
```bash
# View comprehensive report
cat BILLING_REPORT_20251018.md

# View JSON data
cat billing_report_20251018.json
```

**Current estimates** (36 books analyzed):
- Log estimate: $155.83
- **Likely actual: ~$51.94**
- Projected 40 books: **~$57.71**

### Option 2: Manual Console Check

**Gemini (Google Cloud):**
1. Visit: https://console.cloud.google.com/billing/${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}/reports
2. Filter: "Generative Language API" + "October 18, 2025"
3. View cost chart/table

**Claude (Anthropic):**
1. Visit: https://console.anthropic.com/settings/usage
2. Check balance changes for today

---

## Raw BigQuery Commands (Advanced)

Once billing export is configured:

```bash
# Total Gemini costs for today
bq query --use_legacy_sql=false \
"SELECT SUM(cost) as total_cost 
 FROM \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\` 
 WHERE _PARTITIONDATE = CURRENT_DATE() 
   AND service.description = 'Generative Language API'"

# Detailed breakdown by SKU
bq query --use_legacy_sql=false \
"SELECT
   sku.description,
   SUM(cost) as cost_usd,
   SUM(usage.amount) as tokens
 FROM \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\` 
 WHERE _PARTITIONDATE = '2025-10-18'
   AND service.description = 'Generative Language API'
 GROUP BY sku.description
 ORDER BY cost_usd DESC"
```

---

## Key Information

| Item | Value |
|------|-------|
| **Project ID** | ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY} |
| **Billing Account** | ${GOOGLE_CLOUD_BILLING_ACCOUNT_ID} |
| **BigQuery Dataset** | billing_export (once created) |
| **Table Name** | ${BIGQUERY_BILLING_EXPORT_TABLE} |
| **Account Email** | ryanranft56@gmail.com |

---

## Troubleshooting

### "bq: command not found"
```bash
# Ensure gcloud SDK is in PATH
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
```

### "Dataset not found"
**Solution**: BigQuery billing export hasn't been configured yet. Follow setup steps above.

### "Permission denied"
**Solution**: 
```bash
gcloud auth login
gcloud auth application-default login
```

### "No data available"
**Reasons**:
- Export was just configured (wait 24 hours)
- No usage on queried date
- Wrong date format (use YYYY-MM-DD)

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/BIGQUERY_BILLING_SETUP.md` | Complete setup guide with all commands |
| `scripts/check_gemini_costs.py` | Automated cost query script |
| `BILLING_REPORT_20251018.md` | Today's cost report (log-based estimates) |
| `billing_report_20251018.json` | Machine-readable cost data |
| `BILLING_QUICK_REFERENCE.md` | This file |

---

## Next Steps

1. ⏳ **Configure BigQuery billing export** (5 minutes, via web console)
2. ⏰ **Wait 24 hours** for initial data
3. ✅ **Run**: `python3 scripts/check_gemini_costs.py --check-setup`
4. ✅ **Query costs**: `python3 scripts/check_gemini_costs.py --today`

---

**Last Updated**: October 18, 2025  
**Status**: Documentation complete, awaiting BigQuery export configuration  
**Estimated Setup Time**: 5 minutes + 24 hour wait

