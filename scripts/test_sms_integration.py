#!/usr/bin/env python3
"""
Test SMS Integration with Hierarchical Secrets

This script tests that:
1. Twilio credentials load correctly from hierarchical secrets system
2. Environment variables are set properly (both full names and aliases)
3. NotificationManager can initialize with SMS enabled
4. SMS messages can be sent successfully

Usage:
------
    # Test development environment
    python scripts/test_sms_integration.py --context development

    # Test production environment
    python scripts/test_sms_integration.py --context production

    # Test and send actual SMS
    python scripts/test_sms_integration.py --context development --send-sms

    # Show verbose output
    python scripts/test_sms_integration.py --context development --verbose
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_secrets_manager,
    get_health_status,
)
from mcp_server.betting.notifications import NotificationManager


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_full_names(context: str, verbose: bool = False) -> bool:
    """Check that full hierarchical names are loaded"""
    print_section("Checking Full Hierarchical Names")

    # Map context to naming convention
    context_map = {
        "production": "WORKFLOW",
        "workflow": "WORKFLOW",
        "development": "DEVELOPMENT",
        "test": "TEST",
    }
    context_suffix = context_map.get(context.lower(), context.upper())

    full_names = [
        f"TWILIO_ACCOUNT_SID_NBA_MCP_SYNTHESIS_{context_suffix}",
        f"TWILIO_AUTH_TOKEN_NBA_MCP_SYNTHESIS_{context_suffix}",
        f"TWILIO_FROM_NUMBER_NBA_MCP_SYNTHESIS_{context_suffix}",
        f"TWILIO_TO_NUMBERS_NBA_MCP_SYNTHESIS_{context_suffix}",
    ]

    all_present = True
    for name in full_names:
        value = os.getenv(name)
        status = "✅" if value else "❌"
        print(f"  {status} {name}")

        if verbose and value:
            # Show partial value for verification
            if "TOKEN" in name or "PASSWORD" in name:
                print(f"      Value: {value[:8]}...***")
            elif "NUMBER" in name:
                print(f"      Value: {value[:5]}...{value[-4:]}")
            else:
                print(f"      Value: {value[:12]}...")

        if not value:
            all_present = False

    if all_present:
        print(f"\n✅ All full hierarchical names present")
    else:
        print(f"\n❌ Some full hierarchical names missing")

    return all_present


def check_aliases(verbose: bool = False) -> bool:
    """Check that short name aliases are created"""
    print_section("Checking Short Name Aliases")

    short_names = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER",
        "TWILIO_TO_NUMBERS",
    ]

    all_present = True
    for name in short_names:
        value = os.getenv(name)
        status = "✅" if value else "❌"
        print(f"  {status} {name}")

        if verbose and value:
            # Show that alias points to correct value
            if "TOKEN" in name:
                print(f"      Value: {value[:8]}...***")
            elif "NUMBER" in name:
                print(f"      Value: {value}")
            else:
                print(f"      Value: {value[:12]}...")

        if not value:
            all_present = False

    if all_present:
        print(f"\n✅ All aliases present")
    else:
        print(f"\n❌ Some aliases missing")

    return all_present


def check_notifier_init() -> bool:
    """Check that NotificationManager can initialize with SMS"""
    print_section("Testing NotificationManager Initialization")

    try:
        # Try to initialize with SMS enabled
        notifier = NotificationManager(config={"sms": {"enabled": True}})

        # Check if SMS notifier was created
        if "sms" in notifier.notifiers:
            print(f"  ✅ NotificationManager initialized successfully")
            print(f"  ✅ SMS notifier created")

            # Show notifier details
            sms_notifier = notifier.notifiers["sms"]
            print(f"\n  SMS Notifier Details:")
            print(f"    Account SID: {sms_notifier.account_sid[:12]}...")
            print(f"    From Number: {sms_notifier.from_number}")
            print(f"    To Numbers: {', '.join(sms_notifier.to_numbers)}")

            return True
        else:
            print(f"  ❌ SMS notifier not created")
            return False

    except Exception as e:
        print(f"  ❌ Failed to initialize: {e}")
        return False


def send_test_sms(context: str) -> bool:
    """Send a test SMS message"""
    print_section("Sending Test SMS")

    try:
        notifier = NotificationManager(config={"sms": {"enabled": True}})

        if "sms" not in notifier.notifiers:
            print(f"  ❌ SMS notifier not available")
            return False

        # Send test message
        message = f"Test SMS from NBA MCP Synthesis ({context} environment)"
        print(f"  📱 Sending test message...")
        print(f'     Message: "{message}"')

        result = notifier.notifiers["sms"].send(message)

        if result.success:
            print(f"\n  ✅ SMS sent successfully!")
            if result.metadata:
                sent_to = result.metadata.get("sent_to", [])
                print(f"     Sent to: {', '.join(sent_to)}")
            return True
        else:
            print(f"\n  ❌ SMS send failed: {result.error}")
            return False

    except Exception as e:
        print(f"  ❌ Exception during SMS send: {e}")
        return False


def show_secrets_manager_health():
    """Show secrets manager health status"""
    print_section("Secrets Manager Health")

    health = get_health_status()

    print(f"  Secrets Loaded: {health['secrets_loaded']}")
    print(f"  Aliases Created: {health['aliases_created']}")
    print(f"  Provenance Tracked: {health['provenance_tracked']}")
    print(f"  Naming Compliance: {'✅' if health['naming_compliance'] else '❌'}")

    # Show some example TWILIO secrets (without values)
    manager = get_secrets_manager()
    secrets = manager.get_all_secrets()

    twilio_secrets = [k for k in secrets.keys() if "TWILIO" in k]

    if twilio_secrets:
        print(f"\n  TWILIO Secrets Found ({len(twilio_secrets)}):")
        for secret in sorted(twilio_secrets):
            print(f"    - {secret}")
    else:
        print(f"\n  ❌ No TWILIO secrets found")


def main():
    parser = argparse.ArgumentParser(
        description="Test SMS integration with hierarchical secrets"
    )
    parser.add_argument(
        "--context",
        default="development",
        choices=["production", "development", "test", "workflow"],
        help="Context to test (default: development)",
    )
    parser.add_argument(
        "--send-sms", action="store_true", help="Actually send a test SMS"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output including partial credential values",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  SMS Integration Test")
    print("  NBA MCP Synthesis - Hierarchical Secrets")
    print("=" * 60)
    print(f"\nContext: {args.context}")
    print(f"Project: nba-mcp-synthesis")
    print(f"Sport: NBA")

    # Load secrets
    print_section("Loading Secrets")
    print(f"  Loading secrets for {args.context} context...")

    success = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", args.context)

    if not success:
        print(f"  ❌ Failed to load secrets")
        sys.exit(1)

    print(f"  ✅ Secrets loaded successfully")

    # Show health status
    show_secrets_manager_health()

    # Run tests
    results = {}

    results["full_names"] = check_full_names(args.context, args.verbose)
    results["aliases"] = check_aliases(args.verbose)
    results["notifier_init"] = check_notifier_init()

    if args.send_sms:
        results["sms_send"] = send_test_sms(args.context)

    # Summary
    print_section("Test Summary")

    all_passed = True
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        test_label = test_name.replace("_", " ").title()
        print(f"  {status} {test_label}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 All tests passed!")

        if not args.send_sms:
            print("\n💡 Tip: Run with --send-sms to test actual SMS delivery")

        return 0
    else:
        print("❌ Some tests failed")

        print("\n🔧 Troubleshooting:")
        if not results.get("full_names"):
            print("  - Check that credential files exist in hierarchical structure")
            print(
                f"  - Expected directory: .../nba-mcp-synthesis/.env.nba_mcp_synthesis.{args.context}/"
            )

        if not results.get("aliases"):
            print("  - Verify unified_secrets_manager.py has TWILIO aliases")
            print("  - Check that load_secrets_hierarchical() completed successfully")

        if not results.get("notifier_init"):
            print("  - Ensure twilio package is installed: pip install twilio")
            print("  - Verify credentials are valid")

        if args.send_sms and not results.get("sms_send"):
            print("  - Check Twilio account status and balance")
            print("  - Verify phone numbers are in E.164 format (+12345678901)")
            print("  - For trial accounts, verify recipient is verified in Twilio")

        return 1


if __name__ == "__main__":
    sys.exit(main())
