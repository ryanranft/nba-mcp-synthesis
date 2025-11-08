#!/bin/bash
# Quick Status Check - Phase 1 Player Features
#
# Shows at-a-glance status of all Phase 1 components

echo "================================================================================"
echo "Phase 1 Player Features - Quick Status Check"
echo "================================================================================"
echo

# Check if batch is running
echo "Batch Feature Generation:"
echo "--------------------------------------------------------------------------------"
if ps aux | grep "prepare_game_features_complete.py" | grep -v grep > /dev/null; then
    echo "Status: ✅ RUNNING"

    # Get latest progress
    if [ -f logs/batch_feature_generation.log ]; then
        LAST_LINE=$(tail -50 logs/batch_feature_generation.log | grep "Processing games:" | tail -1)
        if echo "$LAST_LINE" | grep -q "%"; then
            PERCENT=$(echo "$LAST_LINE" | sed 's/.*Processing games: *\([0-9]*\)%.*/\1/')
            echo "Progress: $PERCENT%"

            GAMES_DONE=$((4621 * PERCENT / 100))
            echo "Games: ~$GAMES_DONE / 4621"
        fi
    fi
else
    echo "Status: ⏸️  NOT RUNNING"

    # Check if output file exists
    if [ -f data/game_features_with_players.csv ]; then
        ROWS=$(wc -l < data/game_features_with_players.csv)
        echo "Output: ✅ COMPLETE ($ROWS rows)"
    else
        echo "Output: ❌ NOT FOUND"
    fi
fi

echo

# Check infrastructure files
echo "Infrastructure:"
echo "--------------------------------------------------------------------------------"

FILES=(
    "mcp_server/betting/feature_extractors/player_features.py:Player features extractor"
    "mcp_server/betting/feature_extractors/roster_metrics.py:Roster metrics utils"
    "scripts/test_player_features.py:Validation test"
    "scripts/validate_batch_output.py:Batch output validator"
    "scripts/retrain_with_player_features.sh:Retraining pipeline"
)

for entry in "${FILES[@]}"; do
    FILE="${entry%%:*}"
    DESC="${entry##*:}"

    if [ -f "$FILE" ]; then
        echo "✅ $DESC"
    else
        echo "❌ $DESC (missing: $FILE)"
    fi
done

echo

# Check models
echo "Models:"
echo "--------------------------------------------------------------------------------"

if [ -f models/game_outcome_ensemble.pkl ]; then
    SIZE=$(ls -lh models/game_outcome_ensemble.pkl | awk '{print $5}')
    TIMESTAMP=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" models/game_outcome_ensemble.pkl 2>/dev/null || stat -c "%y" models/game_outcome_ensemble.pkl 2>/dev/null | cut -d' ' -f1,2 | cut -d':' -f1,2)
    echo "Current model: ✅ models/game_outcome_ensemble.pkl ($SIZE, $TIMESTAMP)"
else
    echo "Current model: ❌ NOT FOUND"
fi

if [ -f models/ensemble_with_players.pkl ]; then
    SIZE=$(ls -lh models/ensemble_with_players.pkl | awk '{print $5}')
    echo "New model: ✅ models/ensemble_with_players.pkl ($SIZE)"
else
    echo "New model: ⏸️  Not trained yet"
fi

echo

# Next steps
echo "Next Steps:"
echo "--------------------------------------------------------------------------------"

if [ -f data/game_features_with_players.csv ]; then
    echo "1. ✅ Batch generation complete"
    echo "2. ⏸️  Run: ./scripts/retrain_with_player_features.sh"
    echo "3. ⏸️  Review model performance"
    echo "4. ⏸️  Deploy if improvement > 2%"
elif ps aux | grep "prepare_game_features_complete.py" | grep -v grep > /dev/null; then
    echo "1. 🔄 Wait for batch generation (~7.6 hours)"
    echo "2. ⏸️  Validate output: python scripts/validate_batch_output.py"
    echo "3. ⏸️  Retrain model: ./scripts/retrain_with_player_features.sh"
    echo "4. ⏸️  Deploy if successful"
else
    echo "⚠️  Batch generation not running and no output found"
    echo "   Start batch: nohup python3 scripts/prepare_game_features_complete.py \\"
    echo "                --seasons 2021-22 2022-23 2023-24 2024-25 \\"
    echo "                --output data/game_features_with_players.csv \\"
    echo "                > logs/batch_feature_generation.log 2>&1 &"
fi

echo
echo "================================================================================"
echo "For detailed progress: ./scripts/check_batch_progress.sh"
echo "For batch log: tail -f logs/batch_feature_generation.log"
echo "================================================================================"
