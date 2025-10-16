"""
Linear API client for creating issues from book recommendations
"""

import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LinearClient:
    """Linear API client for creating issues"""

    def __init__(self, api_key: str, team_id: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize Linear client

        Args:
            api_key: Linear API key
            team_id: Linear team ID (optional, can be set later)
            project_id: Linear project ID (optional, can be set later)
        """
        self.api_key = api_key
        self.team_id = team_id
        self.project_id = project_id
        self.base_url = "https://api.linear.app/graphql"

        # Priority mapping
        self.priority_map = {
            'CRITICAL': 1,  # Urgent
            'IMPORTANT': 2,  # High
            'NICE_TO_HAVE': 3,  # Normal
            'unknown': 4  # Low
        }

        logger.info("Linear client initialized")

    async def _make_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GraphQL request to Linear API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "query": query,
                "variables": variables or {}
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    logger.error(f"Linear API errors: {data['errors']}")
                    return {'success': False, 'errors': data['errors']}
                return {'success': True, 'data': data['data']}
            else:
                logger.error(f"Linear API request failed: {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Linear API request failed: {e}")
            return {'success': False, 'error': str(e)}

    async def get_team_info(self) -> Dict[str, Any]:
        """Get team information"""
        query = """
        query {
            viewer {
                id
                name
                email
            }
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """

        result = await self._make_request(query)
        if result['success']:
            return result['data']
        return {}

    async def get_projects(self, team_id: str = None) -> List[Dict[str, Any]]:
        """Get projects for team"""
        team = team_id or self.team_id
        if not team:
            logger.error("No team ID provided")
            return []

        query = """
        query GetProjects($teamId: String!) {
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

        result = await self._make_request(query, {"teamId": team})
        if result['success'] and result['data']['team']:
            return result['data']['team']['projects']['nodes']
        return []

    async def create_issue(
        self,
        title: str,
        description: str,
        priority: str = 'IMPORTANT',
        labels: List[str] = None,
        team_id: str = None,
        project_id: str = None
    ) -> str:
        """
        Create Linear issue

        Args:
            title: Issue title
            description: Issue description
            priority: Priority level (CRITICAL, IMPORTANT, NICE_TO_HAVE)
            labels: List of label names
            team_id: Team ID (uses instance default if not provided)
            project_id: Project ID (uses instance default if not provided)

        Returns:
            str: Issue ID if successful, empty string if failed
        """
        team = team_id or self.team_id
        project = project_id or self.project_id

        if not team:
            logger.error("No team ID provided for issue creation")
            return ""

        # Prepare labels
        label_ids = []
        if labels:
            label_ids = await self._get_label_ids(labels, team)

        # Create issue mutation
        mutation = """
        mutation CreateIssue(
            $title: String!,
            $description: String,
            $teamId: String!,
            $projectId: String,
            $priority: Int,
            $labelIds: [String!]
        ) {
            issueCreate(
                input: {
                    title: $title
                    description: $description
                    teamId: $teamId
                    projectId: $projectId
                    priority: $priority
                    labelIds: $labelIds
                }
            ) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """

        variables = {
            "title": title,
            "description": description,
            "teamId": team,
            "priority": self.priority_map.get(priority.upper(), 2),
            "labelIds": label_ids
        }

        if project:
            variables["projectId"] = project

        result = await self._make_request(mutation, variables)

        if result['success'] and result['data']['issueCreate']['success']:
            issue = result['data']['issueCreate']['issue']
            logger.info(f"Created Linear issue: {issue['identifier']} - {issue['title']}")
            return issue['id']
        else:
            logger.error(f"Failed to create Linear issue: {result}")
            return ""

    async def _get_label_ids(self, label_names: List[str], team_id: str) -> List[str]:
        """Get label IDs by name"""
        query = """
        query GetLabels($teamId: String!) {
            team(id: $teamId) {
                labels {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """

        result = await self._make_request(query, {"teamId": team_id})
        if not result['success'] or not result['data']['team']:
            return []

        labels = result['data']['team']['labels']['nodes']
        label_map = {label['name']: label['id'] for label in labels}

        # Return IDs for labels that exist, create missing ones
        label_ids = []
        for name in label_names:
            if name in label_map:
                label_ids.append(label_map[name])
            else:
                # Create missing label
                new_id = await self._create_label(name, team_id)
                if new_id:
                    label_ids.append(new_id)

        return label_ids

    async def _create_label(self, name: str, team_id: str) -> str:
        """Create a new label"""
        mutation = """
        mutation CreateLabel($name: String!, $teamId: String!) {
            issueLabelCreate(
                input: {
                    name: $name
                    teamId: $teamId
                }
            ) {
                success
                issueLabel {
                    id
                    name
                }
            }
        }
        """

        result = await self._make_request(mutation, {"name": name, "teamId": team_id})

        if result['success'] and result['data']['issueLabelCreate']['success']:
            label = result['data']['issueLabelCreate']['issueLabel']
            logger.info(f"Created Linear label: {label['name']}")
            return label['id']

        return ""

    async def create_issues_batch(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple Linear issues in batch

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            List of issue IDs created
        """
        logger.info(f"Creating {len(recommendations)} Linear issues...")

        issue_ids = []
        created_count = 0

        for rec in recommendations:
            try:
                # Prepare issue details
                title = rec.get('title', 'Untitled Recommendation')
                description = self._format_issue_description(rec)
                priority = rec.get('priority', 'IMPORTANT')

                # Generate labels
                labels = self._generate_labels(rec)

                # Create issue
                issue_id = await self.create_issue(
                    title=title,
                    description=description,
                    priority=priority,
                    labels=labels
                )

                if issue_id:
                    issue_ids.append(issue_id)
                    created_count += 1
                    logger.info(f"Created issue {created_count}/{len(recommendations)}: {title}")
                else:
                    logger.warning(f"Failed to create issue for: {title}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error creating issue for {rec.get('title', 'Unknown')}: {e}")
                continue

        logger.info(f"Created {created_count}/{len(recommendations)} Linear issues")
        return issue_ids

    def _format_issue_description(self, rec: Dict[str, Any]) -> str:
        """Format recommendation as Linear issue description"""
        description = f"""## Recommendation Details

**Source:** {', '.join(rec.get('source_books', ['Unknown']))}
**Priority:** {rec.get('priority', 'IMPORTANT')}
**Phase:** {', '.join(map(str, rec.get('phases', [])))}
**Generated:** {datetime.now().isoformat()}

## Description

{rec.get('reasoning', 'No description available')}

## Expected Impact

{rec.get('impact', 'MEDIUM')}

## Implementation Notes

- **Time Estimate:** {rec.get('time_estimate', '1 week')}
- **Category:** {rec.get('category', 'unknown')}
- **Consensus Score:** {rec.get('consensus_score', 'N/A')}

## Files Generated

Implementation files have been generated in the NBA Simulator AWS project:
- Python implementation script
- Test suite
- SQL migrations (if applicable)
- CloudFormation infrastructure (if applicable)
- Implementation guide

## Next Steps

1. Review generated implementation files
2. Execute the implementation script
3. Run tests to verify functionality
4. Deploy infrastructure (if applicable)
5. Mark this issue as complete

---
*Generated by NBA Book Analysis Workflow*
"""
        return description

    def _generate_labels(self, rec: Dict[str, Any]) -> List[str]:
        """Generate labels for recommendation"""
        labels = []

        # Priority label
        priority = rec.get('priority', 'IMPORTANT').lower()
        labels.append(f"priority-{priority}")

        # Phase labels
        phases = rec.get('phases', [])
        for phase in phases:
            labels.append(f"phase-{phase}")

        # Source book labels
        source_books = rec.get('source_books', [])
        for book in source_books:
            # Clean book name for label
            clean_name = book.lower().replace(' ', '-').replace('(', '').replace(')', '')
            labels.append(f"book-{clean_name[:20]}")  # Limit length

        # Category label
        category = rec.get('category', 'unknown').lower()
        labels.append(f"category-{category}")

        # Workflow label
        labels.append("book-analysis-workflow")

        return labels


# Import asyncio for sleep function
import asyncio




