# Player Features - Documentation Index

**Quick Links:**
- [Quick Status Check](#quick-status-check)
- [Complete Workflow Guide](#workflow-guide)
- [Technical Details](#technical-details)
- [Helper Scripts](#helper-scripts)

---

## Quick Status Check

```bash
./scripts/quick_status.sh
```

Shows at-a-glance status of:
- Batch generation progress
- Infrastructure files
- Model status
- Next steps

---

## Documentation Files

### 📘 [PLAYER_FEATURES_WORKFLOW.md](PLAYER_FEATURES_WORKFLOW.md)
**→ START HERE for step-by-step workflow**

Complete operational guide covering:
- Phase-by-phase execution steps
- Command examples for each phase
- Troubleshooting common issues
- Performance characteristics
- File reference guide

**Use when:** Running the workflow, deploying, or debugging issues

---

### 📊 [PHASE1_COMPLETION_SUMMARY.md](PHASE1_COMPLETION_SUMMARY.md)
**→ High-level progress summary**

Executive summary covering:
- What was accomplished (Phase 1A, 1B, 1C)
- Feature comparison (101 vs 130 features)
- Current batch status
- Expected impact (+2-5% accuracy)
- Next steps and timeline

**Use when:** Checking overall progress or explaining to stakeholders

---

### 🔧 [PLAYER_FEATURES_PHASE1_PROGRESS.md](PLAYER_FEATURES_PHASE1_PROGRESS.md)
**→ Detailed technical progress**

Deep technical details covering:
- File-by-file descriptions
- Database schema used
- Known issues and resolutions
- Feature extraction algorithms
- Validation test results

**Use when:** Debugging, understanding implementation details, or technical review

---

## Helper Scripts

### Status & Monitoring

#### `./scripts/quick_status.sh`
**Purpose:** One-command status overview
```bash
./scripts/quick_status.sh
```
**Shows:**
- Batch progress (% complete, ETA)
- Infrastructure status (✅ or ❌)
- Model status
- Next steps

---

#### `./scripts/check_batch_progress.sh`
**Purpose:** Detailed batch generation progress
```bash
./scripts/check_batch_progress.sh
```
**Shows:**
- Is batch running?
- Games processed (X / 4,621)
- Estimated time remaining
- Latest log entries

---

### Validation & Testing

#### `scripts/test_player_features.py`
**Purpose:** Validate live feature extraction
```bash
python scripts/test_player_features.py
```
**Checks:**
- 130 total features extracted ✅
- 29 player features present ✅
- PPG values realistic (10-40 range) ✅
- No missing critical features ✅

---

#### `scripts/validate_batch_output.py`
**Purpose:** Validate batch-generated dataset
```bash
python scripts/validate_batch_output.py
```
**Checks:**
- File exists and loadable ✅
- 4,621 games from 4 seasons ✅
- 130 features (including 29 player) ✅
- No excessive null values ✅
- Realistic value ranges ✅

---

### Training & Deployment

#### `./scripts/retrain_with_player_features.sh`
**Purpose:** Complete automated retraining pipeline
```bash
./scripts/retrain_with_player_features.sh
```
**Does:**
1. Validates batch output
2. Backs up current model
3. Trains new model (130 features)
4. Compares performance
5. Provides deployment instructions

**When to use:** After batch generation completes

---

## Workflow Quick Reference

### Current Status (2025-01-05 23:55 PST)

```
Phase 1A: Infrastructure     ✅ COMPLETE
Phase 1B: Calibration        ✅ COMPLETE
Phase 1C: Batch Integration  🔄 IN PROGRESS (2% complete, ~7.5 hrs remaining)
Phase 1D: Model Retraining   ⏸️  PENDING
Phase 1E: Deployment         ⏸️  PENDING
Phase 1F: Backtesting        ⏸️  PENDING
```

### Next Actions

**Now (batch running):**
```bash
# Monitor progress
./scripts/check_batch_progress.sh

# Or watch live log
tail -f logs/batch_feature_generation.log
```

**When batch completes (~7.5 hours):**
```bash
# 1. Validate output
python scripts/validate_batch_output.py

# 2. Retrain model (automated)
./scripts/retrain_with_player_features.sh

# 3. If accuracy improves >2%, deploy
cp models/ensemble_with_players.pkl models/game_outcome_ensemble.pkl

# 4. Test live predictions
python scripts/paper_trade_today.py --dry-run
```

---

## Feature Overview

### Before: 101 Features (Team-Level Only)
- Rolling stats (L5, L10, L20)
- Rest & fatigue
- Head-to-head history
- Season progress

### After: 130 Features (+29 Player-Level)
**All previous 101 features PLUS:**
- Top scorer stats (PPG, minutes, usage rate)
- Roster strength (PER for top 5 players)
- Bench depth (6th-10th scorer production)
- Star availability (injury impact)
- Matchup advantages (offensive firepower)

---

## File Locations

### Core Infrastructure
```
mcp_server/betting/feature_extractors/
  ├── player_features.py       # Player feature extractor (500 lines)
  └── roster_metrics.py         # Advanced roster metrics (400 lines)

mcp_server/betting/
  └── feature_extractor.py      # Main extractor (integrated with player features)
```

### Scripts
```
scripts/
  ├── test_player_features.py              # Live validation
  ├── validate_batch_output.py             # Batch validation
  ├── retrain_with_player_features.sh      # Automated retraining
  ├── check_batch_progress.sh              # Progress monitor
  └── quick_status.sh                      # Status overview
```

### Data & Models
```
data/
  └── game_features_with_players.csv       # Batch output (4,621 games x 138 columns)

models/
  ├── game_outcome_ensemble.pkl            # Current production model
  ├── game_outcome_ensemble_v1_101features.pkl  # Backup (101 features)
  └── ensemble_with_players.pkl            # New model (130 features)
```

### Logs
```
logs/
  └── batch_feature_generation.log         # Batch processing log
```

---

## Expected Performance Improvement

### Moneyline Accuracy
- **Before:** 67.5% (101 features)
- **After:** 69-71% (130 features)
- **Improvement:** +2-5%

### Why?
Player features capture:
1. **Injuries** - Star players missing
2. **Matchups** - Elite scorers vs weak defenses
3. **Depth** - Bench strength
4. **Form** - Recent individual performance
5. **Usage** - Who's carrying offensive load

---

## Troubleshooting

### Batch Stuck?
```bash
# Check if running
ps aux | grep prepare_game_features_complete.py

# View recent progress
tail -50 logs/batch_feature_generation.log

# Restart if needed
pkill -f prepare_game_features_complete.py
nohup python3 scripts/prepare_game_features_complete.py \
    --seasons 2021-22 2022-23 2023-24 2024-25 \
    --output data/game_features_with_players.csv \
    --min-games 10 \
    > logs/batch_feature_generation.log 2>&1 &
```

### Validation Fails?
```bash
# Check file exists
ls -lh data/game_features_with_players.csv

# Count columns (should be 138)
head -1 data/game_features_with_players.csv | tr ',' '\n' | wc -l

# Count player features (should be 29)
head -1 data/game_features_with_players.csv | tr ',' '\n' | grep 'player__' | wc -l
```

### Live Predictions Fail?
```bash
# Test feature extraction
python scripts/test_player_features.py

# Dry run predictions
python scripts/paper_trade_today.py --dry-run
```

---

## Timeline

**Started:** 2025-01-03
**Phase 1A Complete:** 2025-01-04
**Phase 1B Complete:** 2025-01-05
**Batch Started:** 2025-01-05 23:52 PST
**Batch ETA:** 2025-01-06 ~7:30 AM PST
**Production Ready:** 2025-01-06 Evening PST (estimated)

**Total Duration:** 5-6 days (on schedule)

---

## Support

**For operational questions:** See [PLAYER_FEATURES_WORKFLOW.md](PLAYER_FEATURES_WORKFLOW.md)

**For technical details:** See [PLAYER_FEATURES_PHASE1_PROGRESS.md](PLAYER_FEATURES_PHASE1_PROGRESS.md)

**For progress summary:** See [PHASE1_COMPLETION_SUMMARY.md](PHASE1_COMPLETION_SUMMARY.md)

**Quick status:** `./scripts/quick_status.sh`

---

**Last Updated:** 2025-01-05 23:55 PST
