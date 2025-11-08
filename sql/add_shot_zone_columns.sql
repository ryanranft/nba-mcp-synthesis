-- ============================================================================
-- Add Shot Zone Classification Columns to hoopr_play_by_play
-- ============================================================================
-- Description: Adds zone classification, distance, and angle columns for
--              NBA-standard shot location tracking
-- Date: 2025-11-06
-- Affects: 6.16M shots across 28,770 games (2002-2024)
-- ============================================================================

-- Add zone classification columns
ALTER TABLE hoopr_play_by_play
ADD COLUMN IF NOT EXISTS shot_zone TEXT,
ADD COLUMN IF NOT EXISTS shot_distance DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS shot_angle DOUBLE PRECISION;

-- Add column comments for documentation
COMMENT ON COLUMN hoopr_play_by_play.shot_zone IS
'NBA-standard shot zone classification. Values: restricted_area, paint_non_ra, mid_range_left, mid_range_center, mid_range_right, three_left_corner, three_right_corner, three_above_break_left, three_above_break_center, three_above_break_right, backcourt. NULL for non-shooting plays.';

COMMENT ON COLUMN hoopr_play_by_play.shot_distance IS
'Distance from basket in feet, calculated from court coordinates. NULL for non-shooting plays or missing coordinates.';

COMMENT ON COLUMN hoopr_play_by_play.shot_angle IS
'Angle from basket in degrees (0-360), where 0° = directly above basket. NULL for non-shooting plays or missing coordinates.';

-- Verify columns added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'hoopr_play_by_play'
  AND column_name IN ('shot_zone', 'shot_distance', 'shot_angle')
ORDER BY column_name;

-- Show current shooting plays without zone classification
SELECT
    COUNT(*) as total_shots,
    COUNT(shot_zone) as shots_with_zone,
    COUNT(*) - COUNT(shot_zone) as shots_needing_classification,
    ROUND(100.0 * COUNT(shot_zone) / NULLIF(COUNT(*), 0), 2) as pct_classified
FROM hoopr_play_by_play
WHERE shooting_play = 1;

-- ============================================================================
-- Migration complete
-- Next step: Run sql/create_zone_indexes.sql to add performance indexes
-- ============================================================================
