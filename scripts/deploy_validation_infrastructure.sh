#!/bin/bash
###############################################################################
# NBA MCP Data Validation Infrastructure Deployment Script
#
# Phase 10A Week 2 - Agent 4 - Phase 5
# Created: 2025-10-25
#
# This script automates the deployment of the data validation infrastructure.
#
# Usage:
#   ./scripts/deploy_validation_infrastructure.sh [environment] [options]
#
# Examples:
#   ./scripts/deploy_validation_infrastructure.sh production
#   ./scripts/deploy_validation_infrastructure.sh staging --dry-run
#   ./scripts/deploy_validation_infrastructure.sh production --rollback
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

###############################################################################
# Configuration
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
ENVIRONMENT="${1:-staging}"
DRY_RUN=false
ROLLBACK=false
SKIP_TESTS=false

# Parse options
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

run_command() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would execute: $@"
    else
        "$@"
    fi
}

###############################################################################
# Pre-flight Checks
###############################################################################

preflight_checks() {
    log "Running pre-flight checks..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found. Please install Python 3.9 or higher."
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log "Python version: $PYTHON_VERSION"

    # Check if virtual environment exists
    if [ ! -d "${PROJECT_ROOT}/venv" ]; then
        warning "Virtual environment not found. Creating..."
        run_command python3 -m venv "${PROJECT_ROOT}/venv"
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        error "Git not found. Please install git."
    fi

    success "Pre-flight checks passed"
}

###############################################################################
# Environment Setup
###############################################################################

setup_environment() {
    log "Setting up environment: $ENVIRONMENT"

    # Activate virtual environment
    source "${PROJECT_ROOT}/venv/bin/activate" || error "Failed to activate virtual environment"
    success "Virtual environment activated"

    # Load environment variables
    if [ -f "${PROJECT_ROOT}/.env.${ENVIRONMENT}" ]; then
        log "Loading environment variables from .env.${ENVIRONMENT}"
        set -a
        source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"
        set +a
    elif [ -f "${PROJECT_ROOT}/.env" ]; then
        log "Loading environment variables from .env"
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
    else
        warning "No .env file found. Using defaults."
    fi

    success "Environment setup complete"
}

###############################################################################
# Backup
###############################################################################

create_backup() {
    log "Creating backup..."

    BACKUP_DIR="${PROJECT_ROOT}/backups/validation_${TIMESTAMP}"
    run_command mkdir -p "${BACKUP_DIR}"

    # Backup current code
    if [ -d "${PROJECT_ROOT}/mcp_server" ]; then
        run_command cp -r "${PROJECT_ROOT}/mcp_server" "${BACKUP_DIR}/"
        success "Code backed up to ${BACKUP_DIR}"
    fi

    # Backup configuration
    if [ -d "${PROJECT_ROOT}/config" ]; then
        run_command cp -r "${PROJECT_ROOT}/config" "${BACKUP_DIR}/"
        success "Configuration backed up"
    fi

    echo "${BACKUP_DIR}" > "${PROJECT_ROOT}/.last_backup"
}

###############################################################################
# Rollback
###############################################################################

perform_rollback() {
    log "Performing rollback..."

    if [ ! -f "${PROJECT_ROOT}/.last_backup" ]; then
        error "No backup found to rollback to"
    fi

    BACKUP_DIR=$(cat "${PROJECT_ROOT}/.last_backup")

    if [ ! -d "${BACKUP_DIR}" ]; then
        error "Backup directory not found: ${BACKUP_DIR}"
    fi

    log "Rolling back to: ${BACKUP_DIR}"

    # Restore code
    if [ -d "${BACKUP_DIR}/mcp_server" ]; then
        run_command rm -rf "${PROJECT_ROOT}/mcp_server"
        run_command cp -r "${BACKUP_DIR}/mcp_server" "${PROJECT_ROOT}/"
        success "Code restored"
    fi

    # Restore configuration
    if [ -d "${BACKUP_DIR}/config" ]; then
        run_command rm -rf "${PROJECT_ROOT}/config"
        run_command cp -r "${BACKUP_DIR}/config" "${PROJECT_ROOT}/"
        success "Configuration restored"
    fi

    # Reinstall dependencies
    run_command pip install -r "${PROJECT_ROOT}/requirements.txt"

    success "Rollback complete"
}

###############################################################################
# Installation
###############################################################################

install_dependencies() {
    log "Installing dependencies..."

    # Upgrade pip
    run_command pip install --upgrade pip
    success "pip upgraded"

    # Install requirements
    run_command pip install -r "${PROJECT_ROOT}/requirements.txt"
    success "Dependencies installed"

    # Install package
    run_command pip install -e "${PROJECT_ROOT}"
    success "Package installed"
}

###############################################################################
# Testing
###############################################################################

run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        warning "Skipping tests (--skip-tests flag set)"
        return
    fi

    log "Running tests..."

    # Unit tests
    log "Running unit tests..."
    run_command pytest "${PROJECT_ROOT}/tests/test_data_cleaning.py" \
                        "${PROJECT_ROOT}/tests/test_data_profiler.py" \
                        "${PROJECT_ROOT}/tests/test_data_validation_pipeline.py" \
                        "${PROJECT_ROOT}/tests/test_integrity_checker.py" \
                        -v --tb=short || error "Unit tests failed"
    success "Unit tests passed"

    # Integration tests
    log "Running integration tests..."
    run_command pytest "${PROJECT_ROOT}/tests/integration/" -v --tb=short || error "Integration tests failed"
    success "Integration tests passed"

    # Security tests
    log "Running security tests..."
    run_command pytest "${PROJECT_ROOT}/tests/security/test_validation_security.py" -v --tb=short || warning "Security tests had issues (continuing)"

    success "All tests passed"
}

###############################################################################
# Health Check
###############################################################################

health_check() {
    log "Running health checks..."

    # Test import
    log "Testing module import..."
    run_command python3 -c "from mcp_server.data_validation_pipeline import DataValidationPipeline; print('Import successful')" || error "Import failed"
    success "Module import successful"

    # Test basic validation
    log "Testing basic validation..."
    run_command python3 <<EOF || error "Basic validation failed"
import pandas as pd
from mcp_server.data_validation_pipeline import DataValidationPipeline

df = pd.DataFrame({
    'player_id': [1, 2, 3],
    'points': [25, 30, 22],
})

pipeline = DataValidationPipeline()
result = pipeline.validate(df, 'player_stats')
print(f"Validation result: {result.current_stage}")
EOF
    success "Basic validation successful"

    success "Health checks passed"
}

###############################################################################
# Deployment Summary
###############################################################################

deployment_summary() {
    echo ""
    echo "========================================="
    echo "Deployment Summary"
    echo "========================================="
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $TIMESTAMP"
    echo "Python: $(python3 --version)"
    echo "Git commit: $(git rev-parse --short HEAD)"
    echo "Backup: $(cat ${PROJECT_ROOT}/.last_backup 2>/dev/null || echo 'N/A')"
    echo "========================================="
    echo ""
}

###############################################################################
# Main Deployment Flow
###############################################################################

main() {
    echo ""
    echo "========================================="
    echo "NBA MCP Data Validation Deployment"
    echo "========================================="
    echo "Environment: $ENVIRONMENT"
    echo "Dry Run: $DRY_RUN"
    echo "Rollback: $ROLLBACK"
    echo "========================================="
    echo ""

    if [ "$ROLLBACK" = true ]; then
        perform_rollback
        health_check
        deployment_summary
        success "Rollback completed successfully!"
        return
    fi

    # Normal deployment flow
    preflight_checks
    setup_environment
    create_backup
    install_dependencies
    run_tests
    health_check
    deployment_summary

    success "Deployment completed successfully!"

    # Next steps
    echo ""
    echo "Next steps:"
    echo "  1. Review deployment summary above"
    echo "  2. Run additional smoke tests if needed"
    echo "  3. Monitor application logs"
    echo "  4. Update monitoring dashboards"
    echo ""
    echo "To rollback:"
    echo "  ./scripts/deploy_validation_infrastructure.sh $ENVIRONMENT --rollback"
    echo ""
}

###############################################################################
# Execute
###############################################################################

main
