# ✅ Workflow Environment Setup Complete!

## What Was Done

I've successfully created a separate `.env.workflow` file for your automated book analysis workflow with the following changes:

### 1. ✅ Created `.env.workflow`

A dedicated environment file containing:
- **Your existing LLM API keys** (Google, DeepSeek, Anthropic, OpenAI) - already filled in
- **Placeholder values** for Slack webhook and Linear API credentials
- **Default workflow settings** for cost management, notifications, retry logic, etc.

**Location:** `/Users/ryanranft/nba-mcp-synthesis/.env.workflow`

### 2. ✅ Updated Launch Scripts

Both launch scripts now load from `.env.workflow` instead of `.env`:

- **`scripts/launch_automated_workflow.sh`** - Manual launch script
- **`scripts/schedule_workflow.sh`** - Cron scheduler script

Both scripts now:
- Load credentials from `.env.workflow`
- Validate all required variables
- Export them to the environment
- Provide clear error messages if anything is missing

### 3. ✅ Created `.env.workflow.example`

A template file that's safe to commit to git (contains no real secrets). This makes it easy to:
- Share workflow setup with team members
- Document required environment variables
- Provide examples for new users

**Location:** `/Users/ryanranft/nba-mcp-synthesis/.env.workflow.example`

## 📋 What You Need to Add

Only **3 values** are missing from `.env.workflow`:

### 1. SLACK_WEBHOOK_URL ⚠️ REQUIRED

```bash
# Get from: https://api.slack.com/apps
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Steps:**
1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to your channel
5. Copy the webhook URL

### 2. LINEAR_API_KEY ⚠️ REQUIRED

```bash
# Get from: https://linear.app/settings/api
LINEAR_API_KEY=lin_api_YOUR_LINEAR_API_KEY
```

**Steps:**
1. Go to https://linear.app/settings/api
2. Click "Create new Personal API Key"
3. Give it a name (e.g., "NBA Book Analysis Workflow")
4. Copy the key (starts with `lin_api_`)

### 3. LINEAR_TEAM_ID & LINEAR_PROJECT_ID ⚠️ REQUIRED

```bash
# Get by running the test script after setting LINEAR_API_KEY
LINEAR_TEAM_ID=YOUR_TEAM_ID
LINEAR_PROJECT_ID=YOUR_PROJECT_ID
```

**Steps:**
1. After setting LINEAR_API_KEY in `.env.workflow`
2. Run: `python3 scripts/test_notifications.py`
3. Copy the team ID and project ID from the output

## 🚀 Quick Start Guide

```bash
# Step 1: Edit .env.workflow and add your Slack webhook
nano .env.workflow
# or
code .env.workflow

# Step 2: Add your Linear API key to .env.workflow

# Step 3: Test to get team/project IDs
python3 scripts/test_notifications.py

# Step 4: Add team/project IDs to .env.workflow

# Step 5: Test the complete workflow
./scripts/launch_automated_workflow.sh
```

## 📊 Current Status

**Your `.env.workflow` file contains:**

```
✅ GOOGLE_API_KEY (already set)
✅ DEEPSEEK_API_KEY (already set)
✅ ANTHROPIC_API_KEY (already set)
✅ OPENAI_API_KEY (already set)
✅ WORKFLOW_ENABLE_NOTIFICATIONS (default: true)
✅ WORKFLOW_ENABLE_LINEAR_ISSUES (default: true)
✅ WORKFLOW_CRITICAL_STAGES (default: pre_flight,book_analysis)
✅ All optional settings (cost management, retry logic, etc.)

❌ SLACK_WEBHOOK_URL (you need to add)
❌ LINEAR_API_KEY (you need to add)
❌ LINEAR_TEAM_ID (you need to add)
❌ LINEAR_PROJECT_ID (you need to add)
```

## 🎯 Benefits of Separate .env.workflow

1. **Security** - Keep workflow credentials separate from main project
2. **Portability** - Easy to share workflow setup without exposing other secrets
3. **Organization** - Clear separation of concerns
4. **Flexibility** - Can use different credentials for workflow vs. main project
5. **Git-friendly** - `.env.workflow.example` can be committed safely

## 📁 Files Created

```
/Users/ryanranft/nba-mcp-synthesis/
├── .env.workflow                    # Your workflow environment (DO NOT COMMIT)
├── .env.workflow.example            # Template (SAFE TO COMMIT)
├── WORKFLOW_ENV_SETUP.md            # Detailed setup guide
├── WORKFLOW_SETUP_COMPLETE.md       # This summary
└── scripts/
    ├── launch_automated_workflow.sh # Updated to use .env.workflow
    └── schedule_workflow.sh         # Updated to use .env.workflow
```

## 🔒 Security Notes

- `.env.workflow` is in `.gitignore` and will NOT be committed to git
- `.env.workflow.example` is safe to commit (contains no real secrets)
- Your API keys are kept separate from the main project
- Scripts validate all required variables before running

## 📝 Next Steps

1. **Open `.env.workflow`** in your editor
2. **Add your Slack webhook URL** (get from https://api.slack.com/apps)
3. **Add your Linear API key** (get from https://linear.app/settings/api)
4. **Run test script** to get team/project IDs: `python3 scripts/test_notifications.py`
5. **Add team/project IDs** to `.env.workflow`
6. **Launch workflow**: `./scripts/launch_automated_workflow.sh`

## 🎉 Ready to Launch!

Once you add the 3 missing values, you'll be ready to launch the fully automated workflow! The system will:

- ✅ Load all credentials from `.env.workflow`
- ✅ Validate everything is set correctly
- ✅ Send Slack notifications at each stage
- ✅ Create Linear issues for all recommendations
- ✅ Generate 200+ implementation files
- ✅ Send you a completion notification

**All while you sleep!** 🌙

---

**Need help?** Check `WORKFLOW_ENV_SETUP.md` for detailed setup instructions or run `python3 scripts/test_notifications.py` to test your configuration.




