#!/usr/bin/env python3
"""
Git Workflow Manager

Manages git operations for automated code deployment:
- Creates feature branches
- Commits changes with detailed messages
- Pushes to remote
- Creates GitHub PRs using gh CLI
- Manages branch cleanup

Features:
- Automated branch naming
- Rich commit messages
- PR creation with templates
- Labels and metadata
- Rollback support

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import subprocess
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class GitOperationResult:
    """Result of a git operation"""

    success: bool
    operation: str
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class PullRequestInfo:
    """Information about a created PR"""

    pr_number: int
    pr_url: str
    branch: str
    title: str
    created_at: str


class GitWorkflowManager:
    """
    Manages git workflow for automated deployments.

    Features:
    - Branch creation with standard naming
    - Commit with detailed messages
    - Push to remote
    - PR creation via GitHub CLI
    - Branch cleanup
    """

    def __init__(
        self,
        repo_path: str = "../nba-simulator-aws",
        base_branch: str = "main",
        branch_prefix: str = "feature/auto-impl",
    ):
        """
        Initialize Git Workflow Manager.

        Args:
            repo_path: Path to git repository
            base_branch: Base branch for PRs (usually main/master)
            branch_prefix: Prefix for feature branches
        """
        self.repo_path = Path(repo_path).resolve()
        self.base_branch = base_branch
        self.branch_prefix = branch_prefix

        logger.info(f"🔀 Git Workflow Manager initialized")
        logger.info(f"   Repository: {self.repo_path}")
        logger.info(f"   Base branch: {self.base_branch}")
        logger.info(f"   Branch prefix: {self.branch_prefix}")

        # Verify repository
        if not (self.repo_path / ".git").exists():
            logger.warning(f"⚠️  Not a git repository: {self.repo_path}")

    def create_feature_branch(
        self, recommendation: Dict[str, Any]
    ) -> GitOperationResult:
        """
        Create a feature branch for recommendation.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            GitOperationResult with branch creation status
        """
        rec_id = recommendation.get("id", "unknown")
        title = recommendation.get("title", "untitled")

        # Generate branch name
        branch_name = self._generate_branch_name(rec_id, title)

        logger.info(f"🌿 Creating feature branch: {branch_name}")

        try:
            # Ensure we're on base branch and up to date
            self._run_git_command(["checkout", self.base_branch])
            self._run_git_command(["pull", "origin", self.base_branch])

            # Create and checkout feature branch
            result = self._run_git_command(["checkout", "-b", branch_name])

            if result.returncode == 0:
                logger.info(f"   ✅ Branch created successfully")
                return GitOperationResult(
                    success=True,
                    operation="create_branch",
                    message=f"Created branch: {branch_name}",
                    details={"branch_name": branch_name},
                )
            else:
                # Branch might already exist, try checkout
                checkout_result = self._run_git_command(["checkout", branch_name])
                if checkout_result.returncode == 0:
                    logger.info(f"   ℹ️  Branch already exists, checked out")
                    return GitOperationResult(
                        success=True,
                        operation="checkout_branch",
                        message=f"Checked out existing branch: {branch_name}",
                        details={"branch_name": branch_name},
                    )
                else:
                    raise Exception(
                        f"Failed to create or checkout branch: {result.stderr}"
                    )

        except Exception as e:
            logger.error(f"   ❌ Failed to create branch: {e}")
            return GitOperationResult(
                success=False,
                operation="create_branch",
                message="Failed to create branch",
                error=str(e),
            )

    def commit_changes(
        self,
        recommendation: Dict[str, Any],
        files: List[str],
        implementation_summary: str,
    ) -> GitOperationResult:
        """
        Commit changes with detailed message.

        Args:
            recommendation: Recommendation dictionary
            files: List of files to commit
            implementation_summary: Summary of implementation

        Returns:
            GitOperationResult with commit status
        """
        rec_id = recommendation.get("id", "unknown")
        title = recommendation.get("title", "Untitled")
        priority = recommendation.get("priority", "MEDIUM")
        category = recommendation.get("priority_score", {}).get("category", "Unknown")

        logger.info(f"💾 Committing changes for: {title}")

        try:
            # Add files
            for file in files:
                self._run_git_command(["add", file])

            # Generate commit message
            commit_message = self._generate_commit_message(
                recommendation, implementation_summary
            )

            # Commit
            result = self._run_git_command(["commit", "-m", commit_message])

            if result.returncode == 0:
                logger.info(f"   ✅ Changes committed")
                return GitOperationResult(
                    success=True,
                    operation="commit",
                    message="Changes committed successfully",
                    details={
                        "files_committed": len(files),
                        "commit_message": commit_message,
                    },
                )
            else:
                raise Exception(f"Commit failed: {result.stderr}")

        except Exception as e:
            logger.error(f"   ❌ Failed to commit: {e}")
            return GitOperationResult(
                success=False,
                operation="commit",
                message="Failed to commit changes",
                error=str(e),
            )

    def push_to_remote(
        self, branch_name: str, force: bool = False
    ) -> GitOperationResult:
        """
        Push branch to remote.

        Args:
            branch_name: Branch to push
            force: Force push if True

        Returns:
            GitOperationResult with push status
        """
        logger.info(f"⬆️  Pushing to remote: {branch_name}")

        try:
            cmd = ["push", "-u", "origin", branch_name]
            if force:
                cmd.insert(1, "--force")

            result = self._run_git_command(cmd)

            if result.returncode == 0:
                logger.info(f"   ✅ Pushed successfully")
                return GitOperationResult(
                    success=True,
                    operation="push",
                    message=f"Pushed branch to remote: {branch_name}",
                )
            else:
                raise Exception(f"Push failed: {result.stderr}")

        except Exception as e:
            logger.error(f"   ❌ Failed to push: {e}")
            return GitOperationResult(
                success=False,
                operation="push",
                message="Failed to push to remote",
                error=str(e),
            )

    def create_pull_request(
        self,
        recommendation: Dict[str, Any],
        branch_name: str,
        pr_body: str,
        labels: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[PullRequestInfo]]:
        """
        Create GitHub pull request using gh CLI.

        Args:
            recommendation: Recommendation dictionary
            branch_name: Branch name
            pr_body: PR description
            labels: Labels to add to PR

        Returns:
            Tuple of (success, PullRequestInfo or None)
        """
        title = recommendation.get("title", "Untitled")
        priority = recommendation.get("priority", "MEDIUM")

        # Generate PR title
        pr_title = f"[{priority}] {title}"

        logger.info(f"🔀 Creating pull request: {pr_title}")

        try:
            # Check if gh CLI is available
            gh_check = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True
            )

            if gh_check.returncode != 0:
                logger.error("   ❌ GitHub CLI (gh) not installed")
                return False, None

            # Create PR
            cmd = [
                "gh",
                "pr",
                "create",
                "--base",
                self.base_branch,
                "--head",
                branch_name,
                "--title",
                pr_title,
                "--body",
                pr_body,
            ]

            # Add labels
            if labels:
                for label in labels:
                    cmd.extend(["--label", label])

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                # Extract PR URL from output
                pr_url = result.stdout.strip()

                # Extract PR number from URL
                pr_number_match = re.search(r"/pull/(\d+)", pr_url)
                pr_number = int(pr_number_match.group(1)) if pr_number_match else 0

                logger.info(f"   ✅ PR created successfully")
                logger.info(f"      URL: {pr_url}")
                logger.info(f"      Number: #{pr_number}")

                pr_info = PullRequestInfo(
                    pr_number=pr_number,
                    pr_url=pr_url,
                    branch=branch_name,
                    title=pr_title,
                    created_at=datetime.now().isoformat(),
                )

                return True, pr_info
            else:
                logger.error(f"   ❌ Failed to create PR: {result.stderr}")
                return False, None

        except Exception as e:
            logger.error(f"   ❌ Failed to create PR: {e}")
            return False, None

    def rollback_branch(self, branch_name: str) -> GitOperationResult:
        """
        Rollback/delete a branch (cleanup after failure).

        Args:
            branch_name: Branch to delete

        Returns:
            GitOperationResult
        """
        logger.info(f"🔙 Rolling back branch: {branch_name}")

        try:
            # Checkout base branch first
            self._run_git_command(["checkout", self.base_branch])

            # Delete local branch
            result = self._run_git_command(["branch", "-D", branch_name])

            if result.returncode == 0:
                logger.info(f"   ✅ Branch deleted locally")

                # Try to delete remote branch
                try:
                    self._run_git_command(["push", "origin", "--delete", branch_name])
                    logger.info(f"   ✅ Branch deleted from remote")
                except:
                    logger.info(f"   ℹ️  Remote branch not found or already deleted")

                return GitOperationResult(
                    success=True,
                    operation="rollback",
                    message=f"Branch {branch_name} deleted",
                )
            else:
                raise Exception(f"Failed to delete branch: {result.stderr}")

        except Exception as e:
            logger.error(f"   ❌ Failed to rollback: {e}")
            return GitOperationResult(
                success=False,
                operation="rollback",
                message="Failed to rollback branch",
                error=str(e),
            )

    def _generate_branch_name(self, rec_id: str, title: str) -> str:
        """Generate standardized branch name"""
        # Sanitize title
        sanitized = re.sub(r"[^\w\s-]", "", title.lower())
        sanitized = re.sub(r"[-\s]+", "-", sanitized)
        sanitized = sanitized.strip("-")[:40]  # Limit length

        return f"{self.branch_prefix}/{rec_id}/{sanitized}"

    def _generate_commit_message(
        self, recommendation: Dict[str, Any], implementation_summary: str
    ) -> str:
        """Generate detailed commit message"""
        title = recommendation.get("title", "Untitled")
        rec_id = recommendation.get("id", "unknown")
        priority = recommendation.get("priority", "MEDIUM")
        category = recommendation.get("priority_score", {}).get("category", "Unknown")

        # Build commit message
        message_lines = [
            f"feat: {title}",
            "",
            f"Recommendation ID: {rec_id}",
            f"Priority: {priority}",
            f"Category: {category}",
            "",
            "Implementation Summary:",
            implementation_summary,
            "",
            "🤖 Auto-generated by NBA MCP Synthesis",
            "Generated with Claude Code (https://claude.com/claude-code)",
            "",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
        ]

        return "\n".join(message_lines)

    def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a git command in the repository"""
        return subprocess.run(
            ["git"] + args, cwd=self.repo_path, capture_output=True, text=True
        )

    def get_current_branch(self) -> str:
        """Get current branch name"""
        result = self._run_git_command(["branch", "--show-current"])
        return result.stdout.strip()

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        result = self._run_git_command(["status", "--porcelain"])
        return len(result.stdout.strip()) > 0

    def get_branch_status(self, branch_name: str) -> Dict[str, Any]:
        """
        Get status of a branch.

        Args:
            branch_name: Branch to check

        Returns:
            Dictionary with branch status
        """
        try:
            # Check if branch exists locally
            local_result = self._run_git_command(["branch", "--list", branch_name])
            exists_locally = len(local_result.stdout.strip()) > 0

            # Check if branch exists remotely
            remote_result = self._run_git_command(
                ["ls-remote", "--heads", "origin", branch_name]
            )
            exists_remotely = len(remote_result.stdout.strip()) > 0

            # Get last commit
            last_commit = None
            if exists_locally:
                commit_result = self._run_git_command(
                    ["log", "-1", "--format=%H %s", branch_name]
                )
                if commit_result.returncode == 0:
                    last_commit = commit_result.stdout.strip()

            return {
                "exists_locally": exists_locally,
                "exists_remotely": exists_remotely,
                "last_commit": last_commit,
            }

        except Exception as e:
            logger.error(f"Failed to get branch status: {e}")
            return {
                "exists_locally": False,
                "exists_remotely": False,
                "last_commit": None,
                "error": str(e),
            }


def main():
    """CLI for testing git workflow"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Git Workflow Manager")
    parser.add_argument(
        "--repo", default="../nba-simulator-aws", help="Repository path"
    )
    parser.add_argument("--test-recommendation", help="Test recommendation JSON")
    args = parser.parse_args()

    manager = GitWorkflowManager(repo_path=args.repo)

    # Test with sample recommendation
    if args.test_recommendation:
        with open(args.test_recommendation, "r") as f:
            data = json.load(f)
            rec = data[0] if isinstance(data, list) else data

        print(f"\n{'='*60}")
        print(f"Testing Git Workflow")
        print(f"{'='*60}\n")

        # Create branch
        branch_result = manager.create_feature_branch(rec)
        print(f"Branch creation: {branch_result.success}")
        if branch_result.success:
            print(f"  Branch: {branch_result.details['branch_name']}")

    else:
        # Just show status
        print(f"\n{'='*60}")
        print(f"Git Workflow Manager Status")
        print(f"{'='*60}\n")

        print(f"Repository: {manager.repo_path}")
        print(f"Base branch: {manager.base_branch}")
        print(f"Current branch: {manager.get_current_branch()}")
        print(f"Uncommitted changes: {manager.has_uncommitted_changes()}")


if __name__ == "__main__":
    main()
