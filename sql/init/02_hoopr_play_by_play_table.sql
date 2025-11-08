-- ==============================================================================
-- HoopR Play-by-Play Table - NBA Event-Level Data
-- ==============================================================================
--
-- Stores play-by-play events from NBA games with shot zone classification
--
-- Data sources:
--   - ESPN/hoopR API: Play-by-play events
--   - Internal computation: Shot zone, distance, angle classifications
--
-- Table size: ~6.16M shots across 28,770 games (2002-2024)
--
-- Usage:
--   This script runs automatically when PostgreSQL container initializes
--   Depends on: 01_games_table.sql (for game_id foreign key)
--
-- ==============================================================================

-- Drop existing table if it exists (for clean reinitialization)
DROP TABLE IF EXISTS hoopr_play_by_play CASCADE;

-- ==============================================================================
-- Create Play-by-Play Table
-- ==============================================================================

CREATE TABLE hoopr_play_by_play (
    -- Identifiers (composite primary key: game + sequence)
    game_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,

    -- Event identification
    type_id INTEGER,  -- Numeric event type (e.g., 92 = Jump Shot)
    type_text TEXT,  -- Event type description (e.g., "Jump Shot", "Defensive Rebound")
    text TEXT,  -- Full event description with player names and outcomes

    -- Timing information
    period INTEGER,  -- Quarter/period (1-4 regular, 5+ overtime)
    clock_display_value TEXT,  -- Game clock as string (e.g., "7:58")
    clock_minutes INTEGER,  -- Minutes remaining in period
    clock_seconds DOUBLE PRECISION,  -- Seconds remaining in period

    -- Team information
    team_id INTEGER,  -- Offensive team (team with possession)
    opponent_team_id INTEGER,  -- Defensive team
    home_team_id INTEGER,  -- Home team for this game
    away_team_id INTEGER,  -- Away team for this game

    -- Player attribution (up to 3 players per event)
    athlete_id_1 INTEGER,  -- Primary player (shooter, rebounder, turnover committer)
    athlete_id_2 INTEGER,  -- Secondary player (assister, blocker, stealer)
    athlete_id_3 INTEGER,  -- Tertiary player (rare, for multiple fouls)

    -- Play outcome flags
    scoring_play INTEGER DEFAULT 0,  -- Boolean (0/1): whether points were scored
    shooting_play INTEGER DEFAULT 0,  -- Boolean (0/1): whether a shot was attempted
    score_value INTEGER DEFAULT 0,  -- Points scored on this play (0, 1, 2, or 3)

    -- Running scores (after this event)
    home_score INTEGER,
    away_score INTEGER,

    -- Shot location (ESPN coordinates)
    coordinate_x DOUBLE PRECISION,  -- X coordinate from ESPN API
    coordinate_y DOUBLE PRECISION,  -- Y coordinate from ESPN API

    -- Shot classification (computed from coordinates)
    shot_zone TEXT,  -- NBA-standard zone (e.g., "restricted_area", "three_left_corner")
    shot_distance DOUBLE PRECISION,  -- Distance from basket in feet
    shot_angle DOUBLE PRECISION,  -- Angle from basket in degrees (0-360)

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (game_id, sequence_number),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CHECK (scoring_play IN (0, 1)),
    CHECK (shooting_play IN (0, 1)),
    CHECK (score_value IN (0, 1, 2, 3)),
    CHECK (period >= 1),
    CHECK (shot_distance IS NULL OR shot_distance >= 0),
    CHECK (shot_angle IS NULL OR (shot_angle >= 0 AND shot_angle <= 360))
);

-- ==============================================================================
-- Indexes for Performance
-- ==============================================================================

-- Primary query patterns: game lookups, player stats, team stats, shot analytics

-- Game-level queries (most common)
CREATE INDEX idx_pbp_game ON hoopr_play_by_play(game_id);

-- Player analytics
CREATE INDEX idx_pbp_athlete_1 ON hoopr_play_by_play(athlete_id_1) WHERE athlete_id_1 IS NOT NULL;
CREATE INDEX idx_pbp_athlete_2 ON hoopr_play_by_play(athlete_id_2) WHERE athlete_id_2 IS NOT NULL;

-- Team analytics
CREATE INDEX idx_pbp_team ON hoopr_play_by_play(team_id) WHERE team_id IS NOT NULL;

-- Shot zone analytics (partial indexes for shooting plays only)
CREATE INDEX idx_pbp_shot_zone ON hoopr_play_by_play(shot_zone)
WHERE shooting_play = 1 AND shot_zone IS NOT NULL;

CREATE INDEX idx_pbp_shot_distance ON hoopr_play_by_play(shot_distance)
WHERE shooting_play = 1 AND shot_distance IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX idx_pbp_game_zone ON hoopr_play_by_play(game_id, shot_zone)
WHERE shooting_play = 1 AND shot_zone IS NOT NULL;

CREATE INDEX idx_pbp_player_zone ON hoopr_play_by_play(athlete_id_1, shot_zone)
WHERE shooting_play = 1 AND shot_zone IS NOT NULL;

CREATE INDEX idx_pbp_team_zone ON hoopr_play_by_play(team_id, shot_zone)
WHERE shooting_play = 1 AND shot_zone IS NOT NULL;

-- Index for identifying shots needing classification (backfill monitoring)
CREATE INDEX idx_pbp_unclassified_shots ON hoopr_play_by_play(game_id)
WHERE shooting_play = 1
  AND shot_zone IS NULL
  AND coordinate_x IS NOT NULL
  AND coordinate_y IS NOT NULL;

-- ==============================================================================
-- Comments and Documentation
-- ==============================================================================

COMMENT ON TABLE hoopr_play_by_play IS
'Play-by-play events for NBA games from ESPN/hoopR API. Includes shot zone classification computed from court coordinates.';

COMMENT ON COLUMN hoopr_play_by_play.game_id IS
'Unique game identifier from ESPN API (e.g., "401584893")';

COMMENT ON COLUMN hoopr_play_by_play.sequence_number IS
'Sequential event number within game (starts at 1)';

COMMENT ON COLUMN hoopr_play_by_play.type_id IS
'Numeric event type ID. Common values: 92 (Jump Shot), 57 (Layup), 1 (Field Goal Made), 574 (Defensive Rebound), etc.';

COMMENT ON COLUMN hoopr_play_by_play.type_text IS
'Human-readable event type. Examples: "Jump Shot", "Defensive Rebound", "Bad Pass\nTurnover"';

COMMENT ON COLUMN hoopr_play_by_play.text IS
'Full event description with player names. Example: "LeBron James makes 20-foot jumper (Anthony Davis assists)"';

COMMENT ON COLUMN hoopr_play_by_play.athlete_id_1 IS
'Primary player ID: shooter for shots, rebounder for rebounds, turnover committer for turnovers, fouler for fouls';

COMMENT ON COLUMN hoopr_play_by_play.athlete_id_2 IS
'Secondary player ID: assister for made shots, blocker for blocked shots, stealer for steals, foul drawer for fouls';

COMMENT ON COLUMN hoopr_play_by_play.athlete_id_3 IS
'Tertiary player ID (rare): used for events with 3+ players (e.g., multiple fouls)';

COMMENT ON COLUMN hoopr_play_by_play.shooting_play IS
'Boolean (0/1): 1 if this event is a shot attempt (includes makes, misses, and blocks)';

COMMENT ON COLUMN hoopr_play_by_play.scoring_play IS
'Boolean (0/1): 1 if points were scored on this play (made shots and free throws)';

COMMENT ON COLUMN hoopr_play_by_play.coordinate_x IS
'Shot location X coordinate from ESPN API. Typically ranges 0-94 (feet from baseline). NULL for non-shooting plays.';

COMMENT ON COLUMN hoopr_play_by_play.coordinate_y IS
'Shot location Y coordinate from ESPN API. Typically ranges 0-50 (feet from sideline). NULL for non-shooting plays.';

COMMENT ON COLUMN hoopr_play_by_play.shot_zone IS
'NBA-standard shot zone classification. Values: restricted_area, paint_non_ra, mid_range_left, mid_range_center, mid_range_right, three_left_corner, three_right_corner, three_above_break_left, three_above_break_center, three_above_break_right, backcourt. NULL for non-shooting plays or unclassified shots.';

COMMENT ON COLUMN hoopr_play_by_play.shot_distance IS
'Distance from basket in feet, calculated from court coordinates. NULL for non-shooting plays or missing coordinates.';

COMMENT ON COLUMN hoopr_play_by_play.shot_angle IS
'Angle from basket in degrees (0-360), where 0° = directly above basket, 90° = right sideline, 180° = baseline, 270° = left sideline. NULL for non-shooting plays or missing coordinates.';

-- ==============================================================================
-- Shot Zone Classifications
-- ==============================================================================

-- Zone definitions (from /Users/ryanranft/nba-mcp-synthesis/mcp_server/zone_classifier.py):
--
-- 1. RESTRICTED AREA: Distance <= 4 feet from basket
-- 2. PAINT (NON-RA): 4 < distance <= 8 feet
-- 3. MID-RANGE: 8 < distance < 23.75 feet (non-corner) or < 22 feet (corner)
--    - Left: angle 180-270 degrees
--    - Center: angle 270-360 or 0-90 degrees
--    - Right: angle 90-180 degrees
-- 4. THREE-POINT (CORNER): distance >= 22 feet, angle 135-180 or 0-45 degrees
--    - Left corner: angle 135-180
--    - Right corner: angle 0-45
-- 5. THREE-POINT (ABOVE BREAK): distance >= 23.75 feet, angle 45-135 degrees
--    - Left: angle 45-75 degrees
--    - Center: angle 75-105 degrees
--    - Right: angle 105-135 degrees
-- 6. BACKCOURT: distance > 47 feet (half court+)

-- ==============================================================================
-- Data Quality Notes
-- ==============================================================================

-- IMPORTANT NOTES:
--
-- 1. Shot zone classification: 6,158,912 / 6,158,912 shots (100.0000%) classified
--    - Fixed in 2025-01-07 using contextual inference for edge cases
--    - 82 shots required manual fixes (missing team_id, athlete_id_1, or text)
--
-- 2. Historical data quality (2002-2024):
--    - Play-by-play data: 100% internal consistency across all years
--    - Missing data: <0.001% of shots had NULL coordinates (pre-2007 games)
--
-- 3. Coordinate system:
--    - ESPN uses feet-based coordinates
--    - Origin at home team's baseline (left side on TV)
--    - X: 0-94 feet (baseline to baseline)
--    - Y: 0-50 feet (sideline to sideline)
--
-- 4. Event types for box score generation (key type_ids):
--    - Shots: 1, 92, 93, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 557, etc.
--    - Free throws: 80, 81, 82, 83, 84, 85, 86
--    - Rebounds: 561 (Offensive), 574 (Defensive)
--    - Turnovers: 62, 63, 64, 67, 70, 74, 84, 86
--    - Assists: Embedded in shot event text (not separate event)
--    - Blocks: Embedded in shot event text (not separate event)
--    - Steals: Embedded in turnover event text (not separate event)
--    - Fouls: 42, 44, 45, 46, 47, 48, 49, 50, etc.

-- ==============================================================================
-- Example Queries
-- ==============================================================================

-- Get all shots from a specific game
-- SELECT game_id, sequence_number, athlete_id_1, shot_zone, shot_distance, score_value
-- FROM hoopr_play_by_play
-- WHERE game_id = '401584893'
--   AND shooting_play = 1
-- ORDER BY sequence_number;

-- Player shot chart (restricted area vs three-point)
-- SELECT
--     shot_zone,
--     COUNT(*) as attempts,
--     SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as makes,
--     ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct
-- FROM hoopr_play_by_play
-- WHERE athlete_id_1 = 2544  -- LeBron James
--   AND shooting_play = 1
--   AND shot_zone IS NOT NULL
-- GROUP BY shot_zone
-- ORDER BY attempts DESC;

-- Team corner three-point accuracy
-- SELECT
--     team_id,
--     COUNT(*) as corner_3pa,
--     SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as corner_3pm,
--     ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as corner_3p_pct
-- FROM hoopr_play_by_play
-- WHERE shot_zone IN ('three_left_corner', 'three_right_corner')
--   AND shooting_play = 1
-- GROUP BY team_id
-- ORDER BY corner_3p_pct DESC
-- LIMIT 10;

-- Shots by distance range (0-5ft, 5-10ft, 10-15ft, etc.)
-- SELECT
--     FLOOR(shot_distance / 5) * 5 as distance_range_start,
--     FLOOR(shot_distance / 5) * 5 + 5 as distance_range_end,
--     COUNT(*) as attempts,
--     ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct
-- FROM hoopr_play_by_play
-- WHERE shooting_play = 1
--   AND shot_distance IS NOT NULL
-- GROUP BY FLOOR(shot_distance / 5)
-- ORDER BY distance_range_start;

-- Find unclassified shots needing backfill
-- SELECT
--     COUNT(*) as unclassified_shots,
--     COUNT(DISTINCT game_id) as games_affected
-- FROM hoopr_play_by_play
-- WHERE shooting_play = 1
--   AND shot_zone IS NULL
--   AND coordinate_x IS NOT NULL
--   AND coordinate_y IS NOT NULL;

-- ==============================================================================
-- End of schema
-- ==============================================================================
