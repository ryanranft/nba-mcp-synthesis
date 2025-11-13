-- Migration: Add Archive System for Task Tracker
-- Phase 2.4: Allow archiving old completed tasks
-- Created: 2025-11-12

-- Add is_archived column to tasks table
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS archived_by VARCHAR(255);

-- Create index on is_archived for faster queries
CREATE INDEX IF NOT EXISTS idx_tasks_is_archived ON tasks(is_archived);
CREATE INDEX IF NOT EXISTS idx_tasks_archived_at ON tasks(archived_at) WHERE is_archived = TRUE;

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_status_archived ON tasks(status, is_archived);

-- Update active_tasks view to exclude archived tasks
CREATE OR REPLACE VIEW active_tasks AS
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
    t.estimated_duration_minutes,
    t.actual_duration_minutes,
    ARRAY_AGG(tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags
FROM tasks t
LEFT JOIN task_tags tt ON t.id = tt.task_id
WHERE t.status IN ('pending', 'in_progress', 'blocked')
  AND t.is_archived = FALSE  -- Exclude archived tasks
GROUP BY t.id
ORDER BY
    CASE t.status
        WHEN 'in_progress' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'blocked' THEN 3
    END,
    t.priority DESC,
    t.created_at DESC;

-- Create archived_tasks view for easy access to archived tasks
CREATE OR REPLACE VIEW archived_tasks AS
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
    t.completed_at,
    t.archived_at,
    t.archived_by,
    ARRAY_AGG(tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags,
    EXTRACT(EPOCH FROM (NOW() - t.archived_at)) / 3600 / 24 as days_archived
FROM tasks t
LEFT JOIN task_tags tt ON t.id = tt.task_id
WHERE t.is_archived = TRUE
GROUP BY t.id
ORDER BY t.archived_at DESC;

-- Update task_statistics view to exclude archived tasks by default
CREATE OR REPLACE VIEW task_statistics AS
SELECT
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_tasks,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'blocked') as blocked_tasks,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_tasks,
    COUNT(*) FILTER (WHERE priority = 'critical') as critical_priority,
    COUNT(*) FILTER (WHERE priority = 'high') as high_priority,
    COUNT(*) FILTER (WHERE priority = 'medium') as medium_priority,
    COUNT(*) FILTER (WHERE priority = 'low') as low_priority,
    COUNT(*) FILTER (WHERE is_archived = TRUE) as archived_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 60) as avg_completion_time_minutes
FROM tasks
WHERE is_archived = FALSE;  -- Exclude archived from statistics

-- Update master_tasks_progress view to exclude archived tasks
CREATE OR REPLACE VIEW master_tasks_progress AS
WITH master_tasks AS (
    SELECT
        t.id as master_id,
        t.content as master_title,
        t.context_summary,
        t.status as master_status,
        t.priority as master_priority,
        t.created_at as master_created_at,
        EXTRACT(EPOCH FROM (NOW() - t.created_at)) / 3600 / 24 as days_since_created
    FROM tasks t
    WHERE t.task_type = 'master'
      AND t.is_archived = FALSE  -- Exclude archived
),
task_counts AS (
    SELECT
        t.master_task_id,
        COUNT(*) as total_subtasks,
        COUNT(*) FILTER (WHERE t.status = 'completed') as completed_subtasks,
        COUNT(*) FILTER (WHERE t.status = 'in_progress') as in_progress_subtasks,
        COUNT(*) FILTER (WHERE t.status = 'pending') as pending_subtasks,
        MAX(t.updated_at) as last_activity
    FROM tasks t
    WHERE t.master_task_id IS NOT NULL
      AND t.is_archived = FALSE  -- Exclude archived
    GROUP BY t.master_task_id
)
SELECT
    mt.*,
    COALESCE(tc.total_subtasks, 0) as total_subtasks,
    COALESCE(tc.completed_subtasks, 0) as completed_subtasks,
    COALESCE(tc.in_progress_subtasks, 0) as in_progress_subtasks,
    COALESCE(tc.pending_subtasks, 0) as pending_subtasks,
    CASE
        WHEN COALESCE(tc.total_subtasks, 0) = 0 THEN 0
        ELSE ROUND((COALESCE(tc.completed_subtasks, 0)::NUMERIC / tc.total_subtasks::NUMERIC) * 100, 1)
    END as completion_percentage,
    tc.last_activity,
    EXTRACT(EPOCH FROM (NOW() - tc.last_activity)) / 3600 as hours_since_last_worked
FROM master_tasks mt
LEFT JOIN task_counts tc ON mt.master_id = tc.master_task_id
ORDER BY mt.master_created_at DESC;

-- Add archive statistics function
CREATE OR REPLACE FUNCTION get_archive_statistics()
RETURNS TABLE (
    total_archived BIGINT,
    archived_this_week BIGINT,
    archived_this_month BIGINT,
    oldest_archived_date TIMESTAMPTZ,
    newest_archived_date TIMESTAMPTZ,
    total_size_estimate_mb NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_archived,
        COUNT(*) FILTER (WHERE archived_at >= NOW() - INTERVAL '7 days') as archived_this_week,
        COUNT(*) FILTER (WHERE archived_at >= NOW() - INTERVAL '30 days') as archived_this_month,
        MIN(archived_at) as oldest_archived_date,
        MAX(archived_at) as newest_archived_date,
        -- Rough estimate of size (this is approximate)
        ROUND((COUNT(*) * 2)::NUMERIC / 1024, 2) as total_size_estimate_mb
    FROM tasks
    WHERE is_archived = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add function to bulk archive old completed tasks
CREATE OR REPLACE FUNCTION archive_old_completed_tasks(
    days_old INTEGER DEFAULT 30,
    archived_by_user VARCHAR(255) DEFAULT 'system'
)
RETURNS TABLE (
    archived_count INTEGER,
    task_ids INTEGER[]
) AS $$
DECLARE
    v_task_ids INTEGER[];
    v_count INTEGER;
BEGIN
    -- Find tasks to archive
    SELECT ARRAY_AGG(id)
    INTO v_task_ids
    FROM tasks
    WHERE status = 'completed'
      AND is_archived = FALSE
      AND completed_at < NOW() - (days_old || ' days')::INTERVAL;

    -- Archive the tasks
    UPDATE tasks
    SET
        is_archived = TRUE,
        archived_at = NOW(),
        archived_by = archived_by_user
    WHERE id = ANY(v_task_ids);

    GET DIAGNOSTICS v_count = ROW_COUNT;

    RETURN QUERY SELECT v_count, COALESCE(v_task_ids, ARRAY[]::INTEGER[]);
END;
$$ LANGUAGE plpgsql;

-- Create trigger to log archiving to task_history
CREATE OR REPLACE FUNCTION log_task_archival()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_archived = TRUE AND (OLD.is_archived = FALSE OR OLD.is_archived IS NULL) THEN
        INSERT INTO task_history (task_id, previous_status, new_status, notes, changed_by)
        VALUES (
            NEW.id,
            'active',
            'archived',
            'Task archived on ' || NEW.archived_at::TEXT,
            NEW.archived_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_archival
AFTER UPDATE ON tasks
FOR EACH ROW
WHEN (NEW.is_archived = TRUE AND (OLD.is_archived = FALSE OR OLD.is_archived IS NULL))
EXECUTE FUNCTION log_task_archival();

-- Add comment to document the feature
COMMENT ON COLUMN tasks.is_archived IS 'Whether task has been archived (soft delete)';
COMMENT ON COLUMN tasks.archived_at IS 'When the task was archived';
COMMENT ON COLUMN tasks.archived_by IS 'User or system that archived the task';
COMMENT ON VIEW archived_tasks IS 'View of all archived tasks with metadata';
COMMENT ON FUNCTION get_archive_statistics() IS 'Get statistics about archived tasks';
COMMENT ON FUNCTION archive_old_completed_tasks(INTEGER, VARCHAR) IS 'Bulk archive completed tasks older than specified days';