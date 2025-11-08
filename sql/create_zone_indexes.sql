-- ============================================================================
-- Create Performance Indexes for Shot Zone Queries
-- ============================================================================
-- Description: Adds indexes to optimize zone-based queries and analytics
-- Date: 2025-11-06
-- Impact: Improves query performance for zone filtering and aggregations
-- ============================================================================

-- Index for zone-based queries (most common use case)
-- Partial index: only shooting plays with classified zones
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_shot_zone
ON hoopr_play_by_play(shot_zone)
WHERE shooting_play = 1
  AND shot_zone IS NOT NULL;

-- Index for distance-based queries and analytics
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_shot_distance
ON hoopr_play_by_play(shot_distance)
WHERE shooting_play = 1
  AND shot_distance IS NOT NULL;

-- Composite index for zone + game queries (common pattern)
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_game_zone
ON hoopr_play_by_play(game_id, shot_zone)
WHERE shooting_play = 1
  AND shot_zone IS NOT NULL;

-- Composite index for player zone analytics
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_player_zone
ON hoopr_play_by_play(athlete_id_1, shot_zone)
WHERE shooting_play = 1
  AND shot_zone IS NOT NULL;

-- Composite index for team zone analytics
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_team_zone
ON hoopr_play_by_play(team_id, shot_zone)
WHERE shooting_play = 1
  AND shot_zone IS NOT NULL;

-- Index for identifying shots needing classification (backfill monitoring)
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_unclassified_shots
ON hoopr_play_by_play(game_id)
WHERE shooting_play = 1
  AND shot_zone IS NULL
  AND coordinate_x IS NOT NULL
  AND coordinate_y IS NOT NULL;

-- Verify indexes created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'hoopr_play_by_play'
  AND indexname LIKE '%zone%'
ORDER BY indexname;

-- Show index sizes (helpful for monitoring)
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND relname = 'hoopr_play_by_play'
  AND indexrelname LIKE '%zone%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Test query performance with zone filter
EXPLAIN ANALYZE
SELECT shot_zone, COUNT(*) as shot_count
FROM hoopr_play_by_play
WHERE shooting_play = 1
  AND shot_zone IS NOT NULL
GROUP BY shot_zone
ORDER BY shot_count DESC;

-- ============================================================================
-- Index creation complete
-- Expected query performance: <100ms for zone-filtered queries
-- ============================================================================
