#!/bin/bash
#
# Complete Kelly Criterion Calibration Training Pipeline
#
# This script runs the entire 6-phase training pipeline from start to finish.
# Estimated time: 12-16 hours total
#
# Prerequisites:
# 1. PostgreSQL database with NBA data
# 2. Database credentials configured in hierarchical secrets system
#    (see .claude/claude.md for details)
# 3. Python dependencies installed (pip install -r requirements.txt)
#

set -e  # Exit on any error

echo "======================================================================"
echo "Kelly Criterion Calibration Training Pipeline"
echo "======================================================================"
echo ""
echo "This will run all 6 phases:"
echo "  Phase 1: Feature Engineering (3-4 hours)"
echo "  Phase 2: Ensemble Model Training (2-3 hours)"
echo "  Phase 3: Historical Backtesting (2-3 hours)"
echo "  Phase 4: Calibrator Training (1-2 hours)"
echo "  Phase 5: System Validation (2-3 hours)"
echo "  Phase 6: Completion Report"
echo ""
echo "Total estimated time: 12-16 hours"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

# Check prerequisites
echo ""
echo "Checking prerequisites..."
echo "----------------------------------------------------------------------"

# Check secrets manager module
if [ ! -f mcp_server/unified_secrets_manager.py ]; then
    echo "❌ ERROR: unified_secrets_manager.py not found"
    echo "   Ensure you're in the project root directory"
    exit 1
fi
echo "✓ Secrets manager module found"

# Test secrets loading
python3 -c "
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
config = get_database_config()
missing = [k for k, v in config.items() if not v]
if missing:
    print(f'❌ ERROR: Missing database credentials: {missing}')
    print('See .claude/claude.md for configuration details')
    exit(1)
" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to load database credentials"
    echo "   See .claude/claude.md for configuration instructions"
    exit 1
fi
echo "✓ Database credentials loaded"

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python not found"
    exit 1
fi
echo "✓ Python found: $(python --version)"

# Check required Python packages
python -c "import pandas, numpy, sklearn, xgboost" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Required Python packages not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi
echo "✓ Required packages installed"

# Create directories
mkdir -p data models plots reports
echo "✓ Directories created"

echo ""
echo "======================================================================"
echo "PHASE 1: Feature Engineering"
echo "======================================================================"
echo "Extracting 50+ features from 4,621 NBA games..."
echo "Estimated time: 3-4 hours"
echo ""

python scripts/prepare_game_features_complete.py \
  --seasons 2021-22 2022-23 2023-24 2024-25 \
  --output data/game_features.csv \
  --min-games 10

if [ $? -ne 0 ]; then
    echo "❌ Phase 1 failed"
    exit 1
fi

echo ""
echo "✓ Phase 1 complete: data/game_features.csv created"
echo ""
read -p "Continue to Phase 2? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi

echo ""
echo "======================================================================"
echo "PHASE 2: Ensemble Model Training"
echo "======================================================================"
echo "Training LR + RF + XGBoost ensemble..."
echo "Estimated time: 2-3 hours"
echo ""

python scripts/train_game_outcome_model.py \
  --features data/game_features.csv \
  --output models/

if [ $? -ne 0 ]; then
    echo "❌ Phase 2 failed"
    exit 1
fi

echo ""
echo "✓ Phase 2 complete: models/ensemble_game_outcome_model.pkl created"
echo ""
read -p "Continue to Phase 3? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi

echo ""
echo "======================================================================"
echo "PHASE 3: Historical Backtesting"
echo "======================================================================"
echo "Generating calibration training data (2023-24 season)..."
echo "Estimated time: 2-3 hours"
echo ""

python scripts/backtest_historical_games.py \
  --features data/game_features.csv \
  --model models/ensemble_game_outcome_model.pkl \
  --calibration-season 2023-24 \
  --output data/calibration_training_data.csv \
  --plots-dir plots/

if [ $? -ne 0 ]; then
    echo "❌ Phase 3 failed"
    exit 1
fi

echo ""
echo "✓ Phase 3 complete: data/calibration_training_data.csv created"
echo ""
read -p "Continue to Phase 4? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi

echo ""
echo "======================================================================"
echo "PHASE 4: Kelly Calibrator Training"
echo "======================================================================"
echo "Training Bayesian calibrator..."
echo "Estimated time: 1-2 hours"
echo ""

python scripts/train_kelly_calibrator.py \
  --data data/calibration_training_data.csv \
  --calibrator-type bayesian \
  --output models/ \
  --plots-dir plots/

if [ $? -ne 0 ]; then
    echo "❌ Phase 4 failed"
    exit 1
fi

echo ""
echo "✓ Phase 4 complete: models/calibrated_kelly_engine.pkl created"
echo ""
read -p "Continue to Phase 5? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi

echo ""
echo "======================================================================"
echo "PHASE 5: System Validation"
echo "======================================================================"
echo "Running comprehensive validation tests..."
echo "Estimated time: 2-3 hours"
echo ""

python scripts/test_calibrated_system.py \
  --features data/game_features.csv \
  --engine models/calibrated_kelly_engine.pkl \
  --output reports/

if [ $? -ne 0 ]; then
    echo "❌ Phase 5 failed"
    exit 1
fi

echo ""
echo "✓ Phase 5 complete: reports/validation_report.json created"
echo ""

echo ""
echo "======================================================================"
echo "PHASE 6: Summary & Next Steps"
echo "======================================================================"
echo ""
echo "🎉 ALL PHASES COMPLETE!"
echo ""
echo "Generated artifacts:"
echo "  ✓ data/game_features.csv - 4,200+ games with 50+ features"
echo "  ✓ models/ensemble_game_outcome_model.pkl - Trained ensemble"
echo "  ✓ data/calibration_training_data.csv - 1,393+ predictions"
echo "  ✓ models/calibrated_kelly_engine.pkl - Production model"
echo "  ✓ reports/validation_report.json - Test results"
echo "  ✓ plots/*.png - Diagnostic visualizations"
echo ""
echo "Review validation results:"
echo "  cat reports/validation_report.json | python -m json.tool"
echo ""
echo "Next steps:"
echo "  1. Review plots/ for calibration quality"
echo "  2. Check Brier score < 0.15 in validation report"
echo "  3. Paper trade 50-100 games using production_predict.py"
echo "  4. Go live only after positive CLV validation!"
echo ""
echo "Production prediction example:"
echo "  python scripts/production_predict.py \\"
echo "    --home LAL --away GSW \\"
echo "    --odds 1.9 --away-odds 2.0 \\"
echo "    --bankroll 10000"
echo ""
echo "======================================================================"
echo "Training Complete! 🚀"
echo "======================================================================"
