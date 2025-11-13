-- Claude Tasks Database Schema
-- Purpose: Persistent task tracking across Claude Code sessions
-- Part of: Automatic Task Tracking System (Phase 3)

-- Create database (run this separately as superuser)
-- CREATE DATABASE claude_tasks;

-- Connect to claude_tasks database before running the rest

-- Tasks table - stores all tasks
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    active_form TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),

    -- Context
    project VARCHAR(100) DEFAULT 'nba-mcp-synthesis',
    context TEXT,  -- Additional context about the task
    parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,  -- For sub-tasks

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,  -- When status changed to in_progress
    completed_at TIMESTAMP,  -- When status changed to completed
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,

    -- Tracking
    created_by VARCHAR(100) DEFAULT 'claude-code',
    session_id VARCHAR(100),  -- For grouping tasks from same session
    conversation_id VARCHAR(100),  -- For tracking across conversations

    -- Notes and blockers
    notes TEXT,  -- General notes about the task
    blocker_reason TEXT,  -- Why task is blocked

    CONSTRAINT valid_timestamps CHECK (
        (started_at IS NULL OR started_at >= created_at) AND
        (completed_at IS NULL OR completed_at >= created_at)
    )
);

-- Task tags - for categorization
CREATE TABLE IF NOT EXISTS task_tags (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(task_id, tag)
);

-- Task history - audit trail of all status changes
CREATE TABLE IF NOT EXISTS task_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(100) DEFAULT 'claude-code',
    notes TEXT
);

-- Handoff documents - for complex multi-session work
CREATE TABLE IF NOT EXISTS handoff_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    task_ids INTEGER[],  -- Array of related task IDs
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Optional expiration
    is_active BOOLEAN DEFAULT TRUE
);

-- Session metadata - track Claude Code sessions
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    tasks_created INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_conversation_id ON tasks(conversation_id);
CREATE INDEX IF NOT EXISTS idx_task_tags_tag ON task_tags(tag);
CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_handoff_active ON handoff_documents(is_active) WHERE is_active = TRUE;

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on tasks table
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to track status changes in history
CREATE OR REPLACE FUNCTION track_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only insert if status actually changed
    IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO task_history (task_id, previous_status, new_status, notes)
        VALUES (NEW.id, OLD.status, NEW.status, NEW.notes);

        -- Update timestamps based on status
        IF NEW.status = 'in_progress' AND OLD.status != 'in_progress' THEN
            NEW.started_at = NOW();
        ELSIF NEW.status = 'completed' AND OLD.status != 'completed' THEN
            NEW.completed_at = NOW();
            -- Calculate actual duration if started_at exists
            IF NEW.started_at IS NOT NULL THEN
                NEW.actual_duration_minutes = EXTRACT(EPOCH FROM (NOW() - NEW.started_at)) / 60;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to track status changes
CREATE TRIGGER track_task_status_changes
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION track_status_change();

-- Views for common queries

-- Active tasks (pending or in_progress)
CREATE OR REPLACE VIEW active_tasks AS
SELECT
    t.id,
    t.content,
    t.active_form,
    t.status,
    t.priority,
    t.project,
    t.created_at,
    t.started_at,
    ARRAY_AGG(tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags,
    CASE
        WHEN t.started_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (NOW() - t.started_at)) / 60
        ELSE NULL
    END as minutes_in_progress
FROM tasks t
LEFT JOIN task_tags tt ON t.id = tt.task_id
WHERE t.status IN ('pending', 'in_progress')
GROUP BY t.id
ORDER BY
    CASE t.status
        WHEN 'in_progress' THEN 1
        WHEN 'pending' THEN 2
    END,
    t.priority DESC,
    t.created_at;

-- Recent completed tasks
CREATE OR REPLACE VIEW recent_completed_tasks AS
SELECT
    t.id,
    t.content,
    t.status,
    t.priority,
    t.completed_at,
    t.actual_duration_minutes,
    ARRAY_AGG(tt.tag) FILTER (WHERE tt.tag IS NOT NULL) as tags
FROM tasks t
LEFT JOIN task_tags tt ON t.id = tt.task_id
WHERE t.status = 'completed'
    AND t.completed_at > NOW() - INTERVAL '7 days'
GROUP BY t.id
ORDER BY t.completed_at DESC;

-- Task statistics
CREATE OR REPLACE VIEW task_statistics AS
SELECT
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'blocked') as blocked_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
    AVG(actual_duration_minutes) FILTER (WHERE actual_duration_minutes IS NOT NULL) as avg_completion_time_minutes,
    COUNT(*) FILTER (WHERE completed_at > NOW() - INTERVAL '24 hours') as completed_last_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as created_last_24h
FROM tasks;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- Sample queries for testing
--
-- -- Get all active tasks
-- SELECT * FROM active_tasks;
--
-- -- Get task history for a specific task
-- SELECT * FROM task_history WHERE task_id = 1 ORDER BY changed_at;
--
-- -- Get statistics
-- SELECT * FROM task_statistics;
--
-- -- Find blocked tasks
-- SELECT id, content, blocker_reason FROM tasks WHERE status = 'blocked';
--
-- -- Find tasks by tag
-- SELECT t.* FROM tasks t
-- JOIN task_tags tt ON t.id = tt.task_id
-- WHERE tt.tag = 'mcp-implementation';
