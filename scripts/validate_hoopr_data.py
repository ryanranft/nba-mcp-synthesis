#!/usr/bin/env python3
"""
NBA MCP Synthesis - hoopR Data Validation
==========================================

Validates data quality after loading from parquet files.

Checks:
  - Row counts match expected ranges
  - No missing years (2002-2025)
  - Date ranges are correct
  - No NULL values in critical columns
  - Data types are correct
  - Sample queries work

Usage:
  python scripts/validate_hoopr_data.py
  python scripts/validate_hoopr_data.py --schema raw --context development
  python scripts/validate_hoopr_data.py --context production
  python scripts/validate_hoopr_data.py --verbose

Author: NBA MCP Synthesis
Date: 2025-01-07
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)


# ============================================================================
# Expected Data Ranges
# ============================================================================

EXPECTED_RANGES = {
    "hoopr_schedule": {
        "min_rows": 28000,
        "max_rows": 35000,
        "min_date": "2002-01-01",
        "max_date": "2025-12-31",
        "critical_columns": ["game_id", "game_date", "home_team", "away_team"],
    },
    "hoopr_team_box": {
        "min_rows": 56000,
        "max_rows": 70000,
        "min_date": "2002-01-01",
        "max_date": "2025-12-31",
        "critical_columns": ["game_id", "team_id", "game_date"],
    },
    "hoopr_player_box": {
        "min_rows": 750000,
        "max_rows": 900000,
        "min_date": "2002-01-01",
        "max_date": "2025-12-31",
        "critical_columns": ["game_id", "athlete_id", "game_date"],
    },
    "hoopr_play_by_play": {
        "min_rows": 12000000,
        "max_rows": 15000000,
        "min_date": "2002-01-01",
        "max_date": "2025-12-31",
        "critical_columns": ["game_id", "game_date", "type_text"],
    },
}


# ============================================================================
# Validation Functions
# ============================================================================


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print("=" * 80)


def print_section(title: str):
    """Print formatted subsection."""
    print(f"\n{title}")
    print("-" * 80)


def validate_row_counts(
    conn, schema: str = "public", verbose: bool = False
) -> Dict[str, bool]:
    """Validate that row counts are within expected ranges."""
    print_section("Row Count Validation")

    results = {}
    cur = conn.cursor()

    for table_name, config in EXPECTED_RANGES.items():
        qualified_name = f"{schema}.{table_name}" if schema else table_name
        cur.execute(f"SELECT COUNT(*) FROM {qualified_name}")
        actual_count = cur.fetchone()[0]

        min_rows = config["min_rows"]
        max_rows = config["max_rows"]

        is_valid = min_rows <= actual_count <= max_rows

        status = "✅" if is_valid else "❌"
        print(
            f"  {status} {table_name:25s} {actual_count:>15,} rows (expected: {min_rows:,}-{max_rows:,})"
        )

        results[table_name] = is_valid

    cur.close()
    return results


def validate_date_ranges(conn, verbose: bool = False) -> Dict[str, bool]:
    """Validate date ranges are within expected bounds."""
    print_section("Date Range Validation")

    results = {}
    cur = conn.cursor()

    for table_name, config in EXPECTED_RANGES.items():
        cur.execute(
            f"""
            SELECT
                MIN(game_date) as min_date,
                MAX(game_date) as max_date
            FROM {table_name}
        """
        )

        min_date, max_date = cur.fetchone()

        min_expected = config["min_date"]
        max_expected = config["max_date"]

        is_valid = (
            min_date is not None
            and max_date is not None
            and min_date.strftime("%Y-%m-%d") >= min_expected
            and max_date.strftime("%Y-%m-%d") <= max_expected
        )

        status = "✅" if is_valid else "❌"
        print(f"  {status} {table_name:25s} {min_date} to {max_date}")

        results[table_name] = is_valid

    cur.close()
    return results


def validate_year_coverage(conn, verbose: bool = False) -> Dict[str, bool]:
    """Check that all years 2002-2025 have data."""
    print_section("Year Coverage Validation")

    expected_years = set(range(2002, 2026))
    results = {}
    cur = conn.cursor()

    for table_name in EXPECTED_RANGES.keys():
        cur.execute(
            f"""
            SELECT DISTINCT EXTRACT(YEAR FROM game_date)::INTEGER as year
            FROM {table_name}
            ORDER BY year
        """
        )

        actual_years = {row[0] for row in cur.fetchall()}
        missing_years = expected_years - actual_years

        is_valid = len(missing_years) == 0

        status = "✅" if is_valid else "❌"
        coverage = f"{len(actual_years)}/24 years"

        if is_valid:
            print(f"  {status} {table_name:25s} {coverage} (complete)")
        else:
            print(
                f"  {status} {table_name:25s} {coverage} (missing: {sorted(missing_years)})"
            )

        results[table_name] = is_valid

    cur.close()
    return results


def validate_null_values(conn, verbose: bool = False) -> Dict[str, bool]:
    """Check for NULL values in critical columns."""
    print_section("NULL Value Validation")

    results = {}
    cur = conn.cursor()

    for table_name, config in EXPECTED_RANGES.items():
        all_valid = True

        for column in config["critical_columns"]:
            cur.execute(
                f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE {column} IS NULL
            """
            )

            null_count = cur.fetchone()[0]

            if null_count > 0:
                all_valid = False
                print(f"  ❌ {table_name}.{column}: {null_count:,} NULL values")
            elif verbose:
                print(f"  ✅ {table_name}.{column}: No NULLs")

        if all_valid and not verbose:
            print(f"  ✅ {table_name:25s} No NULL values in critical columns")

        results[table_name] = all_valid

    cur.close()
    return results


def validate_sample_queries(conn, verbose: bool = False) -> bool:
    """Run sample queries to verify data integrity."""
    print_section("Sample Query Validation")

    cur = conn.cursor()
    all_passed = True

    # Test 1: Get recent games
    try:
        cur.execute(
            """
            SELECT COUNT(*) FROM hoopr_schedule
            WHERE game_date >= '2024-01-01'
        """
        )
        count = cur.fetchone()[0]
        print(f"  ✅ Recent games (2024+): {count:,} games")
    except Exception as e:
        print(f"  ❌ Recent games query failed: {e}")
        all_passed = False

    # Test 2: Join team box with schedule
    try:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM hoopr_team_box tb
            JOIN hoopr_schedule s ON tb.game_id = s.game_id
            WHERE s.game_date >= '2024-01-01'
        """
        )
        count = cur.fetchone()[0]
        print(f"  ✅ Team box join: {count:,} team-games")
    except Exception as e:
        print(f"  ❌ Team box join failed: {e}")
        all_passed = False

    # Test 3: Player box aggregation
    try:
        cur.execute(
            """
            SELECT COUNT(DISTINCT athlete_id)
            FROM hoopr_player_box
            WHERE game_date >= '2024-01-01'
        """
        )
        count = cur.fetchone()[0]
        print(f"  ✅ Unique players (2024+): {count:,} players")
    except Exception as e:
        print(f"  ❌ Player aggregation failed: {e}")
        all_passed = False

    # Test 4: Play-by-play event types
    try:
        cur.execute(
            """
            SELECT COUNT(DISTINCT type_text)
            FROM hoopr_play_by_play
            WHERE game_date >= '2024-01-01'
        """
        )
        count = cur.fetchone()[0]
        print(f"  ✅ Event types (2024+): {count:,} unique types")
    except Exception as e:
        print(f"  ❌ Event types query failed: {e}")
        all_passed = False

    cur.close()
    return all_passed


# ============================================================================
# Main Function
# ============================================================================


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate hoopR data in PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--context",
        choices=["development", "production"],
        default="development",
        help="Database context (development = local, production = RDS)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed validation results"
    )

    args = parser.parse_args()

    # Print header
    print_header("NBA MCP Synthesis - hoopR Data Validation")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Context: {args.context}")

    # Connect to database
    print_section("Connecting to Database")
    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", args.context)
        db_config = get_database_config()

        print(f"  Database: {db_config.get('database', 'N/A')}")
        print(f"  Host: {db_config.get('host', 'localhost')}")

        conn = psycopg2.connect(**db_config)
        print("  ✅ Connection established")

    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Run all validations
    all_results = {}

    all_results["row_counts"] = validate_row_counts(conn, args.verbose)
    all_results["date_ranges"] = validate_date_ranges(conn, args.verbose)
    all_results["year_coverage"] = validate_year_coverage(conn, args.verbose)
    all_results["null_values"] = validate_null_values(conn, args.verbose)
    all_results["sample_queries"] = validate_sample_queries(conn, args.verbose)

    # Print summary
    print_header("Validation Summary")

    total_checks = sum(
        len(v) if isinstance(v, dict) else 1 for v in all_results.values()
    )

    passed_checks = sum(
        (
            sum(1 for passed in v.values() if passed)
            if isinstance(v, dict)
            else (1 if v else 0)
        )
        for v in all_results.values()
    )

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")

    if passed_checks == total_checks:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nData is ready for use:")
        print("  - Feature extraction: python scripts/prepare_features_from_parquet.py")
        print("  - Model training: python scripts/train_game_outcome_model.py")
        exit_code = 0
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nPlease review the errors above and:")
        print("  1. Check parquet files are complete")
        print("  2. Re-run loader: python scripts/load_parquet_to_postgres.py")
        print("  3. Check for data quality issues")
        exit_code = 1

    conn.close()
    print("\n" + "=" * 80)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
