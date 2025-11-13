# S3 Data Pipeline - ARCHIVED (2025-01-07)

## Status: DEPRECATED ❌

This S3-based daily data pipeline has been **archived and deprecated** as of January 7, 2025.

## Reason for Deprecation

Data scraping and ingestion is now handled in **a separate directory/repository** managed independently. This pipeline was built assuming local scraping → S3 staging → database loading, but the architecture has changed to handle data ingestion elsewhere.

## What Was Archived

### Files in This Archive:
1. **`load_from_s3.py`** - Loads game data from S3 into PostgreSQL with shot zone classification
2. **`data_fetchers/`** - ESPN API wrapper (hoopr_fetcher.py) for scraping game data
3. **`DAILY_DATA_PIPELINE.md`** - Complete documentation of the S3 pipeline architecture
4. **`daily_data_sync_s3.py`** - Modified daily sync script that uploads to S3
5. **`run_daily_sync_s3.sh`** - Cron wrapper for S3 workflow

### What This Pipeline Did:
```
ESPN API → Local Scraping → S3 Storage → PostgreSQL RDS
                ↓              ↓             ↓
         daily_data_sync.py  S3 Bucket  load_from_s3.py
                                            ↓
                                   Shot Zone Classification
```

**Workflow:**
1. Scrape yesterday's completed games from ESPN API (locally)
2. Upload raw game data to S3 (`s3://nba-mcp-synthesis-data/daily/YYYY-MM-DD/games.json`)
3. Download from S3 and load into PostgreSQL
4. Automatically classify shot zones during insertion

**Schedule:** Was designed to run at 1:30 AM daily via cron

## What Is Still Active

### ✅ Shot Zone Classification System (ACTIVE)
The core shot zone indexing system is **still fully operational** and independent of this pipeline:

- **`mcp_server/spatial/zone_classifier.py`** - ESPN coord transformation + zone classification
- **`mcp_server/spatial/shot_location.py`** - NBA-standard 11-zone definitions
- **Database columns:** `shot_zone`, `shot_distance`, `shot_angle` in `hoopr_play_by_play`
- **Historical data:** 6.16M shots classified (99.99% complete, backfill finished 2025-01-07)

### ✅ Shot Zone Utilities (NEW)
New tools for querying and analyzing shot zones:

- **`scripts/query_shot_zones.py`** - Query database by zone, player, team, date
- **`mcp_server/analytics/shot_zones.py`** - Zone efficiency, player profiles, expected value
- **`docs/SHOT_ZONE_INDEXING.md`** - Complete indexing system documentation

## Why Keep This Code?

This archive preserves a fully functional S3-based ETL pipeline that:
- Demonstrates ESPN API integration
- Shows shot zone classification in action
- Provides S3 staging pattern for data pipelines
- May be useful for future reference or alternative architectures

## If You Need to Use This Code

**Do NOT use this pipeline as-is.** Data scraping is handled elsewhere.

However, you CAN extract useful components:
- **Shot zone classifier:** Already active in `mcp_server/spatial/`
- **ESPN API wrapper:** See `data_fetchers/hoopr_fetcher.py` for reference
- **S3 patterns:** `load_from_s3.py` shows S3 → database loading patterns

## Migration Notes

**From:** S3 pipeline (archived)  
**To:** Shot zone indexing focused on analytics

**What changed:**
- Data ingestion moved to separate directory
- Focus shifted to querying/analyzing existing shot zone data
- S3 staging removed (data ingestion handles this elsewhere)

**What stayed the same:**
- Shot zone classification logic (unchanged)
- Database schema (unchanged)
- 6.16M historical shots (preserved)

## Contact

For questions about:
- **Shot zones:** See `docs/SHOT_ZONE_INDEXING.md`
- **Data ingestion:** Check the separate data scraping directory
- **This archive:** Refer to git history around 2025-01-07

---

**Archived:** January 7, 2025  
**Reason:** Data scraping moved to separate directory  
**Status:** Code preserved but not actively used
