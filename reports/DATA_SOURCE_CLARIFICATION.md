# Data Source Clarification

**Date**: 2025-11-08
**Purpose**: Clarify data sources after database discovery

## Discovery Results

### RDS Database (nba_simulator)

**Schemas Found**:
- `odds` - Betting odds data (23K rows)
- `public` - Main NBA data (35M+ rows)
- `rag` - RAG/embedding data
- `raw_data` - Raw NBA games

### KEY FINDING: No ESPN Data Found

**Expected**: Tables like `espn_raw.nba_box_score`, `espn_raw.nba_play_by_play`, `espn_raw.nba_schedule`

**Actually Found**: hoopR tables in public schema:
```
public.hoopr_play_by_play      13,074,829 rows
public.hoopr_player_box           785,505 rows
public.hoopr_schedule              30,758 rows
public.hoopr_team_box              59,670 rows
```

## Data Source Reality

### Source 1: hoopR (NBA API) - LOCAL DATABASE
- **Location**: `localhost:5432/nba_mcp_synthesis`
- **Schema**: `hoopr_raw`
- **Tables**:
  - `hoopr_raw.nba_schedule` (30,758 rows)
  - `hoopr_raw.nba_team_box` (59,670 rows)
  - `hoopr_raw.nba_player_box` (785,505 rows)
  - `hoopr_raw.nba_play_by_play` (13,074,829 rows)
- **Source**: NBA API via hoopR R package
- **Status**: ✅ Loaded from parquet files (2002-2025)

### Source 2: hoopR (NBA API) - RDS DATABASE
- **Location**: RDS `nba_simulator`
- **Schema**: `public`
- **Tables**:
  - `public.hoopr_schedule` (30,758 rows)
  - `public.hoopr_team_box` (59,670 rows)
  - `public.hoopr_player_box` (785,505 rows)
  - `public.hoopr_play_by_play` (13,074,829 rows)
- **Source**: Same NBA API via hoopR
- **Status**: Needs migration to local

## Implications for Validation Plan

### Original Request
User requested: "External validation of hoopR data using ESPN data"

### Actual Situation
**Both data sources are from hoopR/NBA API**. There is NO ESPN web-scraped data.

### Revised Validation Options

#### Option 1: RDS vs Local Consistency Check
Compare `public.hoopr_*` (RDS) against `hoopr_raw.nba_*` (local):
- Same source (NBA API)
- Same row counts
- Should be identical
- **Purpose**: Verify parquet → local load was correct

#### Option 2: Find Actual ESPN Data
The user mentioned ESPN data exists somewhere. Possible locations:
- Different database?
- Different schema in local database?
- Web scraping project not yet integrated?

#### Option 3: Validate Against NBA Official Stats
Use NBA Stats API directly to validate hoopR data accuracy:
- Pull recent games from stats.nba.com
- Compare box scores
- Validate play-by-play sequences

## Recommended Next Steps

1. **Clarify with User**: Ask where ESPN data actually is
   - Is it in a different database/project?
   - Was it web-scraped separately?
   - Does it need to be fetched first?

2. **If ESPN Data Doesn't Exist**: Proceed with Option 1 (RDS vs Local consistency)
   - Quick validation
   - Confirms parquet load integrity
   - Documents schema reorganization

3. **If ESPN Data Exists Elsewhere**: Locate and integrate it
   - Create proper espn_raw schema
   - Load ESPN data
   - Then run cross-source validation

## Current Database State

### Local Database (nba_mcp_synthesis)
```
hoopr_raw.nba_schedule         30,758 rows
hoopr_raw.nba_team_box         59,670 rows
hoopr_raw.nba_player_box      785,505 rows
hoopr_raw.nba_play_by_play 13,074,829 rows
--------------------------------
Total:                     13,950,762 rows
```

### RDS Database (nba_simulator)
```
public.hoopr_schedule          30,758 rows
public.hoopr_team_box          59,670 rows
public.hoopr_player_box       785,505 rows
public.hoopr_play_by_play  13,074,829 rows
--------------------------------
Total:                     13,950,762 rows

Plus 34 additional tables (odds, temporal_events, box_scores, etc.)
```

## Questions for User

1. Where is the ESPN data located?
   - Separate database?
   - Needs to be scraped first?
   - Part of nba-simulator-aws project?

2. What is the actual validation goal?
   - Verify hoopR data quality?
   - Compare NBA API vs ESPN web scraping?
   - Validate parquet load integrity?

3. Should we proceed with RDS→Local migration regardless?
   - Odds schema (23K rows)
   - Public schema (35M+ rows)
   - Save $600-1800/year on RDS costs
