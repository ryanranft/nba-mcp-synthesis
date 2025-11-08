# Local Database Validation Plan

## Overview

**Database**: `nba_mcp_synthesis` (Local PostgreSQL)
**Location**: `localhost:5432`
**Total Expected Data**: ~28-30 million rows
**Purpose**: Cost reduction and performance improvement by migrating from AWS RDS to local PostgreSQL

### Database Structure

| Schema | Tables | Rows | Source | Status |
|--------|--------|------|--------|--------|
| **raw** | 4 | 13,950,762 | Parquet files (hoopR 2002-2025) | ✅ Complete |
| **odds** | 5 | 22,994 | RDS migration | ✅ Complete |
| **public** | 17 | ~14,000,000 | RDS migration | ⏳ In Progress |
| **computed** | 0 | 0 | Future derived data | Ready |
| **betting** | 0 | 0 | Future automation | Ready |

**Total**: ~28-30M rows across all schemas

---

## Validation Phases

### Phase 1: Raw Schema Validation ✅

**Status**: COMPLETE
**Tables**: `raw.schedule`, `raw.team_box`, `raw.player_box`, `raw.play_by_play`
**Data Source**: Parquet files from hoopR (2002-2025 NBA seasons)

#### Validation Script
**File**: `scripts/validate_hoopr_data.py` (UPDATED for raw schema)

#### Validation Checks
1. **Row Count Validation**
   - `raw.schedule`: 28,000-35,000 rows (✅ 30,758)
   - `raw.team_box`: 56,000-70,000 rows (✅ 59,670)
   - `raw.player_box`: 700,000-900,000 rows (✅ 785,505)
   - `raw.play_by_play`: 12,000,000-15,000,000 rows (✅ 13,074,829)

2. **Date Range Validation**
   - Expected: 2002-2025 NBA seasons
   - Actual: 2001-10-30 to 2025-04-13

3. **Year Coverage**
   - All 24 years (2002-2025) present
   - No missing seasons

4. **NULL Value Checks**
   - Critical columns (game_id, team_id, player_id) have no NULLs
   - Expected NULLs in optional fields only

5. **Sample Query Validation**
   - Cross-table joins work correctly
   - Aggregations produce expected results
   - Foreign key relationships intact

#### Run Validation
```bash
python scripts/validate_hoopr_data.py --schema raw --context development
```

---

### Phase 2: Odds Schema Validation ✅

**Status**: COMPLETE
**Tables**: `odds.bookmakers`, `odds.events`, `odds.market_types`, `odds.odds_snapshots`, `odds.scores`
**Data Source**: Migrated from RDS `nba_simulator`

#### Validation Script
**File**: `scripts/validate_odds_schema.py` (NEW)

#### Validation Checks
1. **Row Count Validation**
   - `odds.bookmakers`: 21 rows (compare with RDS)
   - `odds.events`: 77 rows
   - `odds.market_types`: 36 rows
   - `odds.odds_snapshots`: 22,860 rows
   - `odds.scores`: 0 rows (expected)

2. **Data Integrity**
   - All bookmaker_ids exist in bookmakers table
   - All event_ids exist in events table
   - All market_type_ids exist in market_types table
   - No orphaned foreign keys

3. **Timestamp Validation**
   - All timestamps in valid range
   - commence_time in future or recent past
   - created_at/updated_at consistency

4. **NULL Value Checks**
   - No NULLs in required fields
   - Expected NULLs only in optional fields

#### Run Validation
```bash
python scripts/validate_odds_schema.py --context development
```

---

### Phase 3: Public Schema Validation ⏳

**Status**: IN PROGRESS (RDS Migration Running)
**Tables**: 17 tables including `temporal_events`, `game_state_snapshots`, NBA API tables
**Data Source**: Migrated from RDS `nba_simulator`

#### Validation Script
**File**: `scripts/validate_public_schema.py` (NEW)

#### Priority 1 Tables (Critical - 14.1M rows)
| Table | Expected Rows | Validation |
|-------|---------------|------------|
| `temporal_events` | 14,114,617 | Compare with RDS count |
| `game_state_snapshots` | 200 | Data integrity |
| `lineup_snapshots` | 400 | Data integrity |
| `player_plus_minus_snapshots` | 2,159 | Data integrity |

#### Priority 2 Tables (Important - ~0.5M rows)
| Table | Expected Rows | Validation |
|-------|---------------|------------|
| `nba_api_comprehensive` | 13,154 | API data completeness |
| `nba_api_player_dashboards` | 34,566 | Player stats integrity |
| `nba_api_team_dashboards` | 210 | Team stats integrity |
| `box_score_players` | 408,833 | Box score consistency |
| `box_score_teams` | 15,900 | Team totals match |
| `games` | 44,828 | Game metadata |
| `play_by_play` | 6,781,155 | Event-level data |
| `player_biographical` | 3,632 | Player info |
| `teams` | 87 | Team metadata |
| `team_seasons` | 952 | Season records |

#### Priority 3 Tables (System/Audit)
| Table | Expected Rows | Validation |
|-------|---------------|------------|
| `ddl_audit_log` | 23 | Audit trail |
| `ddl_schema_version` | 1 | Version tracking |
| `dims_*` tables | Various | System metadata |

#### Validation Checks
1. **Migration Completeness**
   - All tables migrated from RDS
   - Row counts match RDS exactly
   - No missing or corrupted data

2. **Data Type Validation**
   - All columns have correct data types
   - Constraints properly migrated
   - Indexes exist (will be created separately)

3. **Sample Query Validation**
   - Complex queries execute successfully
   - Join performance acceptable
   - Aggregations produce correct results

4. **Temporal Data Validation**
   - `temporal_events` covers all games
   - Timestamps in chronological order
   - No gaps in event sequences

#### Run Validation
```bash
python scripts/validate_public_schema.py --context development
```

---

### Phase 4: Migration Completeness Validation

**Purpose**: Ensure all data successfully migrated from RDS to local database

#### Validation Script
**File**: `scripts/validate_migration_completeness.py` (NEW)

#### Validation Checks
1. **Table Count Comparison**
   - Count all tables in RDS vs Local
   - Identify any missing tables
   - Report tables not migrated

2. **Row Count Comparison**
   - For each migrated table, compare RDS vs Local row counts
   - Must match exactly (0% data loss tolerance)
   - Generate detailed comparison report

3. **Schema Comparison**
   - Compare table structures (columns, types, constraints)
   - Ensure no schema drift during migration
   - Validate sequence values

4. **Data Sample Validation**
   - Random sample of 1000 rows per table
   - Compare values between RDS and Local
   - Ensure no data corruption

#### Run Validation
```bash
python scripts/validate_migration_completeness.py
```

#### Expected Output
```
Migration Completeness Report
================================================================================
RDS Database: nba_simulator
Local Database: nba_mcp_synthesis

Tables Migrated: 26/26 (100%)
Total Rows Migrated: 28,234,567
Data Integrity: PASS

Table-by-Table Comparison:
  ✅ odds.bookmakers: 21/21 rows (100%)
  ✅ odds.events: 77/77 rows (100%)
  ✅ public.temporal_events: 14,114,617/14,114,617 rows (100%)
  ...

Summary: All data migrated successfully with 0% data loss
================================================================================
```

---

### Phase 5: Cross-Schema Integration Validation

**Purpose**: Ensure referential integrity and relationships between schemas

#### Validation Script
**File**: `scripts/validate_cross_schema.py` (NEW)

#### Validation Checks
1. **game_id Consistency**
   - All game_ids in `raw.schedule` exist
   - All game_ids in `raw.play_by_play` reference valid games
   - All game_ids in `public.temporal_events` reference valid games
   - All game_ids in `odds.events` can be linked to games

2. **Orphaned Record Detection**
   - No play-by-play events without corresponding game
   - No box scores without corresponding game
   - No odds snapshots without corresponding event

3. **Foreign Key Validation**
   - All team_ids reference valid teams
   - All player_ids reference valid players
   - All bookmaker_ids reference valid bookmakers

4. **Data Consistency**
   - Final scores in `raw.schedule` match last event in `raw.play_by_play`
   - Team totals in `raw.team_box` sum to player totals in `raw.player_box`
   - Game counts consistent across all schemas

#### Run Validation
```bash
python scripts/validate_cross_schema.py --context development
```

---

### Phase 6: Performance & Index Validation

**Purpose**: Ensure optimal query performance on local database

#### Optimization Script
**File**: `scripts/optimize_local_database.py` (NEW)

#### Tasks
1. **Create Missing Indexes**
   - game_id indexes on all tables
   - Date range indexes for temporal queries
   - Player/team lookup indexes
   - Composite indexes for common joins

2. **Index Health Check**
   - Verify all expected indexes exist
   - Check index bloat
   - Rebuild fragmented indexes

3. **Table Statistics Update**
   - Run VACUUM ANALYZE on all tables
   - Update table statistics for query planner
   - Estimate table sizes

4. **Performance Benchmarks**
   - Execute common queries and measure time
   - Compare with RDS baseline
   - Ensure local performance ≥ RDS performance

#### Run Optimization
```bash
python scripts/optimize_local_database.py --context development
```

#### Expected Indexes

**Raw Schema:**
```sql
-- Already exist (confirmed)
CREATE INDEX idx_raw_schedule_game_id ON raw.schedule(game_id);
CREATE INDEX idx_raw_schedule_game_date ON raw.schedule(game_date);
CREATE INDEX idx_raw_team_box_game_id ON raw.team_box(game_id);
CREATE INDEX idx_raw_player_box_game_id ON raw.player_box(game_id);
CREATE INDEX idx_raw_play_by_play_game_id ON raw.play_by_play(game_id);
```

**Odds Schema:**
```sql
-- To be created
CREATE INDEX idx_odds_events_commence_time ON odds.events(commence_time);
CREATE INDEX idx_odds_snapshots_event_id ON odds.odds_snapshots(event_id);
CREATE INDEX idx_odds_snapshots_bookmaker_id ON odds.odds_snapshots(bookmaker_id);
```

**Public Schema:**
```sql
-- To be created
CREATE INDEX idx_temporal_events_game_id ON public.temporal_events(game_id);
CREATE INDEX idx_temporal_events_timestamp ON public.temporal_events(timestamp);
CREATE INDEX idx_game_state_snapshots_game_id ON public.game_state_snapshots(game_id);
```

---

### Phase 7: Application Testing

**Purpose**: Ensure all application code works correctly with local database

#### Test Categories
1. **Model Training Scripts**
   - `scripts/train_game_outcome_model.py`
   - `scripts/train_kelly_calibrator.py`
   - Verify models train successfully using local data

2. **Feature Preparation**
   - `scripts/prepare_game_features.py`
   - `scripts/prepare_game_features_complete.py`
   - Ensure feature extraction works

3. **Daily Workflows**
   - `scripts/daily_data_sync.py`
   - `scripts/daily_betting_analysis.py`
   - Test end-to-end daily operations

4. **Paper Trading**
   - `scripts/paper_trade_today.py`
   - Test betting recommendations generation

5. **Dashboards**
   - `scripts/paper_trade_dashboard.py`
   - `scripts/production_monitoring_dashboard.py`
   - Verify visualization works

#### Run Application Tests
```bash
# Test model training
python scripts/train_game_outcome_model.py --test-mode --context development

# Test feature preparation
python scripts/prepare_game_features.py --limit 100 --context development

# Test daily workflow
python scripts/daily_betting_analysis.py --dry-run --context development
```

---

### Phase 8: Performance Benchmarking

**Purpose**: Compare local database performance with RDS baseline

#### Benchmark Script
**File**: `scripts/benchmark_local_vs_rds.py` (NEW)

#### Benchmark Queries
1. **Simple Lookups** (should be faster locally)
   ```sql
   SELECT * FROM raw.schedule WHERE game_id = '401584798';
   ```

2. **Aggregations** (should be similar)
   ```sql
   SELECT
       season,
       COUNT(*) as games,
       AVG(home_team_score) as avg_home_score
   FROM raw.schedule
   GROUP BY season;
   ```

3. **Complex Joins** (network latency eliminated)
   ```sql
   SELECT
       s.game_id,
       s.game_date,
       COUNT(p.sequence_number) as num_events
   FROM raw.schedule s
   JOIN raw.play_by_play p ON s.game_id = p.game_id
   GROUP BY s.game_id, s.game_date
   LIMIT 1000;
   ```

4. **Large Scans** (disk I/O dependent)
   ```sql
   SELECT COUNT(*)
   FROM public.temporal_events
   WHERE timestamp > '2024-01-01';
   ```

#### Expected Results
| Query Type | RDS (ms) | Local (ms) | Improvement |
|------------|----------|------------|-------------|
| Simple Lookup | 50-100 | 1-5 | 10-50x faster |
| Aggregation | 200-500 | 100-300 | 2-3x faster |
| Complex Join | 1000-2000 | 500-1000 | 2x faster |
| Large Scan | 5000-10000 | 3000-6000 | 1.5-2x faster |

---

## Backup Strategy

### Manual Backup Script
**File**: `scripts/backup_local_database.sh` (NEW)

#### Backup Process
```bash
#!/bin/bash
# Backup local PostgreSQL database

BACKUP_DIR="/path/to/backups/nba_mcp_synthesis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/nba_mcp_synthesis_${TIMESTAMP}.dump"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run pg_dump
PGPASSWORD="nba_mcp_local_dev" pg_dump \
  -h localhost \
  -p 5432 \
  -U ryanranft \
  -d nba_mcp_synthesis \
  -Fc \
  -f "$BACKUP_FILE"

# Compress backup (optional)
gzip "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +7 -delete

echo "Backup complete: ${BACKUP_FILE}.gz"
```

#### Restore Process
```bash
#!/bin/bash
# Restore from backup

BACKUP_FILE="/path/to/backups/nba_mcp_synthesis/nba_mcp_synthesis_20250108_120000.dump.gz"

# Decompress if needed
gunzip -k "$BACKUP_FILE"

# Drop and recreate database
PGPASSWORD="nba_mcp_local_dev" psql -h localhost -p 5432 -U ryanranft -c "DROP DATABASE IF EXISTS nba_mcp_synthesis;"
PGPASSWORD="nba_mcp_local_dev" psql -h localhost -p 5432 -U ryanranft -c "CREATE DATABASE nba_mcp_synthesis;"

# Restore from dump
PGPASSWORD="nba_mcp_local_dev" pg_restore \
  -h localhost \
  -p 5432 \
  -U ryanranft \
  -d nba_mcp_synthesis \
  "${BACKUP_FILE%.gz}"

echo "Restore complete"
```

#### Integration with nba-simulator-aws Cron Jobs
**Note**: This backup script will be integrated into the centralized cron job system in the `nba-simulator-aws` project to:
- Avoid rate limit conflicts
- Centralize all scheduled tasks
- Share backup infrastructure
- Coordinate with other NBA data workflows

---

## RDS Decommissioning Plan

### Timeline: 2-Week Validation Period

#### Week 1: Intensive Testing
- ✅ Complete all validation phases
- ✅ Run all application workflows
- ✅ Monitor for errors or issues
- ✅ Compare query results with RDS
- ✅ Performance benchmarking

#### Week 2: Production Cutover
- ✅ Update all application code to default to `development` context
- ✅ Document RDS credentials as fallback
- ✅ Run full end-to-end tests
- ✅ Monitor application in production use
- ✅ No issues for 7 consecutive days

#### Decommissioning Checklist
- [ ] All validation scripts pass
- [ ] Application tests complete successfully
- [ ] Performance meets or exceeds RDS
- [ ] Backup system operational
- [ ] Team confirms no issues for 7 days
- [ ] RDS credentials documented as fallback
- [ ] Final backup of RDS database created
- [ ] **Stop RDS instance** (don't delete immediately)
- [ ] Monitor for 48 hours
- [ ] **Delete RDS instance** if no issues

### Cost Savings
- **Before**: $50-150/month (RDS db.t3.medium or similar)
- **After**: $0/month (local PostgreSQL)
- **Annual Savings**: $600-1,800/year

---

## Validation Scripts Quick Reference

| Script | Purpose | Status | Command |
|--------|---------|--------|---------|
| `validate_hoopr_data.py` | Validate raw schema (parquet data) | ✅ Updated | `python scripts/validate_hoopr_data.py --schema raw --context development` |
| `validate_box_scores.py` | Validate box score consistency | ✅ Updated | `python scripts/validate_box_scores.py --context development` |
| `validate_odds_schema.py` | Validate odds schema migration | 📝 New | `python scripts/validate_odds_schema.py --context development` |
| `validate_public_schema.py` | Validate public schema migration | 📝 New | `python scripts/validate_public_schema.py --context development` |
| `validate_migration_completeness.py` | Compare RDS vs Local | 📝 New | `python scripts/validate_migration_completeness.py` |
| `validate_cross_schema.py` | Validate cross-schema integrity | 📝 New | `python scripts/validate_cross_schema.py --context development` |
| `optimize_local_database.py` | Create indexes and optimize | 📝 New | `python scripts/optimize_local_database.py --context development` |
| `benchmark_local_vs_rds.py` | Performance comparison | 📝 New | `python scripts/benchmark_local_vs_rds.py` |

---

## Success Criteria

### Database Migration Success
- ✅ All tables migrated (0 missing tables)
- ✅ All rows migrated (0% data loss)
- ✅ All schemas intact (raw, odds, public)
- ✅ All indexes created
- ✅ Database optimized (VACUUM ANALYZE complete)

### Validation Success
- ✅ All validation scripts pass (100% pass rate)
- ✅ No data integrity issues
- ✅ No orphaned records
- ✅ Cross-schema relationships intact

### Application Success
- ✅ All application workflows execute successfully
- ✅ Model training completes without errors
- ✅ Daily automation runs smoothly
- ✅ Dashboards render correctly

### Performance Success
- ✅ Query performance ≥ RDS baseline
- ✅ No performance regressions
- ✅ Application response time acceptable

### Operational Success
- ✅ Backup system operational
- ✅ Restore process tested
- ✅ Team comfortable with local database
- ✅ 7 days of stable operation

---

## Next Steps

1. **Wait for Migration to Complete**: Background process `210053` is currently migrating ~14M rows from RDS
2. **Run All Validation Scripts**: Execute in order (Phases 1-5)
3. **Optimize Database**: Create indexes and run VACUUM ANALYZE
4. **Test Applications**: Run all application workflows
5. **Benchmark Performance**: Compare with RDS baseline
6. **2-Week Validation Period**: Monitor for issues
7. **Decommission RDS**: After successful validation

---

## Related Documentation

- **Migration Script**: `scripts/migrate_rds_to_local.py`
- **Credentials**: `.claude/CLAUDE.md` (hierarchical secrets system)
- **Original Validation Plans**: `docs/plans/AGENT9_TESTING_COMPLETE.md`, `docs/plans/PHASE11A_PROGRESS_REPORT.md`
- **Box Score Methodology**: `docs/BOX_SCORE_METHODOLOGY.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`

---

**Document Status**: Living Document
**Last Updated**: 2025-01-07
**Version**: 1.0
**Owner**: nba-mcp-synthesis Migration Team
