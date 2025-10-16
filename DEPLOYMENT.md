# NBA MCP Synthesis System - Deployment Guide

**Version:** 1.0
**Last Updated:** October 9, 2025
**Status:** Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Validation](#deployment-validation)
6. [Starting the System](#starting-the-system)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)
9. [Production Checklist](#production-checklist)

---

## Prerequisites

### Required Software

- **Python 3.9+** (tested with 3.11)
- **pip** package manager
- **Git** for version control
- **AWS CLI** (optional, for manual AWS operations)

### Required AWS Resources

- **AWS RDS PostgreSQL** database (version 13+)
  - Must contain NBA data tables
  - Tables: `games`, `players`, `teams`, `player_game_stats`, etc.

- **AWS S3** bucket
  - Should contain game data files
  - Read access required

- **AWS Glue** catalog (optional but recommended)
  - Data catalog with table schemas

### Required API Keys

- **DeepSeek API key** - Get from https://platform.deepseek.com/
- **Anthropic API key** - Get from https://console.anthropic.com/
- **OpenAI API key** (optional) - For comparisons
- **Google API key** (optional) - For Gemini

### System Requirements

- **RAM:** Minimum 4GB, recommended 8GB+
- **Disk:** 1GB free space for dependencies + logs
- **Network:** Internet connection for API calls
- **OS:** macOS, Linux, or WSL2 on Windows

---

## Quick Start

**For experienced users who want to get running quickly:**

```bash
# 1. Clone and navigate
git clone <repository-url>
cd nba-mcp-synthesis

# 2. Setup environment
cp .env.example .env
nano .env  # Edit with your credentials

# 3. Install dependencies
pip install -r requirements.txt

# 4. Validate environment
python scripts/validate_environment.py

# 5. Start MCP server
./scripts/start_mcp_server.sh

# 6. Run end-to-end test
python tests/test_e2e_workflow.py

# 7. Try synthesis
python scripts/test_synthesis_direct.py
```

**Expected time: 15-30 minutes**

---

## Detailed Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd nba-mcp-synthesis

# Verify structure
ls -la
# Should see: mcp_server/, synthesis/, scripts/, tests/, README.md, etc.
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Verify
which python
# Should show path inside venv/
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import mcp, boto3, psycopg2, anthropic; print('✅ All packages installed')"
```

**Common Issues:**
- **psycopg2 fails:** Try `pip install psycopg2-binary` instead
- **Permission errors:** Use `pip install --user` or run in venv
- **MacOS SSL errors:** Run `/Applications/Python\ 3.x/Install\ Certificates.command`

### Step 4: AWS Credentials Setup

#### Option A: AWS CLI (Recommended)

```bash
# Install AWS CLI
brew install awscli  # macOS
# OR
pip install awscli

# Configure credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)

# Verify
aws sts get-caller-identity
```

#### Option B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Option C: .env File (Used by this project)

Credentials will be in `.env` file (see next section).

---

## Environment Configuration

### Create .env File

```bash
# Copy example
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

### Required Variables

```bash
# AWS RDS PostgreSQL
RDS_HOST=your-db-endpoint.region.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=nba_simulator
RDS_USERNAME=postgres
RDS_PASSWORD=your_secure_password

# AWS S3
S3_BUCKET=your-s3-bucket-name
S3_REGION=us-east-1

# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# DeepSeek API (Primary Model)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Anthropic API (Synthesis Model)
ANTHROPIC_API_KEY=sk-ant-...
```

### Optional Variables

```bash
# AWS Glue (optional but recommended)
GLUE_DATABASE=nba_raw_data
GLUE_REGION=us-east-1

# Ollama (optional local model)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:32b

# Slack notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Project paths
PROJECT_ROOT=/path/to/nba-simulator-aws
SYNTHESIS_OUTPUT_DIR=/path/to/output

# Performance tuning
MAX_QUERY_ROWS=1000
QUERY_TIMEOUT_SECONDS=30
CACHE_ENABLED=true
```

### Security Note

⚠️ **NEVER commit .env to git!**

The `.env` file contains sensitive credentials. It's already in `.gitignore` but double-check:

```bash
git status
# .env should NOT appear in untracked files
```

---

## Deployment Validation

### Automated Validation

Run the comprehensive validation script:

```bash
python scripts/validate_environment.py

# For CI/CD (exits with code 1 on failure):
python scripts/validate_environment.py --exit-on-failure
```

**What it checks:**
- ✅ All required environment variables are set
- ✅ AWS credentials are valid
- ✅ Database connection works
- ✅ S3 bucket is accessible
- ✅ AWS Glue catalog is reachable (if configured)
- ✅ API keys are valid format
- ✅ Python dependencies are installed
- ✅ Required directories exist

**Expected output:**
```
══════════════════════════════════════════════════════════
NBA MCP Synthesis - Environment Validation
══════════════════════════════════════════════════════════

Environment Variables
✅ RDS_HOST          Set (nba-sim***)
✅ RDS_DATABASE      Set (nba***)
✅ DEEPSEEK_API_KEY  Set (sk-fb5f9***)
... (more checks)

Database
✅ PostgreSQL Connection  Connected (16 tables found)

AWS S3
✅ S3 Bucket Access  Accessible (bucket: your-bucket)

══════════════════════════════════════════════════════════
✅ All Validation Checks Passed
System is ready for deployment!
══════════════════════════════════════════════════════════
```

### Manual Verification

If validation script fails, check manually:

#### 1. Test Database Connection

```bash
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('RDS_HOST'),
    port=os.getenv('RDS_PORT'),
    database=os.getenv('RDS_DATABASE'),
    user=os.getenv('RDS_USERNAME'),
    password=os.getenv('RDS_PASSWORD')
)
print('✅ Database connection successful')
conn.close()
"
```

#### 2. Test S3 Access

```bash
python -c "
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3')
bucket = os.getenv('S3_BUCKET')
response = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
print(f'✅ S3 access successful (bucket: {bucket})')
"
```

#### 3. Test DeepSeek API

```bash
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL')
)

response = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': 'Say hello'}],
    max_tokens=10
)
print('✅ DeepSeek API working')
"
```

---

## Starting the System

### Start MCP Server

```bash
# Start server with validation
./scripts/start_mcp_server.sh

# Expected output:
# ======================================
# NBA MCP Server - Startup
# ======================================
#
# [1/5] Validating environment...
# ✅ Environment validated
#
# [2/5] Checking Python dependencies...
# ✅ Dependencies satisfied
#
# [3/5] Preparing log directory...
# ✅ Log directory ready
#
# [4/5] Starting MCP server...
#    Server PID: 12345
#    Log file: logs/mcp_server.log
#
# [5/5] Waiting for server to be ready...
# ✅ MCP server started successfully
#
# Server Information:
#    PID: 12345
#    Log: logs/mcp_server.log
#    URL: http://localhost:3000
#
# Server is ready! 🚀
```

### Monitor Server Logs

```bash
# Follow logs in real-time
tail -f logs/mcp_server.log

# Search for errors
grep ERROR logs/mcp_server.log

# View last 100 lines
tail -n 100 logs/mcp_server.log
```

### Stop MCP Server

```bash
# Graceful shutdown
./scripts/stop_mcp_server.sh

# Expected output:
# ======================================
# NBA MCP Server - Shutdown
# ======================================
#
# [1/3] Stopping MCP server (PID: 12345)...
# [2/3] Waiting for graceful shutdown...
# [3/3] Cleaning up...
# ✅ MCP server stopped successfully
```

---

## Verification

### End-to-End Integration Test

Run the comprehensive test suite:

```bash
# Run all E2E tests
python tests/test_e2e_workflow.py

# Expected output:
# ════════════════════════════════════════════════════════════
# NBA MCP Synthesis - End-to-End Integration Tests
# ════════════════════════════════════════════════════════════
#
# Running: Environment Setup
# ────────────────────────────────────────────────────────────
# ✅ All required environment variables are set
# ✅ PASSED: Environment Setup
#
# Running: MCP Server Startup
# ────────────────────────────────────────────────────────────
# ✅ MCP server is running
# ✅ PASSED: MCP Server Startup
#
# ... (more tests)
#
# ════════════════════════════════════════════════════════════
# Test Summary: 12 passed, 0 failed
# ════════════════════════════════════════════════════════════
```

### Quick Synthesis Test

```bash
# Test direct synthesis (no MCP server needed)
python scripts/test_synthesis_direct.py

# Should run 5 tests:
# 1. Simple SQL query generation
# 2. Code debugging
# 3. Statistical analysis
# 4. SQL optimization
# 5. Full synthesis workflow

# Total cost: ~$0.04
# Total time: ~30-60 seconds
```

### Manual Synthesis Test

```python
# Create test file: test_manual.py
from synthesis.multi_model_synthesis import synthesize_with_mcp_context
import asyncio

async def test():
    result = await synthesize_with_mcp_context(
        user_input="Calculate the sum of numbers 1 to 10",
        query_type="general_analysis",
        enable_ollama_verification=False
    )

    print(f"Status: {result['status']}")
    print(f"Cost: ${result['total_cost']:.6f}")
    print(f"Response: {result.get('final_explanation', 'No response')[:200]}...")

asyncio.run(test())
```

---

## Troubleshooting

### Common Issues

#### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution:**
```bash
pip install -r requirements.txt
# If still fails:
pip install mcp anthropic openai boto3 psycopg2-binary
```

#### Issue: "Connection refused" to database

**Solution:**
1. Check RDS security group allows your IP
2. Verify RDS endpoint is correct
3. Test with psql:
   ```bash
   psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DATABASE
   ```

#### Issue: "Access Denied" for S3

**Solution:**
1. Verify IAM user has S3 permissions
2. Check bucket name is correct
3. Ensure AWS credentials are valid:
   ```bash
   aws sts get-caller-identity
   ```

#### Issue: MCP server won't start

**Solution:**
1. Check if port 3000 is already in use:
   ```bash
   lsof -i :3000
   ```
2. Kill existing process if needed:
   ```bash
   kill -9 <PID>
   ```
3. Check logs:
   ```bash
   cat logs/mcp_server.log
   ```

#### Issue: High API costs

**Solution:**
1. DeepSeek should be primary model (~$0.001/query)
2. Use Ollama for free verification:
   ```bash
   # Install Ollama
   brew install ollama  # macOS
   # Pull model
   ollama pull qwen2.5-coder:32b
   ```
3. Monitor costs:
   ```bash
   grep "total_cost" logs/*.log | awk '{sum+=$NF} END {print "Total: $"sum}'
   ```

---

## Production Checklist

Before deploying to production, verify:

### Security

- [ ] `.env` file is NOT in git
- [ ] Database password is strong (20+ characters)
- [ ] AWS IAM user has minimal required permissions
- [ ] S3 bucket has proper access controls
- [ ] API keys are from production accounts
- [ ] Slack webhook (if used) is for production channel (e.g., #all-big-cat-bets)

### Performance

- [ ] Database has proper indexes
- [ ] S3 bucket is in same region as RDS
- [ ] Network latency is acceptable (<100ms to AWS)
- [ ] Sufficient RAM for concurrent requests (8GB+)

### Reliability

- [ ] All validation tests pass
- [ ] End-to-end tests pass
- [ ] Logs directory is writable
- [ ] Disk has sufficient space (10GB+ free)
- [ ] Backup strategy for critical data

### Monitoring

- [ ] Log rotation configured
- [ ] Error alerting set up (Slack/email)
- [ ] Cost tracking enabled
- [ ] Performance metrics collected

### Documentation

- [ ] Team knows how to start/stop server
- [ ] Troubleshooting guide is accessible
- [ ] Emergency contacts documented
- [ ] Runbook for common operations

---

## Next Steps

After successful deployment:

1. **Integrate with PyCharm** - See `PYCHARM_INTEGRATION_COMPLETE.md`
2. **Set up monitoring** - Configure Slack notifications
3. **Optimize costs** - Review API usage patterns
4. **Scale if needed** - Deploy MCP server to EC2 for better performance

---

## Support

- **Documentation:** See `docs/` directory
- **Examples:** See `examples/` and `scripts/test_*.py`
- **Issues:** Check `TROUBLESHOOTING.md`
- **Updates:** Check `CHANGELOG.md` for latest changes

---

**🎉 Congratulations! Your NBA MCP Synthesis System is deployed and ready to use.**
