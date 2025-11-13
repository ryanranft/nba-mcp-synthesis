#!/usr/bin/env python3
"""
Reorganize hoopR data: raw schema → hoopr_raw schema with standardized names

This script reorganizes the hoopR NBA data from the generic 'raw' schema
to a properly namespaced 'hoopr_raw' schema with standardized table names.

Transformations:
  raw.schedule         → hoopr_raw.nba_schedule
  raw.team_box         → hoopr_raw.nba_team_box
  raw.player_box       → hoopr_raw.nba_player_box
  raw.play_by_play     → hoopr_raw.nba_play_by_play

Total rows to migrate: ~13.9 million

Author: NBA MCP Synthesis
Date: 2025-01-08
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)


# Table mapping: old_name → new_name
TABLE_MAPPINGS = {
    "schedule": "nba_schedule",
    "team_box": "nba_team_box",
    "player_box": "nba_player_box",
    "play_by_play": "nba_play_by_play",
}


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print("=" * 80)


def print_section(title):
    """Print formatted subsection."""
    print(f"\n{title}")
    print("-" * 80)


def create_hoopr_raw_schema(conn):
    """Create hoopr_raw schema if it doesn't exist."""
    print_section("Creating hoopr_raw Schema")

    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS hoopr_raw;")
        conn.commit()
        print("  ✅ Schema 'hoopr_raw' created")


def get_table_ddl(conn, schema, table):
    """Get CREATE TABLE statement for existing table."""
    with conn.cursor() as cur:
        # Get column definitions
        cur.execute(
            f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position;
        """
        )

        columns = cur.fetchall()

        # Build CREATE TABLE statement
        create_sql = f"CREATE TABLE IF NOT EXISTS {{schema}}.{{table}} (\n"
        col_defs = []

        for col_name, data_type, char_len, is_nullable, col_default in columns:
            col_def = f"  {col_name}"

            # Handle data type
            if data_type in ("character varying", "varchar"):
                col_def += f" VARCHAR({char_len})" if char_len else " VARCHAR"
            elif data_type == "character":
                col_def += f" CHAR({char_len if char_len else 1})"
            elif data_type == "ARRAY":
                # Get actual array type
                cur.execute(
                    f"""
                    SELECT udt_name FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                    AND table_name = '{table}'
                    AND column_name = '{col_name}';
                """
                )
                udt_name = cur.fetchone()[0]
                col_def += f" {udt_name}"
            elif data_type == "USER-DEFINED":
                # Get actual type name
                cur.execute(
                    f"""
                    SELECT udt_name FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                    AND table_name = '{table}'
                    AND column_name = '{col_name}';
                """
                )
                udt_name = cur.fetchone()[0]
                col_def += f" {udt_name}"
            else:
                col_def += f" {data_type}"

            # Add constraints
            if is_nullable == "NO":
                col_def += " NOT NULL"

            if col_default and "nextval" not in col_default:
                col_def += f" DEFAULT {col_default}"

            col_defs.append(col_def)

        create_sql += ",\n".join(col_defs)
        create_sql += "\n);"

        return create_sql


def get_indexes(conn, schema, table):
    """Get all indexes for a table."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = '{schema}' AND tablename = '{table}'
            ORDER BY indexname;
        """
        )

        return cur.fetchall()


def copy_table_data(conn, old_schema, old_table, new_schema, new_table):
    """Copy all data from old table to new table."""
    print_section(f"Copying {old_schema}.{old_table} → {new_schema}.{new_table}")

    with conn.cursor() as cur:
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {old_schema}.{old_table};")
        row_count = cur.fetchone()[0]
        print(f"  Total rows to copy: {row_count:,}")

        # Create table with same schema
        print(f"  Creating table {new_schema}.{new_table}...")
        create_sql = get_table_ddl(conn, old_schema, old_table)
        create_sql = create_sql.format(schema=new_schema, table=new_table)
        cur.execute(create_sql)
        conn.commit()
        print(f"  ✅ Table created")

        # Copy data
        print(f"  Copying {row_count:,} rows...")
        start_time = datetime.now()

        cur.execute(
            f"""
            INSERT INTO {new_schema}.{new_table}
            SELECT * FROM {old_schema}.{old_table};
        """
        )
        conn.commit()

        elapsed = (datetime.now() - start_time).total_seconds()
        rows_per_sec = row_count / elapsed if elapsed > 0 else 0

        print(f"  ✅ Data copied in {elapsed:.1f}s ({rows_per_sec:,.0f} rows/sec)")

        # Verify row count
        cur.execute(f"SELECT COUNT(*) FROM {new_schema}.{new_table};")
        new_count = cur.fetchone()[0]

        if new_count == row_count:
            print(f"  ✅ Verification passed: {new_count:,} rows")
            return True
        else:
            print(f"  ❌ Verification failed: {row_count:,} → {new_count:,}")
            return False


def copy_indexes(conn, old_schema, old_table, new_schema, new_table):
    """Copy indexes from old table to new table."""
    print(f"  Creating indexes on {new_schema}.{new_table}...")

    indexes = get_indexes(conn, old_schema, old_table)

    if not indexes:
        print(f"  ⚠️  No indexes found on {old_schema}.{old_table}")
        return

    with conn.cursor() as cur:
        for idx_name, idx_def in indexes:
            # Modify index definition for new schema/table
            new_idx_name = idx_name.replace(old_table, new_table)
            new_idx_def = idx_def.replace(
                f"{old_schema}.{old_table}", f"{new_schema}.{new_table}"
            )
            new_idx_def = new_idx_def.replace(idx_name, new_idx_name)

            try:
                cur.execute(new_idx_def)
                conn.commit()
                print(f"    ✅ {new_idx_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"    ⚠️  {new_idx_name} (already exists)")
                else:
                    print(f"    ❌ {new_idx_name}: {e}")


def main():
    """Main reorganization function."""
    print_header("hoopR Schema Reorganization")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: raw.* → Target: hoopr_raw.nba_*")

    # Connect to local database
    print_section("Connecting to Database")
    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")
        db_config = get_database_config()

        print(f"  Database: {db_config.get('database', 'N/A')}")
        print(f"  Host: {db_config.get('host', 'localhost')}")

        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        print("  ✅ Connection established")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Create hoopr_raw schema
    create_hoopr_raw_schema(conn)

    # Copy each table
    print_header("Copying Tables")

    success_count = 0
    fail_count = 0

    for old_table, new_table in TABLE_MAPPINGS.items():
        success = copy_table_data(conn, "raw", old_table, "hoopr_raw", new_table)

        if success:
            copy_indexes(conn, "raw", old_table, "hoopr_raw", new_table)
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print_header("Reorganization Summary")
    print(f"  ✅ Successful: {success_count}/{len(TABLE_MAPPINGS)}")
    if fail_count > 0:
        print(f"  ❌ Failed: {fail_count}/{len(TABLE_MAPPINGS)}")

    # Final verification
    print_section("Final Verification")

    with conn.cursor() as cur:
        for new_table in TABLE_MAPPINGS.values():
            cur.execute(f"SELECT COUNT(*) FROM hoopr_raw.{new_table};")
            count = cur.fetchone()[0]
            print(f"  hoopr_raw.{new_table:25s} {count:>12,} rows")

    if fail_count == 0:
        print("\n✅ REORGANIZATION COMPLETE")
        print("\nNew schema structure:")
        print("  hoopr_raw.nba_schedule")
        print("  hoopr_raw.nba_team_box")
        print("  hoopr_raw.nba_player_box")
        print("  hoopr_raw.nba_play_by_play")
        print("\nOld 'raw' schema tables can now be dropped if desired.")
        exit_code = 0
    else:
        print("\n❌ REORGANIZATION FAILED")
        print("\nPlease review errors above")
        exit_code = 1

    conn.close()
    print("\n" + "=" * 80)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
