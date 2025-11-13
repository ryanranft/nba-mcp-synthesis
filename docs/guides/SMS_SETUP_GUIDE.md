# SMS/Text Alerts Setup Guide

## 📱 Overview

Your NBA betting system now supports SMS/text message alerts via Twilio! Get critical alerts delivered straight to your phone.

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Twilio Account

1. **Sign up for Twilio** (free trial includes $15 credit):
   - Go to: https://www.twilio.com/try-twilio
   - Sign up with your email
   - Verify your phone number

2. **Get your credentials**:
   - After signup, you'll see your **Account SID** and **Auth Token**
   - Save these - you'll need them in Step 3

### Step 2: Get a Twilio Phone Number

1. In the Twilio console, go to: **Phone Numbers** → **Manage** → **Buy a number**
2. Select your country
3. Click **Search** to find an available number
4. Click **Buy** (free with trial credit)
5. Save your new phone number (format: +1234567890)

### Step 3: Configure NBA Betting System

**⚡ This system uses hierarchical secrets management!**

Instead of editing `notification_config.json`, credentials are stored in the hierarchical secrets structure.

**Option A: Use Setup Script (Recommended)**

```bash
cd /Users/ryanranft/nba-mcp-synthesis
./scripts/setup_sms_credentials.sh --context production
```

The script will prompt for your Twilio credentials and create the necessary files.

**Option B: Manual Setup**

Create credential files in:
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

Files to create:
```bash
echo "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" > TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_WORKFLOW.env
echo "your_auth_token_here" > TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_WORKFLOW.env
echo "+11234567890" > TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_WORKFLOW.env
echo "+11234567890" > TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Set secure permissions
chmod 600 TWILIO_*_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

**Fill in:**
- Account SID: From Twilio dashboard
- Auth Token: From Twilio dashboard (sensitive!)
- From Number: Your Twilio phone number in E.164 format
- To Numbers: Recipient phone number(s) - comma-separated if multiple

### Step 4: Test It!

**Option A: Use Test Script (Recommended)**

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Test credential loading
python scripts/test_sms_integration.py --context production

# Send actual test SMS
python scripts/test_sms_integration.py --context production --send-sms
```

**Option B: Manual Test**

```python
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.betting.notifications import NotificationManager

# Load secrets from hierarchical structure
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

# Initialize notification manager
notifier = NotificationManager(config={
    'sms': {'enabled': True}
})

# Send test SMS
result = notifier.send_message(
    subject='Test',
    message='Your NBA betting alerts are working!',
    channels=['sms']
)

print('✅ SMS sent!' if result['sms'].success else f'❌ Failed: {result["sms"].error}')
```

✅ **You should receive a text message within seconds!**

---

## 💰 Pricing

### Twilio Free Trial
- **$15 credit** (enough for ~500 SMS)
- **Test mode:** Can only send to verified numbers
- **Upgrade anytime** for full access

### After Trial
- **SMS cost:** ~$0.0075/message (US)
- **Phone number:** $1-2/month
- **Example:** 100 alerts/month = ~$1.75/month total

**💡 Tip:** Use SMS only for critical alerts to minimize costs. Use email/Slack for regular updates.

---

## 🎯 Alert Configuration

### Option 1: SMS for Critical Alerts Only

Edit `mcp_server/betting/alert_system.py` to specify channels per alert level:

```python
# In your alert checking code
if alert.level == AlertLevel.CRITICAL:
    alert_system.send_notifications(alerts, channels=['sms', 'email'])
elif alert.level == AlertLevel.WARNING:
    alert_system.send_notifications(alerts, channels=['email'])
```

### Option 2: Use Environment Variables

Instead of editing `notification_config.json`, set environment variables:

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_FROM_NUMBER="+11234567890"
export TWILIO_TO_NUMBERS="+11234567890,+10987654321"
```

Then use:
```python
notifier = NotificationManager()  # Auto-loads from env vars
```

---

## 📬 What You'll Receive

### Single Alert Example
```
[CRITICAL] roi: ROI is -12.3% (threshold: -10.0%)
```

### Batch Alert Example
```
NBA Betting: 3 alerts
🔴 2 CRITICAL
🟡 1 warnings
```

### Daily Report (Optional)
```bash
python scripts/generate_daily_report.py --sms
```

Sends:
```
NBA Betting System: Your daily betting report is ready. 
ROI: +15.2%, Win Rate: 58.5%
```

---

## ⚙️ Advanced Configuration

### Multiple Recipients

Add multiple phone numbers to receive alerts:

```json
"sms": {
  "enabled": true,
  ...
  "to_numbers": [
    "+11234567890",  # Your phone
    "+10987654321"   # Partner's phone
  ]
}
```

### Rate Limiting

SMS alerts are automatically rate-limited:
- **Minimum 5 minutes** between similar alerts
- Prevents SMS spam
- Batches multiple alerts when possible

To adjust, edit `mcp_server/betting/notifications.py:428`:

```python
self._min_interval = timedelta(minutes=10)  # Change from 5 to 10
```

### Custom Alert Messages

Customize SMS format in `mcp_server/betting/notifications.py:565`:

```python
# Short version (current)
sms_message = f"[{alert.level.value.upper()}] {alert.metric}: {alert.message}"

# Custom format
sms_message = f"🏀 NBA Alert: {alert.message[:100]}"
```

---

## 🔒 Security Best Practices

1. **Never commit credentials** to git
   - Use `notification_config.json` (already in `.gitignore`)
   - Or use environment variables

2. **Rotate auth tokens** periodically
   - In Twilio dashboard: **Settings** → **API Credentials** → **Create new token**

3. **Use subaccounts** for production
   - Twilio supports subaccounts with separate credentials
   - Isolate production from development

4. **Monitor usage**
   - Check Twilio dashboard for SMS costs
   - Set up usage alerts in Twilio

---

## 🐛 Troubleshooting

### "Module not found: twilio"
```bash
pip install twilio
```

### "Unable to create record: Unverified number"
- **Trial accounts** can only send to verified numbers
- In Twilio dashboard: **Phone Numbers** → **Verified Caller IDs**
- Add your phone number OR upgrade account

### "Invalid phone number format"
- Use **E.164 format**: +1234567890
- Include country code (+1 for US)
- No spaces, dashes, or parentheses

### SMS not received
1. Check Twilio logs: **Monitor** → **Logs** → **Messages**
2. Verify phone number is correct
3. Check if number can receive SMS (some VOIP numbers can't)
4. Try from a different phone number

### "Authentication failed"
- Double-check Account SID and Auth Token
- Ensure no extra spaces in config
- Try regenerating auth token in Twilio dashboard

---

## 📊 Integration Examples

### Automatic Critical Alerts

```python
from mcp_server.betting.alert_system import AlertSystem
from mcp_server.betting.paper_trading import PaperTradingEngine

# Load stats
engine = PaperTradingEngine(...)
stats = engine.get_performance_stats()

# Check for alerts
alert_system = AlertSystem(
    notification_config={
        'sms': {'enabled': True, ...}
    }
)

alerts = alert_system.check_performance_metrics(stats)

# Send critical alerts via SMS
critical = [a for a in alerts if a.level.value == 'critical']
if critical:
    alert_system.send_notifications(critical)  # Includes SMS
```

### Daily Summary SMS

```bash
# Add to crontab for daily SMS at 9 AM
0 9 * * * python3 -c "
from mcp_server.betting.notifications import NotificationManager
from mcp_server.betting.paper_trading import PaperTradingEngine
import json

with open('notification_config.json') as f:
    config = json.load(f)

engine = PaperTradingEngine()
stats = engine.get_performance_stats()

notifier = NotificationManager(config=config)
notifier.send_message(
    subject='NBA Betting Daily',
    message=f'ROI: {stats[\"roi\"]*100:.1f}%, Win Rate: {stats[\"win_rate\"]*100:.1f}%',
    channels=['sms']
)
"
```

---

## 📞 Support & Resources

- **Twilio Docs:** https://www.twilio.com/docs/sms
- **Python SDK:** https://www.twilio.com/docs/libraries/python
- **Pricing Calculator:** https://www.twilio.com/sms/pricing
- **Help Center:** https://support.twilio.com

---

## ✅ Verification Checklist

- [ ] Twilio account created
- [ ] Phone number purchased
- [ ] Credentials added to `notification_config.json`
- [ ] SMS enabled (`"enabled": true`)
- [ ] Phone numbers in E.164 format (+1234567890)
- [ ] Test SMS sent successfully
- [ ] Twilio SDK installed (`pip install twilio`)
- [ ] Config file in `.gitignore`

---

**🎉 You're all set! Critical betting alerts will now be sent to your phone.**

*For questions or issues, check the troubleshooting section above or open an issue on GitHub.*

---

*Last Updated: 2025-01-05*
*Twilio SDK Version: 9.8.5*
