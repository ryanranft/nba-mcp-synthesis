#!/bin/bash
# Deploy Security Scanning Protocol to NBA Simulator AWS
# This script copies the complete security setup from nba-mcp-synthesis to nba-simulator-aws

set -e  # Exit on error

SOURCE_PROJECT="/Users/ryanranft/nba-mcp-synthesis"
TARGET_PROJECT="/Users/ryanranft/nba-simulator-aws"

echo "=================================================="
echo "Security Protocol Deployment"
echo "NBA MCP Synthesis → NBA Simulator AWS"
echo "=================================================="
echo ""

# Verify source project has security files
echo "🔍 Step 1: Verifying source security files..."
REQUIRED_FILES=(
    ".pre-commit-config.yaml"
    ".git-secrets-patterns"
    "scripts/setup_security_scanning.sh"
    "scripts/validate_secrets_security.py"
    "scripts/test_security_scanning.py"
    "scripts/validate_s3_public_access.py"
    "pyproject.toml"
    "docs/SECURITY_SCANNING_GUIDE.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SOURCE_PROJECT/$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done
echo "✅ All source security files found"
echo ""

# Verify target project exists
echo "🔍 Step 2: Verifying target project..."
if [ ! -d "$TARGET_PROJECT" ]; then
    echo "❌ Target project not found: $TARGET_PROJECT"
    exit 1
fi

if [ ! -d "$TARGET_PROJECT/.git" ]; then
    echo "❌ Target is not a git repository"
    exit 1
fi
echo "✅ Target project verified"
echo ""

# Create backup of target .env file if it exists
echo "💾 Step 3: Backing up existing .env file..."
if [ -f "$TARGET_PROJECT/.env" ]; then
    BACKUP_FILE="$TARGET_PROJECT/.env.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$TARGET_PROJECT/.env" "$BACKUP_FILE"
    echo "✅ Backed up to: $BACKUP_FILE"
    echo "⚠️  Will remove .env file (secrets should be in hierarchical structure)"
else
    echo "✅ No .env file to backup"
fi
echo ""

# Copy security configuration files
echo "📋 Step 4: Copying security configuration files..."
cp "$SOURCE_PROJECT/.pre-commit-config.yaml" "$TARGET_PROJECT/"
echo "   ✅ .pre-commit-config.yaml"

cp "$SOURCE_PROJECT/.git-secrets-patterns" "$TARGET_PROJECT/"
echo "   ✅ .git-secrets-patterns"

cp "$SOURCE_PROJECT/pyproject.toml" "$TARGET_PROJECT/"
echo "   ✅ pyproject.toml"
echo ""

# Copy security scripts
echo "📋 Step 5: Copying security scripts..."
mkdir -p "$TARGET_PROJECT/scripts"

cp "$SOURCE_PROJECT/scripts/setup_security_scanning.sh" "$TARGET_PROJECT/scripts/"
chmod +x "$TARGET_PROJECT/scripts/setup_security_scanning.sh"
echo "   ✅ setup_security_scanning.sh"

cp "$SOURCE_PROJECT/scripts/validate_secrets_security.py" "$TARGET_PROJECT/scripts/"
chmod +x "$TARGET_PROJECT/scripts/validate_secrets_security.py"
echo "   ✅ validate_secrets_security.py"

cp "$SOURCE_PROJECT/scripts/test_security_scanning.py" "$TARGET_PROJECT/scripts/"
chmod +x "$TARGET_PROJECT/scripts/test_security_scanning.py"
echo "   ✅ test_security_scanning.py"

cp "$SOURCE_PROJECT/scripts/validate_s3_public_access.py" "$TARGET_PROJECT/scripts/"
chmod +x "$TARGET_PROJECT/scripts/validate_s3_public_access.py"
echo "   ✅ validate_s3_public_access.py"
echo ""

# Copy documentation
echo "📋 Step 6: Copying security documentation..."
mkdir -p "$TARGET_PROJECT/docs"
cp "$SOURCE_PROJECT/docs/SECURITY_SCANNING_GUIDE.md" "$TARGET_PROJECT/docs/"
echo "   ✅ SECURITY_SCANNING_GUIDE.md"
echo ""

# Create .github/workflows directory and copy workflows
echo "📋 Step 7: Setting up GitHub Actions workflows..."
mkdir -p "$TARGET_PROJECT/.github/workflows"

# Copy and adapt secrets-scan.yml
cp "$SOURCE_PROJECT/.github/workflows/secrets-scan.yml" "$TARGET_PROJECT/.github/workflows/"
echo "   ✅ secrets-scan.yml"

# Check if ci-cd.yml exists in target
if [ -f "$TARGET_PROJECT/.github/workflows/ci-cd.yml" ]; then
    echo "   ⚠️  ci-cd.yml already exists - manual merge required"
    echo "      See: $SOURCE_PROJECT/.github/workflows/ci-cd.yml (lines 165-218)"
else
    cp "$SOURCE_PROJECT/.github/workflows/ci-cd.yml" "$TARGET_PROJECT/.github/workflows/"
    echo "   ✅ ci-cd.yml"
fi
echo ""

# Update .gitignore
echo "📋 Step 8: Updating .gitignore..."
if [ -f "$TARGET_PROJECT/.gitignore" ]; then
    # Add security patterns if not already present
    if ! grep -q ".secrets.baseline" "$TARGET_PROJECT/.gitignore"; then
        cat >> "$TARGET_PROJECT/.gitignore" << 'EOF'

# Security scanning
.secrets.baseline
.git-secrets-patterns
security_audit_report.md
s3_security_audit_report.md

# Hierarchical secrets (tracked separately)
~/.cursor/secrets/

# Environment files (comprehensive)
.env
.env.*
!.env.example
!.env.template
!.env.sample
EOF
        echo "   ✅ Added security patterns to .gitignore"
    else
        echo "   ✅ .gitignore already has security patterns"
    fi
else
    echo "   ⚠️  No .gitignore found - creating one"
    cp "$SOURCE_PROJECT/.gitignore" "$TARGET_PROJECT/"
fi
echo ""

# Check if mcp_server directory exists for unified_secrets_manager
echo "📋 Step 9: Checking unified_secrets_manager availability..."
if [ -f "$TARGET_PROJECT/mcp_server/unified_secrets_manager.py" ]; then
    echo "   ✅ unified_secrets_manager.py found"
elif [ -f "$SOURCE_PROJECT/mcp_server/unified_secrets_manager.py" ]; then
    echo "   ⚠️  Copying unified_secrets_manager.py from nba-mcp-synthesis"
    mkdir -p "$TARGET_PROJECT/mcp_server"
    cp "$SOURCE_PROJECT/mcp_server/unified_secrets_manager.py" "$TARGET_PROJECT/mcp_server/"
    echo "   ✅ unified_secrets_manager.py copied"
else
    echo "   ❌ unified_secrets_manager.py not found in either project"
    exit 1
fi
echo ""

# Update requirements.txt
echo "📋 Step 10: Updating requirements.txt..."
if [ -f "$TARGET_PROJECT/requirements.txt" ]; then
    # Add security packages if not present
    for package in "pre-commit>=3.6.0" "detect-secrets>=1.4.0" "bandit>=1.7.5" "boto3>=1.26.0"; do
        pkg_name=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1)
        if ! grep -q "^${pkg_name}" "$TARGET_PROJECT/requirements.txt"; then
            echo "$package" >> "$TARGET_PROJECT/requirements.txt"
            echo "   ✅ Added $pkg_name"
        else
            echo "   ✅ $pkg_name already present"
        fi
    done
else
    echo "   ⚠️  No requirements.txt found - creating one"
    echo "pre-commit>=3.6.0" > "$TARGET_PROJECT/requirements.txt"
    echo "detect-secrets>=1.4.0" >> "$TARGET_PROJECT/requirements.txt"
    echo "bandit>=1.7.5" >> "$TARGET_PROJECT/requirements.txt"
    echo "boto3>=1.26.0" >> "$TARGET_PROJECT/requirements.txt"
    echo "   ✅ Created requirements.txt with security packages"
fi
echo ""

# Initialize security tools in target project
echo "🔧 Step 11: Installing security tools in target project..."
cd "$TARGET_PROJECT"
./scripts/setup_security_scanning.sh
echo ""

# Run initial security scan
echo "🔍 Step 12: Running initial security scan..."
python3 scripts/validate_secrets_security.py
echo ""

# Remove .env file if it exists
if [ -f "$TARGET_PROJECT/.env" ]; then
    echo "🗑️  Step 13: Removing .env file (backed up earlier)..."
    rm "$TARGET_PROJECT/.env"
    echo "   ✅ .env removed - use hierarchical secrets at:"
    echo "      /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/"
    echo "      big_cat_bets_simulators/NBA/nba-simulator-aws/"
    echo ""
fi

# Git status check
echo "📊 Step 14: Checking git status..."
cd "$TARGET_PROJECT"
git status --short | head -20
echo ""

echo "=================================================="
echo "✅ Security Protocol Deployment Complete!"
echo "=================================================="
echo ""
echo "📋 Summary of Changes:"
echo "   • Pre-commit hooks configured"
echo "   • GitHub Actions workflows added"
echo "   • Security scanning scripts installed"
echo "   • Documentation added"
echo "   • .env file removed (if existed)"
echo ""
echo "📝 Next Steps:"
echo "   1. Review changes: cd $TARGET_PROJECT && git status"
echo "   2. Test security: python3 scripts/test_security_scanning.py"
echo "   3. Validate S3: python3 scripts/validate_s3_public_access.py"
echo "   4. Commit changes: git add -A && git commit -m 'feat: add security scanning protocol'"
echo "   5. Push to GitHub: git push origin main"
echo ""
echo "📚 Documentation: $TARGET_PROJECT/docs/SECURITY_SCANNING_GUIDE.md"
echo ""


