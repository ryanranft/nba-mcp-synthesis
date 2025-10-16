# Automated Book Analysis Workflow with Notifications

## Overview

This system provides a **fully automated, hands-off workflow** that analyzes technical books and generates implementation files with real-time Slack and Linear notifications. You can set it to run overnight and wake up to 200+ executable files ready for implementation.

## 🚀 Quick Start

### 1. One-Time Setup

```bash
# Add your Slack webhook and Linear API key to .env
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> .env
echo "LINEAR_API_KEY=lin_api_YOUR_LINEAR_API_KEY" >> .env
echo "LINEAR_TEAM_ID=YOUR_TEAM_ID" >> .env
echo "LINEAR_PROJECT_ID=YOUR_PROJECT_ID" >> .env

# Make scripts executable
chmod +x scripts/launch_automated_workflow.sh
chmod +x scripts/schedule_workflow.sh

# Test notifications
python3 scripts/test_notifications.py
```

### 2. Launch Workflow

```bash
# Manual launch (with notifications)
./scripts/launch_automated_workflow.sh

# Or schedule for overnight (2 AM daily)
crontab -e
# Add: 0 2 * * * /Users/ryanranft/nba-mcp-synthesis/scripts/schedule_workflow.sh
```

## 📱 What You'll Receive

### Slack Notifications

1. **🚀 Workflow Start** (2:00 AM)
   - Books to analyze: 20
   - Budget: $410
   - Estimated completion: 4:00 AM

2. **📚 Per-Book Updates** (every ~15 min)
   - Book: "Statistics 601" complete
   - Recommendations: 14
   - Cost: $0.15

3. **🔗 Integration Complete** (3:30 AM)
   - Phases updated: 8
   - Files generated: 200+

4. **📋 Linear Issues Created** (3:45 AM)
   - Issues created: 280
   - Priority breakdown: 50 Critical, 150 Important, 80 Nice-to-have

5. **✅ Workflow Complete** (4:00 AM)
   - Total books: 20
   - Total recommendations: 280
   - Total cost: $3.00
   - Ready for implementation in Cursor

### Linear Issues Created

Each recommendation becomes a Linear issue with:
- **Title**: Recommendation title
- **Description**: Full reasoning and implementation details
- **Priority**: Based on consensus score
- **Labels**: Phase, source book, category
- **Assignee**: You
- **Project**: NBA Simulator AWS

## 🏗️ Architecture

### Core Components

1. **`scripts/automated_workflow.py`** - Main orchestrator
2. **`scripts/notification_manager.py`** - Unified Slack + Linear notifications
3. **`scripts/linear_client.py`** - Linear API integration
4. **`scripts/workflow_dashboard.py`** - Real-time progress tracking
5. **`scripts/launch_automated_workflow.sh`** - One-command launch
6. **`scripts/schedule_workflow.sh`** - Cron scheduler

### Workflow Stages

1. **Pre-flight Checks** - API keys, budget, directories
2. **Book Analysis** - 4-model consensus (Google+DeepSeek → Claude+GPT-4)
3. **Integration** - Organize by phase, generate implementation files
4. **Linear Issues** - Create tracking issues for each recommendation
5. **Final Report** - Complete summary with next steps

## 📊 Progress Tracking

The system provides real-time progress updates:

- **Percentage complete** based on books analyzed
- **ETA calculation** based on current pace
- **Cost tracking** with running totals
- **Error notifications** if anything fails
- **Stage-by-stage updates** via Slack

## 🔧 Configuration

### Environment Variables

```bash
# Required
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
LINEAR_API_KEY=lin_api_YOUR_LINEAR_API_KEY

# Optional
LINEAR_TEAM_ID=YOUR_TEAM_ID
LINEAR_PROJECT_ID=YOUR_PROJECT_ID
SLACK_CHANNEL=#nba-simulator-notifications

# Workflow Settings
WORKFLOW_ENABLE_NOTIFICATIONS=true
WORKFLOW_ENABLE_LINEAR_ISSUES=true
WORKFLOW_CRITICAL_STAGES=pre_flight,book_analysis
```

### Book Configuration

Edit `config/books_to_analyze_all_ai_ml.json` to specify which books to analyze:

```json
{
  "books": [
    {
      "id": "statistics_601",
      "title": "STATISTICS 601 Advanced Statistical Methods",
      "s3_path": "books/STATISTICS 601 Advanced Statistical Methods ( PDFDrive ).pdf",
      "category": "statistics",
      "priority": "high"
    }
  ],
  "metadata": {
    "total_books": 20,
    "created_date": "2025-10-13"
  }
}
```

## 🎯 Expected Results

After the workflow completes, you'll have:

### Generated Files
- **200+ Python implementation scripts** in `/Users/ryanranft/nba-simulator-aws/docs/phases/`
- **200+ Test suites** for each implementation
- **SQL migrations** for database changes
- **CloudFormation templates** for AWS infrastructure
- **Implementation guides** with step-by-step instructions

### Linear Issues
- **280+ Linear issues** created for tracking
- **Priority-based organization** (Critical, Important, Nice-to-have)
- **Phase-based labels** for easy filtering
- **Source book tracking** for reference

### Cost Tracking
- **Detailed cost breakdown** by model
- **Budget monitoring** with alerts
- **Token usage tracking** for optimization

## 🚨 Error Handling

The system includes robust error handling:

- **Critical stage failures** stop the workflow
- **Non-critical failures** continue with warnings
- **Error notifications** sent to Slack immediately
- **Detailed error logs** saved for debugging
- **Automatic retry** for transient failures

## 📈 Monitoring

### Real-Time Monitoring
- **Slack notifications** for every stage
- **Progress percentage** updates
- **Cost tracking** with budget alerts
- **ETA calculations** based on current pace

### Log Files
- **Detailed logs** in `logs/automated_workflow_YYYYMMDD.log`
- **Error tracking** with stack traces
- **Performance metrics** for optimization

### Linear Dashboard
- **Issue tracking** for all recommendations
- **Priority filtering** for implementation order
- **Progress monitoring** as you implement

## 🔄 Scheduling Options

### Daily Overnight (Recommended)
```bash
# Add to crontab
0 2 * * * /Users/ryanranft/nba-mcp-synthesis/scripts/schedule_workflow.sh
```

### Weekly Analysis
```bash
# Every Sunday at 2 AM
0 2 * * 0 /Users/ryanranft/nba-mcp-synthesis/scripts/schedule_workflow.sh
```

### Manual Trigger
```bash
# Run anytime
./scripts/launch_automated_workflow.sh
```

## 🎉 Next Steps After Completion

When you wake up to the completion notification:

1. **Check Linear** for 280+ new issues
2. **Open Cursor** to `/Users/ryanranft/nba-simulator-aws/docs/phases/`
3. **Review generated files** by priority
4. **Execute implementations** starting with Critical issues
5. **Mark Linear issues** as complete as you implement

## 🛠️ Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   # Check .env file
   grep -E "(SLACK_WEBHOOK_URL|LINEAR_API_KEY)" .env
   ```

2. **Slack Notifications Not Working**
   ```bash
   # Test Slack webhook
   curl -X POST "$SLACK_WEBHOOK_URL" \
     -H 'Content-Type: application/json' \
     -d '{"text": "Test message"}'
   ```

3. **Linear Issues Not Creating**
   ```bash
   # Test Linear API
   python3 scripts/test_notifications.py
   ```

4. **Workflow Stuck**
   ```bash
   # Check logs
   tail -f logs/automated_workflow_$(date +%Y%m%d).log
   ```

### Debug Mode

Run with verbose logging:
```bash
python3 scripts/automated_workflow.py \
  --config config/books_to_analyze_all_ai_ml.json \
  --budget 410.0 \
  --slack-webhook "$SLACK_WEBHOOK_URL" \
  --linear-api-key "$LINEAR_API_KEY" \
  --debug
```

## 📚 Benefits

1. **Zero Manual Intervention** - Set it and forget it
2. **Real-Time Updates** - Know exactly what's happening via Slack
3. **Automatic Issue Tracking** - All recommendations in Linear
4. **Error Notifications** - Immediately alerted if something fails
5. **Progress Visibility** - See completion percentage in real-time
6. **Cost Tracking** - Know exactly how much was spent
7. **Ready for Implementation** - Wake up to 200+ executable files in Cursor

## 🔐 Security

- **API keys** stored securely in `.env` file
- **Slack webhooks** use HTTPS
- **Linear API** uses bearer token authentication
- **Logs** don't contain sensitive information
- **Environment variables** loaded securely

## 📞 Support

If you encounter issues:

1. **Check logs** in `logs/` directory
2. **Test notifications** with `python3 scripts/test_notifications.py`
3. **Verify environment** variables are set correctly
4. **Check Slack channel** for error notifications
5. **Review Linear** for any failed issue creation

---

**Ready to go hands-off?** Just set your Slack webhook and Linear API key, then launch the workflow. You'll wake up to a complete implementation plan ready for execution! 🚀




