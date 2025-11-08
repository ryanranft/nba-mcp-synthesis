# Quick Start Guide - Kelly Criterion Calibration Training

## 🚀 Fast Track to Production (60 seconds to start)

### Step 1: Verify Database Credentials (30 seconds)

Database credentials are managed via the **hierarchical secrets management system**.

**Check credentials are configured:**
```bash
python scripts/test_database_credentials.py --context production
```

If credentials are missing, see `.claude/claude.md` for configuration details.

**Quick verification:**
```bash
python -c "
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
config = get_database_config()
print('✓ Credentials loaded:', config['database'], '@', config['host'][:20] + '...')
"
```

### Step 2: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

If you just need the new dependencies:
```bash
pip install xgboost psycopg2-binary
```

### Step 3: Run the Complete Pipeline (12-16 hours)

**Option A: Automated (Recommended)**
```bash
./run_calibration_pipeline.sh
```

**Option B: Step-by-Step**
```bash
# Phase 1: Feature Engineering (3-4 hours)
python scripts/prepare_game_features_complete.py

# Phase 2: Model Training (2-3 hours)
python scripts/train_game_outcome_model.py

# Phase 3: Backtesting (2-3 hours)
python scripts/backtest_historical_games.py

# Phase 4: Calibrator Training (1-2 hours)
python scripts/train_kelly_calibrator.py

# Phase 5: Validation (2-3 hours)
python scripts/test_calibrated_system.py
```

---

## ✅ Validation Checklist

After training, verify these criteria:

```bash
# Check Brier score
python -c "import json; print('Brier:', json.load(open('models/calibrator_metadata.json'))['brier_calibrated'])"
# Target: < 0.15 (< 0.10 ideal)

# Check model accuracy
python -c "import json; print('Accuracy:', json.load(open('models/model_metadata.json'))['test_metrics']['accuracy'])"
# Target: > 0.60

# View validation report
cat reports/validation_report.json | python -m json.tool
# All tests should PASS
```

---

## 🎯 Make Your First Prediction

```bash
python scripts/production_predict.py \
  --home LAL \
  --away GSW \
  --odds 1.9 \
  --away-odds 2.0 \
  --bankroll 10000
```

Output:
```
================================================================================
🏀 LAL vs GSW
================================================================================

📊 Prediction:
  Uncalibrated Probability: 65.3%
  Calibrated Probability: 62.8%
  Market Odds: 1.90 (52.6%)

💰 Betting Decision:
  ✓ RECOMMEND BET
  Bet Amount: $850.00 (8.5% of bankroll)
  Expected Edge: 10.2%
  Kelly Fraction: 25%

  If WIN:
    Profit: $765.00
  If LOSE:
    Loss: $850.00
```

---

## 📊 Check Your Calibration Quality

```bash
# View calibration plots
open plots/calibration_comparison.png
open plots/calibration_correction.png
open plots/bayesian_uncertainty.png
```

**What to look for:**
- Calibration curve should be close to diagonal line
- Brier score improvement > 15%
- Uncertainty bands narrow for most probabilities

---

## ⚠️ IMPORTANT: Paper Trade First!

**DO NOT bet real money until:**

1. ✅ **Brier score < 0.15** (validation passed)
2. ✅ **Model accuracy > 60%** on holdout data
3. ✅ **Paper traded 50-100 games** and tracked results
4. ✅ **CLV is positive** over those paper trades
5. ✅ **You understand the system** completely

Track paper trades in a spreadsheet:
```
Date | Game | Prediction | Odds | Bet Size | Outcome | Profit/Loss | CLV
```

---

## 🔄 Retraining Schedule

**When to retrain:**
- Every 6 months (routine maintenance)
- After 200+ new games
- If Brier score > 0.15 for 3+ weeks
- If model accuracy < 55% over 100 games
- If CLV becomes negative over 50 bets

**Quick retrain (calibrator only):**
```bash
# Update features with new games
python scripts/prepare_game_features_complete.py \
  --seasons 2024-25 2025-26

# Generate new calibration data
python scripts/backtest_historical_games.py \
  --calibration-season 2024-25

# Retrain calibrator
python scripts/train_kelly_calibrator.py

# Validate
python scripts/test_calibrated_system.py
```

---

## 🐛 Troubleshooting

### "Database connection failed"
```bash
# Test credentials loading
python scripts/test_database_credentials.py --context production

# Verify secrets are configured
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# See configuration guide
cat .claude/claude.md
```

### "Python package not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "Brier score > 0.15"
- Collect more calibration data (need 500+ games)
- Retrain model first, then calibrator
- Consider isotonic calibration: `--calibrator-type isotonic`

### "Model accuracy < 55%"
- Review feature importance plots
- Add more sophisticated features
- Collect more training data
- Tune hyperparameters

---

## 📚 Documentation

- **[Calibration Training Guide](docs/CALIBRATION_TRAINING_GUIDE.md)** - Complete guide
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - Kelly system integration
- **[System Complete](CALIBRATION_SYSTEM_COMPLETE.md)** - Full overview
- **[Kelly Implementation](docs/KELLY_CRITERION_IMPLEMENTATION.md)** - Technical details

---

## 💡 Pro Tips

1. **Start conservative:** Use quarter-Kelly (0.25) until you prove your edge
2. **Shop lines:** Always get best odds across multiple books
3. **Track CLV religiously:** This validates your model has real skill
4. **Don't chase 40% bets:** They're extremely rare (0-5 per season)
5. **Monitor weekly:** Check Brier score and CLV every week
6. **Bankroll management:** Never risk more than you can afford to lose

---

## 🎉 Success Criteria

Your system is **production ready** when:

- [x] All 6 phases completed
- [x] Brier score < 0.15
- [x] Model accuracy > 60%
- [x] All validation tests pass
- [x] Paper trading complete (50-100 games)
- [x] CLV > 0% over paper trades
- [x] You understand the system

---

## 🚀 Ready to Start?

```bash
# 1. Verify credentials
python scripts/test_database_credentials.py --context production

# 2. Install
pip install -r requirements.txt

# 3. Run
./run_calibration_pipeline.sh

# 4. Validate
cat reports/validation_report.json | python -m json.tool

# 5. Paper trade
python scripts/production_predict.py --home LAL --away GSW --odds 1.9 --away-odds 2.0

# 6. Track results for 50-100 games

# 7. Go live (only if CLV > 0%)
```

**Good luck! 🍀**

---

*Questions? Check docs/CALIBRATION_TRAINING_GUIDE.md for detailed answers.*
