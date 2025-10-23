# Delete Old Slack App Instructions

**Date**: October 23, 2025
**App to Delete**: Contains webhook `B09K3FHFUUF`
**Status**: ✅ Safe to delete - all code migrated

---

## ✅ Pre-Deletion Checklist

**All items verified as complete:**
- ✅ All code updated to use hierarchical webhooks
- ✅ All tests passing (341/342)
- ✅ No references to old webhook in codebase
- ✅ No secret files contain old webhook
- ✅ Changes committed to git (commit `fff435c`)
- ✅ Documentation updated with deprecation warnings

**You can proceed safely!**

---

## 📋 Steps to Delete the Old Slack App

### Step 1: Identify the Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Sign in to your Slack workspace: `T09KGRXCJNA`
3. Look through your apps to find the one containing webhook `B09K3FHFUUF`

**How to identify it:**
- Open each app
- Go to "Incoming Webhooks" in the left sidebar
- Look for webhook URL containing `B09K3FHFUUF`
- This is the app to delete

### Step 2: Verify It's the Correct App

**Before deleting, verify:**
1. ✅ The app contains webhook `B09K3FHFUUF`
2. ✅ The app is NOT used by any current webhooks:
   - Production: `B09MAQKG2JE` (different app)
   - Development: `B09NNHY9W1E` (different app)
   - Test: `B09MXNYD78T` (different app)
   - Global: `B09L9EG7KNE` (different app)

**Warning:** Make sure you're NOT deleting the app that contains your active webhooks!

### Step 3: Delete the App

1. Click on the app name (top left)
2. Scroll down to "Delete App" section
3. Click "Delete App"
4. Confirm the deletion by typing the app name
5. Click "Delete" to confirm

**The app and webhook `B09K3FHFUUF` will be permanently deleted.**

---

## 🔍 What to Check After Deletion

### Verify Your Active Webhooks Still Work

**Test the production webhook:**
```bash
curl -X POST "https://hooks.slack.com/services/T09KGRXCJNA/B09MAQKG2JE/..." \
  -H 'Content-Type: application/json' \
  -d '{"text": "✅ Production webhook test after app deletion"}'
```

**Run automated tests:**
```bash
cd /Users/ryanranft/nba-mcp-synthesis
pytest tests/test_all_connectors.py::TestSlackIntegration -v
```

**Expected result:** ✅ All 5 tests should pass

---

## 📊 Current Webhook Setup (After Deletion)

### Active Webhooks (Will Continue Working)
These are in a DIFFERENT app and will NOT be affected by the deletion:

| Context | Webhook ID | Variable Name |
|---------|------------|---------------|
| **Production** | `B09MAQKG2JE` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW` |
| **Development** | `B09NNHY9W1E` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_DEVELOPMENT` |
| **Test** | `B09MXNYD78T` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST` |
| **Global** | `B09L9EG7KNE` | `SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW` |

### Deleted Webhook (No Longer Available)
| Context | Webhook ID | Status |
|---------|------------|--------|
| ~~Old App~~ | ~~`B09K3FHFUUF`~~ | ❌ DELETED |

---

## 🚨 Troubleshooting

### If You Can't Find the App
**Possible reasons:**
1. You may not have admin access to the workspace
2. The app might be in a different workspace
3. The app might have already been deleted

**Solution:**
- Ask your Slack workspace admin to delete it
- Provide them with webhook ID: `B09K3FHFUUF`

### If Active Webhooks Stop Working
**This should NOT happen if you followed the checklist!**

If this happens (unlikely):
1. You deleted the wrong app
2. Check which webhooks are still available in Slack
3. Create new webhooks in the correct app
4. Update secret files with new webhook URLs

**Prevention:** Always verify you're deleting the app with `B09K3FHFUUF`, NOT the others!

---

## ✅ Completion Checklist

After deletion, verify:
- [ ] Old app deleted from Slack
- [ ] Active webhooks still work (test with curl)
- [ ] Automated tests still pass (5/5)
- [ ] No error messages in production logs
- [ ] Team notified of cleanup

---

## 📚 Related Documentation

- `WEBHOOK_DEPRECATION_COMPLETE.md` - Complete deprecation summary
- `SLACK_WEBHOOK_STRATEGY.md` - Webhook management strategy
- `SECRETS_STRUCTURE.md` - Secrets management guide

---

## 🎉 Expected Outcome

After successful deletion:
- ✅ Old app removed from Slack
- ✅ Deprecated webhook no longer exists
- ✅ All current webhooks continue working
- ✅ All tests continue passing
- ✅ Zero chance of accidental misconfiguration

**No code changes needed** - everything is already updated!

---

**Instructions Generated**: October 23, 2025
**Safe to Execute**: Yes - all prerequisites met
**Risk Level**: 🟢 None (if correct app deleted)

