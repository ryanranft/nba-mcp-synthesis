#!/usr/bin/env python3
"""
NBA MCP Synthesis - Parquet to PostgreSQL Loader
================================================

Loads hoopR parquet data (2002-2025) into local PostgreSQL database.

Table Naming Convention:
  hoopr_{data_type}

  Where:
    - hoopr: Source (ESPN data via hoopR R package)
    - data_type: schedule, team_box, player_box, play_by_play

Data Sources:
  /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/
    ├── load_nba_schedule/parquet/  → hoopr_schedule
    ├── load_nba_team_box/parquet/  → hoopr_team_box
    ├── load_nba_player_box/parquet/ → hoopr_player_box
    └── load_nba_pbp/parquet/       → hoopr_play_by_play

Usage:
  python scripts/load_parquet_to_postgres.py              # Full reload
  python scripts/load_parquet_to_postgres.py --dry-run    # Preview only
  python scripts/load_parquet_to_postgres.py --years 2023-2025
  python scripts/load_parquet_to_postgres.py --table schedule
  python scripts/load_parquet_to_postgres.py --context development

Author: NBA MCP Synthesis
Date: 2025-01-07
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import time
from typing import List, Dict, Tuple, Optional
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)


# ============================================================================
# Configuration
# ============================================================================

PARQUET_BASE = Path("/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba")

DATASETS = {
    "schedule": {
        "parquet_dir": "load_nba_schedule/parquet",
        "table": "raw.schedule",
        "file_pattern": "nba_data_{year}.parquet",
        "batch_size": 5000,
        "description": "Game schedule and metadata",
    },
    "team_box": {
        "parquet_dir": "load_nba_team_box/parquet",
        "table": "raw.team_box",
        "file_pattern": "nba_data_{year}.parquet",
        "batch_size": 5000,
        "description": "Team box scores",
    },
    "player_box": {
        "parquet_dir": "load_nba_player_box/parquet",
        "table": "raw.player_box",
        "file_pattern": "nba_data_{year}.parquet",
        "batch_size": 5000,
        "description": "Player box scores",
    },
    "play_by_play": {
        "parquet_dir": "load_nba_pbp/parquet",
        "table": "raw.play_by_play",
        "file_pattern": "nba_data_{year}.parquet",
        "batch_size": 10000,
        "description": "Event-level play-by-play data",
    },
}


# ============================================================================
# Helper Functions
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


def get_parquet_files(dataset_name: str, years: List[int]) -> List[Tuple[int, Path]]:
    """
    Get list of parquet files for a dataset.

    Returns:
        List of (year, filepath) tuples
    """
    config = DATASETS[dataset_name]
    parquet_dir = PARQUET_BASE / config["parquet_dir"]

    files = []
    for year in sorted(years):
        filename = config["file_pattern"].format(year=year)
        filepath = parquet_dir / filename

        if filepath.exists():
            files.append((year, filepath))
        else:
            print(f"  ⚠️  Missing: {filepath}")

    return files


def estimate_row_counts(datasets: List[str], years: List[int]) -> Dict[str, int]:
    """
    Estimate total rows for each dataset.

    Returns:
        Dictionary mapping dataset_name -> row_count
    """
    estimates = {}

    for dataset_name in datasets:
        total_rows = 0
        files = get_parquet_files(dataset_name, years)

        for year, filepath in files:
            try:
                df = pd.read_parquet(filepath)
                total_rows += len(df)
            except Exception as e:
                print(f"  ⚠️  Error reading {filepath}: {e}")

        estimates[dataset_name] = total_rows

    return estimates


def load_dataset_to_postgres(
    dataset_name: str,
    years: List[int],
    conn,
    dry_run: bool = False,
    truncate: bool = True,
) -> int:
    """
    Load a single dataset from parquet files to PostgreSQL.

    Args:
        dataset_name: Name of dataset ('schedule', 'team_box', etc.)
        years: List of years to load
        conn: psycopg2 connection
        dry_run: If True, preview only (don't modify database)
        truncate: If True, TRUNCATE table before loading

    Returns:
        Total rows inserted
    """
    config = DATASETS[dataset_name]
    table_name = config["table"]
    batch_size = config["batch_size"]

    print_section(f"Phase: Loading {table_name}")
    print(f"Description: {config['description']}")
    print(f"Batch size: {batch_size:,} rows")

    # Get parquet files
    files = get_parquet_files(dataset_name, years)
    if not files:
        print(f"  ❌ No parquet files found for {dataset_name}")
        return 0

    print(f"Found {len(files)} parquet files for years {min(years)}-{max(years)}")

    if dry_run:
        print(f"  🔍 DRY RUN - Would load {len(files)} files into {table_name}")
        return 0

    # Truncate table if requested
    if truncate:
        cur = conn.cursor()
        print(f"  🗑️  Truncating {table_name}...")
        cur.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        conn.commit()
        cur.close()

    # Load year by year
    total_rows = 0

    for year, filepath in tqdm(files, desc=f"  📅 Loading {dataset_name}", unit="year"):
        try:
            # Read parquet file
            df = pd.read_parquet(filepath)
            year_rows = len(df)

            if year_rows == 0:
                print(f"    ⚠️  {year}: Empty file, skipping")
                continue

            # Prepare data for insertion
            columns = list(df.columns)
            placeholders = ",".join(["%s"] * len(columns))
            insert_query = f"""
                INSERT INTO {table_name} ({','.join(columns)})
                VALUES ({placeholders})
            """

            # Convert DataFrame to list of tuples
            data = [tuple(row) for row in df.values]

            # Insert in batches
            cur = conn.cursor()
            try:
                execute_batch(cur, insert_query, data, page_size=batch_size)
                conn.commit()
                total_rows += year_rows

                # Progress update
                tqdm.write(f"    ✅ {year}: {year_rows:,} rows ({total_rows:,} total)")

            except Exception as e:
                conn.rollback()
                print(f"    ❌ {year}: Error inserting data: {e}")
                raise
            finally:
                cur.close()

        except Exception as e:
            print(f"    ❌ {year}: Error loading {filepath}: {e}")
            raise

    print(f"  ✅ Complete: {total_rows:,} total rows")
    return total_rows


def validate_database_schema(conn) -> bool:
    """
    Validate that all required tables exist (including schema-qualified names).

    Returns:
        True if all tables exist
    """
    required_tables = [config["table"] for config in DATASETS.values()]

    cur = conn.cursor()

    # Check each schema.table separately
    missing_tables = []
    for table_name in required_tables:
        if "." in table_name:
            schema, table = table_name.split(".")
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            """,
                (schema, table),
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            """,
                (table_name,),
            )

        count = cur.fetchone()[0]
        if count == 0:
            missing_tables.append(table_name)

    cur.close()

    if missing_tables:
        print(f"  ❌ Missing tables: {', '.join(missing_tables)}")
        return False

    print(f"  ✅ All {len(required_tables)} required tables exist")
    return True


# ============================================================================
# Main Function
# ============================================================================


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load hoopR parquet data into PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full reload (all datasets, all years)
  python scripts/load_parquet_to_postgres.py

  # Dry run (preview without loading)
  python scripts/load_parquet_to_postgres.py --dry-run

  # Load specific years
  python scripts/load_parquet_to_postgres.py --years 2023-2025

  # Load single dataset
  python scripts/load_parquet_to_postgres.py --table schedule

  # Use development database
  python scripts/load_parquet_to_postgres.py --context development
        """,
    )

    parser.add_argument(
        "--years",
        type=str,
        default="2002-2025",
        help="Year range to load (e.g., 2023-2025)",
    )

    parser.add_argument(
        "--table",
        choices=["schedule", "team_box", "player_box", "play_by_play", "all"],
        default="all",
        help="Which dataset to load",
    )

    parser.add_argument(
        "--context",
        choices=["development", "production"],
        default="development",
        help="Database context (development = local, production = RDS)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without loading data"
    )

    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Do not truncate tables before loading (append mode)",
    )

    args = parser.parse_args()

    # Parse year range
    start_year, end_year = map(int, args.years.split("-"))
    years = list(range(start_year, end_year + 1))

    # Determine which datasets to load
    if args.table == "all":
        datasets_to_load = list(DATASETS.keys())
    else:
        datasets_to_load = [args.table]

    # Print header
    print_header("NBA MCP Synthesis - Parquet to PostgreSQL Loader")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Context: {args.context}")
    print(f"Source: {PARQUET_BASE}")
    print(f"Years: {start_year}-{end_year} ({len(years)} years)")
    print(f"Datasets: {', '.join(datasets_to_load)}")
    print(
        f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (will modify database)'}"
    )
    print(
        f"Truncate: {'No (append mode)' if args.no_truncate else 'Yes (will delete existing data)'}"
    )

    # Load secrets and connect to database
    print_section("Connecting to Database")
    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", args.context)
        db_config = get_database_config()

        print(f"  Database: {db_config.get('database', 'N/A')}")
        print(f"  Host: {db_config.get('host', 'localhost')}")
        print(f"  Port: {db_config.get('port', 5432)}")

        conn = psycopg2.connect(**db_config)
        print("  ✅ Connection established")

    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Validate schema
    print_section("Pre-flight Checks")
    if not validate_database_schema(conn):
        print("\n❌ Database schema validation failed")
        print("Please ensure all hoopr_* tables are created")
        conn.close()
        sys.exit(1)

    # Estimate row counts
    print_section("Estimating Data Size")
    estimates = estimate_row_counts(datasets_to_load, years)

    total_estimated = 0
    for dataset_name in datasets_to_load:
        count = estimates.get(dataset_name, 0)
        total_estimated += count
        table_name = DATASETS[dataset_name]["table"]
        print(f"  {table_name:25s} {count:>15,} rows")

    print(f"  {'─' * 25} {'─' * 15}")
    print(f"  {'TOTAL':25s} {total_estimated:>15,} rows")

    # Confirm before proceeding
    if not args.dry_run and not args.no_truncate:
        print(f"\n⚠️  This will TRUNCATE and reload {len(datasets_to_load)} table(s)")
        response = input("Continue? [y/N]: ")
        if response.lower() != "y":
            print("Aborted by user")
            conn.close()
            sys.exit(0)

    # Load datasets
    start_time = time.time()
    total_rows_loaded = 0
    results = {}

    try:
        for dataset_name in datasets_to_load:
            rows = load_dataset_to_postgres(
                dataset_name=dataset_name,
                years=years,
                conn=conn,
                dry_run=args.dry_run,
                truncate=not args.no_truncate,
            )
            results[dataset_name] = rows
            total_rows_loaded += rows

        elapsed_time = time.time() - start_time

        # Print summary
        print_header("✅ LOADING COMPLETE")

        print("Final Statistics:")
        for dataset_name, rows in results.items():
            table_name = DATASETS[dataset_name]["table"]
            print(f"  {table_name:25s} {rows:>15,} rows")

        print(f"  {'─' * 25} {'─' * 15}")
        print(f"  {'TOTAL':25s} {total_rows_loaded:>15,} rows")
        print(f"\n  Total Time: {elapsed_time / 60:.1f} minutes")

        if total_rows_loaded > 0 and elapsed_time > 0:
            print(f"  Avg Speed: {int(total_rows_loaded / elapsed_time):,} rows/second")

        if not args.dry_run:
            print("\n💡 Next Steps:")
            print("  1. Validate data: python scripts/validate_hoopr_data.py")
            print(
                "  2. Rebuild indexes: psql -c 'REINDEX DATABASE espn_nba_mcp_synthesis;'"
            )
            print("  3. Update statistics: psql -c 'VACUUM ANALYZE;'")

    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
