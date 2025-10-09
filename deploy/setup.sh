#!/bin/bash
#
# Automated Deployment Setup Script
# Deploys NBA MCP Synthesis System from scratch
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
LOG_FILE="${PROJECT_ROOT}/deploy/setup.log"

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}NBA MCP Synthesis - Automated Deployment${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Project: $PROJECT_ROOT"
echo -e "Log file: $LOG_FILE"
echo ""

# Create deploy log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_step() {
    log "${BLUE}[$1]${NC} $2"
}

log_success() {
    log "${GREEN}✅${NC} $1"
}

log_error() {
    log "${RED}❌${NC} $1"
}

log_warning() {
    log "${YELLOW}⚠️${NC}  $1"
}

# Step 1: Check prerequisites
log_step "1/8" "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
log_success "Python ${PYTHON_VERSION} found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 not found. Please install pip first."
    exit 1
fi

log_success "pip3 found"

# Check git
if ! command -v git &> /dev/null; then
    log_warning "git not found (optional)"
else
    log_success "git found"
fi

# Step 2: Create virtual environment (optional but recommended)
log_step "2/8" "Setting up virtual environment..."

if [ -d "$VENV_DIR" ]; then
    log_warning "Virtual environment already exists, skipping creation"
else
    python3 -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
    log_success "Virtual environment created at $VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
log_success "Virtual environment activated"

# Step 3: Install dependencies
log_step "3/8" "Installing Python dependencies..."

cd "$PROJECT_ROOT"

pip install --upgrade pip >> "$LOG_FILE" 2>&1
pip install -r requirements.txt >> "$LOG_FILE" 2>&1

log_success "Dependencies installed"

# Verify critical packages
python3 -c "import mcp, boto3, psycopg2, anthropic" 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "Critical packages verified"
else
    log_error "Failed to verify critical packages"
    exit 1
fi

# Step 4: Configure environment
log_step "4/8" "Configuring environment..."

if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    if [ -f "${PROJECT_ROOT}/.env.example" ]; then
        cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
        log_warning ".env file created from .env.example"
        log_warning "IMPORTANT: Edit .env file with your actual credentials before proceeding"
        echo ""
        echo -e "${YELLOW}Next step: Edit .env file with your credentials${NC}"
        echo -e "Then run: ${GREEN}./deploy/verify.sh${NC}"
        echo ""
        exit 0
    else
        log_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    log_success ".env file exists"
fi

# Step 5: Validate environment
log_step "5/8" "Validating environment configuration..."

python3 "${PROJECT_ROOT}/scripts/validate_environment.py" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log_success "Environment validation passed"
else
    log_error "Environment validation failed. Check $LOG_FILE for details"
    echo ""
    echo -e "${YELLOW}To see errors, run:${NC}"
    echo -e "  python scripts/validate_environment.py"
    echo ""
    exit 1
fi

# Step 6: Create required directories
log_step "6/8" "Creating required directories..."

mkdir -p "${PROJECT_ROOT}/logs"
mkdir -p "${PROJECT_ROOT}/synthesis_output"
mkdir -p "${PROJECT_ROOT}/cache"

log_success "Directories created"

# Step 7: Run connection tests
log_step "7/8" "Testing connections..."

python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from tests.test_e2e_workflow import TestE2EWorkflow
    test_suite = TestE2EWorkflow()

    try:
        await test_suite.test_01_environment_setup()
        print('✅ Environment test passed')
        return 0
    except Exception as e:
        print(f'❌ Environment test failed: {e}')
        return 1

sys.exit(asyncio.run(test()))
" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log_success "Connection tests passed"
else
    log_warning "Connection tests had issues (check log)"
fi

# Step 8: Final summary
log_step "8/8" "Deployment complete!"

echo ""
log_success "NBA MCP Synthesis System is deployed!"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. ${GREEN}./scripts/start_mcp_server.sh${NC}  - Start MCP server"
echo -e "  2. ${GREEN}python tests/test_e2e_workflow.py${NC} - Run E2E tests"
echo -e "  3. ${GREEN}python scripts/test_synthesis_direct.py${NC} - Try synthesis"
echo ""
echo -e "${BLUE}Management:${NC}"
echo -e "  Stop server:    ${GREEN}./scripts/stop_mcp_server.sh${NC}"
echo -e "  View logs:      ${GREEN}tail -f logs/mcp_server.log${NC}"
echo -e "  Verify deploy:  ${GREEN}./deploy/verify.sh${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "  Deployment:  ${GREEN}DEPLOYMENT.md${NC}"
echo -e "  Usage:       ${GREEN}USAGE_GUIDE.md${NC}"
echo -e "  Quick Start: ${GREEN}QUICKSTART.md${NC}"
echo ""
log_success "Setup complete! 🎉"
