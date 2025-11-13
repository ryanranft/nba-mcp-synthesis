#!/usr/bin/env python3
"""
NBA MCP Synthesis - Local Database Initialization Script

Validates and initializes the local PostgreSQL database for development.

Usage:
    python scripts/init_local_database.py --validate    # Check database status
    python scripts/init_local_database.py --reset       # Drop and recreate all tables
    python scripts/init_local_database.py --stats       # Show table statistics

Author: NBA MCP Synthesis Team
Date: 2025-01-07
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


# Expected tables in the database
EXPECTED_TABLES = [
    "games",
    "hoopr_play_by_play",
    "hoopr_player_box",
    "hoopr_team_box",
    "computed_player_box",
    "computed_team_box",
    "arbitrage_opportunities",
    "betting_recommendations",
]


def load_credentials(context: str = "development") -> Dict[str, str]:
    """Load database credentials from hierarchical secrets system."""
    print(f"🔐 Loading {context} credentials from hierarchical secrets...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", context)
    config = get_database_config()

    if not all(
        [
            config["host"],
            config["port"],
            config["database"],
            config["user"],
            config["password"],
        ]
    ):
        print("❌ Missing required database credentials")
        sys.exit(1)

    print(
        f"✅ Credentials loaded: {config['user']}@{config['host']}:{config['port']}/{config['database']}"
    )
    return config


def connect_to_database(config: Dict[str, str]) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database."""
    print(f"\n🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=int(config["port"]),
            database=config["database"],
            user=config["user"],
            password=config["password"],
        )
        print(f"✅ Connected to {config['database']} at {config['host']}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Failed to connect to database: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure PostgreSQL is running: docker-compose up -d postgres")
        print("   2. Check port 5432 is available: lsof -i :5432")
        print("   3. Verify credentials in development secrets")
        sys.exit(1)


def check_tables_exist(
    conn: psycopg2.extensions.connection,
) -> Tuple[List[str], List[str]]:
    """Check which expected tables exist in the database."""
    print("\n📋 Checking table existence...")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    )

    existing_tables = [row[0] for row in cursor.fetchall()]
    missing_tables = [
        table for table in EXPECTED_TABLES if table not in existing_tables
    ]

    for table in EXPECTED_TABLES:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} (MISSING)")

    cursor.close()
    return existing_tables, missing_tables


def get_table_statistics(
    conn: psycopg2.extensions.connection, tables: List[str]
) -> None:
    """Get row counts and size for each table."""
    print("\n📊 Table Statistics:")
    cursor = conn.cursor()

    total_rows = 0
    for table in sorted(tables):
        try:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_rows += count

            # Get table size
            cursor.execute(
                f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}'))
            """
            )
            size = cursor.fetchone()[0]

            print(f"   {table:30} {count:>15,} rows    {size:>10}")
        except Exception as e:
            print(f"   {table:30} ERROR: {e}")

    print(f"   {'─' * 60}")
    print(f"   {'TOTAL':30} {total_rows:>15,} rows")
    cursor.close()


def check_database_health(conn: psycopg2.extensions.connection) -> None:
    """Run health checks on the database."""
    print("\n🏥 Database Health Checks:")
    cursor = conn.cursor()

    # Check PostgreSQL version
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"   PostgreSQL Version: {version.split(',')[0]}")

    # Check database size
    cursor.execute(
        """
        SELECT pg_size_pretty(pg_database_size(current_database()))
    """
    )
    db_size = cursor.fetchone()[0]
    print(f"   Database Size: {db_size}")

    # Check active connections
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM pg_stat_activity
        WHERE datname = current_database()
    """
    )
    active_connections = cursor.fetchone()[0]
    print(f"   Active Connections: {active_connections}")

    cursor.close()


def reset_database(conn: psycopg2.extensions.connection, sql_dir: str) -> None:
    """Drop and recreate all tables using SQL init scripts."""
    print("\n⚠️  RESETTING DATABASE - This will DELETE ALL DATA!")

    confirm = input("Type 'YES' to confirm: ")
    if confirm != "YES":
        print("❌ Reset cancelled")
        return

    print("\n🗑️  Dropping existing tables...")
    cursor = conn.cursor()

    # Drop all tables in reverse order to handle foreign keys
    for table in reversed(EXPECTED_TABLES):
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"   ✅ Dropped {table}")
        except Exception as e:
            print(f"   ⚠️  Error dropping {table}: {e}")

    conn.commit()
    print("\n✅ All tables dropped")

    # Re-run SQL init scripts
    print("\n📜 Running SQL initialization scripts...")
    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    for sql_file in sql_files:
        file_path = os.path.join(sql_dir, sql_file)
        print(f"   Running {sql_file}...")

        try:
            with open(file_path, "r") as f:
                sql = f.read()
                cursor.execute(sql)
                conn.commit()
                print(f"   ✅ {sql_file} completed")
        except Exception as e:
            print(f"   ❌ Error in {sql_file}: {e}")
            conn.rollback()

    cursor.close()
    print("\n✅ Database reset complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize and validate local NBA MCP database"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate database tables exist"
    )
    parser.add_argument("--stats", action="store_true", help="Show table statistics")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (WARNING: deletes all data)",
    )
    parser.add_argument(
        "--context",
        default="development",
        choices=["development", "production"],
        help="Database context (default: development)",
    )

    args = parser.parse_args()

    # Default to validate if no action specified
    if not any([args.validate, args.stats, args.reset]):
        args.validate = True
        args.stats = True

    print("=" * 70)
    print("NBA MCP Synthesis - Local Database Initialization")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Context: {args.context}")

    # Load credentials and connect
    config = load_credentials(args.context)
    conn = connect_to_database(config)

    try:
        # Validate tables
        if args.validate or args.reset:
            existing_tables, missing_tables = check_tables_exist(conn)

            if missing_tables:
                print(f"\n⚠️  {len(missing_tables)} tables missing:")
                for table in missing_tables:
                    print(f"   - {table}")

                if not args.reset:
                    print("\n💡 To create missing tables:")
                    print("   1. Start PostgreSQL: docker-compose up -d postgres")
                    print(
                        "   2. Wait for init scripts to run (check logs: docker-compose logs postgres)"
                    )
                    print("   3. Or run: python scripts/init_local_database.py --reset")
            else:
                print("\n✅ All expected tables exist!")

        # Show statistics
        if args.stats and not args.reset:
            existing_tables, _ = check_tables_exist(conn)
            if existing_tables:
                get_table_statistics(conn, existing_tables)

        # Reset database
        if args.reset:
            sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql", "init")
            if not os.path.exists(sql_dir):
                print(f"❌ SQL init directory not found: {sql_dir}")
                sys.exit(1)
            reset_database(conn, sql_dir)

            # Show stats after reset
            existing_tables, _ = check_tables_exist(conn)
            get_table_statistics(conn, existing_tables)

        # Health checks
        check_database_health(conn)

        print("\n" + "=" * 70)
        print("✅ Database validation complete!")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
