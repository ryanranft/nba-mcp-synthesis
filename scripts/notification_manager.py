#!/usr/bin/env python3
"""
Unified Notification Manager

Handles both Slack and Linear notifications for the automated workflow.
Provides a single interface for all notification needs.
"""

import os
import json
import logging
import asyncio
import ssl
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp

# Add project root to path
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.connectors.slack_notifier import SlackNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinearClient:
    """Linear API client for creating issues and managing projects."""

    def __init__(self, api_key: str):
        """
        Initialize Linear client.

        Args:
            api_key: Linear API key (starts with lin_api_)
        """
        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": api_key,  # Linear doesn't use Bearer prefix
            "Content-Type": "application/json",
        }

        logger.info("✅ Linear client initialized")

    def _get_ssl_context(self):
        """Get SSL context for macOS compatibility."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams accessible to the API key."""
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._get_ssl_context())
        ) as session:
            async with session.post(
                self.base_url, headers=self.headers, json={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    teams = data.get("data", {}).get("teams", {}).get("nodes", [])
                    logger.info(f"Found {len(teams)} teams")
                    return teams
                else:
                    logger.error(f"Failed to get teams: {response.status}")
                    return []

    async def get_projects(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a team."""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                projects {
                    nodes {
                        id
                        name
                        description
                        state
                    }
                }
            }
        }
        """

        variables = {"teamId": team_id}

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._get_ssl_context())
        ) as session:
            async with session.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    projects = (
                        data.get("data", {})
                        .get("team", {})
                        .get("projects", {})
                        .get("nodes", [])
                    )
                    logger.info(f"Found {len(projects)} projects for team {team_id}")
                    return projects
                else:
                    logger.error(f"Failed to get projects: {response.status}")
                    return []

    async def create_issue(
        self,
        title: str,
        description: str,
        team_id: str,
        project_id: Optional[str] = None,
        priority: int = 3,
        labels: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Create a Linear issue.

        Args:
            title: Issue title
            description: Issue description
            team_id: Team ID
            project_id: Project ID (optional)
            priority: Priority (1=Urgent, 2=High, 3=Normal, 4=Low)
            labels: List of label names

        Returns:
            Issue ID if successful, None otherwise
        """
        # Build labels input
        labels_input = []
        if labels:
            for label_name in labels:
                labels_input.append({"name": label_name})

        # Build mutation
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                }
            }
        }
        """

        variables = {
            "input": {
                "title": title,
                "description": description,
                "teamId": team_id,
                "priority": priority,
                "labels": labels_input,
            }
        }

        # Add project if specified
        if project_id:
            variables["input"]["projectId"] = project_id

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._get_ssl_context())
        ) as session:
            async with session.post(
                self.base_url,
                headers=self.headers,
                json={"query": mutation, "variables": variables},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data", {}).get("issueCreate", {}).get("success"):
                        issue = data["data"]["issueCreate"]["issue"]
                        issue_id = issue["id"]
                        identifier = issue["identifier"]
                        logger.info(f"Created Linear issue: {identifier} - {title}")
                        return issue_id
                    else:
                        logger.error(f"Failed to create issue: {data}")
                        return None
                else:
                    logger.error(f"Failed to create issue: {response.status}")
                    return None

    async def create_issues_batch(
        self,
        recommendations: List[Dict[str, Any]],
        team_id: str,
        project_id: Optional[str] = None,
    ) -> List[str]:
        """
        Create multiple Linear issues in batch.

        Args:
            recommendations: List of recommendation dictionaries
            team_id: Team ID
            project_id: Project ID (optional)

        Returns:
            List of created issue IDs
        """
        logger.info(f"Creating {len(recommendations)} Linear issues...")

        issue_ids = []
        for i, rec in enumerate(recommendations):
            try:
                # Determine priority based on category
                priority_map = {
                    "CRITICAL": 1,  # Urgent
                    "IMPORTANT": 2,  # High
                    "NICE_TO_HAVE": 4,  # Low
                }
                priority = priority_map.get(rec.get("category", "IMPORTANT"), 3)

                # Build labels
                labels = [
                    f"Phase-{rec.get('phase', 'Unknown')}",
                    f"Source-{rec.get('source_book', 'Unknown')}",
                    rec.get("category", "IMPORTANT"),
                ]

                # Create issue
                issue_id = await self.create_issue(
                    title=rec["title"],
                    description=self._build_issue_description(rec),
                    team_id=team_id,
                    project_id=project_id,
                    priority=priority,
                    labels=labels,
                )

                if issue_id:
                    issue_ids.append(issue_id)

                # Rate limiting - Linear allows 10 requests per second
                if i % 5 == 0 and i > 0:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(
                    f"Failed to create issue for {rec.get('title', 'Unknown')}: {e}"
                )
                continue

        logger.info(f"Created {len(issue_ids)} Linear issues")
        return issue_ids

    def _build_issue_description(self, rec: Dict[str, Any]) -> str:
        """Build detailed issue description from recommendation."""
        description = f"""## Recommendation Details

**Title:** {rec['title']}
**Priority:** {rec.get('category', 'IMPORTANT')}
**Phase:** {rec.get('phase', 'Unknown')}
**Source Book:** {rec.get('source_book', 'Unknown')}

## Description

{rec.get('reasoning', 'No description available')}

## Implementation Details

**Expected Impact:** {rec.get('impact', 'MEDIUM')}
**Time Estimate:** {rec.get('time_estimate', '1 week')}
**Consensus Score:** {rec.get('consensus_score', 'N/A')}

## Generated Files

The following implementation files have been generated:
- `implement_{rec['id']}.py` - Main implementation script
- `test_{rec['id']}.py` - Test suite
- `{rec['id']}_IMPLEMENTATION_GUIDE.md` - Detailed implementation guide

## Next Steps

1. Review the implementation guide
2. Execute the implementation script
3. Run tests to verify functionality
4. Update this issue with progress

---
*Generated by NBA Book Analysis Workflow on {datetime.now().isoformat()}*
"""
        return description


class NotificationManager:
    """Unified notification system for Slack and Linear."""

    def __init__(self, slack_webhook: str, linear_api_key: str):
        """
        Initialize notification manager.

        Args:
            slack_webhook: Slack webhook URL
            linear_api_key: Linear API key
        """
        self.slack = SlackNotifier(slack_webhook)
        self.linear = LinearClient(linear_api_key)

        logger.info("✅ Notification manager initialized")

    async def notify_stage_start(self, stage: str, details: Dict[str, Any]):
        """Notify when a workflow stage starts."""
        message = {
            "text": f"🔄 Starting {stage.replace('_', ' ').title()}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔄 {stage.replace('_', ' ').title()} Started*\n{details.get('description', '')}",
                    },
                }
            ],
        }

        if details.get("books_count"):
            message["blocks"].append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Books:* {details['books_count']}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Budget:* ${details.get('budget', 0):.2f}",
                        },
                    ],
                }
            )

        await self.slack.send_notification(message)

    async def notify_stage_complete(self, stage: str, results: Dict[str, Any]):
        """Notify when a workflow stage completes."""
        message = {
            "text": f"✅ {stage.replace('_', ' ').title()} Complete",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*✅ {stage.replace('_', ' ').title()} Complete*\n{results.get('description', '')}",
                    },
                }
            ],
        }

        # Add relevant fields based on stage
        fields = []
        if results.get("recommendations"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Recommendations:* {results['recommendations']}",
                }
            )
        if results.get("cost"):
            fields.append({"type": "mrkdwn", "text": f"*Cost:* ${results['cost']:.4f}"})
        if results.get("files_generated"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Files Generated:* {results['files_generated']}",
                }
            )
        if results.get("issues_created"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Linear Issues:* {results['issues_created']}",
                }
            )

        if fields:
            message["blocks"].append({"type": "section", "fields": fields})

        await self.slack.send_notification(message)

    async def notify_error(self, stage: str, error: str):
        """Notify when an error occurs."""
        message = {
            "text": f"❌ Error in {stage.replace('_', ' ').title()}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*❌ Error in {stage.replace('_', ' ').title()}*\n```{error}```",
                    },
                }
            ],
        }

        await self.slack.send_notification(message)

    async def notify_book_analysis_complete(
        self, book_title: str, recommendations: int, cost: float, time_taken: float
    ):
        """Notify when a single book analysis completes."""
        message = {
            "text": f"📚 Book Analysis Complete: {book_title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📚 Book Analysis Complete*\n*Book:* {book_title}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Recommendations:* {recommendations}",
                        },
                        {"type": "mrkdwn", "text": f"*Cost:* ${cost:.4f}"},
                        {"type": "mrkdwn", "text": f"*Time:* {time_taken:.1f}s"},
                    ],
                },
            ],
        }

        await self.slack.send_notification(message)

    async def notify_workflow_complete(self, summary: Dict[str, Any]):
        """Notify when the entire workflow completes."""
        message = {
            "text": "🎉 NBA Book Analysis Workflow Complete!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🎉 NBA Book Analysis Workflow Complete!*\nReady for implementation in Cursor",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Books Analyzed:* {summary.get('books_analyzed', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Recommendations:* {summary.get('recommendations_generated', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Cost:* ${summary.get('total_cost', 0):.2f}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Files Generated:* {summary.get('files_generated', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Linear Issues:* {summary.get('linear_issues_created', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {summary.get('duration', 0):.1f}s",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Next Steps:*\n1. Open `/Users/ryanranft/nba-simulator-aws/docs/phases/` in Cursor\n2. Review generated implementation files\n3. Execute highest priority recommendations\n4. Check Linear for created issues",
                    },
                },
            ],
        }

        await self.slack.send_notification(message)

    async def create_linear_issues(
        self,
        recommendations: List[Dict[str, Any]],
        team_id: str,
        project_id: Optional[str] = None,
    ) -> List[str]:
        """Create Linear issues for all recommendations."""
        logger.info(
            f"Creating Linear issues for {len(recommendations)} recommendations..."
        )

        issue_ids = await self.linear.create_issues_batch(
            recommendations=recommendations, team_id=team_id, project_id=project_id
        )

        # Notify completion
        await self.slack.send_notification(
            {
                "text": f"📋 Created {len(issue_ids)} Linear Issues",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📋 Linear Issues Created*\nCreated {len(issue_ids)} issues in Linear",
                        },
                    }
                ],
            }
        )

        return issue_ids


async def main():
    """Test the notification manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Test notification manager")
    parser.add_argument("--slack-webhook", required=True, help="Slack webhook URL")
    parser.add_argument("--linear-api-key", required=True, help="Linear API key")
    parser.add_argument(
        "--test-slack", action="store_true", help="Test Slack notifications"
    )
    parser.add_argument(
        "--test-linear", action="store_true", help="Test Linear integration"
    )
    parser.add_argument("--get-teams", action="store_true", help="Get Linear teams")
    parser.add_argument("--get-projects", help="Get projects for team ID")

    args = parser.parse_args()

    manager = NotificationManager(args.slack_webhook, args.linear_api_key)

    if args.test_slack:
        logger.info("Testing Slack notifications...")
        await manager.notify_stage_start(
            "test_stage", {"description": "Testing Slack integration"}
        )
        await manager.notify_stage_complete(
            "test_stage", {"description": "Slack test complete"}
        )
        logger.info("Slack test complete")

    if args.get_teams:
        logger.info("Getting Linear teams...")
        teams = await manager.linear.get_teams()
        for team in teams:
            print(f"Team: {team['name']} (ID: {team['id']})")

    if args.get_projects:
        logger.info(f"Getting projects for team {args.get_projects}...")
        projects = await manager.linear.get_projects(args.get_projects)
        for project in projects:
            print(f"Project: {project['name']} (ID: {project['id']})")

    if args.test_linear:
        logger.info("Testing Linear issue creation...")
        # Create a test issue
        test_rec = {
            "id": "test_rec_001",
            "title": "Test Recommendation",
            "reasoning": "This is a test recommendation for the NBA Book Analysis Workflow",
            "category": "IMPORTANT",
            "phase": 5,
            "source_book": "Test Book",
            "impact": "HIGH",
            "time_estimate": "1 day",
            "consensus_score": "2/2",
        }

        # You'll need to provide team_id and project_id
        print("To test Linear issue creation, provide team_id and project_id")
        print("Run with --get-teams and --get-projects to find these values")


if __name__ == "__main__":
    asyncio.run(main())
