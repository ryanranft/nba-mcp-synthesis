#!/bin/bash
# Setup SMS/Twilio Credentials in Hierarchical Secrets Structure
#
# This script helps you set up Twilio credentials in the hierarchical secrets system.
# It prompts for your Twilio credentials and creates the necessary files.
#
# Usage:
#   ./scripts/setup_sms_credentials.sh
#
# Or with options:
#   ./scripts/setup_sms_credentials.sh --context production
#   ./scripts/setup_sms_credentials.sh --context development --skip-confirmation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONTEXT="development"
SKIP_CONFIRMATION=false
BASE_PATH="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --context)
            CONTEXT="$2"
            shift 2
            ;;
        --skip-confirmation)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --context CONTEXT        Set context (production, development, test)"
            echo "  --skip-confirmation      Skip confirmation prompts"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Map context to directory suffix
case "${CONTEXT,,}" in  # Convert to lowercase
    production|workflow)
        DIR_SUFFIX="production"
        ENV_SUFFIX="WORKFLOW"
        ;;
    development)
        DIR_SUFFIX="development"
        ENV_SUFFIX="DEVELOPMENT"
        ;;
    test)
        DIR_SUFFIX="test"
        ENV_SUFFIX="TEST"
        ;;
    *)
        echo -e "${RED}❌ Invalid context: $CONTEXT${NC}"
        echo "Valid contexts: production, development, test"
        exit 1
        ;;
esac

# Construct directory path
SECRETS_DIR="${BASE_PATH}/.env.nba_mcp_synthesis.${DIR_SUFFIX}"

# Print header
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  SMS/Twilio Credentials Setup${NC}"
echo -e "${BLUE}  Hierarchical Secrets System${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Context: ${GREEN}${CONTEXT}${NC}"
echo -e "Directory: ${SECRETS_DIR}"
echo ""

# Check if directory exists
if [ ! -d "$SECRETS_DIR" ]; then
    echo -e "${YELLOW}⚠️  Secrets directory does not exist${NC}"
    echo -e "Creating: ${SECRETS_DIR}"

    if [ "$SKIP_CONFIRMATION" = false ]; then
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted"
            exit 1
        fi
    fi

    mkdir -p "$SECRETS_DIR"
    chmod 700 "$SECRETS_DIR"
    echo -e "${GREEN}✅ Directory created${NC}"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Enter Twilio Credentials${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "You can find these in your Twilio Console:"
echo "  https://console.twilio.com/"
echo ""

# Prompt for credentials
echo -e "${YELLOW}Account SID${NC} (starts with 'AC'):"
read -r ACCOUNT_SID

echo ""
echo -e "${YELLOW}Auth Token${NC} (sensitive - will not be echoed):"
read -rs AUTH_TOKEN
echo ""

echo ""
echo -e "${YELLOW}From Phone Number${NC} (format: +12345678901):"
read -r FROM_NUMBER

echo ""
echo -e "${YELLOW}To Phone Number(s)${NC} (comma-separated, format: +12345678901):"
echo "  (e.g., +12345678901 or +12345678901,+10987654321)"
read -r TO_NUMBERS

# Validate inputs
echo ""
echo -e "${BLUE}Validating inputs...${NC}"

VALIDATION_FAILED=false

if [[ ! $ACCOUNT_SID =~ ^AC[a-f0-9]{32}$ ]]; then
    echo -e "${RED}❌ Invalid Account SID format (should be AC followed by 32 hex chars)${NC}"
    VALIDATION_FAILED=true
fi

if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}❌ Auth Token cannot be empty${NC}"
    VALIDATION_FAILED=true
fi

if [[ ! $FROM_NUMBER =~ ^\+[0-9]{10,15}$ ]]; then
    echo -e "${YELLOW}⚠️  From Number may not be in correct E.164 format (+countrycode + number)${NC}"
fi

if [[ ! $TO_NUMBERS =~ ^\+[0-9] ]]; then
    echo -e "${YELLOW}⚠️  To Numbers may not be in correct E.164 format${NC}"
fi

if [ "$VALIDATION_FAILED" = true ]; then
    echo ""
    echo -e "${RED}Validation failed. Please check your inputs and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Validation passed${NC}"

# Show summary
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Account SID: ${ACCOUNT_SID:0:12}...${ACCOUNT_SID:(-4)}"
echo "Auth Token: ********"
echo "From Number: $FROM_NUMBER"
echo "To Numbers: $TO_NUMBERS"
echo ""
echo "Files to create:"
echo "  1. TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo "  2. TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo "  3. TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo "  4. TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo ""

# Confirm
if [ "$SKIP_CONFIRMATION" = false ]; then
    read -p "Create these files? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

# Create credential files
echo ""
echo -e "${BLUE}Creating credential files...${NC}"

cd "$SECRETS_DIR"

# Account SID
echo -n "$ACCOUNT_SID" > "TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
chmod 600 "TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo -e "${GREEN}✅${NC} TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"

# Auth Token
echo -n "$AUTH_TOKEN" > "TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
chmod 600 "TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo -e "${GREEN}✅${NC} TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"

# From Number
echo -n "$FROM_NUMBER" > "TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
chmod 600 "TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo -e "${GREEN}✅${NC} TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"

# To Numbers
echo -n "$TO_NUMBERS" > "TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
chmod 600 "TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"
echo -e "${GREEN}✅${NC} TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env"

# Verify permissions
echo ""
echo -e "${BLUE}Verifying file permissions...${NC}"
ls -l TWILIO_*_NBA_MCP_SYNTHESIS_${ENV_SUFFIX}.env | awk '{print $1, $9}' | while read -r perms file; do
    if [[ $perms =~ ^-rw------- ]]; then
        echo -e "${GREEN}✅${NC} $file (600)"
    else
        echo -e "${RED}❌${NC} $file ($perms)"
    fi
done

# Success
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Your Twilio credentials have been saved to:"
echo "  $SECRETS_DIR"
echo ""
echo "Next steps:"
echo "  1. Test the integration:"
echo "     cd /Users/ryanranft/nba-mcp-synthesis"
echo "     python scripts/test_sms_integration.py --context $CONTEXT"
echo ""
echo "  2. Send a test SMS:"
echo "     python scripts/test_sms_integration.py --context $CONTEXT --send-sms"
echo ""
echo "  3. Set up production credentials (if not done yet):"
echo "     ./scripts/setup_sms_credentials.sh --context production"
echo ""
echo "💡 Tip: Keep your Auth Token secure and never commit it to version control!"
echo ""
