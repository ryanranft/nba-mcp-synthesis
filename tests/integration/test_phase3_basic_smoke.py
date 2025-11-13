"""
Basic Smoke Tests for Phase 3 UX Enhancements

Quick verification that all Phase 3 tools are functional.
Run with: pytest tests/integration/test_phase3_basic_smoke.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
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
    create_master_task,
)


@pytest.fixture(scope="module")
def cleanup():
    """Clean up test data after all tests."""
    yield
    # Cleanup happens after all tests
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE content LIKE 'SMOKE_TEST:%'")
    cursor.execute("DELETE FROM task_templates WHERE name LIKE 'smoke_test_%'")
    conn.commit()


class TestBulkOperations:
    """Smoke tests for bulk operations."""

    def test_bulk_update_status(self, cleanup):
        """Test bulk status update."""
        # Create test tasks
        task_ids = []
        for i in range(3):
            result = create_task(
                content=f"SMOKE_TEST: Task {i+1}",
                active_form=f"Testing task {i+1}",
                priority="medium",
            )
            task_ids.append(result["task"]["id"])

        # Bulk update
        result = bulk_update_status(task_ids, "completed")

        assert result["success"] is True
        assert result["updated_count"] == 3

    def test_bulk_update_priority(self, cleanup):
        """Test bulk priority update."""
        # Create test tasks
        task_ids = []
        for i in range(3):
            result = create_task(
                content=f"SMOKE_TEST: Priority task {i+1}",
                active_form=f"Testing priority {i+1}",
                priority="low",
            )
            task_ids.append(result["task"]["id"])

        # Bulk update
        result = bulk_update_priority(task_ids, "high")

        assert result["success"] is True
        assert result["updated_count"] == 3

    def test_bulk_add_tags(self, cleanup):
        """Test bulk tag addition."""
        # Create test tasks
        task_ids = []
        for i in range(3):
            result = create_task(
                content=f"SMOKE_TEST: Tag task {i+1}",
                active_form=f"Testing tags {i+1}",
                priority="medium",
            )
            task_ids.append(result["task"]["id"])

        # Bulk add tags
        result = bulk_add_tags(task_ids, ["urgent", "review"])

        assert result["success"] is True
        assert result["updated_count"] == 3


class TestExports:
    """Smoke tests for export tools."""

    def test_generate_summary_report(self, cleanup):
        """Test summary report generation."""
        # Create some test tasks
        for i in range(5):
            create_task(
                content=f"SMOKE_TEST: Report task {i+1}",
                active_form=f"Testing report {i+1}",
                priority="medium",
            )

        result = generate_summary_report(period="weekly")

        assert result["success"] is True
        assert "report" in result

    def test_export_gantt_chart(self, cleanup):
        """Test Gantt chart export."""
        # Create master task
        result = create_master_task(
            title="SMOKE_TEST: Gantt project",
            context_summary="Test project for Gantt",
            subtasks=[
                {"content": "Task 1", "active_form": "Working on task 1"},
                {"content": "Task 2", "active_form": "Working on task 2"},
            ],
        )

        master_id = result["master_task"]["id"]

        # Export Gantt
        gantt_result = export_gantt_chart(master_task_id=master_id)

        assert gantt_result["success"] is True
        assert "chart" in gantt_result


class TestTemplates:
    """Smoke tests for template system."""

    def test_list_templates(self):
        """Test listing templates."""
        result = list_templates()

        assert result["success"] is True
        assert "templates" in result
        assert result["total_count"] >= 8  # Should have 8 built-in templates

    def test_get_template_details(self):
        """Test getting template details."""
        result = get_template_details("Bug Fix")

        assert result["success"] is True
        assert "template" in result

    def test_create_from_template(self, cleanup):
        """Test creating from template."""
        result = create_from_template(
            template_name="Bug Fix", master_task_title="SMOKE_TEST: Fix critical bug"
        )

        assert result["success"] is True
        assert "master_task" in result
        assert result["tasks_created"] > 0

    def test_save_as_template(self, cleanup):
        """Test saving as template."""
        # Create master with subtasks
        result = create_master_task(
            title="SMOKE_TEST: Template source",
            context_summary="Test for saving template",
            subtasks=[
                {"content": "Step 1", "active_form": "Working step 1"},
                {"content": "Step 2", "active_form": "Working step 2"},
                {"content": "Step 3", "active_form": "Working step 3"},
            ],
        )

        master_id = result["master_task"]["id"]

        # Save as template
        template_result = save_as_template(
            master_task_id=master_id,
            template_name="smoke_test_workflow",
            description="Test workflow template",
        )

        assert template_result["success"] is True
        assert template_result["task_count"] >= 3


class TestAnalytics:
    """Smoke tests for analytics tools."""

    def test_get_velocity_metrics(self, cleanup):
        """Test velocity metrics."""
        # Create and complete some tasks
        for i in range(5):
            task_result = create_task(
                content=f"SMOKE_TEST: Velocity task {i+1}",
                active_form=f"Working velocity {i+1}",
                priority="medium",
            )
            task_id = task_result["task"]["id"]

            # Complete them
            bulk_update_status([task_id], "completed")

        result = get_velocity_metrics(days=7)

        assert result["success"] is True
        assert "velocity" in result
        assert "tasks_per_day" in result["velocity"]

    def test_predict_completion(self, cleanup):
        """Test completion prediction."""
        result = predict_completion(use_velocity_days=7)

        # May succeed or fail depending on data
        assert "success" in result

    def test_get_bottlenecks(self, cleanup):
        """Test bottleneck detection."""
        result = get_bottlenecks(min_days_stale=7)

        assert result["success"] is True
        assert "bottlenecks" in result
        assert "severity" in result


class TestSmartFilters:
    """Smoke tests for smart filtering."""

    def test_list_tasks_basic(self, cleanup):
        """Test basic task listing."""
        result = list_tasks()

        assert result["success"] is True
        assert "tasks" in result

    def test_list_tasks_with_priority(self, cleanup):
        """Test listing by priority."""
        result = list_tasks(priority="high")

        assert result["success"] is True
        assert "tasks" in result

    def test_list_tasks_with_tag(self, cleanup):
        """Test listing by tag."""
        # Create task with tag
        create_task(
            content="SMOKE_TEST: Tagged task",
            active_form="Testing tagged task",
            tags=["smoke-tag"],
        )

        result = list_tasks(tag="smoke-tag")

        assert result["success"] is True
        assert "tasks" in result

    def test_list_tasks_with_sorting(self, cleanup):
        """Test task sorting."""
        result = list_tasks(sort_by="priority")

        assert result["success"] is True
        assert "tasks" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
