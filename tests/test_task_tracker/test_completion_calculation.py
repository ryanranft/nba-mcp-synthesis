"""
Unit Tests for Completion Percentage Calculation

Tests the completion percentage calculation logic.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest


def test_empty_hierarchy_completion(db_connection, create_test_task, clean_test_tasks):
    """Test completion for task with no children."""
    task_id = create_test_task({"content": "Standalone", "task_type": "task"})

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (task_id,))
    result = cursor.fetchone()

    # Single task counts as 1 total
    assert result["total_tasks"] == 1
    assert result["completed_tasks"] == 0
    assert result["completion_percentage"] == 0.0


def test_zero_division_handling(db_connection, clean_test_tasks):
    """Test that zero tasks doesn't cause division by zero."""
    cursor = db_connection.cursor()

    # Create a master with no subtasks
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            context_summary, depth_level, session_id
        )
        VALUES ('Empty Master', 'Working', 'pending', 'high', 'master', 'No subtasks', 0, 'test_zero')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]
    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Should handle gracefully (return 0 or similar)
    assert result["completion_percentage"] == 0.0


def test_percentage_rounding(db_connection, create_test_hierarchy, clean_test_tasks):
    """Test that percentages are rounded correctly."""
    hierarchy = create_test_hierarchy("Rounding Test", subtask_count=3)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Complete 1 out of 3 = 33.33...%
    cursor.execute(
        "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[0],)
    )
    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Should be rounded to 1 decimal place
    assert result["completion_percentage"] == pytest.approx(33.3, abs=0.1)


def test_all_statuses_counted(db_connection, create_test_hierarchy, clean_test_tasks):
    """Test that all task statuses are counted."""
    hierarchy = create_test_hierarchy("All Statuses", subtask_count=5)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Set different statuses
    cursor.execute(
        "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[0],)
    )
    cursor.execute(
        "UPDATE tasks SET status = 'in_progress' WHERE id = %s", (subtask_ids[1],)
    )
    cursor.execute(
        "UPDATE tasks SET status = 'blocked' WHERE id = %s", (subtask_ids[2],)
    )
    cursor.execute(
        "UPDATE tasks SET status = 'cancelled' WHERE id = %s", (subtask_ids[3],)
    )
    # subtask_ids[4] remains 'pending'

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # All 5 should be counted in total
    assert result["total_tasks"] == 5
    assert result["completed_tasks"] == 1
    assert result["in_progress_tasks"] == 1
    assert result["pending_tasks"] == 1
    # Note: blocked and cancelled might not have dedicated counters


def test_completed_percentage_100(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test 100% completion."""
    hierarchy = create_test_hierarchy("Full Complete", subtask_count=4)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()

    # Complete all subtasks
    cursor.execute(
        """
        UPDATE tasks SET status = 'completed'
        WHERE master_task_id = %s AND task_type = 'task'
    """,
        (master_id,),
    )
    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["completion_percentage"] == 100.0


def test_master_not_counted_in_completion(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test that master task itself is not counted."""
    hierarchy = create_test_hierarchy("Master Not Counted", subtask_count=2)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()

    # Mark master as completed (shouldn't affect calculation)
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = %s", (master_id,))
    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Only subtasks should be counted (2 total, 0 completed)
    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 0


def test_only_leaf_tasks_counted(db_connection, clean_test_tasks):
    """Test that only task/subtask types are counted, not masters."""
    cursor = db_connection.cursor()

    # Create hierarchy: Master -> Task -> Subtask
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_leaf')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Task', 'Working', 'completed', 'medium', 'task', %s, %s, 1, 'test_leaf')
        RETURNING id
    """,
        (master_id, master_id),
    )
    task_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Subtask', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_leaf')
    """,
        (task_id, master_id),
    )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Should count Task and Subtask (2 total)
    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 1  # Task is completed
    assert result["completion_percentage"] == 50.0


def test_incremental_completion(db_connection, create_test_hierarchy, clean_test_tasks):
    """Test that completion updates incrementally."""
    hierarchy = create_test_hierarchy("Incremental", subtask_count=10)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Complete tasks one by one and check percentage
    for i in range(10):
        cursor.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[i],)
        )
        db_connection.commit()

        cursor.execute(
            "SELECT * FROM calculate_completion_percentage(%s)", (master_id,)
        )
        result = cursor.fetchone()

        expected_pct = (i + 1) * 10.0
        assert result["completion_percentage"] == pytest.approx(expected_pct, abs=0.1)


def test_completion_with_blocked_tasks(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test completion calculation with blocked tasks."""
    hierarchy = create_test_hierarchy("Blocked Test", subtask_count=4)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # 2 completed, 1 blocked, 1 pending
    cursor.execute(
        "UPDATE tasks SET status = 'completed' WHERE id IN (%s, %s)",
        (subtask_ids[0], subtask_ids[1]),
    )
    cursor.execute(
        "UPDATE tasks SET status = 'blocked' WHERE id = %s", (subtask_ids[2],)
    )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 4
    assert result["completed_tasks"] == 2
    assert result["completion_percentage"] == 50.0


def test_completion_with_cancelled_tasks(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test that cancelled tasks are counted in total but not completed."""
    hierarchy = create_test_hierarchy("Cancelled Test", subtask_count=3)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # 1 completed, 1 cancelled, 1 pending
    cursor.execute(
        "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[0],)
    )
    cursor.execute(
        "UPDATE tasks SET status = 'cancelled' WHERE id = %s", (subtask_ids[1],)
    )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 3
    assert result["completed_tasks"] == 1
    # 33.3% (cancelled not counted as complete)
    assert result["completion_percentage"] == pytest.approx(33.3, abs=0.1)


def test_completion_percentage_decimal_precision(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test decimal precision of percentage."""
    hierarchy = create_test_hierarchy("Precision Test", subtask_count=7)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Complete 3 out of 7 = 42.857...%
    for i in range(3):
        cursor.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[i],)
        )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Should be rounded to 1 decimal place: 42.9%
    assert result["completion_percentage"] == pytest.approx(42.9, abs=0.1)


def test_completion_for_subtask_hierarchy(db_connection, clean_test_tasks):
    """Test completion calculation starting from a subtask node."""
    cursor = db_connection.cursor()

    # Create: Master -> Task -> 2 Subtasks
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_sub')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Parent Task', 'Working', 'pending', 'medium', 'task', %s, %s, 1, 'test_sub')
        RETURNING id
    """,
        (master_id, master_id),
    )
    parent_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Subtask 1', 'Working', 'completed', 'low', 'subtask', %s, %s, 2, 'test_sub'),
               ('Subtask 2', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_sub')
    """,
        (parent_id, master_id, parent_id, master_id),
    )

    db_connection.commit()

    # Calculate completion for the parent task (not master)
    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (parent_id,))
    result = cursor.fetchone()

    # Should count only its children (2 subtasks)
    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 1
    assert result["completion_percentage"] == 50.0
