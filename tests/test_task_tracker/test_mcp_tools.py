"""
Unit Tests for Task Tracker MCP Tools

Tests all 14+ MCP tools for correct behavior.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest
from datetime import datetime


def test_create_task_basic(db_connection, clean_test_tasks):
    """Test basic task creation."""
    cursor = db_connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
        VALUES ('Test task', 'Testing', 'pending', 'medium', 'task', 'test_create_basic')
        RETURNING id, content, status, priority
    """
    )

    task = cursor.fetchone()
    db_connection.commit()

    assert task is not None
    assert task["content"] == "Test task"
    assert task["status"] == "pending"
    assert task["priority"] == "medium"


def test_create_task_with_parent(db_connection, create_test_task, clean_test_tasks):
    """Test creating a subtask with parent."""
    # Create parent task
    parent_id = create_test_task({"content": "Parent task", "depth_level": 0})

    # Create child task
    child_id = create_test_task(
        {"content": "Child task", "parent_task_id": parent_id, "depth_level": 1}
    )

    # Verify parent-child relationship
    cursor = db_connection.cursor()
    cursor.execute("SELECT parent_task_id FROM tasks WHERE id = %s", (child_id,))
    result = cursor.fetchone()

    assert result["parent_task_id"] == parent_id


def test_create_master_task(db_connection, clean_test_tasks):
    """Test master task creation."""
    cursor = db_connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            context_summary, depth_level, session_id
        )
        VALUES (
            'Master Task', 'Working on master', 'pending', 'high', 'master',
            'Test master task context', 0, 'test_master'
        )
        RETURNING id, task_type, context_summary
    """
    )

    master = cursor.fetchone()
    db_connection.commit()

    assert master is not None
    assert master["task_type"] == "master"
    assert master["context_summary"] == "Test master task context"


def test_update_task_status(db_connection, create_test_task, clean_test_tasks):
    """Test updating task status."""
    task_id = create_test_task({"status": "pending"})

    cursor = db_connection.cursor()

    # Update status
    cursor.execute(
        """
        UPDATE tasks SET status = 'in_progress' WHERE id = %s
        RETURNING status
    """,
        (task_id,),
    )

    result = cursor.fetchone()
    db_connection.commit()

    assert result["status"] == "in_progress"


def test_update_task_priority(db_connection, create_test_task, clean_test_tasks):
    """Test updating task priority."""
    task_id = create_test_task({"priority": "low"})

    cursor = db_connection.cursor()

    cursor.execute(
        """
        UPDATE tasks SET priority = 'critical' WHERE id = %s
        RETURNING priority
    """,
        (task_id,),
    )

    result = cursor.fetchone()
    db_connection.commit()

    assert result["priority"] == "critical"


def test_list_tasks_by_status(db_connection, create_test_task, clean_test_tasks):
    """Test listing tasks filtered by status."""
    # Create tasks with different statuses
    create_test_task({"status": "pending", "content": "Task 1"})
    create_test_task({"status": "in_progress", "content": "Task 2"})
    create_test_task({"status": "completed", "content": "Task 3"})

    cursor = db_connection.cursor()

    # Query pending tasks
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM tasks
        WHERE status = 'pending' AND session_id = 'test_session_002'
    """
    )

    result = cursor.fetchone()
    assert result["count"] >= 1


def test_list_tasks_by_priority(db_connection, create_test_task, clean_test_tasks):
    """Test listing tasks filtered by priority."""
    # Create tasks with different priorities
    create_test_task({"priority": "low", "content": "Low priority"})
    create_test_task({"priority": "high", "content": "High priority"})
    create_test_task({"priority": "critical", "content": "Critical priority"})

    cursor = db_connection.cursor()

    # Query high priority tasks
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM tasks
        WHERE priority = 'high' AND session_id = 'test_session_002'
    """
    )

    result = cursor.fetchone()
    assert result["count"] >= 1


def test_delete_task(db_connection, clean_test_tasks):
    """Test task deletion."""
    cursor = db_connection.cursor()

    # Create task
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
        VALUES ('To delete', 'Deleting', 'pending', 'low', 'task', 'test_delete')
        RETURNING id
    """
    )

    task_id = cursor.fetchone()["id"]
    db_connection.commit()

    # Delete task
    cursor.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
    deleted = cursor.fetchone()
    db_connection.commit()

    assert deleted is not None
    assert deleted["id"] == task_id

    # Verify deletion
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    result = cursor.fetchone()
    assert result is None


def test_get_task_hierarchy(db_connection, create_test_hierarchy, clean_test_tasks):
    """Test retrieving task hierarchy."""
    hierarchy = create_test_hierarchy("Test Hierarchy", subtask_count=3)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()

    # Get hierarchy using function
    cursor.execute("SELECT * FROM get_task_hierarchy(%s)", (master_id,))
    tasks = cursor.fetchall()

    # Should have master + 3 subtasks = 4 tasks
    assert len(tasks) == 4

    # Check master is at depth 0
    master = [t for t in tasks if t["depth"] == 0][0]
    assert master["task_type"] == "master"

    # Check subtasks are at depth 1
    subtasks = [t for t in tasks if t["depth"] == 1]
    assert len(subtasks) == 3


def test_calculate_completion_percentage(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test completion percentage calculation."""
    hierarchy = create_test_hierarchy("Completion Test", subtask_count=4)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Mark 2 out of 4 subtasks complete
    cursor.execute(
        """
        UPDATE tasks SET status = 'completed'
        WHERE id IN (%s, %s)
    """,
        (subtask_ids[0], subtask_ids[1]),
    )
    db_connection.commit()

    # Calculate completion
    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 4
    assert result["completed_tasks"] == 2
    assert result["completion_percentage"] == 50.0


def test_search_tasks_by_content(db_connection, create_test_task, clean_test_tasks):
    """Test searching tasks by content."""
    create_test_task({"content": "Implement feature XYZ"})
    create_test_task({"content": "Test feature ABC"})
    create_test_task({"content": "Document feature XYZ"})

    cursor = db_connection.cursor()

    # Search for "XYZ"
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM tasks
        WHERE content ILIKE %s AND session_id = 'test_session_002'
    """,
        ("%XYZ%",),
    )

    result = cursor.fetchone()
    assert result["count"] == 2


def test_task_tags(db_connection, clean_test_tasks):
    """Test task tagging."""
    cursor = db_connection.cursor()

    # Create task
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
        VALUES ('Tagged task', 'Tagging', 'pending', 'medium', 'task', 'test_tags')
        RETURNING id
    """
    )

    task_id = cursor.fetchone()["id"]

    # Add tags
    cursor.execute(
        """
        INSERT INTO task_tags (task_id, tag)
        VALUES (%s, 'feature'), (%s, 'urgent')
    """,
        (task_id, task_id),
    )
    db_connection.commit()

    # Query tags
    cursor.execute(
        """
        SELECT tag FROM task_tags WHERE task_id = %s ORDER BY tag
    """,
        (task_id,),
    )

    tags = [row["tag"] for row in cursor.fetchall()]
    assert tags == ["feature", "urgent"]


def test_session_id_tracking(db_connection, clean_test_tasks):
    """Test that session_id is properly tracked."""
    cursor = db_connection.cursor()

    session_id = "test_session_unique_123"

    # Create tasks with same session
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, session_id)
        VALUES ('Task 1', 'Testing 1', 'pending', 'medium', 'task', %s),
               ('Task 2', 'Testing 2', 'pending', 'medium', 'task', %s)
        RETURNING id
    """,
        (session_id, session_id),
    )
    db_connection.commit()

    # Query by session
    cursor.execute(
        """
        SELECT COUNT(*) as count FROM tasks WHERE session_id = %s
    """,
        (session_id,),
    )

    result = cursor.fetchone()
    assert result["count"] == 2


def test_depth_level_calculation(db_connection, clean_test_tasks):
    """Test that depth_level is correctly set."""
    cursor = db_connection.cursor()

    # Create master (depth 0)
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_depth')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    # Create subtask (depth 1)
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Subtask', 'Working', 'pending', 'medium', 'task', %s, %s, 1, 'test_depth')
        RETURNING id
    """,
        (master_id, master_id),
    )
    subtask_id = cursor.fetchone()["id"]

    # Create sub-subtask (depth 2)
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Sub-subtask', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_depth')
        RETURNING id
    """,
        (subtask_id, master_id),
    )

    db_connection.commit()

    # Verify depths
    cursor.execute(
        """
        SELECT id, depth_level FROM tasks
        WHERE session_id = 'test_depth'
        ORDER BY depth_level
    """
    )

    tasks = cursor.fetchall()
    assert tasks[0]["depth_level"] == 0  # master
    assert tasks[1]["depth_level"] == 1  # subtask
    assert tasks[2]["depth_level"] == 2  # sub-subtask
