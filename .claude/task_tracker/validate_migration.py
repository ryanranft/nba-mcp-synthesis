#!/usr/bin/env python3
"""
Migration Validation Script

Validates that all database migrations were applied correctly.
Part of: Enhancement Phase 1.4 - Migration Validation Script
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple

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


class MigrationValidator:
    """Validates database migrations."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []

    def check(self, name: str, check_func) -> bool:
        """Run a validation check."""
        try:
            check_func()
            self.passed.append(f"✅ {name}")
            print(f"✅ {name}")
            return True
        except Exception as e:
            error_msg = f"❌ {name}: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False

    def warn(self, message: str):
        """Record a warning."""
        warning_msg = f"⚠️  {message}"
        self.warnings.append(warning_msg)
        print(warning_msg)

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("MIGRATION VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Passed: {len(self.passed)}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")

        print("\n" + "=" * 80)

        if self.errors:
            print("❌ MIGRATION VALIDATION FAILED")
            return False
        else:
            print("✅ ALL MIGRATIONS VALIDATED")
            return True


def get_connection():
    """Get database connection."""
    config = get_database_config()
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="claude_tasks",
        user=config["user"],
        password=config["password"],
        cursor_factory=RealDictCursor,
    )


# =============================================================================
# VALIDATION CHECKS
# =============================================================================


def validate_hierarchical_migration(conn):
    """Validate hierarchical tracking migration."""
    cursor = conn.cursor()

    # Check new columns exist
    required_columns = [
        "task_type",
        "last_worked_at",
        "context_summary",
        "depth_level",
        "master_task_id",
        "session_id",
    ]

    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'tasks'
    """
    )

    existing_columns = [row["column_name"] for row in cursor.fetchall()]

    for col in required_columns:
        if col not in existing_columns:
            raise Exception(f"Column '{col}' missing from tasks table")


def validate_indexes(conn):
    """Validate that all required indexes exist."""
    cursor = conn.cursor()

    required_indexes = [
        "idx_tasks_task_type",
        "idx_tasks_parent_task_id",
        "idx_tasks_master_task_id",
        "idx_tasks_last_worked_at",
        "idx_tasks_depth_level",
        "idx_tasks_session_id",
    ]

    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = 'tasks'
    """
    )

    existing_indexes = [row["indexname"] for row in cursor.fetchall()]

    for idx in required_indexes:
        if idx not in existing_indexes:
            raise Exception(f"Index '{idx}' missing")


def validate_views(conn):
    """Validate that required views exist."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        AND table_name = 'master_tasks_progress'
    """
    )

    if cursor.fetchone() is None:
        raise Exception("View 'master_tasks_progress' does not exist")


def validate_functions(conn):
    """Validate that required functions exist."""
    cursor = conn.cursor()

    required_functions = [
        "get_task_hierarchy",
        "calculate_completion_percentage",
        "update_last_worked_at",
    ]

    cursor.execute(
        """
        SELECT proname
        FROM pg_proc
        WHERE proname = ANY(%s)
    """,
        (required_functions,),
    )

    existing = [row["proname"] for row in cursor.fetchall()]

    for func in required_functions:
        if func not in existing:
            raise Exception(f"Function '{func}' does not exist")


def validate_triggers(conn):
    """Validate that required triggers exist."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trigger_name
        FROM information_schema.triggers
        WHERE event_object_table = 'tasks'
        AND trigger_name = 'update_task_last_worked'
    """
    )

    if cursor.fetchone() is None:
        raise Exception("Trigger 'update_task_last_worked' does not exist")


def validate_column_types(conn):
    """Validate column data types are correct."""
    cursor = conn.cursor()

    expected_types = {
        "task_type": "character varying",
        "last_worked_at": "timestamp without time zone",
        "context_summary": "text",
        "depth_level": "integer",
        "master_task_id": "integer",
        "session_id": "character varying",
    }

    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'tasks'
        AND column_name = ANY(%s)
    """,
        (list(expected_types.keys()),),
    )

    for row in cursor.fetchall():
        col_name = row["column_name"]
        actual_type = row["data_type"]
        expected_type = expected_types[col_name]

        if actual_type != expected_type:
            raise Exception(
                f"Column '{col_name}' has type '{actual_type}', "
                f"expected '{expected_type}'"
            )


def validate_check_constraints(conn):
    """Validate CHECK constraints are in place."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_schema = 'public'
    """
    )

    constraints = cursor.fetchall()

    # Look for task_type constraint
    task_type_constraint = any(
        "task_type" in str(c.get("check_clause", "")).lower() for c in constraints
    )

    if not task_type_constraint:
        raise Exception("CHECK constraint for task_type not found")


def validate_foreign_keys(conn):
    """Validate foreign key constraints."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'tasks'
    """
    )

    fks = cursor.fetchall()

    # Check for master_task_id FK
    master_fk = any(fk["column_name"] == "master_task_id" for fk in fks)

    if not master_fk:
        raise Exception("Foreign key for master_task_id not found")


def validate_view_queries(conn):
    """Validate that views can be queried without errors."""
    cursor = conn.cursor()

    # Test master_tasks_progress view
    cursor.execute("SELECT * FROM master_tasks_progress LIMIT 1")

    # Should execute without error


def validate_function_signatures(conn):
    """Validate function signatures are correct."""
    cursor = conn.cursor()

    # Check get_task_hierarchy parameters
    cursor.execute(
        """
        SELECT
            pg_proc.proname,
            pg_get_function_arguments(pg_proc.oid) as args
        FROM pg_proc
        WHERE proname = 'get_task_hierarchy'
    """
    )

    result = cursor.fetchone()
    if not result:
        raise Exception("get_task_hierarchy function not found")

    args = result["args"]
    if "root_task_id" not in args.lower():
        raise Exception("get_task_hierarchy missing root_task_id parameter")


def validate_data_integrity(conn):
    """Validate data integrity after migration."""
    cursor = conn.cursor()

    # Check for tasks with invalid task_type
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM tasks
        WHERE task_type NOT IN ('master', 'task', 'subtask')
    """
    )

    result = cursor.fetchone()
    if result["count"] > 0:
        raise Exception(f"{result['count']} tasks have invalid task_type")

    # Check for orphaned master_task_id references
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM tasks t1
        WHERE t1.master_task_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM tasks t2
            WHERE t2.id = t1.master_task_id
        )
    """
    )

    result = cursor.fetchone()
    if result["count"] > 0:
        raise Exception(f"{result['count']} tasks have orphaned master_task_id")


def check_task_count_consistency(conn):
    """Check for any data inconsistencies."""
    cursor = conn.cursor()

    # Get total task count
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    total = cursor.fetchone()["count"]

    # Get master task count
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE task_type = 'master'")
    masters = cursor.fetchone()["count"]

    print(f"   Total tasks: {total}")
    print(f"   Master tasks: {masters}")
    print(f"   Regular tasks: {total - masters}")


def validate_trigger_functionality(conn):
    """Validate that triggers actually work."""
    cursor = conn.cursor()

    # Create a test task
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
        VALUES ('Trigger test', 'Testing', 'pending', 'low', 'task', 'validate_trigger')
        RETURNING id
    """
    )

    task_id = cursor.fetchone()["id"]

    # Update to in_progress (should trigger)
    cursor.execute(
        """
        UPDATE tasks SET status = 'in_progress' WHERE id = %s
        RETURNING last_worked_at
    """,
        (task_id,),
    )

    result = cursor.fetchone()

    # Clean up
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()

    if result["last_worked_at"] is None:
        raise Exception("Trigger did not update last_worked_at")


# =============================================================================
# MAIN VALIDATION
# =============================================================================


def main():
    """Run all migration validations."""
    print("=" * 80)
    print("MIGRATION VALIDATION")
    print(f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 80)
    print()

    # Load credentials
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

    validator = MigrationValidator()
    conn = get_connection()

    try:
        # Validate hierarchical migration
        validator.check(
            "Hierarchical columns exist", lambda: validate_hierarchical_migration(conn)
        )
        validator.check("Required indexes exist", lambda: validate_indexes(conn))
        validator.check("Required views exist", lambda: validate_views(conn))
        validator.check("Required functions exist", lambda: validate_functions(conn))
        validator.check("Required triggers exist", lambda: validate_triggers(conn))

        # Validate schema details
        validator.check(
            "Column data types correct", lambda: validate_column_types(conn)
        )
        validator.check(
            "CHECK constraints in place", lambda: validate_check_constraints(conn)
        )
        validator.check("Foreign keys in place", lambda: validate_foreign_keys(conn))

        # Validate functionality
        validator.check("Views can be queried", lambda: validate_view_queries(conn))
        validator.check(
            "Function signatures correct", lambda: validate_function_signatures(conn)
        )
        validator.check(
            "Triggers functional", lambda: validate_trigger_functionality(conn)
        )

        # Validate data integrity
        validator.check(
            "Data integrity maintained", lambda: validate_data_integrity(conn)
        )

        # Additional checks
        print("\n📊 Database Statistics:")
        check_task_count_consistency(conn)

    finally:
        conn.close()

    # Print summary
    print()
    success = validator.print_summary()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
