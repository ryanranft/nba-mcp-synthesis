#!/usr/bin/env python3
"""
Setup Claude Tasks Database

Creates the claude_tasks database and initializes the schema.
Part of: Automatic Task Tracking System (Phase 3)
"""

import sys
import os

# Add project root to path to import unified_secrets_manager
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_database():
    """Create the claude_tasks database if it doesn't exist."""

    # Load credentials
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    db_config = get_database_config()

    print("Connecting to PostgreSQL server...")

    # Connect to postgres database (not claude_tasks yet)
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database="postgres",  # Connect to default postgres database
        user=db_config["user"],
        password=db_config["password"],
    )

    # Set autocommit for database creation
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = conn.cursor()

    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'claude_tasks'")
    exists = cursor.fetchone()

    if exists:
        print("✅ Database 'claude_tasks' already exists")
    else:
        print("Creating database 'claude_tasks'...")
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier("claude_tasks"))
        )
        print("✅ Database 'claude_tasks' created successfully")

    cursor.close()
    conn.close()


def initialize_schema():
    """Initialize the database schema."""

    # Load credentials
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    db_config = get_database_config()

    print("\nConnecting to claude_tasks database...")

    # Connect to claude_tasks database
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database="claude_tasks",
        user=db_config["user"],
        password=db_config["password"],
    )

    cursor = conn.cursor()

    # Read schema file
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    print(f"Reading schema from {schema_path}...")

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Execute schema
    print("Executing schema...")
    cursor.execute(schema_sql)
    conn.commit()

    print("✅ Schema initialized successfully")

    # Verify tables created
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    )

    tables = cursor.fetchall()
    print("\n✅ Tables created:")
    for table in tables:
        print(f"   - {table[0]}")

    # Verify views created
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    )

    views = cursor.fetchall()
    print("\n✅ Views created:")
    for view in views:
        print(f"   - {view[0]}")

    cursor.close()
    conn.close()


def test_connection():
    """Test that we can connect and query the database."""

    # Load credentials
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    db_config = get_database_config()

    print("\nTesting database connection...")

    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database="claude_tasks",
        user=db_config["user"],
        password=db_config["password"],
    )

    cursor = conn.cursor()

    # Test query
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    print(f"✅ Connection successful - {count} tasks in database")

    cursor.close()
    conn.close()


def main():
    """Main setup function."""

    print("=" * 60)
    print("Claude Tasks Database Setup")
    print("=" * 60)
    print()

    try:
        # Step 1: Create database
        create_database()

        # Step 2: Initialize schema
        initialize_schema()

        # Step 3: Test connection
        test_connection()

        print("\n" + "=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
        print()
        print("Database: claude_tasks")
        print("Tables: tasks, task_tags, task_history, handoff_documents, sessions")
        print("Views: active_tasks, recent_completed_tasks, task_statistics")
        print()
        print("Next steps:")
        print("1. Build the Task Tracker MCP server")
        print("2. Configure it in .claude/mcp.json")
        print("3. Test the complete system")

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
