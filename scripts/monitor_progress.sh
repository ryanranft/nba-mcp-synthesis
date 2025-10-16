#!/bin/bash

# NBA MCP Synthesis - Background Monitoring Script
# Runs in the background to monitor progress and send updates

set -e

# Configuration
LOG_FILE="logs/monitor_$(date +%Y%m%d_%H%M%S).log"
PROGRESS_FILE="analysis_results/multi_pass_progress.json"
MASTER_RECS_FILE="analysis_results/master_recommendations.json"
INTEGRATION_FILE="integration_summary.md"

# Create logs directory
mkdir -p logs

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check deployment status
check_status() {
    if pgrep -f "deploy_book_analysis.py" > /dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

# Function to get current progress
get_progress() {
    if [ -f "$PROGRESS_FILE" ]; then
        CURRENT_PASS=$(jq -r '.current_pass // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")
        OVERALL_STATUS=$(jq -r '.overall_status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")

        # Get pass-specific progress
        PASS1_STATUS=$(jq -r '.pass_1.status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")
        PASS2_STATUS=$(jq -r '.pass_2.status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")
        PASS3_STATUS=$(jq -r '.pass_3.status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")
        PASS4_STATUS=$(jq -r '.pass_4.status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")

        echo "Pass $CURRENT_PASS | Overall: $OVERALL_STATUS | P1:$PASS1_STATUS P2:$PASS2_STATUS P3:$PASS3_STATUS P4:$PASS4_STATUS"
    else
        echo "No progress file found"
    fi
}

# Function to get recommendation count
get_recommendation_count() {
    if [ -f "$MASTER_RECS_FILE" ]; then
        jq '.recommendations | length' "$MASTER_RECS_FILE" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Function to generate status update
generate_status_update() {
    STATUS=$(check_status)
    PROGRESS=$(get_progress)
    REC_COUNT=$(get_recommendation_count)

    cat << EOF
🚀 NBA MCP Synthesis Status Update
================================
📅 Time: $(date)
🔄 Status: $STATUS
📊 Progress: $PROGRESS
📋 Recommendations: $REC_COUNT

EOF
}

# Main monitoring loop
main() {
    log "🔍 Starting background monitoring..."

    while true; do
        STATUS=$(check_status)

        if [ "$STATUS" = "running" ]; then
            # Generate status update every 5 minutes
            generate_status_update >> "$LOG_FILE"

            # Check for completion
            if [ -f "$PROGRESS_FILE" ]; then
                OVERALL_STATUS=$(jq -r '.overall_status // "unknown"' "$PROGRESS_FILE" 2>/dev/null || echo "unknown")

                if [ "$OVERALL_STATUS" = "completed" ]; then
                    log "🎉 Deployment completed successfully!"
                    log "📄 Generating final summary..."

                    # Generate final summary
                    generate_status_update

                    log "✅ Monitoring complete - you can check the results!"
                    break
                elif [ "$OVERALL_STATUS" = "failed" ]; then
                    log "❌ Deployment failed - check logs for details"
                    break
                fi
            fi
        else
            log "⏸️  Deployment not running, waiting..."
        fi

        sleep 300  # Check every 5 minutes
    done
}

# Run main function
main "$@"




