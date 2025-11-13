# NBA MCP Synthesis - Claude Code Configuration

## Database Credentials Location

**IMPORTANT:** This project uses the **hierarchical secrets management system** defined in `/Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md`.

**DO NOT** store credentials in `.env` files in the project directory!

---

## Credentials Storage Locations

### Production Credentials (WORKFLOW Context)

**Location:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

**Files:**
- `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env` - PostgreSQL host
- `RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env` - PostgreSQL port (5432)
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Database name
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Database username
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Database password

### Development Credentials (DEVELOPMENT Context)

**Location:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/
```

**Files:**
- `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `RDS_PORT_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`

---

## How to Load Credentials in Code

### Python Applications

**Method 1: Auto-Detection (Recommended)**

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
import os

# Auto-detects project, sport, and context
load_secrets_hierarchical()

# Access database credentials
db_host = os.getenv('RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW')
db_port = os.getenv('RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW')
db_name = os.getenv('RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW')
db_user = os.getenv('RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW')
db_pass = os.getenv('RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW')
```

**Method 2: Explicit Context**

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
import os

# Explicitly specify production context
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

# Or development context
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")

# Access credentials (same as above)
```

**Method 3: Using Helper Function**

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config

# Load secrets
load_secrets_hierarchical()

# Get database config as dictionary
db_config = get_database_config()
# Returns: {'host': '...', 'port': '...', 'database': '...', 'user': '...', 'password': '...'}

# Use with psycopg2
import psycopg2
conn = psycopg2.connect(**db_config)
```

### Shell Scripts

```bash
#!/bin/bash

# Source the universal loader
source /Users/ryanranft/load_secrets_universal.sh

# Verify secrets loaded
if [ "$SECRETS_LOADED" != "true" ]; then
    echo "❌ Failed to load secrets"
    exit 1
fi

# Use database credentials
echo "Database: $RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW"
echo "Host: $RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW"

# Run your script with loaded secrets
python3 your_script.py
```

---

## Database Sharing

**Important:** nba-mcp-synthesis shares the **same PostgreSQL database** as nba-simulator-aws.

Both projects use identical credentials (same host, port, database, username, password).

---

## Naming Convention

All credentials follow the pattern: `SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT.env`

**Components:**
- `SERVICE`: `RDS` (PostgreSQL on AWS)
- `RESOURCE_TYPE`: `HOST`, `PORT`, `DATABASE`, `USERNAME`, `PASSWORD`
- `PROJECT`: `NBA_MCP_SYNTHESIS`
- `CONTEXT`: `WORKFLOW` (production) or `DEVELOPMENT`

**Examples:**
```
RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env
RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
```

---

## Backwards Compatibility

The unified_secrets_manager automatically creates aliases for old naming conventions:

**New naming (hierarchical):**
- `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW`

**Auto-created aliases:**
- `RDS_HOST` (simple form)
- `DB_HOST` (alternative prefix)
- `DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW` (alternative with context)

This ensures existing code continues to work while migrating to the new system.

---

## Verification

### Test Secret Loading

```bash
cd /Users/ryanranft/nba-mcp-synthesis

python3 -c "
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
import os

# Load secrets
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

# Get database config
config = get_database_config()

# Display status
print('✅ Database Credentials Loaded:')
print(f'  Host: {config[\"host\"][:20]}...' if config['host'] else '❌ Missing')
print(f'  Port: {config[\"port\"]}')
print(f'  Database: {config[\"database\"]}')
print(f'  User: {config[\"user\"]}')
print(f'  Password: {\"***\" if config[\"password\"] else \"❌ Missing\"}')
"
```

### Test Database Connection

```bash
python3 scripts/test_database_credentials.py --context production
```

---

## Troubleshooting

### "Credentials not loading"

**Check:**
1. File permissions (should be 600)
   ```bash
   ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/RDS_*
   ```

2. File naming matches expected pattern
3. Using correct context (`production` vs `development`)

### "Database connection failed"

**Verify:**
1. Credentials are correct:
   ```python
   from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
   load_secrets_hierarchical()
   print(get_database_config())
   ```

2. Database is accessible from your network
3. Firewall/security groups allow connection

### "Cannot find unified_secrets_manager"

**Solution:**
```bash
# Ensure you're in the project directory
cd /Users/ryanranft/nba-mcp-synthesis

# Verify the module exists
ls -la mcp_server/unified_secrets_manager.py

# Add project to Python path if needed
export PYTHONPATH="${PYTHONPATH}:/Users/ryanranft/nba-mcp-synthesis"
```

---

## Security Best Practices

1. **Never commit credential files** to version control
2. **Never store credentials** in `.env` files in project directory
3. **Always use** the hierarchical secrets system
4. **Set proper permissions** on credential files (600)
5. **Use context suffixes** to separate production/development credentials
6. **Rotate credentials** regularly
7. **Monitor secret health** with health checks

---

## SMS/Twilio Notifications

**Location:** SMS credentials are stored in the same hierarchical structure as database credentials.

### Production Credentials

**Directory:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

**Files:**
- `TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Twilio Account SID
- `TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Twilio Auth Token (sensitive!)
- `TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Twilio phone number (+12345678901)
- `TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_WORKFLOW.env` - Recipient phone number(s) (comma-separated)

### Development Credentials

**Directory:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development/
```

**Files:**
- `TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`
- `TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_DEVELOPMENT.env`

### Usage in Code

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.betting.notifications import NotificationManager

# Load secrets (auto-loads SMS credentials)
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

# Initialize notification manager
notifier = NotificationManager(config={
    'sms': {'enabled': True}
})

# Send SMS
result = notifier.send_message(
    subject='NBA Betting Alert',
    message='Critical threshold breached!',
    channels=['sms']
)
```

### Environment Variables Available

After loading secrets, these environment variables are available:

**Full names:**
- `TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_WORKFLOW`
- `TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW`
- `TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_WORKFLOW`
- `TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_WORKFLOW`

**Short name aliases (backward compatible):**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `TWILIO_TO_NUMBERS`

### Testing SMS Integration

```bash
# Test credential loading
python scripts/test_sms_integration.py --context production

# Send test SMS
python scripts/test_sms_integration.py --context production --send-sms

# Test alert system with SMS
python scripts/test_alert_sms.py --context production --critical-only
```

### Production Usage

**Paper trading with SMS:**
```bash
python scripts/paper_trade_today.py --sms
```

**Daily report via SMS:**
```bash
python scripts/generate_daily_report.py --sms
```

**Setup new credentials:**
```bash
./scripts/setup_sms_credentials.sh --context production
```

### Cost Management

- **Free Trial:** $15 credit (~500 SMS)
- **After Trial:** ~$0.0075/SMS + $1-2/month for phone number
- **Best Practice:** Use SMS only for critical alerts (10%+ edge bets)

### Troubleshooting

**"SMS config incomplete"**
- Verify credential files exist in hierarchical structure
- Check file permissions are 600
- Ensure phone numbers are in E.164 format (+countrycode + number)

**"Unable to create record: Unverified number"**
- Trial accounts can only send to verified numbers
- Verify recipient in Twilio dashboard or upgrade account

---

## Related Documentation

- **Hierarchical Secrets System:** `/Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md`
- **Unified Secrets Manager:** `/Users/ryanranft/nba-mcp-synthesis/mcp_server/unified_secrets_manager.py`
- **SMS Setup Guide:** `/Users/ryanranft/nba-mcp-synthesis/SMS_SETUP_GUIDE.md`
- **Calibration Training:** `/Users/ryanranft/nba-mcp-synthesis/docs/CALIBRATION_TRAINING_GUIDE.md`

---

## Quick Reference

### Load Production Secrets
```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
```

### Load Development Secrets
```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")
```

### Get Database Config
```python
from mcp_server.unified_secrets_manager import get_database_config
db_config = get_database_config()
```

### Environment Variables Available
After loading secrets, these are available:
- `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW` (or `_DEVELOPMENT`)
- `RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW`

Plus backwards-compatible aliases:
- `RDS_HOST`, `DB_HOST`, `DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW`, etc.

---

## Task Tracking Protocol (MANDATORY)

**CRITICAL:** You MUST create and maintain tasks for every user request that involves work to be done.

### When to Create Tasks (ALWAYS)

Create tasks immediately when user:
- Asks you to "research", "analyze", "build", "create", "fix", "implement", "investigate", "compare", "test", "deploy"
- Provides any request with multiple steps (>2 distinct actions)
- Assigns complex work (anything taking >5 minutes)
- Continues work from previous sessions

**DO NOT** create tasks for:
- Simple questions/explanations
- Single-step operations
- Purely conversational interactions

### Task Creation Pattern

**1. IMMEDIATE task creation when user assigns work:**

```markdown
[Use TodoWrite or Task MCP to create tasks]

Example structure:
1. Main task from user request (priority: high)
2. Sub-task 1: Specific action needed
3. Sub-task 2: Specific action needed
4. Sub-task 3: Verification/testing
```

**2. Update status BEFORE starting work:**
- Change from "pending" to "in_progress"
- Have exactly ONE task "in_progress" at a time

**3. Mark complete IMMEDIATELY after finishing:**
- Change from "in_progress" to "completed"
- Do NOT batch completions - update as you go

### Session Start Protocol

**At the beginning of EVERY conversation:**

1. **Check for existing tasks:**
   - Query Task Tracker MCP for pending/in_progress tasks
   - Check for HANDOFF documents in project root

2. **Display to user:**
   - Show all pending/in-progress tasks
   - Ask which task to continue or if starting new work

3. **Resume or start:**
   - If continuing: mark resumed task as "in_progress"
   - If new work: create fresh task list

### During Work Protocol

**While working on tasks:**

1. **Update frequently:**
   - Mark task "in_progress" when you start
   - Mark "completed" immediately when done
   - Add notes for discoveries/issues

2. **Track problems:**
   - If encountering blockers, note in task
   - If discovering improvements, add to Future Improvements

3. **Stay on track:**
   - Reference current task in your responses
   - Don't jump to new tasks without updating status

### Session End Protocol

**Before conversation ends:**

1. **Review all tasks:**
   - Verify statuses are accurate
   - Ensure nothing marked "in_progress" incorrectly

2. **For incomplete work:**
   - Suggest creating HANDOFF document if complex
   - Ensure all pending tasks are properly documented

3. **Summarize:**
   - Tell user what was completed
   - List what remains pending

### Task Tracking Tools Available

**Built-in TodoWrite:** For session-level tracking (doesn't persist)

**Task Tracker MCP:** For persistent cross-session tracking (preferred)
- `create_task` - Add new task
- `list_tasks` - View all tasks
- `update_task_status` - Change status
- `get_active_tasks` - See current work

**UserPromptSubmit Hook:** Automatically extracts tasks from user prompts and injects them as context

### Enforcement

**This is NON-NEGOTIABLE:**
- Task tracking prevents wasted time
- Enables continuity across sessions
- Helps user stay organized
- Essential for complex multi-session projects

**VIOLATION CONSEQUENCES:**
- User loses track of progress
- Work gets duplicated
- Context is lost between sessions
- User frustration increases

**Your commitment:** Use task tracking religiously for all non-trivial work.

---

*Last updated: 2025-11-12*
*System: Hierarchical Secrets Management + Automatic Task Tracking*
