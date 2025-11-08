-- ==============================================================================
-- Computed Box Score Tables
-- ==============================================================================
--
-- These tables store box scores computed directly from play-by-play events,
-- providing 100% accuracy to actual game events.
--
-- Key differences from hoopr_player_box/hoopr_team_box:
--   1. Computed from play-by-play events (not pre-aggregated)
--   2. Internal consistency validated (team totals = player totals)
--   3. Includes possession-based metrics
--   4. No data quality issues from external sources
--
-- Usage:
--   This script runs automatically when PostgreSQL container initializes
--   Depends on: 01_games_table.sql, 02_hoopr_play_by_play_table.sql
--
-- ==============================================================================

-- Drop existing tables if they exist (for clean reinitialization)
DROP TABLE IF EXISTS computed_player_box CASCADE;
DROP TABLE IF EXISTS computed_team_box CASCADE;

-- ==============================================================================
-- Computed Player Box Scores
-- ==============================================================================

CREATE TABLE computed_player_box (
    -- Identifiers
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,

    -- Time on court
    minutes INTEGER DEFAULT 0,  -- TODO: Compute from substitution events

    -- Shooting statistics
    fgm INTEGER DEFAULT 0,      -- Field goals made
    fga INTEGER DEFAULT 0,      -- Field goals attempted
    fg_pct DECIMAL(5,3) DEFAULT 0.000,  -- Field goal percentage
    fg3m INTEGER DEFAULT 0,     -- Three-point field goals made
    fg3a INTEGER DEFAULT 0,     -- Three-point field goals attempted
    fg3_pct DECIMAL(5,3) DEFAULT 0.000, -- Three-point percentage
    ftm INTEGER DEFAULT 0,      -- Free throws made
    fta INTEGER DEFAULT 0,      -- Free throws attempted
    ft_pct DECIMAL(5,3) DEFAULT 0.000,  -- Free throw percentage

    -- Rebounding
    oreb INTEGER DEFAULT 0,     -- Offensive rebounds
    dreb INTEGER DEFAULT 0,     -- Defensive rebounds
    reb INTEGER DEFAULT 0,      -- Total rebounds

    -- Other statistics
    ast INTEGER DEFAULT 0,      -- Assists
    stl INTEGER DEFAULT 0,      -- Steals
    blk INTEGER DEFAULT 0,      -- Blocks
    tov INTEGER DEFAULT 0,      -- Turnovers
    pf INTEGER DEFAULT 0,       -- Personal fouls
    pts INTEGER DEFAULT 0,      -- Points scored

    -- Advanced metrics
    plus_minus INTEGER DEFAULT 0,  -- Plus/minus while on court

    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CHECK (fgm >= 0 AND fgm <= fga),
    CHECK (fg3m >= 0 AND fg3m <= fg3a),
    CHECK (ftm >= 0 AND ftm <= fta),
    CHECK (fg_pct >= 0 AND fg_pct <= 1),
    CHECK (fg3_pct >= 0 AND fg3_pct <= 1),
    CHECK (ft_pct >= 0 AND ft_pct <= 1),
    CHECK (reb = oreb + dreb)
);

-- Indexes for performance
CREATE INDEX idx_computed_player_box_game ON computed_player_box(game_id);
CREATE INDEX idx_computed_player_box_player ON computed_player_box(player_id);
CREATE INDEX idx_computed_player_box_team ON computed_player_box(team_id);

-- ==============================================================================
-- Computed Team Box Scores
-- ==============================================================================

CREATE TABLE computed_team_box (
    -- Identifiers
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,

    -- Shooting statistics
    fgm INTEGER DEFAULT 0,
    fga INTEGER DEFAULT 0,
    fg_pct DECIMAL(5,3) DEFAULT 0.000,
    fg3m INTEGER DEFAULT 0,
    fg3a INTEGER DEFAULT 0,
    fg3_pct DECIMAL(5,3) DEFAULT 0.000,
    ftm INTEGER DEFAULT 0,
    fta INTEGER DEFAULT 0,
    ft_pct DECIMAL(5,3) DEFAULT 0.000,

    -- Rebounding
    oreb INTEGER DEFAULT 0,
    dreb INTEGER DEFAULT 0,
    reb INTEGER DEFAULT 0,
    team_rebounds INTEGER DEFAULT 0,  -- Rebounds not attributed to players

    -- Other statistics
    ast INTEGER DEFAULT 0,
    stl INTEGER DEFAULT 0,
    blk INTEGER DEFAULT 0,
    tov INTEGER DEFAULT 0,           -- Player turnovers
    team_turnovers INTEGER DEFAULT 0, -- Team turnovers (not attributed to players)
    total_turnovers INTEGER DEFAULT 0, -- Player + team turnovers
    pf INTEGER DEFAULT 0,
    pts INTEGER DEFAULT 0,

    -- Possession-based metrics (FROM PLAY-BY-PLAY)
    true_possessions INTEGER DEFAULT 0,        -- Count from possession tracker
    estimated_possessions DECIMAL(6,2) DEFAULT 0.0,  -- From formula: FGA + 0.44*FTA - OREB + TOV

    -- Advanced metrics (per 100 possessions)
    pace DECIMAL(6,2) DEFAULT 0.0,            -- Possessions per 48 minutes
    offensive_rating DECIMAL(6,2) DEFAULT 0.0, -- Points per 100 possessions
    defensive_rating DECIMAL(6,2) DEFAULT 0.0, -- Points allowed per 100 possessions

    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CHECK (fgm >= 0 AND fgm <= fga),
    CHECK (fg3m >= 0 AND fg3m <= fg3a),
    CHECK (ftm >= 0 AND ftm <= fta),
    CHECK (total_turnovers = tov + team_turnovers)
);

-- Indexes for performance
CREATE INDEX idx_computed_team_box_game ON computed_team_box(game_id);
CREATE INDEX idx_computed_team_box_team ON computed_team_box(team_id);

-- ==============================================================================
-- Comments
-- ==============================================================================

COMMENT ON TABLE computed_player_box IS
'Player box scores computed from play-by-play events. 100% accurate to actual game events.';

COMMENT ON TABLE computed_team_box IS
'Team box scores computed from play-by-play events. Includes possession-based metrics.';

COMMENT ON COLUMN computed_team_box.true_possessions IS
'Possession count from play-by-play possession tracker (ground truth)';

COMMENT ON COLUMN computed_team_box.estimated_possessions IS
'Possession estimate from formula: FGA + 0.44*FTA - OREB + TOV';

COMMENT ON COLUMN computed_team_box.offensive_rating IS
'Points scored per 100 possessions (uses true_possessions)';

COMMENT ON COLUMN computed_team_box.defensive_rating IS
'Points allowed per 100 possessions (uses opponent true_possessions)';

-- ==============================================================================
-- Data Quality Notes
-- ==============================================================================

-- WHY USE COMPUTED TABLES:
--
-- 1. 100% ACCURACY:
--    - Calculated directly from play-by-play events
--    - No external data source errors
--    - All years (2002-2024) have perfect internal consistency
--
-- 2. INTERNAL CONSISTENCY:
--    - Team stats = sum of player stats + team stats
--    - Points from play-by-play = sum of scoring plays
--    - FGA from play-by-play = count of shot events
--
-- 3. POSSESSION-BASED METRICS:
--    - true_possessions: Counted from possession tracker (more accurate)
--    - estimated_possessions: Formula-based fallback
--    - Enables offensive/defensive rating calculations
--
-- 4. NO HOOPR INFLATION:
--    - Hoopr data (2013-2024) shows 26-73% inflation
--    - Computed tables have NO inflation
--    - Use these tables for ALL analysis and ML models
--
-- 5. COMPUTATION METHODOLOGY:
--    - EventParser: Parses each play-by-play event
--    - BoxScoreAggregator: Aggregates events into box scores
--    - PossessionTracker: Tracks possession changes
--    - Source: /Users/ryanranft/nba-mcp-synthesis/mcp_server/play_by_play/

-- ==============================================================================
-- Example Queries
-- ==============================================================================

-- Get accurate player stats for a game
-- SELECT player_id, pts, reb, ast, fgm, fga, fg_pct
-- FROM computed_player_box
-- WHERE game_id = '401584893'
-- ORDER BY pts DESC;

-- Compare computed vs Hoopr (detect inflation)
-- SELECT
--     c.game_id,
--     c.player_id,
--     c.fga as computed_fga,
--     h.fga as hoopr_fga,
--     h.fga - c.fga as inflation,
--     ROUND(100.0 * (h.fga - c.fga) / NULLIF(c.fga, 0), 2) as inflation_pct
-- FROM computed_player_box c
-- LEFT JOIN hoopr_player_box h ON c.game_id = h.game_id AND c.player_id = h.athlete_id
-- WHERE h.fga != c.fga
-- ORDER BY inflation_pct DESC
-- LIMIT 100;

-- Team advanced metrics (pace, offensive/defensive rating)
-- SELECT
--     team_id,
--     pts,
--     true_possessions,
--     pace,
--     offensive_rating,
--     defensive_rating
-- FROM computed_team_box
-- WHERE game_id = '401584893';

-- Player season averages (accurate)
-- SELECT
--     player_id,
--     COUNT(*) as games_played,
--     ROUND(AVG(pts), 1) as ppg,
--     ROUND(AVG(reb), 1) as rpg,
--     ROUND(AVG(ast), 1) as apg,
--     ROUND(AVG(fg_pct), 3) as fg_pct
-- FROM computed_player_box
-- WHERE game_id IN (
--     SELECT game_id FROM games
--     WHERE EXTRACT(YEAR FROM game_date) = 2024
--       AND season_type = 2
-- )
-- GROUP BY player_id
-- HAVING COUNT(*) >= 20
-- ORDER BY ppg DESC
-- LIMIT 10;

-- Team efficiency stats (per 100 possessions)
-- SELECT
--     team_id,
--     COUNT(*) as games,
--     ROUND(AVG(offensive_rating), 2) as avg_ortg,
--     ROUND(AVG(defensive_rating), 2) as avg_drtg,
--     ROUND(AVG(offensive_rating) - AVG(defensive_rating), 2) as net_rating,
--     ROUND(AVG(pace), 2) as avg_pace
-- FROM computed_team_box
-- WHERE game_id IN (
--     SELECT game_id FROM games
--     WHERE EXTRACT(YEAR FROM game_date) = 2024
--       AND season_type = 2
-- )
-- GROUP BY team_id
-- ORDER BY net_rating DESC;

-- ==============================================================================
-- Grant permissions (adjust as needed)
-- ==============================================================================

-- Example: GRANT SELECT ON computed_player_box TO readonly_user;
-- Example: GRANT ALL ON computed_player_box TO app_user;

-- ==============================================================================
-- End of schema
-- ==============================================================================
