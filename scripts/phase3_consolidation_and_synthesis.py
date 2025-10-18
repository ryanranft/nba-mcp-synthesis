#!/usr/bin/env python3
"""
Phase 3: Consolidation and Synthesis (Tier 0 Basic Version)

Consolidates recommendations from all book analyses and prepares
them for file generation in Phase 4.

Tier 0 Features:
- Load recommendations from analysis_results/
- Consolidate into single JSON file
- Basic deduplication
- Save to implementation_plans/consolidated_recommendations.json

Tier 1+ Features (not in Tier 0):
- Claude + GPT-4 synthesis
- Smart integration analysis
- Phase assignment
- Tier assignment

Usage:
    # Basic consolidation
    python scripts/phase3_consolidation_and_synthesis.py

    # With dry-run
    python scripts/phase3_consolidation_and_synthesis.py --dry-run

    # Specific analysis directory
    python scripts/phase3_consolidation_and_synthesis.py --analysis-dir custom_results/
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import hashlib

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from cost_safety_manager import CostSafetyManager
from rollback_manager import RollbackManager
from error_recovery import ErrorRecoveryManager
from checkpoint_manager import CheckpointManager

logger = logging.getLogger(__name__)


class Phase3ConsolidationBasic:
    """
    Basic version of Phase 3: Consolidation and Synthesis.

    Tier 0 Implementation:
    - Loads all analysis results
    - Consolidates recommendations
    - Basic deduplication
    - Saves consolidated output

    Does NOT include (these are Tier 1+):
    - AI-powered synthesis
    - Smart integration analysis
    - Automatic phase assignment
    - Tier classification
    """

    def __init__(
        self,
        analysis_dir: Path = Path("analysis_results"),
        output_dir: Path = Path("implementation_plans")
    ):
        """
        Initialize Phase 3 consolidation.

        Args:
            analysis_dir: Directory containing analysis results
            output_dir: Directory for consolidated output
        """
        self.analysis_dir = analysis_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize safety managers
        self.cost_mgr = CostSafetyManager()
        self.rollback_mgr = RollbackManager()
        self.recovery_mgr = ErrorRecoveryManager()
        self.checkpoint_mgr = CheckpointManager(phase='phase_3', save_interval_seconds=300)  # 5 minutes

        logger.info("📊 Phase 3: Consolidation and Synthesis (Basic)")
        logger.info(f"   Analysis directory: {self.analysis_dir}")
        logger.info(f"   Output directory: {self.output_dir}")

    def _generate_hash(self, text: str) -> str:
        """Generate hash for deduplication."""
        return hashlib.md5(text.lower().encode()).hexdigest()[:8]

    async def consolidate_recommendations(self, dry_run: bool = False) -> Dict:
        """
        Consolidate all recommendations from analysis results.

        Args:
            dry_run: Preview consolidation without saving

        Returns:
            Consolidated recommendations dictionary
        """
        logger.info("\n" + "="*60)
        logger.info("STEP 1: CONSOLIDATE RECOMMENDATIONS")
        logger.info("="*60 + "\n")

        if dry_run:
            logger.info("🔍 DRY RUN MODE - Previewing consolidation\n")

        # Note: Backup is handled by orchestrator, not here

        # Try to resume from checkpoint
        checkpoint = self.checkpoint_mgr.get_latest_checkpoint()
        if checkpoint:
            logger.info(f"💾 Resuming from checkpoint (iteration {checkpoint['iteration']})\n")
            # Return saved consolidated result if complete
            if checkpoint['state'].get('complete', False):
                logger.info("✅ Checkpoint shows consolidation already complete")
                return checkpoint['state']['consolidated']

        # Find all analysis result files
        result_files = list(self.analysis_dir.glob("*_convergence_tracker.json"))

        if len(result_files) == 0:
            logger.error(f"❌ No analysis results found in {self.analysis_dir}")
            logger.error("   Run Phase 2 (recursive_book_analysis.py) first")
            return {'error': 'No analysis results found'}

        logger.info(f"Found {len(result_files)} analysis result files")

        # Load recommendations from each file
        all_recommendations = []
        book_sources = {}

        for idx, result_file in enumerate(result_files, 1):
            try:
                logger.info(f"   Loading: {result_file.name}")

                with open(result_file, 'r') as f:
                    data = json.load(f)

                book_title = data.get('book_title', result_file.stem.replace('_convergence_tracker', ''))
                book_sources[book_title] = result_file.name

                # Extract recommendations from iterations
                for iteration in data.get('iterations', []):
                    recs_dict = iteration.get('recommendations', {})

                    # Iterate over all priority levels
                    for priority in ['critical', 'important', 'nice_to_have']:
                        for rec in recs_dict.get(priority, []):
                            # Add source book info and priority
                            rec['source_book'] = book_title
                            rec['source_file'] = result_file.name
                            rec['priority'] = priority
                            all_recommendations.append(rec)

                # Save checkpoint every 5 minutes (handled by checkpoint manager)
                if not dry_run:
                    self.checkpoint_mgr.save_checkpoint(
                        iteration=idx,
                        state={
                            'processed_books': idx,
                            'total_books': len(result_files),
                            'recommendations_so_far': len(all_recommendations),
                            'complete': False
                        }
                    )

            except Exception as e:
                logger.error(f"   ❌ Error loading {result_file.name}: {e}")
                continue

        logger.info(f"\n✅ Loaded {len(all_recommendations)} total recommendations from {len(book_sources)} books\n")

        # Basic deduplication
        logger.info("Deduplicating recommendations...")
        unique_recs = []
        seen_hashes = set()

        for rec in all_recommendations:
            # Create hash from title + description
            text = f"{rec.get('title', '')}{rec.get('description', '')}".lower()
            rec_hash = self._generate_hash(text)

            if rec_hash not in seen_hashes:
                seen_hashes.add(rec_hash)
                rec['rec_hash'] = rec_hash
                unique_recs.append(rec)

        duplicates_removed = len(all_recommendations) - len(unique_recs)
        logger.info(f"   Removed {duplicates_removed} duplicates")
        logger.info(f"   Unique recommendations: {len(unique_recs)}\n")

        # Create consolidated output
        consolidated = {
            'metadata': {
                'phase': 'phase_3_consolidation',
                'tier': 0,  # Tier 0 basic version
                'timestamp': datetime.now().isoformat(),
                'total_books': len(book_sources),
                'total_recommendations': len(unique_recs),
                'duplicates_removed': duplicates_removed,
                'books_analyzed': list(book_sources.keys())
            },
            'recommendations': unique_recs,
            'book_sources': book_sources
        }

        # Preview in dry-run
        if dry_run:
            logger.info("="*60)
            logger.info("CONSOLIDATION PREVIEW")
            logger.info("="*60)
            logger.info(f"Books analyzed: {len(book_sources)}")
            logger.info(f"Total recommendations: {len(unique_recs)}")
            logger.info(f"\nTop 5 recommendations:")
            for i, rec in enumerate(unique_recs[:5], 1):
                logger.info(f"\n{i}. {rec.get('title', 'Untitled')}")
                logger.info(f"   Source: {rec.get('source_book', 'Unknown')}")
                logger.info(f"   Category: {rec.get('category', 'Unknown')}")

            logger.info("\n⚠️  No files will be created (dry run)")
            return consolidated

        # Save consolidated recommendations
        output_file = self.output_dir / "consolidated_recommendations.json"

        logger.info(f"💾 Saving consolidated recommendations...")
        with open(output_file, 'w') as f:
            json.dump(consolidated, f, indent=2)

        logger.info(f"   ✅ Saved: {output_file}")
        logger.info(f"   Size: {output_file.stat().st_size / 1024:.1f} KB\n")

        # Generate summary report
        self._generate_summary_report(consolidated)

        # Save final checkpoint marking completion
        self.checkpoint_mgr.save_checkpoint(
            iteration=len(result_files),
            state={
                'complete': True,
                'consolidated': consolidated
            },
            force=True
        )

        # Clean up old checkpoints (keep final one)
        logger.info("🗑️  Cleaning up old checkpoints...")
        stats = self.checkpoint_mgr.get_checkpoint_stats()
        logger.info(f"   Kept {stats['valid_checkpoints']} checkpoint(s)\n")

        return consolidated

    def _generate_summary_report(self, consolidated: Dict):
        """Generate human-readable summary report."""
        report = f"""# Phase 3: Consolidation Summary

**Generated:** {datetime.now().isoformat()}
**Phase:** Phase 3 - Consolidation and Synthesis (Tier 0 Basic)

## Statistics

- **Books Analyzed:** {consolidated['metadata']['total_books']}
- **Total Recommendations:** {consolidated['metadata']['total_recommendations']}
- **Duplicates Removed:** {consolidated['metadata']['duplicates_removed']}

## Books Analyzed

"""

        for i, book in enumerate(consolidated['metadata']['books_analyzed'], 1):
            book_recs = [r for r in consolidated['recommendations'] if r.get('source_book') == book]
            report += f"{i}. **{book}** - {len(book_recs)} recommendations\n"

        report += f"""

## Recommendation Categories

"""

        # Count by category
        categories = {}
        for rec in consolidated['recommendations']:
            cat = rec.get('category', 'Uncategorized')
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{cat}**: {count} recommendations\n"

        report += f"""

## Next Steps

1. ✅ Phase 3 consolidation complete
2. ⏭️  Run Phase 4 to generate implementation files:
   ```bash
   python scripts/phase4_file_generation.py
   ```
3. ✅ Then run Phase 8.5 validation:
   ```bash
   python scripts/phase8_5_validation.py
   ```

## Files Generated

- `implementation_plans/consolidated_recommendations.json` - All recommendations
- `implementation_plans/PHASE3_SUMMARY.md` - This report

**Note:** This is the Tier 0 basic version. Tier 1+ includes AI-powered synthesis,
smart integration analysis, and automatic phase/tier assignment.
"""

        report_file = self.output_dir / "PHASE3_SUMMARY.md"
        report_file.write_text(report)
        logger.info(f"📊 Summary report: {report_file}\n")


async def main():
    """Main entry point for Phase 3."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Consolidation and Synthesis (Tier 0 Basic)"
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("analysis_results"),
        help="Directory containing analysis results"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("implementation_plans"),
        help="Output directory for consolidated results"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview consolidation without saving files"
    )

    args = parser.parse_args()

    # Initialize Phase 3
    phase3 = Phase3ConsolidationBasic(
        analysis_dir=args.analysis_dir,
        output_dir=args.output_dir
    )

    # Run consolidation
    result = await phase3.consolidate_recommendations(dry_run=args.dry_run)

    if 'error' in result:
        logger.error("\n❌ Phase 3 failed")
        sys.exit(1)
    else:
        logger.info("\n✅ Phase 3 complete!")
        sys.exit(0)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    asyncio.run(main())

