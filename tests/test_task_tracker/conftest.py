"""
PyTest Configuration and Fixtures for Task Tracker Tests

Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import sys
import os
import pytest
from datetime import datetime

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


@pytest.fixture(scope="session")
def db_config():
    """Load database configuration once for all tests."""
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    return get_database_config()


@pytest.fixture(scope="function")
def db_connection(db_config):
    """Provide a fresh database connection for each test."""
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database="claude_tasks",
        user=db_config["user"],
        password=db_config["password"],
        cursor_factory=RealDictCursor,
    )

    yield conn

    # Cleanup: rollback any uncommitted changes
    conn.rollback()
    conn.close()


@pytest.fixture(scope="function")
def clean_test_tasks(db_connection):
    """Clean up test tasks before and after each test."""
    cursor = db_connection.cursor()

    # Cleanup before test
    cursor.execute("DELETE FROM tasks WHERE session_id LIKE 'test_%'")
    db_connection.commit()

    yield

    # Cleanup after test
    cursor.execute("DELETE FROM tasks WHERE session_id LIKE 'test_%'")
    db_connection.commit()


@pytest.fixture
def sample_task_data():
    """Provide sample task data for testing."""
    return {
        "content": "Test task",
        "active_form": "Testing",
        "status": "pending",
        "priority": "medium",
        "task_type": "task",
        "session_id": "test_session_001",
    }


@pytest.fixture
def sample_master_task_data():
    """Provide sample master task data for testing."""
    return {
        "content": "Test master task",
        "active_form": "Working on test master task",
        "status": "pending",
        "priority": "high",
        "task_type": "master",
        "context_summary": "This is a test master task with multiple subtasks",
        "session_id": "test_session_001",
    }


@pytest.fixture
def create_test_task(db_connection):
    """Factory fixture to create test tasks."""
    created_ids = []

    def _create(data_override=None):
        cursor = db_connection.cursor()

        data = {
            "content": "Test task",
            "active_form": "Testing",
            "status": "pending",
            "priority": "medium",
            "task_type": "task",
            "depth_level": 0,
            "session_id": "test_session_002",
        }

        if data_override:
            data.update(data_override)

        cursor.execute(
            """
            INSERT INTO tasks (
                content, active_form, status, priority, task_type,
                depth_level, session_id
            )
            VALUES (%(content)s, %(active_form)s, %(status)s, %(priority)s, %(task_type)s,
                    %(depth_level)s, %(session_id)s)
            RETURNING id
        """,
            data,
        )

        task_id = cursor.fetchone()["id"]
        created_ids.append(task_id)
        db_connection.commit()

        return task_id

    yield _create

    # Cleanup
    cursor = db_connection.cursor()
    if created_ids:
        cursor.execute("DELETE FROM tasks WHERE id = ANY(%s)", (created_ids,))
        db_connection.commit()


@pytest.fixture
def create_test_hierarchy(db_connection):
    """Factory fixture to create test task hierarchies."""
    created_ids = []

    def _create(master_content="Test Master", subtask_count=3):
        cursor = db_connection.cursor()

        # Create master task
        cursor.execute(
            """
            INSERT INTO tasks (
                content, active_form, status, priority, task_type,
                context_summary, depth_level, session_id
            )
            VALUES (%s, %s, 'pending', 'high', 'master', %s, 0, 'test_hierarchy')
            RETURNING id
        """,
            (master_content, f"Working on {master_content}", "Test hierarchy"),
        )

        master_id = cursor.fetchone()["id"]
        created_ids.append(master_id)

        # Create subtasks
        subtask_ids = []
        for i in range(subtask_count):
            cursor.execute(
                """
                INSERT INTO tasks (
                    content, active_form, status, priority, task_type,
                    parent_task_id, master_task_id, depth_level, session_id
                )
                VALUES (%s, %s, 'pending', 'medium', 'task', %s, %s, 1, 'test_hierarchy')
                RETURNING id
            """,
                (f"Subtask {i+1}", f"Working on subtask {i+1}", master_id, master_id),
            )

            subtask_id = cursor.fetchone()["id"]
            created_ids.append(subtask_id)
            subtask_ids.append(subtask_id)

        db_connection.commit()

        return {"master_id": master_id, "subtask_ids": subtask_ids}

    yield _create

    # Cleanup
    cursor = db_connection.cursor()
    if created_ids:
        cursor.execute("DELETE FROM tasks WHERE id = ANY(%s)", (created_ids,))
        db_connection.commit()
