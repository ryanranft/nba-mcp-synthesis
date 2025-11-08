# NBA MCP Synthesis - Database Schema Documentation

**Last Updated:** 2025-01-07
**Database:** PostgreSQL 16
**Schema Version:** 1.0

---

## Overview

This document provides comprehensive documentation for all tables in the NBA MCP Synthesis database. The schema is designed to support:

- **Game data storage**: Schedule, scores, and metadata
- **Event-level tracking**: Play-by-play data with shot classification
- **Box score analytics**: Both external (Hoopr) and computed (internal)
- **Betting operations**: Arbitrage opportunities and ML-based recommendations

---

## Table Relationships

```
games (1) ──────< hoopr_play_by_play (N)
  │
  ├──────< hoopr_player_box (N)
  │
  ├──────< hoopr_team_box (N)
  │
  ├──────< computed_player_box (N)
  │
  └──────< computed_team_box (N)

betting_recommendations (N) ──> games (1) [soft reference]
arbitrage_opportunities (N) ──> games (1) [soft reference]
```

---

## Core Tables

### 1. `games` - Game Schedule and Metadata

**Purpose**: Stores NBA game schedule, final scores, and data quality metadata.

**Primary Key**: `game_id`

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `game_id` | TEXT | Unique ESPN game identifier |
| `game_date` | DATE | Game date (YYYY-MM-DD) |
| `season` | INTEGER | Season year (e.g., 2024) |
| `season_type` | INTEGER | 2=regular, 3=playoffs, 4=all-star |
| `home_team` | TEXT | Home team name |
| `away_team` | TEXT | Away team name |
| `home_team_id` | INTEGER | ESPN home team ID |
| `away_team_id` | INTEGER | ESPN away team ID |
| `home_score` | INTEGER | Final home team score |
| `away_score` | INTEGER | Final away team score |
| `data_quality_score` | INTEGER | Composite quality score (0-100) |
| `data_quality_tier` | VARCHAR(1) | Quality tier (A/B/C/D) |
| `known_data_issues` | TEXT[] | Array of known issues |
| `hoopr_match_rate` | DECIMAL(5,2) | % match with Hoopr data |

**Indexes**:
- `idx_games_date` on `game_date`
- `idx_games_season` on `(season, season_type)`
- `idx_games_home_team_id` on `home_team_id`
- `idx_games_away_team_id` on `away_team_id`
- `idx_games_quality_tier` on `data_quality_tier`

**Data Quality Notes**:
- **All years (2002-2024)** have 100% internal consistency
- Quality scores reflect **Hoopr data quality**, not play-by-play quality
- Tier A: 2002, 2004 (95-100 score)
- Tier B: 2003, 2005-2012 (85-95 score)
- Tier C: 2013-2024 (70-85 score, significant Hoopr inflation)

**Example Query**:
```sql
-- Get recent Lakers games
SELECT game_date, home_team, away_team, home_score, away_score
FROM games
WHERE (home_team_id = 1610612747 OR away_team_id = 1610612747)
  AND game_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY game_date DESC;
```

---

### 2. `hoopr_play_by_play` - Event-Level Play Data

**Purpose**: Stores every play-by-play event from NBA games, including shot locations and classifications.

**Primary Key**: `(game_id, sequence_number)`

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `game_id` | TEXT | Foreign key to games |
| `sequence_number` | INTEGER | Event order within game |
| `type_id` | INTEGER | Numeric event type (e.g., 92=Jump Shot) |
| `type_text` | TEXT | Event description |
| `text` | TEXT | Full play description |
| `period` | INTEGER | Quarter/OT (1-4+) |
| `clock_display_value` | TEXT | Game clock (e.g., "7:58") |
| `team_id` | INTEGER | Offensive team ID |
| `athlete_id_1` | INTEGER | Primary player (shooter, rebounder) |
| `athlete_id_2` | INTEGER | Secondary player (assister, blocker) |
| `athlete_id_3` | INTEGER | Tertiary player (rare) |
| `scoring_play` | INTEGER | 0/1: Points scored? |
| `shooting_play` | INTEGER | 0/1: Shot attempt? |
| `score_value` | INTEGER | Points (0/1/2/3) |
| `coordinate_x` | DOUBLE | X coordinate (feet) |
| `coordinate_y` | DOUBLE | Y coordinate (feet) |
| `shot_zone` | TEXT | NBA zone classification |
| `shot_distance` | DOUBLE | Distance from basket (feet) |
| `shot_angle` | DOUBLE | Angle (0-360 degrees) |

**Shot Zone Values**:
- `restricted_area`: <= 4 feet from basket
- `paint_non_ra`: 4-8 feet
- `mid_range_left`, `mid_range_center`, `mid_range_right`: 8-23.75 feet
- `three_left_corner`, `three_right_corner`: Corner 3s
- `three_above_break_left`, `three_above_break_center`, `three_above_break_right`: Above-the-break 3s
- `backcourt`: > 47 feet

**Indexes**:
- `idx_pbp_game` on `game_id`
- `idx_pbp_athlete_1` on `athlete_id_1` (partial: WHERE NOT NULL)
- `idx_pbp_shot_zone` on `shot_zone` (partial: WHERE shooting_play=1)
- `idx_pbp_game_zone` on `(game_id, shot_zone)` (partial)
- `idx_pbp_player_zone` on `(athlete_id_1, shot_zone)` (partial)

**Size**: ~6.16M shots across 28,770 games (2002-2024)

**Example Query**:
```sql
-- Player shot chart by zone
SELECT shot_zone, COUNT(*) as attempts,
       SUM(CASE WHEN scoring_play=1 THEN 1 ELSE 0 END) as makes,
       ROUND(100.0 * SUM(CASE WHEN scoring_play=1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct
FROM hoopr_play_by_play
WHERE athlete_id_1 = 2544  -- LeBron James
  AND shooting_play = 1
GROUP BY shot_zone
ORDER BY attempts DESC;
```

---

### 3. `hoopr_player_box` - External Player Box Scores

**Purpose**: Player box scores aggregated by ESPN/hoopR. **WARNING**: Contains inflation issues (2013-2024).

**Primary Key**: `(game_id, athlete_id)`

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `game_id` | TEXT | Foreign key to games |
| `athlete_id` | INTEGER | ESPN player ID |
| `team_id` | INTEGER | Team ID |
| `game_date` | DATE | Game date |
| `minutes` | INTEGER | Minutes played |
| `fgm`, `fga` | INTEGER | Field goals made/attempted |
| `fg3m`, `fg3a` | INTEGER | 3-point FG made/attempted |
| `ftm`, `fta` | INTEGER | Free throws made/attempted |
| `oreb`, `dreb`, `rebounds` | INTEGER | Offensive/defensive/total rebounds |
| `assists`, `steals`, `blocks` | INTEGER | Standard stats |
| `turnovers`, `fouls`, `points` | INTEGER | Standard stats |
| `athlete_position_abbreviation` | VARCHAR(5) | Position (PG/SG/SF/PF/C) |

**Data Quality Issues**:
- Years 2013-2024: 26-73% mismatch with play-by-play
- FGA inflation: 3-14% more than actual attempts
- **Recommendation**: Use `computed_player_box` instead

**Example Query**:
```sql
-- Season averages (with caveats about data quality)
SELECT athlete_id, season,
       COUNT(*) as games,
       ROUND(AVG(points), 1) as ppg,
       ROUND(AVG(rebounds), 1) as rpg,
       ROUND(AVG(assists), 1) as apg
FROM hoopr_player_box
WHERE season = 2024 AND season_type = 2
GROUP BY athlete_id, season
HAVING COUNT(*) >= 20
ORDER BY ppg DESC
LIMIT 10;
```

---

### 4. `hoopr_team_box` - External Team Box Scores

**Purpose**: Team box scores aggregated by ESPN/hoopR. **WARNING**: Contains inflation issues (2013-2024).

**Primary Key**: `(game_id, team_id)`

**Key Columns**: Similar to `hoopr_player_box` but at team level.

**Additional Columns**:
- `fast_break_points`: Fast break scoring
- `points_in_paint`: Paint scoring
- `second_chance_points`: Points after offensive rebounds
- `turnovers_points`: Points off turnovers

**Data Quality Issues**: Same as `hoopr_player_box`.

**Recommendation**: Use `computed_team_box` instead.

---

## Computed Tables (100% Accurate)

### 5. `computed_player_box` - Accurate Player Box Scores

**Purpose**: Player box scores computed directly from play-by-play events. **100% accurate**.

**Primary Key**: `(game_id, player_id)`

**Key Columns**: Same shooting stats as `hoopr_player_box`, plus:
- `plus_minus`: Plus/minus rating
- `computed_at`: Timestamp of computation

**Advantages**:
1. ✅ 100% accurate to actual game events
2. ✅ No external data quality issues
3. ✅ Internal consistency validated
4. ✅ Works across all years (2002-2024)

**Computation Method**:
- Source: `mcp_server/play_by_play/box_score_aggregator.py`
- Parser: `mcp_server/play_by_play/event_parser.py`
- Counts every relevant event from play-by-play data

**Example Query**:
```sql
-- Accurate player stats
SELECT player_id, pts, reb, ast, fgm, fga, fg_pct
FROM computed_player_box
WHERE game_id = '401584893'
ORDER BY pts DESC;
```

---

### 6. `computed_team_box` - Accurate Team Box Scores

**Purpose**: Team box scores computed from play-by-play events. **100% accurate**.

**Primary Key**: `(game_id, team_id)`

**Key Columns**: Team shooting stats, plus:
- `team_rebounds`: Team rebounds (not attributed to players)
- `team_turnovers`: Team turnovers
- `true_possessions`: Possession count from tracker (**ground truth**)
- `estimated_possessions`: Formula-based estimate
- `pace`: Possessions per 48 minutes
- `offensive_rating`: Points per 100 possessions
- `defensive_rating`: Points allowed per 100 possessions

**Possession-Based Metrics**:
```
offensive_rating = (pts / true_possessions) * 100
defensive_rating = (opponent_pts / opponent_true_possessions) * 100
pace = (true_possessions / minutes) * 48
```

**Example Query**:
```sql
-- Team efficiency stats
SELECT team_id, pts, true_possessions,
       offensive_rating, defensive_rating,
       offensive_rating - defensive_rating as net_rating
FROM computed_team_box
WHERE game_id = '401584893';
```

---

## Betting Tables

### 7. `arbitrage_opportunities` - Cross-Bookmaker Arbitrage

**Purpose**: Tracks guaranteed profit opportunities across multiple bookmakers.

**Primary Key**: `arb_id` (SERIAL)

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | VARCHAR(255) | Event identifier |
| `game_date` | DATE | Game date |
| `matchup` | VARCHAR(255) | Team matchup |
| `bookmaker_a`, `bookmaker_b` | VARCHAR(100) | Bookmaker names |
| `odds_a_american`, `odds_b_american` | DECIMAL(10,2) | American odds |
| `odds_a_decimal`, `odds_b_decimal` | DECIMAL(10,4) | Decimal odds |
| `arb_percentage` | DECIMAL(6,4) | Guaranteed profit % |
| `total_implied_prob` | DECIMAL(6,4) | Sum of implied probs |
| `stake_a`, `stake_b` | DECIMAL(10,2) | Recommended stakes |
| `guaranteed_profit` | DECIMAL(10,2) | Expected profit |
| `is_valid` | BOOLEAN | Still valid? |
| `expires_at` | TIMESTAMP | Expected expiration |

**Arbitrage Calculation**:
```
total_implied_prob = (1 / odds_a_decimal) + (1 / odds_b_decimal)
arb_percentage = 1 - total_implied_prob
```

If `arb_percentage > 0`, arbitrage exists.

**Example Query**:
```sql
-- Today's valid arbitrage opportunities
SELECT matchup, bookmaker_a, odds_a_american,
       bookmaker_b, odds_b_american,
       arb_percentage, guaranteed_profit
FROM arbitrage_opportunities
WHERE game_date = CURRENT_DATE
  AND is_valid = TRUE
  AND expires_at > NOW()
ORDER BY arb_percentage DESC;
```

---

### 8. `betting_recommendations` - ML-Based Recommendations

**Purpose**: Daily betting recommendations combining ML predictions with live odds and Kelly sizing.

**Primary Key**: `rec_id` (SERIAL)

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `game_id` | VARCHAR(255) | Game identifier |
| `game_date` | DATE | Game date |
| `matchup` | VARCHAR(255) | Team matchup |
| `bet_side` | VARCHAR(100) | Team or Over/Under |
| `bet_type` | VARCHAR(50) | home/away/over/under/spread |
| `bookmaker` | VARCHAR(100) | Bookmaker name |
| `odds_american`, `odds_decimal` | DECIMAL | Odds |
| `ml_prob` | DECIMAL(6,4) | Model probability (0-1) |
| `implied_prob` | DECIMAL(6,4) | Market implied prob |
| `edge` | DECIMAL(6,4) | ml_prob - implied_prob |
| `ev` | DECIMAL(10,4) | Expected value |
| `kelly_fraction` | DECIMAL(6,4) | Kelly bet size (capped 5%) |
| `recommended_stake` | DECIMAL(10,2) | Recommended $ amount |
| `result` | VARCHAR(50) | win/loss/push/pending |
| `profit_loss` | DECIMAL(10,2) | Final P&L |
| `is_critical` | BOOLEAN | Edge >= 10%? |
| `is_paper_trade` | BOOLEAN | Paper or real money? |

**Kelly Criterion**:
```
kelly_raw = (ml_prob * odds_decimal - 1) / (odds_decimal - 1)
kelly_fraction = min(kelly_raw, 0.05)  # Cap at 5%
recommended_stake = bankroll * kelly_fraction
```

**Example Query**:
```sql
-- Today's top picks
SELECT matchup, bet_side, odds_american,
       edge, recommended_stake, bookmaker
FROM betting_recommendations
WHERE game_date = CURRENT_DATE
  AND result IS NULL
ORDER BY edge DESC
LIMIT 3;
```

---

## Data Types Reference

| PostgreSQL Type | Description | Range/Notes |
|----------------|-------------|-------------|
| TEXT | Variable-length string | Unlimited |
| VARCHAR(N) | Variable-length string | Max N characters |
| INTEGER | 32-bit integer | -2B to 2B |
| DECIMAL(M,N) | Exact decimal | M total digits, N after decimal |
| DOUBLE PRECISION | 64-bit float | 15 decimal digits precision |
| DATE | Calendar date | YYYY-MM-DD |
| TIMESTAMP | Date + time | Microsecond precision |
| BOOLEAN | True/false | TRUE/FALSE/NULL |
| TEXT[] | Array of text | Variable length array |

---

## Index Strategy

### Primary Indexes (All Tables)
- **Primary keys**: Automatically indexed
- **Foreign keys**: Indexed for JOIN performance

### Query-Specific Indexes
- **Date ranges**: `idx_games_date`, `idx_rec_game_date`
- **Player lookups**: `idx_pbp_athlete_1`, `idx_computed_player_box_player`
- **Team lookups**: `idx_pbp_team`, `idx_computed_team_box_team`
- **Shot analytics**: `idx_pbp_shot_zone`, `idx_pbp_shot_distance`

### Partial Indexes (Filtered)
- **Shooting plays only**: `WHERE shooting_play = 1`
- **Valid arbitrage**: `WHERE is_valid = TRUE`
- **Critical bets**: `WHERE is_critical = TRUE`

### Composite Indexes (Multi-Column)
- `(game_id, shot_zone)` - Game-specific shot charts
- `(athlete_id_1, shot_zone)` - Player shot profiles
- `(team_id, game_date)` - Team history queries

---

## Query Performance Tips

### Use Appropriate Indexes
```sql
-- GOOD: Uses idx_pbp_game
SELECT * FROM hoopr_play_by_play WHERE game_id = '401584893';

-- BAD: Full table scan
SELECT * FROM hoopr_play_by_play WHERE text LIKE '%LeBron%';
```

### Leverage Partial Indexes
```sql
-- GOOD: Uses idx_pbp_shot_zone (partial index)
SELECT * FROM hoopr_play_by_play
WHERE shooting_play = 1 AND shot_zone = 'restricted_area';

-- BAD: Doesn't use partial index
SELECT * FROM hoopr_play_by_play
WHERE shot_zone = 'restricted_area';  -- Missing shooting_play=1
```

### Use Computed Tables
```sql
-- GOOD: Fast, accurate
SELECT * FROM computed_player_box WHERE game_id = '401584893';

-- AVOID: Slow, inaccurate (for 2013-2024)
SELECT * FROM hoopr_player_box WHERE game_id = '401584893';
```

### EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT shot_zone, COUNT(*) as shots
FROM hoopr_play_by_play
WHERE athlete_id_1 = 2544 AND shooting_play = 1
GROUP BY shot_zone;
```

---

## Migration Strategy

### Adding New Tables
1. Create migration SQL in `sql/migrations/XXX_description.sql`
2. Test locally
3. Update `sql/init/` for fresh installations
4. Document in this file

### Modifying Existing Tables
1. Always use `ALTER TABLE` (never drop/recreate)
2. Add columns with `IF NOT EXISTS`
3. Make nullable initially, backfill, then add NOT NULL
4. Update indexes if needed

### Example Migration
```sql
-- sql/migrations/004_add_player_injury_status.sql
ALTER TABLE hoopr_player_box
ADD COLUMN IF NOT EXISTS injury_status TEXT;

-- Backfill with data...
UPDATE hoopr_player_box SET injury_status = 'active' WHERE active = 1;

-- Add constraint
ALTER TABLE hoopr_player_box
ADD CONSTRAINT valid_injury_status
CHECK (injury_status IN ('active', 'injured', 'out', 'questionable'));
```

---

## Maintenance

### Regular Tasks

**Daily**:
- Load new games: `python scripts/daily_data_sync.py`

**Weekly**:
- Vacuum analyze: `VACUUM ANALYZE;`
- Check table sizes: `python scripts/init_local_database.py --stats`

**Monthly**:
- Backup database: `pg_dump > backups/monthly_backup.sql`
- Reindex if needed: `REINDEX DATABASE espn_nba_mcp_synthesis;`

---

## Additional Resources

- **Local Development**: `docs/LOCAL_DEVELOPMENT.md`
- **Box Score Methodology**: `docs/BOX_SCORE_METHODOLOGY.md`
- **Shot Zone Classification**: `docs/SHOT_ZONE_INDEXING.md`
- **Play-by-Play Events**: `docs/PLAY_BY_PLAY_EVENT_SCHEMA.md`
- **SQL Init Scripts**: `sql/init/*.sql`

---

*Last Updated: 2025-01-07*
*Schema Version: 1.0*
