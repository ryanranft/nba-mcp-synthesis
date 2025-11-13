# Daily NBA Data Pipeline

## Overview

Automated daily ETL pipeline that:
1. **Scrapes** yesterday's completed NBA games from ESPN API (locally)
2. **Uploads** scraped data to S3 for staging
3. **Loads** data from S3 into PostgreSQL database
4. **Classifies** shot zones automatically during insertion

## Architecture

```
ESPN API → Local Scraping → S3 Storage → PostgreSQL RDS
                ↓              ↓             ↓
         daily_data_sync.py  S3 Bucket  load_from_s3.py
                                            ↓
                                   Shot Zone Classification
```

## Components

### 1. Data Fetcher (`mcp_server/data_fetchers/hoopr_fetcher.py`)

Python wrapper around ESPN API that provides hoopR-compatible functionality.

**Methods:**
- `get_games_for_date(date)` - Fetch all games for a date
- `fetch_play_by_play(game_id)` - Fetch detailed play-by-play events
- `get_yesterday_games()` - Get completed games from yesterday

**Usage:**
```python
from mcp_server.data_fetchers import HoopRFetcher

fetcher = HoopRFetcher()
games = fetcher.get_yesterday_games()

for game_id in games:
    game_data = fetcher.fetch_play_by_play(game_id)
    # game_data contains events, coordinates, metadata
```

### 2. S3 Connector (`mcp_server/connectors/s3_connector.py`)

Handles all S3 operations for the pipeline.

**Methods:**
- `upload_game_data(date, games_data)` - Upload game data as JSON
- `download_game_data(date)` - Download game data for a date
- `list_objects(prefix)` - List files in S3

**S3 Structure:**
```
s3://nba-mcp-synthesis-data/
├── daily/
│   ├── 2024-12-01/
│   │   └── games.json
│   ├── 2024-12-02/
│   │   └── games.json
│   └── ...
```

### 3. Daily Sync Script (`scripts/daily_data_sync.py`)

**Purpose:** Scrapes ESPN API and uploads to S3

**Workflow:**
1. Fetch yesterday's completed games from ESPN
2. Fetch play-by-play data for each game
3. Upload all game data to S3 as single JSON file

**Usage:**
```bash
# Sync yesterday's games
python3 scripts/daily_data_sync.py

# Sync specific date
python3 scripts/daily_data_sync.py --date 2024-12-02

# Dry run (no S3 upload)
python3 scripts/daily_data_sync.py --dry-run
```

### 4. Database Loader (`scripts/load_from_s3.py`)

**Purpose:** Load data from S3 into PostgreSQL with shot zone classification

**Workflow:**
1. Download game data from S3
2. Classify shot zones using ESPN coordinate transformer
3. Insert into `hoopr_schedule` and `hoopr_play_by_play` tables
4. Handle duplicates gracefully (ON CONFLICT DO UPDATE)

**Usage:**
```bash
# Load yesterday's data
python3 scripts/load_from_s3.py

# Load specific date
python3 scripts/load_from_s3.py --date 2024-12-02

# Dry run
python3 scripts/load_from_s3.py --dry-run

# Custom S3 bucket
python3 scripts/load_from_s3.py --bucket my-bucket-name
```

### 5. Cron Wrapper (`scripts/run_daily_sync.sh`)

**Purpose:** Orchestrates complete daily pipeline with error handling

**Workflow:**
1. Load secrets from hierarchical system
2. Run daily_data_sync.py (scrape → S3)
3. Run load_from_s3.py (S3 → database)
4. Log all output to timestamped log file
5. Send alerts on failure (TODO)

**Schedule:**
```bash
# Add to crontab (runs at 1:30 AM daily)
30 1 * * * /Users/ryanranft/nba-mcp-synthesis/scripts/run_daily_sync.sh
```

**Logs:**
```
logs/daily_sync_YYYYMMDD.log
```

## Configuration

### Environment Variables

**S3 Bucket:**
```bash
# Set in hierarchical secrets (optional, defaults to 'nba-mcp-synthesis-data')
export S3_BUCKET_NBA_MCP_SYNTHESIS=nba-mcp-synthesis-data
```

**AWS Credentials:**
```bash
# Load from ~/.aws/credentials or environment variables
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Database Credentials:**
Automatically loaded from hierarchical secrets system:
- `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW`

### S3 Bucket Setup

Create S3 bucket if not exists:
```bash
aws s3 mb s3://nba-mcp-synthesis-data --region us-east-1
```

Set lifecycle policy (optional - archive old data):
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket nba-mcp-synthesis-data \
  --lifecycle-configuration file://s3_lifecycle.json
```

## Testing

### Test Individual Components

**Test data fetcher:**
```bash
python3 -c "
from mcp_server.data_fetchers import HoopRFetcher
fetcher = HoopRFetcher()
games = fetcher.get_games_for_date('2024-12-02')
print(f'Found {len(games)} games')
"
```

**Test S3 upload:**
```bash
python3 scripts/daily_data_sync.py --date 2024-11-06 --dry-run
```

**Test S3 download + database load:**
```bash
python3 scripts/load_from_s3.py --date 2024-11-06 --dry-run
```

### Test Complete Pipeline

```bash
# Test scraping today's games (likely no completed games)
./scripts/run_daily_sync.sh

# Check logs
tail -f logs/daily_sync_$(date +%Y%m%d).log
```

## Shot Zone Classification

All shooting events are automatically classified during database insertion using the **ESPN coordinate transformer** (`mcp_server/spatial/zone_classifier.py`).

**Zones:**
- `restricted_area` - Within restricted area circle
- `paint_non_ra` - Paint but outside restricted area
- `mid_range_left`, `mid_range_center`, `mid_range_right` - 2-point mid-range
- `three_corner_left`, `three_corner_right` - Corner 3-pointers
- `three_above_break_left`, `three_above_break_center`, `three_above_break_right` - Above break 3s
- `backcourt` - Beyond half court

**Metadata:**
- `shot_distance` - Distance from basket (feet)
- `shot_angle` - Angle from basket center (-180 to 180 degrees)

## Monitoring

### Check Pipeline Status

```bash
# View recent logs
tail -100 logs/daily_sync_$(date +%Y%m%d).log

# Check S3 for recent uploads
aws s3 ls s3://nba-mcp-synthesis-data/daily/ --recursive | tail -10

# Query database for recent games
psql -c "SELECT game_id, date, COUNT(*) as events 
         FROM hoopr_play_by_play 
         GROUP BY game_id, date 
         ORDER BY date DESC 
         LIMIT 10"
```

### Verify Shot Classifications

```bash
python3 -c "
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
import psycopg2

load_secrets_hierarchical()
config = get_database_config()
conn = psycopg2.connect(**config)
cur = conn.cursor()

# Count classified vs unclassified shots
cur.execute('''
    SELECT 
        shot_zone IS NOT NULL as classified,
        COUNT(*) as count
    FROM hoopr_play_by_play
    WHERE shooting_play = 1
      AND coordinate_x IS NOT NULL
    GROUP BY classified
''')

for row in cur.fetchall():
    print(f'Classified: {row[0]}, Count: {row[1]:,}')

cur.close()
conn.close()
"
```

## Troubleshooting

### ESPN API Rate Limiting

If you encounter rate limiting errors:
1. Increase `rate_limit_delay` in `HoopRFetcher` (default: 1.0 second)
2. Split large date ranges into multiple smaller batches

### S3 Upload Failures

**Check AWS credentials:**
```bash
aws s3 ls s3://nba-mcp-synthesis-data/ --region us-east-1
```

**Verify bucket permissions:**
- Ensure your IAM user/role has `s3:PutObject` and `s3:GetObject` permissions

### Database Connection Errors

**Verify credentials:**
```bash
python3 scripts/test_database_credentials.py --context production
```

**Check network connectivity:**
```bash
pg_isready -h $RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW \
           -p $RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW
```

### No Games Found

If scraping returns 0 games:
- Verify the date has completed games (games finish late, typically sync runs at 1:30 AM)
- Check ESPN API is returning data for that date
- Try manually: `python3 scripts/daily_data_sync.py --date 2024-12-02`

## Maintenance

### Backfill Historical Data

If you need to re-scrape historical dates:

```bash
# Scrape specific date
python3 scripts/daily_data_sync.py --date 2024-11-01

# Load from S3 to database
python3 scripts/load_from_s3.py --date 2024-11-01
```

### Clean Up Old S3 Data

```bash
# Delete data older than 30 days (optional)
aws s3 rm s3://nba-mcp-synthesis-data/daily/ \
  --recursive \
  --exclude "*" \
  --include "$(date -d '30 days ago' +%Y-%m-)*"
```

### Update Schema

If database schema changes, update:
1. `scripts/load_from_s3.py` - INSERT statement
2. `sql/schema.sql` - Table definitions

## Next Steps

- [ ] Set up AWS Lambda for serverless execution
- [ ] Add email/SMS notifications on pipeline failures
- [ ] Implement incremental updates (only new events)
- [ ] Add data quality validation checks
- [ ] Create monitoring dashboard
- [ ] Backfill early 2001-02 season data (if available)

---

**Last Updated:** 2025-01-07  
**Pipeline Version:** 1.0  
**Shot Zone Backfill:** ✅ Complete (6.16M shots classified)
