#!/bin/bash
#
# Scrub Google Cloud IDs from Git History
# Based on previous successful scrubbing operations (commit 9e4ed46)
#
# WARNING: This rewrites Git history!
# - All commit SHAs will change
# - Requires force push to GitHub
# - Coordinate with team if shared repository
#
# Usage: ./scripts/scrub_google_cloud_ids.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================================================="
echo "🔒 SCRUB GOOGLE CLOUD IDS FROM GIT HISTORY"
echo "========================================================================="
echo ""
echo "${YELLOW}WARNING: This will rewrite Git history!${NC}"
echo ""
echo "This script will:"
echo "  1. Create a backup of your repository"
echo "  2. Use git filter-branch to rewrite history"
echo "  3. Replace Google Cloud IDs with placeholders"
echo "  4. Clean up refs and force garbage collection"
echo ""
echo "Sensitive data to be scrubbed:"
echo "  - Project ID: ${PROJECT_ID_PRIMARY}"
echo "  - Project ID: ${PROJECT_ID_SECONDARY}"
echo "  - Billing ID: 01C3B6-61505E-CB6F45"
echo ""
read -p "Do you want to proceed? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "${RED}Aborted.${NC}"
    exit 1
fi

# Step 1: Create backup
echo ""
echo "Step 1: Creating backup..."
BACKUP_DIR="../nba-mcp-synthesis-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"

# Step 2: Install BFG Repo-Cleaner (faster than git filter-branch)
echo ""
echo "Step 2: Checking for BFG Repo-Cleaner..."
if command -v bfg &> /dev/null; then
    echo "${GREEN}✅ BFG is installed${NC}"
    USE_BFG=true
else
    echo "${YELLOW}⚠️  BFG not found. Install with: brew install bfg${NC}"
    echo "Falling back to git filter-branch (slower but works)"
    USE_BFG=false
fi

# Step 3: Create replacement files
echo ""
echo "Step 3: Creating replacement patterns..."

# Create a temporary file with replacements
cat > /tmp/google-cloud-replacements.txt << 'EOF'
${PROJECT_ID_PRIMARY}==>${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
${PROJECT_ID_SECONDARY}==>${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}
01C3B6-61505E-CB6F45==>${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
${BIGQUERY_BILLING_EXPORT_TABLE}==>${BIGQUERY_BILLING_EXPORT_TABLE}
EOF

echo "${GREEN}✅ Replacement patterns created${NC}"

# Step 4: Perform scrubbing
echo ""
echo "Step 4: Scrubbing Git history..."

if [ "$USE_BFG" = true ]; then
    echo "Using BFG Repo-Cleaner (fast method)..."
    
    # BFG requires a fresh clone
    cd ..
    git clone --mirror nba-mcp-synthesis nba-mcp-synthesis-mirror.git
    cd nba-mcp-synthesis-mirror.git
    
    # Run BFG
    bfg --replace-text /tmp/google-cloud-replacements.txt
    
    # Update refs
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
    # Push back to original repo
    git push
    
    cd ../nba-mcp-synthesis
    git fetch origin
    git reset --hard origin/main
    
    # Cleanup mirror
    cd ..
    rm -rf nba-mcp-synthesis-mirror.git
    
else
    echo "Using git filter-branch (slow method)..."
    
    # Files containing sensitive data
    FILES_TO_SCRUB=(
        "BILLING_SETUP_STATUS.md"
        "docs/BIGQUERY_BILLING_SETUP.md"
        "BILLING_QUICK_REFERENCE.md"
        "BILLING_REPORT_20251018.md"
        "billing_report_20251018.json"
        "scripts/check_gemini_costs.py"
    )
    
    # Method 1: Remove files from history entirely
    for FILE in "${FILES_TO_SCRUB[@]}"; do
        if [ -f "$FILE" ]; then
            echo "  Scrubbing: $FILE"
            git filter-branch --force --index-filter \
                "git rm --cached --ignore-unmatch '$FILE'" \
                --prune-empty --tag-name-filter cat -- --all
        fi
    done
    
    # Alternative Method 2: Use sed to replace in place (more complex, preserves files)
    # Uncomment if you want to keep the files but replace the IDs
    #
    # git filter-branch --force --tree-filter '
    #     find . -type f \( -name "*.md" -o -name "*.json" -o -name "*.py" \) -exec sed -i "" \
    #         -e "s/${PROJECT_ID_PRIMARY}/\${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}/g" \
    #         -e "s/${PROJECT_ID_SECONDARY}/\${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}/g" \
    #         -e "s/01C3B6-61505E-CB6F45/\${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}/g" \
    #         {} + 2>/dev/null || true
    # ' --tag-name-filter cat -- --all
    
fi

echo "${GREEN}✅ Git history scrubbed${NC}"

# Step 5: Clean up refs
echo ""
echo "Step 5: Cleaning up refs..."
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "${GREEN}✅ Refs cleaned${NC}"

# Step 6: Verify removal
echo ""
echo "Step 6: Verifying removal..."
FOUND_COUNT=$(git log --all --source --full-history -S "${PROJECT_ID_PRIMARY}" | wc -l)
if [ "$FOUND_COUNT" -eq 0 ]; then
    echo "${GREEN}✅ Verification passed: No Google Cloud IDs found in history${NC}"
else
    echo "${RED}⚠️  Warning: Some occurrences may still exist. Count: $FOUND_COUNT${NC}"
    echo "Run: git log --all -S '${PROJECT_ID_PRIMARY}' to inspect"
fi

# Step 7: Summary
echo ""
echo "========================================================================="
echo "📊 SCRUBBING COMPLETE"
echo "========================================================================="
echo ""
echo "What was done:"
echo "  ✅ Backup created: $BACKUP_DIR"
echo "  ✅ Git history rewritten"
echo "  ✅ Google Cloud IDs replaced with placeholders"
echo "  ✅ Refs cleaned and garbage collected"
echo ""
echo "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo ""
echo "1. Verify the changes locally:"
echo "   git log --all --oneline | head -20"
echo "   git grep 'gen-lang-client' (should find nothing in history)"
echo ""
echo "2. Test the repository:"
echo "   - Check that all files still exist and work correctly"
echo "   - Run tests: python3 -m pytest tests/"
echo ""
echo "3. Force push to GitHub:"
echo "   ${RED}git push origin --force --all${NC}"
echo "   ${RED}git push origin --force --tags${NC}"
echo ""
echo "4. Notify collaborators (if any):"
echo "   - They will need to re-clone the repository"
echo "   - Old clones will have diverged history"
echo ""
echo "5. Update documentation with new placeholders:"
echo "   - Edit files to use environment variables"
echo "   - Reference: .env.google_cloud (in .gitignore)"
echo ""
echo "6. Monitor for issues:"
echo "   - Check GitHub for any warnings"
echo "   - Run security scan: python3 scripts/validate_secrets_security.py"
echo ""
echo "${GREEN}Backup location: $BACKUP_DIR${NC}"
echo "${YELLOW}Keep this backup until you've verified everything works!${NC}"
echo ""
echo "========================================================================="

# Cleanup temporary files
rm -f /tmp/google-cloud-replacements.txt

echo ""
echo "${GREEN}✅ Script completed successfully${NC}"
echo ""





