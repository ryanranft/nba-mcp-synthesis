#!/bin/bash
#
# NBA MCP Synthesis - Automated Deployment Script
# Deploys the system from scratch with full validation
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${PROJECT_DIR}/deploy/deployment_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="${PROJECT_DIR}/deploy/backups"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

step() {
    echo -e "\n${BLUE}[$1]${NC} $2" | tee -a "$LOG_FILE"
}

# Banner
echo "========================================" | tee "$LOG_FILE"
echo "NBA MCP Synthesis - Automated Deployment" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
log "Starting deployment process..."
log "Project directory: $PROJECT_DIR"
log "Log file: $LOG_FILE"
echo ""

# Step 1: Validate prerequisites
step "1/8" "Validating prerequisites"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log "Python version: $PYTHON_VERSION"
else
    error "Python 3 not found"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    log "Git version: $GIT_VERSION"
else
    error "Git not found"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    log "pip is available"
else
    error "pip not found"
    exit 1
fi

# Step 2: Create backup of existing installation
step "2/8" "Creating backup"

mkdir -p "$BACKUP_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
    BACKUP_NAME="env_backup_$(date +%Y%m%d_%H%M%S).env"
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME"
    log "Backed up .env to: $BACKUP_DIR/$BACKUP_NAME"
else
    info "No existing .env file to backup"
fi

# Step 3: Install dependencies
step "3/8" "Installing Python dependencies"

cd "$PROJECT_DIR"

if [ ! -f "requirements.txt" ]; then
    error "requirements.txt not found"
    exit 1
fi

# Install dependencies
log "Installing from requirements.txt..."
pip3 install -r requirements.txt >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "Dependencies installed successfully"
else
    error "Failed to install dependencies"
    exit 1
fi

# Step 4: Environment configuration
step "4/8" "Configuring environment"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        info "No .env file found. Creating from .env.example..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        warn "Please edit .env with your actual credentials before continuing"
        warn "Press ENTER to continue after editing .env, or CTRL+C to abort"
        read -r
    else
        error "No .env or .env.example file found"
        exit 1
    fi
else
    log ".env file exists"
fi

# Step 5: Validate environment
step "5/8" "Validating environment configuration"

if [ -f "$PROJECT_DIR/scripts/validate_environment.py" ]; then
    log "Running environment validation..."
    python3 "$PROJECT_DIR/scripts/validate_environment.py" --exit-on-failure >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "Environment validation passed"
    else
        error "Environment validation failed. Check log file: $LOG_FILE"
        error "Run: python3 scripts/validate_environment.py (for detailed output)"
        exit 1
    fi
else
    warn "Validation script not found, skipping validation"
fi

# Step 6: Create required directories
step "6/8" "Creating required directories"

mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/synthesis_output"
mkdir -p "$PROJECT_DIR/cache"

log "Created required directories"

# Step 7: Run post-deployment verification
step "7/8" "Running post-deployment verification"

# Check if verification script exists
if [ -f "$PROJECT_DIR/deploy/verify.sh" ]; then
    log "Running verification script..."
    bash "$PROJECT_DIR/deploy/verify.sh" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "Verification passed"
    else
        error "Verification failed. Check log file: $LOG_FILE"
        exit 1
    fi
else
    warn "Verification script not found, skipping"
fi

# Step 8: Final summary
step "8/8" "Deployment complete"

echo ""
echo "========================================" | tee -a "$LOG_FILE"
log "✅ Deployment completed successfully!"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

log "Next steps:"
echo "" | tee -a "$LOG_FILE"
echo "  1. Start the MCP server:" | tee -a "$LOG_FILE"
echo "     ./scripts/start_mcp_server.sh" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "  2. Run end-to-end tests:" | tee -a "$LOG_FILE"
echo "     python3 tests/test_e2e_workflow.py" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "  3. Run performance benchmarks:" | tee -a "$LOG_FILE"
echo "     python3 scripts/benchmark_system.py" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "  4. Run load tests:" | tee -a "$LOG_FILE"
echo "     python3 tests/test_load.py" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

log "Deployment log saved to: $LOG_FILE"
echo ""

exit 0
