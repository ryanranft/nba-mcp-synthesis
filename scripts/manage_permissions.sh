#!/bin/bash
# File Permission Management Script

set -e

# Configuration
SECRETS_DIR="/Users/ryanranft/Desktop/++/big_cat_bets_assets"
LOG_FILE="/var/log/secrets_permissions.log"
AUDIT_LOG="/var/log/secrets_audit.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date -u +%Y-%m-%dT%H:%M:%SZ)]${NC} $1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR:${NC} $1" >&2
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR: $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING:${NC} $1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING: $1" >> "$LOG_FILE"
}

# Audit logging
audit_log() {
    local action=$1
    local file=$2
    local user=$3
    local result=$4

    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $action: $file by $user: $result" >> "$AUDIT_LOG"
}

# Set file permissions
set_file_permissions() {
    local file=$1
    local permissions=$2

    if [ -f "$file" ]; then
        chmod "$permissions" "$file"
        log "Set permissions $permissions on $file"
        audit_log "SET_PERMISSIONS" "$file" "$USER" "SUCCESS"
    else
        log_error "File not found: $file"
        audit_log "SET_PERMISSIONS" "$file" "$USER" "FAILED - FILE_NOT_FOUND"
    fi
}

# Set directory permissions
set_directory_permissions() {
    local dir=$1
    local permissions=$2

    if [ -d "$dir" ]; then
        chmod "$permissions" "$dir"
        log "Set permissions $permissions on directory $dir"
        audit_log "SET_DIRECTORY_PERMISSIONS" "$dir" "$USER" "SUCCESS"
    else
        log_error "Directory not found: $dir"
        audit_log "SET_DIRECTORY_PERMISSIONS" "$dir" "$USER" "FAILED - DIRECTORY_NOT_FOUND"
    fi
}

# Set recursive permissions
set_recursive_permissions() {
    local dir=$1
    local file_permissions=$2
    local dir_permissions=$3

    if [ -d "$dir" ]; then
        # Set directory permissions
        find "$dir" -type d -exec chmod "$dir_permissions" {} \;
        log "Set directory permissions $dir_permissions recursively on $dir"

        # Set file permissions
        find "$dir" -type f -exec chmod "$file_permissions" {} \;
        log "Set file permissions $file_permissions recursively on $dir"

        audit_log "SET_RECURSIVE_PERMISSIONS" "$dir" "$USER" "SUCCESS"
    else
        log_error "Directory not found: $dir"
        audit_log "SET_RECURSIVE_PERMISSIONS" "$dir" "$USER" "FAILED - DIRECTORY_NOT_FOUND"
    fi
}

# Check file permissions
check_file_permissions() {
    local file=$1
    local expected_permissions=$2

    if [ -f "$file" ]; then
        local actual_permissions=$(stat -f "%OLp" "$file")
        if [ "$actual_permissions" = "$expected_permissions" ]; then
            log "Permissions OK: $file ($actual_permissions)"
            audit_log "CHECK_PERMISSIONS" "$file" "$USER" "SUCCESS - MATCH"
        else
            log_warning "Permissions mismatch: $file (expected: $expected_permissions, actual: $actual_permissions)"
            audit_log "CHECK_PERMISSIONS" "$file" "$USER" "FAILED - MISMATCH"
        fi
    else
        log_error "File not found: $file"
        audit_log "CHECK_PERMISSIONS" "$file" "$USER" "FAILED - FILE_NOT_FOUND"
    fi
}

# Check directory permissions
check_directory_permissions() {
    local dir=$1
    local expected_permissions=$2

    if [ -d "$dir" ]; then
        local actual_permissions=$(stat -f "%OLp" "$dir")
        if [ "$actual_permissions" = "$expected_permissions" ]; then
            log "Directory permissions OK: $dir ($actual_permissions)"
            audit_log "CHECK_DIRECTORY_PERMISSIONS" "$dir" "$USER" "SUCCESS - MATCH"
        else
            log_warning "Directory permissions mismatch: $dir (expected: $expected_permissions, actual: $actual_permissions)"
            audit_log "CHECK_DIRECTORY_PERMISSIONS" "$dir" "$USER" "FAILED - MISMATCH"
        fi
    else
        log_error "Directory not found: $dir"
        audit_log "CHECK_DIRECTORY_PERMISSIONS" "$dir" "$USER" "FAILED - DIRECTORY_NOT_FOUND"
    fi
}

# Fix permissions
fix_permissions() {
    local dir=$1

    log "Fixing permissions for $dir"

    # Set directory permissions to 700 (owner only)
    set_recursive_permissions "$dir" "600" "700"

    # Set owner to current user
    chown -R "$USER" "$dir"
    log "Set owner to $USER for $dir"

    audit_log "FIX_PERMISSIONS" "$dir" "$USER" "SUCCESS"
}

# Audit permissions
audit_permissions() {
    local dir=$1

    log "Auditing permissions for $dir"

    # Check directory permissions
    check_directory_permissions "$dir" "700"

    # Check file permissions
    find "$dir" -type f -exec check_file_permissions {} "600" \;

    audit_log "AUDIT_PERMISSIONS" "$dir" "$USER" "COMPLETED"
}

# Generate permission report
generate_permission_report() {
    local dir=$1
    local output_file=$2

    log "Generating permission report for $dir"

    {
        echo "Permission Report for $dir"
        echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "Generated by: $USER"
        echo "=================================="
        echo

        echo "Directory Permissions:"
        find "$dir" -type d -exec stat -f "%N: %OLp" {} \;
        echo

        echo "File Permissions:"
        find "$dir" -type f -exec stat -f "%N: %OLp" {} \;
        echo

        echo "Permission Issues:"
        find "$dir" -type d ! -perm 700 -exec echo "Directory: {} (permissions: $(stat -f "%OLp" {}))" \;
        find "$dir" -type f ! -perm 600 -exec echo "File: {} (permissions: $(stat -f "%OLp" {}))" \;

    } > "$output_file"

    log "Permission report generated: $output_file"
    audit_log "GENERATE_REPORT" "$dir" "$USER" "SUCCESS"
}

# Monitor permission changes
monitor_permissions() {
    local dir=$1

    log "Starting permission monitoring for $dir"

    # Use fswatch to monitor file system changes
    if command -v fswatch &> /dev/null; then
        fswatch -o "$dir" | while read f; do
            log "Permission change detected in $dir"
            audit_log "PERMISSION_CHANGE" "$dir" "$USER" "DETECTED"
        done
    else
        log_warning "fswatch not available, cannot monitor permission changes"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  set [file] [perms]     Set permissions on a file"
    echo "  setdir [dir] [perms]   Set permissions on a directory"
    echo "  setrec [dir] [fperms] [dperms]  Set recursive permissions"
    echo "  check [file] [perms]  Check file permissions"
    echo "  checkdir [dir] [perms] Check directory permissions"
    echo "  fix [dir]             Fix permissions for directory"
    echo "  audit [dir]           Audit permissions for directory"
    echo "  report [dir] [file]   Generate permission report"
    echo "  monitor [dir]         Monitor permission changes"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 set /path/to/secret.env 600"
    echo "  $0 setdir /path/to/secrets 700"
    echo "  $0 setrec /path/to/secrets 600 700"
    echo "  $0 check /path/to/secret.env 600"
    echo "  $0 checkdir /path/to/secrets 700"
    echo "  $0 fix /path/to/secrets"
    echo "  $0 audit /path/to/secrets"
    echo "  $0 report /path/to/secrets report.txt"
    echo "  $0 monitor /path/to/secrets"
}

# Main function
main() {
    case "$1" in
        set)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "File and permissions not specified"
                show_help
                exit 1
            fi
            set_file_permissions "$2" "$3"
            ;;
        setdir)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Directory and permissions not specified"
                show_help
                exit 1
            fi
            set_directory_permissions "$2" "$3"
            ;;
        setrec)
            if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
                log_error "Directory, file permissions, and directory permissions not specified"
                show_help
                exit 1
            fi
            set_recursive_permissions "$2" "$3" "$4"
            ;;
        check)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "File and expected permissions not specified"
                show_help
                exit 1
            fi
            check_file_permissions "$2" "$3"
            ;;
        checkdir)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Directory and expected permissions not specified"
                show_help
                exit 1
            fi
            check_directory_permissions "$2" "$3"
            ;;
        fix)
            if [ -z "$2" ]; then
                log_error "Directory not specified"
                show_help
                exit 1
            fi
            fix_permissions "$2"
            ;;
        audit)
            if [ -z "$2" ]; then
                log_error "Directory not specified"
                show_help
                exit 1
            fi
            audit_permissions "$2"
            ;;
        report)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Directory and output file not specified"
                show_help
                exit 1
            fi
            generate_permission_report "$2" "$3"
            ;;
        monitor)
            if [ -z "$2" ]; then
                log_error "Directory not specified"
                show_help
                exit 1
            fi
            monitor_permissions "$2"
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


