# Parquet Data Loading Guide

## Overview

This guide explains how to load NBA data from hoopR parquet files into your local PostgreSQL database.

## Table Naming Convention

All tables use the `{source}_{data_type}` naming pattern:

| Table Name | Description | Source | Granularity |
|------------|-------------|--------|-------------|
| `hoopr_play_by_play` | Event-level play data | hoopR/ESPN | Event-level (~13M rows) |
| `hoopr_player_box` | Player box scores | hoopR/ESPN | Player-game-level (~785K rows) |
| `hoopr_team_box` | Team box scores | hoopR/ESPN | Team-game-level (~60K rows) |
| `hoopr_schedule` | Game schedule/metadata | hoopR/ESPN | Game-level (~31K rows) |

**Why `hoopr_`?**
- Clearly indicates data source (ESPN data via hoopR R package)
- Distinguishes from `computed_*` tables (internally calculated)
- Distinguishes from `nba_api_*` tables (from stats.nba.com)
- Makes data lineage transparent

## Data Sources

### Local Parquet Files

Location: `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`

```
hoopR/nba/
├── load_nba_schedule/parquet/     # Game metadata
│   ├── nba_data_2002.parquet
│   ├── nba_data_2003.parquet
│   └── ... (24 files, 2002-2025)
│
├── load_nba_team_box/parquet/     # Team box scores
│   ├── nba_data_2002.parquet
│   └── ... (24 files)
│
├── load_nba_player_box/parquet/   # Player box scores
│   ├── nba_data_2002.parquet
│   └── ... (24 files)
│
└── load_nba_pbp/parquet/          # Play-by-play events
    ├── nba_data_2002.parquet
    └── ... (24 files)
```

### Data Coverage

- **Years:** 2002-2025 (24 NBA seasons)
- **Games:** ~30,758 total games
- **Events:** ~13,074,829 play-by-play events
- **Players:** ~785,505 player-game records

## Loading Data

### Quick Start

```bash
# Full reload (all datasets, all years)
python scripts/load_parquet_to_postgres.py

# This will:
# 1. Truncate existing hoopr_* tables
# 2. Load all 24 years from parquet files
# 3. Take ~25 minutes to complete
```

### Command Line Options

```bash
# Preview without loading (dry run)
python scripts/load_parquet_to_postgres.py --dry-run

# Load specific years
python scripts/load_parquet_to_postgres.py --years 2023-2025

# Load single dataset
python scripts/load_parquet_to_postgres.py --table schedule
python scripts/load_parquet_to_postgres.py --table team_box
python scripts/load_parquet_to_postgres.py --table player_box
python scripts/load_parquet_to_postgres.py --table play_by_play

# Append mode (don't truncate existing data)
python scripts/load_parquet_to_postgres.py --no-truncate --years 2025

# Use development database (local PostgreSQL)
python scripts/load_parquet_to_postgres.py --context development

# Use production database (AWS RDS)
python scripts/load_parquet_to_postgres.py --context production
```

### Example Output

```
================================================================================
NBA MCP Synthesis - Parquet to PostgreSQL Loader
================================================================================
Timestamp: 2025-01-07 14:30:00
Context: development
Source: /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba
Years: 2002-2025 (24 years)
Datasets: schedule, team_box, player_box, play_by_play
Mode: LIVE (will modify database)
Truncate: Yes (will delete existing data)

Connecting to Database
--------------------------------------------------------------------------------
  Database: espn_nba_mcp_synthesis
  Host: localhost
  Port: 5432
  ✅ Connection established

Pre-flight Checks
--------------------------------------------------------------------------------
  ✅ All 4 required tables exist

Estimating Data Size
--------------------------------------------------------------------------------
  hoopr_schedule                        30,758 rows
  hoopr_team_box                        59,670 rows
  hoopr_player_box                     785,505 rows
  hoopr_play_by_play                13,074,829 rows
  ───────────────────────── ───────────────
  TOTAL                            13,950,762 rows

⚠️  This will TRUNCATE and reload 4 table(s)
Continue? [y/N]: y

Phase: Loading hoopr_schedule
--------------------------------------------------------------------------------
  📅 Loading schedule: 100%|██████████| 24/24 [00:45<00:00]
  ✅ Complete: 30,758 total rows

Phase: Loading hoopr_team_box
--------------------------------------------------------------------------------
  📅 Loading team_box: 100%|██████████| 24/24 [01:30<00:00]
  ✅ Complete: 59,670 total rows

Phase: Loading hoopr_player_box
--------------------------------------------------------------------------------
  📅 Loading player_box: 100%|██████████| 24/24 [02:30<00:00]
  ✅ Complete: 785,505 total rows

Phase: Loading hoopr_play_by_play
--------------------------------------------------------------------------------
  📅 Loading play_by_play: 100%|██████████| 24/24 [18:00<00:00]
  ✅ Complete: 13,074,829 total rows

================================================================================
✅ LOADING COMPLETE
================================================================================
Final Statistics:
  hoopr_schedule                        30,758 rows
  hoopr_team_box                        59,670 rows
  hoopr_player_box                     785,505 rows
  hoopr_play_by_play                13,074,829 rows
  ───────────────────────── ───────────────
  TOTAL                            13,950,762 rows

  Total Time: 22.5 minutes
  Avg Speed: 10,334 rows/second

💡 Next Steps:
  1. Validate data: python scripts/validate_hoopr_data.py
  2. Rebuild indexes: psql -c 'REINDEX DATABASE espn_nba_mcp_synthesis;'
  3. Update statistics: psql -c 'VACUUM ANALYZE;'

================================================================================
```

## Validating Data

After loading, always validate the data:

```bash
# Run all validation checks
python scripts/validate_hoopr_data.py

# Verbose output (shows all checks)
python scripts/validate_hoopr_data.py --verbose

# Validate production database
python scripts/validate_hoopr_data.py --context production
```

### Validation Checks

The validation script performs:

1. **Row Count Validation:** Ensures row counts are within expected ranges
2. **Date Range Validation:** Checks dates are 2002-2025
3. **Year Coverage:** Verifies all 24 years have data
4. **NULL Value Checks:** Ensures critical columns have no NULLs
5. **Sample Queries:** Tests joins and aggregations work

### Example Validation Output

```
================================================================================
NBA MCP Synthesis - hoopR Data Validation
================================================================================

Row Count Validation
--------------------------------------------------------------------------------
  ✅ hoopr_schedule                     30,758 rows (expected: 28,000-35,000)
  ✅ hoopr_team_box                     59,670 rows (expected: 56,000-70,000)
  ✅ hoopr_player_box                  785,505 rows (expected: 750,000-900,000)
  ✅ hoopr_play_by_play             13,074,829 rows (expected: 12,000,000-15,000,000)

Date Range Validation
--------------------------------------------------------------------------------
  ✅ hoopr_schedule              2002-10-29 to 2025-06-17
  ✅ hoopr_team_box              2002-10-29 to 2025-06-17
  ✅ hoopr_player_box            2002-10-29 to 2025-06-17
  ✅ hoopr_play_by_play          2002-10-29 to 2025-06-17

Year Coverage Validation
--------------------------------------------------------------------------------
  ✅ hoopr_schedule              24/24 years (complete)
  ✅ hoopr_team_box              24/24 years (complete)
  ✅ hoopr_player_box            24/24 years (complete)
  ✅ hoopr_play_by_play          24/24 years (complete)

NULL Value Validation
--------------------------------------------------------------------------------
  ✅ hoopr_schedule              No NULL values in critical columns
  ✅ hoopr_team_box              No NULL values in critical columns
  ✅ hoopr_player_box            No NULL values in critical columns
  ✅ hoopr_play_by_play          No NULL values in critical columns

Sample Query Validation
--------------------------------------------------------------------------------
  ✅ Recent games (2024+): 1,312 games
  ✅ Team box join: 2,624 team-games
  ✅ Unique players (2024+): 612 players
  ✅ Event types (2024+): 42 unique types

================================================================================
Validation Summary
================================================================================
Total Checks: 20
Passed: 20
Failed: 0

✅ ALL VALIDATIONS PASSED

Data is ready for use:
  - Feature extraction: python scripts/prepare_features_from_parquet.py
  - Model training: python scripts/train_game_outcome_model.py
```

## Troubleshooting

### Issue: "Missing parquet files"

**Symptom:**
```
⚠️  Missing: /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/load_nba_schedule/parquet/nba_data_2024.parquet
```

**Solution:**
- Check that parquet files exist at the expected location
- Verify file naming matches pattern: `nba_data_{year}.parquet`
- Use `--years 2002-2023` to skip missing years

### Issue: "Connection failed"

**Symptom:**
```
❌ Connection failed: could not connect to server
```

**Solution:**
1. Ensure PostgreSQL is running:
   ```bash
   /Applications/Docker.app/Contents/Resources/bin/docker compose up -d postgres
   ```

2. Check credentials are loaded:
   ```bash
   python3 -c "from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config; load_secrets_hierarchical(); print(get_database_config())"
   ```

3. Verify correct context:
   ```bash
   python scripts/load_parquet_to_postgres.py --context development
   ```

### Issue: "Table does not exist"

**Symptom:**
```
❌ Missing tables: hoopr_schedule, hoopr_team_box
```

**Solution:**
1. Initialize database schema:
   ```bash
   /Applications/Docker.app/Contents/Resources/bin/docker compose up -d postgres
   ```

2. Verify tables were created:
   ```bash
   psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -c "\dt hoopr_*"
   ```

### Issue: "Out of memory"

**Symptom:**
Script crashes or becomes very slow during large file processing.

**Solution:**
1. Load one table at a time:
   ```bash
   python scripts/load_parquet_to_postgres.py --table schedule
   python scripts/load_parquet_to_postgres.py --table team_box
   python scripts/load_parquet_to_postgres.py --table player_box
   python scripts/load_parquet_to_postgres.py --table play_by_play
   ```

2. Load fewer years at once:
   ```bash
   python scripts/load_parquet_to_postgres.py --years 2002-2010
   python scripts/load_parquet_to_postgres.py --years 2011-2020 --no-truncate
   python scripts/load_parquet_to_postgres.py --years 2021-2025 --no-truncate
   ```

### Issue: "Validation failed"

**Symptom:**
```
❌ hoopr_schedule: 15,234 rows (expected: 28,000-35,000)
```

**Solution:**
1. Check which years are missing:
   ```bash
   python scripts/validate_hoopr_data.py --verbose
   ```

2. Reload missing years:
   ```bash
   python scripts/load_parquet_to_postgres.py --years 2023-2025 --no-truncate
   ```

3. Re-validate:
   ```bash
   python scripts/validate_hoopr_data.py
   ```

## Maintenance

### Refreshing Data

To update with new data (e.g., add 2026 season):

```bash
# 1. Load new year only (append mode)
python scripts/load_parquet_to_postgres.py --years 2026 --no-truncate

# 2. Validate
python scripts/validate_hoopr_data.py

# 3. Rebuild indexes
psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -c "REINDEX DATABASE espn_nba_mcp_synthesis;"

# 4. Update statistics
psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -c "VACUUM ANALYZE;"
```

### Full Reload

To completely refresh all data:

```bash
# 1. Backup first (optional but recommended)
pg_dump -h localhost -U ryanranft espn_nba_mcp_synthesis > backup_$(date +%Y%m%d).sql

# 2. Full reload (truncate + load all years)
python scripts/load_parquet_to_postgres.py

# 3. Validate
python scripts/validate_hoopr_data.py

# 4. Optimize database
psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -c "REINDEX DATABASE espn_nba_mcp_synthesis; VACUUM ANALYZE;"
```

## Performance Tips

1. **Use SSD storage** for PostgreSQL data directory (faster I/O)
2. **Increase batch size** for faster loading (edit `batch_size` in script)
3. **Load tables in parallel** by running multiple instances:
   ```bash
   # Terminal 1
   python scripts/load_parquet_to_postgres.py --table schedule &

   # Terminal 2
   python scripts/load_parquet_to_postgres.py --table team_box &

   # Wait for both to complete
   wait
   ```

4. **Disable indexes during load** (advanced):
   ```sql
   -- Drop indexes
   DROP INDEX idx_hoopr_play_by_play_game_id;

   -- Load data
   python scripts/load_parquet_to_postgres.py

   -- Recreate indexes
   CREATE INDEX idx_hoopr_play_by_play_game_id ON hoopr_play_by_play(game_id);
   ```

## Data Quality Notes

### Known Issues

From `sql/init/01_games_table.sql` documentation:

1. **Hoopr Inflation (2013-2024):** Hoopr box scores show 3-14% more FGA/FGM/PTS than play-by-play
   - This is an **external issue** (Hoopr data quality)
   - Our play-by-play data is 100% internally consistent
   - **Solution:** Always use `computed_*` tables (derived from play-by-play)

2. **Data Quality Tiers:**
   - **Tier A (Excellent):** 2002, 2004 (95-100% Hoopr match rate)
   - **Tier B (Good):** 2003, 2005-2012 (85-95% match rate)
   - **Tier C (Fair):** 2013-2024 (70-85% match rate)

### Best Practices

1. **Use play-by-play for truth:** `hoopr_play_by_play` is the source of truth
2. **Compute stats from events:** Use `computed_player_box` and `computed_team_box`
3. **Filter by quality tier:** For ML models, consider filtering to Tier A/B years
4. **Document data source:** Always note which tables you're using in analyses

## Related Documentation

- **Database Schema:** `docs/DATABASE_SCHEMA.md`
- **Data Quality:** `reports/DATA_QUALITY_BY_ERA.md`
- **Feature Extraction:** `scripts/prepare_features_from_parquet.py`
- **Secrets Management:** `.claude/CLAUDE.md`

---

**Last Updated:** 2025-01-07
**Maintainer:** NBA MCP Synthesis
