#!/bin/bash
#
# NBA MCP Synthesis - Post-Deployment Verification
#

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "========================================="
echo "Post-Deployment Verification"
echo "========================================="
echo ""

# Check 1: Python dependencies
echo "[1/5] Checking Python dependencies..."
python3 -c "import boto3, psycopg2, anthropic, mcp" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All required packages installed"
else
    echo "❌ Missing required packages"
    exit 1
fi

# Check 2: Environment variables
echo "[2/5] Checking environment variables..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file missing"
    exit 1
fi

# Check 3: Required directories
echo "[3/5] Checking required directories..."
for dir in logs synthesis_output cache; do
    if [ -d "$dir" ]; then
        echo "✅ Directory '$dir' exists"
    else
        echo "⚠️  Directory '$dir' missing (will be created)"
        mkdir -p "$dir"
    fi
done

# Check 4: Key scripts executable
echo "[4/5] Checking script permissions..."
for script in scripts/start_mcp_server.sh scripts/stop_mcp_server.sh; do
    if [ -x "$script" ]; then
        echo "✅ $script is executable"
    else
        echo "⚠️  $script not executable (fixing)"
        chmod +x "$script"
    fi
done

# Check 5: Run validation script
echo "[5/5] Running environment validation..."
if [ -f "scripts/validate_environment.py" ]; then
    python3 scripts/validate_environment.py --exit-on-failure
    if [ $? -eq 0 ]; then
        echo "✅ Environment validation passed"
    else
        echo "❌ Environment validation failed"
        exit 1
    fi
else
    echo "⚠️  Validation script not found"
fi

echo ""
echo "========================================="
echo "✅ All verification checks passed!"
echo "========================================="
echo ""

exit 0
