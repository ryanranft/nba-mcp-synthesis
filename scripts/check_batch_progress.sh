#!/bin/bash
# Monitor batch feature generation progress

LOG_FILE="logs/batch_feature_generation.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

# Check if process is running
if ps aux | grep "prepare_game_features_complete.py" | grep -v grep > /dev/null; then
    echo "✅ Batch feature generation is RUNNING"
    echo
else
    echo "⚠️  Process not running (may have completed or failed)"
    echo
fi

# Show latest progress
echo "Latest Progress:"
echo "================================================================================"
tail -20 "$LOG_FILE" | grep -E "Processing games:|✓|✅|❌|Error" || tail -20 "$LOG_FILE"
echo

# Estimate completion
if grep -q "Processing games:" "$LOG_FILE"; then
    LAST_LINE=$(tail -50 "$LOG_FILE" | grep "Processing games:" | tail -1)
    if echo "$LAST_LINE" | grep -q "%"; then
        PERCENT=$(echo "$LAST_LINE" | sed 's/.*Processing games: *\([0-9]*\)%.*/\1/')
        if [ ! -z "$PERCENT" ] && [ "$PERCENT" -gt 0 ]; then
            REMAINING=$((100 - PERCENT))
            # Estimate at 5.5s per game average
            GAMES_DONE=$((4621 * PERCENT / 100))
            GAMES_LEFT=$((4621 - GAMES_DONE))
            SECONDS_LEFT=$((GAMES_LEFT * 6))
            HOURS_LEFT=$(echo "scale=1; $SECONDS_LEFT / 3600" | bc)

            echo "Progress: $PERCENT% complete"
            echo "Games processed: ~$GAMES_DONE / 4621"
            echo "Estimated time remaining: ~${HOURS_LEFT} hours"
        fi
    fi
fi

echo
echo "To view full log:"
echo "  tail -f logs/batch_feature_generation.log"
echo
echo "To check if complete:"
echo "  ls -lh data/game_features_with_players.csv"
