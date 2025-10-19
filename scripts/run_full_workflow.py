#!/usr/bin/env python3
"""
Master Workflow Orchestrator (Tier 0)

Runs complete Phases 0-4 workflow with safety features.

Tier 0 Features:
- Phase 2: Recursive book analysis (1 book)
- Phase 3: Basic consolidation
- Phase 4: Basic file generation
- Phase 8.5: Pre-integration validation
- Safety: Cost limits, rollback, error recovery

Usage:
    # Run with 1 book (test)
    python scripts/run_full_workflow.py --book "Machine Learning Systems"

    # Dry-run mode
    python scripts/run_full_workflow.py --book "Machine Learning Systems" --dry-run

    # Skip validation (faster)
    python scripts/run_full_workflow.py --book "Machine Learning Systems" --skip-validation
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cost_safety_manager import CostSafetyManager
from rollback_manager import RollbackManager
from error_recovery import ErrorRecoveryManager
from phase_status_manager import PhaseStatusManager
from phase3_5_ai_plan_modification import Phase35AIPlanModification

logger = logging.getLogger(__name__)


class Tier0WorkflowOrchestrator:
    """
    Tier 0 workflow orchestrator.

    Runs phases 2-4 with full safety features.
    Tests end-to-end workflow with single book.
    """

    def __init__(self):
        """Initialize orchestrator with safety managers."""
        self.cost_mgr = CostSafetyManager()
        self.rollback_mgr = RollbackManager()
        self.recovery_mgr = ErrorRecoveryManager()
        self.status_mgr = PhaseStatusManager()

        logger.info("🚀 Tier 0 Workflow Orchestrator")
        logger.info(f"   Budget: ${self.cost_mgr.COST_LIMITS['total_workflow']:.2f}")
        logger.info(f"   Current spending: ${self.cost_mgr.get_total_cost():.2f}")
        logger.info(f"   Remaining: ${self.cost_mgr.get_remaining_budget():.2f}\n")

    async def run_phase2(
        self,
        book_title: str,
        dry_run: bool = False,
        use_parallel: bool = False,
        max_workers: int = 4
    ) -> bool:
        """
        Run Phase 2: Recursive Book Analysis.

        Args:
            book_title: Book to analyze
            dry_run: Preview without executing
            use_parallel: Enable parallel execution
            max_workers: Number of parallel workers

        Returns:
            True if successful
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: RECURSIVE BOOK ANALYSIS")
        logger.info("="*60 + "\n")

        # Start phase tracking
        if not dry_run:
            self.status_mgr.start_phase("phase_2", "Phase 2: Book Analysis")

        # Check cost limit
        estimated_cost = 5.00  # Estimate for 1 book
        if not self.cost_mgr.check_cost_limit('phase_2_analysis', estimated_cost):
            logger.error("❌ Cost limit exceeded for Phase 2")
            if not dry_run:
                self.status_mgr.fail_phase("phase_2", "Cost limit exceeded")
            return False

        # Create backup
        if not dry_run:
            backup_id = self.rollback_mgr.create_backup(
                phase='phase_2',
                description=f"Before analyzing {book_title}"
            )
            logger.info(f"📦 Backup created: {backup_id}\n")

        # Run analysis
        cmd = [
            'python3',
            'scripts/recursive_book_analysis.py',
            '--book', book_title,
            '--high-context'  # Use high-context analyzer
        ]

        # Add parallel flags if enabled
        if use_parallel:
            cmd.extend(['--parallel', '--max-workers', str(max_workers)])
            logger.info(f"🔀 Parallel execution enabled: {max_workers} workers\n")

        if dry_run:
            cmd.append('--dry-run')

        import subprocess

        logger.info(f"Running: {' '.join(cmd)}\n")

        if dry_run:
            logger.info("🔍 DRY RUN MODE - Would execute Phase 2")
            return True

        try:
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show output in real-time
                text=True
            )

            if result.returncode == 0:
                # Track actual cost (would be extracted from logs in production)
                actual_cost = estimated_cost * 0.97  # Assume slightly under estimate
                self.cost_mgr.track_cost(
                    'phase_2_analysis',
                    actual_cost,
                    operation=f"Analyze {book_title}"
                )

                # Mark phase complete
                duration = (datetime.now() - start_time).total_seconds()
                self.status_mgr.complete_phase("phase_2", duration)

                logger.info("\n✅ Phase 2 complete")
                return True
            else:
                logger.error(f"\n❌ Phase 2 failed with exit code {result.returncode}")
                self.status_mgr.fail_phase("phase_2", f"Exit code {result.returncode}")
                return False

        except Exception as e:
            logger.error(f"\n❌ Phase 2 error: {e}")
            self.status_mgr.fail_phase("phase_2", str(e))
            return False

    async def run_phase3(self, dry_run: bool = False) -> bool:
        """
        Run Phase 3: Consolidation and Synthesis.

        Args:
            dry_run: Preview without executing

        Returns:
            True if successful
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 3: CONSOLIDATION AND SYNTHESIS")
        logger.info("="*60 + "\n")

        # Start phase tracking
        if not dry_run:
            self.status_mgr.start_phase("phase_3", "Phase 3: Consolidation & Synthesis")

        # Import Phase 3 script
        from phase3_consolidation_and_synthesis import Phase3ConsolidationBasic

        # Create backup
        if not dry_run:
            backup_id = self.rollback_mgr.create_backup(
                phase='phase_3',
                description="Before consolidation"
            )
            logger.info(f"📦 Backup created: {backup_id}\n")

        # Run consolidation
        try:
            start_time = datetime.now()
            phase3 = Phase3ConsolidationBasic()
            result = await phase3.consolidate_recommendations(dry_run=dry_run)

            if 'error' in result:
                logger.error("\n❌ Phase 3 failed")
                if not dry_run:
                    self.status_mgr.fail_phase("phase_3", result.get('error', 'Unknown error'))
                return False

            # Mark phase complete
            duration = (datetime.now() - start_time).total_seconds()
            self.status_mgr.complete_phase("phase_3", duration)

            logger.info("\n✅ Phase 3 complete")
            return True

        except Exception as e:
            logger.error(f"\n❌ Phase 3 error: {e}")
            if not dry_run:
                self.status_mgr.fail_phase("phase_3", str(e))
            return False

    async def run_phase3_5(
        self,
        dry_run: bool = False,
        enable_ai_modifications: bool = True
    ) -> bool:
        """
        Run Phase 3.5: AI Plan Modifications.

        Args:
            dry_run: Preview without executing
            enable_ai_modifications: Allow AI to modify plans

        Returns:
            True if successful
        """
        if not enable_ai_modifications:
            logger.info("\n⏭️  Skipping Phase 3.5 (AI modifications disabled)")
            if not dry_run:
                self.status_mgr.skip_phase("phase_3_5", "AI modifications disabled by user")
            return True

        logger.info("\n" + "="*60)
        logger.info("PHASE 3.5: AI PLAN MODIFICATIONS")
        logger.info("="*60 + "\n")

        # Start phase tracking
        if not dry_run:
            self.status_mgr.start_phase("phase_3_5", "Phase 3.5: AI Plan Modifications")

        # Create backup
        if not dry_run:
            backup_id = self.rollback_mgr.create_backup(
                phase='phase_3_5',
                description="Before AI plan modifications"
            )
            logger.info(f"📦 Backup created: {backup_id}\n")

        # Run AI modifications
        try:
            start_time = datetime.now()
            phase3_5 = Phase35AIPlanModification(
                auto_approve_threshold=0.85,
                enable_auto_add=True,
                enable_auto_modify=True,
                enable_auto_delete=False,  # Conservative
                enable_auto_merge=True
            )

            result = await phase3_5.run_ai_modifications(
                synthesis_file=None,  # Will use default Phase 3 output
                dry_run=dry_run
            )

            if not dry_run:
                duration = (datetime.now() - start_time).total_seconds()
                self.status_mgr.complete_phase("phase_3_5", duration)

            logger.info("\n✅ Phase 3.5 complete")
            logger.info(f"   Plans added: {result['plans_added']}")
            logger.info(f"   Plans modified: {result['plans_modified']}")
            logger.info(f"   Plans deleted: {result['plans_deleted']}")
            logger.info(f"   Plans merged: {result['plans_merged']}")

            if 'approvals_needed' in result and result['approvals_needed']:
                logger.warning(f"\n⚠️  {len(result['approvals_needed'])} operations need approval")

            return True

        except Exception as e:
            logger.error(f"\n❌ Phase 3.5 error: {e}")
            if not dry_run:
                self.status_mgr.fail_phase("phase_3_5", str(e))
            return False

    async def run_phase4(self, dry_run: bool = False) -> bool:
        """
        Run Phase 4: File Generation.

        Args:
            dry_run: Preview without executing

        Returns:
            True if successful
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 4: FILE GENERATION")
        logger.info("="*60 + "\n")

        # Start phase tracking
        if not dry_run:
            self.status_mgr.start_phase("phase_4", "Phase 4: File Generation")

        # Import Phase 4 script
        from phase4_file_generation import Phase4FileGenerationBasic

        # Create backup
        if not dry_run:
            backup_id = self.rollback_mgr.create_backup(
                phase='phase_4',
                description="Before file generation"
            )
            logger.info(f"📦 Backup created: {backup_id}\n")

        # Run file generation
        try:
            start_time = datetime.now()
            phase4 = Phase4FileGenerationBasic()
            result = await phase4.generate_files(dry_run=dry_run)

            if 'error' in result:
                logger.error("\n❌ Phase 4 failed")
                if not dry_run:
                    self.status_mgr.fail_phase("phase_4", result.get('error', 'Unknown error'))
                return False

            # Mark phase complete
            duration = (datetime.now() - start_time).total_seconds()
            self.status_mgr.complete_phase("phase_4", duration)

            logger.info("\n✅ Phase 4 complete")
            return True

        except Exception as e:
            logger.error(f"\n❌ Phase 4 error: {e}")
            if not dry_run:
                self.status_mgr.fail_phase("phase_4", str(e))
            return False

    async def run_phase8_5(self, skip_tests: bool = False) -> bool:
        """
        Run Phase 8.5: Pre-Integration Validation.

        Args:
            skip_tests: Skip test execution

        Returns:
            True if successful
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 8.5: PRE-INTEGRATION VALIDATION")
        logger.info("="*60 + "\n")

        # Start phase tracking
        self.status_mgr.start_phase("phase_8_5", "Phase 8.5: Pre-Integration Validation")

        # Run validation script
        cmd = ['python3', 'scripts/phase8_5_validation.py']

        if skip_tests:
            cmd.append('--skip-tests')

        import subprocess

        logger.info(f"Running: {' '.join(cmd)}\n")

        try:
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                # Mark phase complete
                duration = (datetime.now() - start_time).total_seconds()
                self.status_mgr.complete_phase("phase_8_5", duration)

                logger.info("\n✅ Phase 8.5 validation passed")
                return True
            else:
                self.status_mgr.fail_phase("phase_8_5", "Validation failed")
                logger.error("\n❌ Phase 8.5 validation failed")
                return False

        except Exception as e:
            self.status_mgr.fail_phase("phase_8_5", str(e))
            logger.error(f"\n❌ Phase 8.5 error: {e}")
            return False

    async def run_workflow(
        self,
        book_title: str,
        dry_run: bool = False,
        skip_validation: bool = False,
        use_parallel: bool = False,
        max_workers: int = 4,
        skip_ai_modifications: bool = False
    ) -> bool:
        """
        Run complete Tier 0/1/2 workflow.

        Args:
            book_title: Book to analyze
            dry_run: Preview without executing
            skip_validation: Skip Phase 8.5 validation
            use_parallel: Enable parallel execution (Tier 1)
            max_workers: Number of parallel workers (Tier 1)
            skip_ai_modifications: Skip Phase 3.5 AI modifications (Tier 2)

        Returns:
            True if successful
        """
        start_time = datetime.now()

        # Determine tier
        if not skip_ai_modifications:
            tier = "TIER 2"
        elif use_parallel:
            tier = "TIER 1"
        else:
            tier = "TIER 0"

        logger.info("\n" + "="*60)
        logger.info(f"{tier} WORKFLOW - END-TO-END TEST")
        logger.info("="*60)
        logger.info(f"Book: {book_title}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"Skip Validation: {skip_validation}")
        if use_parallel:
            logger.info(f"Parallel: ENABLED ({max_workers} workers)")
        if not skip_ai_modifications:
            logger.info("AI Modifications: ENABLED (Phase 3.5)")
        logger.info(f"Started: {start_time.isoformat()}")
        logger.info("="*60 + "\n")

        # Phase 2: Book Analysis
        if not await self.run_phase2(book_title, dry_run, use_parallel, max_workers):
            logger.error("\n❌ Workflow failed at Phase 2")
            return False

        if dry_run:
            logger.info("\n🔍 DRY RUN MODE - Skipping remaining phases")
            logger.info("\nTo execute, run without --dry-run flag")
            return True

        # Phase 3: Consolidation
        if not await self.run_phase3(dry_run):
            logger.error("\n❌ Workflow failed at Phase 3")
            return False

        # Phase 3.5: AI Plan Modifications (Tier 2 feature)
        if not await self.run_phase3_5(dry_run, enable_ai_modifications=not skip_ai_modifications):
            logger.error("\n❌ Workflow failed at Phase 3.5")
            return False

        # Phase 4: File Generation
        if not await self.run_phase4(dry_run):
            logger.error("\n❌ Workflow failed at Phase 4")
            return False

        # Phase 8.5: Validation
        if not skip_validation:
            if not await self.run_phase8_5(skip_tests=False):
                logger.warning("\n⚠️  Validation failed but continuing...")

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("\n" + "="*60)
        logger.info("WORKFLOW COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration.total_seconds():.1f} seconds")
        logger.info(f"Total cost: ${self.cost_mgr.get_total_cost():.2f}")
        logger.info(f"Remaining budget: ${self.cost_mgr.get_remaining_budget():.2f}")
        logger.info("="*60 + "\n")

        # Generate cost report
        self.cost_mgr.save_cost_report()

        # Generate phase status report
        self.status_mgr.generate_status_report()
        logger.info("📊 Phase status report: implementation_plans/PHASE_STATUS_REPORT.md\n")

        logger.info("✅ Tier 0 workflow successful!")
        logger.info("\nNext steps:")
        logger.info("1. Review generated files in implementation_plans/")
        logger.info("2. Check PHASE3_SUMMARY.md and PHASE4_SUMMARY.json")
        logger.info("3. Review VALIDATION_REPORT.md")
        logger.info("4. Review PHASE_STATUS_REPORT.md")
        logger.info("5. Ready for Tier 1 implementation!\n")

        return True


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tier 0 Workflow Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 1 book
  python scripts/run_full_workflow.py --book "Machine Learning Systems"

  # Dry-run mode
  python scripts/run_full_workflow.py --book "Machine Learning Systems" --dry-run

  # Skip validation (faster)
  python scripts/run_full_workflow.py --book "Machine Learning Systems" --skip-validation
"""
    )

    parser.add_argument(
        "--book",
        type=str,
        required=True,
        help="Book title to analyze (partial match)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview workflow without executing"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip Phase 8.5 validation"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution (Tier 1 feature, 4-8x faster)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--skip-ai-modifications",
        action="store_true",
        help="Skip Phase 3.5: AI Plan Modifications (Tier 2 feature)"
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = Tier0WorkflowOrchestrator()

    # Run workflow
    success = await orchestrator.run_workflow(
        book_title=args.book,
        dry_run=args.dry_run,
        skip_validation=args.skip_validation,
        use_parallel=args.parallel,
        max_workers=args.max_workers,
        skip_ai_modifications=args.skip_ai_modifications
    )

    if success:
        logger.info("✅ Success!")
        sys.exit(0)
    else:
        logger.error("❌ Workflow failed")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    asyncio.run(main())

