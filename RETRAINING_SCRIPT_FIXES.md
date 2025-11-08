# Retraining Script Fixes - 2025-01-06

## Issues Found & Fixed

### Critical Issues Fixed in `scripts/retrain_with_player_features.sh`

#### 1. ❌ Argument Mismatch: `--input` vs `--features`
**Problem:** Script used `--input` flag but training script expects `--features`
```bash
# BEFORE (broken):
python3 scripts/train_game_outcome_model.py \
    --input "$FEATURES_FILE" \
    --output "$MODEL_OUTPUT"

# AFTER (fixed):
python3 scripts/train_game_outcome_model.py \
    --features "$FEATURES_FILE" \
    --output "$MODEL_OUTPUT_DIR/"
```

---

#### 2. ❌ Unsupported Arguments: `--test-season`, `--verbose`
**Problem:** Script passed arguments that don't exist in training script

**Removed:**
- `--test-season "$TEST_SEASON"` (training uses hardcoded season splits)
- `--verbose` (not supported)

---

#### 3. ❌ Missing Kelly Calibrator Retraining
**Problem:** Script only trained ensemble, didn't retrain calibrator

**Added Steps 4-5:**
```bash
# Step 4: Generate calibration data
python3 scripts/backtest_historical_games.py \
    --features "$FEATURES_FILE" \
    --model "$MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl" \
    --calibration-season 2023-24 \
    --output "$CALIBRATION_DATA"

# Step 5: Train Kelly calibrator
python3 scripts/train_kelly_calibrator.py \
    --data "$CALIBRATION_DATA" \
    --output "$CALIBRATOR_OUTPUT_DIR/" \
    --calibrator-type bayesian
```

---

#### 4. ❌ Incorrect Feature Count in Backup Name
**Problem:** Backup file named `*_101features.pkl` but current model uses 83 features

**Fixed:**
```bash
# BEFORE:
BACKUP_CURRENT="models/game_outcome_ensemble_v1_101features.pkl"

# AFTER:
BACKUP_CURRENT="models/ensemble_game_outcome_model_83features_$(date +%Y%m%d_%H%M%S).pkl"
BACKUP_CALIBRATOR="models/calibrated_kelly_engine_83features_$(date +%Y%m%d_%H%M%S).pkl"
```

---

#### 5. ❌ Single Model Backup, Missing Calibrator
**Problem:** Only backed up ensemble, not calibrator

**Fixed:** Now backs up both models with timestamps

---

#### 6. ❌ Incomplete Deployment Instructions
**Problem:** Deployment section didn't include calibrator or metadata

**Fixed:**
```bash
# Deploy new ensemble model
cp $MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl $CURRENT_MODEL

# Deploy new calibrator
cp $CALIBRATOR_OUTPUT_DIR/calibrated_kelly_engine.pkl $CURRENT_CALIBRATOR

# Update metadata
cp $MODEL_OUTPUT_DIR/model_metadata.json models/
```

---

## New Script Structure

### Complete Workflow (7 Steps):

1. **Validate batch output** - Check 130 features present
2. **Backup current models** - Both ensemble and calibrator with timestamps
3. **Train new ensemble** - With 130 features (83→130)
4. **Generate calibration data** - Backtest on 2023-24 season
5. **Train Kelly calibrator** - Bayesian calibrator on new predictions
6. **Compare performance** - Side-by-side metrics
7. **Deployment instructions** - Complete deployment commands

---

## Expected Behavior

### When Run:
```bash
./scripts/retrain_with_player_features.sh
```

### Outputs:
```
models/
├── ensemble_130features/
│   ├── ensemble_game_outcome_model.pkl    (NEW 130-feature model)
│   ├── model_metadata.json
│   ├── confusion_matrix.png
│   └── calibration_curve.png
├── calibrated_130features/
│   ├── calibrated_kelly_engine.pkl        (NEW calibrator)
│   └── calibrator_metadata.json
├── ensemble_game_outcome_model_83features_20250106_123456.pkl  (backup)
└── calibrated_kelly_engine_83features_20250106_123456.pkl      (backup)

data/
└── calibration_130features.csv            (calibration training data)
```

---

## Deployment Criteria

**Deploy if ALL conditions met:**
- ✅ Test accuracy improves by ≥2% (e.g., 67.5% → 69.5%+)
- ✅ Brier score decreases (e.g., 0.209 → 0.199 or better)
- ✅ Log loss decreases
- ✅ No training errors
- ✅ Validation passes

**If conditions met:**
```bash
# Deploy ensemble
cp models/ensemble_130features/ensemble_game_outcome_model.pkl models/

# Deploy calibrator
cp models/calibrated_130features/calibrated_kelly_engine.pkl models/

# Update metadata
cp models/ensemble_130features/model_metadata.json models/

# Test
python scripts/paper_trade_today.py --dry-run
```

---

## Rollback Procedure

**If new model underperforms:**
```bash
# Find backup files (most recent)
ls -lt models/ensemble_game_outcome_model_83features_*.pkl | head -1
ls -lt models/calibrated_kelly_engine_83features_*.pkl | head -1

# Rollback (use actual filenames)
cp models/ensemble_game_outcome_model_83features_20250106_123456.pkl models/ensemble_game_outcome_model.pkl
cp models/calibrated_kelly_engine_83features_20250106_123456.pkl models/calibrated_kelly_engine.pkl
```

---

## Performance Baseline (Current Model)

**Model:** 83 features (not 101 as previously stated)

**Metrics:**
- Accuracy: 67.5%
- AUC: 0.724
- Brier Score: 0.209
- Log Loss: 0.608

**Ensemble Weights:**
- Logistic Regression: 0.8
- Random Forest: 0.2
- XGBoost: 0.0

**Target (130 features):**
- Accuracy: 69-71% (+2-5%)
- Brier Score: <0.20
- Log Loss: <0.58

---

## Estimated Runtime

**Complete retraining workflow:**
- Validation: 1 minute
- Ensemble training: 10-30 minutes
- Calibration data generation: 10-20 minutes
- Calibrator training: 5-10 minutes
- **Total: 30-60 minutes**

---

## Testing Checklist

**Before deployment:**
- [ ] Batch validation passed (130 features)
- [ ] Ensemble training completed without errors
- [ ] Calibrator training completed
- [ ] Accuracy improved by ≥2%
- [ ] Brier score decreased
- [ ] Log loss decreased

**After deployment:**
- [ ] Live predictions work (`paper_trade_today.py --dry-run`)
- [ ] Backtest on 2023-24 shows improvement
- [ ] Paper trade for 1 week before real money
- [ ] Monitor calibration quality daily

---

## Key Improvements

✅ **Correct argument names** - Script now works with actual training script
✅ **Complete workflow** - Both ensemble and calibrator retrained
✅ **Proper backups** - Timestamped backups of both models
✅ **Clear deployment** - Complete deployment instructions
✅ **Easy rollback** - Simple rollback procedure
✅ **Accurate baselines** - Correct feature counts (83→130)

---

**Status:** ✅ Script fixed and ready to use when batch completes

**Next:** Wait for batch to complete (~7.6 hours), then run:
```bash
./scripts/retrain_with_player_features.sh
```
