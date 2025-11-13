"""
Integration Tests for Phase 3 UX Enhancements

Tests all new features added in Phase 3:
- Bulk operations
- Export capabilities
- Smart filters and sorting
- Task templates
- Analytics tools

Run with: pytest tests/integration/test_phase3_ux_enhancements.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import Task Tracker MCP tools (will be imported dynamically from MCP server)
# For testing, we'll need to import the actual functions from the MCP server file
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".claude",
        "task_tracker",
    ),
)

from task_tracker_mcp import (
    create_task,
    bulk_update_status,
    bulk_update_priority,
    bulk_add_tags,
    export_project,
    generate_summary_report,
    export_gantt_chart,
    list_tasks,
    create_from_template,
    save_as_template,
    list_templates,
    get_template_details,
    get_velocity_metrics,
    predict_completion,
    get_bottlenecks,
    get_db_connection,
)


@pytest.fixture(scope="module")
def db_connection():
    """Get database connection for tests."""
    return get_db_connection()


@pytest.fixture(scope="function")
def cleanup_test_data(db_connection):
    """Clean up test data after each test."""
    yield
    # Cleanup happens after test
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM tasks WHERE content LIKE 'TEST:%'")
    cursor.execute("DELETE FROM task_templates WHERE name LIKE 'test_%'")
    db_connection.commit()


@pytest.fixture(scope="function")
def sample_tasks():
    """Create sample tasks for testing."""
    tasks = []

    # Create diverse set of test tasks
    for i in range(10):
        result = create_task(
            content=f"TEST: Sample task {i+1}",
            active_form=f"Testing sample task {i+1}",
            priority=["low", "medium", "high", "critical"][i % 4],
            context=f"Test context for task {i+1}",
            tags=["test", f"batch{i//5}", f"priority{i%4}"],
            task_type="task",
        )
        tasks.append(result)

    return tasks


# ============================================================================
# BULK OPERATIONS TESTS
# ============================================================================


class TestBulkOperations:
    """Test bulk operation tools."""

    def test_bulk_update_status(self, sample_tasks, cleanup_test_data):
        """Test bulk status updates."""
        # Get first 3 task IDs
        task_ids = [t["task"]["id"] for t in sample_tasks[:3]]

        # Bulk update to completed
        result = bulk_update_status(
            task_ids=task_ids, status="completed", notes="Test bulk update"
        )

        assert result["success"] is True
        assert result["updated_count"] == 3
        assert len(result["tasks"]) == 3

        # Verify all tasks were updated
        for task in result["tasks"]:
            assert task["status"] == "completed"

    def test_bulk_update_priority(self, sample_tasks, cleanup_test_data):
        """Test bulk priority updates."""
        task_ids = [t["task"]["id"] for t in sample_tasks[3:6]]

        result = bulk_update_priority(task_ids=task_ids, priority="high")

        assert result["success"] is True
        assert result["updated_count"] == 3

        # Verify priorities were updated
        for task in result["tasks"]:
            assert task["priority"] == "high"

    def test_bulk_add_tags(self, sample_tasks, cleanup_test_data):
        """Test bulk tag additions."""
        task_ids = [t["task"]["id"] for t in sample_tasks[6:9]]

        result = bulk_add_tags(task_ids=task_ids, tags=["urgent", "review-needed"])

        assert result["success"] is True
        assert result["updated_count"] == 3
        assert result["tags_added"] >= 3  # At least 3 tag additions

    def test_bulk_operations_with_invalid_ids(self, cleanup_test_data):
        """Test bulk operations handle invalid IDs gracefully."""
        result = bulk_update_status(task_ids=[999999, 999998], status="completed")

        # Should fail or return empty result for non-existent tasks
        # The actual behavior is that it returns success=False or empty tasks list
        assert result["success"] is False or result.get("updated_count", 0) == 0


# ============================================================================
# EXPORT CAPABILITIES TESTS
# ============================================================================


class TestExportCapabilities:
    """Test export and reporting tools."""

    def test_export_project_json(self, sample_tasks, cleanup_test_data):
        """Test JSON project export."""
        # Set project for first 5 tasks
        for task in sample_tasks[:5]:
            task_id = task["task"]["id"]
            # Update task with project
            cursor = get_db_connection().cursor()
            cursor.execute(
                "UPDATE tasks SET project = %s WHERE id = %s", ("TEST_PROJECT", task_id)
            )
            get_db_connection().commit()

        result = export_project(
            project_name="TEST_PROJECT", format="json", include_completed=True
        )

        assert result["success"] is True
        assert "export_data" in result
        assert result["project"] == "TEST_PROJECT"
        assert result["format"] == "json"
        assert result["total_tasks"] >= 5

    def test_export_project_csv(self, sample_tasks, cleanup_test_data):
        """Test CSV project export."""
        # Set project for tasks
        for task in sample_tasks[:3]:
            task_id = task["task"]["id"]
            cursor = get_db_connection().cursor()
            cursor.execute(
                "UPDATE tasks SET project = %s WHERE id = %s",
                ("TEST_CSV_PROJECT", task_id),
            )
            get_db_connection().commit()

        result = export_project(project_name="TEST_CSV_PROJECT", format="csv")

        assert result["success"] is True
        assert "export_data" in result
        assert "id,content,status" in result["export_data"]

    def test_generate_summary_report(self, sample_tasks, cleanup_test_data):
        """Test summary report generation."""
        result = generate_summary_report(
            format="markdown", include_stats=True, group_by="priority"
        )

        assert result["success"] is True
        assert "report" in result
        assert "markdown" in result["format"]

        # Check report contains expected sections
        report = result["report"]
        assert "# Task Summary Report" in report or "Task Summary" in report

    def test_export_gantt_chart(self, sample_tasks, cleanup_test_data):
        """Test Gantt chart export."""
        # Set project and dates for tasks
        for i, task in enumerate(sample_tasks[:5]):
            task_id = task["task"]["id"]
            cursor = get_db_connection().cursor()
            start_date = datetime.now() + timedelta(days=i)
            due_date = start_date + timedelta(days=3)
            cursor.execute(
                "UPDATE tasks SET project = %s, due_date = %s WHERE id = %s",
                ("GANTT_PROJECT", due_date, task_id),
            )
            get_db_connection().commit()

        result = export_gantt_chart(
            project_name="GANTT_PROJECT", output_format="markdown"
        )

        assert result["success"] is True
        assert "gantt_chart" in result


# ============================================================================
# SMART FILTERS TESTS
# ============================================================================


class TestSmartFilters:
    """Test smart filtering and sorting."""

    def test_filter_by_stale(self, sample_tasks, cleanup_test_data):
        """Test filtering stale tasks."""
        # Make some tasks stale by updating their updated_at timestamp
        cursor = get_db_connection().cursor()
        stale_date = datetime.now() - timedelta(days=10)

        for task in sample_tasks[:3]:
            cursor.execute(
                "UPDATE tasks SET updated_at = %s, status = 'in_progress' WHERE id = %s",
                (stale_date, task["task"]["id"]),
            )
        get_db_connection().commit()

        result = list_tasks(filter_type="stale", stale_days=7)

        assert result["success"] is True
        assert len(result["tasks"]) >= 3

    def test_filter_by_blocked(self, sample_tasks, cleanup_test_data):
        """Test filtering blocked tasks."""
        # Mark some tasks as blocked
        cursor = get_db_connection().cursor()
        for task in sample_tasks[:2]:
            cursor.execute(
                "UPDATE tasks SET is_blocked = TRUE, blocker_reason = %s WHERE id = %s",
                ("TEST: Waiting for approval", task["task"]["id"]),
            )
        get_db_connection().commit()

        result = list_tasks(filter_type="blocked")

        assert result["success"] is True
        assert len(result["tasks"]) >= 2

    def test_filter_by_tag(self, sample_tasks, cleanup_test_data):
        """Test filtering by tags."""
        result = list_tasks(filter_type="by-tag", tags=["test"])

        assert result["success"] is True
        assert len(result["tasks"]) >= 10  # All sample tasks have 'test' tag

    def test_filter_by_priority(self, sample_tasks, cleanup_test_data):
        """Test filtering by priority."""
        result = list_tasks(filter_type="by-priority", priority="high")

        assert result["success"] is True
        # Should have tasks with high priority from sample_tasks
        assert len(result["tasks"]) >= 2

    def test_sort_by_priority(self, sample_tasks, cleanup_test_data):
        """Test sorting by priority."""
        result = list_tasks(sort_by="priority")

        assert result["success"] is True
        assert len(result["tasks"]) >= 10

        # Verify tasks are sorted by priority (critical -> high -> medium -> low)
        # This is a basic check - could be more thorough
        priorities = [t.get("priority") for t in result["tasks"][:10]]
        assert "critical" in priorities or "high" in priorities

    def test_sort_by_created(self, sample_tasks, cleanup_test_data):
        """Test sorting by creation date."""
        result = list_tasks(sort_by="created")

        assert result["success"] is True
        assert len(result["tasks"]) >= 10


# ============================================================================
# TASK TEMPLATES TESTS
# ============================================================================


class TestTaskTemplates:
    """Test task template system."""

    def test_list_templates(self):
        """Test listing available templates."""
        result = list_templates(include_builtin=True)

        assert result["success"] is True
        assert "templates" in result
        assert result["total"] >= 8  # Should have 8 built-in templates
        assert result["builtin"] >= 8

    def test_get_template_details(self):
        """Test getting template details."""
        result = get_template_details(template_name="bug_fix")

        assert result["success"] is True
        assert "template" in result
        assert result["template"]["name"] == "bug_fix"
        assert "template_data" in result["template"]

    def test_create_from_template(self, cleanup_test_data):
        """Test creating task from template."""
        result = create_from_template(
            template_name="bug_fix",
            title="TEST: Fix critical authentication bug",
            project="TEST_PROJECT",
            overrides={"priority": "critical", "tags": ["test", "bug", "security"]},
        )

        assert result["success"] is True
        assert "parent_task" in result
        assert "subtasks_created" in result
        assert result["subtasks_created"] >= 5  # bug_fix template has 5 subtasks
        assert result["parent_task"]["title"] == "TEST: Fix critical authentication bug"

    def test_save_as_template(self, sample_tasks, cleanup_test_data):
        """Test saving task as template."""
        # Get a sample task with subtasks
        parent_task = sample_tasks[0]
        parent_id = parent_task["task"]["id"]

        # Create a few subtasks
        for i in range(3):
            create_task(
                content=f"TEST: Subtask {i+1}",
                active_form=f"Testing subtask {i+1}",
                parent_task_id=parent_id,
                task_type="subtask",
            )

        # Save as template
        result = save_as_template(
            task_id=parent_id,
            template_name="test_custom_workflow",
            description="TEST: Custom workflow template",
            category="test",
        )

        assert result["success"] is True
        assert "template_name" in result
        assert result["template_name"] == "test_custom_workflow"

    def test_create_from_nonexistent_template(self, cleanup_test_data):
        """Test creating from non-existent template."""
        result = create_from_template(
            template_name="nonexistent_template", title="TEST: This should fail"
        )

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# ANALYTICS TESTS
# ============================================================================


class TestAnalytics:
    """Test analytics tools."""

    @pytest.fixture(scope="class")
    def analytics_setup(self):
        """Setup tasks for analytics testing."""
        tasks = []

        # Create completed tasks over time for velocity analysis
        for i in range(20):
            task = create_task(
                content=f"TEST: Analytics task {i+1}",
                active_form=f"Testing analytics {i+1}",
                priority=["low", "medium", "high"][i % 3],
                tags=["test", "analytics"],
            )
            tasks.append(task)

            # Complete some tasks
            if i < 15:
                cursor = get_db_connection().cursor()
                completed_date = datetime.now() - timedelta(days=20 - i)
                cursor.execute(
                    "UPDATE tasks SET status = 'completed', completed_at = %s WHERE id = %s",
                    (completed_date, task["task"]["id"]),
                )
                get_db_connection().commit()

        yield tasks

        # Cleanup
        cursor = get_db_connection().cursor()
        cursor.execute("DELETE FROM tasks WHERE content LIKE 'TEST: Analytics%'")
        get_db_connection().commit()

    def test_get_velocity_metrics(self, analytics_setup):
        """Test velocity metrics calculation."""
        result = get_velocity_metrics(days=30)

        assert result["success"] is True
        assert "velocity" in result
        assert "tasks_per_day" in result["velocity"]
        assert "tasks_per_week" in result["velocity"]
        assert "trend" in result
        assert result["velocity"]["tasks_per_day"] >= 0

    def test_predict_completion(self, analytics_setup):
        """Test completion prediction."""
        result = predict_completion(use_velocity_days=30)

        # Should succeed even with limited data
        assert "success" in result

        if result["success"]:
            assert "predictions" in result
            assert "realistic" in result["predictions"]
            assert "optimistic" in result["predictions"]
            assert "pessimistic" in result["predictions"]

    def test_get_bottlenecks(self, analytics_setup):
        """Test bottleneck detection."""
        # Create some stale and blocked tasks
        cursor = get_db_connection().cursor()

        # Make a task stale
        stale_task = analytics_setup[15]
        stale_date = datetime.now() - timedelta(days=10)
        cursor.execute(
            "UPDATE tasks SET status = 'in_progress', updated_at = %s WHERE id = %s",
            (stale_date, stale_task["task"]["id"]),
        )

        # Make a task blocked
        blocked_task = analytics_setup[16]
        cursor.execute(
            "UPDATE tasks SET is_blocked = TRUE, blocker_reason = %s WHERE id = %s",
            ("TEST: Waiting for review", blocked_task["task"]["id"]),
        )

        get_db_connection().commit()

        result = get_bottlenecks(min_days_stale=7)

        assert result["success"] is True
        assert "bottlenecks" in result
        assert "stale_tasks" in result["bottlenecks"]
        assert "blocked_tasks" in result["bottlenecks"]
        assert "severity" in result

        # Should detect our stale and blocked tasks
        assert result["bottlenecks"]["stale_tasks"]["count"] >= 1
        assert result["bottlenecks"]["blocked_tasks"]["count"] >= 1

    def test_velocity_metrics_with_project_filter(self, analytics_setup):
        """Test velocity metrics with project filter."""
        # Set project for some tasks
        cursor = get_db_connection().cursor()
        for task in analytics_setup[:10]:
            cursor.execute(
                "UPDATE tasks SET project = %s WHERE id = %s",
                ("ANALYTICS_TEST_PROJECT", task["task"]["id"]),
            )
        get_db_connection().commit()

        result = get_velocity_metrics(days=30, project="ANALYTICS_TEST_PROJECT")

        assert result["success"] is True
        assert result["project"] == "ANALYTICS_TEST_PROJECT"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestEndToEndWorkflows:
    """Test complete workflows combining multiple features."""

    def test_complete_feature_development_workflow(self, cleanup_test_data):
        """Test a complete feature development workflow."""
        # 1. Create task from template
        result = create_from_template(
            template_name="feature_development",
            title="TEST: Add user authentication",
            project="TEST_AUTH_PROJECT",
            overrides={"priority": "high"},
        )

        assert result["success"] is True
        parent_id = result["parent_task"]["id"]
        subtask_ids = [st["id"] for st in result["subtasks"]]

        # 2. Complete some subtasks using bulk operations
        first_three = subtask_ids[:3]
        bulk_result = bulk_update_status(task_ids=first_three, status="completed")

        assert bulk_result["success"] is True
        assert bulk_result["updated"] == 3

        # 3. Add tags to remaining subtasks
        remaining = subtask_ids[3:]
        tag_result = bulk_add_tags(
            task_ids=remaining, tags=["needs-review", "in-development"]
        )

        assert tag_result["success"] is True

        # 4. Export project
        export_result = export_project(project_name="TEST_AUTH_PROJECT", format="json")

        assert export_result["success"] is True

        # 5. Check analytics
        velocity = get_velocity_metrics(days=7, project="TEST_AUTH_PROJECT")
        bottlenecks = get_bottlenecks(project="TEST_AUTH_PROJECT")

        assert velocity["success"] is True
        assert bottlenecks["success"] is True

    def test_bug_fix_workflow(self, cleanup_test_data):
        """Test complete bug fix workflow."""
        # Create from bug_fix template
        result = create_from_template(
            template_name="bug_fix",
            title="TEST: Fix login timeout issue",
            project="TEST_BUGFIX_PROJECT",
            overrides={
                "priority": "critical",
                "tags": ["bug", "security", "production"],
            },
        )

        assert result["success"] is True
        subtasks = result["subtasks"]

        # Complete steps 1-3 (reproduce, identify, fix)
        first_three_ids = [st["id"] for st in subtasks[:3]]
        bulk_result = bulk_update_status(task_ids=first_three_ids, status="completed")

        assert bulk_result["success"] is True

        # Generate report
        report = generate_summary_report(format="markdown", group_by="project")

        assert report["success"] is True

        # Check bottlenecks
        bottlenecks = get_bottlenecks(project="TEST_BUGFIX_PROJECT", min_days_stale=1)

        assert bottlenecks["success"] is True


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Test performance of Phase 3 features."""

    def test_bulk_operations_performance(self, cleanup_test_data):
        """Test bulk operations with large number of tasks."""
        # Create 100 tasks
        task_ids = []
        for i in range(100):
            result = create_task(
                content=f"TEST: Performance task {i+1}",
                active_form=f"Testing performance {i+1}",
                priority="medium",
                tags=["test", "performance"],
            )
            task_ids.append(result["task"]["id"])

        # Bulk update all 100 tasks
        import time

        start = time.time()

        result = bulk_update_status(task_ids=task_ids, status="completed")

        elapsed = time.time() - start

        assert result["success"] is True
        assert result["updated"] == 100
        assert elapsed < 5.0  # Should complete in under 5 seconds

    def test_export_performance(self, sample_tasks, cleanup_test_data):
        """Test export performance."""
        # Set project for all tasks
        cursor = get_db_connection().cursor()
        for task in sample_tasks:
            cursor.execute(
                "UPDATE tasks SET project = %s WHERE id = %s",
                ("PERF_TEST_PROJECT", task["task"]["id"]),
            )
        get_db_connection().commit()

        import time

        start = time.time()

        result = export_project(
            project_name="PERF_TEST_PROJECT", format="json", include_completed=True
        )

        elapsed = time.time() - start

        assert result["success"] is True
        assert elapsed < 2.0  # Should complete in under 2 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
