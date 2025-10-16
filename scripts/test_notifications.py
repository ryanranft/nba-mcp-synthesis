#!/usr/bin/env python3
"""
Test Notifications Script

Tests Slack and Linear notifications to help you get your team and project IDs.
Run this script to verify your notification setup and get the IDs you need.
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.notification_manager import NotificationManager, LinearClient

async def test_slack_notifications(webhook_url: str):
    """Test Slack notifications."""
    print("🔔 Testing Slack notifications...")

    try:
        from mcp_server.connectors.slack_notifier import SlackNotifier
        notifier = SlackNotifier(webhook_url)

        # Test basic notification
        test_message = {
            "text": "🧪 NBA Book Analysis Workflow - Test Notification",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🧪 Test Notification*\nThis is a test message from the NBA Book Analysis Workflow system."
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Status:* ✅ Working"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Time:* " + str(asyncio.get_event_loop().time())
                        }
                    ]
                }
            ]
        }

        await notifier.send_notification(test_message)
        print("✅ Slack notification sent successfully!")
        return True

    except Exception as e:
        print(f"❌ Slack notification failed: {e}")
        return False

async def test_linear_integration(api_key: str):
    """Test Linear integration and get team/project IDs."""
    print("📋 Testing Linear integration...")

    try:
        client = LinearClient(api_key)

        # Get teams
        print("🔍 Getting Linear teams...")
        teams = await client.get_teams()

        if not teams:
            print("❌ No teams found. Check your Linear API key.")
            return False

        print(f"✅ Found {len(teams)} team(s):")
        for team in teams:
            print(f"  📁 Team: {team['name']} (ID: {team['id']})")

        # Get projects for each team
        print("\n🔍 Getting projects for each team...")
        for team in teams:
            print(f"\n📁 Projects for team '{team['name']}':")
            projects = await client.get_projects(team['id'])

            if projects:
                for project in projects:
                    print(f"  📋 Project: {project['name']} (ID: {project['id']})")
                    print(f"      Description: {project.get('description', 'No description')}")
                    print(f"      State: {project.get('state', 'Unknown')}")
            else:
                print("  📋 No projects found")

        # Test issue creation (optional)
        print("\n🧪 Testing issue creation...")
        if teams:
            test_team_id = teams[0]['id']
            test_project_id = None

            # Try to find a project
            projects = await client.get_projects(test_team_id)
            if projects:
                test_project_id = projects[0]['id']

            test_issue_id = await client.create_issue(
                title="🧪 NBA Book Analysis Workflow - Test Issue",
                description="This is a test issue created by the NBA Book Analysis Workflow system. You can safely delete this issue.",
                team_id=test_team_id,
                project_id=test_project_id,
                priority=4,  # Low priority
                labels=["test", "workflow"]
            )

            if test_issue_id:
                print(f"✅ Test issue created successfully! (ID: {test_issue_id})")
                print("   You can delete this test issue from Linear.")
            else:
                print("❌ Test issue creation failed")

        return True

    except Exception as e:
        print(f"❌ Linear integration failed: {e}")
        return False

async def test_notification_manager(slack_webhook: str, linear_api_key: str):
    """Test the complete notification manager."""
    print("🔧 Testing complete notification manager...")

    try:
        manager = NotificationManager(slack_webhook, linear_api_key)

        # Test stage notifications
        await manager.notify_stage_start("test_stage", {
            "description": "Testing notification manager",
            "books_count": 3,
            "budget": 10.0
        })

        await manager.notify_stage_complete("test_stage", {
            "description": "Test stage completed successfully",
            "recommendations": 5,
            "cost": 0.15
        })

        print("✅ Notification manager test completed!")
        return True

    except Exception as e:
        print(f"❌ Notification manager test failed: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions for getting credentials."""
    print("\n" + "="*80)
    print("📋 SETUP INSTRUCTIONS")
    print("="*80)

    print("\n🔔 SLACK SETUP:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create a new app or select existing")
    print("3. Go to 'Incoming Webhooks'")
    print("4. Click 'Add New Webhook to Workspace'")
    print("5. Select your channel (e.g., #nba-simulator-notifications)")
    print("6. Copy the webhook URL")
    print("7. Add to .env.workflow: SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")

    print("\n📋 LINEAR SETUP:")
    print("1. Go to https://linear.app/settings/api")
    print("2. Click 'Create new Personal API Key'")
    print("3. Give it a name (e.g., 'NBA Book Analysis Workflow')")
    print("4. Copy the key (starts with lin_api_)")
    print("5. Add to .env.workflow: LINEAR_API_KEY=lin_api_...")
    print("6. Run this script to get your team and project IDs")
    print("7. Add to .env.workflow: LINEAR_TEAM_ID=... and LINEAR_PROJECT_ID=...")

    print("\n🚀 QUICK START:")
    print("1. Add SLACK_WEBHOOK_URL to .env.workflow")
    print("2. Add LINEAR_API_KEY to .env.workflow")
    print("3. Run: python3 scripts/test_notifications.py --slack-webhook YOUR_WEBHOOK --linear-api-key YOUR_KEY")
    print("4. Copy the team and project IDs from the output")
    print("5. Add LINEAR_TEAM_ID and LINEAR_PROJECT_ID to .env.workflow")
    print("6. Run: ./scripts/launch_automated_workflow.sh")

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test Slack and Linear notifications')
    parser.add_argument('--slack-webhook', help='Slack webhook URL')
    parser.add_argument('--linear-api-key', help='Linear API key')
    parser.add_argument('--test-slack-only', action='store_true', help='Test only Slack')
    parser.add_argument('--test-linear-only', action='store_true', help='Test only Linear')
    parser.add_argument('--setup-instructions', action='store_true', help='Show setup instructions')

    args = parser.parse_args()

    if args.setup_instructions:
        print_setup_instructions()
        return

    if not args.slack_webhook and not args.linear_api_key:
        print("❌ Please provide --slack-webhook and/or --linear-api-key")
        print("   Or use --setup-instructions to see how to get them")
        return

    print("🧪 NBA Book Analysis Workflow - Notification Test")
    print("="*60)

    success_count = 0
    total_tests = 0

    # Test Slack
    if args.slack_webhook and not args.test_linear_only:
        total_tests += 1
        if await test_slack_notifications(args.slack_webhook):
            success_count += 1
        print()

    # Test Linear
    if args.linear_api_key and not args.test_slack_only:
        total_tests += 1
        if await test_linear_integration(args.linear_api_key):
            success_count += 1
        print()

    # Test combined
    if args.slack_webhook and args.linear_api_key:
        total_tests += 1
        if await test_notification_manager(args.slack_webhook, args.linear_api_key):
            success_count += 1
        print()

    # Summary
    print("="*60)
    print(f"🧪 Test Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("✅ All tests passed! Your notification setup is working.")
        print("\n📋 Next steps:")
        print("1. Copy the team and project IDs from the output above")
        print("2. Add them to your .env.workflow file")
        print("3. Run: ./scripts/launch_automated_workflow.sh")
    else:
        print("❌ Some tests failed. Check the error messages above.")
        print("   Use --setup-instructions to see how to get credentials")

if __name__ == '__main__':
    asyncio.run(main())