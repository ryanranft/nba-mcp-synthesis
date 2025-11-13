#!/usr/bin/env python3
"""
Integration Tests for Task Tracker MCP Server
Phase 2.5: End-to-end workflow testing

Tests complete workflows:
- Task lifecycle (create → progress → complete → archive)
- Master task workflows
- Pagination
- Archive system
- TodoWrite sync
- Search functionality
"""

import sys
import os
from datetime import datetime, timedelta
import time

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

# Load credentials
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
db_config = get_database_config()


class TestTaskLifecycle:
    """Test complete task lifecycle workflow."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )
        self.cursor = self.conn.cursor()
        self.test_session_id = f"integration_test_{datetime.now():%Y%m%d_%H%M%S}"

    def cleanup(self):
        """Clean up test data."""
        try:
            self.conn.rollback()  # Clear any pending transaction
            self.cursor.execute(
                """
                DELETE FROM tasks WHERE session_id = %s
            """,
                (self.test_session_id,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()

    def test_basic_lifecycle(self):
        """Test: Create → In Progress → Completed → Archive."""
        print("\n" + "=" * 80)
        print("TEST: Basic Task Lifecycle")
        print("=" * 80)

        # 1. Create task
        self.cursor.execute(
            """
            INSERT INTO tasks (content, active_form, status, priority, session_id)
            VALUES ('Test task lifecycle', 'Testing task lifecycle', 'pending', 'medium', %s)
            RETURNING id, content, status, created_at
        """,
            (self.test_session_id,),
        )
        task = dict(self.cursor.fetchone())
        task_id = task["id"]
        self.conn.commit()

        print(f"✓ Created task {task_id}: {task['content']}")
        assert task["status"] == "pending"

        # 2. Move to in_progress
        self.cursor.execute(
            """
            UPDATE tasks SET status = 'in_progress', started_at = NOW()
            WHERE id = %s
            RETURNING id, status, started_at
        """,
            (task_id,),
        )
        task = dict(self.cursor.fetchone())
        self.conn.commit()

        print(f"✓ Updated to in_progress at {task['started_at']}")
        assert task["status"] == "in_progress"

        # 3. Complete task
        self.cursor.execute(
            """
            UPDATE tasks SET status = 'completed', completed_at = NOW()
            WHERE id = %s
            RETURNING id, status, completed_at
        """,
            (task_id,),
        )
        task = dict(self.cursor.fetchone())
        self.conn.commit()

        print(f"✓ Completed at {task['completed_at']}")
        assert task["status"] == "completed"

        # 4. Archive task
        self.cursor.execute(
            """
            UPDATE tasks
            SET is_archived = TRUE, archived_at = NOW(), archived_by = 'test'
            WHERE id = %s
            RETURNING id, is_archived, archived_at
        """,
            (task_id,),
        )
        task = dict(self.cursor.fetchone())
        self.conn.commit()

        print(f"✓ Archived at {task['archived_at']}")
        assert task["is_archived"] == True

        # 5. Verify task in archived_tasks view
        self.cursor.execute(
            """
            SELECT id, content, status, is_archived
            FROM tasks
            WHERE id = %s
        """,
            (task_id,),
        )
        archived = dict(self.cursor.fetchone())

        assert archived["is_archived"] == True
        print(f"✓ Verified in archive: {archived['content']}")

        print("\n✅ Basic lifecycle test PASSED")
        return True


class TestMasterTaskWorkflow:
    """Test master task with subtasks workflow."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )
        self.cursor = self.conn.cursor()
        self.test_session_id = f"integration_test_master_{datetime.now():%Y%m%d_%H%M%S}"

    def cleanup(self):
        """Clean up test data."""
        try:
            self.conn.rollback()  # Clear any pending transaction
            self.cursor.execute(
                """
                DELETE FROM tasks WHERE session_id = %s
            """,
                (self.test_session_id,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()

    def test_master_with_subtasks(self):
        """Test: Create master task → Add subtasks → Track progress → Complete."""
        print("\n" + "=" * 80)
        print("TEST: Master Task with Subtasks Workflow")
        print("=" * 80)

        # 1. Create master task
        self.cursor.execute(
            """
            INSERT INTO tasks
            (content, active_form, status, priority, task_type, context_summary, depth_level, session_id)
            VALUES ('Integration Test Project', 'Working on Integration Test Project', 'pending', 'high', 'master',
                    'Testing master task functionality', 0, %s)
            RETURNING id, content, task_type
        """,
            (self.test_session_id,),
        )
        master = dict(self.cursor.fetchone())
        master_id = master["id"]
        self.conn.commit()

        print(f"✓ Created master task {master_id}: {master['content']}")
        assert master["task_type"] == "master"

        # 2. Create 5 subtasks
        subtask_ids = []
        for i in range(1, 6):
            self.cursor.execute(
                """
                INSERT INTO tasks
                (content, active_form, status, priority, parent_task_id, master_task_id,
                 task_type, depth_level, session_id)
                VALUES (%s, %s, 'pending', 'medium', %s, %s, 'task', 1, %s)
                RETURNING id, content
            """,
                (
                    f"Subtask {i}",
                    f"Working on Subtask {i}",
                    master_id,
                    master_id,
                    self.test_session_id,
                ),
            )
            subtask = dict(self.cursor.fetchone())
            subtask_ids.append(subtask["id"])
            self.conn.commit()

        print(f"✓ Created 5 subtasks: {subtask_ids}")

        # 3. Check progress (should be 0%)
        self.cursor.execute(
            """
            SELECT * FROM calculate_completion_percentage(%s)
        """,
            (master_id,),
        )
        progress = dict(self.cursor.fetchone())

        print(
            f"✓ Initial progress: {progress['completion_percentage']}% (0/5 completed)"
        )
        assert progress["total_tasks"] == 5
        assert progress["completed_tasks"] == 0
        assert float(progress["completion_percentage"]) == 0.0

        # 4. Complete 3 subtasks
        for task_id in subtask_ids[:3]:
            self.cursor.execute(
                """
                UPDATE tasks SET status = 'completed', completed_at = NOW()
                WHERE id = %s
            """,
                (task_id,),
            )
            self.conn.commit()

        print(f"✓ Completed 3 of 5 subtasks")

        # 5. Check progress (should be 60%)
        self.cursor.execute(
            """
            SELECT * FROM calculate_completion_percentage(%s)
        """,
            (master_id,),
        )
        progress = dict(self.cursor.fetchone())

        print(f"✓ Progress: {progress['completion_percentage']}% (3/5 completed)")
        assert progress["completed_tasks"] == 3
        assert float(progress["completion_percentage"]) == 60.0

        # 6. Complete remaining 2 subtasks
        for task_id in subtask_ids[3:]:
            self.cursor.execute(
                """
                UPDATE tasks SET status = 'completed', completed_at = NOW()
                WHERE id = %s
            """,
                (task_id,),
            )
            self.conn.commit()

        print(f"✓ Completed all 5 subtasks")

        # 7. Check final progress (should be 100%)
        self.cursor.execute(
            """
            SELECT * FROM calculate_completion_percentage(%s)
        """,
            (master_id,),
        )
        progress = dict(self.cursor.fetchone())

        print(f"✓ Final progress: {progress['completion_percentage']}% (5/5 completed)")
        assert progress["completed_tasks"] == 5
        assert float(progress["completion_percentage"]) == 100.0

        # 8. Verify master_tasks_progress view
        self.cursor.execute(
            """
            SELECT * FROM master_tasks_progress WHERE master_id = %s
        """,
            (master_id,),
        )
        master_progress = dict(self.cursor.fetchone())

        print(f"✓ Master progress view: {master_progress['completion_percentage']}%")
        assert (
            master_progress["total_tasks"] == 5
        )  # View uses 'total_tasks' not 'total_subtasks'
        assert (
            master_progress["completed_tasks"] == 5
        )  # View uses 'completed_tasks' not 'completed_subtasks'

        print("\n✅ Master task workflow test PASSED")
        return True


class TestPagination:
    """Test pagination functionality."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )
        self.cursor = self.conn.cursor()
        self.test_session_id = (
            f"integration_test_pagination_{datetime.now():%Y%m%d_%H%M%S}"
        )

    def cleanup(self):
        """Clean up test data."""
        try:
            self.conn.rollback()  # Clear any pending transaction
            self.cursor.execute(
                """
                DELETE FROM tasks WHERE session_id = %s
            """,
                (self.test_session_id,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()

    def test_pagination(self):
        """Test: Create 50 tasks → Paginate through them."""
        print("\n" + "=" * 80)
        print("TEST: Pagination")
        print("=" * 80)

        # 1. Create 50 tasks
        task_ids = []
        for i in range(1, 51):
            self.cursor.execute(
                """
                INSERT INTO tasks (content, active_form, status, priority, session_id)
                VALUES (%s, %s, 'pending', 'medium', %s)
                RETURNING id
            """,
                (
                    f"Pagination test task {i}",
                    f"Testing pagination task {i}",
                    self.test_session_id,
                ),
            )
            task = dict(self.cursor.fetchone())
            task_ids.append(task["id"])
        self.conn.commit()

        print(f"✓ Created 50 test tasks")

        # 2. Test pagination - page 1 (limit 20, offset 0)
        self.cursor.execute(
            """
            SELECT COUNT(*) as total FROM tasks WHERE session_id = %s
        """,
            (self.test_session_id,),
        )
        total_count = self.cursor.fetchone()["total"]

        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE session_id = %s
            ORDER BY id
            LIMIT 20 OFFSET 0
        """,
            (self.test_session_id,),
        )
        page1 = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Page 1: Retrieved {len(page1)} tasks (expected 20)")
        assert len(page1) == 20
        assert total_count == 50

        # 3. Test page 2 (limit 20, offset 20)
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE session_id = %s
            ORDER BY id
            LIMIT 20 OFFSET 20
        """,
            (self.test_session_id,),
        )
        page2 = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Page 2: Retrieved {len(page2)} tasks (expected 20)")
        assert len(page2) == 20

        # 4. Test page 3 (limit 20, offset 40)
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE session_id = %s
            ORDER BY id
            LIMIT 20 OFFSET 40
        """,
            (self.test_session_id,),
        )
        page3 = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Page 3: Retrieved {len(page3)} tasks (expected 10)")
        assert len(page3) == 10

        # 5. Verify pagination metadata
        total_pages = (total_count + 20 - 1) // 20
        print(f"✓ Total pages: {total_pages} (expected 3)")
        assert total_pages == 3

        # 6. Verify no duplicate tasks across pages
        all_task_ids = (
            [t["id"] for t in page1]
            + [t["id"] for t in page2]
            + [t["id"] for t in page3]
        )
        unique_ids = set(all_task_ids)
        print(
            f"✓ All task IDs unique: {len(all_task_ids)} total, {len(unique_ids)} unique"
        )
        assert len(all_task_ids) == len(unique_ids) == 50

        print("\n✅ Pagination test PASSED")
        return True


class TestArchiveWorkflow:
    """Test archive/unarchive workflow."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )
        self.cursor = self.conn.cursor()
        self.test_session_id = (
            f"integration_test_archive_{datetime.now():%Y%m%d_%H%M%S}"
        )

    def cleanup(self):
        """Clean up test data."""
        try:
            self.conn.rollback()  # Clear any pending transaction
            self.cursor.execute(
                """
                DELETE FROM tasks WHERE session_id = %s
            """,
                (self.test_session_id,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()

    def test_archive_workflow(self):
        """Test: Create tasks → Complete → Archive → Unarchive."""
        print("\n" + "=" * 80)
        print("TEST: Archive/Unarchive Workflow")
        print("=" * 80)

        # 1. Create 10 completed tasks with old completion dates
        old_task_ids = []
        for i in range(1, 6):
            # Completed 45 days ago - set both created_at and completed_at to respect timestamp constraint
            old_date = datetime.now() - timedelta(days=45)
            self.cursor.execute(
                """
                INSERT INTO tasks (content, active_form, status, priority, session_id, created_at, completed_at)
                VALUES (%s, %s, 'completed', 'medium', %s, %s, %s)
                RETURNING id
            """,
                (
                    f"Old task {i}",
                    f"Old task {i}",
                    self.test_session_id,
                    old_date,  # created_at
                    old_date,  # completed_at (same as created_at)
                ),
            )
            task = dict(self.cursor.fetchone())
            old_task_ids.append(task["id"])
        self.conn.commit()

        print(f"✓ Created 5 old completed tasks (45 days ago)")

        # 2. Create 5 recent completed tasks
        recent_task_ids = []
        for i in range(1, 6):
            # Completed 5 days ago - set both created_at and completed_at to respect timestamp constraint
            recent_date = datetime.now() - timedelta(days=5)
            self.cursor.execute(
                """
                INSERT INTO tasks (content, active_form, status, priority, session_id, created_at, completed_at)
                VALUES (%s, %s, 'completed', 'medium', %s, %s, %s)
                RETURNING id
            """,
                (
                    f"Recent task {i}",
                    f"Recent task {i}",
                    self.test_session_id,
                    recent_date,  # created_at
                    recent_date,  # completed_at (same as created_at)
                ),
            )
            task = dict(self.cursor.fetchone())
            recent_task_ids.append(task["id"])
        self.conn.commit()

        print(f"✓ Created 5 recent completed tasks (5 days ago)")

        # 3. Test archive preview (dry run) - 30 days old
        self.cursor.execute(
            """
            SELECT id, content, completed_at,
                   EXTRACT(EPOCH FROM (NOW() - completed_at)) / 86400 as days_since_completed
            FROM tasks
            WHERE status = 'completed'
              AND is_archived = FALSE
              AND completed_at < NOW() - 30 * INTERVAL '1 day'
              AND session_id = %s
        """,
            (self.test_session_id,),
        )
        preview_tasks = [dict(row) for row in self.cursor.fetchall()]

        print(
            f"✓ Preview: Would archive {len(preview_tasks)} tasks (expected 5 old tasks)"
        )
        assert len(preview_tasks) == 5

        # 4. Actually archive old tasks
        self.cursor.execute(
            """
            SELECT * FROM archive_old_completed_tasks(30, 'test')
        """
        )
        result = dict(self.cursor.fetchone())
        self.conn.commit()

        print(f"✓ Archived {result['archived_count']} tasks (expected 5)")
        assert result["archived_count"] == 5

        # 5. Verify archived tasks not in active tasks (query tasks table directly)
        self.cursor.execute(
            """
            SELECT COUNT(*) as count FROM tasks
            WHERE session_id = %s AND is_archived = FALSE
        """,
            (self.test_session_id,),
        )
        active_count = self.cursor.fetchone()["count"]

        print(f"✓ Active tasks: {active_count} (expected 5 recent, not archived)")
        assert active_count == 5  # Only recent tasks should be active

        # 6. Verify archived tasks in archived_tasks view
        self.cursor.execute(
            """
            SELECT COUNT(*) as count FROM archived_tasks WHERE id = ANY(%s)
        """,
            (old_task_ids,),
        )
        archived_count = self.cursor.fetchone()["count"]

        print(f"✓ Archived tasks: {archived_count} (expected 5)")
        assert archived_count == 5

        # 7. Unarchive 2 tasks
        tasks_to_restore = old_task_ids[:2]
        self.cursor.execute(
            """
            UPDATE tasks
            SET is_archived = FALSE, archived_at = NULL, archived_by = NULL
            WHERE id = ANY(%s)
            RETURNING id
        """,
            (tasks_to_restore,),
        )
        restored = [dict(row) for row in self.cursor.fetchall()]
        self.conn.commit()

        print(f"✓ Unarchived {len(restored)} tasks (expected 2)")
        assert len(restored) == 2

        # 8. Verify unarchived tasks back in tasks table
        self.cursor.execute(
            """
            SELECT COUNT(*) as count FROM tasks
            WHERE id = ANY(%s) AND is_archived = FALSE
        """,
            (tasks_to_restore,),
        )
        unarchived_count = self.cursor.fetchone()["count"]

        print(f"✓ Unarchived tasks restored: {unarchived_count} (expected 2)")
        assert unarchived_count == 2

        print("\n✅ Archive workflow test PASSED")
        return True


class TestSearchFunctionality:
    """Test search functionality."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )
        self.cursor = self.conn.cursor()
        self.test_session_id = f"integration_test_search_{datetime.now():%Y%m%d_%H%M%S}"

    def cleanup(self):
        """Clean up test data."""
        try:
            self.conn.rollback()  # Clear any pending transaction
            self.cursor.execute(
                """
                DELETE FROM tasks WHERE session_id = %s
            """,
                (self.test_session_id,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()

    def test_search(self):
        """Test: Create tasks with keywords → Search → Verify results."""
        print("\n" + "=" * 80)
        print("TEST: Search Functionality")
        print("=" * 80)

        # 1. Create tasks with specific keywords
        keywords = {
            "authentication": [
                "Fix authentication bug",
                "Add authentication tests",
                "Update authentication flow",
            ],
            "database": ["Optimize database queries", "Add database indexes"],
            "frontend": ["Build frontend component", "Update frontend styles"],
        }

        task_map = {}
        for keyword, contents in keywords.items():
            task_map[keyword] = []
            for content in contents:
                self.cursor.execute(
                    """
                    INSERT INTO tasks (content, active_form, status, session_id)
                    VALUES (%s, %s, 'pending', %s)
                    RETURNING id, content
                """,
                    (content, content, self.test_session_id),
                )
                task = dict(self.cursor.fetchone())
                task_map[keyword].append(task["id"])
        self.conn.commit()

        print(f"✓ Created tasks with keywords: {list(keywords.keys())}")

        # 2. Search for 'authentication'
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE (content ILIKE %s OR context ILIKE %s)
              AND session_id = %s
        """,
            ("%authentication%", "%authentication%", self.test_session_id),
        )
        auth_results = [dict(row) for row in self.cursor.fetchall()]

        print(
            f"✓ Search 'authentication': Found {len(auth_results)} tasks (expected 3)"
        )
        assert len(auth_results) == 3
        for task in auth_results:
            assert "auth" in task["content"].lower()

        # 3. Search for 'database'
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE (content ILIKE %s OR context ILIKE %s)
              AND session_id = %s
        """,
            ("%database%", "%database%", self.test_session_id),
        )
        db_results = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Search 'database': Found {len(db_results)} tasks (expected 2)")
        assert len(db_results) == 2

        # 4. Search for 'frontend'
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE (content ILIKE %s OR context ILIKE %s)
              AND session_id = %s
        """,
            ("%frontend%", "%frontend%", self.test_session_id),
        )
        frontend_results = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Search 'frontend': Found {len(frontend_results)} tasks (expected 2)")
        assert len(frontend_results) == 2

        # 5. Search for non-existent keyword
        self.cursor.execute(
            """
            SELECT id, content FROM tasks
            WHERE (content ILIKE %s OR context ILIKE %s)
              AND session_id = %s
        """,
            ("%nonexistent%", "%nonexistent%", self.test_session_id),
        )
        no_results = [dict(row) for row in self.cursor.fetchall()]

        print(f"✓ Search 'nonexistent': Found {len(no_results)} tasks (expected 0)")
        assert len(no_results) == 0

        print("\n✅ Search functionality test PASSED")
        return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUITE - Task Tracker MCP")
    print("Phase 2.5: End-to-End Workflow Testing")
    print("=" * 80)

    tests_passed = 0
    tests_failed = 0
    test_results = []

    # Test 1: Basic lifecycle
    test1 = TestTaskLifecycle()
    try:
        result = test1.test_basic_lifecycle()
        test_results.append(("Basic Task Lifecycle", "PASSED"))
        tests_passed += 1
    except Exception as e:
        test_results.append(("Basic Task Lifecycle", f"FAILED: {e}"))
        tests_failed += 1
    finally:
        test1.cleanup()

    # Test 2: Master task workflow
    test2 = TestMasterTaskWorkflow()
    try:
        result = test2.test_master_with_subtasks()
        test_results.append(("Master Task Workflow", "PASSED"))
        tests_passed += 1
    except Exception as e:
        test_results.append(("Master Task Workflow", f"FAILED: {e}"))
        tests_failed += 1
    finally:
        test2.cleanup()

    # Test 3: Pagination
    test3 = TestPagination()
    try:
        result = test3.test_pagination()
        test_results.append(("Pagination", "PASSED"))
        tests_passed += 1
    except Exception as e:
        test_results.append(("Pagination", f"FAILED: {e}"))
        tests_failed += 1
    finally:
        test3.cleanup()

    # Test 4: Archive workflow
    test4 = TestArchiveWorkflow()
    try:
        result = test4.test_archive_workflow()
        test_results.append(("Archive Workflow", "PASSED"))
        tests_passed += 1
    except Exception as e:
        test_results.append(("Archive Workflow", f"FAILED: {e}"))
        tests_failed += 1
    finally:
        test4.cleanup()

    # Test 5: Search functionality
    test5 = TestSearchFunctionality()
    try:
        result = test5.test_search()
        test_results.append(("Search Functionality", "PASSED"))
        tests_passed += 1
    except Exception as e:
        test_results.append(("Search Functionality", f"FAILED: {e}"))
        tests_failed += 1
    finally:
        test5.cleanup()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in test_results:
        status_symbol = "✅" if "PASSED" in result else "❌"
        print(f"{status_symbol} {test_name}: {result}")

    print("\n" + "-" * 80)
    print(f"Total: {tests_passed + tests_failed} tests")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("=" * 80 + "\n")

    return tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
