#!/bin/bash
# NBA MCP Synthesis - Timeout Wrapper for detect-secrets
# Prevents detect-secrets scans from hanging indefinitely

set -e

# Configuration
DEFAULT_TIMEOUT=300  # 5 minutes in seconds
TIMEOUT="${DETECT_SECRETS_TIMEOUT:-$DEFAULT_TIMEOUT}"
LOG_FILE="${DETECT_SECRETS_LOG:-/tmp/detect-secrets-scan.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage message
usage() {
    cat <<EOF
Usage: $0 [OPTIONS] -- [DETECT-SECRETS ARGS]

Wrapper for detect-secrets with timeout protection to prevent hanging scans.

OPTIONS:
    -t, --timeout SECONDS   Set timeout in seconds (default: $DEFAULT_TIMEOUT)
    -l, --log FILE          Set log file location (default: $LOG_FILE)
    -h, --help             Show this help message

ENVIRONMENT VARIABLES:
    DETECT_SECRETS_TIMEOUT  Override default timeout (seconds)
    DETECT_SECRETS_LOG      Override default log file location

EXAMPLES:
    # Scan with default 5-minute timeout
    $0 -- scan --baseline .secrets.baseline

    # Scan with custom 10-minute timeout
    $0 --timeout 600 -- scan --all-files

    # Scan specific files with 2-minute timeout
    $0 -t 120 -- scan file1.py file2.py

NOTES:
    - Do NOT use --all-files with large repositories (hangs easily)
    - For full repo scans, use smaller timeout or scan in batches
    - Progress is logged to: $LOG_FILE

EXIT CODES:
    0   Scan completed successfully
    1   Scan found secrets (normal detect-secrets behavior)
    124 Scan timed out (killed after $TIMEOUT seconds)
    Other: detect-secrets error codes

EOF
}

# Parse arguments
DETECT_SECRETS_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -l|--log)
            LOG_FILE="$2"
            shift 2
            ;;
        --)
            shift
            DETECT_SECRETS_ARGS=("$@")
            break
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ ${#DETECT_SECRETS_ARGS[@]} -eq 0 ]]; then
    echo -e "${RED}Error: No detect-secrets arguments provided${NC}" >&2
    echo "Use: $0 -- scan [OPTIONS]" >&2
    exit 1
fi

if ! command -v detect-secrets &> /dev/null; then
    echo -e "${RED}Error: detect-secrets not found${NC}" >&2
    echo "Install with: pip install detect-secrets" >&2
    exit 1
fi

# Check for --all-files flag and warn
for arg in "${DETECT_SECRETS_ARGS[@]}"; do
    if [[ "$arg" == "--all-files" ]]; then
        echo -e "${YELLOW}WARNING: --all-files flag detected!${NC}" >&2
        echo "This can cause scans to hang on large repositories." >&2
        echo "Consider scanning specific files or using a longer timeout." >&2
        echo "" >&2
    fi
done

# Create log file directory if needed
mkdir -p "$(dirname "$LOG_FILE")"

# Log scan start
{
    echo "======================================"
    echo "detect-secrets scan started"
    echo "Time: $(date)"
    echo "Timeout: ${TIMEOUT}s"
    echo "Command: detect-secrets ${DETECT_SECRETS_ARGS[*]}"
    echo "======================================"
} > "$LOG_FILE"

# Run detect-secrets with timeout
echo -e "${GREEN}Starting detect-secrets scan with ${TIMEOUT}s timeout...${NC}"
echo -e "Log file: $LOG_FILE"
echo ""

# Use timeout command (available on macOS and Linux)
if timeout --help &> /dev/null 2>&1; then
    # GNU timeout (Linux)
    TIMEOUT_CMD="timeout --signal=TERM --kill-after=10s $TIMEOUT"
elif gtimeout --help &> /dev/null 2>&1; then
    # GNU timeout via Homebrew (macOS)
    TIMEOUT_CMD="gtimeout --signal=TERM --kill-after=10s $TIMEOUT"
else
    echo -e "${YELLOW}WARNING: timeout command not found${NC}" >&2
    echo "Install with: brew install coreutils (macOS) or apt install coreutils (Linux)" >&2
    echo "Running without timeout protection..." >&2
    TIMEOUT_CMD=""
fi

# Run the scan
EXIT_CODE=0
if [[ -n "$TIMEOUT_CMD" ]]; then
    $TIMEOUT_CMD detect-secrets "${DETECT_SECRETS_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?
else
    detect-secrets "${DETECT_SECRETS_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?
fi

# Log completion
{
    echo ""
    echo "======================================"
    echo "detect-secrets scan completed"
    echo "Time: $(date)"
    echo "Exit code: $EXIT_CODE"
    echo "======================================"
} >> "$LOG_FILE"

# Handle exit codes
case $EXIT_CODE in
    0)
        echo -e "${GREEN}✅ Scan completed: No secrets detected${NC}"
        ;;
    1)
        echo -e "${YELLOW}⚠️  Scan completed: Secrets detected!${NC}"
        echo "Review the output above for details."
        ;;
    124)
        echo -e "${RED}❌ Scan timed out after ${TIMEOUT}s${NC}" >&2
        echo "" >&2
        echo "The scan was taking too long and was terminated." >&2
        echo "" >&2
        echo "Possible causes:" >&2
        echo "  - Using --all-files on a large repository" >&2
        echo "  - Scanning large binary files" >&2
        echo "  - Complex regex patterns causing performance issues" >&2
        echo "" >&2
        echo "Solutions:" >&2
        echo "  1. Increase timeout: $0 --timeout 600 -- scan ..." >&2
        echo "  2. Scan specific files instead of --all-files" >&2
        echo "  3. Update .secrets.baseline to exclude large files" >&2
        echo "  4. Run: detect-secrets scan --exclude-files 'pattern'" >&2
        echo "" >&2
        ;;
    *)
        echo -e "${RED}❌ Scan failed with exit code: $EXIT_CODE${NC}" >&2
        ;;
esac

exit $EXIT_CODE
