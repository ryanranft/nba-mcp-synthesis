#!/bin/bash

# NBA MCP Synthesis - Phase 2: Secrets Migration
# This script migrates local secrets to AWS Secrets Manager

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/nba-mcp-phase2-secrets.log"

# Default values
DRY_RUN=false
VERBOSE=false
BACKUP_DIR=""
VERIFY_ONLY=false

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
NBA MCP Synthesis - Phase 2: Secrets Migration

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -d, --dry-run          Show what would be done without executing
    -v, --verbose          Enable verbose output
    -b, --backup-dir DIR   Custom backup directory (default: auto-generated)
    --verify-only          Only verify existing migration, don't migrate
    -h, --help            Show this help message

EXAMPLES:
    $0                                    # Standard migration
    $0 --dry-run                          # Preview migration
    $0 --verify-only                      # Verify existing migration
    $0 --backup-dir /custom/backup        # Use custom backup directory

DESCRIPTION:
    This script migrates local secrets to AWS Secrets Manager:
    1. Backs up current local secrets
    2. Runs migration dry-run
    3. Executes actual migration
    4. Verifies migration success
    5. Configures External Secrets Operator

REQUIREMENTS:
    - AWS CLI configured with Secrets Manager permissions
    - Local secrets exist in expected locations
    - External Secrets Operator installed (from Phase 1)

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -b|--backup-dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            --verify-only)
                VERIFY_ONLY=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Validation functions
validate_prerequisites() {
    log "Validating prerequisites..."

    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        log "Please run: aws configure"
        exit 1
    fi

    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    log_success "AWS credentials valid (Account: $account_id)"

    # Check AWS Secrets Manager permissions
    if ! aws secretsmanager list-secrets >/dev/null 2>&1; then
        log_error "AWS Secrets Manager permissions not available"
        log "Please ensure your AWS credentials have Secrets Manager permissions"
        exit 1
    fi

    log_success "AWS Secrets Manager permissions verified"

    # Check local secrets exist
    local secrets_dir="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"

    if [[ ! -d "$secrets_dir" ]]; then
        log_error "Local secrets directory not found: $secrets_dir"
        log "Please ensure local secrets are in the expected location"
        exit 1
    fi

    local production_secrets="$secrets_dir/.env.nba_mcp_synthesis.production"
    if [[ ! -f "$production_secrets" ]]; then
        log_error "Production secrets file not found: $production_secrets"
        exit 1
    fi

    log_success "Local secrets found"

    # Check External Secrets Operator
    if ! kubectl get pods -n external-secrets-system >/dev/null 2>&1; then
        log_error "External Secrets Operator not found"
        log "Please run Phase 1 first: ./scripts/deploy_phase1_infrastructure.sh"
        exit 1
    fi

    log_success "External Secrets Operator is available"
}

# Backup functions
create_backup() {
    log "Creating backup of local secrets..."

    if [[ -z "$BACKUP_DIR" ]]; then
        BACKUP_DIR="backups/secrets/$(date +%Y%m%d-%H%M%S)"
    fi

    mkdir -p "$BACKUP_DIR"

    local secrets_dir="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would backup secrets to $BACKUP_DIR"
        return 0
    fi

    # Backup all environment files
    cp -r "$secrets_dir" "$BACKUP_DIR/"

    # Verify backup
    if [[ -f "$BACKUP_DIR/nba-mcp-synthesis/.env.nba_mcp_synthesis.production" ]]; then
        log_success "Secrets backed up to $BACKUP_DIR"
    else
        log_error "Backup verification failed"
        exit 1
    fi
}

# Migration functions
run_migration_dry_run() {
    log "Running migration dry-run..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute migration dry-run"
        return 0
    fi

    cd "$PROJECT_ROOT"

    if python3 scripts/migrate_secrets_to_aws.py --dry-run; then
        log_success "Migration dry-run completed successfully"
    else
        log_error "Migration dry-run failed"
        exit 1
    fi
}

run_migration() {
    log "Executing secrets migration..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute actual migration"
        return 0
    fi

    cd "$PROJECT_ROOT"

    if python3 scripts/migrate_secrets_to_aws.py; then
        log_success "Secrets migration completed successfully"
    else
        log_error "Secrets migration failed"
        log "Rolling back to local secrets..."
        restore_from_backup
        exit 1
    fi
}

verify_migration() {
    log "Verifying migration..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would verify migration"
        return 0
    fi

    cd "$PROJECT_ROOT"

    if python3 scripts/migrate_secrets_to_aws.py --verify; then
        log_success "Migration verification completed successfully"
    else
        log_error "Migration verification failed"
        exit 1
    fi
}

restore_from_backup() {
    log "Restoring from backup..."

    if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi

    local secrets_dir="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"

    cp -r "$BACKUP_DIR/nba-mcp-synthesis/"* "$secrets_dir/"

    log_success "Secrets restored from backup"
}

# External Secrets configuration
configure_external_secrets() {
    log "Configuring External Secrets Operator..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would configure External Secrets Operator"
        return 0
    fi

    # Apply External Secrets configuration
    if kubectl apply -f k8s/external-secrets.yaml; then
        log_success "External Secrets configuration applied"
    else
        log_error "Failed to apply External Secrets configuration"
        exit 1
    fi

    # Wait for ExternalSecret resources to be created
    log "Waiting for ExternalSecret resources..."
    kubectl wait --for=condition=Ready externalsecret/nba-mcp-synthesis-secrets -n nba-mcp-synthesis --timeout=300s || true

    # Check ExternalSecret status
    if kubectl get externalsecrets -n nba-mcp-synthesis | grep -q "nba-mcp-synthesis-secrets"; then
        log_success "ExternalSecret resources created"
    else
        log_warning "ExternalSecret resources may not be ready yet"
    fi

    # Check Kubernetes secrets
    if kubectl get secrets -n nba-mcp-synthesis | grep -q "nba-mcp-synthesis-secrets"; then
        log_success "Kubernetes secrets created"
    else
        log_warning "Kubernetes secrets may not be ready yet"
    fi
}

# Test functions
test_secret_access() {
    log "Testing secret access..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would test secret access"
        return 0
    fi

    # Test AWS Secrets Manager access
    if aws secretsmanager get-secret-value --secret-id nba-mcp-synthesis-production --query SecretString --output text >/dev/null 2>&1; then
        log_success "AWS Secrets Manager access verified"
    else
        log_error "Failed to access secrets in AWS Secrets Manager"
        exit 1
    fi

    # Test Kubernetes secret access
    if kubectl get secret nba-mcp-synthesis-secrets -n nba-mcp-synthesis >/dev/null 2>&1; then
        log_success "Kubernetes secret access verified"
    else
        log_warning "Kubernetes secrets may not be ready yet"
    fi
}

# Main execution
main() {
    log "Starting NBA MCP Synthesis Phase 2: Secrets Migration..."
    log "Configuration:"
    log "  Dry Run: $DRY_RUN"
    log "  Verbose: $VERBOSE"
    log "  Backup Dir: ${BACKUP_DIR:-"auto-generated"}"
    log "  Verify Only: $VERIFY_ONLY"

    # Validation phase
    log "Starting validation phase..."
    validate_prerequisites
    log_success "Validation phase completed"

    if [[ "$VERIFY_ONLY" == "true" ]]; then
        log "Running verification only..."
        verify_migration
        test_secret_access
        log_success "Phase 2: Secrets verification completed successfully!"
        return 0
    fi

    # Backup phase
    log "Starting backup phase..."
    create_backup
    log_success "Backup phase completed"

    # Migration phase
    log "Starting migration phase..."
    run_migration_dry_run
    run_migration
    verify_migration
    log_success "Migration phase completed"

    # Configuration phase
    log "Starting configuration phase..."
    configure_external_secrets
    test_secret_access
    log_success "Configuration phase completed"

    log_success "Phase 2: Secrets migration completed successfully!"

    if [[ "$DRY_RUN" == "false" ]]; then
        log "Next steps:"
        log "1. Run Phase 3: ./scripts/deploy_phase3_application.sh"
        log "2. Or run application deployment: kubectl apply -f k8s/"
        log "3. Then run Phase 4: ./scripts/deploy_phase4_monitoring.sh"
    fi
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Parse arguments and run main function
parse_args "$@"
main


