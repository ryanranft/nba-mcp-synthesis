# Calibration Training Guide

Complete guide for training and retraining the Kelly Criterion calibrator for your NBA betting system.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Training (First Time Setup)](#initial-training)
4. [Retraining (Periodic Updates)](#retraining)
5. [Validation & Testing](#validation)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Calibration?

Your game simulation model might predict 90% win probability, but historically that team only wins 60% of the time. **Calibration** fixes this bias by learning the correction function:

```
90% simulation → 65% calibrated probability
```

This is CRITICAL for the Kelly Criterion - betting 40% of your bankroll on an uncalibrated 90% becomes a disaster!

### The Pipeline

```
Historical Games → Feature Engineering → Model Training → Backtesting → Calibration → Validation → Production
```

**Time Required:**
- Initial Setup: 12-16 hours
- Retraining: 2-3 hours (every 6-12 months)

---

## Prerequisites

### 1. Environment Setup

```bash
# Clone/navigate to project
cd nba-mcp-synthesis

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.template .env
```

Edit `.env` with your database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nba
DB_USER=your_username
DB_PASSWORD=your_password
```

### 2. Database Access

You need PostgreSQL access to the NBA database with:
- `games` table (4,621+ games from 2021-22 to present)
- `team_game_stats` table (detailed statistics)

Verify access:
```bash
psql -h localhost -U your_username -d nba -c "SELECT COUNT(*) FROM games;"
```

### 3. Directory Structure

Create required directories:
```bash
mkdir -p data models plots reports
```

---

## Initial Training

### Step 1: Feature Engineering (3-4 hours)

Extract features from historical games:

```bash
python scripts/prepare_game_features_complete.py \
  --seasons 2021-22 2022-23 2023-24 2024-25 \
  --output data/game_features.csv \
  --min-games 10
```

**What this does:**
- Fetches 4,621 games from database
- Calculates rolling stats (PPG, FG%, 3PT%, etc.) for last 5, 10, 20 games
- Computes home/away splits
- Calculates head-to-head history
- Adds rest days, back-to-back indicators
- Outputs ~50 features per game

**Expected output:**
```
Total games: 4,200 (after filtering for min games)
Total features: 52
Date range: 2021-10-19 to 2025-04-13
```

**Troubleshooting:**
- If < 1,000 games: Check `--min-games` parameter
- If database errors: Verify .env credentials
- If memory errors: Process seasons separately

### Step 2: Train Ensemble Model (2-3 hours)

Train Logistic Regression + Random Forest + XGBoost ensemble:

```bash
python scripts/train_game_outcome_model.py \
  --features data/game_features.csv \
  --output models/
```

**What this does:**
- Splits data: Train (2021-22, 2022-23), Val (2023-24), Test (2024-25)
- Trains 3 models individually
- Optimizes ensemble weights via grid search
- Validates on 2023-24 holdout
- Saves models to `models/ensemble_game_outcome_model.pkl`

**Expected output:**
```
Train (2021-22, 2022-23): 2,781 games
Val (2023-24): 1,393 games
Test (2024-25): 447 games

Model Performance:
  Accuracy: 62.3%
  AUC-ROC: 0.687
  Brier Score: 0.231
```

**Quality thresholds:**
- ✅ Accuracy > 60%: Excellent
- ✅ Accuracy 55-60%: Good
- ⚠️ Accuracy < 55%: Consider feature engineering improvements

### Step 3: Generate Calibration Data (2-3 hours)

Run backtesting to generate (sim_prob, outcome) pairs:

```bash
python scripts/backtest_historical_games.py \
  --features data/game_features.csv \
  --model models/ensemble_game_outcome_model.pkl \
  --calibration-season 2023-24 \
  --output data/calibration_training_data.csv \
  --plots-dir plots/
```

**What this does:**
- Loads trained ensemble model
- Generates predictions for 2023-24 season (1,393 games)
- Creates (simulation_probability, actual_outcome) pairs
- Analyzes prediction quality
- Generates diagnostic plots

**Expected output:**
```
Generated predictions: 1,393
Uncalibrated Brier score: 0.232
```

**Review diagnostic plots:**
- `plots/pre_calibration_curve.png` - Shows calibration bias
- `plots/prediction_distribution.png` - Prediction spread by outcome
- `plots/confidence_distribution.png` - Games per confidence bin

### Step 4: Train Calibrator (1-2 hours)

Train Bayesian calibrator to correct simulation bias:

```bash
python scripts/train_kelly_calibrator.py \
  --data data/calibration_training_data.csv \
  --calibrator-type bayesian \
  --output models/ \
  --plots-dir plots/
```

**What this does:**
- Loads calibration training data
- Trains Bayesian calibrator with uncertainty quantification
- Validates calibration quality
- Tests large bet (40%) criteria
- Saves to `models/calibrated_kelly_engine.pkl`

**Expected output:**
```
Brier Score Improvement: 0.045 (19.4%)
Final Brier Score: 0.187

✓ GOOD calibration - Safe for betting
```

**Quality thresholds:**
- ✓ Brier < 0.06: EXCELLENT - Ready for 40% bets
- ✓ Brier < 0.10: GOOD - Safe for betting
- ⚠️ Brier < 0.15: ACCEPTABLE - Use caution
- ❌ Brier ≥ 0.15: POOR - Do NOT use

**Review calibration plots:**
- `plots/calibration_comparison.png` - Before vs after
- `plots/calibration_correction.png` - Correction function
- `plots/bayesian_uncertainty.png` - Uncertainty estimates

### Step 5: Validate System (2-3 hours)

Run comprehensive validation tests:

```bash
python scripts/test_calibrated_system.py \
  --features data/game_features.csv \
  --engine models/calibrated_kelly_engine.pkl \
  --output reports/
```

**What this does:**
- Tests calibration on 2024-25 holdout
- Validates Kelly sizing logic
- Tests edge detection
- Simulates CLV tracking
- Validates 40% bet criteria
- Runs end-to-end workflow

**Expected output:**
```
✓ ALL TESTS PASSED - System Ready for Production!

Calibration Accuracy: ✓ GOOD
Kelly Sizing: ✓ PASS (5/5 tests)
Edge Detection: ✓ PASS
CLV Tracking: ✓ GOOD - Positive CLV
Large Bet Criteria: ✓ PASS
End-to-End Workflow: ✓ PASS
```

**Review validation report:**
- `reports/validation_report.json` - Detailed test results
- `plots/holdout_calibration.png` - Holdout set performance

---

## Retraining

Retrain calibrator every 6-12 months or after collecting 200+ new games.

### Quick Retraining (Calibrator Only)

If your model performance is stable, just retrain the calibrator:

```bash
# 1. Update features with new games
python scripts/prepare_game_features_complete.py \
  --seasons 2023-24 2024-25 2025-26 \
  --output data/game_features_updated.csv

# 2. Generate new calibration data (use existing model)
python scripts/backtest_historical_games.py \
  --features data/game_features_updated.csv \
  --model models/ensemble_game_outcome_model.pkl \
  --calibration-season 2024-25 \
  --output data/calibration_training_data_v2.csv

# 3. Retrain calibrator
python scripts/train_kelly_calibrator.py \
  --data data/calibration_training_data_v2.csv \
  --output models/ \
  --plots-dir plots/

# 4. Validate
python scripts/test_calibrated_system.py \
  --features data/game_features_updated.csv \
  --engine models/calibrated_kelly_engine.pkl \
  --output reports/
```

**Time:** 2-3 hours

### Full Retraining (Model + Calibrator)

If model accuracy drops or you have 2+ new seasons:

```bash
# Run all scripts in sequence
./scripts/run_full_pipeline.sh
```

**Time:** 8-10 hours

---

## Validation

### Key Metrics to Monitor

**1. Calibration Quality (Brier Score)**
- Target: < 0.10
- Warning threshold: > 0.15
- Check monthly

**2. Model Accuracy**
- Target: > 60%
- Warning threshold: < 55%
- Check every 100 games

**3. CLV (Closing Line Value)**
- Target: > +5%
- Warning threshold: < 0%
- Check after every 50 bets

**4. Bet Sizing Distribution**
- Most bets: 5-15% of bankroll
- Few bets: > 25% of bankroll
- Rare bets: 40% of bankroll

### When to Retrain

Retrain if ANY of these occur:

- ❌ Brier score > 0.15 for 3+ weeks
- ❌ Model accuracy < 55% over 100 games
- ❌ Negative CLV over 50 bets
- ❌ 6 months since last training
- ❌ Major NBA rule changes (e.g., 3-point line moved)

---

## Production Deployment

### 1. Save Production Artifacts

```bash
# Copy trained models
cp models/ensemble_game_outcome_model.pkl production/
cp models/calibrated_kelly_engine.pkl production/
cp models/feature_scaler.pkl production/

# Save metadata
cp models/model_metadata.json production/
cp models/calibrator_metadata.json production/
```

### 2. Create Production Prediction Script

Use `scripts/production_predict.py` (see next section).

### 3. Set Up Monitoring

Create monitoring dashboard to track:
- Daily Brier score
- Weekly CLV
- Bet sizing distribution
- Bankroll growth

### 4. Paper Trading

**CRITICAL:** Paper trade for 50-100 games before using real money.

Track in spreadsheet:
- Game, Date, Prediction, Odds, Bet Size, Outcome, Profit/Loss
- Validate positive CLV and positive EV

---

## Troubleshooting

### Problem: Brier Score > 0.15

**Possible causes:**
1. Insufficient training data (< 500 games)
2. Model drift (game dynamics changed)
3. Poor feature quality

**Solutions:**
- Collect more historical data
- Retrain model with recent seasons
- Add new features (injuries, rest days, etc.)

### Problem: Model Accuracy < 55%

**Possible causes:**
1. Weak features
2. Class imbalance
3. Overfitting

**Solutions:**
- Review feature importance plots
- Add more sophisticated features (player-level data)
- Tune hyperparameters
- Use SMOTE for class balancing

### Problem: Negative CLV

**Possible causes:**
1. Slow line detection (getting worst odds)
2. Model not finding value
3. Vig too high

**Solutions:**
- Get faster odds feeds
- Only bet +EV > 5%
- Shop for best lines across books

### Problem: System Never Recommends 40% Bets

**This is EXPECTED!** 40% bets require:
- Calibrated probability > 88%
- Edge > 20%
- Uncertainty < 2%
- Brier score < 0.06
- CLV > 5%

You might get 0-5 per season. That's normal!

---

## Advanced Topics

### Custom Calibrators

Create custom calibrator for specific scenarios:

```python
from mcp_server.betting import BayesianCalibrator

# Train separate calibrators for home/away
calibrator_home = BayesianCalibrator()
calibrator_away = BayesianCalibrator()

# Train on filtered data
home_games = df[df['is_home'] == True]
calibrator_home.fit(home_games['sim_prob'], home_games['outcome'])
```

### Seasonal Adjustments

Account for playoff intensity:

```python
# Adjust predictions for playoffs
if is_playoff_game:
    sim_prob = adjust_for_playoff_intensity(sim_prob, home_team, away_team)
```

### Bankroll Management

```python
# Dynamic Kelly fraction based on confidence
if brier_score < 0.06:
    kelly_fraction = 0.40  # Aggressive
elif brier_score < 0.10:
    kelly_fraction = 0.25  # Normal
else:
    kelly_fraction = 0.10  # Conservative
```

---

## Summary Checklist

### Initial Training
- [ ] Environment setup (.env, dependencies)
- [ ] Feature engineering (4,200+ games)
- [ ] Model training (ensemble model)
- [ ] Backtesting (1,393+ predictions)
- [ ] Calibrator training (Brier < 0.15)
- [ ] Validation (all tests pass)
- [ ] Paper trading (50-100 games)

### Retraining (Every 6 months)
- [ ] Update features with new games
- [ ] Generate new calibration data
- [ ] Retrain calibrator
- [ ] Validate on holdout
- [ ] Monitor CLV for 50 bets

### Production
- [ ] Production deployment
- [ ] Monitoring dashboard
- [ ] Weekly Brier score checks
- [ ] Monthly CLV analysis
- [ ] Quarterly full retraining

---

## Support & Resources

- **Integration Guide:** `/docs/INTEGRATION_GUIDE.md`
- **Kelly System Docs:** `/mcp_server/betting/README.md`
- **Test Script:** `scripts/test_kelly_criterion.py`
- **Example Notebooks:** `/notebooks/`

For questions or issues, refer to the validation reports and diagnostic plots first.

---

**Remember:** The calibrator is only as good as your training data. More high-quality historical predictions = better calibration = safer betting!

Good luck! 🎰📈
