-- Session Tracking Migration
-- Purpose: Add session_id column for tracking task creation across sessions
-- Part of: Enhancement Phase 1.1 - Session ID Auto-Generation

-- ============================================================================
-- STEP 1: ADD SESSION_ID COLUMN
-- ============================================================================

ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS session_id VARCHAR(50);

-- ============================================================================
-- STEP 2: ADD INDEX FOR SESSION QUERIES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);

-- ============================================================================
-- STEP 3: BACKFILL EXISTING TASKS (group by creation date)
-- ============================================================================

-- Generate session IDs for existing tasks grouped by creation date
WITH session_ids AS (
    SELECT DISTINCT DATE_TRUNC('day', created_at) as day,
           'historical_' || TO_CHAR(DATE_TRUNC('day', created_at), 'YYYYMMDD') as session_id
    FROM tasks
    WHERE session_id IS NULL
)
UPDATE tasks t
SET session_id = s.session_id
FROM session_ids s
WHERE DATE_TRUNC('day', t.created_at) = s.day
  AND t.session_id IS NULL;

-- ============================================================================
-- STEP 4: VERIFY MIGRATION
-- ============================================================================

DO $$
DECLARE
    null_sessions INTEGER;
BEGIN
    -- Check for tasks without session_id
    SELECT COUNT(*) INTO null_sessions
    FROM tasks
    WHERE session_id IS NULL;

    IF null_sessions > 0 THEN
        RAISE WARNING 'Warning: % tasks still have NULL session_id', null_sessions;
    ELSE
        RAISE NOTICE '✅ All tasks have session_id assigned';
    END IF;

    RAISE NOTICE '✅ Session tracking migration complete';
END $$;
