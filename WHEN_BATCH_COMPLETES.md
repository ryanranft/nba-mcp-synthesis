# When Batch Generation Completes - Action Items

**Expected Completion:** 2025-01-06 ~7:30 AM PST (±30 minutes)

---

## 🔍 Step 1: Verify Batch Completion

### Quick Check
```bash
./scripts/quick_status.sh
```

**Look for:**
```
Batch Feature Generation:
Status: ⏸️  NOT RUNNING
Output: ✅ COMPLETE (4,XXX rows)
```

### Detailed Check
```bash
# Check file exists and size
ls -lh data/game_features_with_players.csv

# Expected: ~600-800 MB file

# Quick stats
wc -l data/game_features_with_players.csv
# Expected: ~4,000-4,500 rows (some games filtered by min-games threshold)

# Check columns
head -1 data/game_features_with_players.csv | tr ',' '\n' | wc -l
# Expected: 138 columns (130 features + 8 metadata)

# Verify player features present
head -1 data/game_features_with_players.csv | tr ',' '\n' | grep 'player__' | wc -l
# Expected: 29 player features
```

### If Batch Failed or Incomplete

**Check log for errors:**
```bash
tail -100 logs/batch_feature_generation.log | grep -i error
```

**Restart if needed:**
```bash
nohup python3 scripts/prepare_game_features_complete.py \
    --seasons 2021-22 2022-23 2023-24 2024-25 \
    --output data/game_features_with_players.csv \
    --min-games 10 \
    > logs/batch_feature_generation.log 2>&1 &

echo "Process ID: $!"
```

---

## ✅ Step 2: Validate Output Quality

### Automated Validation
```bash
python scripts/validate_batch_output.py
```

**Expected Output:**
```
================================================================================
VALIDATION SUMMARY
================================================================================

✅ VALIDATION PASSED

Dataset ready for training:
  - 4,XXX games
  - 130 features (including 29 player features)
  - 4 seasons

Next step:
  python scripts/train_game_outcome_model.py \
      --input data/game_features_with_players.csv \
      --output models/ensemble_with_players.pkl \
      --test-season 2024-25
```

### If Validation Fails

**Review validation output for issues:**
- Missing player features → Check player_features.py
- Excessive null values → Check data quality in database
- Value range issues → Check feature calculations

**Manual data inspection:**
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/game_features_with_players.csv')
print(f'Shape: {df.shape}')
print(f'\nColumns with player__: {len([c for c in df.columns if \"player__\" in c])}')
print(f'\nNull counts (top 10):')
print(df.isnull().sum().sort_values(ascending=False).head(10))
print(f'\nSample player features:')
player_cols = [c for c in df.columns if 'player__' in c][:5]
print(df[player_cols].describe())
"
```

---

## 🚀 Step 3: Retrain Models (Fully Automated)

### Run Complete Retraining Pipeline
```bash
./scripts/retrain_with_player_features.sh
```

**This script will:** ✅ **ALL FIXED - READY TO USE**
1. ✅ Validate batch output (130 features)
2. ✅ Backup current models (ensemble + calibrator) with timestamps
3. ✅ Train new ensemble model → `models/ensemble_130features/`
4. ✅ Generate calibration data via backtest on 2023-24
5. ✅ Train Kelly calibrator → `models/calibrated_130features/`
6. ✅ Display performance comparison (83 vs 130 features)
7. ✅ Provide complete deployment instructions

**Expected Training Time:** 30-60 minutes total

**Note:** Script was FIXED (see [RETRAINING_SCRIPT_FIXES.md](RETRAINING_SCRIPT_FIXES.md)):
- ✅ Argument mismatches corrected
- ✅ Kelly calibrator retraining added
- ✅ Proper backups with timestamps
- ✅ Complete deployment workflow

### What to Look For in Training Output

**Key Metrics to Review:**

#### Test Set Performance (2024-25 Season)
```
Old Model (101 features):
  Accuracy: ~67.5%
  Brier Score: ~0.210
  Log Loss: ~0.590

New Model (130 features):
  Accuracy: 69-71%  ← Should be +2-5% higher
  Brier Score: 0.195-0.200  ← Should be lower (better)
  Log Loss: 0.560-0.575  ← Should be lower (better)
```

#### Decision Criteria

**Deploy new model if:**
- ✅ Accuracy improves by ≥2%
- ✅ Brier score decreases
- ✅ Log loss decreases
- ✅ No errors during training

**Don't deploy if:**
- ❌ Accuracy improvement <1%
- ❌ Metrics worse than old model
- ❌ Training errors or warnings

---

## 📦 Step 4: Deploy New Model

### If Validation Successful (Improvement ≥2%)

```bash
# Backup is already done by retrain script, so just deploy
cp models/ensemble_with_players.pkl models/game_outcome_ensemble.pkl

echo "✅ New model deployed!"
```

### Test Live Predictions
```bash
python scripts/paper_trade_today.py --dry-run
```

**Expected Output:**
```
✅ Using enhanced model with 130 features
✅ Found X games for today
✅ Predictions generated successfully

Game Predictions:
  Home Team vs Away Team
  Home Win Probability: 0.XX
  Edge: X.X%
  Recommended Bet: ...
```

### If Live Predictions Fail

**Rollback to old model:**
```bash
cp models/game_outcome_ensemble_v1_101features.pkl models/game_outcome_ensemble.pkl
```

**Debug:**
```bash
# Test feature extraction
python scripts/test_player_features.py

# Check model file
ls -lh models/game_outcome_ensemble.pkl

# Try predictions again
python scripts/paper_trade_today.py --dry-run --verbose
```

---

## 📊 Step 5: Backtest Validation

### Run Historical Backtest
```bash
python scripts/backtest_historical_games.py \
    --model models/game_outcome_ensemble.pkl \
    --features data/game_features_with_players.csv \
    --seasons 2023-24 \
    --kelly-mode conservative \
    --min-edge 0.05 \
    --verbose
```

**What to Analyze:**

1. **ROI Improvement**
   - Old model: Baseline ROI on 2023-24
   - New model: Should show +2-5% improvement

2. **Bet Selectivity**
   - New model should be more selective (fewer bets)
   - Higher average edge per bet
   - Better calibration

3. **Calibration Curves**
   - Predicted probabilities closer to actual outcomes
   - Sharper Brier score decomposition

### Save Backtest Results
```bash
# Create results directory
mkdir -p reports/player_features_backtest/

# Save results
python scripts/backtest_historical_games.py \
    --model models/game_outcome_ensemble.pkl \
    --features data/game_features_with_players.csv \
    --seasons 2023-24 \
    --output reports/player_features_backtest/2023-24_results.json
```

---

## 📝 Step 6: Document Results

### Create Performance Report

```bash
cat > reports/player_features_performance.md << 'EOF'
# Player Features Model Performance Report

**Date:** $(date +%Y-%m-%d)
**Model:** ensemble_with_players.pkl (130 features)

## Training Results

**Test Set (2024-25 Season):**
- Accuracy: XX.X%
- Brier Score: X.XXX
- Log Loss: X.XXX

**Improvement over baseline (101 features):**
- Accuracy: +X.X%
- Brier Score: -X.XXX (better)
- Log Loss: -X.XXX (better)

## Backtest Results (2023-24 Season)

- Total Games: XXX
- Bets Placed: XXX
- Win Rate: XX.X%
- ROI: +X.X%
- Average Edge: X.X%

## Deployment

- Status: ✅ DEPLOYED
- Date: $(date +%Y-%m-%d)
- Backup: models/game_outcome_ensemble_v1_101features.pkl

EOF

# View report
cat reports/player_features_performance.md
```

### Update Todo List

**Mark as complete:**
- ✅ Batch feature generation
- ✅ Model retraining
- ✅ Performance validation
- ✅ Deployment

---

## 🎯 Expected Outcomes

### Success Criteria

✅ **SUCCESSFUL DEPLOYMENT** if:
- Batch generated 4,000+ games with 130 features
- Validation passed all checks
- Model accuracy improved by ≥2%
- Live predictions work correctly
- Backtest shows ROI improvement

### If Success Criteria Not Met

**Scenario 1: Minimal Improvement (<2%)**
- Keep new features but don't deploy yet
- Investigate which player features have low importance
- Consider feature engineering improvements
- May still benefit spreads/totals models (Phase 2)

**Scenario 2: Technical Issues**
- Rollback to old model
- Review error logs
- Fix issues and retrain
- Re-validate before deployment

**Scenario 3: Data Quality Issues**
- Review database queries in player_features.py
- Check for systematic null values
- Validate player stat calculations
- May need to refine feature definitions

---

## 📞 Quick Reference Commands

### Status & Monitoring
```bash
./scripts/quick_status.sh                  # Overall status
./scripts/check_batch_progress.sh          # Batch progress
tail -f logs/batch_feature_generation.log  # Live log
```

### Validation
```bash
python scripts/validate_batch_output.py    # Validate batch
python scripts/test_player_features.py     # Test live extraction
```

### Training & Deployment
```bash
./scripts/retrain_with_player_features.sh  # Full automated retraining
python scripts/paper_trade_today.py --dry-run  # Test predictions
```

### Rollback
```bash
cp models/game_outcome_ensemble_v1_101features.pkl models/game_outcome_ensemble.pkl
```

---

## 🚨 Troubleshooting

### Batch Didn't Complete
- Check logs: `tail -100 logs/batch_feature_generation.log`
- Look for Python errors, database disconnects
- Restart with same command

### Validation Fails
- Review specific validation errors
- Check player feature columns present
- Inspect data quality manually

### Training Fails
- Check input file exists and valid
- Review training error messages
- Ensure sufficient memory (need ~2-4 GB)
- Try manual training with verbose flag

### Predictions Fail
- Test feature extraction: `python scripts/test_player_features.py`
- Check model file loaded correctly
- Verify database connection
- Look for missing player data

---

## 📖 Documentation Reference

- **Workflow Guide:** [PLAYER_FEATURES_WORKFLOW.md](PLAYER_FEATURES_WORKFLOW.md)
- **Progress Summary:** [PHASE1_COMPLETION_SUMMARY.md](PHASE1_COMPLETION_SUMMARY.md)
- **Technical Details:** [PLAYER_FEATURES_PHASE1_PROGRESS.md](PLAYER_FEATURES_PHASE1_PROGRESS.md)
- **Documentation Index:** [PLAYER_FEATURES_INDEX.md](PLAYER_FEATURES_INDEX.md)

---

## ✅ Final Checklist

When you return and batch is complete:

- [ ] Verify batch completed successfully
- [ ] Run validation: `python scripts/validate_batch_output.py`
- [ ] Retrain model: `./scripts/retrain_with_player_features.sh`
- [ ] Review performance metrics (≥2% improvement?)
- [ ] Deploy if successful: `cp models/ensemble_with_players.pkl models/game_outcome_ensemble.pkl`
- [ ] Test live predictions: `python scripts/paper_trade_today.py --dry-run`
- [ ] Run backtest: `python scripts/backtest_historical_games.py --seasons 2023-24`
- [ ] Document results in `reports/player_features_performance.md`
- [ ] Update production betting scripts to use new model

---

**Estimated Time for Steps 1-6:** 1-2 hours (mostly automated)

**Current Batch Status:** 3% complete (126/4,621 games), ~7.4 hours remaining

**Next Check:** 2025-01-06 ~7:30 AM PST
