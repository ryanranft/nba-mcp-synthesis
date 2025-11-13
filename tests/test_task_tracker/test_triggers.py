"""
Unit Tests for Database Triggers

Tests that database triggers fire correctly and update related fields.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest
from datetime import datetime, timedelta


def test_last_worked_at_trigger_on_in_progress(
    db_connection, create_test_task, clean_test_tasks
):
    """Test that last_worked_at is set when task moves to in_progress."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Initially should be NULL
    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    result = cursor.fetchone()
    assert result["last_worked_at"] is None

    # Update to in_progress
    cursor.execute(
        """
        UPDATE tasks SET status = 'in_progress' WHERE id = %s
        RETURNING last_worked_at
    """,
        (task_id,),
    )
    result = cursor.fetchone()
    db_connection.commit()

    # Should now have a timestamp
    assert result["last_worked_at"] is not None
    assert isinstance(result["last_worked_at"], datetime)


def test_last_worked_at_trigger_on_completed(
    db_connection, create_test_task, clean_test_tasks
):
    """Test that last_worked_at is set when task is completed."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Update to completed
    cursor.execute(
        """
        UPDATE tasks SET status = 'completed' WHERE id = %s
        RETURNING last_worked_at
    """,
        (task_id,),
    )
    result = cursor.fetchone()
    db_connection.commit()

    # Should have timestamp
    assert result["last_worked_at"] is not None


def test_last_worked_at_not_updated_on_other_changes(
    db_connection, create_test_task, clean_test_tasks
):
    """Test that last_worked_at is NOT updated for other status changes."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Update to blocked (not in_progress or completed)
    cursor.execute(
        """
        UPDATE tasks SET status = 'blocked' WHERE id = %s
        RETURNING last_worked_at
    """,
        (task_id,),
    )
    result = cursor.fetchone()
    db_connection.commit()

    # Should still be NULL
    assert result["last_worked_at"] is None


def test_last_worked_at_not_updated_on_priority_change(
    db_connection, create_test_task, clean_test_tasks
):
    """Test that last_worked_at is NOT updated when changing priority."""
    task_id = create_test_task({"status": "pending", "priority": "low"})

    cursor = db_connection.cursor()

    # Change priority (not status)
    cursor.execute(
        """
        UPDATE tasks SET priority = 'high' WHERE id = %s
        RETURNING last_worked_at
    """,
        (task_id,),
    )
    result = cursor.fetchone()
    db_connection.commit()

    # Should still be NULL
    assert result["last_worked_at"] is None


def test_trigger_propagates_to_parent(db_connection, clean_test_tasks):
    """Test that updating child task updates parent's last_worked_at."""
    cursor = db_connection.cursor()

    # Create parent
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Parent', 'Working', 'pending', 'high', 'task', 0, 'test_trigger')
        RETURNING id
    """
    )
    parent_id = cursor.fetchone()["id"]

    # Create child
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, depth_level, session_id
        )
        VALUES ('Child', 'Working', 'pending', 'medium', 'subtask', %s, 1, 'test_trigger')
        RETURNING id
    """,
        (parent_id,),
    )
    child_id = cursor.fetchone()["id"]

    db_connection.commit()

    # Update child status
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (child_id,))
    db_connection.commit()

    # Check parent's last_worked_at was updated
    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (parent_id,))
    result = cursor.fetchone()

    assert result["last_worked_at"] is not None


def test_trigger_propagates_to_master(db_connection, clean_test_tasks):
    """Test that updating task updates master's last_worked_at."""
    cursor = db_connection.cursor()

    # Create master
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_trigger_master')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    # Create task under master
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Task', 'Working', 'pending', 'medium', 'task', %s, %s, 1, 'test_trigger_master')
        RETURNING id
    """,
        (master_id, master_id),
    )
    task_id = cursor.fetchone()["id"]

    db_connection.commit()

    # Update task status
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = %s", (task_id,))
    db_connection.commit()

    # Check master's last_worked_at was updated
    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (master_id,))
    result = cursor.fetchone()

    assert result["last_worked_at"] is not None


def test_trigger_only_fires_on_status_change(
    db_connection, create_test_task, clean_test_tasks
):
    """Test that trigger only fires when status actually changes."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Update to in_progress (should trigger)
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
    db_connection.commit()

    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    first_timestamp = cursor.fetchone()["last_worked_at"]

    # Wait a tiny bit
    import time

    time.sleep(0.1)

    # Update to in_progress again (no change, should not trigger)
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
    db_connection.commit()

    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    second_timestamp = cursor.fetchone()["last_worked_at"]

    # Timestamps should be the same (trigger didn't fire second time)
    assert first_timestamp == second_timestamp


def test_trigger_timestamp_accuracy(db_connection, create_test_task, clean_test_tasks):
    """Test that trigger sets accurate timestamp."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    before = datetime.now()

    # Update status
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
    db_connection.commit()

    after = datetime.now()

    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    timestamp = cursor.fetchone()["last_worked_at"]

    # Timestamp should be between before and after
    # Add some tolerance for clock differences
    assert before - timedelta(seconds=1) <= timestamp <= after + timedelta(seconds=1)


def test_trigger_with_null_parent(db_connection, create_test_task, clean_test_tasks):
    """Test that trigger works when parent_task_id is NULL."""
    task_id = create_test_task({"status": "pending", "parent_task_id": None})

    cursor = db_connection.cursor()

    # Should not error even with NULL parent
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = %s", (task_id,))
    db_connection.commit()

    # Task should have timestamp
    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    result = cursor.fetchone()

    assert result["last_worked_at"] is not None


def test_trigger_with_null_master(db_connection, create_test_task, clean_test_tasks):
    """Test that trigger works when master_task_id is NULL."""
    task_id = create_test_task(
        {"status": "pending", "parent_task_id": None, "master_task_id": None}
    )

    cursor = db_connection.cursor()

    # Should not error even with NULL master
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
    db_connection.commit()

    # Task should have timestamp
    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    result = cursor.fetchone()

    assert result["last_worked_at"] is not None


def test_trigger_multiple_status_changes(
    db_connection, create_test_task, clean_test_tasks
):
    """Test trigger with multiple status changes."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Change to in_progress
    cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
    db_connection.commit()

    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    first_timestamp = cursor.fetchone()["last_worked_at"]

    import time

    time.sleep(0.1)

    # Change to completed
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = %s", (task_id,))
    db_connection.commit()

    cursor.execute("SELECT last_worked_at FROM tasks WHERE id = %s", (task_id,))
    second_timestamp = cursor.fetchone()["last_worked_at"]

    # Second timestamp should be later
    assert second_timestamp > first_timestamp


def test_trigger_on_batch_update(db_connection, create_test_task, clean_test_tasks):
    """Test trigger fires for each row in batch update."""
    # Create multiple tasks
    task_ids = [
        create_test_task({"status": "pending", "content": f"Task {i}"})
        for i in range(3)
    ]

    cursor = db_connection.cursor()

    # Batch update
    cursor.execute(
        """
        UPDATE tasks SET status = 'completed'
        WHERE id = ANY(%s)
    """,
        (task_ids,),
    )
    db_connection.commit()

    # Check all have timestamp
    cursor.execute(
        """
        SELECT id, last_worked_at FROM tasks
        WHERE id = ANY(%s)
    """,
        (task_ids,),
    )

    results = cursor.fetchall()

    assert len(results) == 3
    for row in results:
        assert row["last_worked_at"] is not None


def test_trigger_name_exists(db_connection):
    """Test that the trigger is actually installed."""
    cursor = db_connection.cursor()

    cursor.execute(
        """
        SELECT trigger_name
        FROM information_schema.triggers
        WHERE event_object_table = 'tasks'
        AND trigger_name = 'update_task_last_worked'
    """
    )

    result = cursor.fetchone()

    assert result is not None
    assert result["trigger_name"] == "update_task_last_worked"


def test_trigger_function_exists(db_connection):
    """Test that the trigger function exists."""
    cursor = db_connection.cursor()

    cursor.execute(
        """
        SELECT proname
        FROM pg_proc
        WHERE proname = 'update_last_worked_at'
    """
    )

    result = cursor.fetchone()

    assert result is not None
    assert result["proname"] == "update_last_worked_at"
