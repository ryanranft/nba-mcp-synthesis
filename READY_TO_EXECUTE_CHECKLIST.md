# Ready to Execute - Retraining Checklist

**Batch Status:** 9% complete (420/4,621 games)
**ETA:** ~6.5 hours (2025-01-06 ~7:00 AM PST)
**All Systems:** ✅ READY

---

## ✅ Pre-Flight Checks (All Complete)

- ✅ Player feature extraction infrastructure (500 lines)
- ✅ Roster metrics utilities (400 lines)
- ✅ Batch pipeline updated to use unified FeatureExtractor
- ✅ Retraining script fixed (argument mismatches, calibrator added)
- ✅ Validation scripts ready
- ✅ Documentation complete
- ✅ Batch generation running smoothly

---

## 🚀 When Batch Completes - Execute This

### Step 1: Quick Status (30 seconds)
```bash
./scripts/quick_status.sh
```

**Expected:** Batch status shows "COMPLETE" with CSV file created

---

### Step 2: Validate Batch Output (1 minute)
```bash
python scripts/validate_batch_output.py
```

**Success Criteria:**
- ✅ 130 features total
- ✅ 29 player features present (player__*)
- ✅ ~4,000+ games loaded
- ✅ No excessive null values
- ✅ Realistic value ranges

**If fails:** Check logs and debug before proceeding

---

### Step 3: Run Complete Retraining (30-60 minutes)
```bash
./scripts/retrain_with_player_features.sh
```

**What happens:**
1. ✅ Validates batch output (130 features)
2. ✅ Backs up current models (timestamped)
3. ✅ Trains new ensemble (83→130 features)
4. ✅ Generates calibration data (backtest on 2023-24)
5. ✅ Trains Kelly calibrator (Bayesian)
6. ✅ Shows performance comparison
7. ✅ Provides deployment commands

**Watch for:**
- Training progress bars
- Accuracy metrics at end
- Brier score comparison
- Deployment recommendations

---

### Step 4: Review Performance (5 minutes)

**Compare these metrics:**

| Metric | Old (83 feat) | Target (130 feat) | Decision |
|--------|---------------|-------------------|----------|
| Accuracy | 67.5% | ≥69.5% (+2%) | Deploy if ≥2% |
| Brier Score | 0.209 | <0.199 | Deploy if lower |
| Log Loss | 0.608 | <0.578 | Deploy if lower |

**Deployment Criteria:**
- ✅ **MUST** improve accuracy by ≥2%
- ✅ **MUST** decrease Brier score
- ✅ **SHOULD** decrease log loss
- ✅ No training errors

---

### Step 5: Deploy (if successful) (2 minutes)

**If ALL criteria met, copy these commands from script output:**
```bash
# Deploy ensemble
cp models/ensemble_130features/ensemble_game_outcome_model.pkl models/

# Deploy calibrator
cp models/calibrated_130features/calibrated_kelly_engine.pkl models/

# Update metadata
cp models/ensemble_130features/model_metadata.json models/
```

---

### Step 6: Test Live Predictions (2 minutes)
```bash
python scripts/paper_trade_today.py --dry-run
```

**Expected:**
```
✅ Using enhanced model with 130 features
✅ Found X games for today
✅ Predictions generated successfully
✅ Kelly sizing working correctly
```

**If fails:** Rollback immediately (see below)

---

### Step 7: Backtest Validation (30 minutes)
```bash
python scripts/backtest_historical_games.py \
    --features data/game_features_with_players.csv \
    --model models/ensemble_game_outcome_model.pkl \
    --calibration-season 2023-24
```

**Analyze:**
- ROI vs old model
- Bet selectivity (higher quality bets?)
- Calibration quality (predictions match reality?)

---

## 🔙 Rollback Procedure (If Needed)

**If new model underperforms or breaks:**
```bash
# Find backup files (use actual timestamps from script output)
ls -lt models/ensemble_game_outcome_model_83features_*.pkl | head -1
ls -lt models/calibrated_kelly_engine_83features_*.pkl | head -1

# Restore (use actual filenames)
cp models/ensemble_game_outcome_model_83features_YYYYMMDD_HHMMSS.pkl models/ensemble_game_outcome_model.pkl
cp models/calibrated_kelly_engine_83features_YYYYMMDD_HHMMSS.pkl models/calibrated_kelly_engine.pkl

# Verify
python scripts/paper_trade_today.py --dry-run
```

---

## 📊 Expected Timeline

**From batch completion:**
- Validation: 1 minute
- Retraining: 30-60 minutes
- Review: 5 minutes
- Deploy: 2 minutes
- Test: 2 minutes
- Backtest: 30 minutes

**Total: ~1.5-2 hours to production**

---

## ✅ Final Checklist

**Before deploying:**
- [ ] Batch validation passed
- [ ] Accuracy improved ≥2%
- [ ] Brier score decreased
- [ ] No training errors
- [ ] Live predictions work
- [ ] Backtest shows improvement

**After deploying:**
- [ ] Paper trade for 1 week minimum
- [ ] Monitor calibration quality daily
- [ ] Compare paper trade ROI
- [ ] Keep backup models for 30 days

---

## 📚 Quick Reference

**Status:** `./scripts/quick_status.sh`
**Validate:** `python scripts/validate_batch_output.py`
**Retrain:** `./scripts/retrain_with_player_features.sh`
**Test:** `python scripts/paper_trade_today.py --dry-run`

**Documentation:**
- [WHEN_BATCH_COMPLETES.md](WHEN_BATCH_COMPLETES.md) - Complete guide
- [RETRAINING_SCRIPT_FIXES.md](RETRAINING_SCRIPT_FIXES.md) - What was fixed
- [PLAYER_FEATURES_WORKFLOW.md](PLAYER_FEATURES_WORKFLOW.md) - Full workflow

---

## 🎯 Success Metrics

**Baseline Performance (Current 83 Features):**
```
Accuracy:    67.5%
Brier Score: 0.209
Log Loss:    0.608
```

**Target Performance (New 130 Features):**
```
Accuracy:    69-71%   (improvement: +2-5%)
Brier Score: <0.20    (improvement: -0.01+)
Log Loss:    <0.58    (improvement: -0.03+)
```

**If achieved:** 🎉 **DEPLOY**
**If not achieved:** Keep for Phase 2 (spreads/totals may benefit more)

---

**Current Status:** Batch at 9% (~6.5 hours remaining)
**Next Check:** 2025-01-06 ~7:00 AM PST
**Action:** Run this checklist top to bottom

✅ **ALL SYSTEMS READY**
