#!/usr/bin/env python3
"""
NBA MCP Synthesis - Secrets Migration Script
Migrate production secrets from local files to AWS Secrets Manager
"""

import os
import sys
import json
import boto3
import argparse
from pathlib import Path
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecretsMigrator:
    def __init__(self, region: str = "us-east-1"):
        """Initialize the secrets migrator"""
        self.region = region
        self.secrets_client = boto3.client("secretsmanager", region_name=region)
        self.secrets_base_path = Path(
            "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production"
        )

    def read_local_secret(self, secret_file: str) -> str:
        """Read a secret from local file"""
        secret_path = self.secrets_base_path / f"{secret_file}.env"

        if not secret_path.exists():
            logger.warning(f"Secret file not found: {secret_path}")
            return None

        try:
            with open(secret_path, "r") as f:
                content = f.read().strip()
                logger.info(f"Read secret from {secret_path}")
                return content
        except Exception as e:
            logger.error(f"Error reading secret file {secret_path}: {e}")
            return None

    def create_aws_secret(
        self, secret_name: str, secret_value: str, description: str
    ) -> bool:
        """Create a secret in AWS Secrets Manager"""
        try:
            # Check if secret already exists
            try:
                self.secrets_client.describe_secret(SecretId=secret_name)
                logger.info(f"Secret {secret_name} already exists, updating...")

                # Update existing secret
                self.secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=secret_value,
                    Description=description,
                )
                logger.info(f"Updated secret: {secret_name}")

            except self.secrets_client.exceptions.ResourceNotFoundException:
                # Create new secret
                self.secrets_client.create_secret(
                    Name=secret_name, Description=description, SecretString=secret_value
                )
                logger.info(f"Created secret: {secret_name}")

            return True

        except Exception as e:
            logger.error(f"Error creating/updating secret {secret_name}: {e}")
            return False

    def migrate_secrets(self, dry_run: bool = False) -> Dict[str, Any]:
        """Migrate all secrets from local files to AWS Secrets Manager"""
        results = {"success": [], "failed": [], "skipped": []}

        # Define secret mappings
        secret_mappings = {
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/google-api-key",
                "description": "Google API key for NBA MCP Synthesis production",
            },
            "ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/anthropic-api-key",
                "description": "Anthropic API key for NBA MCP Synthesis production",
            },
            "OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/openai-api-key",
                "description": "OpenAI API key for NBA MCP Synthesis production",
            },
            "DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/deepseek-api-key",
                "description": "DeepSeek API key for NBA MCP Synthesis production",
            },
            "SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/slack-webhook-url",
                "description": "Slack webhook URL for NBA MCP Synthesis production notifications",
            },
            "LINEAR_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/linear-api-key",
                "description": "Linear API key for NBA MCP Synthesis production",
            },
            "LINEAR_TEAM_ID_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/linear-team-id",
                "description": "Linear team ID for NBA MCP Synthesis production",
            },
            "LINEAR_PROJECT_ID_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/linear-project-id",
                "description": "Linear project ID for NBA MCP Synthesis production",
            },
            "DATABASE_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/database-password",
                "description": "Database password for NBA MCP Synthesis production",
            },
            "AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/aws-access-key-id",
                "description": "AWS access key ID for NBA MCP Synthesis production",
            },
            "AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": {
                "aws_name": "nba-mcp-synthesis/production/aws-secret-access-key",
                "description": "AWS secret access key for NBA MCP Synthesis production",
            },
        }

        logger.info(f"Starting secrets migration (dry_run={dry_run})")

        for local_name, config in secret_mappings.items():
            logger.info(f"Processing secret: {local_name}")

            # Read secret from local file
            secret_value = self.read_local_secret(local_name)

            if secret_value is None:
                logger.warning(f"Skipping {local_name} - no local file found")
                results["skipped"].append(
                    {
                        "local_name": local_name,
                        "aws_name": config["aws_name"],
                        "reason": "No local file found",
                    }
                )
                continue

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would migrate {local_name} -> {config['aws_name']}"
                )
                results["success"].append(
                    {
                        "local_name": local_name,
                        "aws_name": config["aws_name"],
                        "description": config["description"],
                        "dry_run": True,
                    }
                )
            else:
                # Create/update secret in AWS
                success = self.create_aws_secret(
                    config["aws_name"], secret_value, config["description"]
                )

                if success:
                    results["success"].append(
                        {
                            "local_name": local_name,
                            "aws_name": config["aws_name"],
                            "description": config["description"],
                        }
                    )
                else:
                    results["failed"].append(
                        {
                            "local_name": local_name,
                            "aws_name": config["aws_name"],
                            "description": config["description"],
                        }
                    )

        return results

    def verify_migration(self) -> Dict[str, Any]:
        """Verify that all secrets were migrated successfully"""
        logger.info("Verifying secrets migration...")

        verification_results = {"verified": [], "missing": [], "errors": []}

        expected_secrets = [
            "nba-mcp-synthesis/production/google-api-key",
            "nba-mcp-synthesis/production/anthropic-api-key",
            "nba-mcp-synthesis/production/openai-api-key",
            "nba-mcp-synthesis/production/deepseek-api-key",
            "nba-mcp-synthesis/production/slack-webhook-url",
            "nba-mcp-synthesis/production/linear-api-key",
            "nba-mcp-synthesis/production/linear-team-id",
            "nba-mcp-synthesis/production/linear-project-id",
            "nba-mcp-synthesis/production/database-password",
            "nba-mcp-synthesis/production/aws-access-key-id",
            "nba-mcp-synthesis/production/aws-secret-access-key",
        ]

        for secret_name in expected_secrets:
            try:
                response = self.secrets_client.describe_secret(SecretId=secret_name)
                verification_results["verified"].append(
                    {
                        "name": secret_name,
                        "arn": response["ARN"],
                        "last_changed": response.get("LastChangedDate"),
                        "description": response.get("Description"),
                    }
                )
                logger.info(f"✓ Verified secret: {secret_name}")

            except self.secrets_client.exceptions.ResourceNotFoundException:
                verification_results["missing"].append(secret_name)
                logger.error(f"✗ Missing secret: {secret_name}")

            except Exception as e:
                verification_results["errors"].append(
                    {"name": secret_name, "error": str(e)}
                )
                logger.error(f"✗ Error verifying secret {secret_name}: {e}")

        return verification_results


def main():
    parser = argparse.ArgumentParser(
        description="Migrate NBA MCP Synthesis secrets to AWS Secrets Manager"
    )
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually migrating",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify existing secrets migration"
    )
    parser.add_argument("--output", help="Output file for results (JSON format)")

    args = parser.parse_args()

    migrator = SecretsMigrator(region=args.region)

    if args.verify:
        # Verify existing migration
        results = migrator.verify_migration()
        logger.info(
            f"Verification complete: {len(results['verified'])} verified, {len(results['missing'])} missing, {len(results['errors'])} errors"
        )

    else:
        # Perform migration
        results = migrator.migrate_secrets(dry_run=args.dry_run)

        logger.info(f"Migration complete:")
        logger.info(f"  Success: {len(results['success'])}")
        logger.info(f"  Failed: {len(results['failed'])}")
        logger.info(f"  Skipped: {len(results['skipped'])}")

        if results["failed"]:
            logger.error("Failed secrets:")
            for secret in results["failed"]:
                logger.error(f"  - {secret['local_name']} -> {secret['aws_name']}")

    # Output results to file if specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")

    # Exit with error code if there were failures
    if not args.verify and results.get("failed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
