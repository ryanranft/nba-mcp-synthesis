# NBA MCP Synthesis - Local Development Guide

**Last Updated:** 2025-01-07
**Author:** NBA MCP Synthesis Team

---

## Overview

This guide walks you through setting up a local PostgreSQL database for NBA MCP Synthesis development. The local database mirrors the production RDS structure and allows for:

- **Offline development** without RDS access
- **Faster iteration** with local data
- **Cost savings** by reducing RDS queries during development
- **Testing** schema changes before production deployment
- **CI/CD integration** with containerized databases

---

## Quick Start

### 1. Start PostgreSQL Container

```bash
cd /Users/ryanranft/nba-mcp-synthesis
docker-compose up -d postgres
```

This will:
- Pull PostgreSQL 16 Alpine image
- Create the `espn_nba_mcp_synthesis` database
- Run SQL initialization scripts from `sql/init/`
- Expose port 5432 on localhost

### 2. Verify Database Setup

```bash
python scripts/init_local_database.py --validate --stats
```

Expected output:
```
✅ All expected tables exist!
📊 Table Statistics:
   games                           0 rows
   hoopr_play_by_play              0 rows
   ...
```

### 3. Load Sample Data

```bash
# Load last 7 days of games (metadata only, fast)
python scripts/load_recent_games.py --days 7

# Load last 7 days with full play-by-play (slower)
python scripts/load_recent_games.py --days 7 --full
```

### 4. Use Local Database in Code

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config

# Load development credentials (points to localhost)
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'development')

# Get database config
db_config = get_database_config()

# Connect with psycopg2
import psycopg2
conn = psycopg2.connect(**db_config)
```

---

## Prerequisites

### Required Software

- **Docker** (for PostgreSQL container)
  - Install: https://www.docker.com/get-started
  - Verify: `docker --version`

- **Python 3.9+**
  - Verify: `python3 --version`

- **Python Packages**:
  ```bash
  pip install psycopg2-binary requests
  ```

### System Requirements

- **RAM**: 2GB minimum for PostgreSQL (4GB recommended)
- **Disk**: 10GB free space for database storage
- **Port 5432**: Must be available (not used by another PostgreSQL instance)

Check if port 5432 is available:
```bash
lsof -i :5432
```

If another PostgreSQL is running, stop it or change the port in `docker-compose.yml`.

---

## Database Architecture

### Container Setup

The local database runs in a Docker container with:

**Image**: `postgres:16-alpine`
**Database**: `espn_nba_mcp_synthesis`
**User**: `ryanranft`
**Password**: `nba_mcp_local_dev` (configurable via `POSTGRES_PASSWORD` env var)
**Port**: `5432` (mapped to host)

**Performance Tuning (96GB RAM system)**:
- `shared_buffers`: 2GB
- `effective_cache_size`: 6GB
- `maintenance_work_mem`: 512MB
- `work_mem`: 50MB
- `max_connections`: 100

### Volume Mounts

| Container Path | Host Path | Purpose |
|---------------|-----------|---------|
| `/var/lib/postgresql/data` | `postgres-data` volume | Database files (persistent) |
| `/docker-entrypoint-initdb.d` | `./sql/init/` | SQL initialization scripts (read-only) |
| `/backups` | `./backups/` | Database backups |

### Database Schema

The local database includes:

**Core Tables**:
- `games` - Game schedule and metadata
- `hoopr_play_by_play` - Play-by-play events (~6.16M rows for full dataset)
- `hoopr_player_box` - Player box scores from ESPN/hoopR
- `hoopr_team_box` - Team box scores from ESPN/hoopR

**Computed Tables** (100% accurate):
- `computed_player_box` - Player box scores from play-by-play
- `computed_team_box` - Team box scores from play-by-play

**Betting Tables**:
- `arbitrage_opportunities` - Cross-bookmaker arbitrage opportunities
- `betting_recommendations` - ML-based betting recommendations

See `docs/DATABASE_SCHEMA.md` for complete schema documentation.

---

## Secrets Management

### Hierarchical Structure

Credentials are stored using the **hierarchical secrets system**:

**Development Credentials Location**:
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/
```

**Files**:
- `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT.env` → `localhost`
- `RDS_PORT_NBA_MCP_SYNTHESIS_DEVELOPMENT.env` → `5432`
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT.env` → `espn_nba_mcp_synthesis`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT.env` → `ryanranft`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT.env` → `nba_mcp_local_dev`

### Using Credentials in Code

The `unified_secrets_manager` automatically loads credentials based on context:

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical

# Development (localhost)
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'development')

# Production (RDS)
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
```

**Backward Compatibility**: The system creates aliases for old naming conventions:
- `RDS_HOST` → `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT`
- `DB_HOST` → `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT`

---

## Common Tasks

### Start/Stop Database

```bash
# Start
docker-compose up -d postgres

# Stop
docker-compose stop postgres

# Restart
docker-compose restart postgres

# View logs
docker-compose logs -f postgres
```

### Check Database Status

```bash
# Quick health check
python scripts/init_local_database.py --validate

# Full statistics
python scripts/init_local_database.py --stats

# View container status
docker-compose ps
```

### Reset Database

**⚠️ WARNING**: This deletes ALL data!

```bash
python scripts/init_local_database.py --reset
```

This will:
1. Drop all tables
2. Re-run SQL init scripts from `sql/init/`
3. Create fresh empty tables

### Load Data

**Option 1: Recent Games (Recommended for Development)**

```bash
# Load last 7 days (games only, ~1 minute)
python scripts/load_recent_games.py --days 7

# Load last 30 days with play-by-play (~10 minutes)
python scripts/load_recent_games.py --days 30 --full
```

**Option 2: Specific Date**

```bash
# Load games from a specific date
python scripts/load_recent_games.py --date 2024-01-15 --full
```

**Option 3: Dump from Production RDS** (optional)

```bash
# Export from RDS (requires AWS credentials)
pg_dump -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
        -U ryanranft \
        -d espn_nba_mcp_synthesis \
        --schema-only \
        > backups/schema_dump.sql

# Export recent data (last 30 days)
pg_dump -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
        -U ryanranft \
        -d espn_nba_mcp_synthesis \
        --data-only \
        --table=games \
        --table=hoopr_play_by_play \
        --where="game_date >= CURRENT_DATE - INTERVAL '30 days'" \
        > backups/data_dump.sql

# Import to local
psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis < backups/data_dump.sql
```

### Backup/Restore

```bash
# Backup local database
pg_dump -h localhost -U ryanranft -d espn_nba_mcp_synthesis > backups/local_backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis < backups/local_backup_20250107.sql
```

---

## Development Workflows

### Workflow 1: Schema Development

When adding new tables or columns:

1. Create migration SQL in `sql/migrations/`
2. Test locally:
   ```bash
   psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -f sql/migrations/003_add_new_feature.sql
   ```
3. Verify:
   ```bash
   python scripts/init_local_database.py --validate
   ```
4. Update `sql/init/` scripts for fresh installations
5. Test clean installation:
   ```bash
   python scripts/init_local_database.py --reset
   python scripts/load_recent_games.py --days 1 --full
   ```

### Workflow 2: Feature Development

When developing new features that query the database:

1. Start with local database:
   ```python
   load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'development')
   ```
2. Develop and test locally (fast iteration)
3. When ready, test against production (read-only):
   ```python
   load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
   ```

### Workflow 3: Testing

```bash
# Run integration tests against local database
pytest tests/integration/ --context=development

# Run with fresh data
python scripts/load_recent_games.py --days 1 --full
pytest tests/integration/test_box_score_computation.py
```

---

## Troubleshooting

### Port 5432 Already in Use

**Problem**: Another PostgreSQL instance is using port 5432.

**Solution 1** - Stop other instance:
```bash
# Find process
lsof -i :5432

# Stop system PostgreSQL (macOS)
brew services stop postgresql

# Or kill process
kill -9 <PID>
```

**Solution 2** - Change port in `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Map to different host port
```

Then update development secrets:
```bash
echo "5433" > "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/RDS_PORT_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
```

### Container Won't Start

**Problem**: `docker-compose up -d postgres` fails.

**Check logs**:
```bash
docker-compose logs postgres
```

**Common issues**:
- Insufficient disk space: `df -h`
- Permission issues: `sudo chmod 755 sql/init/`
- Syntax errors in SQL scripts: Check logs for line numbers

### Database Connection Refused

**Problem**: `psycopg2.OperationalError: could not connect to server`.

**Solutions**:
1. Ensure container is running:
   ```bash
   docker-compose ps
   ```

2. Check health:
   ```bash
   docker-compose exec postgres pg_isready -U ryanranft
   ```

3. Verify credentials:
   ```bash
   python -c "from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config; load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'development'); print(get_database_config())"
   ```

### Tables Not Created

**Problem**: Database starts but tables are missing.

**Solution**:
```bash
# Check if SQL files exist
ls -la sql/init/

# Check initialization logs
docker-compose logs postgres | grep "init"

# Manually run init scripts
for sql in sql/init/*.sql; do
    psql -h localhost -U ryanranft -d espn_nba_mcp_synthesis -f "$sql"
done
```

### Slow Query Performance

**Problem**: Queries are slower than expected.

**Solutions**:
1. Check if indexes exist:
   ```sql
   SELECT tablename, indexname
   FROM pg_indexes
   WHERE schemaname = 'public'
   ORDER BY tablename, indexname;
   ```

2. Analyze tables:
   ```sql
   ANALYZE games;
   ANALYZE hoopr_play_by_play;
   ```

3. Check table sizes:
   ```sql
   SELECT schemaname, tablename,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

---

## Performance Optimization

### Tuning for Larger Datasets

If loading full historical data (2002-2024, ~6.16M shots):

**Increase PostgreSQL resources** in `docker-compose.yml`:
```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 4GB  # 25% of RAM
  POSTGRES_EFFECTIVE_CACHE_SIZE: 12GB  # 50-75% of RAM
  POSTGRES_MAINTENANCE_WORK_MEM: 1GB
```

**Disable auto-indexing during bulk load**:
```sql
-- Before load
DROP INDEX idx_pbp_game;
DROP INDEX idx_pbp_shot_zone;

-- Bulk insert data...

-- After load, recreate indexes
CREATE INDEX idx_pbp_game ON hoopr_play_by_play(game_id);
CREATE INDEX idx_pbp_shot_zone ON hoopr_play_by_play(shot_zone)
WHERE shooting_play = 1 AND shot_zone IS NOT NULL;
```

---

## Differences from Production

| Aspect | Production (RDS) | Local (Docker) |
|--------|-----------------|----------------|
| **Data Size** | Full history (2002-2024) | Recent games only |
| **Performance** | Tuned for production | Tuned for development |
| **Backups** | Automated daily | Manual |
| **High Availability** | Multi-AZ | Single container |
| **Security** | VPC, IAM, encryption | Local only |
| **Cost** | $50-100/month | Free |

---

## Next Steps

After setting up your local database:

1. **Read Database Schema**: `docs/DATABASE_SCHEMA.md`
2. **Explore Example Queries**: Each SQL init file has example queries
3. **Run Integration Tests**: `pytest tests/integration/`
4. **Build a Feature**: Use local DB for fast iteration
5. **Contribute**: Submit PRs with schema improvements

---

## Additional Resources

- **Hierarchical Secrets**: `/Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md`
- **Box Score Methodology**: `docs/BOX_SCORE_METHODOLOGY.md`
- **Shot Zone Classification**: `docs/SHOT_ZONE_INDEXING.md`
- **Play-by-Play Schema**: `docs/PLAY_BY_PLAY_EVENT_SCHEMA.md`
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/16/

---

**Questions or Issues?**
Open an issue at: https://github.com/anthropics/claude-code/issues

---

*Last Updated: 2025-01-07*
