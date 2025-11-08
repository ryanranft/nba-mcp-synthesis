-- ==============================================================================
-- HoopR Player Box Scores Table - NBA Player Statistics
-- ==============================================================================
--
-- Stores player box score statistics aggregated by ESPN/hoopR
--
-- Data sources:
--   - ESPN/hoopR API: Pre-aggregated player statistics
--
-- IMPORTANT: This table has known data quality issues (2013-2024)
-- - Hoopr reports 26-73% more stats than play-by-play computed values
-- - Always prefer computed_player_box for accurate statistics
-- - Use this table only for comparison/validation purposes
--
-- Usage:
--   This script runs automatically when PostgreSQL container initializes
--   Depends on: 01_games_table.sql (for game_id foreign key)
--
-- ==============================================================================

-- Drop existing table if it exists (for clean reinitialization)
DROP TABLE IF EXISTS hoopr_player_box CASCADE;

-- ==============================================================================
-- Create HoopR Player Box Scores Table
-- ==============================================================================

CREATE TABLE hoopr_player_box (
    -- Identifiers (composite primary key: game + player)
    game_id TEXT NOT NULL,
    athlete_id INTEGER NOT NULL,

    -- Team information
    team_id INTEGER,
    opponent_team_id INTEGER,

    -- Game metadata
    game_date DATE,
    season INTEGER,
    season_type INTEGER,  -- 2 = regular season, 3 = playoffs

    -- Time on court
    minutes INTEGER,  -- Minutes played

    -- Shooting statistics
    fgm INTEGER DEFAULT 0,  -- Field goals made
    fga INTEGER DEFAULT 0,  -- Field goals attempted
    fg_pct DECIMAL(5,3),  -- Field goal percentage (0.000-1.000)
    fg3m INTEGER DEFAULT 0,  -- Three-point field goals made
    fg3a INTEGER DEFAULT 0,  -- Three-point field goals attempted
    fg3_pct DECIMAL(5,3),  -- Three-point percentage (0.000-1.000)
    ftm INTEGER DEFAULT 0,  -- Free throws made
    fta INTEGER DEFAULT 0,  -- Free throws attempted
    ft_pct DECIMAL(5,3),  -- Free throw percentage (0.000-1.000)

    -- Rebounding
    oreb INTEGER DEFAULT 0,  -- Offensive rebounds
    dreb INTEGER DEFAULT 0,  -- Defensive rebounds
    rebounds INTEGER DEFAULT 0,  -- Total rebounds (oreb + dreb)

    -- Other statistics
    assists INTEGER DEFAULT 0,  -- Assists
    steals INTEGER DEFAULT 0,  -- Steals
    blocks INTEGER DEFAULT 0,  -- Blocks
    turnovers INTEGER DEFAULT 0,  -- Turnovers
    fouls INTEGER DEFAULT 0,  -- Personal fouls
    points INTEGER DEFAULT 0,  -- Points scored

    -- Player metadata
    athlete_position_abbreviation VARCHAR(5),  -- Position (e.g., "PG", "SF", "C")
    active INTEGER,  -- Boolean (0/1): whether player was active for this game

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (game_id, athlete_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CHECK (fgm >= 0 AND fgm <= fga),
    CHECK (fg3m >= 0 AND fg3m <= fg3a),
    CHECK (ftm >= 0 AND ftm <= fta),
    CHECK (fg_pct IS NULL OR (fg_pct >= 0 AND fg_pct <= 1)),
    CHECK (fg3_pct IS NULL OR (fg3_pct >= 0 AND fg3_pct <= 1)),
    CHECK (ft_pct IS NULL OR (ft_pct >= 0 AND ft_pct <= 1)),
    CHECK (rebounds = oreb + dreb),
    CHECK (active IN (0, 1, NULL))
);

-- ==============================================================================
-- Indexes for Performance
-- ==============================================================================

-- Primary query patterns: player lookups, team stats, game stats

-- Game-level queries
CREATE INDEX idx_hoopr_player_box_game ON hoopr_player_box(game_id);

-- Player analytics (most common)
CREATE INDEX idx_hoopr_player_box_athlete ON hoopr_player_box(athlete_id);

-- Team analytics
CREATE INDEX idx_hoopr_player_box_team ON hoopr_player_box(team_id);

-- Date range queries
CREATE INDEX idx_hoopr_player_box_date ON hoopr_player_box(game_date);

-- Season queries
CREATE INDEX idx_hoopr_player_box_season ON hoopr_player_box(season, season_type);

-- Composite index for player history
CREATE INDEX idx_hoopr_player_box_athlete_date ON hoopr_player_box(athlete_id, game_date);

-- Composite index for team rosters
CREATE INDEX idx_hoopr_player_box_team_date ON hoopr_player_box(team_id, game_date);

-- ==============================================================================
-- Comments and Documentation
-- ==============================================================================

COMMENT ON TABLE hoopr_player_box IS
'Player box score statistics from ESPN/hoopR API. WARNING: Contains known inflation issues (2013-2024). Always prefer computed_player_box for accurate statistics.';

COMMENT ON COLUMN hoopr_player_box.athlete_id IS
'Unique player identifier from ESPN API (e.g., 2544 for LeBron James)';

COMMENT ON COLUMN hoopr_player_box.season_type IS
'Season type: 2 = regular season, 3 = playoffs, 4 = all-star';

COMMENT ON COLUMN hoopr_player_box.minutes IS
'Minutes played in game. May not match play-by-play data due to Hoopr inflation.';

COMMENT ON COLUMN hoopr_player_box.rebounds IS
'Total rebounds (oreb + dreb). Should equal sum of offensive and defensive rebounds.';

COMMENT ON COLUMN hoopr_player_box.athlete_position_abbreviation IS
'Player position abbreviation: PG (Point Guard), SG (Shooting Guard), SF (Small Forward), PF (Power Forward), C (Center)';

COMMENT ON COLUMN hoopr_player_box.active IS
'Boolean (0/1): whether player was active (played) in this game. NULL if unknown.';

-- ==============================================================================
-- Data Quality Notes
-- ==============================================================================

-- CRITICAL DATA QUALITY ISSUES:
--
-- 1. HOOPR INFLATION (2013-2024):
--    - Years 2013-2024 show significant stat inflation compared to play-by-play
--    - Match rates range from 26.90% (2022) to 72.72% (2013)
--    - FGA inflation: Hoopr reports 3-14% more field goal attempts than play-by-play
--    - FGM inflation: Hoopr reports more made shots than actually occurred
--    - PTS inflation: Point totals don't match play-by-play computed scores
--
-- 2. RECOMMENDED APPROACH:
--    - ALWAYS use computed_player_box for accurate statistics
--    - Use this table ONLY for:
--      - Comparison with official box scores
--      - Validation of data quality
--      - Historical reference (pre-computed tables)
--
-- 3. DATA QUALITY BY YEAR:
--    - Tier A (2002, 2004): 98-99% match rate with play-by-play
--    - Tier B (2003, 2005-2012): 85-97% match rate
--    - Tier C (2013-2024): 27-73% match rate (NOT RELIABLE)
--
-- 4. WHY USE COMPUTED TABLES INSTEAD:
--    - computed_player_box: Calculated directly from play-by-play events
--    - 100% accurate to actual game events across all years
--    - No external data quality issues
--    - Internal consistency validated
--
-- 5. MIGRATION PATH:
--    - New applications: Use computed_player_box exclusively
--    - Existing applications: Migrate queries to computed_player_box
--    - This table: Keep for historical comparison only

-- ==============================================================================
-- Example Queries
-- ==============================================================================

-- Get player's stats for a specific game
-- SELECT athlete_id, points, rebounds, assists, fgm, fga, fg_pct
-- FROM hoopr_player_box
-- WHERE game_id = '401584893'
-- ORDER BY points DESC;

-- Player season averages (regular season only)
-- SELECT
--     athlete_id,
--     season,
--     COUNT(*) as games_played,
--     ROUND(AVG(points), 1) as ppg,
--     ROUND(AVG(rebounds), 1) as rpg,
--     ROUND(AVG(assists), 1) as apg,
--     ROUND(AVG(fg_pct), 3) as fg_pct
-- FROM hoopr_player_box
-- WHERE season = 2024
--   AND season_type = 2
--   AND active = 1
-- GROUP BY athlete_id, season
-- HAVING COUNT(*) >= 20  -- Min 20 games
-- ORDER BY ppg DESC
-- LIMIT 10;

-- Compare Hoopr vs Computed box scores (detect inflation)
-- SELECT
--     h.game_id,
--     h.athlete_id,
--     h.fga as hoopr_fga,
--     c.fga as computed_fga,
--     h.fga - c.fga as fga_difference,
--     ROUND(100.0 * (h.fga - c.fga) / NULLIF(c.fga, 0), 2) as inflation_pct
-- FROM hoopr_player_box h
-- JOIN computed_player_box c ON h.game_id = c.game_id AND h.athlete_id = c.player_id
-- WHERE h.fga != c.fga
-- ORDER BY inflation_pct DESC
-- LIMIT 100;

-- Team roster for a specific game
-- SELECT
--     athlete_id,
--     athlete_position_abbreviation as position,
--     minutes,
--     points,
--     rebounds,
--     assists
-- FROM hoopr_player_box
-- WHERE game_id = '401584893'
--   AND team_id = 1610612747  -- Lakers
--   AND active = 1
-- ORDER BY minutes DESC;

-- Player's last N games (rolling statistics)
-- SELECT
--     game_date,
--     points,
--     rebounds,
--     assists,
--     fgm,
--     fga,
--     fg_pct,
--     AVG(points) OVER (ORDER BY game_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as ppg_last_10
-- FROM hoopr_player_box
-- WHERE athlete_id = 2544  -- LeBron James
--   AND active = 1
-- ORDER BY game_date DESC
-- LIMIT 20;

-- ==============================================================================
-- End of schema
-- ==============================================================================
