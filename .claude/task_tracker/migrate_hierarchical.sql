-- Hierarchical Master Task Tracking Migration
-- Purpose: Add support for unlimited nesting, master tasks, and resume view
-- Part of: Automatic Task Tracking System (Phase 3 Enhancement)

-- ============================================================================
-- STEP 1: ADD NEW COLUMNS
-- ============================================================================

-- Add task_type column (master/task/subtask)
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS task_type VARCHAR(20) DEFAULT 'task'
CHECK (task_type IN ('master', 'task', 'subtask'));

-- Add last_worked_at timestamp for resume view sorting
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS last_worked_at TIMESTAMP;

-- Add context_summary for project descriptions
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS context_summary TEXT;

-- Add depth_level for performance optimization
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS depth_level INTEGER DEFAULT 0;

-- Add master_task_id for direct link to top-level master
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS master_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE;

-- ============================================================================
-- STEP 2: ADD INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_master_task_id ON tasks(master_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_last_worked_at ON tasks(last_worked_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_tasks_depth_level ON tasks(depth_level);

-- ============================================================================
-- STEP 3: DROP OLD TRIGGER IF EXISTS (for clean migration)
-- ============================================================================

DROP TRIGGER IF EXISTS update_task_last_worked ON tasks;
DROP FUNCTION IF EXISTS update_last_worked_at();

-- ============================================================================
-- STEP 4: CREATE TRIGGER FUNCTION TO AUTO-UPDATE last_worked_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_last_worked_at()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_worked_at when status changes to in_progress or completed
    IF (NEW.status = 'in_progress' AND (OLD.status IS NULL OR OLD.status != 'in_progress')) OR
       (NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status != 'completed')) THEN
        NEW.last_worked_at = NOW();

        -- Also update parent's last_worked_at (if exists)
        IF NEW.parent_task_id IS NOT NULL THEN
            UPDATE tasks
            SET last_worked_at = NOW()
            WHERE id = NEW.parent_task_id;
        END IF;

        -- Also update master task's last_worked_at (if exists and different from parent)
        IF NEW.master_task_id IS NOT NULL AND
           (NEW.parent_task_id IS NULL OR NEW.master_task_id != NEW.parent_task_id) THEN
            UPDATE tasks
            SET last_worked_at = NOW()
            WHERE id = NEW.master_task_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 5: CREATE TRIGGER
-- ============================================================================

CREATE TRIGGER update_task_last_worked
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_last_worked_at();

-- ============================================================================
-- STEP 6: CREATE VIEW FOR MASTER TASKS WITH PROGRESS
-- ============================================================================

CREATE OR REPLACE VIEW master_tasks_progress AS
WITH RECURSIVE master_tasks_with_children AS (
    -- Base case: all master tasks with their direct children
    SELECT
        m.id as master_id,
        m.content as master_content,
        m.active_form as master_active_form,
        m.status as master_status,
        m.priority as master_priority,
        m.context_summary,
        m.last_worked_at,
        m.created_at,
        t.id as child_id,
        t.status as child_status,
        t.task_type as child_type,
        1 as level
    FROM tasks m
    LEFT JOIN tasks t ON t.master_task_id = m.id
    WHERE m.task_type = 'master'

    UNION ALL

    -- Recursive case: get all descendants
    SELECT
        mtc.master_id,
        mtc.master_content,
        mtc.master_active_form,
        mtc.master_status,
        mtc.master_priority,
        mtc.context_summary,
        mtc.last_worked_at,
        mtc.created_at,
        t.id,
        t.status,
        t.task_type,
        mtc.level + 1
    FROM master_tasks_with_children mtc
    INNER JOIN tasks t ON t.parent_task_id = mtc.child_id
    WHERE mtc.level < 20  -- Prevent infinite recursion (20 levels max)
),
aggregated_stats AS (
    SELECT
        master_id,
        master_content,
        master_active_form,
        master_status,
        master_priority,
        context_summary,
        last_worked_at,
        created_at,
        COUNT(*) FILTER (WHERE child_type IN ('task', 'subtask') AND child_id IS NOT NULL) as total_tasks,
        COUNT(*) FILTER (WHERE child_status = 'completed' AND child_type IN ('task', 'subtask')) as completed_tasks,
        COUNT(*) FILTER (WHERE child_status = 'in_progress' AND child_type IN ('task', 'subtask')) as in_progress_tasks,
        COUNT(*) FILTER (WHERE child_status = 'pending' AND child_type IN ('task', 'subtask')) as pending_tasks,
        COUNT(*) FILTER (WHERE child_status = 'blocked' AND child_type IN ('task', 'subtask')) as blocked_tasks,
        MAX(level) as max_depth
    FROM master_tasks_with_children
    GROUP BY master_id, master_content, master_active_form, master_status, master_priority,
             context_summary, last_worked_at, created_at
)
SELECT
    master_id,
    master_content,
    master_active_form,
    master_status,
    master_priority,
    context_summary,
    last_worked_at,
    created_at,
    total_tasks,
    completed_tasks,
    in_progress_tasks,
    pending_tasks,
    blocked_tasks,
    CASE
        WHEN total_tasks = 0 THEN 0
        ELSE ROUND((completed_tasks::NUMERIC / total_tasks::NUMERIC) * 100, 1)
    END as completion_percentage,
    CASE
        WHEN last_worked_at IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (NOW() - last_worked_at)) / 3600
    END as hours_since_last_worked,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 as days_since_created,
    max_depth
FROM aggregated_stats
ORDER BY
    CASE master_status
        WHEN 'in_progress' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'blocked' THEN 3
        WHEN 'completed' THEN 4
        WHEN 'cancelled' THEN 5
    END,
    last_worked_at DESC NULLS LAST;

-- ============================================================================
-- STEP 7: CREATE FUNCTION TO GET TASK HIERARCHY
-- ============================================================================

CREATE OR REPLACE FUNCTION get_task_hierarchy(root_task_id INTEGER, max_depth_param INTEGER DEFAULT NULL)
RETURNS TABLE(
    task_id INTEGER,
    task_content TEXT,
    task_active_form TEXT,
    task_status VARCHAR,
    task_priority VARCHAR,
    task_type VARCHAR,
    parent_id INTEGER,
    master_id INTEGER,
    depth INTEGER,
    path INTEGER[],
    last_worked TIMESTAMP,
    created TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE task_tree AS (
        -- Base case: root task
        SELECT
            t.id,
            t.content,
            t.active_form,
            t.status,
            t.priority,
            t.task_type,
            t.parent_task_id,
            t.master_task_id,
            0 as depth,
            ARRAY[t.id] as path,
            t.last_worked_at,
            t.created_at
        FROM tasks t
        WHERE t.id = root_task_id

        UNION ALL

        -- Recursive case: children
        SELECT
            t.id,
            t.content,
            t.active_form,
            t.status,
            t.priority,
            t.task_type,
            t.parent_task_id,
            t.master_task_id,
            tt.depth + 1,
            tt.path || t.id,
            t.last_worked_at,
            t.created_at
        FROM tasks t
        INNER JOIN task_tree tt ON t.parent_task_id = tt.id
        WHERE NOT t.id = ANY(tt.path)  -- Prevent cycles
          AND (max_depth_param IS NULL OR tt.depth < max_depth_param)
    )
    SELECT
        task_tree.id,
        task_tree.content,
        task_tree.active_form,
        task_tree.status,
        task_tree.priority,
        task_tree.task_type,
        task_tree.parent_task_id,
        task_tree.master_task_id,
        task_tree.depth,
        task_tree.path,
        task_tree.last_worked_at,
        task_tree.created_at
    FROM task_tree
    ORDER BY path;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 8: CREATE FUNCTION TO CALCULATE COMPLETION PERCENTAGE
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_completion_percentage(task_id_param INTEGER)
RETURNS TABLE(
    total_tasks BIGINT,           -- Changed from INTEGER to match COUNT() return type
    completed_tasks BIGINT,       -- Changed from INTEGER to match COUNT() return type
    in_progress_tasks BIGINT,     -- Changed from INTEGER to match COUNT() return type
    pending_tasks BIGINT,         -- Changed from INTEGER to match COUNT() return type
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

-- ============================================================================
-- STEP 9: BACKFILL EXISTING DATA (if any)
-- ============================================================================

-- Set all existing tasks to task_type='task' if not already set
UPDATE tasks
SET task_type = 'task'
WHERE task_type IS NULL;

-- Set depth_level based on parent hierarchy
WITH RECURSIVE depth_calc AS (
    -- Root tasks (no parent)
    SELECT id, 0 as calc_depth
    FROM tasks
    WHERE parent_task_id IS NULL

    UNION ALL

    -- Children
    SELECT t.id, dc.calc_depth + 1
    FROM tasks t
    INNER JOIN depth_calc dc ON t.parent_task_id = dc.id
)
UPDATE tasks t
SET depth_level = dc.calc_depth
FROM depth_calc dc
WHERE t.id = dc.id;

-- Set master_task_id to self for orphaned root tasks
UPDATE tasks
SET master_task_id = id
WHERE parent_task_id IS NULL
  AND master_task_id IS NULL
  AND task_type != 'master';

-- ============================================================================
-- STEP 10: VERIFY MIGRATION
-- ============================================================================

-- Check that all columns were added
DO $$
DECLARE
    missing_columns TEXT[];
BEGIN
    SELECT ARRAY_AGG(column_name)
    INTO missing_columns
    FROM (
        SELECT unnest(ARRAY['task_type', 'last_worked_at', 'context_summary', 'depth_level', 'master_task_id']) as column_name
    ) required
    WHERE column_name NOT IN (
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'tasks' AND table_schema = 'public'
    );

    IF missing_columns IS NOT NULL THEN
        RAISE EXCEPTION 'Missing columns: %', missing_columns;
    END IF;

    RAISE NOTICE '✅ All columns added successfully';
END $$;

-- Check that view was created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.views
        WHERE table_name = 'master_tasks_progress' AND table_schema = 'public'
    ) THEN
        RAISE EXCEPTION 'View master_tasks_progress was not created';
    END IF;

    RAISE NOTICE '✅ View master_tasks_progress created successfully';
END $$;

-- Check that functions were created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'get_task_hierarchy'
    ) THEN
        RAISE EXCEPTION 'Function get_task_hierarchy was not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'calculate_completion_percentage'
    ) THEN
        RAISE EXCEPTION 'Function calculate_completion_percentage was not created';
    END IF;

    RAISE NOTICE '✅ Functions created successfully';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Print summary
DO $$
DECLARE
    task_count INTEGER;
    master_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO task_count FROM tasks;
    SELECT COUNT(*) INTO master_count FROM tasks WHERE task_type = 'master';

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '✅ HIERARCHICAL TASK TRACKING MIGRATION COMPLETE';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Columns Added:';
    RAISE NOTICE '  - task_type (master/task/subtask)';
    RAISE NOTICE '  - last_worked_at (timestamp)';
    RAISE NOTICE '  - context_summary (text)';
    RAISE NOTICE '  - depth_level (integer)';
    RAISE NOTICE '  - master_task_id (foreign key)';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes Added: 5';
    RAISE NOTICE 'Triggers Added: 1 (update_last_worked_at)';
    RAISE NOTICE 'Views Added: 1 (master_tasks_progress)';
    RAISE NOTICE 'Functions Added: 2 (get_task_hierarchy, calculate_completion_percentage)';
    RAISE NOTICE '';
    RAISE NOTICE 'Current Database Status:';
    RAISE NOTICE '  - Total tasks: %', task_count;
    RAISE NOTICE '  - Master tasks: %', master_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Update task_tracker_mcp.py with new tools';
    RAISE NOTICE '  2. Enhance user_prompt_submit.py hook';
    RAISE NOTICE '  3. Update /resume command';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
END $$;
