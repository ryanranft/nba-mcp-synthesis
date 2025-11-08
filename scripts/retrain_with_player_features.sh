#!/bin/bash
# Retrain Ensemble Model with Player Features
#
# This script runs the complete retraining pipeline after batch feature generation completes.
#
# Usage:
#   ./scripts/retrain_with_player_features.sh

set -e  # Exit on error

echo "================================================================================"
echo "Ensemble Model Retraining with Player Features"
echo "================================================================================"
echo

# Configuration
FEATURES_FILE="data/game_features_with_players.csv"
MODEL_OUTPUT_DIR="models/ensemble_130features"
CALIBRATOR_OUTPUT_DIR="models/calibrated_130features"
BACKUP_CURRENT="models/ensemble_game_outcome_model_83features_$(date +%Y%m%d_%H%M%S).pkl"
BACKUP_CALIBRATOR="models/calibrated_kelly_engine_83features_$(date +%Y%m%d_%H%M%S).pkl"
CURRENT_MODEL="models/ensemble_game_outcome_model.pkl"
CURRENT_CALIBRATOR="models/calibrated_kelly_engine.pkl"
CALIBRATION_DATA="data/calibration_130features.csv"

# Step 1: Validate batch output
echo "Step 1: Validating batch feature output..."
echo "--------------------------------------------------------------------------------"
python3 scripts/validate_batch_output.py --file "$FEATURES_FILE"

if [ $? -ne 0 ]; then
    echo
    echo "❌ Validation failed! Please check batch output."
    exit 1
fi

echo
echo "✅ Validation passed"
echo

# Step 2: Backup current models
echo "Step 2: Backing up current models..."
echo "--------------------------------------------------------------------------------"

if [ -f "$CURRENT_MODEL" ]; then
    cp "$CURRENT_MODEL" "$BACKUP_CURRENT"
    echo "✅ Ensemble model backed up to: $BACKUP_CURRENT"
else
    echo "⚠️  No current ensemble model found to backup"
fi

if [ -f "$CURRENT_CALIBRATOR" ]; then
    cp "$CURRENT_CALIBRATOR" "$BACKUP_CALIBRATOR"
    echo "✅ Calibrator backed up to: $BACKUP_CALIBRATOR"
else
    echo "⚠️  No current calibrator found to backup"
fi

# Create output directories
mkdir -p "$MODEL_OUTPUT_DIR"
mkdir -p "$CALIBRATOR_OUTPUT_DIR"

echo

# Step 3: Train new ensemble model
echo "Step 3: Training new ensemble model with player features..."
echo "--------------------------------------------------------------------------------"

python3 scripts/train_game_outcome_model.py \
    --features "$FEATURES_FILE" \
    --output "$MODEL_OUTPUT_DIR/"

if [ $? -ne 0 ]; then
    echo
    echo "❌ Training failed!"
    exit 1
fi

echo
echo "✅ Ensemble training completed"
echo

# Step 4: Generate calibration data
echo "Step 4: Generating calibration data from backtest..."
echo "--------------------------------------------------------------------------------"

python3 scripts/backtest_historical_games.py \
    --features "$FEATURES_FILE" \
    --model "$MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl" \
    --calibration-season 2023-24 \
    --output "$CALIBRATION_DATA"

if [ $? -ne 0 ]; then
    echo
    echo "❌ Calibration data generation failed!"
    exit 1
fi

echo
echo "✅ Calibration data generated"
echo

# Step 5: Train Kelly calibrator
echo "Step 5: Training Kelly Criterion calibrator..."
echo "--------------------------------------------------------------------------------"

python3 scripts/train_kelly_calibrator.py \
    --data "$CALIBRATION_DATA" \
    --output "$CALIBRATOR_OUTPUT_DIR/" \
    --calibrator-type bayesian

if [ $? -ne 0 ]; then
    echo
    echo "❌ Calibrator training failed!"
    exit 1
fi

echo
echo "✅ Calibrator training completed"
echo

# Step 6: Compare models
echo "Step 6: Comparing old vs new model performance..."
echo "--------------------------------------------------------------------------------"

if [ -f "$BACKUP_CURRENT" ]; then
    echo "Old Model (83 features):"
    echo "  Ensemble: $BACKUP_CURRENT"
    echo "  Calibrator: $BACKUP_CALIBRATOR"
    echo

    echo "New Model (130 features):"
    echo "  Ensemble: $MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl"
    echo "  Calibrator: $CALIBRATOR_OUTPUT_DIR/calibrated_kelly_engine.pkl"
    echo

    echo "⚠️  Manual comparison required - check training output above for:"
    echo "   - Test accuracy improvement (must be ≥2%)"
    echo "   - Brier score improvement (must decrease)"
    echo "   - Log loss improvement (must decrease)"
else
    echo "⚠️  No old model to compare"
fi

echo

# Step 7: Deployment decision
echo "================================================================================"
echo "RETRAINING COMPLETE"
echo "================================================================================"
echo
echo "New models trained:"
echo "  Ensemble: $MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl"
echo "  Calibrator: $CALIBRATOR_OUTPUT_DIR/calibrated_kelly_engine.pkl"
echo
echo "Next steps:"
echo "  1. Review training metrics above"
echo "  2. If accuracy improved by ≥2%, proceed with deployment:"
echo
echo "     # Deploy new ensemble model"
echo "     cp $MODEL_OUTPUT_DIR/ensemble_game_outcome_model.pkl $CURRENT_MODEL"
echo
echo "     # Deploy new calibrator"
echo "     cp $CALIBRATOR_OUTPUT_DIR/calibrated_kelly_engine.pkl $CURRENT_CALIBRATOR"
echo
echo "     # Update metadata"
echo "     cp $MODEL_OUTPUT_DIR/model_metadata.json models/"
echo
echo "  3. Test live predictions:"
echo
echo "     python scripts/paper_trade_today.py --dry-run"
echo
echo "  4. Run backtest validation:"
echo
echo "     python scripts/backtest_historical_games.py \\"
echo "         --features $FEATURES_FILE \\"
echo "         --model $CURRENT_MODEL \\"
echo "         --calibration-season 2023-24"
echo

echo "To rollback if needed:"
echo "  cp $BACKUP_CURRENT $CURRENT_MODEL"
echo "  cp $BACKUP_CALIBRATOR $CURRENT_CALIBRATOR"
echo
