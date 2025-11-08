# Kelly Criterion Calibration Training System

> **Solve the "90% simulation → 60% reality" problem with automated Bayesian calibration**

## 🎯 What This Does

Trains a calibrator that corrects your simulation bias:

```
Your 10k simulation: 90% home team wins
Calibrator corrects: → 65% calibrated probability
Kelly Criterion uses: 65% for safe bet sizing
Result: Long-term profitability ✅
```

**Without calibration:** Bet 40% of bankroll on "90%" → Lose 40% of bets → Bankruptcy
**With calibration:** Bet 15% of bankroll on "65%" → Positive EV → Profit

---

## ⚡ Quick Start (3 Commands)

```bash
# 1. Verify credentials
python scripts/test_database_credentials.py --context production

# 2. Install
pip install -r requirements.txt

# 3. Run (12-16 hours)
./run_calibration_pipeline.sh
```

**Done!** Your calibrated Kelly engine is ready at `models/calibrated_kelly_engine.pkl`

---

## 📦 What You Get

### 6 Production Scripts
1. **`prepare_game_features_complete.py`** - Extract 50+ features from 4,621 games
2. **`train_game_outcome_model.py`** - Train LR + RF + XGBoost ensemble
3. **`backtest_historical_games.py`** - Generate calibration training data
4. **`train_kelly_calibrator.py`** - Train Bayesian calibrator
5. **`test_calibrated_system.py`** - 6 comprehensive validation tests
6. **`production_predict.py`** - Make live betting decisions

### Complete Documentation
- **`QUICK_START.md`** - Get started in 60 seconds
- **`docs/CALIBRATION_TRAINING_GUIDE.md`** - 11,000+ word complete guide
- **`CALIBRATION_SYSTEM_COMPLETE.md`** - Full system overview
- **`docs/INTEGRATION_GUIDE.md`** - Kelly system integration

### Automation & Configuration
- **`run_calibration_pipeline.sh`** - One script runs entire pipeline
- **`.claude/claude.md`** - Database credentials configuration guide
- **`scripts/test_database_credentials.py`** - Credentials validation script

---

## 🔄 The Pipeline

```
Historical NBA Data (4,621 games)
         ↓
   Feature Engineering (50+ features per game)
         ↓
   Ensemble Training (LR + RF + XGBoost)
         ↓
   Backtesting (1,393 predictions)
         ↓
   Bayesian Calibration (learns correction function)
         ↓
   Validation (6 tests)
         ↓
   Production Ready! 🚀
```

---

## 📊 Expected Results

**Model Performance:**
- Accuracy: 60-62% on holdout ✓
- Brier Score (calibrated): < 0.15 ✓
- CLV: Positive over 50+ bets ✓

**Bet Sizing:**
- Typical bets: 5-15% of bankroll
- Large bets (>25%): 1-3% of games
- 40% bets: 0-5 per season (very rare!)

---

## 🎯 Usage Example

```bash
# Make prediction
python scripts/production_predict.py \
  --home LAL --away GSW \
  --odds 1.9 --away-odds 2.0 \
  --bankroll 10000
```

**Output:**
```
================================================================================
🏀 LAL vs GSW
================================================================================

📊 Prediction:
  Calibrated Probability: 62.8%
  Market Odds: 1.90 (52.6%)

💰 Betting Decision:
  ✓ RECOMMEND BET
  Bet Amount: $850.00 (8.5% of bankroll)
  Expected Edge: 10.2%

  If WIN: Profit $765.00
  If LOSE: Loss $850.00
```

---

## ⚠️ Important: Paper Trade First!

**DO NOT** use real money until:

1. ✅ Brier score < 0.15
2. ✅ Model accuracy > 60%
3. ✅ Paper traded 50-100 games
4. ✅ **CLV is positive** (critical!)
5. ✅ You understand the system

Track every paper trade:
```
Date | Game | Pred | Odds | Bet | Outcome | P/L | CLV
```

---

## 🔧 Requirements

### Database
- PostgreSQL with NBA data
- Tables: `games`, `team_game_stats`
- 4,621+ games from 2021-22 to present

### Python Dependencies
```bash
# Core
pandas >= 2.2.3
numpy >= 1.26.4
scikit-learn >= 1.3.0

# New (for this system)
xgboost >= 2.0.0
psycopg2-binary >= 2.9.10

# Note: python-dotenv removed (now uses unified_secrets_manager)
# All others in requirements.txt
```

### System
- Python 3.11+
- 8GB+ RAM
- 10GB+ disk space
- 12-16 hours for initial training

---

## 📁 Directory Structure

```
nba-mcp-synthesis/
├── scripts/
│   ├── prepare_game_features_complete.py
│   ├── train_game_outcome_model.py
│   ├── backtest_historical_games.py
│   ├── train_kelly_calibrator.py
│   ├── test_calibrated_system.py
│   └── production_predict.py
├── mcp_server/
│   └── betting/  # Existing Kelly system
├── docs/
│   ├── CALIBRATION_TRAINING_GUIDE.md
│   ├── INTEGRATION_GUIDE.md
│   └── KELLY_CRITERION_IMPLEMENTATION.md
├── data/  # Generated during training
│   ├── game_features.csv
│   └── calibration_training_data.csv
├── models/  # Generated during training
│   ├── ensemble_game_outcome_model.pkl
│   └── calibrated_kelly_engine.pkl
├── plots/  # Generated during training
│   ├── calibration_comparison.png
│   └── bayesian_uncertainty.png
├── reports/  # Generated during validation
│   └── validation_report.json
├── run_calibration_pipeline.sh
├── QUICK_START.md
├── CALIBRATION_SYSTEM_COMPLETE.md
├── .claude/
│   └── claude.md  # Database credentials configuration
└── .env.template  # Deprecation notice
```

---

## 🔄 Maintenance

**Retrain Every 6 Months:**

```bash
# Quick retrain (2-3 hours)
python scripts/prepare_game_features_complete.py --seasons 2024-25 2025-26
python scripts/backtest_historical_games.py --calibration-season 2024-25
python scripts/train_kelly_calibrator.py
python scripts/test_calibrated_system.py
```

**Monitor Weekly:**
- Brier score (keep < 0.15)
- Model accuracy (keep > 60%)
- CLV (keep > 0%)

---

## 🎓 How It Works

### The Problem
Your game simulation predicts 90% win probability, but historically teams with that prediction only win 60% of the time. Betting 40% of your bankroll based on 90% is a disaster!

### The Solution
Train a Bayesian calibrator on historical (prediction, outcome) pairs:
- Learns: "When I predict 90%, it's actually 65%"
- Corrects: All future predictions automatically
- Quantifies: Uncertainty for each prediction

### The Kelly Formula
```
f* = (bp - q) / b

Where:
f* = Fraction of bankroll to bet
b = Decimal odds - 1
p = Calibrated probability (not simulation!)
q = 1 - p
```

**With calibration:**
- Input: 90% simulation → 65% calibrated
- Kelly: (0.9 * 0.65 - 0.35) / 0.9 = 26% of bankroll
- Quarter Kelly: 6.5% (safe)

**Without calibration:**
- Input: 90% simulation (uncorrected)
- Kelly: (0.9 * 0.90 - 0.10) / 0.9 = 79% of bankroll (!!)
- Quarter Kelly: 20% (still too much!)
- Reality: Lose 40% of the time → Ruin

---

## 📈 Success Stories

**What happens with proper calibration:**

1. **Accurate probabilities** → Better decisions
2. **Safe bet sizing** → Bankroll protection
3. **Positive CLV** → Proving your edge
4. **Long-term profit** → 3-8% ROI per bet

**What happens without calibration:**

1. **Overconfident predictions** → Bad decisions
2. **Oversized bets** → Massive losses
3. **Negative CLV** → No real edge
4. **Bankruptcy** → Game over

---

## 🐛 Troubleshooting

### "Brier score > 0.15"
→ Need more calibration data (500+ games)
→ Retrain model first, then calibrator
→ Try isotonic calibration

### "Model accuracy < 55%"
→ Add better features (player-level data)
→ Collect more training data
→ Tune hyperparameters

### "Negative CLV"
→ Your model has no edge (don't bet!)
→ Improve predictions or stop betting
→ Check if vig is too high

### "System never recommends 40% bets"
→ **This is normal!** 40% bets are extremely rare
→ Requires all criteria met (happens 0-5 times per season)
→ Most bets will be 5-15% of bankroll

---

## 📚 Learn More

**Start here:**
1. **`QUICK_START.md`** - Get running in 60 seconds
2. **`docs/CALIBRATION_TRAINING_GUIDE.md`** - Complete training guide
3. **`CALIBRATION_SYSTEM_COMPLETE.md`** - Full system overview

**Deep dives:**
- Kelly system design: `mcp_server/betting/README.md`
- Technical implementation: `docs/KELLY_CRITERION_IMPLEMENTATION.md`
- Integration: `docs/INTEGRATION_GUIDE.md`

---

## ⚖️ Disclaimer

**This is an educational system for learning about:**
- Bayesian calibration
- Machine learning for sports
- Kelly Criterion bet sizing
- Closing line value tracking

**Important:**
- Gambling involves risk
- Past performance ≠ future results
- Only bet what you can afford to lose
- Check local gambling laws
- Seek help if gambling becomes a problem

---

## 🤝 Contributing

Found a bug? Have a suggestion?

1. Check existing issues
2. Create detailed bug report
3. Include steps to reproduce
4. Share logs/error messages

---

## 📝 License

Part of the NBA MCP Synthesis System.

See main repository for license details.

---

## 🎯 Summary

**You have:**
- ✅ Complete calibration training system
- ✅ 6 production scripts
- ✅ Comprehensive documentation
- ✅ Automated pipeline
- ✅ Validation suite

**You need to:**
- Verify credentials (30 seconds): `python scripts/test_database_credentials.py`
- Run pipeline (12-16 hours): `./run_calibration_pipeline.sh`
- Paper trade (50-100 games)
- Validate CLV > 0%
- Go live responsibly

**Start now:**
```bash
./run_calibration_pipeline.sh
```

---

**Questions?** → Read `docs/CALIBRATION_TRAINING_GUIDE.md`

**Ready to bet?** → Paper trade first!

**Good luck! 🍀📈💰**
