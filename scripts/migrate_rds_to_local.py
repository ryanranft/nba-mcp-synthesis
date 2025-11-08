#!/usr/bin/env python3
"""
Migrate RDS (nba_simulator) data to local PostgreSQL (nba_mcp_synthesis).

This script migrates all tables that exist in RDS but not in the local database,
with special handling for large tables (>1M rows) using batch processing.
"""

import psycopg2
from psycopg2.extras import execute_batch
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
import sys
from datetime import datetime

# Define tables to migrate (schema, table, priority, batch_size)
# Priority: 1=critical, 2=important, 3=nice-to-have
TABLES_TO_MIGRATE = [
    # Critical tables - temporal and state data
    ('public', 'temporal_events', 1, 10000),  # 14M rows - large batches
    ('public', 'game_state_snapshots', 1, 5000),
    ('public', 'lineup_snapshots', 1, 5000),
    ('public', 'player_plus_minus_snapshots', 1, 5000),

    # Important - NBA API data
    ('public', 'nba_api_comprehensive', 2, 5000),
    ('public', 'nba_api_player_dashboards', 2, 5000),
    ('public', 'nba_api_team_dashboards', 2, 1000),
    ('public', 'nba_api_player_tracking', 2, 1000),
    ('public', 'nba_api_game_advanced', 2, 1000),

    # Important - box score data
    ('public', 'box_score_players', 2, 5000),
    ('public', 'box_score_teams', 2, 5000),
    ('public', 'box_score_snapshots', 2, 1000),

    # Important - game data
    ('public', 'games', 2, 5000),
    ('public', 'play_by_play', 2, 10000),  # 6.7M rows

    # Important - metadata
    ('public', 'player_biographical', 2, 1000),
    ('public', 'teams', 2, 100),
    ('public', 'team_seasons', 2, 1000),
    ('public', 'possession_metadata', 2, 100),
    ('public', 'player_snapshot_stats', 2, 5000),

    # Nice-to-have - system/audit tables
    ('public', 'ddl_audit_log', 3, 100),
    ('public', 'ddl_schema_version', 3, 10),
    ('public', 'dims_config', 3, 10),
    ('public', 'dims_metrics_history', 3, 1000),
    ('public', 'dims_verification_runs', 3, 1000),

    # Raw data (small)
    ('raw_data', 'nba_games', 3, 1000),
    ('raw_data', 'schema_version', 3, 10),
]


def create_schema_if_not_exists(conn, schema):
    """Create schema if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    conn.commit()


def get_table_schema(rds_cur, schema, table):
    """Get CREATE TABLE statement for a table."""
    # Get column definitions
    rds_cur.execute(f"""
        SELECT column_name, data_type, character_maximum_length,
               is_nullable, column_default, udt_name
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table}'
        ORDER BY ordinal_position;
    """)
    columns = rds_cur.fetchall()

    # Build CREATE TABLE statement
    create_sql = f"CREATE TABLE IF NOT EXISTS {schema}.{table} (\n"
    col_defs = []

    for col_name, data_type, char_len, is_nullable, col_default, udt_name in columns:
        # Handle different data types
        if data_type == 'ARRAY':
            col_def = f"  {col_name} {udt_name}"
        elif data_type == 'USER-DEFINED':
            col_def = f"  {col_name} {udt_name}"
        elif data_type in ('character varying', 'varchar'):
            if char_len:
                col_def = f"  {col_name} VARCHAR({char_len})"
            else:
                col_def = f"  {col_name} VARCHAR"
        elif data_type == 'character':
            col_def = f"  {col_name} CHAR({char_len if char_len else 1})"
        else:
            col_def = f"  {col_name} {data_type}"

        if is_nullable == 'NO':
            col_def += " NOT NULL"

        # Handle defaults (skip sequences)
        if col_default and 'nextval' not in col_default:
            col_def += f" DEFAULT {col_default}"

        col_defs.append(col_def)

    create_sql += ",\n".join(col_defs)
    create_sql += "\n);"

    return create_sql


def migrate_table(rds_conn, local_conn, schema, table, batch_size):
    """Migrate a single table from RDS to local."""
    rds_cur = rds_conn.cursor()
    local_cur = local_conn.cursor()

    try:
        # Check if table exists in RDS
        rds_cur.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = '{schema}' AND table_name = '{table}';
        """)
        if rds_cur.fetchone()[0] == 0:
            print(f"  ⚠️  Table {schema}.{table} does not exist in RDS")
            return False

        # Count rows in RDS
        rds_cur.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
        rds_count = rds_cur.fetchone()[0]

        if rds_count == 0:
            print(f"  ⚠️  No data in {schema}.{table}")
            return True

        print(f"  Found {rds_count:,} rows in RDS")

        # Check if table exists in local
        local_cur.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = '{schema}' AND table_name = '{table}';
        """)

        if local_cur.fetchone()[0] == 0:
            # Create table
            print(f"  Creating table {schema}.{table}...")
            create_sql = get_table_schema(rds_cur, schema, table)
            local_cur.execute(create_sql)
            local_conn.commit()

        # Get column names
        rds_cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in rds_cur.fetchall()]
        col_list = ', '.join(columns)

        # Clear local table
        print(f"  Truncating local table...")
        local_cur.execute(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE;")
        local_conn.commit()

        # Fetch and insert data in batches
        print(f"  Migrating {rds_count:,} rows in batches of {batch_size:,}...")

        offset = 0
        total_inserted = 0

        while offset < rds_count:
            # Fetch batch from RDS
            rds_cur.execute(f"""
                SELECT {col_list}
                FROM {schema}.{table}
                ORDER BY ctid
                LIMIT {batch_size} OFFSET {offset};
            """)
            rows = rds_cur.fetchall()

            if not rows:
                break

            # Insert batch into local
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {schema}.{table} ({col_list}) VALUES ({placeholders})"

            execute_batch(local_cur, insert_sql, rows, page_size=1000)
            local_conn.commit()

            total_inserted += len(rows)
            offset += batch_size

            # Progress update
            progress = (total_inserted / rds_count) * 100
            print(f"    Progress: {total_inserted:,}/{rds_count:,} ({progress:.1f}%)", end='\r')

        print()  # New line after progress

        # Verify
        local_cur.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
        local_count = local_cur.fetchone()[0]

        if local_count == rds_count:
            print(f"  ✅ Successfully migrated {local_count:,} rows")
            return True
        else:
            print(f"  ⚠️  Row count mismatch! RDS: {rds_count:,}, Local: {local_count:,}")
            return False

    except Exception as e:
        print(f"  ❌ Error migrating {schema}.{table}: {e}")
        local_conn.rollback()
        return False
    finally:
        rds_cur.close()
        local_cur.close()


def main():
    """Main migration function."""
    print("=" * 80)
    print("RDS TO LOCAL DATABASE MIGRATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to RDS
    print("[1/3] Connecting to RDS (nba_simulator)...")
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
    rds_config = get_database_config()
    rds_conn = psycopg2.connect(**rds_config)
    rds_conn.autocommit = False
    print("  ✅ Connected to RDS")

    # Connect to Local
    print("[2/3] Connecting to local database (nba_mcp_synthesis)...")
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'development')
    local_config = get_database_config()
    local_conn = psycopg2.connect(**local_config)
    local_conn.autocommit = False
    print("  ✅ Connected to local database")
    print()

    # Create schemas
    print("[3/3] Ensuring schemas exist...")
    schemas = set([schema for schema, _, _, _ in TABLES_TO_MIGRATE])
    for schema in schemas:
        create_schema_if_not_exists(local_conn, schema)
        print(f"  ✅ Schema '{schema}' ready")
    print()

    # Migrate tables by priority
    print("=" * 80)
    print("MIGRATING TABLES")
    print("=" * 80)
    print()

    # Filter tables to migrate (priority 1 and 2 by default)
    # Change this to [1, 2, 3] to include all tables
    priorities_to_migrate = [1, 2]

    tables_to_process = [
        (schema, table, priority, batch_size)
        for schema, table, priority, batch_size in TABLES_TO_MIGRATE
        if priority in priorities_to_migrate
    ]

    print(f"Migrating {len(tables_to_process)} tables (priorities: {priorities_to_migrate})")
    print()

    success_count = 0
    failure_count = 0

    for schema, table, priority, batch_size in tables_to_process:
        print(f"[Priority {priority}] Migrating {schema}.{table}...")
        success = migrate_table(rds_conn, local_conn, schema, table, batch_size)

        if success:
            success_count += 1
        else:
            failure_count += 1
        print()

    # Close connections
    rds_conn.close()
    local_conn.close()

    # Summary
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ✅ Successful: {success_count}")
    if failure_count > 0:
        print(f"  ❌ Failed: {failure_count}")
    print("=" * 80)

    return 0 if failure_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
