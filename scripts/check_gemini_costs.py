#!/usr/bin/env python3
"""
Check actual Gemini API costs from BigQuery billing export.

Usage:
    python3 scripts/check_gemini_costs.py --today
    python3 scripts/check_gemini_costs.py --yesterday
    python3 scripts/check_gemini_costs.py --last-7-days
    python3 scripts/check_gemini_costs.py --date 2025-10-18
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Configuration
PROJECT_ID = "${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}"
DATASET = "billing_export"
TABLE = "${BIGQUERY_BILLING_EXPORT_TABLE}"


def query_bigquery(sql: str) -> Optional[List[Dict]]:
    """
    Execute BigQuery query and return results as JSON.

    Args:
        sql: SQL query string

    Returns:
        List of result rows as dictionaries, or None if error
    """
    cmd = [
        "bq", "query",
        "--use_legacy_sql=false",
        "--format=json",
        sql
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"Error querying BigQuery: {result.stderr}", file=sys.stderr)
            return None

        return json.loads(result.stdout) if result.stdout else []
    except Exception as e:
        print(f"Exception querying BigQuery: {e}", file=sys.stderr)
        return None


def get_gemini_costs_today() -> Optional[List[Dict]]:
    """
    Get Gemini API costs for today.

    Returns:
        List of cost records by SKU
    """
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


def get_gemini_costs_date_range(start_date: str, end_date: str) -> Optional[List[Dict]]:
    """
    Get Gemini API costs for a date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of cost records by date
    """
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


def get_gemini_costs_detailed(date: str) -> Optional[List[Dict]]:
    """
    Get detailed Gemini API costs for a specific date with SKU breakdown.

    Args:
        date: Date (YYYY-MM-DD)

    Returns:
        List of cost records with SKU details
    """
    sql = f"""
    SELECT
      service.description as service,
      sku.description as sku,
      SUM(cost) as cost_usd,
      SUM(usage.amount) as usage_amount,
      usage.unit as unit,
      ROUND(SUM(cost) / NULLIF(SUM(usage.amount), 0) * 1000000, 4) as cost_per_million_units
    FROM
      `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE
      _PARTITIONDATE = '{date}'
      AND service.description = 'Generative Language API'
    GROUP BY
      service, sku, unit
    ORDER BY
      cost_usd DESC
    """

    return query_bigquery(sql)


def print_cost_report(results: Optional[List[Dict]], title: str):
    """
    Print formatted cost report.

    Args:
        results: Query results
        title: Report title
    """
    print("=" * 80)
    print(title)
    print("=" * 80)

    if results is None:
        print("\n⚠️  Could not query BigQuery. Possible reasons:")
        print("   1. BigQuery billing export is not configured")
        print("   2. 'bq' command is not installed or not in PATH")
        print("   3. Authentication issue (run: gcloud auth login)")
        print("\nSee: docs/BIGQUERY_BILLING_SETUP.md for setup instructions")
        return

    if not results:
        print("\nℹ️  No data available. Possible reasons:")
        print("   1. BigQuery export was just configured (wait 24 hours)")
        print("   2. No usage occurred on the queried date")
        print("   3. Data is still being processed")
        return

    total_cost = 0
    for row in results:
        cost = float(row.get('cost_usd', 0))
        total_cost += cost

        if 'sku' in row:
            # Detailed report with SKU breakdown
            print(f"\n{row['sku']}:")
            print(f"  Cost: ${cost:.4f}")
            print(f"  Usage: {row.get('usage_amount', 0):,.0f} {row.get('unit', 'units')}")

            if 'cost_per_million_units' in row:
                cpm = float(row.get('cost_per_million_units', 0))
                print(f"  Rate: ${cpm:.4f} per million {row.get('unit', 'units')}")

        elif 'date' in row:
            # Date range report
            tokens = row.get('total_tokens', 0)
            print(f"{row['date']}: ${cost:.2f} ({tokens:,.0f} tokens)")

    print(f"\n{'='*80}")
    print(f"TOTAL: ${total_cost:.2f}")
    print(f"{'='*80}")


def check_bigquery_setup() -> bool:
    """
    Check if BigQuery billing export is set up.

    Returns:
        True if setup is verified, False otherwise
    """
    # Check if bq command is available
    result = subprocess.run(
        ["which", "bq"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ 'bq' command not found. Install with: brew install google-cloud-sdk")
        return False

    # Check if dataset exists
    result = subprocess.run(
        ["bq", "ls", f"{PROJECT_ID}:{DATASET}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Dataset {PROJECT_ID}:{DATASET} not found or not accessible")
        print("   Set up BigQuery billing export: docs/BIGQUERY_BILLING_SETUP.md")
        return False

    print(f"✅ BigQuery billing export is configured")
    return True


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check Gemini API costs from BigQuery billing export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --today                    # Show today's costs
  %(prog)s --yesterday                # Show yesterday's costs
  %(prog)s --last-7-days              # Show last 7 days
  %(prog)s --date 2025-10-18          # Show specific date
  %(prog)s --date 2025-10-18 --detailed  # Detailed breakdown

For setup instructions, see: docs/BIGQUERY_BILLING_SETUP.md
        """
    )

    parser.add_argument('--today', action='store_true', help="Show today's costs")
    parser.add_argument('--yesterday', action='store_true', help="Show yesterday's costs")
    parser.add_argument('--last-7-days', action='store_true', help="Show last 7 days")
    parser.add_argument('--date', type=str, help="Show costs for specific date (YYYY-MM-DD)")
    parser.add_argument('--detailed', action='store_true', help="Show detailed SKU breakdown")
    parser.add_argument('--check-setup', action='store_true', help="Verify BigQuery setup")

    args = parser.parse_args()

    # Check setup if requested
    if args.check_setup:
        if check_bigquery_setup():
            print("\n✅ BigQuery billing export is ready to use")
            sys.exit(0)
        else:
            print("\n❌ BigQuery billing export needs configuration")
            print("   See: docs/BIGQUERY_BILLING_SETUP.md")
            sys.exit(1)

    # Default to today if no options specified
    if not any([args.yesterday, args.last_7_days, args.date]):
        args.today = True

    # Execute queries based on arguments
    if args.today:
        if args.detailed:
            today = datetime.now().strftime('%Y-%m-%d')
            results = get_gemini_costs_detailed(today)
            print_cost_report(results, f"Gemini API Costs - TODAY ({today}) - DETAILED")
        else:
            results = get_gemini_costs_today()
            print_cost_report(results, "Gemini API Costs - TODAY")

    if args.yesterday:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        if args.detailed:
            results = get_gemini_costs_detailed(yesterday)
            print_cost_report(results, f"Gemini API Costs - {yesterday} - DETAILED")
        else:
            results = get_gemini_costs_date_range(yesterday, yesterday)
            print_cost_report(results, f"Gemini API Costs - {yesterday}")

    if args.last_7_days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        results = get_gemini_costs_date_range(start_date, end_date)
        print_cost_report(results, f"Gemini API Costs - Last 7 Days ({start_date} to {end_date})")

    if args.date:
        if args.detailed:
            results = get_gemini_costs_detailed(args.date)
            print_cost_report(results, f"Gemini API Costs - {args.date} - DETAILED")
        else:
            results = get_gemini_costs_date_range(args.date, args.date)
            print_cost_report(results, f"Gemini API Costs - {args.date}")


if __name__ == "__main__":
    main()

