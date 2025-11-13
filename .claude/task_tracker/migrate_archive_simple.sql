-- Simple Archive System Migration
-- Adds archive columns and functions without modifying existing views

-- Add archive columns if they don't exist
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS archived_by VARCHAR(255);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tasks_is_archived ON tasks(is_archived);
CREATE INDEX IF NOT EXISTS idx_tasks_archived_at ON tasks(archived_at) WHERE is_archived = TRUE;
CREATE INDEX IF NOT EXISTS idx_tasks_status_archived ON tasks(status, is_archived);

-- Create archived_tasks view
DROP VIEW IF EXISTS archived_tasks CASCADE;
CREATE VIEW archived_tasks AS
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

-- Create archive statistics function
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
        ROUND((COUNT(*) * 2)::NUMERIC / 1024, 2) as total_size_estimate_mb
    FROM tasks
    WHERE is_archived = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create bulk archive function
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

-- Create trigger to log archival
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

DROP TRIGGER IF EXISTS trigger_log_archival ON tasks;
CREATE TRIGGER trigger_log_archival
AFTER UPDATE ON tasks
FOR EACH ROW
WHEN (NEW.is_archived = TRUE AND (OLD.is_archived = FALSE OR OLD.is_archived IS NULL))
EXECUTE FUNCTION log_task_archival();

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Archive system migration complete!';
    RAISE NOTICE '   - Added is_archived, archived_at, archived_by columns';
    RAISE NOTICE '   - Created indexes for performance';
    RAISE NOTICE '   - Created archived_tasks view';
    RAISE NOTICE '   - Created archive functions and triggers';
END $$;