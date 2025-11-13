-- ============================================================================
-- FIX: BIGINT Type Mismatch in calculate_completion_percentage()
-- ============================================================================
--
-- Issue: PostgreSQL COUNT() returns BIGINT, but function declared INTEGER
-- Impact: Type coercion works but causes test failures
-- Fix: Change return type declarations from INTEGER to BIGINT
--
-- Created: 2025-11-12
-- ============================================================================

\echo '========================================='
\echo 'Fixing BIGINT type mismatch...'
\echo '========================================='

-- Drop existing function (if exists)
DROP FUNCTION IF EXISTS calculate_completion_percentage(INTEGER);

-- Recreate with corrected BIGINT return types
CREATE OR REPLACE FUNCTION calculate_completion_percentage(task_id_param INTEGER)
RETURNS TABLE(
    total_tasks BIGINT,           -- ✅ Changed from INTEGER to BIGINT
    completed_tasks BIGINT,       -- ✅ Changed from INTEGER to BIGINT
    in_progress_tasks BIGINT,     -- ✅ Changed from INTEGER to BIGINT
    pending_tasks BIGINT,         -- ✅ Changed from INTEGER to BIGINT
    completion_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE task_tree AS (
        -- Base: specified task
        SELECT
            t.id,
            t.parent_task_id,
            t.status,
            t.task_type
        FROM tasks t
        WHERE t.id = task_id_param

        UNION ALL

        -- Recursive: all descendants
        SELECT
            t.id,
            t.parent_task_id,
            t.status,
            t.task_type
        FROM tasks t
        INNER JOIN task_tree tt ON t.parent_task_id = tt.id
    ),
    completion_stats AS (
        SELECT
            COUNT(*) FILTER (WHERE task_type IN ('task', 'subtask')) as total,
            COUNT(*) FILTER (WHERE status = 'completed' AND task_type IN ('task', 'subtask')) as completed,
            COUNT(*) FILTER (WHERE status = 'in_progress' AND task_type IN ('task', 'subtask')) as in_progress,
            COUNT(*) FILTER (WHERE status = 'pending' AND task_type IN ('task', 'subtask')) as pending
        FROM task_tree
    )
    SELECT
        total,
        completed,
        in_progress,
        pending,
        CASE
            WHEN total = 0 THEN 0
            ELSE ROUND((completed::NUMERIC / total::NUMERIC) * 100, 1)
        END
    FROM completion_stats;
END;
$$ LANGUAGE plpgsql;

-- Verify function was created successfully
SELECT
    routine_name,
    data_type,
    dtd_identifier
FROM information_schema.routines
WHERE routine_name = 'calculate_completion_percentage';

\echo '✅ BIGINT type mismatch fixed!'
\echo ''
