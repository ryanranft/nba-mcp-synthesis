#!/usr/bin/env python3
"""
Test Alert System with SMS

Tests the complete alert system workflow with SMS notifications.
Creates mock performance data that triggers alerts and sends them via SMS.

Usage:
------
    # Test with development credentials
    python scripts/test_alert_sms.py --context development

    # Test with production credentials
    python scripts/test_alert_sms.py --context production

    # Test critical alerts only
    python scripts/test_alert_sms.py --critical-only
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.betting.alert_system import (
    AlertSystem,
    Alert,
    AlertLevel,
    AlertCategory,
)
from mcp_server.betting.notifications import NotificationManager
from datetime import datetime


def create_test_alerts():
    """Create test alerts for SMS notification"""
    alerts = []

    # Critical alert - Low ROI
    alerts.append(
        Alert(
            alert_id="test_critical_roi",
            timestamp=datetime.now(),
            level=AlertLevel.CRITICAL,
            category=AlertCategory.PERFORMANCE,
            metric="roi",
            value=-0.12,
            threshold=-0.10,
            message="ROI is -12.0% (threshold: -10.0%)",
        )
    )

    # Warning alert - Low win rate
    alerts.append(
        Alert(
            alert_id="test_warning_winrate",
            timestamp=datetime.now(),
            level=AlertLevel.WARNING,
            category=AlertCategory.PERFORMANCE,
            metric="win_rate",
            value=0.48,
            threshold=0.50,
            message="Win rate is 48.0% (threshold: 50.0%)",
        )
    )

    # Critical alert - High Brier score (calibration)
    alerts.append(
        Alert(
            alert_id="test_critical_brier",
            timestamp=datetime.now(),
            level=AlertLevel.CRITICAL,
            category=AlertCategory.CALIBRATION,
            metric="brier_score",
            value=0.25,
            threshold=0.20,
            message="Brier score is 0.2500 (threshold: 0.2000)",
        )
    )

    return alerts


def main():
    parser = argparse.ArgumentParser(description="Test alert system with SMS")
    parser.add_argument(
        "--context",
        default="production",
        choices=["production", "development", "test"],
        help="Context to use for credentials (default: production)",
    )
    parser.add_argument(
        "--critical-only", action="store_true", help="Only send critical alerts via SMS"
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  Alert System SMS Test")
    print("=" * 70)
    print(f"\nContext: {args.context}")

    # Load secrets
    print("\n1️⃣  Loading secrets...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", args.context)
    print("   ✓ Secrets loaded")

    # Initialize alert system with SMS
    print("\n2️⃣  Initializing alert system with SMS...")
    alert_system = AlertSystem(
        db_path="data/test_alerts.db", notification_config={"sms": {"enabled": True}}
    )
    print("   ✓ Alert system initialized")

    # Create test alerts
    print("\n3️⃣  Creating test alerts...")
    all_alerts = create_test_alerts()

    for alert in all_alerts:
        print(f"   {alert}")

    # Filter alerts for SMS if critical-only
    if args.critical_only:
        sms_alerts = [a for a in all_alerts if a.level == AlertLevel.CRITICAL]
        print(
            f"\n   Filtering: {len(sms_alerts)} critical alerts (from {len(all_alerts)} total)"
        )
    else:
        sms_alerts = all_alerts
        print(f"\n   Sending all {len(sms_alerts)} alerts")

    # Send via SMS
    if sms_alerts:
        print("\n4️⃣  Sending SMS notifications...")
        try:
            results = alert_system.send_notifications(sms_alerts)

            if results:
                print(f"   ✓ Notifications sent:")
                print(f"      Success: {results.get('sent', 0)}")
                print(f"      Failed: {results.get('failed', 0)}")

                # Show detailed results
                if "results" in results:
                    for channel, result in results["results"].items():
                        status = "✓" if result.success else "✗"
                        print(f"      {status} {channel.upper()}")
            else:
                print("   ⚠️  No notification results returned")

        except Exception as e:
            print(f"   ✗ Failed to send notifications: {e}")
            import traceback

            traceback.print_exc()
            return 1
    else:
        print("\n   ℹ️  No alerts to send")

    # Success
    print("\n" + "=" * 70)
    print("  ✅ Test Complete!")
    print("=" * 70)
    print(f"\nCheck your phone for SMS alert(s).")
    print(f"Expected {len(sms_alerts)} message(s).\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
