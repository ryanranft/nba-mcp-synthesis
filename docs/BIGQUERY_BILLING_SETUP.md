# BigQuery Billing Export Setup Guide

**Status**: ✅ Dataset Created | ⏳ Awaiting Export Configuration  
**Dataset Created**: 2025-10-18 19:50 UTC

**Purpose**: Enable programmatic cost querying via terminal for Gemini API usage
**Project**: ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
**Billing Account**: ${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
**Dataset**: billing_export (US location)

---

## Overview

By exporting Google Cloud billing data to BigQuery, you can query your actual API costs using SQL commands from the terminal. This eliminates the need to rely on log-based estimates (which are 3x inflated) and enables:

- Real-time cost monitoring
- Automated cost reporting
- Detailed usage analysis by service/SKU
- Integration with alerting systems

---

## Step 1: Set Up BigQuery Billing Export

### 1.1 Enable BigQuery API

```bash
# Enable BigQuery API for your project
gcloud services enable bigquery.googleapis.com --project=${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
```

### 1.2 Create BigQuery Dataset (Web Console)

Since this requires billing account permissions, use the Google Cloud Console:

1. **Navigate to Billing Export**:
   - Go to: https://console.cloud.google.com/billing/${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
   - In the left menu, click **"Billing export"**
   - Select **"BigQuery export"** tab

2. **Configure Standard Usage Cost Export**:
   - Click **"EDIT SETTINGS"** under "Standard usage cost data"
   - Select or create a BigQuery dataset:
     - **Project**: `${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}`
     - **Dataset name**: `billing_export` (or your choice)
     - **Location**: `US` (multi-region recommended)
   - Click **"SAVE"**

3. **Configure Detailed Usage Cost Export (Optional but Recommended)**:
   - Click **"EDIT SETTINGS"** under "Detailed usage cost data"
   - Same dataset as above
   - This provides more granular SKU-level data
   - Click **"SAVE"**

### 1.3 Create Dataset via CLI (Alternative)

If you have billing admin permissions:

```bash
# Create BigQuery dataset for billing export
bq mk --dataset \
  --location=US \
  --description="Google Cloud Billing Export Data" \
  ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}:billing_export

# Grant billing account access to the dataset
bq update --source billing_export \
  ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}:billing_export
```

---

## Step 2: Wait for Data Export

⚠️ **Important**: Billing data export is **not real-time**. Expect:

- **Initial data**: Available within 24 hours
- **Regular updates**: Multiple times per day (usually every few hours)
- **Finalization**: Costs may be adjusted up to 48 hours later
- **Partition date**: Data is organized by `_PARTITIONDATE`

---

## Step 3: Query Billing Data via Terminal

### 3.1 Find Your Table Name

```bash
# List all tables in the billing dataset
bq ls ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}:billing_export

# You should see something like:
# ${BIGQUERY_BILLING_EXPORT_TABLE}
# gcp_billing_export_resource_v1_01C3B6_61505E_CB6F45 (detailed, if enabled)
```

The table name will be: `${BIGQUERY_BILLING_EXPORT_TABLE}`

### 3.2 Basic Cost Queries

#### Total Cost for Today

```bash
bq query --use_legacy_sql=false \
"SELECT
   SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as total_cost
 FROM
   \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE
   _PARTITIONDATE = CURRENT_DATE()"
```

#### Gemini API Costs for Today

```bash
bq query --use_legacy_sql=false \
"SELECT
   service.description as service,
   SUM(cost) as total_cost,
   SUM(usage.amount) as total_usage,
   usage.unit as unit
 FROM
   \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE
   _PARTITIONDATE = CURRENT_DATE()
   AND service.description LIKE '%Generative%'
 GROUP BY
   service, unit"
```

#### Gemini Costs for Specific Date

```bash
bq query --use_legacy_sql=false \
"SELECT
   service.description,
   sku.description,
   SUM(cost) as cost_usd,
   SUM(usage.amount) as usage_amount,
   usage.unit
 FROM
   \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE
   _PARTITIONDATE = '2025-10-18'
   AND service.description = 'Generative Language API'
 GROUP BY
   service.description, sku.description, usage.unit
 ORDER BY
   cost_usd DESC"
```

#### Breakdown by SKU (Input vs Output Tokens)

```bash
bq query --use_legacy_sql=false \
"SELECT
   sku.description,
   SUM(cost) as cost_usd,
   SUM(usage.amount) as tokens,
   usage.unit,
   ROUND(SUM(cost) / NULLIF(SUM(usage.amount), 0) * 1000000, 4) as cost_per_million_tokens
 FROM
   \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE
   _PARTITIONDATE = '2025-10-18'
   AND service.description = 'Generative Language API'
 GROUP BY
   sku.description, usage.unit
 ORDER BY
   cost_usd DESC"
```

#### Date Range Query (Last 7 Days)

```bash
bq query --use_legacy_sql=false \
"SELECT
   DATE(_PARTITIONTIME) as date,
   service.description,
   SUM(cost) as daily_cost
 FROM
   \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE
   _PARTITIONDATE BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND CURRENT_DATE()
   AND service.description = 'Generative Language API'
 GROUP BY
   date, service.description
 ORDER BY
   date DESC"
```

---

## Step 4: Create Automated Cost Tracking Script

### 4.1 Python Script for Daily Cost Reports

Create: `/Users/ryanranft/nba-mcp-synthesis/scripts/check_gemini_costs.py`

```python
#!/usr/bin/env python3
"""
Check actual Gemini API costs from BigQuery billing export.
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta

# Configuration
PROJECT_ID = "${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}"
DATASET = "billing_export"
TABLE = "${BIGQUERY_BILLING_EXPORT_TABLE}"

def query_bigquery(sql):
    """Execute BigQuery query and return results as JSON."""
    cmd = [
        "bq", "query",
        "--use_legacy_sql=false",
        "--format=json",
        sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error querying BigQuery: {result.stderr}", file=sys.stderr)
        return None

    return json.loads(result.stdout) if result.stdout else []

def get_gemini_costs_today():
    """Get Gemini API costs for today."""
    sql = f"""
    SELECT
      service.description as service,
      sku.description as sku,
      SUM(cost) as cost_usd,
      SUM(usage.amount) as usage_amount,
      usage.unit as unit
    FROM
      `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE
      _PARTITIONDATE = CURRENT_DATE()
      AND service.description = 'Generative Language API'
    GROUP BY
      service, sku, unit
    ORDER BY
      cost_usd DESC
    """

    return query_bigquery(sql)

def get_gemini_costs_date_range(start_date, end_date):
    """Get Gemini API costs for a date range."""
    sql = f"""
    SELECT
      DATE(_PARTITIONTIME) as date,
      SUM(cost) as cost_usd,
      SUM(usage.amount) as total_tokens
    FROM
      `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE
      _PARTITIONDATE BETWEEN '{start_date}' AND '{end_date}'
      AND service.description = 'Generative Language API'
    GROUP BY
      date
    ORDER BY
      date DESC
    """

    return query_bigquery(sql)

def print_cost_report(results, title):
    """Print formatted cost report."""
    print("=" * 80)
    print(title)
    print("=" * 80)

    if not results:
        print("No data available yet. BigQuery export may not be set up or data is pending.")
        return

    total_cost = 0
    for row in results:
        cost = float(row.get('cost_usd', 0))
        total_cost += cost

        if 'sku' in row:
            print(f"\n{row['sku']}:")
            print(f"  Cost: ${cost:.4f}")
            print(f"  Usage: {row.get('usage_amount', 0):,.0f} {row.get('unit', 'units')}")
        elif 'date' in row:
            print(f"{row['date']}: ${cost:.2f} ({row.get('total_tokens', 0):,.0f} tokens)")

    print(f"\n{'='*80}")
    print(f"TOTAL: ${total_cost:.2f}")
    print(f"{'='*80}")

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Gemini API costs from BigQuery")
    parser.add_argument('--today', action='store_true', help="Show today's costs")
    parser.add_argument('--yesterday', action='store_true', help="Show yesterday's costs")
    parser.add_argument('--last-7-days', action='store_true', help="Show last 7 days")
    parser.add_argument('--date', type=str, help="Show costs for specific date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.today or not any([args.yesterday, args.last_7_days, args.date]):
        results = get_gemini_costs_today()
        print_cost_report(results, "Gemini API Costs - TODAY")

    if args.yesterday:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        results = get_gemini_costs_date_range(yesterday, yesterday)
        print_cost_report(results, f"Gemini API Costs - {yesterday}")

    if args.last_7_days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        results = get_gemini_costs_date_range(start_date, end_date)
        print_cost_report(results, f"Gemini API Costs - Last 7 Days ({start_date} to {end_date})")

    if args.date:
        results = get_gemini_costs_date_range(args.date, args.date)
        print_cost_report(results, f"Gemini API Costs - {args.date}")

if __name__ == "__main__":
    main()
```

Make it executable:

```bash
chmod +x /Users/ryanranft/nba-mcp-synthesis/scripts/check_gemini_costs.py
```

### 4.2 Usage Examples

```bash
# Check today's costs
python3 scripts/check_gemini_costs.py --today

# Check yesterday's costs
python3 scripts/check_gemini_costs.py --yesterday

# Check last 7 days
python3 scripts/check_gemini_costs.py --last-7-days

# Check specific date
python3 scripts/check_gemini_costs.py --date 2025-10-18
```

---

## Step 5: Integration with Book Analysis Workflow

### 5.1 Update Cost Tracking in Logs

Modify `/Users/ryanranft/nba-mcp-synthesis/scripts/high_context_book_analyzer.py` to log actual costs:

```python
# After analysis completes
try:
    from scripts.check_gemini_costs import get_gemini_costs_today
    actual_costs = get_gemini_costs_today()
    if actual_costs:
        logger.info(f"Actual Gemini costs today: ${sum(float(r['cost_usd']) for r in actual_costs):.2f}")
except Exception as e:
    logger.warning(f"Could not retrieve actual costs: {e}")
```

### 5.2 Add Cost Verification to Workflow

Update `/Users/ryanranft/nba-mcp-synthesis/scripts/run_full_workflow.py`:

```python
# At end of workflow
def verify_actual_costs():
    """Compare estimated vs actual costs."""
    logger.info("Verifying actual costs from BigQuery...")

    result = subprocess.run(
        ["python3", "scripts/check_gemini_costs.py", "--today"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        logger.info(f"Actual costs:\n{result.stdout}")
    else:
        logger.warning("Could not retrieve actual costs. BigQuery export may not be set up.")
```

---

## Step 6: Set Up Cost Alerts

### 6.1 Create Budget Alert via gcloud

```bash
# Create a budget for Gemini API usage
gcloud billing budgets create \
  --billing-account=${GOOGLE_CLOUD_BILLING_ACCOUNT_ID} \
  --display-name="Gemini API Monthly Budget" \
  --budget-amount=100 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### 6.2 Daily Cost Check Cron Job

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add daily cost check at 11 PM
0 23 * * * cd /Users/ryanranft/nba-mcp-synthesis && python3 scripts/check_gemini_costs.py --today >> logs/daily_costs.log 2>&1
```

---

## Troubleshooting

### Issue: "Table not found"

**Solution**: BigQuery export hasn't been configured yet. Follow Step 1.

### Issue: "Permission denied"

**Solution**: You need billing account admin or viewer permissions:

```bash
# Check current permissions
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}

# Request billing account access from project owner
```

### Issue: "No data available"

**Reasons**:
1. Export was just configured (wait 24 hours)
2. No usage occurred on the queried date
3. Wrong partition date format

### Issue: "Authentication failed"

**Solution**: Re-authenticate:

```bash
gcloud auth login
gcloud auth application-default login
```

---

## Expected Results

Once set up, you'll be able to:

✅ **Query exact Gemini costs** within hours of usage
✅ **Breakdown costs** by input/output tokens and pricing tier
✅ **Track daily/weekly/monthly** spending trends
✅ **Automate cost reports** in your workflows
✅ **Set up budget alerts** for cost overruns
✅ **Compare log estimates vs actual billing** (validate 3x overestimation factor)

---

## Quick Reference

### Essential Commands

```bash
# List datasets
bq ls ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}:

# List tables in billing dataset
bq ls ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}:billing_export

# Query today's Gemini costs
bq query --use_legacy_sql=false \
"SELECT SUM(cost) as total_cost
 FROM \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`
 WHERE _PARTITIONDATE = CURRENT_DATE()
   AND service.description = 'Generative Language API'"

# Check latest data available
bq query --use_legacy_sql=false \
"SELECT MAX(_PARTITIONDATE) as latest_date
 FROM \`${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}.billing_export.${BIGQUERY_BILLING_EXPORT_TABLE}\`"
```

---

## Resources

- **BigQuery Billing Export Docs**: https://cloud.google.com/billing/docs/how-to/export-data-bigquery
- **Understanding Billing Data Schema**: https://cloud.google.com/billing/docs/how-to/bq-examples
- **BigQuery Command Reference**: https://cloud.google.com/bigquery/docs/bq-command-line-tool
- **Your Billing Console**: https://console.cloud.google.com/billing/${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}

---

**Last Updated**: October 18, 2025
**Status**: Documentation ready, awaiting BigQuery export configuration
**Next Step**: Configure billing export in Google Cloud Console (Step 1.2)

