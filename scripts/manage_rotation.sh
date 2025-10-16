#!/bin/bash
# Secrets Rotation Utilities Script

set -e

# Configuration
SECRETS_DIR="/Users/ryanranft/Desktop/++/big_cat_bets_assets"
ROTATION_LOG="/var/log/secrets_rotation.log"
BACKUP_DIR="/var/backups/secrets"
ROTATION_SCHEDULE="/etc/cron.d/secrets_rotation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date -u +%Y-%m-%dT%H:%M:%SZ)]${NC} $1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" >> "$ROTATION_LOG"
}

log_error() {
    echo -e "${RED}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR:${NC} $1" >&2
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR: $1" >> "$ROTATION_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING:${NC} $1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING: $1" >> "$ROTATION_LOG"
}

# Initialize rotation system
init_rotation_system() {
    log "Initializing secrets rotation system..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"

    # Create rotation log
    touch "$ROTATION_LOG"
    chmod 600 "$ROTATION_LOG"

    # Create rotation schedule
    cat > "$ROTATION_SCHEDULE" << EOF
# Secrets Rotation Schedule
# Run daily at 2 AM
0 2 * * * $USER $0 rotate-daily
# Run weekly on Sunday at 3 AM
0 3 * * 0 $USER $0 rotate-weekly
# Run monthly on the 1st at 4 AM
0 4 1 * * $USER $0 rotate-monthly
EOF

    chmod 644 "$ROTATION_SCHEDULE"

    log "Secrets rotation system initialized"
}

# Backup secret
backup_secret() {
    local secret_file=$1
    local backup_type=$2

    if [ -f "$secret_file" ]; then
        local backup_file="$BACKUP_DIR/$(basename "$secret_file")_$(date +%Y%m%d_%H%M%S)_$backup_type"
        cp "$secret_file" "$backup_file"
        chmod 600 "$backup_file"
        log "Backed up secret: $secret_file -> $backup_file"
    else
        log_error "Secret file not found: $secret_file"
    fi
}

# Rotate API key
rotate_api_key() {
    local service=$1
    local project=$2
    local context=$3

    log "Rotating API key for $service in $project ($context)..."

    # Find the secret file
    local secret_file=$(find "$SECRETS_DIR" -name "*${service}_API_KEY_${project}_${context}.env" -type f)

    if [ -n "$secret_file" ]; then
        # Backup the current secret
        backup_secret "$secret_file" "pre_rotation"

        # Generate new API key (this would be service-specific)
        local new_key=$(generate_new_api_key "$service")

        if [ -n "$new_key" ]; then
            # Update the secret file
            echo "$new_key" > "$secret_file"
            chmod 600 "$secret_file"

            # Backup the new secret
            backup_secret "$secret_file" "post_rotation"

            log "Successfully rotated API key for $service"

            # Notify about rotation
            notify_rotation "$service" "$project" "$context" "SUCCESS"
        else
            log_error "Failed to generate new API key for $service"
            notify_rotation "$service" "$project" "$context" "FAILED"
        fi
    else
        log_error "Secret file not found for $service in $project ($context)"
    fi
}

# Generate new API key
generate_new_api_key() {
    local service=$1

    case "$service" in
        GOOGLE)
            # This would call Google Cloud API to generate a new key
            echo "new_google_api_key_$(date +%s)"
            ;;
        ANTHROPIC)
            # This would call Anthropic API to generate a new key
            echo "new_anthropic_api_key_$(date +%s)"
            ;;
        DEEPSEEK)
            # This would call DeepSeek API to generate a new key
            echo "new_deepseek_api_key_$(date +%s)"
            ;;
        OPENAI)
            # This would call OpenAI API to generate a new key
            echo "new_openai_api_key_$(date +%s)"
            ;;
        *)
            log_error "Unknown service: $service"
            return 1
            ;;
    esac
}

# Notify about rotation
notify_rotation() {
    local service=$1
    local project=$2
    local context=$3
    local result=$4

    # Send notification to Slack
    local message="Secrets Rotation: $service API key for $project ($context): $result"

    # This would send to Slack webhook
    if [ -n "$SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW"
    fi

    log "Notification sent: $message"
}

# Rotate all API keys
rotate_all_api_keys() {
    local project=$1
    local context=$2

    log "Rotating all API keys for $project ($context)..."

    local services=("GOOGLE" "ANTHROPIC" "DEEPSEEK" "OPENAI")

    for service in "${services[@]}"; do
        rotate_api_key "$service" "$project" "$context"
        sleep 5  # Wait between rotations
    done

    log "Completed rotation of all API keys for $project ($context)"
}

# Daily rotation
rotate_daily() {
    log "Starting daily rotation..."

    # Rotate development API keys
    rotate_all_api_keys "NBA_MCP_SYNTHESIS" "DEVELOPMENT"

    log "Daily rotation completed"
}

# Weekly rotation
rotate_weekly() {
    log "Starting weekly rotation..."

    # Rotate test API keys
    rotate_all_api_keys "NBA_MCP_SYNTHESIS" "TEST"

    log "Weekly rotation completed"
}

# Monthly rotation
rotate_monthly() {
    log "Starting monthly rotation..."

    # Rotate production API keys
    rotate_all_api_keys "NBA_MCP_SYNTHESIS" "WORKFLOW"

    log "Monthly rotation completed"
}

# Clean old backups
clean_old_backups() {
    local retention_days=$1

    log "Cleaning old backups (retention: $retention_days days)..."

    find "$BACKUP_DIR" -name "*.env_*" -mtime +$retention_days -delete

    log "Old backups cleaned"
}

# Restore from backup
restore_from_backup() {
    local secret_file=$1
    local backup_file=$2

    if [ -f "$backup_file" ]; then
        cp "$backup_file" "$secret_file"
        chmod 600 "$secret_file"
        log "Restored secret from backup: $backup_file -> $secret_file"
    else
        log_error "Backup file not found: $backup_file"
    fi
}

# List available backups
list_backups() {
    local secret_name=$1

    log "Listing backups for: $secret_name"

    find "$BACKUP_DIR" -name "*${secret_name}*" -type f | sort -r
}

# Show rotation status
show_rotation_status() {
    log "Secrets rotation status:"

    echo "Rotation Schedule:"
    cat "$ROTATION_SCHEDULE"
    echo

    echo "Recent Rotations:"
    tail -20 "$ROTATION_LOG"
    echo

    echo "Backup Directory:"
    ls -la "$BACKUP_DIR"
    echo

    echo "Next Rotation:"
    # This would show when the next rotation is scheduled
    echo "Daily: $(date -d 'tomorrow 2:00')"
    echo "Weekly: $(date -d 'next sunday 3:00')"
    echo "Monthly: $(date -d 'next month 1st 4:00')"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  init                    Initialize rotation system"
    echo "  rotate [service] [project] [context]  Rotate specific API key"
    echo "  rotate-all [project] [context]  Rotate all API keys"
    echo "  rotate-daily            Run daily rotation"
    echo "  rotate-weekly           Run weekly rotation"
    echo "  rotate-monthly          Run monthly rotation"
    echo "  backup [file] [type]    Backup secret file"
    echo "  restore [file] [backup] Restore from backup"
    echo "  list-backups [name]     List available backups"
    echo "  clean [days]            Clean old backups"
    echo "  status                  Show rotation status"
    echo "  help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 rotate GOOGLE NBA_MCP_SYNTHESIS WORKFLOW"
    echo "  $0 rotate-all NBA_MCP_SYNTHESIS DEVELOPMENT"
    echo "  $0 rotate-daily"
    echo "  $0 rotate-weekly"
    echo "  $0 rotate-monthly"
    echo "  $0 backup /path/to/secret.env pre_rotation"
    echo "  $0 restore /path/to/secret.env /path/to/backup.env"
    echo "  $0 list-backups GOOGLE_API_KEY"
    echo "  $0 clean 30"
    echo "  $0 status"
}

# Main function
main() {
    case "$1" in
        init)
            init_rotation_system
            ;;
        rotate)
            if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
                log_error "Service, project, and context not specified"
                show_help
                exit 1
            fi
            rotate_api_key "$2" "$3" "$4"
            ;;
        rotate-all)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Project and context not specified"
                show_help
                exit 1
            fi
            rotate_all_api_keys "$2" "$3"
            ;;
        rotate-daily)
            rotate_daily
            ;;
        rotate-weekly)
            rotate_weekly
            ;;
        rotate-monthly)
            rotate_monthly
            ;;
        backup)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "File and backup type not specified"
                show_help
                exit 1
            fi
            backup_secret "$2" "$3"
            ;;
        restore)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "File and backup file not specified"
                show_help
                exit 1
            fi
            restore_from_backup "$2" "$3"
            ;;
        list-backups)
            if [ -z "$2" ]; then
                log_error "Secret name not specified"
                show_help
                exit 1
            fi
            list_backups "$2"
            ;;
        clean)
            if [ -z "$2" ]; then
                log_error "Retention days not specified"
                show_help
                exit 1
            fi
            clean_old_backups "$2"
            ;;
        status)
            show_rotation_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

