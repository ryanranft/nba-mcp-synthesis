# Comprehensive Scrubbing Plan - Option A

**Created**: 2025-10-18 20:55 UTC
**Status**: 🚨 **URGENT - Real API Keys Exposed**
**Severity**: HIGH

---

## 🚨 Exposed Secrets Found

### In Commit 9e4ed46 (WORKFLOW_ENV_SETUP.md:130-131)

1. **Google/Gemini API Key**
   ```
   ${GOOGLE_API_KEY_REVOKED}
   ```
   - Service: Google Generative Language API
   - Risk: HIGH - Can incur costs

2. **DeepSeek API Key**
   ```
   ${DEEPSEEK_API_KEY_REVOKED}
   ```
   - Service: DeepSeek AI
   - Risk: MEDIUM - Can incur costs

3. **Anthropic API Key**
   ```
   ${ANTHROPIC_API_KEY_REVOKED}
   ```
   - Service: Claude/Anthropic
   - Risk: HIGH - Can incur costs

4. **OpenAI API Key**
   ```
   ${OPENAI_API_KEY_REVOKED}
   ```
   - Service: OpenAI/ChatGPT
   - Risk: HIGH - Can incur costs

5. **Slack Webhook URL**
   ```
   ${SLACK_WEBHOOK_URL_REVOKED}
   ```
   - Service: Slack Incoming Webhook
   - Risk: MEDIUM - Can send spam to Slack

### Plus: Google Cloud IDs (Already Being Scrubbed)

- `${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}`
- `${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}`
- `${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}`

---

## 📋 Execution Plan

### Phase 1: IMMEDIATE REVOCATION (URGENT - Do First!)

**⚠️ STOP READING - DO THIS NOW:**

#### 1.1 Revoke Google/Gemini API Key (2 minutes)

```bash
# Visit Google Cloud Console
open "https://console.cloud.google.com/apis/credentials?project=${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}"

# Steps:
# 1. Find API key: ${GOOGLE_API_KEY_REVOKED}
# 2. Click "Delete" or "Disable"
# 3. Confirm deletion
```

Or via CLI:
```bash
gcloud alpha services api-keys delete ${GOOGLE_API_KEY_REVOKED} \
  --project=${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
```

#### 1.2 Revoke Anthropic API Key (2 minutes)

```bash
# Visit Anthropic Console
open "https://console.anthropic.com/settings/keys"

# Steps:
# 1. Find key ending in: ...R1MhBgAA
# 2. Click "Delete"
# 3. Confirm deletion
```

#### 1.3 Revoke OpenAI API Key (2 minutes)

```bash
# Visit OpenAI Platform
open "https://platform.openai.com/api-keys"

# Steps:
# 1. Find key starting with: sk-proj-n0vYpupv...
# 2. Click "Revoke"
# 3. Confirm revocation
```

#### 1.4 Revoke DeepSeek API Key (2 minutes)

```bash
# Visit DeepSeek Platform
open "https://platform.deepseek.com/api_keys"

# Steps:
# 1. Find key: ${DEEPSEEK_API_KEY_REVOKED}
# 2. Delete the key
```

#### 1.5 Revoke Slack Webhook (2 minutes)

```bash
# Visit Slack App Settings
open "https://api.slack.com/apps"

# Steps:
# 1. Find app with webhook: T09KGRXCJNA
# 2. Go to "Incoming Webhooks"
# 3. Delete the webhook URL
```

**⏱️ Total Time**: 10 minutes
**Status**: ⏳ **PENDING - DO THIS FIRST**

---

### Phase 2: CREATE REPLACEMENT FILE (5 minutes)

After keys are revoked, create a comprehensive replacement file:

```bash
cat > /tmp/comprehensive-replacements.txt << 'EOF'
***REMOVED***
${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}==>${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}==>${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}
${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}==>${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
${BIGQUERY_BILLING_EXPORT_TABLE}==>${BIGQUERY_BILLING_EXPORT_TABLE}

# API Keys (REVOKED)
${GOOGLE_API_KEY_REVOKED}==>${GOOGLE_API_KEY_REVOKED}
${DEEPSEEK_API_KEY_REVOKED}==>${DEEPSEEK_API_KEY_REVOKED}
${ANTHROPIC_API_KEY_REVOKED}==>${ANTHROPIC_API_KEY_REVOKED}
${OPENAI_API_KEY_REVOKED}==>${OPENAI_API_KEY_REVOKED}

# Slack Webhook (REVOKED)
${SLACK_WEBHOOK_URL_REVOKED}==>${SLACK_WEBHOOK_URL_REVOKED}
EOF
```

---

### Phase 3: RUN BFG SCRUBBING (10 minutes)

```bash
# Navigate to parent directory
cd /Users/ryanranft

# Remove old mirror
rm -rf nba-mcp-synthesis-mirror.git

# Create fresh mirror
git clone --mirror nba-mcp-synthesis nba-mcp-synthesis-mirror.git

# Navigate to mirror
cd nba-mcp-synthesis-mirror.git

# Run BFG with comprehensive replacements
bfg --replace-text /tmp/comprehensive-replacements.txt .

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

### Phase 4: VERIFY SCRUBBING (5 minutes)

```bash
cd /Users/ryanranft/nba-mcp-synthesis-mirror.git

# Check for any remaining API keys
git log --all -S "${GOOGLE_API_KEY_REVOKED}" --oneline
git log --all -S "sk-ant-api03" --oneline
git log --all -S "sk-proj-n0vYpupv" --oneline

# Should return no results
```

---

### Phase 5: FORCE PUSH TO GITHUB (5 minutes)

```bash
cd /Users/ryanranft/nba-mcp-synthesis-mirror.git

# Push cleaned history
git push --force --all

# Push tags
git push --force --tags
```

---

### Phase 6: SYNC LOCAL REPOSITORY (5 minutes)

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Fetch cleaned history
git fetch origin

# Reset to cleaned history
git reset --hard origin/main

# Verify
git log --oneline -5
```

---

### Phase 7: GENERATE NEW API KEYS (10 minutes)

After scrubbing is complete, generate new keys:

#### Google/Gemini API Key
```bash
# Visit: https://console.cloud.google.com/apis/credentials
# Click: "Create Credentials" > "API Key"
# Restrict to: Generative Language API
# Store in: .env.google_cloud (gitignored)
```

#### Anthropic API Key
```bash
# Visit: https://console.anthropic.com/settings/keys
# Click: "Create Key"
# Store in: secrets/anthropic/api_keys/...
```

#### OpenAI API Key
```bash
# Visit: https://platform.openai.com/api-keys
# Click: "Create new secret key"
# Store in: secrets/openai/api_keys/...
```

#### DeepSeek API Key
```bash
# Visit: https://platform.deepseek.com/api_keys
# Generate new key
# Store in: secrets/deepseek/api_keys/...
```

#### Slack Webhook
```bash
# Visit: https://api.slack.com/apps
# Recreate incoming webhook
# Store in: secrets/slack/webhooks/...
```

---

### Phase 8: UPDATE DOCUMENTATION (5 minutes)

Update all references to use environment variables:

```bash
# Files to update:
# - WORKFLOW_ENV_SETUP.md
# - docs/API_DOCUMENTATION.md
# - docs/TROUBLESHOOTING_GUIDE.md
# - scripts/launch_self_healing_workflow.sh
```

---

## 📊 Timeline Summary

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Revoke API Keys | 10 min | ⏳ PENDING |
| 2 | Create Replacement File | 5 min | ⏳ PENDING |
| 3 | Run BFG Scrubbing | 10 min | ⏳ PENDING |
| 4 | Verify Scrubbing | 5 min | ⏳ PENDING |
| 5 | Force Push to GitHub | 5 min | ⏳ PENDING |
| 6 | Sync Local Repository | 5 min | ⏳ PENDING |
| 7 | Generate New API Keys | 10 min | ⏳ PENDING |
| 8 | Update Documentation | 5 min | ⏳ PENDING |
| **TOTAL** | | **55 min** | |

---

## ⚠️ IMPORTANT NOTES

### Before Starting

1. **Confirm Keys Are Yours**: Verify these are your actual keys before revoking
2. **Save Backup**: Backup is at `/Users/ryanranft/nba-mcp-synthesis-backup-20251018-204942`
3. **Stop All Services**: Ensure no services are actively using these keys

### During Execution

1. **Revoke First, Scrub Second**: Always revoke before scrubbing (prevent race condition)
2. **Verify Each Step**: Don't proceed until current step is verified
3. **Keep Terminal Open**: Don't close terminal until complete

### After Completion

1. **Test New Keys**: Verify new keys work before deleting old ones
2. **Monitor Billing**: Watch for unusual charges in the next 24 hours
3. **Update Team**: Notify anyone who may have cached the old keys

---

## 🆘 Emergency Contacts

If something goes wrong:

- **Google Cloud Support**: https://cloud.google.com/support
- **Anthropic Support**: https://support.anthropic.com
- **OpenAI Support**: https://help.openai.com
- **Slack Support**: https://slack.com/help

---

## ✅ Success Criteria

Scrubbing is complete when:

1. [ ] All 5 API keys revoked
2. [ ] BFG successfully replaced all secrets
3. [ ] Git history contains no real API keys
4. [ ] GitHub push protection passes
5. [ ] Local repository synced with cleaned history
6. [ ] New API keys generated and stored securely
7. [ ] All services working with new keys
8. [ ] Documentation updated with placeholders

---

**Next Step**: Start with Phase 1 - Revoke API Keys **NOW**

**Time to Complete**: ~1 hour
**Safety**: Backup created, can restore if needed
**Result**: Completely clean history, all secrets removed

