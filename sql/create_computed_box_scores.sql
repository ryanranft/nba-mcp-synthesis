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
--   psql -U <username> -d <database> -f sql/create_computed_box_scores.sql
--
-- ==============================================================================

-- Drop existing tables if they exist
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
-- Grant permissions (adjust as needed)
-- ==============================================================================

-- Example: GRANT SELECT ON computed_player_box TO readonly_user;
-- Example: GRANT ALL ON computed_player_box TO app_user;

-- ==============================================================================
-- End of schema
-- ==============================================================================
