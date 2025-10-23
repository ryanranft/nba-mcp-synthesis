#!/usr/bin/env python3
"""
Automated Deployment Orchestrator

Main orchestration script for automated code implementation and deployment.
Coordinates all components to implement recommendations from AI analysis.

Workflow:
1. Load recommendations in dependency order
2. For each recommendation:
   - Map to project structure
   - Analyze existing code
   - Generate implementation with AI
   - Generate and run tests
   - Create branch, commit, push
   - Create GitHub PR
   - Update progress tracker
3. Generate deployment report

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Add parent directory to path for MCP server imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize secrets from hierarchical structure
from mcp_server.secrets_loader import init_secrets

logger_temp = logging.getLogger(__name__)
if not init_secrets(project="nba-mcp-synthesis", context="WORKFLOW", quiet=True):
    logger_temp.warning("⚠️  Secrets not fully loaded - some features may not work")
    logger_temp.warning(
        "⚠️  Ensure secrets are in: /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/"
    )

# Import our modules
from project_structure_mapper import ProjectStructureMapper, FileMapping
from code_integration_analyzer import CodeIntegrationAnalyzer, IntegrationPlan
from ai_code_implementer import ImplementationContext
from ai_code_implementer import AICodeImplementer, GeneratedImplementation
from test_generator_and_runner import TestGeneratorAndRunner, TestResult
from git_workflow_manager import GitWorkflowManager, PullRequestInfo
from deployment_safety_manager import (
    DeploymentSafetyManager,
    SafetyCheckResult,
    DeploymentBackup,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for automated deployment"""

    enabled: bool = True
    mode: str = "pr"  # pr, commit, local
    batch_size: int = 5
    dry_run: bool = False
    block_on_test_failure: bool = True
    max_failures: int = 3
    target_repo: str = "../nba-simulator-aws"
    base_branch: str = "main"
    create_prs: bool = True


@dataclass
class DeploymentResult:
    """Result of deploying a single recommendation"""

    recommendation_id: str
    success: bool
    implementation_generated: bool
    tests_generated: bool
    tests_passed: bool
    branch_created: bool
    pr_created: bool
    pr_url: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class DeploymentReport:
    """Complete deployment report"""

    total_recommendations: int
    successful_deployments: int
    failed_deployments: int
    prs_created: int
    tests_passed: int
    tests_failed: int
    results: List[DeploymentResult]
    start_time: str
    end_time: str
    total_time: float


class AutomatedDeploymentOrchestrator:
    """
    Orchestrates automated code implementation and deployment.

    Coordinates all components to transform recommendations
    into deployed code with PRs.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to configuration YAML
        """
        # Load configuration
        if config_path and Path(config_path).exists():
            self.config = self._load_config(config_path)
        else:
            self.config = DeploymentConfig()

        logger.info(f"🚀 Automated Deployment Orchestrator initialized")
        logger.info(f"   Mode: {self.config.mode}")
        logger.info(f"   Dry run: {self.config.dry_run}")
        logger.info(f"   Target: {self.config.target_repo}")

        # Initialize components
        self.structure_mapper = ProjectStructureMapper(
            target_project=self.config.target_repo
        )
        self.integration_analyzer = CodeIntegrationAnalyzer(
            project_root=self.config.target_repo
        )
        self.code_implementer = AICodeImplementer()
        self.test_runner = TestGeneratorAndRunner(project_root=self.config.target_repo)
        self.git_manager = GitWorkflowManager(
            repo_path=self.config.target_repo, base_branch=self.config.base_branch
        )
        self.safety_manager = DeploymentSafetyManager(
            project_root=self.config.target_repo
        )

        # Deployment state
        self.deployment_results: List[DeploymentResult] = []
        self.start_time: Optional[datetime] = None

    def deploy_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        max_deployments: Optional[int] = None,
    ) -> DeploymentReport:
        """
        Deploy multiple recommendations.

        Args:
            recommendations: List of recommendations to deploy
            max_deployments: Maximum number to deploy (for testing)

        Returns:
            DeploymentReport with results
        """
        self.start_time = datetime.now()

        logger.info(f"📦 Starting deployment batch")
        logger.info(f"   Recommendations: {len(recommendations)}")
        if max_deployments:
            logger.info(f"   Max deployments: {max_deployments}")

        # Limit if specified
        recs_to_deploy = (
            recommendations[:max_deployments] if max_deployments else recommendations
        )

        # Deploy each recommendation
        for i, rec in enumerate(recs_to_deploy, 1):
            logger.info(f"\n{'='*70}")
            logger.info(
                f"Deploying {i}/{len(recs_to_deploy)}: {rec.get('title', 'Untitled')}"
            )
            logger.info(f"{'='*70}\n")

            # Check circuit breaker
            can_proceed, message = self.safety_manager.circuit_breaker.can_proceed()
            if not can_proceed:
                logger.error(f"🚨 {message}")
                logger.error(f"   Stopping deployment batch")
                break

            # Deploy single recommendation
            result = self.deploy_single_recommendation(rec)
            self.deployment_results.append(result)

            # Update circuit breaker
            if result.success:
                self.safety_manager.circuit_breaker.record_success()
            else:
                self.safety_manager.circuit_breaker.record_failure(
                    rec.get("id", "unknown"), result.error_message or "Unknown error"
                )

            # Log result
            if result.success:
                logger.info(f"✅ Deployment successful")
                if result.pr_url:
                    logger.info(f"   PR: {result.pr_url}")
            else:
                logger.error(f"❌ Deployment failed: {result.error_message}")

        # Generate report
        end_time = datetime.now()
        report = self._generate_report(end_time)

        logger.info(f"\n{'='*70}")
        logger.info(f"Deployment Batch Complete")
        logger.info(f"{'='*70}\n")
        logger.info(
            f"Successful: {report.successful_deployments}/{report.total_recommendations}"
        )
        logger.info(f"PRs created: {report.prs_created}")
        logger.info(f"Total time: {report.total_time:.1f}s")

        return report

    def deploy_single_recommendation(
        self, recommendation: Dict[str, Any]
    ) -> DeploymentResult:
        """
        Deploy a single recommendation through complete workflow.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            DeploymentResult
        """
        rec_id = recommendation.get("id", "unknown")
        title = recommendation.get("title", "Untitled")

        result = DeploymentResult(
            recommendation_id=rec_id,
            success=False,
            implementation_generated=False,
            tests_generated=False,
            tests_passed=False,
            branch_created=False,
            pr_created=False,
        )

        start_time = datetime.now()

        try:
            # Step 1: Map to project structure
            logger.info(f"📍 Step 1: Mapping to project structure...")
            file_mapping = self.structure_mapper.map_recommendation(recommendation)

            # Step 2: Analyze integration
            logger.info(f"🔬 Step 2: Analyzing integration strategy...")
            integration_plan = self.integration_analyzer.analyze_integration(
                recommendation, file_mapping.full_path
            )

            # Step 3: Gather context
            logger.info(f"📚 Step 3: Gathering implementation context...")
            context = self._gather_context(file_mapping, integration_plan)

            # Step 4: Generate implementation
            logger.info(f"🤖 Step 4: Generating implementation with AI...")
            implementation = self.code_implementer.implement_recommendation(
                recommendation=recommendation,
                context=context,
                integration_strategy=integration_plan.primary_strategy.value,
            )

            if not implementation:
                result.error_message = "Failed to generate implementation"
                return result

            result.implementation_generated = True
            logger.info(
                f"   ✅ Implementation generated ({len(implementation.code)} chars)"
            )

            # Step 5: Save implementation (to temp in dry run, real location otherwise)
            temp_file = None
            if self.config.dry_run:
                logger.info(f"💾 Step 5: Saving to temp for validation...")
                temp_file = f"/tmp/{Path(file_mapping.full_path).name}"
                self._save_implementation(implementation, temp_file)
                validation_path = temp_file
            else:
                logger.info(f"💾 Step 5: Saving implementation...")
                self._save_implementation(implementation, file_mapping.full_path)
                validation_path = file_mapping.full_path

            # Step 6: Safety checks
            logger.info(f"🛡️  Step 6: Running safety checks...")
            safety_result = self.safety_manager.run_pre_deployment_checks(
                files_to_deploy=[validation_path], recommendation=recommendation
            )

            # Clean up temp file if dry run
            if temp_file and Path(temp_file).exists():
                Path(temp_file).unlink()

            if not safety_result.passed:
                result.error_message = f"Safety checks failed: {len(safety_result.critical_failures)} critical failures"
                return result

            # Step 7: Create backup (if modifying existing)
            backup = None
            if not self.config.dry_run and Path(file_mapping.full_path).exists():
                logger.info(f"💾 Step 7: Creating backup...")
                backup = self.safety_manager.create_backup(
                    files=[file_mapping.full_path], recommendation_id=rec_id
                )

            # Step 8: Generate tests
            logger.info(f"🧪 Step 8: Generating tests...")
            should_proceed, test_result = self.test_runner.generate_and_run_tests(
                implementation_code=implementation.code,
                recommendation=recommendation,
                module_path=file_mapping.full_path,
                block_on_failure=self.config.block_on_test_failure,
            )

            result.tests_generated = True

            if test_result:
                result.tests_passed = test_result.passed
                logger.info(
                    f"   Tests: {test_result.passed_tests}/{test_result.total_tests} passed"
                )

            if not should_proceed:
                result.error_message = (
                    f"Tests failed ({test_result.failed_tests} failures)"
                )
                # Restore backup
                if backup:
                    self.safety_manager.restore_backup(backup)
                return result

            # Step 9: Git workflow (if not dry run and mode is pr or commit)
            if not self.config.dry_run and self.config.mode in ["pr", "commit"]:
                logger.info(f"🌿 Step 9: Git workflow...")

                # Create branch
                branch_result = self.git_manager.create_feature_branch(recommendation)
                if not branch_result.success:
                    result.error_message = (
                        f"Failed to create branch: {branch_result.error}"
                    )
                    return result

                result.branch_created = True
                branch_name = branch_result.details["branch_name"]

                # Commit changes
                files_to_commit = (
                    [file_mapping.full_path, file_mapping.test_full_path]
                    if file_mapping.test_full_path
                    else [file_mapping.full_path]
                )

                commit_result = self.git_manager.commit_changes(
                    recommendation=recommendation,
                    files=files_to_commit,
                    implementation_summary=implementation.description,
                )

                if not commit_result.success:
                    result.error_message = f"Failed to commit: {commit_result.error}"
                    self.git_manager.rollback_branch(branch_name)
                    return result

                # Push to remote
                push_result = self.git_manager.push_to_remote(branch_name)
                if not push_result.success:
                    result.error_message = f"Failed to push: {push_result.error}"
                    self.git_manager.rollback_branch(branch_name)
                    return result

                # Create PR (if configured)
                if self.config.create_prs:
                    logger.info(f"🔀 Step 10: Creating pull request...")
                    pr_body = self._generate_pr_body(
                        recommendation, implementation, test_result
                    )

                    pr_success, pr_info = self.git_manager.create_pull_request(
                        recommendation=recommendation,
                        branch_name=branch_name,
                        pr_body=pr_body,
                        labels=[
                            "auto-generated",
                            f"priority-{recommendation.get('priority', 'medium').lower()}",
                        ],
                    )

                    if pr_success and pr_info:
                        result.pr_created = True
                        result.pr_url = pr_info.pr_url
                        logger.info(f"   ✅ PR created: {pr_info.pr_url}")

            # Success!
            result.success = True

            # Log deployment
            self.safety_manager.log_deployment(
                recommendation_id=rec_id,
                action="deploy",
                status="success",
                details={"pr_url": result.pr_url, "tests_passed": result.tests_passed},
            )

        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            result.error_message = str(e)

            # Log failure
            self.safety_manager.log_deployment(
                recommendation_id=rec_id,
                action="deploy",
                status="failed",
                details={"error": str(e)},
            )

        finally:
            result.execution_time = (datetime.now() - start_time).total_seconds()

        return result

    def _gather_context(
        self, file_mapping: FileMapping, integration_plan: IntegrationPlan
    ) -> ImplementationContext:
        """Gather context for implementation"""
        context = ImplementationContext()

        # If file exists, read it
        file_path = Path(file_mapping.full_path)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    context.existing_code = f.read()

                # Analyze with integration analyzer (already done, but get info)
                module_info = self.integration_analyzer._analyze_module(str(file_path))
                context.existing_classes = module_info.classes
                context.existing_functions = module_info.functions

            except Exception as e:
                logger.warning(f"Could not read existing file: {e}")

        context.integration_strategy = integration_plan.primary_strategy.value

        return context

    def _save_implementation(
        self, implementation: GeneratedImplementation, file_path: str
    ):
        """Save implementation to file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(implementation.code)

        logger.info(f"   💾 Saved: {path}")

    def _generate_pr_body(
        self,
        recommendation: Dict[str, Any],
        implementation: GeneratedImplementation,
        test_result: Optional[TestResult],
    ) -> str:
        """Generate PR description"""
        title = recommendation.get("title", "Untitled")
        description = recommendation.get("description", "")
        priority = recommendation.get("priority", "MEDIUM")
        category = recommendation.get("priority_score", {}).get("category", "Unknown")

        pr_body = f"""# {title}

## Description
{description}

## Metadata
- **Priority**: {priority}
- **Category**: {category}
- **Recommendation ID**: {recommendation.get('id', 'unknown')}

## Implementation Summary
{implementation.description}

## Testing
"""

        if test_result:
            pr_body += f"""- **Total Tests**: {test_result.total_tests}
- **Passed**: {test_result.passed_tests}
- **Failed**: {test_result.failed_tests}
- **Execution Time**: {test_result.execution_time:.2f}s
"""
        else:
            pr_body += "- No automated tests run\n"

        pr_body += """
## Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass and provide adequate coverage
- [ ] Documentation is updated if needed
- [ ] No breaking changes or dependencies resolved
- [ ] Performance impact assessed

## Auto-Generated
🤖 This PR was automatically generated by the NBA MCP Synthesis system using Claude Code.

**Please review carefully before merging.**
"""

        return pr_body

    def _generate_report(self, end_time: datetime) -> DeploymentReport:
        """Generate deployment report"""
        successful = sum(1 for r in self.deployment_results if r.success)
        failed = len(self.deployment_results) - successful
        prs_created = sum(1 for r in self.deployment_results if r.pr_created)
        tests_passed = sum(1 for r in self.deployment_results if r.tests_passed)
        tests_failed = sum(
            1
            for r in self.deployment_results
            if r.tests_generated and not r.tests_passed
        )

        total_time = (end_time - self.start_time).total_seconds()

        return DeploymentReport(
            total_recommendations=len(self.deployment_results),
            successful_deployments=successful,
            failed_deployments=failed,
            prs_created=prs_created,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            results=self.deployment_results,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_time=total_time,
        )

    def _load_config(self, config_path: str) -> DeploymentConfig:
        """Load configuration from YAML"""
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        deployment_config = config_data.get("deployment", {})

        return DeploymentConfig(
            enabled=deployment_config.get("enabled", True),
            mode=deployment_config.get("mode", "pr"),
            batch_size=deployment_config.get("batch_size", 5),
            dry_run=deployment_config.get("dry_run", False),
            block_on_test_failure=config_data.get("testing", {}).get(
                "block_on_failure", True
            ),
            max_failures=config_data.get("safety", {}).get("max_failures", 3),
            target_repo=config_data.get("project", {}).get(
                "target_repo", "../nba-simulator-aws"
            ),
            base_branch=config_data.get("git", {}).get("base_branch", "main"),
            create_prs=config_data.get("git", {}).get("create_prs", True),
        )

    def save_report(self, report: DeploymentReport, output_path: str):
        """Save deployment report to file"""
        report_data = {
            "summary": {
                "total_recommendations": report.total_recommendations,
                "successful_deployments": report.successful_deployments,
                "failed_deployments": report.failed_deployments,
                "prs_created": report.prs_created,
                "tests_passed": report.tests_passed,
                "tests_failed": report.tests_failed,
                "start_time": report.start_time,
                "end_time": report.end_time,
                "total_time": report.total_time,
            },
            "results": [
                {
                    "recommendation_id": r.recommendation_id,
                    "success": r.success,
                    "pr_url": r.pr_url,
                    "tests_passed": r.tests_passed,
                    "error_message": r.error_message,
                    "execution_time": r.execution_time,
                }
                for r in report.results
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"📊 Report saved: {output_path}")


def main():
    """CLI for orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated Deployment Orchestrator")
    parser.add_argument(
        "--recommendations", required=True, help="Recommendations JSON file"
    )
    parser.add_argument("--config", help="Configuration YAML file")
    parser.add_argument(
        "--max-deployments", type=int, help="Max number to deploy (for testing)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no actual deployment)"
    )
    parser.add_argument(
        "--report-output", default="deployment_report.json", help="Report output file"
    )
    args = parser.parse_args()

    # Load recommendations
    with open(args.recommendations, "r") as f:
        recs = json.load(f)

    # Initialize orchestrator
    orchestrator = AutomatedDeploymentOrchestrator(config_path=args.config)

    if args.dry_run:
        orchestrator.config.dry_run = True
        logger.info("🔍 DRY RUN MODE - No actual changes will be made")

    # Deploy
    report = orchestrator.deploy_recommendations(
        recommendations=recs, max_deployments=args.max_deployments
    )

    # Save report
    orchestrator.save_report(report, args.report_output)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Deployment Complete")
    print(f"{'='*70}\n")
    print(f"Total: {report.total_recommendations}")
    print(f"Successful: {report.successful_deployments}")
    print(f"Failed: {report.failed_deployments}")
    print(f"PRs Created: {report.prs_created}")
    print(f"Time: {report.total_time:.1f}s")
    print(f"\nReport: {args.report_output}")


if __name__ == "__main__":
    main()
