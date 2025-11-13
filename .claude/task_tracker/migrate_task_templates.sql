-- Task Templates Migration
-- Phase 3 UX Enhancement: Task templates for common workflows
-- Created: 2025-11-12

-- Create task_templates table
CREATE TABLE IF NOT EXISTS task_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),
    structure JSONB NOT NULL,
    is_builtin BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    usage_count INTEGER DEFAULT 0
);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_task_templates_category ON task_templates(category);
CREATE INDEX IF NOT EXISTS idx_task_templates_builtin ON task_templates(is_builtin);
CREATE INDEX IF NOT EXISTS idx_task_templates_name ON task_templates(name);

-- Insert built-in templates
INSERT INTO task_templates (name, description, category, structure, is_builtin, created_by) VALUES
(
    'Feature Implementation',
    'Standard workflow for implementing a new feature',
    'development',
    '{
        "tasks": [
            {"content": "Design and plan feature architecture", "priority": "high"},
            {"content": "Implement core functionality", "priority": "high"},
            {"content": "Write unit tests", "priority": "medium"},
            {"content": "Write integration tests", "priority": "medium"},
            {"content": "Update documentation", "priority": "medium"},
            {"content": "Code review and refinement", "priority": "high"},
            {"content": "Deploy to staging", "priority": "high"},
            {"content": "QA testing", "priority": "medium"},
            {"content": "Deploy to production", "priority": "critical"},
            {"content": "Monitor and verify", "priority": "high"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Bug Fix',
    'Workflow for investigating and fixing bugs',
    'maintenance',
    '{
        "tasks": [
            {"content": "Reproduce and investigate bug", "priority": "high"},
            {"content": "Identify root cause", "priority": "high"},
            {"content": "Implement fix", "priority": "high"},
            {"content": "Write regression tests", "priority": "high"},
            {"content": "Test fix in development", "priority": "medium"},
            {"content": "Deploy to staging", "priority": "high"},
            {"content": "Verify fix in staging", "priority": "high"},
            {"content": "Deploy hotfix to production", "priority": "critical"},
            {"content": "Monitor production", "priority": "high"},
            {"content": "Document fix and prevention", "priority": "low"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Research Project',
    'Structured approach to research and evaluation',
    'research',
    '{
        "tasks": [
            {"content": "Define research goals and success criteria", "priority": "high"},
            {"content": "Literature review and competitive analysis", "priority": "medium"},
            {"content": "Setup development environment", "priority": "medium"},
            {"content": "Build proof of concept", "priority": "high"},
            {"content": "Benchmark and evaluate performance", "priority": "high"},
            {"content": "Assess pros and cons", "priority": "medium"},
            {"content": "Write recommendation report", "priority": "high"},
            {"content": "Present findings to stakeholders", "priority": "medium"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'System Integration',
    'Integrating with external systems or APIs',
    'integration',
    '{
        "tasks": [
            {"content": "Review integration requirements and API docs", "priority": "high"},
            {"content": "Design integration architecture", "priority": "high"},
            {"content": "Setup development credentials and access", "priority": "medium"},
            {"content": "Implement API client/connector", "priority": "high"},
            {"content": "Add error handling and retry logic", "priority": "high"},
            {"content": "Write integration tests", "priority": "medium"},
            {"content": "Test with staging environment", "priority": "high"},
            {"content": "Setup monitoring and alerting", "priority": "medium"},
            {"content": "Deploy to production", "priority": "high"},
            {"content": "Document integration and troubleshooting", "priority": "medium"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Database Migration',
    'Safe database schema changes',
    'database',
    '{
        "tasks": [
            {"content": "Design migration strategy and rollback plan", "priority": "critical"},
            {"content": "Write migration scripts (up and down)", "priority": "high"},
            {"content": "Test migration on development database", "priority": "high"},
            {"content": "Backup production database", "priority": "critical"},
            {"content": "Test migration on staging with production data copy", "priority": "critical"},
            {"content": "Schedule maintenance window", "priority": "high"},
            {"content": "Execute migration on production", "priority": "critical"},
            {"content": "Verify data integrity", "priority": "critical"},
            {"content": "Monitor application performance", "priority": "high"},
            {"content": "Document migration and lessons learned", "priority": "medium"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Code Refactoring',
    'Improving code quality without changing behavior',
    'maintenance',
    '{
        "tasks": [
            {"content": "Identify code smells and improvement areas", "priority": "medium"},
            {"content": "Write comprehensive tests for current behavior", "priority": "high"},
            {"content": "Refactor code incrementally", "priority": "high"},
            {"content": "Run test suite after each change", "priority": "high"},
            {"content": "Update documentation and comments", "priority": "medium"},
            {"content": "Code review", "priority": "high"},
            {"content": "Performance benchmarking", "priority": "medium"},
            {"content": "Deploy and monitor", "priority": "medium"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Security Audit',
    'Comprehensive security review',
    'security',
    '{
        "tasks": [
            {"content": "Review authentication and authorization", "priority": "critical"},
            {"content": "Check for SQL injection vulnerabilities", "priority": "critical"},
            {"content": "Review XSS prevention", "priority": "critical"},
            {"content": "Audit dependency vulnerabilities", "priority": "high"},
            {"content": "Check CSRF protection", "priority": "high"},
            {"content": "Review data encryption (at rest and in transit)", "priority": "critical"},
            {"content": "Test rate limiting and DDoS protection", "priority": "high"},
            {"content": "Audit logging and monitoring", "priority": "high"},
            {"content": "Document findings and remediation plan", "priority": "high"},
            {"content": "Implement critical fixes", "priority": "critical"}
        ]
    }'::jsonb,
    true,
    'system'
),
(
    'Production Deployment',
    'Safe production deployment process',
    'deployment',
    '{
        "tasks": [
            {"content": "Code freeze and final testing", "priority": "high"},
            {"content": "Prepare deployment checklist", "priority": "high"},
            {"content": "Backup current production state", "priority": "critical"},
            {"content": "Deploy to staging for final verification", "priority": "high"},
            {"content": "Schedule deployment window", "priority": "high"},
            {"content": "Execute deployment", "priority": "critical"},
            {"content": "Run smoke tests", "priority": "critical"},
            {"content": "Monitor error rates and performance", "priority": "critical"},
            {"content": "Verify critical user flows", "priority": "high"},
            {"content": "Send deployment notification", "priority": "medium"},
            {"content": "Document deployment and rollback procedure", "priority": "medium"}
        ]
    }'::jsonb,
    true,
    'system'
);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_task_template_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_template_timestamp
    BEFORE UPDATE ON task_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_task_template_updated_at();

-- Comments
COMMENT ON TABLE task_templates IS 'Templates for common task workflows (Phase 3)';
COMMENT ON COLUMN task_templates.structure IS 'JSON structure defining template tasks with priorities';
COMMENT ON COLUMN task_templates.is_builtin IS 'System-provided templates cannot be deleted';
COMMENT ON COLUMN task_templates.usage_count IS 'Number of times this template has been used';
