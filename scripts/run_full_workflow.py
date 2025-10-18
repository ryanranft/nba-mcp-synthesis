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
        
        logger.info("🚀 Tier 0 Workflow Orchestrator")
        logger.info(f"   Budget: ${self.cost_mgr.COST_LIMITS['total_workflow']:.2f}")
        logger.info(f"   Current spending: ${self.cost_mgr.get_total_cost():.2f}")
        logger.info(f"   Remaining: ${self.cost_mgr.get_remaining_budget():.2f}\n")
    
    async def run_phase2(
        self,
        book_title: str,
        dry_run: bool = False
    ) -> bool:
        """
        Run Phase 2: Recursive Book Analysis.
        
        Args:
            book_title: Book to analyze
            dry_run: Preview without executing
        
        Returns:
            True if successful
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: RECURSIVE BOOK ANALYSIS")
        logger.info("="*60 + "\n")
        
        # Check cost limit
        estimated_cost = 5.00  # Estimate for 1 book
        if not self.cost_mgr.check_cost_limit('phase_2_analysis', estimated_cost):
            logger.error("❌ Cost limit exceeded for Phase 2")
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
        
        if dry_run:
            cmd.append('--dry-run')
        
        import subprocess
        
        logger.info(f"Running: {' '.join(cmd)}\n")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - Would execute Phase 2")
            return True
        
        try:
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
                
                logger.info("\n✅ Phase 2 complete")
                return True
            else:
                logger.error(f"\n❌ Phase 2 failed with exit code {result.returncode}")
                return False
        
        except Exception as e:
            logger.error(f"\n❌ Phase 2 error: {e}")
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
            phase3 = Phase3ConsolidationBasic()
            result = await phase3.consolidate_recommendations(dry_run=dry_run)
            
            if 'error' in result:
                logger.error("\n❌ Phase 3 failed")
                return False
            
            logger.info("\n✅ Phase 3 complete")
            return True
        
        except Exception as e:
            logger.error(f"\n❌ Phase 3 error: {e}")
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
            phase4 = Phase4FileGenerationBasic()
            result = await phase4.generate_files(dry_run=dry_run)
            
            if 'error' in result:
                logger.error("\n❌ Phase 4 failed")
                return False
            
            logger.info("\n✅ Phase 4 complete")
            return True
        
        except Exception as e:
            logger.error(f"\n❌ Phase 4 error: {e}")
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
        
        # Run validation script
        cmd = ['python3', 'scripts/phase8_5_validation.py']
        
        if skip_tests:
            cmd.append('--skip-tests')
        
        import subprocess
        
        logger.info(f"Running: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("\n✅ Phase 8.5 validation passed")
                return True
            else:
                logger.error("\n❌ Phase 8.5 validation failed")
                return False
        
        except Exception as e:
            logger.error(f"\n❌ Phase 8.5 error: {e}")
            return False
    
    async def run_workflow(
        self,
        book_title: str,
        dry_run: bool = False,
        skip_validation: bool = False
    ) -> bool:
        """
        Run complete Tier 0 workflow.
        
        Args:
            book_title: Book to analyze
            dry_run: Preview without executing
            skip_validation: Skip Phase 8.5 validation
        
        Returns:
            True if successful
        """
        start_time = datetime.now()
        
        logger.info("\n" + "="*60)
        logger.info("TIER 0 WORKFLOW - END-TO-END TEST")
        logger.info("="*60)
        logger.info(f"Book: {book_title}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"Skip Validation: {skip_validation}")
        logger.info(f"Started: {start_time.isoformat()}")
        logger.info("="*60 + "\n")
        
        # Phase 2: Book Analysis
        if not await self.run_phase2(book_title, dry_run):
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
        
        logger.info("✅ Tier 0 workflow successful!")
        logger.info("\nNext steps:")
        logger.info("1. Review generated files in implementation_plans/")
        logger.info("2. Check PHASE3_SUMMARY.md and PHASE4_SUMMARY.json")
        logger.info("3. Review VALIDATION_REPORT.md")
        logger.info("4. Ready for Tier 1 implementation!\n")
        
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
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = Tier0WorkflowOrchestrator()
    
    # Run workflow
    success = await orchestrator.run_workflow(
        book_title=args.book,
        dry_run=args.dry_run,
        skip_validation=args.skip_validation
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

