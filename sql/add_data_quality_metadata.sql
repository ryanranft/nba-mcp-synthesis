-- ==============================================================================
-- Add Data Quality Metadata to Games Table
-- ==============================================================================
--
-- Adds year-level data quality metadata to enable ML models to:
--   1. Filter training data by quality tier
--   2. Weight samples by quality score
--   3. Identify known data issues for specific years
--
-- Usage:
--   psql -U <username> -d <database> -f sql/add_data_quality_metadata.sql
--
-- Based on year-over-year analysis results (2002-2024)
-- Analysis date: 2025-11-06
--
-- ==============================================================================

-- Add quality metadata columns to games table
ALTER TABLE games
ADD COLUMN IF NOT EXISTS data_quality_score INTEGER,
ADD COLUMN IF NOT EXISTS data_quality_tier VARCHAR(1),
ADD COLUMN IF NOT EXISTS known_data_issues TEXT[],
ADD COLUMN IF NOT EXISTS hoopr_match_rate DECIMAL(5,2);

-- Add comments
COMMENT ON COLUMN games.data_quality_score IS
'Composite quality score (0-100) for play-by-play data. Based on internal consistency (40pts), Hoopr match rate (30pts), error patterns (20pts), game-to-game consistency (10pts).';

COMMENT ON COLUMN games.data_quality_tier IS
'Quality tier: A (95-100), B (85-95), C (70-85), D (<70). All years 2002-2024 are A/B/C tier.';

COMMENT ON COLUMN games.known_data_issues IS
'Array of known data quality issues for this year. Common values: "hoopr_fga_inflation", "hoopr_pts_inflation", "hoopr_fgm_inflation".';

COMMENT ON COLUMN games.hoopr_match_rate IS
'Average match rate between play-by-play computed stats and Hoopr box scores for this year (%).';

-- ==============================================================================
-- Populate Quality Metadata by Year
-- ==============================================================================

-- Tier A: 2002, 2004 (Excellent - 95-100 score)
UPDATE games
SET
    data_quality_score = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2002 THEN 96
        WHEN 2004 THEN 97
    END,
    data_quality_tier = 'A',
    hoopr_match_rate = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2002 THEN 98.55
        WHEN 2004 THEN 99.32
    END,
    known_data_issues = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2002 THEN ARRAY['hoopr_fga_inflation']::TEXT[]
        WHEN 2004 THEN ARRAY['hoopr_fga_inflation']::TEXT[]
    END
WHERE EXTRACT(YEAR FROM game_date)::INTEGER IN (2002, 2004);

-- Tier B: 2003, 2005-2012 (Good - 85-95 score)
UPDATE games
SET
    data_quality_score = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2003 THEN 91
        WHEN 2005 THEN 89
        WHEN 2006 THEN 90
        WHEN 2007 THEN 89
        WHEN 2008 THEN 88
        WHEN 2009 THEN 85
        WHEN 2010 THEN 90
        WHEN 2011 THEN 89
        WHEN 2012 THEN 87
    END,
    data_quality_tier = 'B',
    hoopr_match_rate = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2003 THEN 96.51
        WHEN 2005 THEN 87.40
        WHEN 2006 THEN 91.79
        WHEN 2007 THEN 89.94
        WHEN 2008 THEN 91.03
        WHEN 2009 THEN 85.38
        WHEN 2010 THEN 92.55
        WHEN 2011 THEN 90.75
        WHEN 2012 THEN 87.68
    END,
    known_data_issues = ARRAY['hoopr_fga_inflation', 'hoopr_fgm_inflation', 'hoopr_pts_inflation']::TEXT[]
WHERE EXTRACT(YEAR FROM game_date)::INTEGER IN (2003, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012);

-- Tier C: 2013-2024 (Fair - 70-85 score, significant Hoopr discrepancies)
UPDATE games
SET
    data_quality_score = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2013 THEN 81
        WHEN 2014 THEN 76
        WHEN 2015 THEN 72
        WHEN 2016 THEN 72
        WHEN 2017 THEN 75
        WHEN 2018 THEN 74
        WHEN 2019 THEN 73
        WHEN 2020 THEN 73
        WHEN 2021 THEN 71
        WHEN 2022 THEN 70
        WHEN 2023 THEN 71
        WHEN 2024 THEN 71
    END,
    data_quality_tier = 'C',
    hoopr_match_rate = CASE EXTRACT(YEAR FROM game_date)::INTEGER
        WHEN 2013 THEN 72.72
        WHEN 2014 THEN 64.60
        WHEN 2015 THEN 51.02
        WHEN 2016 THEN 36.83
        WHEN 2017 THEN 49.71
        WHEN 2018 THEN 38.42
        WHEN 2019 THEN 36.81
        WHEN 2020 THEN 34.67
        WHEN 2021 THEN 31.37
        WHEN 2022 THEN 26.90
        WHEN 2023 THEN 28.52
        WHEN 2024 THEN 35.23
    END,
    known_data_issues = ARRAY['hoopr_fga_inflation', 'hoopr_fgm_inflation', 'hoopr_pts_inflation']::TEXT[]
WHERE EXTRACT(YEAR FROM game_date)::INTEGER BETWEEN 2013 AND 2024;

-- ==============================================================================
-- Create Index for ML Model Filtering
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_games_quality_tier ON games(data_quality_tier);
CREATE INDEX IF NOT EXISTS idx_games_quality_score ON games(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_games_year_quality ON games(EXTRACT(YEAR FROM game_date)::INTEGER, data_quality_tier);

-- ==============================================================================
-- Verification Queries
-- ==============================================================================

-- Count games by quality tier
SELECT
    data_quality_tier,
    COUNT(*) as num_games,
    MIN(data_quality_score) as min_score,
    MAX(data_quality_score) as max_score,
    AVG(hoopr_match_rate)::DECIMAL(5,2) as avg_match_rate
FROM games
WHERE data_quality_tier IS NOT NULL
GROUP BY data_quality_tier
ORDER BY data_quality_tier;

-- Count games by year and tier
SELECT
    EXTRACT(YEAR FROM game_date)::INTEGER as year,
    data_quality_tier,
    data_quality_score,
    hoopr_match_rate,
    ARRAY_LENGTH(known_data_issues, 1) as num_issues,
    COUNT(*) as num_games
FROM games
WHERE data_quality_tier IS NOT NULL
GROUP BY year, data_quality_tier, data_quality_score, hoopr_match_rate, known_data_issues
ORDER BY year;

-- ==============================================================================
-- ML Model Usage Examples
-- ==============================================================================

-- Example 1: Filter training data to high-quality years only (Tier A/B)
-- SELECT * FROM games
-- WHERE data_quality_tier IN ('A', 'B')
-- AND game_date >= '2002-01-01';

-- Example 2: Weight samples by quality score
-- SELECT
--     game_id,
--     game_date,
--     data_quality_score / 100.0 as sample_weight
-- FROM games
-- WHERE data_quality_score IS NOT NULL;

-- Example 3: Identify games with specific data issues
-- SELECT game_id, game_date, known_data_issues
-- FROM games
-- WHERE 'hoopr_fga_inflation' = ANY(known_data_issues);

-- Example 4: Get quality distribution for a specific season
-- SELECT
--     data_quality_tier,
--     COUNT(*) as games,
--     AVG(data_quality_score)::DECIMAL(5,2) as avg_score
-- FROM games
-- WHERE EXTRACT(YEAR FROM game_date) = 2024
-- GROUP BY data_quality_tier;

-- ==============================================================================
-- Important Notes
-- ==============================================================================

-- 1. ALL YEARS (2002-2024) have 100% internal consistency
--    - Our play-by-play parser is fully accurate
--    - Computed box scores always match event counts
--
-- 2. Quality scores reflect HOOPR DATA QUALITY, not play-by-play quality
--    - Lower scores = larger discrepancies with Hoopr box scores
--    - Recent years (2013-2024) show significant Hoopr inflation
--
-- 3. For ML models:
--    - ALWAYS use computed box scores from play-by-play (100% accurate)
--    - Use Hoopr box scores only for comparison/validation
--    - Consider filtering Tier C years if Hoopr stats are needed
--
-- 4. Known data issues are EXTERNAL (Hoopr), not in our data:
--    - "hoopr_fga_inflation": Hoopr reports 3-14% more FGA than play-by-play
--    - "hoopr_fgm_inflation": Hoopr reports more FGM than play-by-play
--    - "hoopr_pts_inflation": Hoopr reports more PTS than play-by-play
--
-- ==============================================================================
-- End of migration
-- ==============================================================================
