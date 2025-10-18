#!/bin/bash
# NBA MCP Secrets Permission Audit Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECRETS_BASE_PATH="/Users/ryanranft/Desktop/++/big_cat_bets_assets"
REPORT_FILE="secrets_permission_audit_$(date +%Y%m%d_%H%M%S).txt"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Initialize counters
total_files=0
secure_files=0
insecure_files=0
total_dirs=0
secure_dirs=0
insecure_dirs=0

# Function to check file permissions
check_file_permissions() {
    local file="$1"
    local perms=$(stat -f "%OLp" "$file" 2>/dev/null || echo "000")
    local owner=$(stat -f "%Su" "$file" 2>/dev/null || echo "unknown")
    local group=$(stat -f "%Sg" "$file" 2>/dev/null || echo "unknown")

    total_files=$((total_files + 1))

    # Check if file is secure (600 or more restrictive)
    if [[ "$perms" == "600" ]] || [[ "$perms" == "400" ]] || [[ "$perms" == "000" ]]; then
        secure_files=$((secure_files + 1))
        echo "✅ $file (perms: $perms, owner: $owner, group: $group)" >> "$REPORT_FILE"
    else
        insecure_files=$((insecure_files + 1))
        echo "❌ $file (perms: $perms, owner: $owner, group: $group) - INSECURE" >> "$REPORT_FILE"
        log_warn "Insecure file: $file (permissions: $perms)"
    fi
}

# Function to check directory permissions
check_dir_permissions() {
    local dir="$1"
    local perms=$(stat -f "%OLp" "$dir" 2>/dev/null || echo "000")
    local owner=$(stat -f "%Su" "$dir" 2>/dev/null || echo "unknown")
    local group=$(stat -f "%Sg" "$dir" 2>/dev/null || echo "unknown")

    total_dirs=$((total_dirs + 1))

    # Check if directory is secure (700 or more restrictive)
    if [[ "$perms" == "700" ]] || [[ "$perms" == "600" ]] || [[ "$perms" == "400" ]] || [[ "$perms" == "000" ]]; then
        secure_dirs=$((secure_dirs + 1))
        echo "✅ $dir/ (perms: $perms, owner: $owner, group: $group)" >> "$REPORT_FILE"
    else
        insecure_dirs=$((insecure_dirs + 1))
        echo "❌ $dir/ (perms: $perms, owner: $owner, group: $group) - INSECURE" >> "$REPORT_FILE"
        log_warn "Insecure directory: $dir (permissions: $perms)"
    fi
}

# Function to audit a directory
audit_directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        log_error "Directory not found: $dir"
        return 1
    fi

    log "Auditing directory: $dir"

    # Check directory permissions
    check_dir_permissions "$dir"

    # Find all .env files recursively
    while IFS= read -r -d '' file; do
        check_file_permissions "$file"
    done < <(find "$dir" -name "*.env" -type f -print0)

    # Find all .env directories recursively
    while IFS= read -r -d '' env_dir; do
        check_dir_permissions "$env_dir"
    done < <(find "$dir" -name ".env.*" -type d -print0)
}

# Function to fix insecure permissions
fix_permissions() {
    local fix_mode="$1"

    if [[ "$fix_mode" != "fix" ]]; then
        return 0
    fi

    log "🔧 Fixing insecure permissions..."

    # Fix insecure files
    while IFS= read -r -d '' file; do
        if [[ -f "$file" ]]; then
            chmod 600 "$file"
            log_info "Fixed file permissions: $file"
        fi
    done < <(find "$SECRETS_BASE_PATH" -name "*.env" -type f -print0)

    # Fix insecure directories
    while IFS= read -r -d '' dir; do
        if [[ -d "$dir" ]]; then
            chmod 700 "$dir"
            log_info "Fixed directory permissions: $dir"
        fi
    done < <(find "$SECRETS_BASE_PATH" -name ".env.*" -type d -print0)

    log "✅ Permission fixes applied"
}

# Function to generate summary report
generate_summary() {
    local fix_mode="$1"

    echo "" >> "$REPORT_FILE"
    echo "===========================================" >> "$REPORT_FILE"
    echo "AUDIT SUMMARY" >> "$REPORT_FILE"
    echo "===========================================" >> "$REPORT_FILE"
    echo "Audit Date: $(date)" >> "$REPORT_FILE"
    echo "Secrets Base Path: $SECRETS_BASE_PATH" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "FILES:" >> "$REPORT_FILE"
    echo "  Total files checked: $total_files" >> "$REPORT_FILE"
    echo "  Secure files: $secure_files" >> "$REPORT_FILE"
    echo "  Insecure files: $insecure_files" >> "$REPORT_FILE"
    echo "  Security rate: $(( secure_files * 100 / total_files ))%" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "DIRECTORIES:" >> "$REPORT_FILE"
    echo "  Total directories checked: $total_dirs" >> "$REPORT_FILE"
    echo "  Secure directories: $secure_dirs" >> "$REPORT_FILE"
    echo "  Insecure directories: $insecure_dirs" >> "$REPORT_FILE"
    echo "  Security rate: $(( secure_dirs * 100 / total_dirs ))%" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    if [[ "$fix_mode" == "fix" ]]; then
        echo "ACTIONS TAKEN:" >> "$REPORT_FILE"
        echo "  - Fixed file permissions to 600" >> "$REPORT_FILE"
        echo "  - Fixed directory permissions to 700" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi

    echo "RECOMMENDATIONS:" >> "$REPORT_FILE"
    echo "  - All .env files should have 600 permissions (owner read/write only)" >> "$REPORT_FILE"
    echo "  - All .env directories should have 700 permissions (owner read/write/execute only)" >> "$REPORT_FILE"
    echo "  - Run this audit regularly to ensure security" >> "$REPORT_FILE"
    echo "  - Consider using 'chmod 600' for files and 'chmod 700' for directories" >> "$REPORT_FILE"
}

# Main function
main() {
    local fix_mode="$1"

    log "🔍 Starting NBA MCP Secrets Permission Audit..."
    log "Secrets base path: $SECRETS_BASE_PATH"

    if [[ "$fix_mode" == "fix" ]]; then
        log "🔧 Fix mode enabled - will attempt to fix insecure permissions"
    else
        log "📊 Audit mode - will only report issues"
    fi

    # Initialize report file
    echo "NBA MCP Secrets Permission Audit Report" > "$REPORT_FILE"
    echo "Generated: $(date)" >> "$REPORT_FILE"
    echo "Secrets Base Path: $SECRETS_BASE_PATH" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "===========================================" >> "$REPORT_FILE"
    echo "DETAILED FINDINGS" >> "$REPORT_FILE"
    echo "===========================================" >> "$REPORT_FILE"

    # Check if secrets base path exists
    if [[ ! -d "$SECRETS_BASE_PATH" ]]; then
        log_error "Secrets base path not found: $SECRETS_BASE_PATH"
        exit 1
    fi

    # Audit the secrets directory
    audit_directory "$SECRETS_BASE_PATH"

    # Fix permissions if requested
    fix_permissions "$fix_mode"

    # Generate summary
    generate_summary "$fix_mode"

    # Display results
    log "📊 Audit complete!"
    log "📁 Report saved to: $REPORT_FILE"
    echo ""
    log "📈 SUMMARY:"
    log "  Files: $secure_files/$total_files secure ($(( secure_files * 100 / total_files ))%)"
    log "  Directories: $secure_dirs/$total_dirs secure ($(( secure_dirs * 100 / total_dirs ))%)"
    echo ""

    if [[ $insecure_files -gt 0 ]] || [[ $insecure_dirs -gt 0 ]]; then
        log_warn "⚠️  Found $insecure_files insecure files and $insecure_dirs insecure directories"
        log "🔧 To fix permissions, run: $0 fix"
    else
        log "✅ All permissions are secure!"
    fi

    echo ""
    log "📋 To view detailed report: cat $REPORT_FILE"
}

# Check arguments
if [[ "$1" == "fix" ]]; then
    main "fix"
elif [[ "$1" == "help" ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "NBA MCP Secrets Permission Audit Script"
    echo ""
    echo "Usage: $0 [fix|help]"
    echo ""
    echo "Commands:"
    echo "  (no args)  - Run audit and report issues"
    echo "  fix        - Run audit and fix insecure permissions"
    echo "  help       - Show this help message"
    echo ""
    echo "This script audits file and directory permissions for NBA MCP secrets."
    echo "It ensures that .env files have 600 permissions and .env directories have 700 permissions."
else
    main "audit"
fi


