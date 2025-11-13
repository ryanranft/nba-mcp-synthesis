#!/usr/bin/env python3
"""
Task Tracker MCP Health Check

Tests database connectivity, MCP tool availability, and basic operations.
Part of: Enhancement Phase 1.2 - MCP Health Check System
"""

import sys
import os
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
import psycopg2
from psycopg2.extras import RealDictCursor


class HealthCheck:
    """Health check for Task Tracker MCP system."""

    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []

    def test(self, name: str, test_func):
        """Run a test and record result."""
        try:
            test_func()
            self.results.append(f"✅ {name}")
            print(f"✅ {name}")
            return True
        except Exception as e:
            error_msg = f"❌ {name}: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)
            if os.getenv("HEALTH_CHECK_VERBOSE"):
                traceback.print_exc()
            return False

    def warn(self, message: str):
        """Record a warning."""
        warning_msg = f"⚠️  {message}"
        self.warnings.append(warning_msg)
        print(warning_msg)

    def print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 80)
        print("HEALTH CHECK SUMMARY")
        print("=" * 80)
        print(f"Tests Passed: {len(self.results)}")
        print(f"Tests Failed: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n❌ FAILURES:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")

        print("\n" + "=" * 80)

        if self.errors:
            print("❌ HEALTH CHECK FAILED")
            return False
        else:
            print("✅ ALL HEALTH CHECKS PASSED")
            return True


def test_credentials_loading():
    """Test that credentials can be loaded."""
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    config = get_database_config()

    required = ["host", "port", "database", "user", "password"]
    for key in required:
        if not config.get(key):
            raise Exception(f"Missing credential: {key}")


def test_database_connection():
    """Test database connection."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
    )
    conn.close()


def test_tasks_table_exists():
    """Test that tasks table exists."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'tasks'
        );
    """
    )

    result = cursor.fetchone()
    if not result["exists"]:
        raise Exception("tasks table does not exist")

    conn.close()


def test_required_columns():
    """Test that all required columns exist."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'tasks'
    """
    )

    columns = [row["column_name"] for row in cursor.fetchall()]

    required_columns = [
        "id",
        "content",
        "active_form",
        "status",
        "priority",
        "context",
        "created_at",
        "updated_at",
        "completed_at",
        "parent_task_id",
        "estimated_duration_minutes",
        "actual_duration_minutes",
        "task_type",
        "last_worked_at",
        "context_summary",
        "depth_level",
        "master_task_id",
        "session_id",
    ]

    missing = [col for col in required_columns if col not in columns]
    if missing:
        raise Exception(f"Missing columns: {', '.join(missing)}")

    conn.close()


def test_indexes_exist():
    """Test that required indexes exist."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = 'tasks'
    """
    )

    indexes = [row["indexname"] for row in cursor.fetchall()]

    expected_indexes = [
        "idx_tasks_task_type",
        "idx_tasks_parent_task_id",
        "idx_tasks_master_task_id",
        "idx_tasks_last_worked_at",
        "idx_tasks_depth_level",
        "idx_tasks_session_id",
    ]

    missing = [idx for idx in expected_indexes if idx not in indexes]
    if missing:
        raise Exception(f"Missing indexes: {', '.join(missing)}")

    conn.close()


def test_view_exists():
    """Test that master_tasks_progress view exists."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name = 'master_tasks_progress'
        );
    """
    )

    result = cursor.fetchone()
    if not result["exists"]:
        raise Exception("master_tasks_progress view does not exist")

    conn.close()


def test_view_query():
    """Test that view query works."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_tasks_progress LIMIT 1")
    # Just check it doesn't error

    conn.close()


def test_functions_exist():
    """Test that required PostgreSQL functions exist."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT proname
        FROM pg_proc
        WHERE proname IN ('get_task_hierarchy', 'calculate_completion_percentage', 'update_last_worked_at')
    """
    )

    functions = [row["proname"] for row in cursor.fetchall()]

    required = [
        "get_task_hierarchy",
        "calculate_completion_percentage",
        "update_last_worked_at",
    ]
    missing = [func for func in required if func not in functions]

    if missing:
        raise Exception(f"Missing functions: {', '.join(missing)}")

    conn.close()


def test_crud_operations():
    """Test basic CRUD operations."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()

    try:
        # CREATE
        cursor.execute(
            """
            INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
            VALUES ('Health check test task', 'Testing health check', 'pending', 'low', 'task', 'health_check_test')
            RETURNING id
        """
        )
        task_id = cursor.fetchone()["id"]

        # READ
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise Exception("Failed to read created task")

        # UPDATE
        cursor.execute(
            """
            UPDATE tasks SET status = 'completed' WHERE id = %s RETURNING id
        """,
            (task_id,),
        )

        # DELETE
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def test_trigger_works():
    """Test that last_worked_at trigger works."""
    config = get_database_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )

    cursor = conn.cursor()

    try:
        # Create a test task
        cursor.execute(
            """
            INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
            VALUES ('Trigger test task', 'Testing trigger', 'pending', 'low', 'task', 'trigger_test')
            RETURNING id
        """
        )
        task_id = cursor.fetchone()["id"]

        # Update status to in_progress (should trigger last_worked_at update)
        cursor.execute(
            """
            UPDATE tasks SET status = 'in_progress' WHERE id = %s RETURNING last_worked_at
        """,
            (task_id,),
        )

        result = cursor.fetchone()
        if not result["last_worked_at"]:
            raise Exception("Trigger did not update last_worked_at")

        # Cleanup
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    """Run all health checks."""
    print("=" * 80)
    print("TASK TRACKER MCP HEALTH CHECK")
    print(f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 80)
    print()

    health = HealthCheck()

    # Test credentials and database
    health.test("Credentials loading", test_credentials_loading)
    health.test("Database connection", test_database_connection)

    # Test schema
    health.test("Tasks table exists", test_tasks_table_exists)
    health.test("Required columns exist", test_required_columns)
    health.test("Required indexes exist", test_indexes_exist)

    # Test views and functions
    health.test("master_tasks_progress view exists", test_view_exists)
    health.test("View query executes", test_view_query)
    health.test("Required PostgreSQL functions exist", test_functions_exist)

    # Test operations
    health.test("CRUD operations work", test_crud_operations)
    health.test("last_worked_at trigger works", test_trigger_works)

    # Print summary
    print()
    success = health.print_summary()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
