#!/bin/bash

# Migration script to move secrets from old structure to new hierarchical structure
# This script migrates secrets from .env.workflow and .env to the new directory structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-mcp-synthesis"
SECRETS_ROOT="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"
PRODUCTION_DIR="${SECRETS_ROOT}/.env.nba_mcp_synthesis.production"
DEVELOPMENT_DIR="${SECRETS_ROOT}/.env.nba_mcp_synthesis.development"
TEST_DIR="${SECRETS_ROOT}/.env.nba_mcp_synthesis.test"

echo -e "${BLUE}🔄 Starting migration to hierarchical secrets structure...${NC}"

# Function to create directory if it doesn't exist
create_directory() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}📁 Creating directory: $dir${NC}"
        mkdir -p "$dir"
        chmod 700 "$dir"
    fi
}

# Function to migrate secrets from a source file
migrate_secrets() {
    local source_file="$1"
    local target_dir="$2"
    local context="$3"

    if [ ! -f "$source_file" ]; then
        echo -e "${YELLOW}⚠️  Source file not found: $source_file${NC}"
        return
    fi

    echo -e "${BLUE}📋 Migrating secrets from $source_file to $target_dir (context: $context)${NC}"

    # Read the source file and process each line
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi

        # Extract variable name and value
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            local var_name="${BASH_REMATCH[1]}"
            local var_value="${BASH_REMATCH[2]}"

            # Check if variable already has the correct naming convention
            if [[ "$var_name" =~ _NBA_MCP_SYNTHESIS_WORKFLOW$ ]]; then
                # Already has correct naming, use as-is
                new_var_name="$var_name"
            elif [[ "$var_name" =~ _NBA_MCP_SYNTHESIS_WORFKLOW$ ]]; then
                # Has typo in naming, fix it
                new_var_name="${var_name%_WORFKLOW}_WORKFLOW"
            else
                # Convert to new naming convention
                new_var_name="${var_name}_NBA_MCP_SYNTHESIS_WORKFLOW"
            fi

            # Create the secret file
            local secret_file="${target_dir}/${new_var_name}.env"
            echo "$var_value" > "$secret_file"
            chmod 600 "$secret_file"

            echo -e "${GREEN}✅ Migrated: $var_name -> $new_var_name${NC}"
        fi
    done < "$source_file"
}

# Create directories
create_directory "$PRODUCTION_DIR"
create_directory "$DEVELOPMENT_DIR"
create_directory "$TEST_DIR"

# Migrate from .env.workflow to production
if [ -f "${PROJECT_ROOT}/.env.workflow" ]; then
    migrate_secrets "${PROJECT_ROOT}/.env.workflow" "$PRODUCTION_DIR" "production"
else
    echo -e "${YELLOW}⚠️  .env.workflow not found, skipping production migration${NC}"
fi

# Migrate from .env to development (with some modifications for dev context)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${BLUE}📋 Migrating secrets from .env to development context${NC}"

    # Read .env and create development versions
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi

        # Extract variable name and value
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            var_name="${BASH_REMATCH[1]}"
            var_value="${BASH_REMATCH[2]}"

            # Check if variable already has the correct naming convention
            if [[ "$var_name" =~ _NBA_MCP_SYNTHESIS_DEVELOPMENT$ ]]; then
                # Already has correct naming, use as-is
                new_var_name="$var_name"
            else
                # Convert to new naming convention for development
                new_var_name="${var_name}_NBA_MCP_SYNTHESIS_DEVELOPMENT"
            fi

            # Create the secret file
            secret_file="${DEVELOPMENT_DIR}/${new_var_name}.env"
            echo "$var_value" > "$secret_file"
            chmod 600 "$secret_file"

            echo -e "${GREEN}✅ Migrated: $var_name -> $new_var_name${NC}"
        fi
    done < "${PROJECT_ROOT}/.env"
else
    echo -e "${YELLOW}⚠️  .env not found, skipping development migration${NC}"
fi

# Create some test secrets
echo -e "${BLUE}📋 Creating test secrets...${NC}"
echo "test_value_production" > "${TEST_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_TEST.env"
echo "test_value_development" > "${DEVELOPMENT_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
echo "test_value_production" > "${PRODUCTION_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_WORKFLOW.env"

chmod 600 "${TEST_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_TEST.env"
chmod 600 "${DEVELOPMENT_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_DEVELOPMENT.env"
chmod 600 "${PRODUCTION_DIR}/TEST_SECRET_NBA_MCP_SYNTHESIS_WORKFLOW.env"

echo -e "${GREEN}✅ Created test secrets${NC}"

# Set proper permissions on all directories
echo -e "${BLUE}🔒 Setting proper permissions...${NC}"
chmod 700 "$PRODUCTION_DIR"
chmod 700 "$DEVELOPMENT_DIR"
chmod 700 "$TEST_DIR"

# Count migrated secrets
prod_count=$(find "$PRODUCTION_DIR" -name "*.env" | wc -l)
dev_count=$(find "$DEVELOPMENT_DIR" -name "*.env" | wc -l)
test_count=$(find "$TEST_DIR" -name "*.env" | wc -l)

echo -e "${GREEN}🎉 Migration completed successfully!${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo -e "  Production secrets: $prod_count"
echo -e "  Development secrets: $dev_count"
echo -e "  Test secrets: $test_count"

echo -e "${BLUE}🔍 Next steps:${NC}"
echo -e "  1. Test secret loading: python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA production"
echo -e "  2. Validate naming conventions: python3 scripts/enforce_naming_convention.py"
echo -e "  3. Run health checks: python3 mcp_server/secrets_health_monitor.py"
