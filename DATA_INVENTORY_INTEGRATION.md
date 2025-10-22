# Data Inventory Integration Guide

## Overview

The book analysis system now integrates with the **Data Inventory Management System (DIMS)** from nba-simulator-aws to provide AI models with comprehensive awareness of available data assets when generating recommendations.

## What This Enables

When analyzing technical books, AI models can now:

1. **Reference Actual Data Tables**: Instead of generic "collect player data", recommendations can specify "Query master_player_game_stats table for plus_minus statistics"

2. **Leverage Existing Systems**: Build on the 2,103 lines of prediction system code and 4,619 lines of plus/minus calculation system

3. **Use Real Data Coverage**: Reference the 172,726 S3 objects of play-by-play data spanning 2014-2025

4. **Avoid Duplication**: Check if features are already implemented before recommending them

## System Architecture

### Components

#### 1. Data Inventory Scanner (`scripts/data_inventory_scanner.py`)

Scans the DIMS inventory system and extracts:

- **Metrics** from `inventory/metrics.yaml`
  - S3 storage statistics (objects, size, coverage)
  - Code metrics (prediction system, plus/minus system)
  - Documentation metrics

- **Schema** from `sql/master_schema.sql`
  - Table structures and column definitions
  - Primary keys and relationships
  - 7 core tables: master_players, master_teams, master_games, master_player_game_stats, etc.

- **System Capabilities**
  - Prediction system (game outcome, player performance models)
  - Plus/Minus calculation system
  - Data pipeline status

#### 2. Project Code Analyzer Integration

The `EnhancedProjectScanner` now calls `_scan_data_inventory()` which:

1. Checks if data inventory is enabled in project config
2. Verifies the inventory path exists
3. Instantiates `DataInventoryScanner`
4. Scans the full inventory
5. Includes results in project context sent to AI models

#### 3. AI Prompt Enhancement

The data inventory summary is automatically included in prompts sent to:

- **Gemini 1.5 Pro** (`synthesis/models/google_model_v2.py`)
- **Claude Sonnet 4** (`synthesis/models/claude_model_v2.py`)

Both receive a structured summary like:

```
## 📊 DATA INVENTORY SUMMARY

**Database Schema**:
- 7 core tables
- Panel Data: master_player_game_stats (game-level player performance)
- Dimensions: master_players, master_teams, master_games

**Data Coverage**:
- 172,726 objects in S3 (118.26 GB)
- Seasons: 2014-2025
- Estimated 15000+ games, 5000+ players

**Available Systems**:
- ✅ Game Prediction System (2,103 lines of code)
- ✅ Plus/Minus Calculation System (4,619 lines of code)
- ✅ PostgreSQL panel data backend
- ✅ S3 data lake with play-by-play events

**IMPORTANT FOR RECOMMENDATIONS**:
When recommending features from the book, leverage these existing data assets:
1. Use master_player_game_stats for player performance analysis
2. Reference the 172k S3 objects of play-by-play data for sequence modeling
3. Build on the existing prediction system (2,103 lines)
4. Integrate with the plus/minus calculation system
5. Query PostgreSQL for historical panel data analysis
```

## Configuration

### Enable Data Inventory in Project Config

Edit `project_configs/nba_mcp_synthesis.json`:

```json
{
  "data_inventory": {
    "enabled": true,
    "inventory_path": "/Users/ryanranft/nba-simulator-aws/inventory",
    "description": "Data Inventory Management System (DIMS) for NBA panel data",
    "database": {
      "type": "PostgreSQL",
      "schema": "public",
      "key_tables": [
        "master_players",
        "master_teams",
        "master_games",
        "master_player_game_stats"
      ]
    },
    "data_coverage": {
      "s3_objects": 172726,
      "s3_size_gb": 118.26,
      "seasons": "2014-2025",
      "games_estimated": "15000+",
      "players_estimated": "5000+"
    },
    "systems": [
      "prediction_system",
      "plus_minus_system",
      "game_simulation",
      "mcp_server"
    ]
  }
}
```

### Disable Data Inventory (Optional)

Set `"enabled": false` in the config:

```json
{
  "data_inventory": {
    "enabled": false
  }
}
```

## Usage

### Test Data Inventory Scanner Standalone

```bash
python scripts/data_inventory_scanner.py /Users/ryanranft/nba-simulator-aws/inventory
```

Output:
- Console: AI-formatted summary
- File: `data_inventory_report.json` with full details

### Test Project Scanner with Data Inventory

```bash
python scripts/project_code_analyzer.py \
  --config project_configs/nba_mcp_synthesis.json
```

Verify output includes:
- `📊 Scanning data inventory` in logs
- Data inventory summary at end of formatted output

### Run Book Analysis with Data Inventory

```bash
python scripts/recursive_book_analysis.py \
  --book "Machine Learning for Engineers" \
  --high-context \
  --project project_configs/nba_mcp_synthesis.json \
  --local-books
```

The AI models will now receive project context + data inventory awareness.

## Example: Before vs After

### Before Data Inventory Integration

**Generic Recommendation:**
> "Implement a player performance prediction model using historical statistics"

**Issues:**
- Doesn't know what data is available
- Might recommend collecting data that already exists
- No guidance on which tables/columns to use

### After Data Inventory Integration

**Data-Aware Recommendation:**
> "Build a gradient boosting model for player performance prediction using the master_player_game_stats table. Leverage the existing 172k play-by-play events in S3 for feature engineering. The table includes points, rebounds, assists, and plus_minus columns covering 2014-2025 seasons. Integrate with the existing prediction system (2,103 lines in scripts/ml/) to avoid duplication."

**Benefits:**
- Specific table and column references
- Aware of existing systems to build on
- Knows data coverage and constraints
- Actionable and implementable

## Data Inventory Report Schema

The scanner generates comprehensive reports with this structure:

```json
{
  "metadata": {
    "system": "DIMS",
    "version": "1.0.0",
    "backend": "PostgreSQL"
  },
  "metrics": {
    "s3_storage": {
      "total_objects": { "value": 172726 },
      "total_size_gb": { "value": 118.26 }
    },
    "prediction_system": {
      "total_lines": { "value": 2103 },
      "scripts": { ... }
    },
    "plus_minus_system": {
      "total_lines": { "value": 4619 }
    }
  },
  "schema": {
    "tables": {
      "master_player_game_stats": {
        "type": "fact",
        "columns": [...],
        "key_metrics": ["points", "rebounds", "assists", "plus_minus"]
      }
    }
  },
  "data_coverage": {
    "s3_objects": 172726,
    "seasons_estimated": "2014-2025"
  },
  "available_features": [...],
  "system_capabilities": {...},
  "summary_for_ai": "..."
}
```

## Multi-Sport Support

For future sports (NFL, MLB), create similar inventory structures:

### NFL Example Configuration

```json
{
  "data_inventory": {
    "enabled": true,
    "inventory_path": "/path/to/nfl-simulator-aws/inventory",
    "database": {
      "key_tables": [
        "master_teams",
        "master_games",
        "master_player_stats",
        "master_play_by_play"
      ]
    }
  }
}
```

### MLB Example Configuration

```json
{
  "data_inventory": {
    "enabled": true,
    "inventory_path": "/path/to/mlb-simulator-aws/inventory",
    "database": {
      "key_tables": [
        "master_teams",
        "master_games",
        "master_batting_stats",
        "master_pitching_stats"
      ]
    }
  }
}
```

## Maintenance

### Updating Inventory Metrics

The inventory scanner reads live data from:

- `inventory/metrics.yaml` - Updated by DIMS
- `sql/master_schema.sql` - Updated when schema changes

No code changes needed when data changes. Just re-run the analysis.

### Adding New Tables

When new tables are added to the schema:

1. Update `sql/master_schema.sql` with new CREATE TABLE statement
2. Scanner will automatically detect new table
3. Add table metadata to scanner's `_extract_tables_from_sql()` if needed

## Troubleshooting

### Import Error: DataInventoryScanner not available

**Issue:** Import path problem when running from different directories

**Solution:** The code now handles both module and direct execution:

```python
try:
    from scripts.data_inventory_scanner import DataInventoryScanner
except ImportError:
    # Fallback to local import
    from data_inventory_scanner import DataInventoryScanner
```

### No Data Inventory Summary in Output

**Check:**
1. Is `"enabled": true` in config?
2. Does `inventory_path` exist?
3. Check logs for "📊 Scanning data inventory"

### Incomplete Schema Detection

**Issue:** Some tables not detected from SQL

**Solution:** Add table metadata explicitly in `_extract_tables_from_sql()`:

```python
table_metadata = {
    'new_table_name': {
        'type': 'fact',
        'description': 'Description here',
        'primary_key': 'id_column',
    }
}
```

## Performance Considerations

- **Scan Time**: ~1-2 seconds for full inventory
- **Memory**: Minimal (loads YAML/SQL into memory)
- **Cache**: No caching currently (always fresh data)
- **Token Impact**: Adds ~500-800 tokens to AI prompts

## Future Enhancements

1. **Database Query Integration**: Query live PostgreSQL for row counts
2. **Cache Layer**: Cache inventory scans for X minutes
3. **Differential Updates**: Track what changed since last scan
4. **Data Quality Metrics**: Include data completeness, freshness scores
5. **Visual Dashboards**: Generate HTML reports from inventory

## References

- **DIMS Documentation**: See nba-simulator-aws/inventory/
- **Project Scanner**: `scripts/project_code_analyzer.py`
- **Inventory Scanner**: `scripts/data_inventory_scanner.py`
- **Example Config**: `project_configs/nba_mcp_synthesis.json`
