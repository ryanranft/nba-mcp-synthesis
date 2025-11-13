#!/usr/bin/env python3
"""
Task Tracker MCP Server

Persistent task tracking across Claude Code sessions using PostgreSQL.
Part of: Automatic Task Tracking System (Phase 3)

Built with FastMCP framework.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import uuid

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
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Task Tracker")

# Global connection pool (simple implementation)
_db_connection = None

# Generate unique session ID on server startup
SESSION_ID = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
print(f"[Task Tracker MCP] Session ID: {SESSION_ID}", file=sys.stderr)


def get_db_connection():
    """Get database connection (with simple connection reuse)."""
    global _db_connection

    # Load credentials if not already loaded
    if not os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW"):
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

    db_config = get_database_config()

    # Create new connection if needed
    if _db_connection is None or _db_connection.closed:
        _db_connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database="claude_tasks",
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )

    return _db_connection


def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())[:8]


@mcp.tool()
def create_task(
    content: str,
    active_form: str,
    priority: str = "medium",
    context: Optional[str] = None,
    tags: Optional[List[str]] = None,
    parent_task_id: Optional[int] = None,
    master_task_id: Optional[int] = None,
    task_type: str = "task",
    estimated_duration_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a new task.

    Args:
        content: Task description (imperative form, e.g., "Run tests")
        active_form: Active form (e.g., "Running tests")
        priority: Task priority (low, medium, high, critical)
        context: Additional context about the task
        tags: List of tags for categorization
        parent_task_id: Parent task ID if this is a sub-task
        master_task_id: Master task ID (for associating with large initiatives)
        task_type: Type of task (master, task, subtask)
        estimated_duration_minutes: Estimated time to complete

    Returns:
        Dictionary with created task details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Calculate depth level if parent_task_id provided
        depth_level = 0
        if parent_task_id:
            cursor.execute(
                "SELECT depth_level FROM tasks WHERE id = %s", (parent_task_id,)
            )
            parent = cursor.fetchone()
            if parent:
                depth_level = parent["depth_level"] + 1

        # Insert task
        cursor.execute(
            """
            INSERT INTO tasks
            (content, active_form, status, priority, context, parent_task_id, master_task_id,
             task_type, depth_level, estimated_duration_minutes, session_id)
            VALUES (%s, %s, 'pending', %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, content, active_form, status, priority, task_type, created_at
        """,
            (
                content,
                active_form,
                priority,
                context,
                parent_task_id,
                master_task_id,
                task_type,
                depth_level,
                estimated_duration_minutes,
                SESSION_ID,
            ),
        )

        task = dict(cursor.fetchone())
        task_id = task["id"]

        # Add tags if provided
        if tags:
            for tag in tags:
                cursor.execute(
                    """
                    INSERT INTO task_tags (task_id, tag)
                    VALUES (%s, %s)
                    ON CONFLICT (task_id, tag) DO NOTHING
                """,
                    (task_id, tag.lower()),
                )

        conn.commit()

        return {
            "success": True,
            "task": task,
            "message": f"Task {task_id} created successfully",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    master_task_id: Optional[int] = None,
    task_type: Optional[str] = None,
    tag: Optional[str] = None,
    stale_days: Optional[int] = None,
    sort_by: Optional[str] = None,
    view: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List tasks with advanced filtering, sorting, and saved views.

    Phase 3 UX Enhancement: Smart filters and discovery.

    Args:
        status: Filter by status (pending, in_progress, completed, blocked, cancelled)
        priority: Filter by priority (low, medium, high, critical)
        master_task_id: Filter by master task (show only tasks for this master)
        task_type: Filter by task type (master, task, subtask)
        tag: Filter by tag (tasks with this tag)
        stale_days: Filter by staleness (not worked on in X days)
        sort_by: Sort order - priority, staleness, progress, created, updated (default: status+priority)
        view: Saved view - focus, blocked, stale, active (overrides other filters)
        limit: Maximum number of tasks to return (default: 50)
        offset: Number of tasks to skip (for pagination, default: 0)

    Returns:
        Dictionary with list of tasks and pagination metadata

    Examples:
        # Stale tasks (not worked on in 3+ days)
        list_tasks(stale_days=3)

        # Blocked tasks
        list_tasks(status="blocked")

        # High priority tasks
        list_tasks(priority="high")

        # Tasks with specific tag
        list_tasks(tag="sprint-15")

        # Focus view (high priority + in progress)
        list_tasks(view="focus")

        # Sort by staleness
        list_tasks(sort_by="staleness")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # PHASE 3 ENHANCEMENT: Apply saved view presets
        if view:
            if view == "focus":
                # High priority + in progress
                priority = "high"
                status = "in_progress"
            elif view == "blocked":
                status = "blocked"
            elif view == "stale":
                stale_days = 3
            elif view == "active":
                # Pending or in progress (exclude completed/cancelled)
                status = None  # Will be handled by NOT IN clause below
            else:
                return {
                    "success": False,
                    "error": f"Invalid view. Must be one of: focus, blocked, stale, active",
                }

        # Build base query for counting total
        count_query = "SELECT COUNT(DISTINCT t.id) as total FROM tasks t"

        # PHASE 3 ENHANCEMENT: Join with tags if filtering by tag
        if tag:
            count_query = "SELECT COUNT(DISTINCT t.id) as total FROM tasks t INNER JOIN task_tags tt ON t.id = tt.task_id"
        else:
            count_query = "SELECT COUNT(DISTINCT t.id) as total FROM tasks t"

        conditions = []
        params = []

        # Existing filters
        if status:
            conditions.append("t.status = %s")
            params.append(status)

        if priority:
            conditions.append("t.priority = %s")
            params.append(priority)

        if master_task_id is not None:
            conditions.append("t.master_task_id = %s")
            params.append(master_task_id)

        if task_type:
            conditions.append("t.task_type = %s")
            params.append(task_type)

        # PHASE 3 ENHANCEMENT: New filters
        if tag:
            conditions.append("tt.tag = %s")
            params.append(tag)

        if stale_days is not None:
            # Tasks not worked on in X days
            conditions.append(
                "(t.last_worked_at IS NULL OR t.last_worked_at < NOW() - INTERVAL '%s days')"
            )
            params.append(stale_days)

        # PHASE 3 ENHANCEMENT: Active view (exclude completed/cancelled)
        if view == "active":
            conditions.append("t.status NOT IN ('completed', 'cancelled')")

        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)

        # Get total count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["total"]

        # Build main query with staleness calculation
        query = """
            SELECT
                t.id,
                t.content,
                t.active_form,
                t.status,
                t.priority,
                t.context,
                t.task_type,
                t.parent_task_id,
                t.master_task_id,
                t.depth_level,
                t.created_at,
                t.updated_at,
                t.started_at,
                t.completed_at,
                t.last_worked_at,
                t.estimated_duration_minutes,
                t.actual_duration_minutes,
                EXTRACT(EPOCH FROM (NOW() - COALESCE(t.last_worked_at, t.created_at))) / 3600 as hours_since_worked,
                ARRAY_AGG(DISTINCT tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags
            FROM tasks t
            LEFT JOIN task_tags tt ON t.id = tt.task_id
        """

        # PHASE 3: If filtering by tag, use INNER JOIN
        if tag:
            query = query.replace("LEFT JOIN task_tags tt", "INNER JOIN task_tags tt")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY t.id"

        # PHASE 3 ENHANCEMENT: Sort options
        if sort_by == "priority":
            query += """
                ORDER BY
                    CASE t.priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    t.created_at DESC
            """
        elif sort_by == "staleness":
            query += """
                ORDER BY
                    COALESCE(t.last_worked_at, t.created_at) ASC,
                    t.priority DESC
            """
        elif sort_by == "created":
            query += " ORDER BY t.created_at DESC"
        elif sort_by == "updated":
            query += " ORDER BY t.updated_at DESC"
        elif sort_by == "progress":
            # For master tasks, sort by completion percentage
            query += """
                ORDER BY
                    CASE t.task_type WHEN 'master' THEN 1 ELSE 2 END,
                    t.created_at DESC
            """
        else:
            # Default: status-based ordering + priority
            query += """
                ORDER BY
                    CASE t.status
                        WHEN 'in_progress' THEN 1
                        WHEN 'pending' THEN 2
                        WHEN 'blocked' THEN 3
                        WHEN 'completed' THEN 4
                        WHEN 'cancelled' THEN 5
                    END,
                    CASE t.priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    t.created_at DESC
            """

        query += " LIMIT %s OFFSET %s"

        # Add limit and offset to params
        query_params = params + [limit, offset]

        cursor.execute(query, query_params)
        tasks = [dict(row) for row in cursor.fetchall()]

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        current_page = (offset // limit) + 1
        has_more = offset + len(tasks) < total_count

        return {
            "success": True,
            "tasks": tasks,
            "pagination": {
                "total_count": total_count,
                "count": len(tasks),
                "limit": limit,
                "offset": offset,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_more": has_more,
                "has_previous": offset > 0,
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def update_task_status(
    task_id: int, status: str, notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update task status.

    Args:
        task_id: ID of the task to update
        status: New status (pending, in_progress, completed, blocked, cancelled)
        notes: Optional notes about the status change

    Returns:
        Dictionary with updated task details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update task
        cursor.execute(
            """
            UPDATE tasks
            SET status = %s, notes = COALESCE(%s, notes)
            WHERE id = %s
            RETURNING id, content, active_form, status, priority, updated_at
        """,
            (status, notes, task_id),
        )

        task = cursor.fetchone()

        if task is None:
            return {"success": False, "error": f"Task {task_id} not found"}

        task = dict(task)
        conn.commit()

        return {
            "success": True,
            "task": task,
            "message": f"Task {task_id} status updated to {status}",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def bulk_update_status(
    task_ids: List[int], status: str, notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update status for multiple tasks at once.

    Phase 3 UX Enhancement: Bulk operation for efficiency.

    Args:
        task_ids: List of task IDs to update
        status: New status (pending, in_progress, completed, blocked, cancelled)
        notes: Optional notes to add to all tasks

    Returns:
        Dictionary with update results

    Example:
        bulk_update_status([45, 46, 47], "completed", "Finished all related tasks")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if not task_ids:
            return {"success": False, "error": "No task IDs provided"}

        # Validate status
        valid_statuses = ["pending", "in_progress", "completed", "blocked", "cancelled"]
        if status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            }

        # Update all tasks
        cursor.execute(
            """
            UPDATE tasks
            SET status = %s,
                notes = CASE
                    WHEN %s IS NOT NULL THEN COALESCE(notes || E'\n' || %s, %s)
                    ELSE notes
                END
            WHERE id = ANY(%s)
            RETURNING id, content, status, priority
        """,
            (status, notes, notes, notes, task_ids),
        )

        updated_tasks = [dict(row) for row in cursor.fetchall()]

        if not updated_tasks:
            return {"success": False, "error": "No tasks found with the provided IDs"}

        conn.commit()

        # If completing tasks, check for parent/master tasks to update progress
        if status == "completed":
            master_ids = set()
            for task in updated_tasks:
                cursor.execute(
                    """
                    SELECT master_task_id, parent_task_id
                    FROM tasks
                    WHERE id = %s
                """,
                    (task["id"],),
                )
                row = cursor.fetchone()
                if row:
                    row = dict(row)
                    if row["master_task_id"]:
                        master_ids.add(row["master_task_id"])
                    if row["parent_task_id"]:
                        master_ids.add(row["parent_task_id"])

            # Calculate updated completion percentages
            progress_updates = {}
            for master_id in master_ids:
                cursor.execute(
                    """
                    SELECT calculate_completion_percentage(%s) as percentage
                """,
                    (master_id,),
                )
                pct = cursor.fetchone()["percentage"]
                progress_updates[master_id] = pct

            conn.commit()

            return {
                "success": True,
                "updated_count": len(updated_tasks),
                "tasks": updated_tasks,
                "master_progress_updates": progress_updates,
                "message": f"Successfully updated {len(updated_tasks)} task(s) to status '{status}'",
            }

        return {
            "success": True,
            "updated_count": len(updated_tasks),
            "tasks": updated_tasks,
            "message": f"Successfully updated {len(updated_tasks)} task(s) to status '{status}'",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def bulk_update_priority(task_ids: List[int], priority: str) -> Dict[str, Any]:
    """
    Update priority for multiple tasks at once.

    Phase 3 UX Enhancement: Bulk priority management.

    Args:
        task_ids: List of task IDs to update
        priority: New priority (low, medium, high, critical)

    Returns:
        Dictionary with update results

    Example:
        bulk_update_priority([12, 13, 14], "high")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if not task_ids:
            return {"success": False, "error": "No task IDs provided"}

        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            return {
                "success": False,
                "error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}",
            }

        # Update all tasks
        cursor.execute(
            """
            UPDATE tasks
            SET priority = %s
            WHERE id = ANY(%s)
            RETURNING id, content, status, priority
        """,
            (priority, task_ids),
        )

        updated_tasks = [dict(row) for row in cursor.fetchall()]

        if not updated_tasks:
            return {"success": False, "error": "No tasks found with the provided IDs"}

        conn.commit()

        return {
            "success": True,
            "updated_count": len(updated_tasks),
            "tasks": updated_tasks,
            "message": f"Successfully updated {len(updated_tasks)} task(s) to priority '{priority}'",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def bulk_add_tags(task_ids: List[int], tags: List[str]) -> Dict[str, Any]:
    """
    Add tags to multiple tasks at once.

    Phase 3 UX Enhancement: Bulk tagging for organization.

    Args:
        task_ids: List of task IDs to tag
        tags: List of tags to add (e.g., ["bug", "frontend", "urgent"])

    Returns:
        Dictionary with update results

    Example:
        bulk_add_tags([45, 46, 47], ["sprint-3", "backend", "api"])
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if not task_ids:
            return {"success": False, "error": "No task IDs provided"}

        if not tags:
            return {"success": False, "error": "No tags provided"}

        # Verify tasks exist
        cursor.execute(
            """
            SELECT id, content FROM tasks WHERE id = ANY(%s)
        """,
            (task_ids,),
        )
        existing_tasks = [dict(row) for row in cursor.fetchall()]

        if not existing_tasks:
            return {"success": False, "error": "No tasks found with the provided IDs"}

        # Add tags to all tasks
        tags_added = 0
        for task_id in task_ids:
            for tag in tags:
                cursor.execute(
                    """
                    INSERT INTO task_tags (task_id, tag)
                    VALUES (%s, %s)
                    ON CONFLICT (task_id, tag) DO NOTHING
                """,
                    (task_id, tag.strip().lower()),
                )
                if cursor.rowcount > 0:
                    tags_added += 1

        conn.commit()

        # Get updated tag counts for each task
        cursor.execute(
            """
            SELECT task_id, array_agg(tag) as tags
            FROM task_tags
            WHERE task_id = ANY(%s)
            GROUP BY task_id
        """,
            (task_ids,),
        )
        tag_counts = {row["task_id"]: row["tags"] for row in cursor.fetchall()}

        return {
            "success": True,
            "updated_count": len(existing_tasks),
            "tags_added": tags_added,
            "tasks": existing_tasks,
            "tag_counts": tag_counts,
            "message": f"Successfully added {tags_added} tag(s) to {len(existing_tasks)} task(s)",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_active_tasks() -> Dict[str, Any]:
    """
    Get all active tasks (pending or in_progress).

    Returns:
        Dictionary with list of active tasks
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM active_tasks")
        tasks = [dict(row) for row in cursor.fetchall()]

        # Count by status
        pending = sum(1 for t in tasks if t["status"] == "pending")
        in_progress = sum(1 for t in tasks if t["status"] == "in_progress")

        return {
            "success": True,
            "tasks": tasks,
            "summary": {
                "total": len(tasks),
                "pending": pending,
                "in_progress": in_progress,
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_task_statistics() -> Dict[str, Any]:
    """
    Get task statistics.

    Returns:
        Dictionary with task statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM task_statistics")
        stats = dict(cursor.fetchone())

        return {"success": True, "statistics": stats}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_task_history(task_id: int) -> Dict[str, Any]:
    """
    Get history of status changes for a task.

    Args:
        task_id: ID of the task

    Returns:
        Dictionary with task history
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, previous_status, new_status, changed_at, changed_by, notes
            FROM task_history
            WHERE task_id = %s
            ORDER BY changed_at DESC
        """,
            (task_id,),
        )

        history = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "task_id": task_id,
            "history": history,
            "count": len(history),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_handoff_document(
    title: str,
    content: str,
    task_ids: Optional[List[int]] = None,
    expires_in_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a handoff document for complex multi-session work.

    Args:
        title: Title of the handoff document
        content: Content of the handoff (markdown format)
        task_ids: List of related task IDs
        expires_in_days: Number of days until expiration (optional)

    Returns:
        Dictionary with created handoff document details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        cursor.execute(
            """
            INSERT INTO handoff_documents (title, content, task_ids, expires_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, created_at, expires_at
        """,
            (title, content, task_ids or [], expires_at),
        )

        handoff = dict(cursor.fetchone())
        conn.commit()

        return {
            "success": True,
            "handoff": handoff,
            "message": f"Handoff document {handoff['id']} created successfully",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_active_handoffs() -> Dict[str, Any]:
    """
    Get all active handoff documents.

    Returns:
        Dictionary with list of active handoff documents
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, title, content, task_ids, created_at, expires_at
            FROM handoff_documents
            WHERE is_active = TRUE
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
        """
        )

        handoffs = [dict(row) for row in cursor.fetchall()]

        return {"success": True, "handoffs": handoffs, "count": len(handoffs)}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_task_tags(task_id: int, tags: List[str]) -> Dict[str, Any]:
    """
    Add tags to a task.

    Args:
        task_id: ID of the task
        tags: List of tags to add

    Returns:
        Dictionary with result
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for tag in tags:
            cursor.execute(
                """
                INSERT INTO task_tags (task_id, tag)
                VALUES (%s, %s)
                ON CONFLICT (task_id, tag) DO NOTHING
            """,
                (task_id, tag.lower()),
            )

        conn.commit()

        return {"success": True, "message": f"Tags added to task {task_id}"}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_tasks(query: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Search tasks by content or context with pagination.

    Args:
        query: Search query
        limit: Maximum number of results (default: 20)
        offset: Number of results to skip (for pagination, default: 0)

    Returns:
        Dictionary with matching tasks and pagination metadata
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get total count
        cursor.execute(
            """
            SELECT COUNT(*) as total
            FROM tasks t
            WHERE t.content ILIKE %s OR t.context ILIKE %s
        """,
            (f"%{query}%", f"%{query}%"),
        )

        total_count = cursor.fetchone()["total"]

        # Get paginated results
        cursor.execute(
            """
            SELECT
                t.id,
                t.content,
                t.active_form,
                t.status,
                t.priority,
                t.context,
                t.created_at,
                ARRAY_AGG(tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags
            FROM tasks t
            LEFT JOIN task_tags tt ON t.id = tt.task_id
            WHERE t.content ILIKE %s OR t.context ILIKE %s
            GROUP BY t.id
            ORDER BY t.created_at DESC
            LIMIT %s OFFSET %s
        """,
            (f"%{query}%", f"%{query}%", limit, offset),
        )

        tasks = [dict(row) for row in cursor.fetchall()]

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        current_page = (offset // limit) + 1
        has_more = offset + len(tasks) < total_count

        return {
            "success": True,
            "tasks": tasks,
            "query": query,
            "pagination": {
                "total_count": total_count,
                "count": len(tasks),
                "limit": limit,
                "offset": offset,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_more": has_more,
                "has_previous": offset > 0,
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_master_task(
    title: str,
    context_summary: str,
    subtasks: List[Dict[str, str]],
    priority: str = "high",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a master task with subtasks in one operation.

    Args:
        title: Master task title
        context_summary: Brief description of the initiative
        subtasks: List of subtask definitions with 'content' and 'active_form'
        priority: Master task priority
        tags: Tags for categorization

    Returns:
        Dictionary with created master task and all subtasks
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create master task
        cursor.execute(
            """
            INSERT INTO tasks
            (content, active_form, status, priority, task_type, context_summary, depth_level, session_id)
            VALUES (%s, %s, 'pending', %s, 'master', %s, 0, %s)
            RETURNING id, content, active_form, status, priority, task_type, created_at
        """,
            (title, f"Working on {title}", priority, context_summary, SESSION_ID),
        )

        master_task = dict(cursor.fetchone())
        master_id = master_task["id"]

        # Add tags to master task
        if tags:
            for tag in tags:
                cursor.execute(
                    """
                    INSERT INTO task_tags (task_id, tag)
                    VALUES (%s, %s)
                    ON CONFLICT (task_id, tag) DO NOTHING
                """,
                    (master_id, tag.lower()),
                )

        # Create subtasks
        created_subtasks = []
        for subtask in subtasks:
            cursor.execute(
                """
                INSERT INTO tasks
                (content, active_form, status, priority, parent_task_id, master_task_id,
                 task_type, depth_level, session_id)
                VALUES (%s, %s, 'pending', %s, %s, %s, 'task', 1, %s)
                RETURNING id, content, active_form, status, priority
            """,
                (
                    subtask.get("content"),
                    subtask.get("active_form"),
                    subtask.get("priority", "medium"),
                    master_id,
                    master_id,
                    SESSION_ID,
                ),
            )
            created_subtasks.append(dict(cursor.fetchone()))

        conn.commit()

        return {
            "success": True,
            "master_task": master_task,
            "subtasks": created_subtasks,
            "message": f"Master task {master_id} created with {len(created_subtasks)} subtasks",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_master_tasks_with_progress(
    include_completed: bool = False, limit: int = 20
) -> Dict[str, Any]:
    """
    Get all master tasks with completion percentage and progress.

    Args:
        include_completed: Include completed master tasks
        limit: Maximum number to return

    Returns:
        List of master tasks with progress metrics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM master_tasks_progress"

        if not include_completed:
            query += " WHERE master_status != 'completed'"

        query += f" LIMIT {limit}"

        cursor.execute(query)
        masters = [dict(row) for row in cursor.fetchall()]

        # Format for display
        for master in masters:
            if master.get("hours_since_last_worked") is not None:
                hours = master["hours_since_last_worked"]
                if hours < 24:
                    master["last_worked_display"] = f"{hours:.1f} hours ago"
                else:
                    days = hours / 24
                    master["last_worked_display"] = f"{days:.1f} days ago"
            else:
                master["last_worked_display"] = "Never"

        return {"success": True, "master_tasks": masters, "count": len(masters)}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_task_hierarchy(task_id: int, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """
    Get complete hierarchy for a task (all descendants).

    Args:
        task_id: Root task ID
        max_depth: Maximum depth to traverse (None = unlimited)

    Returns:
        Nested hierarchy with all children
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call PostgreSQL function
        cursor.execute("SELECT * FROM get_task_hierarchy(%s, %s)", (task_id, max_depth))

        hierarchy = [dict(row) for row in cursor.fetchall()]

        # Build nested structure
        def build_tree(items, parent_id=None):
            """Recursively build tree structure."""
            tree = []
            for item in items:
                if (parent_id is None and item["parent_id"] is None) or (
                    item["parent_id"] == parent_id
                ):
                    node = dict(item)
                    children = build_tree(items, item["task_id"])
                    if children:
                        node["children"] = children
                    tree.append(node)
            return tree

        # Get root task
        root = [h for h in hierarchy if h["depth"] == 0]
        if not root:
            return {"success": False, "error": f"Task {task_id} not found"}

        nested = build_tree(hierarchy)

        return {
            "success": True,
            "root_task_id": task_id,
            "hierarchy": nested[0] if nested else {},
            "total_descendants": len(hierarchy) - 1,  # Exclude root
            "max_depth": max([h["depth"] for h in hierarchy]),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def calculate_completion_percentage(task_id: int) -> Dict[str, Any]:
    """
    Calculate completion percentage for a task and all descendants.

    Args:
        task_id: Task ID (typically master task)

    Returns:
        Completion stats (completed/total/percentage)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call PostgreSQL function
        cursor.execute("SELECT * FROM calculate_completion_percentage(%s)", (task_id,))

        stats = dict(cursor.fetchone())

        return {
            "success": True,
            "task_id": task_id,
            "total_tasks": stats["total_tasks"],
            "completed_tasks": stats["completed_tasks"],
            "in_progress_tasks": stats["in_progress_tasks"],
            "pending_tasks": stats["pending_tasks"],
            "completion_percentage": float(stats["completion_percentage"]),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def update_context_summary(task_id: int, context_summary: str) -> Dict[str, Any]:
    """
    Update context summary for a task (typically master tasks).

    Args:
        task_id: Task ID
        context_summary: New context summary

    Returns:
        Updated task
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE tasks
            SET context_summary = %s
            WHERE id = %s
            RETURNING id, content, context_summary, task_type
        """,
            (context_summary, task_id),
        )

        task = cursor.fetchone()

        if task is None:
            return {"success": False, "error": f"Task {task_id} not found"}

        task = dict(task)
        conn.commit()

        return {
            "success": True,
            "task": task,
            "message": f"Context summary updated for task {task_id}",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_resume_view() -> Dict[str, Any]:
    """
    Get resume-style view of all active projects.

    Shows:
    - Master tasks with completion percentages
    - Last worked-on task (highlighted)
    - Time since last worked on each project
    - Context summaries

    Returns:
        Formatted resume view data
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all master tasks with progress
        cursor.execute("SELECT * FROM master_tasks_progress LIMIT 50")
        projects = [dict(row) for row in cursor.fetchall()]

        # Format display
        for project in projects:
            # Format time since last worked
            if project.get("hours_since_last_worked") is not None:
                hours = project["hours_since_last_worked"]
                if hours < 1:
                    minutes = hours * 60
                    project["last_worked_display"] = f"{minutes:.0f} minutes ago"
                elif hours < 24:
                    project["last_worked_display"] = f"{hours:.1f} hours ago"
                else:
                    days = hours / 24
                    project["last_worked_display"] = f"{days:.1f} days ago"
            else:
                project["last_worked_display"] = "Never worked on"

            # Format days since created
            if project.get("days_since_created") is not None:
                days = project["days_since_created"]
                if days < 1:
                    project["created_display"] = "Today"
                elif days < 2:
                    project["created_display"] = "Yesterday"
                else:
                    project["created_display"] = f"{days:.0f} days ago"
            else:
                project["created_display"] = "Unknown"

            # Format status emoji
            if project["master_status"] == "in_progress":
                project["status_emoji"] = "🔄"
            elif project["master_status"] == "completed":
                project["status_emoji"] = "✅"
            elif project["master_status"] == "blocked":
                project["status_emoji"] = "🚫"
            else:
                project["status_emoji"] = "⏸️"

            # Progress bar
            pct = project["completion_percentage"]
            filled = int(pct / 10)
            empty = 10 - filled
            project["progress_bar"] = "█" * filled + "░" * empty

        # Get overall statistics
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE task_type = 'master') as total_projects,
                COUNT(*) FILTER (WHERE task_type IN ('task', 'subtask')) as total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed' AND task_type IN ('task', 'subtask')) as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'in_progress') as active_tasks
            FROM tasks
        """
        )
        stats = dict(cursor.fetchone())

        return {
            "success": True,
            "projects": projects,
            "statistics": stats,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_resume_view_enhanced() -> Dict[str, Any]:
    """
    Enhanced resume view with color-coded progress, staleness warnings, and velocity indicators.

    Phase 3 UX Enhancement: Improved visual resume view with:
    - 🟢 Green progress (>75% complete)
    - 🟡 Yellow progress (25-75% complete)
    - 🔴 Red progress (<25% complete or stale >7 days)
    - 🟡 Staleness warning (>3 days inactive)
    - 📈 Velocity trending up
    - 📉 Velocity trending down
    - Interactive numbered menu for quick project selection

    Returns:
        Enhanced resume view data with visual enhancements
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all master tasks with progress
        cursor.execute("SELECT * FROM master_tasks_progress LIMIT 50")
        projects = [dict(row) for row in cursor.fetchall()]

        # Format display with enhancements
        for idx, project in enumerate(projects, 1):
            # Add project number for quick selection
            project["project_number"] = idx

            # Format time since last worked
            if project.get("hours_since_last_worked") is not None:
                hours = project["hours_since_last_worked"]
                if hours < 1:
                    minutes = hours * 60
                    project["last_worked_display"] = f"{minutes:.0f} minutes ago"
                elif hours < 24:
                    project["last_worked_display"] = f"{hours:.1f} hours ago"
                else:
                    days = hours / 24
                    project["last_worked_display"] = f"{days:.1f} days ago"
            else:
                project["last_worked_display"] = "Never worked on"
                hours = 999999  # Very stale if never worked

            # Format days since created
            if project.get("days_since_created") is not None:
                days = project["days_since_created"]
                if days < 1:
                    project["created_display"] = "Today"
                elif days < 2:
                    project["created_display"] = "Yesterday"
                else:
                    project["created_display"] = f"{days:.0f} days ago"
            else:
                project["created_display"] = "Unknown"

            # Format status emoji
            if project["master_status"] == "in_progress":
                project["status_emoji"] = "🔄"
            elif project["master_status"] == "completed":
                project["status_emoji"] = "✅"
            elif project["master_status"] == "blocked":
                project["status_emoji"] = "🚫"
            else:
                project["status_emoji"] = "⏸️"

            # ENHANCEMENT: Staleness warning indicators
            if project.get("hours_since_last_worked") is not None:
                hours = project["hours_since_last_worked"]
                if hours > 168:  # >7 days
                    project["staleness_indicator"] = "🔴 STALE"
                    project["staleness_level"] = "critical"
                elif hours > 72:  # >3 days
                    project["staleness_indicator"] = "🟡 WARNING"
                    project["staleness_level"] = "warning"
                else:
                    project["staleness_indicator"] = "✨ ACTIVE"
                    project["staleness_level"] = "active"
            else:
                project["staleness_indicator"] = "🔴 NEVER STARTED"
                project["staleness_level"] = "critical"

            # ENHANCEMENT: Color-coded progress bar
            pct = project["completion_percentage"]
            filled = int(pct / 10)
            empty = 10 - filled
            base_bar = "█" * filled + "░" * empty

            # Determine color based on progress and staleness
            if pct >= 75:
                project["progress_color"] = "🟢"  # Green - excellent progress
                project["progress_level"] = "excellent"
            elif pct >= 25:
                project["progress_color"] = "🟡"  # Yellow - moderate progress
                project["progress_level"] = "moderate"
            else:
                project["progress_color"] = "🔴"  # Red - needs attention
                project["progress_level"] = "needs_attention"

            # Override to red if critically stale
            if project["staleness_level"] == "critical" and pct < 100:
                project["progress_color"] = "🔴"
                project["progress_level"] = "needs_attention"

            project["progress_bar"] = base_bar
            project["progress_bar_colored"] = (
                f"{project['progress_color']} [{base_bar}]"
            )

            # ENHANCEMENT: Velocity indicators
            # Calculate velocity by comparing completion % to time elapsed
            if project.get("days_since_created") and project["days_since_created"] > 0:
                days_elapsed = project["days_since_created"]
                velocity = pct / days_elapsed  # % complete per day

                # Determine trend based on recent activity
                if project.get("hours_since_last_worked") is not None:
                    hours_inactive = project["hours_since_last_worked"]

                    if hours_inactive < 24 and velocity > 5:  # Active and fast
                        project["velocity_indicator"] = "📈 TRENDING UP"
                        project["velocity_level"] = "up"
                    elif hours_inactive > 72 or velocity < 2:  # Slow or stale
                        project["velocity_indicator"] = "📉 TRENDING DOWN"
                        project["velocity_level"] = "down"
                    else:  # Moderate
                        project["velocity_indicator"] = "➡️  STEADY"
                        project["velocity_level"] = "steady"
                else:
                    project["velocity_indicator"] = "⏸️  NOT STARTED"
                    project["velocity_level"] = "not_started"

                project["velocity_value"] = f"{velocity:.1f}%/day"
            else:
                project["velocity_indicator"] = "➡️  NEW"
                project["velocity_level"] = "new"
                project["velocity_value"] = "N/A"

            # ENHANCEMENT: Suggested action based on project state
            if project["staleness_level"] == "critical" and pct < 100:
                project["suggested_action"] = "Resume this stale project immediately"
            elif project["progress_level"] == "excellent" and pct < 100:
                project["suggested_action"] = "Nearly complete - finish this project"
            elif project["master_status"] == "in_progress":
                project["suggested_action"] = "Continue current work"
            elif project["master_status"] == "blocked":
                project["suggested_action"] = "Resolve blockers"
            else:
                project["suggested_action"] = "Start working on pending tasks"

        # Get overall statistics
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE task_type = 'master') as total_projects,
                COUNT(*) FILTER (WHERE task_type IN ('task', 'subtask')) as total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed' AND task_type IN ('task', 'subtask')) as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'in_progress') as active_tasks
            FROM tasks
        """
        )
        stats = dict(cursor.fetchone())

        # ENHANCEMENT: Calculate project health metrics
        total_active_projects = len(
            [p for p in projects if p["master_status"] != "completed"]
        )
        stale_projects = len(
            [p for p in projects if p["staleness_level"] == "critical"]
        )
        blocked_projects = len([p for p in projects if p["master_status"] == "blocked"])

        health_metrics = {
            "total_active": total_active_projects,
            "stale_count": stale_projects,
            "blocked_count": blocked_projects,
            "health_score": max(
                0, 100 - (stale_projects * 20) - (blocked_projects * 15)
            ),
        }

        # ENHANCEMENT: Priority recommendations
        # Sort projects by priority (stale > blocked > in_progress > high completion)
        priority_order = []
        for p in projects:
            if p["staleness_level"] == "critical" and p["master_status"] != "completed":
                priority_order.append((p, 4))  # Highest priority
            elif p["master_status"] == "blocked":
                priority_order.append((p, 3))
            elif p["master_status"] == "in_progress":
                priority_order.append((p, 2))
            elif p["completion_percentage"] >= 75 and p["master_status"] != "completed":
                priority_order.append((p, 2))  # Almost done
            else:
                priority_order.append((p, 1))

        priority_order.sort(key=lambda x: x[1], reverse=True)
        recommended_next = priority_order[0][0] if priority_order else None

        return {
            "success": True,
            "projects": projects,
            "statistics": stats,
            "health_metrics": health_metrics,
            "recommended_next_project": recommended_next,
            "generated_at": datetime.now().isoformat(),
            "enhancement_version": "3.0",
            "features": [
                "color_coded_progress",
                "staleness_warnings",
                "velocity_indicators",
                "interactive_menu",
                "priority_recommendations",
            ],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def sync_todowrite_tasks(
    todos: List[Dict[str, str]], session_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync TodoWrite tasks to persistent storage.

    Allows users to persist their TodoWrite (session-level) tasks
    into the Task Tracker database for long-term tracking.

    Args:
        todos: List of todo items, each with 'content', 'activeForm', 'status'
        session_name: Optional name for this session (default: auto-generated)

    Returns:
        Dictionary with sync results

    Example:
        todos = [
            {"content": "Fix bug", "activeForm": "Fixing bug", "status": "completed"},
            {"content": "Write tests", "activeForm": "Writing tests", "status": "in_progress"}
        ]
        sync_todowrite_tasks(todos, "My work session")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate session name if not provided
        if not session_name:
            session_name = f"TodoWrite sync {datetime.now():%Y-%m-%d %H:%M}"

        session_id = f"todowrite_sync_{SESSION_ID}"

        # Track sync results
        created_tasks = []
        skipped_tasks = []

        for idx, todo in enumerate(todos, 1):
            content = todo.get("content", "").strip()
            active_form = todo.get("activeForm", content).strip()
            status = todo.get("status", "pending").lower()

            if not content:
                skipped_tasks.append({"index": idx, "reason": "Empty content"})
                continue

            # Map TodoWrite status to task status
            status_map = {
                "pending": "pending",
                "in_progress": "in_progress",
                "completed": "completed",
                "in progress": "in_progress",
            }
            mapped_status = status_map.get(status, "pending")

            # Create task
            cursor.execute(
                """
                INSERT INTO tasks (
                    content, active_form, status, priority, task_type,
                    depth_level, session_id, context
                )
                VALUES (%s, %s, %s, 'medium', 'task', 0, %s, %s)
                RETURNING id, content, status
            """,
                (
                    content,
                    active_form,
                    mapped_status,
                    session_id,
                    f"Synced from TodoWrite: {session_name}",
                ),
            )

            task = dict(cursor.fetchone())
            created_tasks.append(task)

        conn.commit()

        return {
            "success": True,
            "message": f"Synced {len(created_tasks)} tasks from TodoWrite",
            "created_tasks": created_tasks,
            "skipped_tasks": skipped_tasks,
            "session_id": session_id,
            "session_name": session_name,
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def export_project(
    master_task_id: int,
    format: str = "markdown",
    include_completed: bool = True,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export a project (master task) to various formats.

    Phase 3 UX Enhancement: Export for reporting and sharing.

    Args:
        master_task_id: ID of the master task to export
        format: Export format - "markdown", "json", or "gantt" (default: "markdown")
        include_completed: Include completed tasks in export (default: True)
        output_path: Optional file path to save export (otherwise returns content)

    Returns:
        Dictionary with export content or file path

    Examples:
        # Export to Markdown
        export_project(45, format="markdown")

        # Export to JSON file
        export_project(45, format="json", output_path="project_45.json")

        # Export Gantt chart
        export_project(45, format="gantt")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Validate format
        valid_formats = ["markdown", "json", "gantt"]
        if format not in valid_formats:
            return {
                "success": False,
                "error": f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            }

        # Get master task details
        cursor.execute(
            """
            SELECT id, content, context_summary, status, priority, created_at, completed_at
            FROM tasks
            WHERE id = %s AND task_type = 'master'
        """,
            (master_task_id,),
        )

        master_task = cursor.fetchone()
        if not master_task:
            return {
                "success": False,
                "error": f"Master task {master_task_id} not found",
            }

        master_task = dict(master_task)

        # Get task hierarchy
        cursor.execute(
            """
            WITH RECURSIVE task_tree AS (
                SELECT id, content, status, priority, depth_level, parent_task_id,
                       created_at, completed_at, notes, context_summary
                FROM tasks
                WHERE master_task_id = %s OR id = %s
            )
            SELECT * FROM task_tree
            ORDER BY depth_level, id
        """,
            (master_task_id, master_task_id),
        )

        all_tasks = [dict(row) for row in cursor.fetchall()]

        # Filter completed if needed
        if not include_completed:
            all_tasks = [t for t in all_tasks if t["status"] != "completed"]

        # Calculate progress
        cursor.execute(
            """
            SELECT calculate_completion_percentage(%s) as percentage
        """,
            (master_task_id,),
        )
        completion_pct = cursor.fetchone()["percentage"]

        # Generate export based on format
        if format == "markdown":
            content = _generate_markdown_export(master_task, all_tasks, completion_pct)
        elif format == "json":
            content = _generate_json_export(master_task, all_tasks, completion_pct)
        elif format == "gantt":
            content = _generate_gantt_export(master_task, all_tasks)

        # Save to file if path provided
        if output_path:
            import os

            os.makedirs(
                os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
                exist_ok=True,
            )

            if format == "json":
                with open(output_path, "w") as f:
                    json.dump(content, f, indent=2, default=str)
            else:
                with open(output_path, "w") as f:
                    f.write(content)

            return {
                "success": True,
                "format": format,
                "file_path": output_path,
                "task_count": len(all_tasks),
                "completion_percentage": completion_pct,
                "message": f"Project exported to {output_path}",
            }
        else:
            return {
                "success": True,
                "format": format,
                "content": content,
                "task_count": len(all_tasks),
                "completion_percentage": completion_pct,
                "message": f"Project exported successfully",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _generate_markdown_export(master_task, all_tasks, completion_pct):
    """Generate Markdown export of project."""
    lines = []

    # Header
    lines.append(f"# {master_task['content']}")
    lines.append("")
    lines.append(
        f"**Status:** {master_task['status']} | **Progress:** {completion_pct}%"
    )
    lines.append(f"**Created:** {master_task['created_at']}")
    if master_task["completed_at"]:
        lines.append(f"**Completed:** {master_task['completed_at']}")
    lines.append("")

    # Context
    if master_task.get("context_summary"):
        lines.append("## Summary")
        lines.append("")
        lines.append(master_task["context_summary"])
        lines.append("")

    # Task list
    lines.append("## Tasks")
    lines.append("")

    # Build hierarchy
    task_map = {t["id"]: t for t in all_tasks}
    root_tasks = [
        t
        for t in all_tasks
        if t["parent_task_id"] is None or t["id"] == master_task["id"]
    ]

    def render_task(task, depth=0):
        if task["id"] == master_task["id"]:
            return  # Skip master task itself in list

        indent = "  " * depth
        checkbox = "[x]" if task["status"] == "completed" else "[ ]"
        priority_badge = (
            f" **{task['priority'].upper()}**"
            if task["priority"] in ["high", "critical"]
            else ""
        )

        lines.append(f"{indent}- {checkbox} {task['content']}{priority_badge}")

        if task.get("notes"):
            lines.append(f"{indent}  *Notes: {task['notes']}*")

        # Find children
        children = [t for t in all_tasks if t.get("parent_task_id") == task["id"]]
        for child in children:
            render_task(child, depth + 1)

    for task in root_tasks:
        render_task(task)

    lines.append("")

    # Statistics
    total_tasks = len([t for t in all_tasks if t["id"] != master_task["id"]])
    completed_tasks = len(
        [
            t
            for t in all_tasks
            if t["status"] == "completed" and t["id"] != master_task["id"]
        ]
    )

    lines.append("## Statistics")
    lines.append("")
    lines.append(f"- **Total Tasks:** {total_tasks}")
    lines.append(f"- **Completed:** {completed_tasks}")
    lines.append(f"- **Remaining:** {total_tasks - completed_tasks}")
    lines.append(f"- **Completion:** {completion_pct}%")

    return "\n".join(lines)


def _generate_json_export(master_task, all_tasks, completion_pct):
    """Generate JSON export of project."""
    return {
        "master_task": {
            "id": master_task["id"],
            "title": master_task["content"],
            "status": master_task["status"],
            "priority": master_task["priority"],
            "context_summary": master_task.get("context_summary"),
            "created_at": str(master_task["created_at"]),
            "completed_at": (
                str(master_task["completed_at"])
                if master_task["completed_at"]
                else None
            ),
            "completion_percentage": completion_pct,
        },
        "tasks": [
            {
                "id": t["id"],
                "content": t["content"],
                "status": t["status"],
                "priority": t["priority"],
                "depth_level": t["depth_level"],
                "parent_task_id": t["parent_task_id"],
                "created_at": str(t["created_at"]),
                "completed_at": str(t["completed_at"]) if t["completed_at"] else None,
                "notes": t.get("notes"),
                "context_summary": t.get("context_summary"),
            }
            for t in all_tasks
            if t["id"] != master_task["id"]
        ],
        "statistics": {
            "total_tasks": len([t for t in all_tasks if t["id"] != master_task["id"]]),
            "completed_tasks": len(
                [
                    t
                    for t in all_tasks
                    if t["status"] == "completed" and t["id"] != master_task["id"]
                ]
            ),
            "completion_percentage": completion_pct,
        },
        "exported_at": datetime.now().isoformat(),
    }


def _generate_gantt_export(master_task, all_tasks):
    """Generate Mermaid Gantt chart of project."""
    lines = []

    lines.append("```mermaid")
    lines.append("gantt")
    lines.append(f"    title {master_task['content']}")
    lines.append("    dateFormat YYYY-MM-DD")
    lines.append("")

    # Filter to non-master tasks
    tasks = [t for t in all_tasks if t["id"] != master_task["id"]]

    # Sort by creation date
    tasks.sort(key=lambda t: t["created_at"])

    for task in tasks:
        task_id = f"task{task['id']}"
        task_name = task["content"][:50]  # Limit length

        # Status indicator
        status_marker = (
            "done"
            if task["status"] == "completed"
            else "active" if task["status"] == "in_progress" else ""
        )

        # Dates
        start_date = task["created_at"].strftime("%Y-%m-%d")
        if task["completed_at"]:
            end_date = task["completed_at"].strftime("%Y-%m-%d")
        else:
            # Estimate end date as 7 days from start if not completed
            end_date = (task["created_at"] + timedelta(days=7)).strftime("%Y-%m-%d")

        line = f"    {task_name} :{status_marker}, {task_id}, {start_date}, {end_date}"
        lines.append(line)

    lines.append("```")

    return "\n".join(lines)


@mcp.tool()
def generate_summary_report(
    period: str = "weekly",
    include_projects: bool = True,
    include_statistics: bool = True,
) -> Dict[str, Any]:
    """
    Generate summary report of task activity.

    Phase 3 UX Enhancement: Weekly/monthly summaries for reporting.

    Args:
        period: Report period - "weekly" (last 7 days), "monthly" (last 30 days), "all" (default: "weekly")
        include_projects: Include project-level summaries (default: True)
        include_statistics: Include completion statistics (default: True)

    Returns:
        Dictionary with report content

    Examples:
        # Weekly summary
        generate_summary_report(period="weekly")

        # Monthly report
        generate_summary_report(period="monthly")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Determine date range
        if period == "weekly":
            days_ago = 7
            period_name = "Last 7 Days"
        elif period == "monthly":
            days_ago = 30
            period_name = "Last 30 Days"
        else:
            days_ago = None
            period_name = "All Time"

        # Get tasks completed in period
        if days_ago:
            cursor.execute(
                """
                SELECT id, content, status, priority, completed_at, master_task_id
                FROM tasks
                WHERE completed_at >= CURRENT_TIMESTAMP - make_interval(days => %s)
                ORDER BY completed_at DESC
            """,
                (days_ago,),
            )
        else:
            cursor.execute(
                """
                SELECT id, content, status, priority, completed_at, master_task_id
                FROM tasks
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 100
            """
            )

        completed_tasks = [dict(row) for row in cursor.fetchall()]

        # Get project summaries
        projects = []
        if include_projects:
            cursor.execute(
                """
                SELECT * FROM master_tasks_progress
                WHERE master_status != 'completed'
                ORDER BY completion_percentage DESC
                LIMIT 20
            """
            )
            projects = [dict(row) for row in cursor.fetchall()]

        # Calculate statistics
        stats = {}
        if include_statistics:
            if days_ago:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE status = 'blocked') as blocked_count,
                        COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
                        COUNT(*) FILTER (WHERE priority = 'high') as high_count
                    FROM tasks
                    WHERE created_at >= CURRENT_TIMESTAMP - make_interval(days => %s)
                       OR updated_at >= CURRENT_TIMESTAMP - make_interval(days => %s)
                """,
                    (days_ago, days_ago),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE status = 'blocked') as blocked_count,
                        COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
                        COUNT(*) FILTER (WHERE priority = 'high') as high_count
                    FROM tasks
                """
                )

            stats_row = cursor.fetchone()
            if stats_row:
                stats = dict(stats_row)
            else:
                # Default stats if no data
                stats = {
                    "completed_count": 0,
                    "in_progress_count": 0,
                    "pending_count": 0,
                    "blocked_count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                }

            # Calculate velocity (tasks/day)
            if days_ago and stats.get("completed_count", 0) > 0:
                stats["velocity"] = round(stats.get("completed_count", 0) / days_ago, 2)
            else:
                stats["velocity"] = 0

        # Generate report content
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"TASK TRACKER SUMMARY REPORT - {period_name}")
        report_lines.append("=" * 80)
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        if include_statistics:
            report_lines.append("📊 STATISTICS")
            report_lines.append("-" * 80)
            report_lines.append(f"Tasks Completed: {stats.get('completed_count', 0)}")
            report_lines.append(
                f"Tasks In Progress: {stats.get('in_progress_count', 0)}"
            )
            report_lines.append(f"Tasks Pending: {stats.get('pending_count', 0)}")
            report_lines.append(f"Tasks Blocked: {stats.get('blocked_count', 0)}")
            report_lines.append(f"Critical Priority: {stats.get('critical_count', 0)}")
            report_lines.append(f"High Priority: {stats.get('high_count', 0)}")
            if stats.get("velocity", 0) > 0:
                report_lines.append(f"Velocity: {stats['velocity']} tasks/day")
            report_lines.append("")

        if include_projects and projects:
            report_lines.append("🏗️  ACTIVE PROJECTS")
            report_lines.append("-" * 80)
            for proj in projects[:10]:  # Top 10
                pct = proj["completion_percentage"]
                status_emoji = (
                    "✅"
                    if proj["master_status"] == "completed"
                    else "🔄" if proj["master_status"] == "in_progress" else "⏸️"
                )
                report_lines.append(
                    f"{status_emoji} {proj['master_content']} - {pct}% ({proj['completed_tasks']}/{proj['total_tasks']} tasks)"
                )
            report_lines.append("")

        if completed_tasks:
            report_lines.append("✅ RECENTLY COMPLETED TASKS")
            report_lines.append("-" * 80)
            for task in completed_tasks[:20]:  # Top 20
                completed_date = task["completed_at"].strftime("%Y-%m-%d")
                priority_badge = (
                    f"[{task['priority'].upper()}]"
                    if task["priority"] in ["high", "critical"]
                    else ""
                )
                report_lines.append(
                    f"• {task['content']} {priority_badge} - {completed_date}"
                )
            report_lines.append("")

        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        return {
            "success": True,
            "period": period_name,
            "report": report_content,
            "statistics": stats if include_statistics else None,
            "projects": projects if include_projects else None,
            "completed_tasks": len(completed_tasks),
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def export_gantt_chart(
    master_task_id: int, output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export project as Mermaid Gantt chart.

    Phase 3 UX Enhancement: Visual timeline for projects.

    Args:
        master_task_id: ID of the master task
        output_path: Optional file path to save chart (otherwise returns content)

    Returns:
        Dictionary with Gantt chart content

    Example:
        export_gantt_chart(45, output_path="project_timeline.md")
    """
    # Reuse export_project with gantt format
    result = export_project(master_task_id, format="gantt", output_path=output_path)

    # Add 'chart' key as alias for 'content' for backward compatibility
    if result.get("success") and "content" in result:
        result["chart"] = result["content"]

    return result


@mcp.tool()
def create_from_template(
    template_name: str,
    master_task_title: str,
    master_task_description: Optional[str] = None,
    customize_tasks: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """
    Create tasks from a template.

    Phase 3 UX Enhancement: Quickly create common task structures.

    Args:
        template_name: Name of the template to use
        master_task_title: Title for the new master task
        master_task_description: Optional description (default: template description)
        customize_tasks: Optional dict to customize task content {index: new_content}

    Returns:
        Dictionary with created master task and subtasks

    Examples:
        # Use feature template
        create_from_template("Feature Implementation", "Build user profile page")

        # Customize specific tasks
        create_from_template(
            "Bug Fix",
            "Fix login timeout",
            customize_tasks={0: "Reproduce timeout on staging", 1: "Check session management code"}
        )
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get template
        cursor.execute(
            """
            SELECT id, name, description, structure
            FROM task_templates
            WHERE name = %s
        """,
            (template_name,),
        )

        template = cursor.fetchone()
        if not template:
            return {
                "success": False,
                "error": f"Template '{template_name}' not found. Use list_templates() to see available templates.",
            }

        template = dict(template)
        template_structure = template["structure"]

        # Create master task
        description = master_task_description or template["description"]
        master_active_form = f"Working on {master_task_title.lower()}"

        cursor.execute(
            """
            INSERT INTO tasks (
                content, active_form, status, priority, task_type, depth_level,
                context_summary, session_id
            )
            VALUES (%s, %s, 'pending', 'medium', 'master', 0, %s, %s)
            RETURNING id, content, status, created_at
        """,
            (master_task_title, master_active_form, description, SESSION_ID),
        )

        master_task = dict(cursor.fetchone())
        master_task_id = master_task["id"]

        # Create subtasks from template
        subtasks = []
        for idx, task_spec in enumerate(template_structure["tasks"]):
            # Allow customization
            if customize_tasks and idx in customize_tasks:
                task_content = customize_tasks[idx]
            else:
                task_content = task_spec["content"]

            task_priority = task_spec.get("priority", "medium")
            task_active_form = f"Working on {task_content.lower()}"

            cursor.execute(
                """
                INSERT INTO tasks (
                    content, active_form, status, priority, task_type, depth_level,
                    parent_task_id, master_task_id, session_id
                )
                VALUES (%s, %s, 'pending', %s, 'task', 1, %s, %s, %s)
                RETURNING id, content, status, priority
            """,
                (
                    task_content,
                    task_active_form,
                    task_priority,
                    master_task_id,
                    master_task_id,
                    SESSION_ID,
                ),
            )

            subtask = dict(cursor.fetchone())
            subtasks.append(subtask)

        # Update template usage count
        cursor.execute(
            """
            UPDATE task_templates
            SET usage_count = usage_count + 1
            WHERE id = %s
        """,
            (template["id"],),
        )

        conn.commit()

        return {
            "success": True,
            "master_task": master_task,
            "subtasks": subtasks,
            "template_used": template_name,
            "total_tasks_created": len(subtasks) + 1,
            "tasks_created": len(subtasks) + 1,  # Backward compatibility alias
            "message": f"Created master task '{master_task_title}' with {len(subtasks)} subtasks from template '{template_name}'",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def save_as_template(
    master_task_id: int,
    template_name: str,
    description: Optional[str] = None,
    category: Optional[str] = "custom",
) -> Dict[str, Any]:
    """
    Save a master task as a reusable template.

    Phase 3 UX Enhancement: Create custom templates from existing work.

    Args:
        master_task_id: ID of master task to save as template
        template_name: Name for the new template (must be unique)
        description: Optional description of what the template is for
        category: Template category (default: "custom")

    Returns:
        Dictionary with template details

    Example:
        save_as_template(45, "OAuth Integration", "Standard OAuth2 implementation workflow", "integration")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get master task and subtasks
        cursor.execute(
            """
            SELECT id, content, context_summary
            FROM tasks
            WHERE id = %s AND task_type = 'master'
        """,
            (master_task_id,),
        )

        master_task = cursor.fetchone()
        if not master_task:
            return {
                "success": False,
                "error": f"Master task {master_task_id} not found",
            }

        master_task = dict(master_task)

        # Get all subtasks
        cursor.execute(
            """
            SELECT content, priority, depth_level
            FROM tasks
            WHERE master_task_id = %s AND task_type != 'master'
            ORDER BY id
        """,
            (master_task_id,),
        )

        subtasks = [dict(row) for row in cursor.fetchall()]

        if not subtasks:
            return {
                "success": False,
                "error": "Master task has no subtasks. Templates require at least one subtask.",
            }

        # Build template structure
        template_structure = {
            "tasks": [
                {"content": task["content"], "priority": task["priority"]}
                for task in subtasks
            ]
        }

        # Use context_summary as description if not provided
        template_description = (
            description
            or master_task.get("context_summary")
            or f"Template based on '{master_task['content']}'"
        )

        # Insert template
        cursor.execute(
            """
            INSERT INTO task_templates (name, description, category, structure, is_builtin, created_by)
            VALUES (%s, %s, %s, %s, FALSE, %s)
            RETURNING id, name, description, category, usage_count
        """,
            (
                template_name,
                template_description,
                category,
                json.dumps(template_structure),
                "user",
            ),
        )

        template = dict(cursor.fetchone())
        conn.commit()

        return {
            "success": True,
            "template": template,
            "task_count": len(subtasks),
            "message": f"Template '{template_name}' created with {len(subtasks)} tasks",
        }

    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            return {
                "success": False,
                "error": f"Template name '{template_name}' already exists. Please choose a different name.",
            }
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_templates(
    category: Optional[str] = None,
    include_builtin: bool = True,
    include_custom: bool = True,
) -> Dict[str, Any]:
    """
    List available task templates.

    Phase 3 UX Enhancement: Browse templates for quick task creation.

    Args:
        category: Filter by category (development, maintenance, research, integration, etc.)
        include_builtin: Include system-provided templates (default: True)
        include_custom: Include user-created templates (default: True)

    Returns:
        Dictionary with list of templates

    Examples:
        # All templates
        list_templates()

        # Only built-in templates
        list_templates(include_custom=False)

        # Development templates only
        list_templates(category="development")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)

        if not include_builtin:
            conditions.append("is_builtin = FALSE")

        if not include_custom:
            conditions.append("is_builtin = TRUE")

        query = """
            SELECT
                id,
                name,
                description,
                category,
                is_builtin,
                usage_count,
                created_at,
                jsonb_array_length(structure->'tasks') as task_count
            FROM task_templates
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY is_builtin DESC, usage_count DESC, name"

        cursor.execute(query, params)
        templates = [dict(row) for row in cursor.fetchall()]

        # Group by category
        by_category = {}
        for template in templates:
            cat = template["category"] or "uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(template)

        return {
            "success": True,
            "templates": templates,
            "by_category": by_category,
            "total_count": len(templates),
            "categories": list(by_category.keys()),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_template_details(template_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a template including all task definitions.

    Args:
        template_name: Name of the template

    Returns:
        Dictionary with complete template details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                name,
                description,
                category,
                structure,
                is_builtin,
                usage_count,
                created_at,
                updated_at
            FROM task_templates
            WHERE name = %s
        """,
            (template_name,),
        )

        template = cursor.fetchone()
        if not template:
            return {"success": False, "error": f"Template '{template_name}' not found"}

        template = dict(template)

        return {
            "success": True,
            "template": template,
            "task_count": len(template["structure"]["tasks"]),
            "tasks": template["structure"]["tasks"],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def archive_tasks(
    task_ids: Optional[List[int]] = None,
    days_old: Optional[int] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Archive tasks (soft delete).

    Can archive specific tasks by ID or auto-archive old completed tasks.

    Args:
        task_ids: Specific task IDs to archive (optional)
        days_old: Archive completed tasks older than this many days (optional)
        dry_run: If True, show what would be archived without actually archiving (default: True)

    Returns:
        Dictionary with archive results

    Examples:
        # Archive specific tasks
        archive_tasks(task_ids=[123, 456, 789], dry_run=False)

        # Archive completed tasks older than 30 days (preview)
        archive_tasks(days_old=30, dry_run=True)

        # Actually archive old tasks
        archive_tasks(days_old=30, dry_run=False)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if task_ids:
            # Archive specific tasks
            if dry_run:
                cursor.execute(
                    """
                    SELECT id, content, status, completed_at
                    FROM tasks
                    WHERE id = ANY(%s) AND is_archived = FALSE
                """,
                    (task_ids,),
                )
                tasks = [dict(row) for row in cursor.fetchall()]

                return {
                    "success": True,
                    "dry_run": True,
                    "would_archive": len(tasks),
                    "tasks": tasks,
                    "message": f"Would archive {len(tasks)} tasks (dry run)",
                }
            else:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET is_archived = TRUE,
                        archived_at = NOW(),
                        archived_by = 'user'
                    WHERE id = ANY(%s) AND is_archived = FALSE
                    RETURNING id, content
                """,
                    (task_ids,),
                )

                archived = [dict(row) for row in cursor.fetchall()]
                conn.commit()

                return {
                    "success": True,
                    "dry_run": False,
                    "archived": len(archived),
                    "tasks": archived,
                    "message": f"Archived {len(archived)} tasks",
                }

        elif days_old is not None:
            # Archive old completed tasks
            if dry_run:
                cursor.execute(
                    """
                    SELECT id, content, status, completed_at,
                           EXTRACT(EPOCH FROM (NOW() - completed_at)) / 86400 as days_since_completed
                    FROM tasks
                    WHERE status = 'completed'
                      AND is_archived = FALSE
                      AND completed_at < NOW() - %s * INTERVAL '1 day'
                    ORDER BY completed_at DESC
                """,
                    (days_old,),
                )

                tasks = [dict(row) for row in cursor.fetchall()]

                return {
                    "success": True,
                    "dry_run": True,
                    "would_archive": len(tasks),
                    "days_old": days_old,
                    "tasks": tasks,
                    "message": f"Would archive {len(tasks)} completed tasks older than {days_old} days (dry run)",
                }
            else:
                cursor.execute(
                    """
                    SELECT * FROM archive_old_completed_tasks(%s, 'user')
                """,
                    (days_old,),
                )

                result = dict(cursor.fetchone())
                conn.commit()

                return {
                    "success": True,
                    "dry_run": False,
                    "archived": result["archived_count"],
                    "task_ids": result["task_ids"],
                    "days_old": days_old,
                    "message": f"Archived {result['archived_count']} completed tasks older than {days_old} days",
                }

        else:
            return {
                "success": False,
                "error": "Must specify either task_ids or days_old",
            }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def unarchive_tasks(task_ids: List[int]) -> Dict[str, Any]:
    """
    Restore archived tasks.

    Args:
        task_ids: List of task IDs to restore

    Returns:
        Dictionary with restore results
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE tasks
            SET is_archived = FALSE,
                archived_at = NULL,
                archived_by = NULL
            WHERE id = ANY(%s) AND is_archived = TRUE
            RETURNING id, content, status
        """,
            (task_ids,),
        )

        restored = [dict(row) for row in cursor.fetchall()]
        conn.commit()

        return {
            "success": True,
            "restored": len(restored),
            "tasks": restored,
            "message": f"Restored {len(restored)} tasks from archive",
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_archived_tasks(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    List archived tasks with pagination.

    Args:
        limit: Maximum number of tasks to return (default: 50)
        offset: Number of tasks to skip (for pagination, default: 0)

    Returns:
        Dictionary with list of archived tasks and pagination metadata
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE is_archived = TRUE")
        total_count = cursor.fetchone()["total"]

        # Get paginated results
        cursor.execute(
            """
            SELECT * FROM archived_tasks
            LIMIT %s OFFSET %s
        """,
            (limit, offset),
        )

        tasks = [dict(row) for row in cursor.fetchall()]

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        current_page = (offset // limit) + 1
        has_more = offset + len(tasks) < total_count

        return {
            "success": True,
            "tasks": tasks,
            "pagination": {
                "total_count": total_count,
                "count": len(tasks),
                "limit": limit,
                "offset": offset,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_more": has_more,
                "has_previous": offset > 0,
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_archive_stats() -> Dict[str, Any]:
    """
    Get statistics about archived tasks.

    Returns:
        Dictionary with archive statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM get_archive_statistics()")
        stats = dict(cursor.fetchone())

        # Format dates
        if stats.get("oldest_archived_date"):
            stats["oldest_archived_date"] = stats["oldest_archived_date"].isoformat()
        if stats.get("newest_archived_date"):
            stats["newest_archived_date"] = stats["newest_archived_date"].isoformat()

        return {"success": True, "statistics": stats}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_velocity_metrics(
    days: int = 30, project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate task completion velocity metrics.

    Provides insights into:
    - Tasks completed per day/week
    - Average completion time
    - Velocity trend (improving/declining)
    - Completion rate by priority

    Args:
        days: Number of days to analyze (default: 30)
        project: Optional project filter

    Returns:
        Dictionary with velocity metrics and trends
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Calculate start date
        start_date = datetime.now() - timedelta(days=days)

        # Base query with optional project filter
        project_filter = ""
        params = [start_date]

        if project:
            project_filter = "AND project = %s"
            params.append(project)

        # Get completed tasks in time period
        cursor.execute(
            f"""
            SELECT
                DATE(completed_at) as completion_date,
                COUNT(*) as tasks_completed,
                AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours_to_complete,
                priority
            FROM tasks
            WHERE status = 'completed'
            AND completed_at >= %s
            {project_filter}
            GROUP BY DATE(completed_at), priority
            ORDER BY completion_date
        """,
            params,
        )

        daily_data = [dict(row) for row in cursor.fetchall()]

        # Calculate overall metrics
        cursor.execute(
            f"""
            SELECT
                COUNT(*) as total_completed,
                AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours,
                MIN(completed_at) as first_completion,
                MAX(completed_at) as last_completion
            FROM tasks
            WHERE status = 'completed'
            AND completed_at >= %s
            {project_filter}
        """,
            params,
        )

        overall = dict(cursor.fetchone())

        # Calculate velocity (tasks per day)
        if (
            overall["total_completed"]
            and overall["first_completion"]
            and overall["last_completion"]
        ):
            time_range_days = (
                overall["last_completion"] - overall["first_completion"]
            ).days + 1
            velocity_per_day = (
                overall["total_completed"] / time_range_days
                if time_range_days > 0
                else 0
            )
            velocity_per_week = velocity_per_day * 7
        else:
            velocity_per_day = 0
            velocity_per_week = 0

        # Calculate trend (compare first half vs second half)
        mid_date = start_date + timedelta(days=days / 2)

        cursor.execute(
            f"""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'completed'
            AND completed_at >= %s AND completed_at < %s
            {project_filter}
        """,
            [start_date, mid_date] + ([project] if project else []),
        )
        first_half = cursor.fetchone()["count"]

        cursor.execute(
            f"""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'completed'
            AND completed_at >= %s
            {project_filter}
        """,
            [mid_date] + ([project] if project else []),
        )
        second_half = cursor.fetchone()["count"]

        # Determine trend
        if first_half == 0 and second_half == 0:
            trend = "no_data"
            trend_percentage = 0
        elif first_half == 0:
            trend = "improving"
            trend_percentage = 100
        else:
            trend_percentage = ((second_half - first_half) / first_half) * 100
            if trend_percentage > 10:
                trend = "improving"
            elif trend_percentage < -10:
                trend = "declining"
            else:
                trend = "stable"

        # Get completion rate by priority
        cursor.execute(
            f"""
            SELECT
                priority,
                COUNT(*) as completed_count,
                AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours
            FROM tasks
            WHERE status = 'completed'
            AND completed_at >= %s
            {project_filter}
            GROUP BY priority
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """,
            params,
        )

        by_priority = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "period_days": days,
            "project": project,
            "velocity": {
                "tasks_per_day": round(velocity_per_day, 2),
                "tasks_per_week": round(velocity_per_week, 2),
                "total_completed": overall["total_completed"],
                "avg_completion_hours": (
                    round(float(overall["avg_hours"]), 2) if overall["avg_hours"] else 0
                ),
            },
            "trend": {
                "direction": trend,
                "percentage_change": round(trend_percentage, 1),
                "first_half_count": first_half,
                "second_half_count": second_half,
            },
            "by_priority": by_priority,
            "daily_breakdown": daily_data,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def predict_completion(
    project: Optional[str] = None, use_velocity_days: int = 30
) -> Dict[str, Any]:
    """
    Predict project completion date based on current velocity.

    Uses historical velocity to estimate when remaining tasks will be completed.
    Provides different scenarios (optimistic, realistic, pessimistic).

    Args:
        project: Optional project to analyze
        use_velocity_days: Days of history to use for velocity calculation (default: 30)

    Returns:
        Dictionary with completion predictions and confidence intervals
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get velocity metrics
        velocity_data = get_velocity_metrics(days=use_velocity_days, project=project)

        if not velocity_data["success"]:
            return velocity_data

        velocity_per_day = velocity_data["velocity"]["tasks_per_day"]

        if velocity_per_day == 0:
            return {
                "success": False,
                "error": "No completed tasks in the specified period. Cannot predict completion.",
            }

        # Count remaining tasks
        project_filter = ""
        params = []

        if project:
            project_filter = "AND project = %s"
            params.append(project)

        cursor.execute(
            f"""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE priority = 'high') as high_count
            FROM tasks
            WHERE status IN ('pending', 'in_progress')
            {project_filter}
        """,
            params,
        )

        remaining = dict(cursor.fetchone())
        total_remaining = remaining["pending_count"] + remaining["in_progress_count"]

        if total_remaining == 0:
            return {
                "success": True,
                "project": project,
                "message": "All tasks completed!",
                "total_remaining": 0,
                "completion_date": datetime.now().isoformat(),
            }

        # Calculate predictions
        # Realistic: based on current velocity
        realistic_days = total_remaining / velocity_per_day
        realistic_date = datetime.now() + timedelta(days=realistic_days)

        # Optimistic: assume 20% improvement in velocity
        optimistic_days = total_remaining / (velocity_per_day * 1.2)
        optimistic_date = datetime.now() + timedelta(days=optimistic_days)

        # Pessimistic: assume 20% decline in velocity
        pessimistic_days = total_remaining / (velocity_per_day * 0.8)
        pessimistic_date = datetime.now() + timedelta(days=pessimistic_days)

        # Calculate confidence based on velocity trend
        trend = velocity_data["trend"]["direction"]
        if trend == "improving":
            confidence = "high"
        elif trend == "stable":
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "success": True,
            "project": project,
            "total_remaining": total_remaining,
            "breakdown": {
                "pending": remaining["pending_count"],
                "in_progress": remaining["in_progress_count"],
                "critical": remaining["critical_count"],
                "high": remaining["high_count"],
            },
            "current_velocity": {
                "tasks_per_day": velocity_per_day,
                "based_on_days": use_velocity_days,
            },
            "predictions": {
                "optimistic": {
                    "completion_date": optimistic_date.isoformat(),
                    "days_remaining": round(optimistic_days, 1),
                    "assumes": "+20% velocity improvement",
                },
                "realistic": {
                    "completion_date": realistic_date.isoformat(),
                    "days_remaining": round(realistic_days, 1),
                    "assumes": "current velocity maintained",
                },
                "pessimistic": {
                    "completion_date": pessimistic_date.isoformat(),
                    "days_remaining": round(pessimistic_days, 1),
                    "assumes": "-20% velocity decline",
                },
            },
            "confidence": confidence,
            "velocity_trend": trend,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_bottlenecks(
    project: Optional[str] = None, min_days_stale: int = 7
) -> Dict[str, Any]:
    """
    Identify workflow bottlenecks and stuck tasks.

    Analyzes:
    - Tasks stuck in 'in_progress' for too long
    - Blocked tasks and common blockers
    - Priority mismatches (low priority blocking high priority)
    - Tasks with many dependencies

    Args:
        project: Optional project filter
        min_days_stale: Minimum days without update to flag as stale (default: 7)

    Returns:
        Dictionary with bottleneck analysis and recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        stale_threshold = datetime.now() - timedelta(days=min_days_stale)

        project_filter = ""
        params = [stale_threshold]

        if project:
            project_filter = "AND project = %s"
            params.append(project)

        # Find stale in-progress tasks
        cursor.execute(
            f"""
            SELECT
                id,
                content,
                priority,
                status,
                project,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - updated_at))/86400 as days_stale
            FROM tasks
            WHERE status = 'in_progress'
            AND updated_at < %s
            {project_filter}
            ORDER BY updated_at ASC
        """,
            params,
        )

        stale_tasks = [dict(row) for row in cursor.fetchall()]

        # Find blocked tasks (tasks with blocker_reason set)
        cursor.execute(
            f"""
            SELECT
                id,
                content,
                priority,
                project,
                blocker_reason,
                created_at,
                EXTRACT(EPOCH FROM (NOW() - created_at))/86400 as days_blocked
            FROM tasks
            WHERE blocker_reason IS NOT NULL
            AND blocker_reason != ''
            {project_filter}
            ORDER BY priority DESC, created_at ASC
        """,
            params[1:] if project else [],
        )

        blocked_tasks = [dict(row) for row in cursor.fetchall()]

        # Find tasks with many subtasks (potential complexity bottlenecks)
        cursor.execute(
            f"""
            SELECT
                t.id,
                t.content,
                t.priority,
                t.project,
                COUNT(st.id) as subtask_count,
                COUNT(st.id) FILTER (WHERE st.status = 'completed') as completed_subtasks,
                COUNT(st.id) FILTER (WHERE st.status = 'in_progress') as in_progress_subtasks,
                COUNT(st.id) FILTER (WHERE st.status = 'pending') as pending_subtasks
            FROM tasks t
            LEFT JOIN tasks st ON st.parent_task_id = t.id
            WHERE t.status IN ('pending', 'in_progress')
            {project_filter.replace('project', 't.project') if project else ''}
            GROUP BY t.id, t.content, t.priority, t.project
            HAVING COUNT(st.id) >= 5
            ORDER BY COUNT(st.id) DESC
        """,
            params[1:] if project else [],
        )

        complex_tasks = [dict(row) for row in cursor.fetchall()]

        # Analyze blocker reasons (most common blockers)
        cursor.execute(
            f"""
            SELECT
                blocker_reason,
                COUNT(*) as occurrence_count,
                ARRAY_AGG(id) as task_ids
            FROM tasks
            WHERE blocker_reason IS NOT NULL
            AND blocker_reason != ''
            {project_filter}
            GROUP BY blocker_reason
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """,
            params[1:] if project else [],
        )

        common_blockers = [dict(row) for row in cursor.fetchall()]

        # Calculate bottleneck score
        total_bottlenecks = len(stale_tasks) + len(blocked_tasks) + len(complex_tasks)

        # Determine severity
        if total_bottlenecks == 0:
            severity = "none"
        elif total_bottlenecks <= 3:
            severity = "low"
        elif total_bottlenecks <= 7:
            severity = "medium"
        elif total_bottlenecks <= 15:
            severity = "high"
        else:
            severity = "critical"

        # Generate recommendations
        recommendations = []

        if stale_tasks:
            recommendations.append(
                f"Review {len(stale_tasks)} stale in-progress tasks - consider breaking down or reassigning"
            )

        if blocked_tasks:
            recommendations.append(
                f"Unblock {len(blocked_tasks)} tasks to improve flow"
            )

        if complex_tasks:
            recommendations.append(
                f"Simplify {len(complex_tasks)} complex tasks with many subtasks"
            )

        if common_blockers:
            top_blocker = common_blockers[0]["blocker_reason"]
            recommendations.append(f"Address common blocker: '{top_blocker}'")

        if not recommendations:
            recommendations.append(
                "No major bottlenecks detected - workflow is healthy!"
            )

        return {
            "success": True,
            "project": project,
            "analysis_date": datetime.now().isoformat(),
            "severity": severity,
            "total_bottlenecks": total_bottlenecks,
            "bottlenecks": {
                "stale_tasks": {
                    "count": len(stale_tasks),
                    "min_days_stale": min_days_stale,
                    "tasks": stale_tasks,
                },
                "blocked_tasks": {"count": len(blocked_tasks), "tasks": blocked_tasks},
                "complex_tasks": {"count": len(complex_tasks), "tasks": complex_tasks},
            },
            "common_blockers": common_blockers,
            "recommendations": recommendations,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Run the server
if __name__ == "__main__":
    mcp.run()
