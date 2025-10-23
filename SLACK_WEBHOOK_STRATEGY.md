# Slack Webhook Strategy

## Overview
This project uses separate Slack webhooks for production and testing environments to prevent test notifications from spamming production channels.

## Webhook Configuration

### Production Webhook
- **Secret**: `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW`
- **Channel**: `#nba-simulator-notifications`
- **Purpose**: Real deployment notifications, alerts, status updates
- **Usage**: Production code, manual deployments

### Test Webhook
- **Secret**: `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST`
- **Channel**: `#nba-simulator-test-notifications`
- **Purpose**: Automated test notifications, CI/CD validation
- **Usage**: Test suite, CI/CD pipelines

## Test Behavior

### Automated Test (`test_real_slack_notification`)
The Slack integration test follows this logic:

1. **Check for test webhook** (`SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST`)
2. **If found**: Send test notification, validate response
3. **If not found**: Skip test with mock (local development)

### Running the Test

**With Test Webhook (Automatic)**:
```bash
# Secrets automatically loaded from test context
pytest tests/test_all_connectors.py::TestSlackIntegration::test_real_slack_notification -v
```

**Without Webhook (Mocked)**:
```bash
# Test will skip gracefully if no webhook configured
pytest tests/test_all_connectors.py::TestSlackIntegration::test_real_slack_notification -v
```

## Benefits

1. **Safety**: Test messages never reach production channel
2. **Automation**: CI/CD can validate Slack integration
3. **Visibility**: Test channel shows all automated notifications
4. **Isolation**: Production channel only has real alerts

## Adding New Webhooks

To add webhooks for other services (Discord, Teams, etc.), follow this pattern:

1. Create separate webhooks for TEST and WORKFLOW contexts
2. Store in appropriate secret files following naming convention
3. Update tests to prefer TEST webhook, fall back to mock
4. Document in `.env.example` and this file

## Troubleshooting

**Test skipping even with webhook?**
- Verify secret file exists in TEST context directory
- Check file permissions (should be 600)
- Ensure webhook URL is valid

**Test failing with 404?**
- Webhook URL may be invalid or expired
- Regenerate webhook in Slack and update secret file

**Want to test without sending messages?**
- Remove the test webhook secret file
- Test will automatically use mocks

## Example Notification

When the test runs successfully, it sends a message to the test channel:

```
🧪 Test Notification
✅ Slack integration test passed!

Operation: 🧪 Test Notification
Models: deepseek, claude
Execution Time: 1.5s
Tokens: 500
Success: Yes
```

## Secret File Location

The test webhook is stored at:
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.test/SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST.env
```

Content (single line):
```
https://hooks.slack.com/services/T09KGRXCJNA/B09MXNYD78T/[REDACTED]
```

## Production Deployment

When deploying to production:
- Ensure `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW` points to production channel
- Test webhook remains pointed at test channel
- CI/CD validates Slack integration using test webhook before deployment
- No production spam during development or testing

## Monitoring

### Test Channel Activity
Expected notifications in `#nba-simulator-test-notifications`:
- Automated test runs from CI/CD
- Developer test runs during feature development
- Integration validation during deployments

### Production Channel Activity
Expected notifications in `#nba-simulator-notifications`:
- Successful deployments
- System alerts and errors
- Status updates for long-running processes
- Real synthesis workflow completions

## Best Practices

1. **Never use production webhook in tests** - Always use TEST context
2. **Keep test channel accessible** - Team should be able to see test notifications
3. **Rotate webhooks periodically** - Regenerate if exposed or every 6 months
4. **Document webhook changes** - Update this file if channels change
5. **Monitor test channel** - Verify tests are actually sending notifications

## Migration from Old Webhook

### Deprecated Webhook (DO NOT USE)
- **Webhook ID**: B09K3FHFUUF
- **Status**: ❌ DEPRECATED - Different Slack app
- **Action**: This webhook has been removed from all configurations
- **Replaced By**: Context-specific webhooks (WORKFLOW, DEVELOPMENT, TEST)

### If You See This Webhook
If you encounter references to `B09K3FHFUUF` or the old `SLACK_WEBHOOK_URL` environment variable:
1. Update code to use `get_hierarchical_env("SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW")`
2. Remove any shell environment variables without context suffix
3. Use the appropriate context-specific webhook instead

### Migration Completed
✅ All legacy code has been updated to use hierarchical naming convention as of October 23, 2025.

**Files Updated**:
- `synthesis/multi_model_synthesis.py` - Now uses `get_hierarchical_env()`
- `workflows/recursive_book_analysis.yaml` - Updated variable reference
- `great_expectations/uncommitted/config_variables.yml` - Updated variable reference
- `scripts/schedule_workflow.sh` - Updated all references
- `scripts/launch_automated_workflow.sh` - Updated all references
- `scripts/setup.py` - Updated prompts and env writing

## Related Documentation

- `SECRETS_STRUCTURE.md` - Complete secrets management documentation
- `TEST_SUITE_FINAL_STATUS.md` - Current test suite status
- `SKIPPED_TESTS_EXPLANATION.md` - Why tests skip and how to enable them
- `.env.example` - Environment variable templates

