-- ==============================================================================
-- Games Table - NBA Game Schedule and Metadata
-- ==============================================================================
--
-- Stores game schedule, scores, and data quality metadata for NBA games
--
-- Data sources:
--   - ESPN/hoopR API: Game schedule and scores
--   - Internal analysis: Data quality metadata
--
-- Usage:
--   This script runs automatically when PostgreSQL container initializes
--   Tables are created in order: 01_games -> 02_play_by_play -> ...
--
-- ==============================================================================

-- Drop existing table if it exists (for clean reinitialization)
DROP TABLE IF EXISTS games CASCADE;

-- ==============================================================================
-- Create Games Table
-- ==============================================================================

CREATE TABLE games (
    -- Identifiers
    game_id TEXT PRIMARY KEY,

    -- Date and season information
    game_date DATE NOT NULL,
    season INTEGER,
    season_type INTEGER,  -- 2 = regular season, 3 = playoffs

    -- Team information
    home_team TEXT,
    away_team TEXT,
    home_team_id INTEGER,
    away_team_id INTEGER,

    -- Final scores
    home_score INTEGER,
    away_score INTEGER,

    -- Data quality metadata (for ML model filtering and weighting)
    data_quality_score INTEGER,  -- 0-100, composite quality score
    data_quality_tier VARCHAR(1),  -- A (95-100), B (85-95), C (70-85), D (<70)
    known_data_issues TEXT[],  -- Array of known issues (e.g., 'hoopr_fga_inflation')
    hoopr_match_rate DECIMAL(5,2),  -- % match between play-by-play and Hoopr stats

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- Indexes for Performance
-- ==============================================================================

-- Primary query patterns: date range filtering, team lookups, quality filtering
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_games_season ON games(season, season_type);
CREATE INDEX idx_games_home_team_id ON games(home_team_id);
CREATE INDEX idx_games_away_team_id ON games(away_team_id);
CREATE INDEX idx_games_quality_tier ON games(data_quality_tier);
CREATE INDEX idx_games_quality_score ON games(data_quality_score);
CREATE INDEX idx_games_year_quality ON games(CAST(EXTRACT(YEAR FROM game_date) AS INTEGER), data_quality_tier);

-- ==============================================================================
-- Comments and Documentation
-- ==============================================================================

COMMENT ON TABLE games IS
'NBA game schedule, scores, and data quality metadata. Primary source: ESPN/hoopR API.';

COMMENT ON COLUMN games.game_id IS
'Unique game identifier from ESPN API (e.g., "401584893")';

COMMENT ON COLUMN games.season_type IS
'Season type: 2 = regular season, 3 = playoffs, 4 = all-star';

COMMENT ON COLUMN games.data_quality_score IS
'Composite quality score (0-100) for play-by-play data. Based on internal consistency (40pts), Hoopr match rate (30pts), error patterns (20pts), game-to-game consistency (10pts). All years 2002-2024 have scores 70-97.';

COMMENT ON COLUMN games.data_quality_tier IS
'Quality tier for filtering training data: A (95-100), B (85-95), C (70-85), D (<70). All years 2002-2024 are A/B/C tier (usable for production).';

COMMENT ON COLUMN games.known_data_issues IS
'Array of known data quality issues. Common values: "hoopr_fga_inflation", "hoopr_pts_inflation", "hoopr_fgm_inflation". These are EXTERNAL issues (Hoopr data), NOT play-by-play issues.';

COMMENT ON COLUMN games.hoopr_match_rate IS
'Average match rate between play-by-play computed stats and Hoopr box scores (%). Ranges from 26.90% (2022) to 99.32% (2004). Lower rates indicate Hoopr inflation, not play-by-play errors.';

-- ==============================================================================
-- Data Quality Notes
-- ==============================================================================

-- IMPORTANT NOTES:
--
-- 1. ALL YEARS (2002-2024) have 100% internal consistency
--    - Our play-by-play parser is fully accurate
--    - Computed box scores always match event counts
--
-- 2. Quality scores reflect HOOPR DATA QUALITY, not play-by-play quality
--    - Lower scores = larger discrepancies with Hoopr box scores
--    - Recent years (2013-2024) show significant Hoopr inflation (26-73% mismatch)
--
-- 3. For ML models:
--    - ALWAYS use computed box scores from play-by-play (100% accurate)
--    - Use Hoopr box scores only for comparison/validation
--    - Consider filtering Tier C years if Hoopr stats are needed
--
-- 4. Data quality tier distribution (2002-2024):
--    - Tier A (Excellent): 2002, 2004 (2 years, ~3,500 games)
--    - Tier B (Good): 2003, 2005-2012 (9 years, ~11,000 games)
--    - Tier C (Fair): 2013-2024 (12 years, ~14,000 games)
--
-- 5. Known data issues are EXTERNAL (Hoopr), not in our data:
--    - "hoopr_fga_inflation": Hoopr reports 3-14% more FGA than play-by-play
--    - "hoopr_fgm_inflation": Hoopr reports more FGM than play-by-play
--    - "hoopr_pts_inflation": Hoopr reports more PTS than play-by-play

-- ==============================================================================
-- Example Queries
-- ==============================================================================

-- Get recent games for a specific team
-- SELECT game_id, game_date, home_team, away_team, home_score, away_score
-- FROM games
-- WHERE (home_team_id = 1610612747 OR away_team_id = 1610612747)
--   AND game_date >= CURRENT_DATE - INTERVAL '30 days'
-- ORDER BY game_date DESC;

-- Filter training data to high-quality years only (Tier A/B)
-- SELECT * FROM games
-- WHERE data_quality_tier IN ('A', 'B')
--   AND game_date >= '2002-01-01';

-- Get quality distribution for a specific season
-- SELECT
--     data_quality_tier,
--     COUNT(*) as games,
--     AVG(data_quality_score)::DECIMAL(5,2) as avg_score,
--     AVG(hoopr_match_rate)::DECIMAL(5,2) as avg_match_rate
-- FROM games
-- WHERE EXTRACT(YEAR FROM game_date) = 2024
-- GROUP BY data_quality_tier;

-- Find games with specific data issues
-- SELECT game_id, game_date, home_team, away_team, known_data_issues
-- FROM games
-- WHERE 'hoopr_fga_inflation' = ANY(known_data_issues)
-- ORDER BY game_date DESC
-- LIMIT 10;

-- ==============================================================================
-- End of schema
-- ==============================================================================
