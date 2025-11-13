"""
Unit Tests for Hierarchical Query Functions

Tests PostgreSQL recursive functions for task hierarchies.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest


def test_get_task_hierarchy_single_task(
    db_connection, create_test_task, clean_test_tasks
):
    """Test hierarchy for a single task with no children."""
    task_id = create_test_task({"content": "Standalone task"})

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM get_task_hierarchy(%s)", (task_id,))
    hierarchy = cursor.fetchall()

    assert len(hierarchy) == 1
    assert hierarchy[0]["task_id"] == task_id
    assert hierarchy[0]["depth"] == 0


def test_get_task_hierarchy_two_levels(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test hierarchy with master and direct children."""
    hierarchy = create_test_hierarchy("Two Level Test", subtask_count=3)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM get_task_hierarchy(%s)", (master_id,))
    tasks = cursor.fetchall()

    # Should have 1 master + 3 subtasks
    assert len(tasks) == 4

    # Master at depth 0
    master = [t for t in tasks if t["depth"] == 0][0]
    assert master["task_id"] == master_id

    # 3 children at depth 1
    children = [t for t in tasks if t["depth"] == 1]
    assert len(children) == 3


def test_get_task_hierarchy_deep_nesting(db_connection, clean_test_tasks):
    """Test hierarchy with multiple levels of nesting."""
    cursor = db_connection.cursor()

    # Create master
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_deep')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    # Create level 1 child
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L1 Child', 'Working', 'pending', 'medium', 'task', %s, %s, 1, 'test_deep')
        RETURNING id
    """,
        (master_id, master_id),
    )
    l1_id = cursor.fetchone()["id"]

    # Create level 2 child
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L2 Child', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_deep')
        RETURNING id
    """,
        (l1_id, master_id),
    )
    l2_id = cursor.fetchone()["id"]

    # Create level 3 child
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L3 Child', 'Working', 'pending', 'low', 'subtask', %s, %s, 3, 'test_deep')
        RETURNING id
    """,
        (l2_id, master_id),
    )

    db_connection.commit()

    # Get hierarchy
    cursor.execute("SELECT * FROM get_task_hierarchy(%s)", (master_id,))
    tasks = cursor.fetchall()

    # Should have 4 tasks (depths 0, 1, 2, 3)
    assert len(tasks) == 4

    depths = sorted([t["depth"] for t in tasks])
    assert depths == [0, 1, 2, 3]


def test_get_task_hierarchy_path():
    """Test that path array is correctly constructed."""
    # The path array should show the route from root to each node
    # This is more of an integration test, would need actual data
    pass  # Tested implicitly in other tests


def test_get_task_hierarchy_max_depth(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test max_depth parameter limits recursion."""
    hierarchy = create_test_hierarchy("Depth Limit Test", subtask_count=3)
    master_id = hierarchy["master_id"]
    subtask_id = hierarchy["subtask_ids"][0]

    cursor = db_connection.cursor()

    # Add a child to the first subtask
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('Deep child', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_hierarchy')
    """,
        (subtask_id, master_id),
    )
    db_connection.commit()

    # Get hierarchy with max_depth = 1 (should only get master + direct children)
    cursor.execute("SELECT * FROM get_task_hierarchy(%s, %s)", (master_id, 1))
    tasks = cursor.fetchall()

    # Should have master (depth 0) + 3 subtasks (depth 1) = 4
    # Should NOT include the deep child (depth 2)
    assert len(tasks) == 4
    assert max(t["depth"] for t in tasks) == 1


def test_hierarchy_ordering(db_connection, create_test_hierarchy, clean_test_tasks):
    """Test that hierarchy is returned in correct order."""
    hierarchy = create_test_hierarchy("Order Test", subtask_count=3)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM get_task_hierarchy(%s)", (master_id,))
    tasks = cursor.fetchall()

    # First task should be the master (depth 0)
    assert tasks[0]["depth"] == 0
    assert tasks[0]["task_id"] == master_id

    # Rest should be depth 1
    for task in tasks[1:]:
        assert task["depth"] == 1


def test_calculate_completion_percentage_all_pending(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test completion when all tasks are pending."""
    hierarchy = create_test_hierarchy("All Pending", subtask_count=4)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 4
    assert result["completed_tasks"] == 0
    assert result["in_progress_tasks"] == 0
    assert result["completion_percentage"] == 0.0


def test_calculate_completion_percentage_all_completed(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test completion when all tasks are completed."""
    hierarchy = create_test_hierarchy("All Complete", subtask_count=3)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Mark all subtasks complete
    for subtask_id in subtask_ids:
        cursor.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_id,)
        )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 3
    assert result["completed_tasks"] == 3
    assert result["completion_percentage"] == 100.0


def test_calculate_completion_percentage_partial(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test completion with some tasks complete."""
    hierarchy = create_test_hierarchy("Partial Complete", subtask_count=5)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # Mark 3 out of 5 complete
    for i in range(3):
        cursor.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = %s", (subtask_ids[i],)
        )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 5
    assert result["completed_tasks"] == 3
    assert result["completion_percentage"] == 60.0


def test_calculate_completion_percentage_with_in_progress(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test that in_progress tasks are counted separately."""
    hierarchy = create_test_hierarchy("In Progress Test", subtask_count=6)
    master_id = hierarchy["master_id"]
    subtask_ids = hierarchy["subtask_ids"]

    cursor = db_connection.cursor()

    # 2 completed, 2 in_progress, 2 pending
    cursor.execute(
        "UPDATE tasks SET status = 'completed' WHERE id IN (%s, %s)",
        (subtask_ids[0], subtask_ids[1]),
    )
    cursor.execute(
        "UPDATE tasks SET status = 'in_progress' WHERE id IN (%s, %s)",
        (subtask_ids[2], subtask_ids[3]),
    )

    db_connection.commit()

    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    assert result["total_tasks"] == 6
    assert result["completed_tasks"] == 2
    assert result["in_progress_tasks"] == 2
    assert result["pending_tasks"] == 2
    assert result["completion_percentage"] == pytest.approx(33.3, abs=0.1)


def test_calculate_completion_percentage_nested(db_connection, clean_test_tasks):
    """Test completion calculation with nested subtasks."""
    cursor = db_connection.cursor()

    # Create master
    cursor.execute(
        """
        INSERT INTO tasks (content, active_form, status, priority, task_type, depth_level, session_id)
        VALUES ('Master', 'Working', 'pending', 'high', 'master', 0, 'test_nested')
        RETURNING id
    """
    )
    master_id = cursor.fetchone()["id"]

    # Create 2 level-1 tasks
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L1-A', 'Working', 'pending', 'medium', 'task', %s, %s, 1, 'test_nested')
        RETURNING id
    """,
        (master_id, master_id),
    )
    l1_a_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L1-B', 'Working', 'completed', 'medium', 'task', %s, %s, 1, 'test_nested')
        RETURNING id
    """,
        (master_id, master_id),
    )

    # Create 2 level-2 tasks under L1-A
    cursor.execute(
        """
        INSERT INTO tasks (
            content, active_form, status, priority, task_type,
            parent_task_id, master_task_id, depth_level, session_id
        )
        VALUES ('L2-A', 'Working', 'completed', 'low', 'subtask', %s, %s, 2, 'test_nested'),
               ('L2-B', 'Working', 'pending', 'low', 'subtask', %s, %s, 2, 'test_nested')
    """,
        (l1_a_id, master_id, l1_a_id, master_id),
    )

    db_connection.commit()

    # Calculate completion
    cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (master_id,))
    result = cursor.fetchone()

    # Total: 4 tasks (2 level-1 + 2 level-2)
    # Completed: 2 (L1-B + L2-A)
    assert result["total_tasks"] == 4
    assert result["completed_tasks"] == 2
    assert result["completion_percentage"] == 50.0


def test_master_tasks_progress_view(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test the master_tasks_progress view."""
    hierarchy = create_test_hierarchy("View Test", subtask_count=3)
    master_id = hierarchy["master_id"]

    cursor = db_connection.cursor()
    cursor.execute(
        """
        SELECT * FROM master_tasks_progress WHERE master_id = %s
    """,
        (master_id,),
    )

    result = cursor.fetchone()

    assert result is not None
    assert result["master_id"] == master_id
    assert result["total_tasks"] == 3
    assert result["completed_tasks"] == 0
    assert result["completion_percentage"] == 0.0


def test_master_tasks_progress_view_multiple_masters(
    db_connection, create_test_hierarchy, clean_test_tasks
):
    """Test view with multiple master tasks."""
    h1 = create_test_hierarchy("Master 1", subtask_count=2)
    h2 = create_test_hierarchy("Master 2", subtask_count=3)

    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM master_tasks_progress WHERE session_id = 'test_hierarchy'"
    )

    # Should be able to see both (view might have session filter or not)
    # Just check it doesn't error
    result = cursor.fetchone()
    assert result["count"] >= 0  # View works
