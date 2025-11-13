#!/usr/bin/env python3
"""
Copy ESPN data from localhost:5432/nba_simulator to nba_mcp_synthesis espn_raw schema.

This script copies all ESPN web-scraped data and master/curated data into a new
espn_raw schema with standardized naming convention.

Tables copied:
  espn.espn_games → espn_raw.schedule_espn_nba
  espn.espn_team_stats → espn_raw.team_box_espn_nba
  espn.espn_plays → espn_raw.play_by_play_espn_nba
  espn.espn_schedules → espn_raw.schedules_metadata_espn_nba
  master.nba_games → espn_raw.schedule_curated_espn_nba
  master.nba_plays → espn_raw.play_by_play_curated_espn_nba
  master.espn_file_validation → espn_raw.file_validation_espn_nba

Author: NBA MCP Synthesis
Date: 2025-11-08
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)


# Table mappings: (source_schema, source_table, target_table, batch_size)
TABLE_MAPPINGS = [
    ("espn", "espn_games", "schedule_espn_nba", 5000),
    ("espn", "espn_team_stats", "team_box_espn_nba", 10000),
    ("espn", "espn_plays", "play_by_play_espn_nba", 10000),
    ("espn", "espn_schedules", "schedules_metadata_espn_nba", 1000),
    ("master", "nba_games", "schedule_curated_espn_nba", 5000),
    ("master", "nba_plays", "play_by_play_curated_espn_nba", 10000),
    ("master", "espn_file_validation", "file_validation_espn_nba", 5000),
]


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print("=" * 80)


def print_section(title):
    """Print formatted subsection."""
    print(f"\n{title}")
    print("-" * 80)


def create_espn_raw_schema(target_conn):
    """Create espn_raw schema if it doesn't exist."""
    print_section("Creating espn_raw Schema")

    with target_conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS espn_raw;")
        target_conn.commit()
        print("  ✅ Schema 'espn_raw' created")


def get_table_ddl(source_conn, schema, table):
    """Get CREATE TABLE statement for existing table."""
    with source_conn.cursor() as cur:
        # Get column definitions
        cur.execute(
            f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position;
        """
        )

        columns = cur.fetchall()

        # Build CREATE TABLE statement
        create_sql = "CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (\n"
        col_defs = []

        for (
            col_name,
            data_type,
            char_len,
            is_nullable,
            col_default,
            udt_name,
        ) in columns:
            col_def = f"  {col_name}"

            # Handle data types
            if data_type in ("character varying", "varchar"):
                col_def += f" VARCHAR({char_len})" if char_len else " VARCHAR"
            elif data_type == "character":
                col_def += f" CHAR({char_len if char_len else 1})"
            elif data_type == "ARRAY":
                col_def += f" {udt_name}"
            elif data_type == "USER-DEFINED":
                col_def += f" {udt_name}"
            elif data_type == "timestamp without time zone":
                col_def += " TIMESTAMP"
            elif data_type == "timestamp with time zone":
                col_def += " TIMESTAMPTZ"
            else:
                col_def += f" {data_type.upper()}"

            # Add constraints
            if is_nullable == "NO":
                col_def += " NOT NULL"

            if col_default and "nextval" not in col_default:
                col_def += f" DEFAULT {col_default}"

            col_defs.append(col_def)

        create_sql += ",\n".join(col_defs)
        create_sql += "\n);"

        return create_sql


def copy_table_data(
    source_conn, target_conn, source_schema, source_table, target_table, batch_size
):
    """Copy all data from source table to target table."""
    print_section(f"Copying {source_schema}.{source_table} → espn_raw.{target_table}")

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    try:
        # Get row count
        source_cur.execute(f"SELECT COUNT(*) FROM {source_schema}.{source_table};")
        row_count = source_cur.fetchone()[0]
        print(f"  Total rows to copy: {row_count:,}")

        if row_count == 0:
            print(f"  ⚠️  No data to copy")
            return True

        # Create table with same schema
        print(f"  Creating table espn_raw.{target_table}...")
        create_sql = get_table_ddl(source_conn, source_schema, source_table)
        create_sql = create_sql.format(schema_name="espn_raw", table_name=target_table)
        target_cur.execute(create_sql)
        target_conn.commit()
        print(f"  ✅ Table created")

        # Get column names
        source_cur.execute(
            f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{source_schema}' AND table_name = '{source_table}'
            ORDER BY ordinal_position;
        """
        )
        columns = [row[0] for row in source_cur.fetchall()]
        col_list = ", ".join(columns)

        # Clear target table if it exists
        print(f"  Truncating target table...")
        target_cur.execute(
            f"TRUNCATE TABLE espn_raw.{target_table} RESTART IDENTITY CASCADE;"
        )
        target_conn.commit()

        # Copy data in batches
        print(f"  Copying {row_count:,} rows in batches of {batch_size:,}...")

        offset = 0
        total_inserted = 0
        start_time = datetime.now()

        while offset < row_count:
            # Fetch batch from source
            source_cur.execute(
                f"""
                SELECT {col_list}
                FROM {source_schema}.{source_table}
                ORDER BY ctid
                LIMIT {batch_size} OFFSET {offset};
            """
            )
            rows = source_cur.fetchall()

            if not rows:
                break

            # Insert batch into target
            placeholders = ",".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO espn_raw.{target_table} ({col_list}) VALUES ({placeholders})"

            execute_batch(target_cur, insert_sql, rows, page_size=1000)
            target_conn.commit()

            total_inserted += len(rows)
            offset += batch_size

            # Progress update
            progress = (total_inserted / row_count) * 100
            print(
                f"    Progress: {total_inserted:,}/{row_count:,} ({progress:.1f}%)",
                end="\r",
            )

        print()  # New line after progress

        elapsed = (datetime.now() - start_time).total_seconds()
        rows_per_sec = total_inserted / elapsed if elapsed > 0 else 0

        print(f"  ✅ Data copied in {elapsed:.1f}s ({rows_per_sec:,.0f} rows/sec)")

        # Verify
        target_cur.execute(f"SELECT COUNT(*) FROM espn_raw.{target_table};")
        target_count = target_cur.fetchone()[0]

        if target_count == row_count:
            print(f"  ✅ Verification passed: {target_count:,} rows")
            return True
        else:
            print(f"  ❌ Verification failed: {row_count:,} → {target_count:,}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        target_conn.rollback()
        return False
    finally:
        source_cur.close()
        target_cur.close()


def main():
    """Main copy function."""
    print_header("ESPN Data Copy to espn_raw Schema")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: localhost:5432/nba_simulator")
    print(f"Target: localhost:5432/nba_mcp_synthesis (espn_raw schema)")

    # Connect to source database (nba_simulator)
    print_section("Connecting to Source Database (nba_simulator)")
    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")
        source_config = get_database_config()
        source_config["database"] = "nba_simulator"

        print(f"  Database: {source_config['database']}")
        print(f"  Host: {source_config['host']}")

        source_conn = psycopg2.connect(**source_config)
        source_conn.autocommit = False
        print("  ✅ Connected to source")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Connect to target database (nba_mcp_synthesis)
    print_section("Connecting to Target Database (nba_mcp_synthesis)")
    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")
        target_config = get_database_config()

        print(f"  Database: {target_config['database']}")
        print(f"  Host: {target_config['host']}")

        target_conn = psycopg2.connect(**target_config)
        target_conn.autocommit = False
        print("  ✅ Connected to target")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        source_conn.close()
        sys.exit(1)

    # Create espn_raw schema
    create_espn_raw_schema(target_conn)

    # Copy each table
    print_header("Copying Tables")

    success_count = 0
    fail_count = 0

    for source_schema, source_table, target_table, batch_size in TABLE_MAPPINGS:
        success = copy_table_data(
            source_conn,
            target_conn,
            source_schema,
            source_table,
            target_table,
            batch_size,
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print_header("Copy Summary")
    print(f"  ✅ Successful: {success_count}/{len(TABLE_MAPPINGS)}")
    if fail_count > 0:
        print(f"  ❌ Failed: {fail_count}/{len(TABLE_MAPPINGS)}")

    # Final verification
    print_section("Final Verification")

    with target_conn.cursor() as cur:
        for _, _, target_table, _ in TABLE_MAPPINGS:
            cur.execute(f"SELECT COUNT(*) FROM espn_raw.{target_table};")
            count = cur.fetchone()[0]
            print(f"  espn_raw.{target_table:35s} {count:>12,} rows")

    # Close connections
    source_conn.close()
    target_conn.close()

    if fail_count == 0:
        print("\n✅ ESPN DATA COPY COMPLETE")
        print("\nNew espn_raw schema structure:")
        print("  espn_raw.schedule_espn_nba")
        print("  espn_raw.team_box_espn_nba")
        print("  espn_raw.play_by_play_espn_nba")
        print("  espn_raw.schedules_metadata_espn_nba")
        print("  espn_raw.schedule_curated_espn_nba")
        print("  espn_raw.play_by_play_curated_espn_nba")
        print("  espn_raw.file_validation_espn_nba")
        exit_code = 0
    else:
        print("\n❌ ESPN DATA COPY FAILED")
        print("\nPlease review errors above")
        exit_code = 1

    print("\n" + "=" * 80)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
