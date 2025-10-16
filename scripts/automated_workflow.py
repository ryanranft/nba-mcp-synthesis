#!/usr/bin/env python3
"""
Automated Workflow Orchestrator

Main orchestrator for the automated book analysis workflow with notifications.
Handles the complete end-to-end process with Slack and Linear integration.

Updated to use the new unified secrets and configuration management system.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from mcp_server.env_helper import get_hierarchical_env

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.notification_manager import NotificationManager
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomatedWorkflow:
    """Automated workflow orchestrator with notifications."""

    def __init__(
        self,
        config_file: str,
        budget: float,
        notification_manager: NotificationManager,
        output_dir: str = "analysis_results"
    ):
        """
        Initialize automated workflow.

        Args:
            config_file: Path to books configuration file
            budget: Maximum budget in USD
            notification_manager: Notification manager instance
            output_dir: Output directory for results
        """
        self.config_file = config_file
        self.budget = budget
        self.notifier = notification_manager
        self.output_dir = Path(output_dir)
        self.start_time = datetime.now()
        self.results = {
            'books_analyzed': 0,
            'recommendations_generated': 0,
            'total_cost': 0.0,
            'files_generated': 0,
            'linear_issues_created': 0,
            'errors': []
        }

        # Load configuration
        self.config = self._load_config()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("✅ Automated workflow initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load books configuration."""
        with open(self.config_file, 'r') as f:
            config = json.load(f)

        logger.info(f"Loaded configuration: {len(config.get('books', []))} books")
        return config

    async def _safe_execute(self, stage: str, func, *args, **kwargs):
        """
        Execute stage with error handling and notifications.

        Args:
            stage: Stage name
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or None if failed
        """
        try:
            await self.notifier.notify_stage_start(stage, {
                "description": f"Starting {stage.replace('_', ' ').title()}",
                "books_count": len(self.config.get('books', [])),
                "budget": self.budget
            })

            result = await func(*args, **kwargs)

            await self.notifier.notify_stage_complete(stage, {
                "description": f"{stage.replace('_', ' ').title()} completed successfully",
                **result
            })

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in {stage}: {error_msg}")

            await self.notifier.notify_error(stage, error_msg)

            self.results['errors'].append({
                'stage': stage,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })

            # Decide whether to continue or abort
            critical_stages = ['pre_flight', 'book_analysis']
            if stage in critical_stages:
                logger.error(f"Critical stage {stage} failed, aborting workflow")
                raise
            else:
                logger.warning(f"Non-critical stage {stage} failed, continuing...")
                return None

    async def _pre_flight_checks(self) -> Dict[str, Any]:
        """Run pre-flight checks."""
        logger.info("🔍 Running pre-flight checks...")

        checks = {
            'api_keys_valid': True,
            'budget_sufficient': True,
            'output_dir_writable': True,
            'config_valid': True
        }

        # Check API keys
        required_keys = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        for key in required_keys:
            if not get_hierarchical_env(key, "NBA_MCP_SYNTHESIS", "WORKFLOW"):
                checks['api_keys_valid'] = False
                logger.error(f"Missing API key: {key}")

        # Check budget
        num_books = len(self.config.get('books', []))
        estimated_cost = num_books * 0.20  # Conservative estimate
        if self.budget < estimated_cost:
            checks['budget_sufficient'] = False
            logger.error(f"Budget ${self.budget:.2f} insufficient for {num_books} books (estimated: ${estimated_cost:.2f})")

        # Check output directory
        try:
            test_file = self.output_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            checks['output_dir_writable'] = False
            logger.error(f"Cannot write to output directory: {e}")

        # Check configuration
        if not self.config.get('books'):
            checks['config_valid'] = False
            logger.error("No books found in configuration")

        all_passed = all(checks.values())

        logger.info(f"Pre-flight checks: {'✅ PASSED' if all_passed else '❌ FAILED'}")

        return {
            'checks': checks,
            'all_passed': all_passed,
            'books_count': num_books,
            'estimated_cost': estimated_cost
        }

    async def _analyze_books(self) -> Dict[str, Any]:
        """Run book analysis."""
        logger.info("📚 Starting book analysis...")

        books = self.config.get('books', [])
        total_recommendations = 0
        total_cost = 0.0

        for i, book in enumerate(books):
            book_start_time = datetime.now()

            logger.info(f"Analyzing book {i+1}/{len(books)}: {book.get('title', 'Unknown')}")

            try:
                # Run book analysis using existing script
                cmd = [
                    'python3',
                    'scripts/simplified_recursive_analysis.py',
                    '--config', self.config_file,
                    '--output-dir', str(self.output_dir),
                    '--book', book.get('title', '')
                ]

                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        timeout=600  # 10 minute timeout per book (reduced from 30 minutes)
                    )
                except subprocess.TimeoutExpired:
                    logger.error(f"Book analysis timeout for {book.get('title', 'Unknown')} after 10 minutes")
                    continue

                if result.returncode == 0:
                    # Parse results from output
                    book_recommendations = self._parse_book_results(book.get('id', ''))
                    book_cost = self._estimate_book_cost(book)

                    total_recommendations += book_recommendations
                    total_cost += book_cost

                    book_time = (datetime.now() - book_start_time).total_seconds()

                    # Notify book completion
                    await self.notifier.notify_book_analysis_complete(
                        book_title=book.get('title', 'Unknown'),
                        recommendations=book_recommendations,
                        cost=book_cost,
                        time_taken=book_time
                    )

                    self.results['books_analyzed'] += 1

                else:
                    logger.error(f"Book analysis failed for {book.get('title', 'Unknown')}: {result.stderr}")

            except Exception as e:
                logger.error(f"Error analyzing book {book.get('title', 'Unknown')}: {e}")
                continue

        self.results['recommendations_generated'] = total_recommendations
        self.results['total_cost'] = total_cost

        logger.info(f"Book analysis complete: {total_recommendations} recommendations, ${total_cost:.2f} cost")

        return {
            'books_analyzed': self.results['books_analyzed'],
            'recommendations': total_recommendations,
            'cost': total_cost
        }

    def _parse_book_results(self, book_id: str) -> int:
        """Parse book analysis results to count recommendations."""
        try:
            # Look for book-specific results file
            book_results_file = self.output_dir / f"{book_id}_results.json"
            if book_results_file.exists():
                with open(book_results_file, 'r') as f:
                    data = json.load(f)
                return len(data.get('recommendations', []))

            # Fallback: check master recommendations
            master_file = self.output_dir / 'master_recommendations.json'
            if master_file.exists():
                with open(master_file, 'r') as f:
                    data = json.load(f)
                recommendations = data.get('recommendations', [])
                # Count recommendations from this book
                book_recs = [r for r in recommendations if book_id in r.get('source_books', [])]
                return len(book_recs)

            return 0

        except Exception as e:
            logger.warning(f"Could not parse results for book {book_id}: {e}")
            return 0

    def _estimate_book_cost(self, book: Dict[str, Any]) -> float:
        """Estimate cost for analyzing a single book."""
        # Rough estimate based on book size and complexity
        pages = book.get('pages', 100)
        complexity = book.get('category', 'medium')

        base_cost = 0.05  # Base cost per book

        if complexity == 'high':
            multiplier = 1.5
        elif complexity == 'low':
            multiplier = 0.7
        else:
            multiplier = 1.0

        page_factor = min(pages / 100, 3.0)  # Cap at 3x for very large books

        return base_cost * multiplier * page_factor

    async def _integrate_recommendations(self) -> Dict[str, Any]:
        """Run recommendation integration."""
        logger.info("🔗 Integrating recommendations...")

        try:
            # Run integration script
            cmd = [
                'python3',
                'scripts/integrate_recommendations.py',
                '--synthesis-path', '/Users/ryanranft/nba-mcp-synthesis',
                '--simulator-path', '/Users/ryanranft/nba-simulator-aws'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode == 0:
                # Parse integration results
                phases_updated = self._count_updated_phases()
                files_generated = self._count_generated_files()

                self.results['files_generated'] = files_generated

                logger.info(f"Integration complete: {phases_updated} phases updated, {files_generated} files generated")

                return {
                    'phases_updated': phases_updated,
                    'files_generated': files_generated,
                    'success': True
                }
            else:
                logger.error(f"Integration failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}

        except Exception as e:
            logger.error(f"Error in integration: {e}")
            return {'success': False, 'error': str(e)}

    def _count_updated_phases(self) -> int:
        """Count number of phases that were updated."""
        simulator_path = Path('/Users/ryanranft/nba-simulator-aws/docs/phases')
        phases_updated = 0

        for phase_dir in simulator_path.glob('phase_*'):
            if phase_dir.is_dir():
                # Check if phase has book recommendations
                book_recs_file = phase_dir / 'BOOK_RECOMMENDATIONS_INDEX.md'
                if book_recs_file.exists():
                    phases_updated += 1

        return phases_updated

    def _count_generated_files(self) -> int:
        """Count number of implementation files generated."""
        simulator_path = Path('/Users/ryanranft/nba-simulator-aws/docs/phases')
        files_count = 0

        # Count Python implementation files
        for py_file in simulator_path.rglob('implement_*.py'):
            files_count += 1

        # Count test files
        for test_file in simulator_path.rglob('test_*.py'):
            files_count += 1

        # Count SQL files
        for sql_file in simulator_path.rglob('*_migration.sql'):
            files_count += 1

        # Count CloudFormation files
        for cf_file in simulator_path.rglob('*_infrastructure.yaml'):
            files_count += 1

        # Count implementation guides
        for guide_file in simulator_path.rglob('*_IMPLEMENTATION_GUIDE.md'):
            files_count += 1

        return files_count

    async def _create_linear_issues(self) -> Dict[str, Any]:
        """Create Linear issues for all recommendations."""
        logger.info("📋 Creating Linear issues...")

        try:
            # Load master recommendations
            master_file = self.output_dir / 'master_recommendations.json'
            if not master_file.exists():
                logger.warning("No master recommendations file found")
                return {'issues_created': 0, 'success': False}

            with open(master_file, 'r') as f:
                data = json.load(f)

            recommendations = data.get('recommendations', [])

            if not recommendations:
                logger.warning("No recommendations found to create issues for")
                return {'issues_created': 0, 'success': True}

            # Get team and project IDs from environment
            team_id = get_hierarchical_env("LINEAR_TEAM_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW")
            project_id = get_hierarchical_env("LINEAR_PROJECT_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW")

            if not team_id:
                logger.error("LINEAR_TEAM_ID not set")
                return {'issues_created': 0, 'success': False}

            # Create issues
            issue_ids = await self.notifier.create_linear_issues(
                recommendations=recommendations,
                team_id=team_id,
                project_id=project_id
            )

            self.results['linear_issues_created'] = len(issue_ids)

            logger.info(f"Created {len(issue_ids)} Linear issues")

            return {
                'issues_created': len(issue_ids),
                'success': True
            }

        except Exception as e:
            logger.error(f"Error creating Linear issues: {e}")
            return {'issues_created': 0, 'success': False, 'error': str(e)}

    async def _run_multi_pass_deployment(self) -> Dict[str, Any]:
        """Run multi-pass deployment (Passes 1-5)."""
        logger.info("🔄 Running multi-pass deployment...")

        try:
            from multi_pass_book_deployment import MultiPassOrchestrator

            orchestrator = MultiPassOrchestrator()

            # Run full deployment
            success = await orchestrator.run_full_deployment()

            if success:
                # Count results
                progress_file = Path('analysis_results/multi_pass_progress.json')
                if progress_file.exists():
                    with open(progress_file, 'r') as f:
                        progress = json.load(f)

                    return {
                        'success': True,
                        'phases_updated': progress.get('pass_4', {}).get('phases_updated', 0),
                        'implementations_generated': progress.get('pass_5', {}).get('implementations_generated', 0),
                        'files_created': progress.get('pass_5', {}).get('files_created', 0)
                    }
                else:
                    return {'success': True}
            else:
                return {'success': False, 'error': 'Deployment failed'}

        except Exception as e:
            logger.error(f"Multi-pass deployment error: {e}")
            return {'success': False, 'error': str(e)}

    async def run(self) -> bool:
        """Run the complete automated workflow."""
        logger.info("🚀 Starting automated workflow...")

        try:
            # Stage 1: Pre-flight checks
            pre_flight_result = await self._safe_execute('pre_flight', self._pre_flight_checks)
            if not pre_flight_result or not pre_flight_result.get('all_passed'):
                logger.error("Pre-flight checks failed, aborting workflow")
                return False

            # Stage 2: Book analysis
            analysis_result = await self._safe_execute('book_analysis', self._analyze_books)
            if not analysis_result:
                logger.error("Book analysis failed, aborting workflow")
                return False

            # Stage 3: Integration
            integration_result = await self._safe_execute('integration', self._integrate_recommendations)
            if not integration_result:
                logger.warning("Integration had issues, but continuing...")

            # NEW STAGE 3.5: Multi-Pass Deployment
            deployment_result = await self._safe_execute('multi_pass_deployment', self._run_multi_pass_deployment)
            if deployment_result and deployment_result.get('success'):
                logger.info(f"✅ Multi-pass deployment: {deployment_result.get('implementations_generated', 0)} implementations generated")
                self.results['files_generated'] = deployment_result.get('files_created', 0)
            else:
                logger.warning("Multi-pass deployment had issues, but continuing...")

            # Stage 4: Linear issues
            linear_result = await self._safe_execute('linear_issues', self._create_linear_issues)
            if not linear_result:
                logger.warning("Linear issue creation had issues, but continuing...")

            # Final notification
            duration = (datetime.now() - self.start_time).total_seconds()
            summary = {
                **self.results,
                'duration': duration
            }

            await self.notifier.notify_workflow_complete(summary)

            logger.info("✅ Automated workflow completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            await self.notifier.notify_error('workflow', str(e))
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run automated book analysis workflow')
    parser.add_argument('--config', default='config/books_to_analyze_all_ai_ml.json',
                        help='Path to books configuration file')
    parser.add_argument('--budget', type=float, default=410.0,
                        help='Maximum budget in USD')
    parser.add_argument('--output', default='analysis_results',
                        help='Output directory for results')
    parser.add_argument('--project', default='nba-mcp-synthesis',
                        help='Project name for secrets loading')
    parser.add_argument('--sport', default='NBA',
                        help='Sport name for secrets loading')
    parser.add_argument('--context', default='production',
                        help='Context for secrets loading (production, development, test)')
    parser.add_argument('--slack-webhook', help='Slack webhook URL (overrides secrets)')
    parser.add_argument('--linear-api-key', help='Linear API key (overrides secrets)')
    parser.add_argument('--linear-team-id', help='Linear team ID (overrides secrets)')
    parser.add_argument('--linear-project-id', help='Linear project ID (overrides secrets)')

    args = parser.parse_args()

    # Load secrets using hierarchical loader
    logger.info(f"Loading secrets for project={args.project}, sport={args.sport}, context={args.context}")
    try:
        result = subprocess.run([
            sys.executable,
            "/Users/ryanranft/load_env_hierarchical.py",
            args.project, args.sport, args.context
        ], capture_output=True, text=True, check=True)

        logger.info("✅ Secrets loaded successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to load secrets: {e.stderr}")
        return 1
    except Exception as e:
        logger.error(f"Error loading secrets: {e}")
        return 1

    # Initialize unified configuration manager
    try:
        config = UnifiedConfigurationManager(args.project, args.context)
        logger.info("✅ Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Get credentials from config or command line args
    slack_webhook = args.slack_webhook or config.api_config.slack_webhook_url
    linear_api_key = args.linear_api_key or config.api_config.linear_api_key
    linear_team_id = args.linear_team_id or config.api_config.linear_team_id
    linear_project_id = args.linear_project_id or config.api_config.linear_project_id

    # Validate required credentials
    if not slack_webhook:
        logger.error("Slack webhook URL is required (set via --slack-webhook or secrets)")
        return 1
    if not linear_api_key:
        logger.error("Linear API key is required (set via --linear-api-key or secrets)")
        return 1

    # Set environment variables for backward compatibility
    if linear_team_id:
        os.environ['LINEAR_TEAM_ID'] = linear_team_id
    if linear_project_id:
        os.environ['LINEAR_PROJECT_ID'] = linear_project_id

    # Initialize notification manager
    notifier = NotificationManager(slack_webhook, linear_api_key)

    # Initialize workflow
    workflow = AutomatedWorkflow(
        config_file=args.config,
        budget=args.budget,
        notification_manager=notifier,
        output_dir=args.output
    )

    # Run workflow
    success = await workflow.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())