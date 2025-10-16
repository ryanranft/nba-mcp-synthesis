# Workflow Environment Setup Guide

## ✅ Completed

I've created a separate `.env.workflow` file specifically for the automated book analysis workflow. This keeps your workflow credentials separate from your main project configuration.

## 📁 Files Created

1. **`.env.workflow`** - Your workflow-specific environment file (with your existing API keys already filled in)
2. **`.env.workflow.example`** - Template file safe to commit to git
3. **Updated `scripts/launch_automated_workflow.sh`** - Now loads from `.env.workflow`
4. **Updated `scripts/schedule_workflow.sh`** - Now loads from `.env.workflow`

## 🔑 What You Already Have

Your `.env.workflow` file already contains:
- ✅ GOOGLE_API_KEY
- ✅ DEEPSEEK_API_KEY
- ✅ ANTHROPIC_API_KEY
- ✅ OPENAI_API_KEY

## ❌ What You Need to Add

You need to add **3 values** to `.env.workflow`:

### 1. SLACK_WEBHOOK_URL

**How to get it:**
```bash
# 1. Go to https://api.slack.com/apps
# 2. Create a new app or select existing
# 3. Enable "Incoming Webhooks"
# 4. Click "Add New Webhook to Workspace"
# 5. Select your channel (e.g., #nba-simulator-notifications)
# 6. Copy the webhook URL
```

**Add to .env.workflow:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
```

### 2. LINEAR_API_KEY

**How to get it:**
```bash
# 1. Go to https://linear.app/settings/api
# 2. Click "Create new Personal API Key"
# 3. Give it a name (e.g., "NBA Book Analysis Workflow")
# 4. Copy the key (starts with lin_api_)
```

**Add to .env.workflow:**
```bash
LINEAR_API_KEY=lin_api_...
```

### 3. LINEAR_TEAM_ID and LINEAR_PROJECT_ID

**How to get them:**
```bash
# After setting LINEAR_API_KEY, run:
python3 scripts/test_notifications.py

# It will show your team IDs and projects
# Copy the IDs you want to use
```

**Add to .env.workflow:**
```bash
LINEAR_TEAM_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
LINEAR_PROJECT_ID=p1q2r3s4-t5u6-7890-vwxy-z1234567890
```

## 🚀 Quick Setup

```bash
# 1. Edit .env.workflow and add your Slack webhook
nano .env.workflow
# or
code .env.workflow

# 2. Add your Linear API key to .env.workflow

# 3. Test to get team/project IDs
python3 scripts/test_notifications.py

# 4. Add team/project IDs to .env.workflow

# 5. Test the complete workflow
./scripts/launch_automated_workflow.sh
```

## 📋 Current Status

**File:** `.env.workflow`

```
✅ GOOGLE_API_KEY (set)
✅ DEEPSEEK_API_KEY (set)
✅ ANTHROPIC_API_KEY (set)
✅ OPENAI_API_KEY (set)
❌ SLACK_WEBHOOK_URL (needs your value)
❌ LINEAR_API_KEY (needs your value)
❌ LINEAR_TEAM_ID (needs your value - get after setting LINEAR_API_KEY)
❌ LINEAR_PROJECT_ID (needs your value - get after setting LINEAR_API_KEY)
```

## 🎯 Next Steps

1. **Add Slack webhook** to `.env.workflow`
2. **Add Linear API key** to `.env.workflow`
3. **Run test script** to get team/project IDs
4. **Add team/project IDs** to `.env.workflow`
5. **Launch workflow** with `./scripts/launch_automated_workflow.sh`

## 🔒 Security

- `.env.workflow` is in `.gitignore` and will NOT be committed
- `.env.workflow.example` is safe to commit (contains no secrets)
- Your API keys are kept separate from the main project
- Easy to share workflow setup without exposing secrets

## 📝 Example .env.workflow (After You Fill It In)

```bash
# LLM API Keys (Already set)
GOOGLE_API_KEY=${GOOGLE_API_KEY_REVOKED}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY_REVOKED}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY_REVOKED}
OPENAI_API_KEY=${OPENAI_API_KEY_REVOKED}

# Slack (You need to add)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T01ABC123/B01DEF456/xyz789...
SLACK_CHANNEL=#nba-simulator-notifications

# Linear (You need to add)
LINEAR_API_KEY=lin_api_abc123def456ghi789...
LINEAR_TEAM_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
LINEAR_PROJECT_ID=p1q2r3s4-t5u6-7890-vwxy-z1234567890

# Workflow Settings (Already set - use defaults)
WORKFLOW_ENABLE_NOTIFICATIONS=true
WORKFLOW_ENABLE_LINEAR_ISSUES=true
WORKFLOW_CRITICAL_STAGES=pre_flight,book_analysis
```

## ✅ Ready to Go!

Once you add the 3 missing values, you'll be ready to launch the automated workflow! The system will:

1. Load credentials from `.env.workflow`
2. Validate all required variables
3. Send Slack notifications at each stage
4. Create Linear issues for all recommendations
5. Generate 200+ implementation files
6. Send you a completion notification

**All while you sleep!** 🌙




