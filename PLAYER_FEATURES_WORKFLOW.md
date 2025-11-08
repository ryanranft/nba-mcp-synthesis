# Player Features - Complete Workflow Guide

**Last Updated:** 2025-01-05 23:55 PST
**Status:** Phase 1B Complete | Phase 1C In Progress

---

## Quick Start

### Check Current Status
```bash
./scripts/quick_status.sh
```

### Monitor Batch Progress
```bash
./scripts/check_batch_progress.sh
```

### Full Log
```bash
tail -f logs/batch_feature_generation.log
```

---

## Complete Workflow

### Phase 1A: Infrastructure Setup ✅ COMPLETE

**Objective:** Build player feature extraction infrastructure

**Steps:**
1. Created `mcp_server/betting/feature_extractors/player_features.py`
2. Created `mcp_server/betting/feature_extractors/roster_metrics.py`
3. Integrated with `mcp_server/betting/feature_extractor.py`
4. Created test script `scripts/test_player_features.py`

**Test:**
```bash
python scripts/test_player_features.py
```

**Expected Output:**
```
✅ Found 29 player features
Total features: 130
```

---

### Phase 1B: Value Calibration ✅ COMPLETE

**Objective:** Fix player stat calculations

**Issue Fixed:**
- Player PPG was using `team_score` (team total) instead of individual points
- Solution: Calculate as `FGM*2 + 3PM*3 + FTM`

**Changes:**
- Modified 3 SQL queries in `player_features.py` (lines 147, 244, 397)

**Validation:**
```bash
python scripts/test_player_features.py
```

**Expected:**
```
player__home_top1_ppg_l10: 25-40 PPG ✅
player__home_top2_ppg_l10: 15-30 PPG ✅
player__away_bench_ppg: 15-25 PPG ✅
```

---

### Phase 1C: Batch Integration 🔄 IN PROGRESS

**Objective:** Generate historical features for model training

#### Part 1: Update Batch Pipeline ✅ COMPLETE

**Changes Made:**
```python
# scripts/prepare_game_features_complete.py

# Old (custom extraction):
features = extract_features_for_game(game, all_games, all_team_stats, rest_extractor)

# New (unified extractor):
features = feature_extractor.extract_game_features(home_team_id, away_team_id, game_date)
```

**Result:** Batch and live predictions now use identical feature extraction

#### Part 2: Run Batch Generation 🔄 RUNNING

**Command:**
```bash
nohup python3 scripts/prepare_game_features_complete.py \
    --seasons 2021-22 2022-23 2023-24 2024-25 \
    --output data/game_features_with_players.csv \
    --min-games 10 \
    > logs/batch_feature_generation.log 2>&1 &
```

**Status:**
- Started: 2025-01-05 23:52 PST
- Progress: ~92/4621 games (2%)
- ETA: ~7.5 hours (2025-01-06 ~7:30 AM PST)

**Monitor:**
```bash
./scripts/check_batch_progress.sh
```

#### Part 3: Validate Output ⏸️ PENDING

**When batch completes, run:**
```bash
python scripts/validate_batch_output.py
```

**Expected:**
```
✅ VALIDATION PASSED
- 4,621 games
- 130 features (including 29 player features)
- 4 seasons
```

---

### Phase 1D: Model Retraining ⏸️ PENDING

**Objective:** Train ensemble with player features

#### Automated Retraining

**Run complete pipeline:**
```bash
./scripts/retrain_with_player_features.sh
```

**What it does:**
1. Validates batch output
2. Backs up current model
3. Trains new model with 130 features
4. Compares performance
5. Provides deployment instructions

#### Manual Retraining

**Step 1: Validate**
```bash
python scripts/validate_batch_output.py --file data/game_features_with_players.csv
```

**Step 2: Backup Current**
```bash
cp models/game_outcome_ensemble.pkl models/game_outcome_ensemble_v1_101features.pkl
```

**Step 3: Train**
```bash
python scripts/train_game_outcome_model.py \
    --input data/game_features_with_players.csv \
    --output models/ensemble_with_players.pkl \
    --test-season 2024-25 \
    --verbose
```

**Expected Improvements:**
- Accuracy: 67.5% → 69-71% (+2-5%)
- Brier Score: 0.210 → 0.195-0.200
- Log Loss: 0.590 → 0.560-0.575

**Step 4: Compare**
```bash
# Review training output for metrics comparison
# Check test set performance on 2024-25 season
```

---

### Phase 1E: Deployment ⏸️ PENDING

**Objective:** Deploy new model if successful

#### Deployment Criteria

Deploy if:
- ✅ Accuracy improves by >2%
- ✅ Brier score decreases
- ✅ Log loss decreases
- ✅ No errors in validation

#### Deploy New Model

```bash
# Deploy
cp models/ensemble_with_players.pkl models/game_outcome_ensemble.pkl

# Test live predictions
python scripts/paper_trade_today.py --dry-run
```

**Expected output:**
```
✅ Using enhanced model with 130 features
✅ Found 10 games for today
✅ Predictions generated successfully
```

#### Rollback (if needed)

```bash
cp models/game_outcome_ensemble_v1_101features.pkl models/game_outcome_ensemble.pkl
```

---

### Phase 1F: Backtesting ⏸️ PENDING

**Objective:** Validate improvement on historical holdout

```bash
python scripts/backtest_historical_games.py \
    --model models/game_outcome_ensemble.pkl \
    --features data/game_features_with_players.csv \
    --seasons 2023-24 \
    --kelly-mode conservative \
    --min-edge 0.05
```

**Expected:**
- ROI improvement: +2-5%
- More selective betting (higher average edge)
- Better calibration (predicted probabilities closer to reality)

---

## Feature Breakdown

### Total Features: 130

#### Team-Level Features (101)
- Rolling stats (L5, L10, L20): 76 features
- Rest & fatigue: 14 features
- Head-to-head: 5 features
- Season progress: 2 features
- Location splits: 4 features

#### Player-Level Features (29) ✨ NEW
```
Top Scorers (18 features):
  player__home_top1_ppg_l10          # Leading scorer PPG (last 10)
  player__home_top1_minutes_l10      # Minutes per game
  player__home_top1_usage_pct_l10    # Usage rate %
  ... (same for top2, top3, and away team)

Roster Quality (4 features):
  player__home_roster_per_sum        # Sum of PER for top 5
  player__away_roster_per_sum
  player__home_bench_ppg             # Bench strength (6th-10th scorers)
  player__away_bench_ppg

Injury & Availability (4 features):
  player__home_injury_impact         # PPG lost from injuries
  player__away_injury_impact
  player__home_stars_available       # % of top 3 scorers available
  player__away_stars_available

Matchup Advantages (3 features):
  player__top5_ppg_advantage         # Home vs away firepower
  player__home_top5_ppg              # Top 5 scorer total
  player__away_top5_ppg
```

---

## Troubleshooting

### Batch Generation Stuck

**Check if running:**
```bash
ps aux | grep prepare_game_features_complete.py
```

**View recent log:**
```bash
tail -50 logs/batch_feature_generation.log
```

**Restart if needed:**
```bash
# Kill existing process
pkill -f prepare_game_features_complete.py

# Restart
nohup python3 scripts/prepare_game_features_complete.py \
    --seasons 2021-22 2022-23 2023-24 2024-25 \
    --output data/game_features_with_players.csv \
    --min-games 10 \
    > logs/batch_feature_generation.log 2>&1 &
```

### Validation Fails

**Check output file:**
```bash
ls -lh data/game_features_with_players.csv
head -1 data/game_features_with_players.csv | tr ',' '\n' | wc -l  # Should be ~138
head -1 data/game_features_with_players.csv | tr ',' '\n' | grep 'player__' | wc -l  # Should be 29
```

**Re-run validation:**
```bash
python scripts/validate_batch_output.py --file data/game_features_with_players.csv
```

### Model Training Fails

**Check input file:**
```bash
python scripts/validate_batch_output.py
```

**Check for null values:**
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/game_features_with_players.csv')
print(f'Total rows: {len(df)}')
print(f'Null counts:\\n{df.isnull().sum()[df.isnull().sum() > 0]}')
"
```

**Manual training with debug:**
```bash
python scripts/train_game_outcome_model.py \
    --input data/game_features_with_players.csv \
    --output models/ensemble_with_players.pkl \
    --test-season 2024-25 \
    --verbose 2>&1 | tee logs/training.log
```

### Live Predictions Fail

**Test feature extraction:**
```bash
python scripts/test_player_features.py
```

**Check model file:**
```bash
ls -lh models/game_outcome_ensemble.pkl
```

**Dry run:**
```bash
python scripts/paper_trade_today.py --dry-run
```

---

## Performance Characteristics

### Feature Extraction Speed
- Live prediction: ~5.5 seconds per game
- Batch processing: ~6 seconds per game
- Full batch (4,621 games): ~7-8 hours

### Why So Slow?
Player queries are complex:
- Multiple CTEs (Common Table Expressions)
- Window functions (ROW_NUMBER, partitioning)
- Aggregations over recent games (last 10, top 5 players)
- Multiple joins (hoopr_player_box + games)

### Optimization Options (if needed)
1. **Materialized views** for player stats
2. **Caching** frequently-accessed player data
3. **Parallel processing** (batch in chunks)
4. **Database indexing** on athlete_id, team_id, game_date

---

## Expected Impact

### Moneyline Predictions
- **Current:** 67.5% accuracy (101 features)
- **Expected:** 69-71% accuracy (130 features)
- **Improvement:** +2-5%

### Why Player Features Help
1. **Injuries:** Detect when star players are out
2. **Matchups:** Elite scorers vs weak defenses
3. **Depth:** Bench strength in blowouts
4. **Usage:** Who's carrying the offensive load
5. **Form:** Individual player recent performance

### Future Capabilities Enabled
- **Phase 2:** Point spreads & totals (same features, different targets)
- **Phase 3:** Player props (individual player models)

---

## File Reference

### Core Files
```
mcp_server/betting/feature_extractors/player_features.py    (500 lines)
mcp_server/betting/feature_extractors/roster_metrics.py     (400 lines)
mcp_server/betting/feature_extractor.py                     (modified)
```

### Scripts
```
scripts/prepare_game_features_complete.py      (batch pipeline)
scripts/test_player_features.py                (validation)
scripts/validate_batch_output.py               (batch validator)
scripts/retrain_with_player_features.sh        (retraining pipeline)
scripts/check_batch_progress.sh                (progress monitor)
scripts/quick_status.sh                        (status overview)
```

### Documentation
```
PLAYER_FEATURES_PHASE1_PROGRESS.md    (technical progress)
PHASE1_COMPLETION_SUMMARY.md          (completion summary)
PLAYER_FEATURES_WORKFLOW.md           (THIS FILE - workflow guide)
```

### Logs
```
logs/batch_feature_generation.log     (batch processing log)
```

### Data Files
```
data/game_features_with_players.csv   (output: 4,621 games x 138 columns)
```

### Models
```
models/game_outcome_ensemble.pkl                  (current production)
models/game_outcome_ensemble_v1_101features.pkl   (backup)
models/ensemble_with_players.pkl                  (new enhanced model)
```

---

## Timeline

**Completed:**
- Phase 1A: Infrastructure (2 days) ✅
- Phase 1B: Calibration (1 day) ✅
- Phase 1C Part 1: Pipeline update (0.5 days) ✅

**In Progress:**
- Phase 1C Part 2: Batch generation (~7.5 hours) 🔄

**Remaining:**
- Phase 1C Part 3: Validation (0.25 days)
- Phase 1D: Model retraining (0.5 days)
- Phase 1E: Deployment (0.25 days)
- Phase 1F: Backtesting (0.5 days)

**Total Phase 1:** 5-6 days (on schedule)

---

## Support Commands

### Status Check
```bash
./scripts/quick_status.sh
```

### Progress Monitor
```bash
./scripts/check_batch_progress.sh
```

### Full Retraining
```bash
./scripts/retrain_with_player_features.sh
```

### Validation
```bash
python scripts/validate_batch_output.py
python scripts/test_player_features.py
```

### Live Test
```bash
python scripts/paper_trade_today.py --dry-run
```

---

**Current Status:** Batch generation running (~2% complete, ETA: ~7.5 hours)

**Next Milestone:** Batch completion → validation → retraining

**Production Ready:** 2025-01-06 Evening PST (estimated)
