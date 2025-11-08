-- ==============================================================================
-- HoopR Team Box Scores Table - NBA Team Statistics
-- ==============================================================================
--
-- Stores team box score statistics aggregated by ESPN/hoopR
--
-- Data sources:
--   - ESPN/hoopR API: Pre-aggregated team statistics
--
-- IMPORTANT: This table has known data quality issues (2013-2024)
-- - Hoopr reports 26-73% more stats than play-by-play computed values
-- - Always prefer computed_team_box for accurate statistics
-- - Use this table only for comparison/validation purposes
--
-- Usage:
--   This script runs automatically when PostgreSQL container initializes
--   Depends on: 01_games_table.sql (for game_id foreign key)
--
-- ==============================================================================

-- Drop existing table if it exists (for clean reinitialization)
DROP TABLE IF EXISTS hoopr_team_box CASCADE;

-- ==============================================================================
-- Create HoopR Team Box Scores Table
-- ==============================================================================

CREATE TABLE hoopr_team_box (
    -- Identifiers (composite primary key: game + team)
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,

    -- Opponent information
    opponent_team_id INTEGER,

    -- Game metadata
    game_date DATE,
    season INTEGER,
    season_type INTEGER,  -- 2 = regular season, 3 = playoffs

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
    reb INTEGER DEFAULT 0,  -- Total rebounds (oreb + dreb)

    -- Other statistics
    ast INTEGER DEFAULT 0,  -- Assists
    stl INTEGER DEFAULT 0,  -- Steals
    blk INTEGER DEFAULT 0,  -- Blocks
    tov INTEGER DEFAULT 0,  -- Turnovers
    pf INTEGER DEFAULT 0,  -- Personal fouls
    pts INTEGER DEFAULT 0,  -- Points scored

    -- Additional team metrics (may be NULL if not provided by Hoopr)
    fast_break_points INTEGER,
    points_in_paint INTEGER,
    second_chance_points INTEGER,
    turnovers_points INTEGER,  -- Points off turnovers
    biggest_lead INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CHECK (fgm >= 0 AND fgm <= fga),
    CHECK (fg3m >= 0 AND fg3m <= fg3a),
    CHECK (ftm >= 0 AND ftm <= fta),
    CHECK (fg_pct IS NULL OR (fg_pct >= 0 AND fg_pct <= 1)),
    CHECK (fg3_pct IS NULL OR (fg3_pct >= 0 AND fg3_pct <= 1)),
    CHECK (ft_pct IS NULL OR (ft_pct >= 0 AND ft_pct <= 1))
);

-- ==============================================================================
-- Indexes for Performance
-- ==============================================================================

-- Primary query patterns: game lookups, team history, head-to-head

-- Game-level queries
CREATE INDEX idx_hoopr_team_box_game ON hoopr_team_box(game_id);

-- Team analytics (most common)
CREATE INDEX idx_hoopr_team_box_team ON hoopr_team_box(team_id);

-- Date range queries
CREATE INDEX idx_hoopr_team_box_date ON hoopr_team_box(game_date);

-- Season queries
CREATE INDEX idx_hoopr_team_box_season ON hoopr_team_box(season, season_type);

-- Composite index for team history
CREATE INDEX idx_hoopr_team_box_team_date ON hoopr_team_box(team_id, game_date);

-- Head-to-head queries
CREATE INDEX idx_hoopr_team_box_matchup ON hoopr_team_box(team_id, opponent_team_id);

-- ==============================================================================
-- Comments and Documentation
-- ==============================================================================

COMMENT ON TABLE hoopr_team_box IS
'Team box score statistics from ESPN/hoopR API. WARNING: Contains known inflation issues (2013-2024). Always prefer computed_team_box for accurate statistics.';

COMMENT ON COLUMN hoopr_team_box.team_id IS
'Unique team identifier from ESPN API (e.g., 1610612747 for Los Angeles Lakers)';

COMMENT ON COLUMN hoopr_team_box.season_type IS
'Season type: 2 = regular season, 3 = playoffs, 4 = all-star';

COMMENT ON COLUMN hoopr_team_box.reb IS
'Total rebounds (oreb + dreb). Should equal sum of offensive and defensive rebounds.';

COMMENT ON COLUMN hoopr_team_box.fast_break_points IS
'Points scored in fast break situations. May be NULL if not provided by Hoopr.';

COMMENT ON COLUMN hoopr_team_box.points_in_paint IS
'Points scored in the paint (restricted area + non-RA paint). May be NULL if not provided by Hoopr.';

COMMENT ON COLUMN hoopr_team_box.second_chance_points IS
'Points scored after offensive rebounds. May be NULL if not provided by Hoopr.';

COMMENT ON COLUMN hoopr_team_box.turnovers_points IS
'Points scored off opponent turnovers. May be NULL if not provided by Hoopr.';

-- ==============================================================================
-- Data Quality Notes
-- ==============================================================================

-- CRITICAL DATA QUALITY ISSUES:
--
-- 1. HOOPR INFLATION (2013-2024):
--    - Same inflation issues as hoopr_player_box
--    - Years 2013-2024 show 26-73% mismatch with play-by-play
--    - Team totals should equal sum of player stats, but often don't
--    - FGA/FGM/PTS inflation affects team-level analysis
--
-- 2. RECOMMENDED APPROACH:
--    - ALWAYS use computed_team_box for accurate team statistics
--    - Use this table ONLY for:
--      - Comparison with official box scores
--      - Validation of data quality
--      - Historical reference (pre-computed tables)
--
-- 3. INTERNAL CONSISTENCY ISSUES:
--    - Team rebounds may not match sum of player rebounds + team rebounds
--    - Team turnovers may not match sum of player turnovers + team turnovers
--    - Points may not match sum of player points
--
-- 4. WHY USE COMPUTED TABLES INSTEAD:
--    - computed_team_box: Calculated directly from play-by-play events
--    - 100% accurate to actual game events across all years
--    - Internal consistency validated (team stats = sum of player stats + team stats)
--    - Includes possession-based metrics (true_possessions, pace, ratings)
--
-- 5. MIGRATION PATH:
--    - New applications: Use computed_team_box exclusively
--    - Existing applications: Migrate queries to computed_team_box
--    - This table: Keep for historical comparison only

-- ==============================================================================
-- Example Queries
-- ==============================================================================

-- Get team stats for a specific game
-- SELECT team_id, pts, reb, ast, fgm, fga, fg_pct, tov
-- FROM hoopr_team_box
-- WHERE game_id = '401584893'
-- ORDER BY pts DESC;

-- Team season averages (regular season only)
-- SELECT
--     team_id,
--     season,
--     COUNT(*) as games_played,
--     ROUND(AVG(pts), 1) as ppg,
--     ROUND(AVG(reb), 1) as rpg,
--     ROUND(AVG(ast), 1) as apg,
--     ROUND(AVG(tov), 1) as topg,
--     ROUND(AVG(fg_pct), 3) as fg_pct,
--     ROUND(AVG(fg3_pct), 3) as fg3_pct
-- FROM hoopr_team_box
-- WHERE season = 2024
--   AND season_type = 2
-- GROUP BY team_id, season
-- ORDER BY ppg DESC;

-- Compare Hoopr vs Computed team box scores
-- SELECT
--     h.game_id,
--     h.team_id,
--     h.fga as hoopr_fga,
--     c.fga as computed_fga,
--     h.fga - c.fga as fga_difference,
--     ROUND(100.0 * (h.fga - c.fga) / NULLIF(c.fga, 0), 2) as inflation_pct
-- FROM hoopr_team_box h
-- JOIN computed_team_box c ON h.game_id = c.game_id AND h.team_id = c.team_id
-- WHERE h.fga != c.fga
-- ORDER BY inflation_pct DESC
-- LIMIT 100;

-- Head-to-head record between two teams
-- SELECT
--     team_id,
--     opponent_team_id,
--     COUNT(*) as games,
--     SUM(CASE WHEN pts > (SELECT pts FROM hoopr_team_box h2
--                          WHERE h2.game_id = h1.game_id
--                            AND h2.team_id = h1.opponent_team_id)
--         THEN 1 ELSE 0 END) as wins,
--     SUM(CASE WHEN pts < (SELECT pts FROM hoopr_team_box h2
--                          WHERE h2.game_id = h1.game_id
--                            AND h2.team_id = h1.opponent_team_id)
--         THEN 1 ELSE 0 END) as losses
-- FROM hoopr_team_box h1
-- WHERE team_id = 1610612747  -- Lakers
--   AND opponent_team_id = 1610612738  -- Celtics
-- GROUP BY team_id, opponent_team_id;

-- Team's last N games (rolling statistics)
-- SELECT
--     game_date,
--     pts,
--     reb,
--     ast,
--     tov,
--     fg_pct,
--     AVG(pts) OVER (ORDER BY game_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as ppg_last_10,
--     AVG(fg_pct) OVER (ORDER BY game_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as fg_pct_last_10
-- FROM hoopr_team_box
-- WHERE team_id = 1610612747  -- Lakers
-- ORDER BY game_date DESC
-- LIMIT 20;

-- Top teams by offensive efficiency (points per 100 FGA)
-- SELECT
--     team_id,
--     season,
--     COUNT(*) as games,
--     SUM(pts) as total_pts,
--     SUM(fga) as total_fga,
--     ROUND(100.0 * SUM(pts) / NULLIF(SUM(fga), 0), 2) as pts_per_100_fga
-- FROM hoopr_team_box
-- WHERE season = 2024
--   AND season_type = 2
-- GROUP BY team_id, season
-- HAVING COUNT(*) >= 20  -- Min 20 games
-- ORDER BY pts_per_100_fga DESC
-- LIMIT 10;

-- ==============================================================================
-- End of schema
-- ==============================================================================
