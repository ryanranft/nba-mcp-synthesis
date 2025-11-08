#!/usr/bin/env python3
"""
Test Email Integration

Tests email delivery through Gmail SMTP using credentials from hierarchical secrets.

Usage:
    python scripts/test_email_integration.py
    python scripts/test_email_integration.py --to custom@email.com
    python scripts/test_email_integration.py --html

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import sys
import os
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.betting.notifications import NotificationManager
from datetime import datetime


def test_email_basic(to_addr: str = None):
    """
    Test basic email delivery

    Args:
        to_addr: Optional override for recipient address
    """
    print("=" * 60)
    print("NBA MCP Synthesis - Email Integration Test")
    print("=" * 60)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    success = load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

    if not success:
        print("❌ Failed to load secrets. Check unified_secrets_manager configuration.")
        return False

    # Check SMTP credentials
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')

    print(f"✅ Secrets loaded successfully")
    print(f"   SMTP Host: {smtp_host}")
    print(f"   SMTP User: {smtp_user}")
    print(f"   From: {email_from}")
    print(f"   To: {to_addr or email_to}")
    print()

    # Initialize notification manager
    print("🔧 Initializing notification manager...")
    try:
        notifier = NotificationManager(config={
            'email': {
                'enabled': True
            }
        })
        print("✅ Notification manager initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize notification manager: {e}")
        return False

    # Prepare test message
    subject = f"🏀 NBA MCP Synthesis - Email Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    message = f"""
NBA MCP Synthesis Email Integration Test
==========================================

This is a test email from the NBA MCP Synthesis betting automation system.

Test Details:
  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  • SMTP Server: {smtp_host}
  • From Address: {email_from}
  • To Address: {to_addr or email_to}

System Status:
  ✅ Hierarchical secrets loaded
  ✅ SMTP credentials configured
  ✅ Email notifier initialized
  ✅ Email delivery working

Next Steps:
  1. Verify this email arrived in your inbox
  2. Check spam folder if not in inbox
  3. Add sender to contacts to avoid spam
  4. Test HTML email formatting (use --html flag)

If you received this email, the automation system is ready for:
  • Daily betting recommendations
  • Arbitrage opportunity alerts
  • Performance reports
  • Critical threshold notifications

---
Automated by NBA MCP Synthesis
Powered by Claude Code
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Send email
    print("📧 Sending test email...")
    try:
        results = notifier.send_message(
            subject=subject,
            message=message,
            channels=['email']
        )

        if results and 'email' in results and results['email'].success:
            print("✅ Email sent successfully!")
            print()
            print("📬 Check your inbox:")
            print(f"   {to_addr or email_to}")
            print()
            print("   If you don't see the email:")
            print("   1. Check spam/junk folder")
            print("   2. Wait 1-2 minutes for delivery")
            print("   3. Verify Gmail app password is correct")
            print()
            return True
        else:
            error = results.get('email').error if 'email' in results else 'Unknown error'
            print(f"❌ Email delivery failed: {error}")
            return False

    except Exception as e:
        print(f"❌ Exception during email send: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_html():
    """Test HTML email with rich formatting"""
    print("=" * 60)
    print("NBA MCP Synthesis - HTML Email Test")
    print("=" * 60)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    success = load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

    if not success:
        print("❌ Failed to load secrets")
        return False

    print("✅ Secrets loaded")
    print()

    # Initialize notifier
    notifier = NotificationManager(config={'email': {'enabled': True}})

    # Create HTML email
    subject = f"🏀 NBA Betting Alert - Top 3 Picks - {datetime.now().strftime('%Y-%m-%d')}"

    html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        h1 {{ color: #1a73e8; }}
        h2 {{ color: #34a853; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background-color: #1a73e8; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .edge-high {{ color: #34a853; font-weight: bold; }}
        .edge-medium {{ color: #fbbc04; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>🏀 NBA Betting Recommendations</h1>
    <p><strong>Date:</strong> {datetime.now().strftime('%A, %B %d, %Y')}</p>

    <h2>Top 3 Picks for Today</h2>

    <table>
        <tr>
            <th>Game</th>
            <th>Bet</th>
            <th>Odds</th>
            <th>Stake</th>
            <th>Edge</th>
            <th>Kelly %</th>
        </tr>
        <tr>
            <td>Lakers vs Warriors<br><small>7:00 PM ET</small></td>
            <td>Lakers ML</td>
            <td>+150</td>
            <td>$183</td>
            <td><span class="edge-high">+10.7%</span></td>
            <td>3.2%</td>
        </tr>
        <tr>
            <td>Celtics vs Heat<br><small>7:30 PM ET</small></td>
            <td>Heat +5.5</td>
            <td>-110</td>
            <td>$145</td>
            <td><span class="edge-medium">+6.2%</span></td>
            <td>2.1%</td>
        </tr>
        <tr>
            <td>Nuggets vs Suns<br><small>9:00 PM ET</small></td>
            <td>Over 225.5</td>
            <td>-105</td>
            <td>$128</td>
            <td><span class="edge-medium">+5.1%</span></td>
            <td>1.8%</td>
        </tr>
    </table>

    <h2>System Summary</h2>
    <ul>
        <li><strong>Bankroll:</strong> $5,000</li>
        <li><strong>Total Stake Today:</strong> $456 (9.1% of bankroll)</li>
        <li><strong>Expected Value:</strong> +$37.42</li>
        <li><strong>Brier Score:</strong> 0.082 (excellent calibration)</li>
    </ul>

    <p><strong>Note:</strong> This is a TEST email with DEMO data. No real betting recommendations.</p>

    <div class="footer">
        <p>
            🤖 Automated by NBA MCP Synthesis<br>
            Powered by Claude Code | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
"""

    print("📧 Sending HTML test email...")
    try:
        # Get email notifier directly
        email_notifier = notifier.notifiers['email']
        result = email_notifier.send(subject, html_body, html=True)

        if result.success:
            print("✅ HTML email sent successfully!")
            print()
            print("📬 Check your inbox for a formatted betting report")
            return True
        else:
            print(f"❌ HTML email failed: {result.error}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(
        description='Test NBA MCP Synthesis email integration'
    )
    parser.add_argument(
        '--to',
        help='Override recipient email address',
        default=None
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Test HTML email formatting'
    )

    args = parser.parse_args()

    if args.html:
        success = test_email_html()
    else:
        success = test_email_basic(args.to)

    if success:
        print("=" * 60)
        print("✅ EMAIL TEST PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ EMAIL TEST FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
