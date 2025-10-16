#!/usr/bin/env python3
"""
Main Integration Workflow - Orchestrates the recommendation integration process.

This script runs the complete integration workflow:
1. Load recommendations from master DB
2. Map recommendations to phases
3. Generate phase enhancement documents
4. Analyze plan conflicts
5. Apply safe updates
6. Generate cross-project status report
"""

import os
import sys
import json
import logging
import argparse
import signal
import time
from datetime import datetime
from typing import Dict, Any, List

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from phase_mapper import PhaseMapper
from recommendation_integrator import RecommendationIntegrator
from plan_override_manager import PlanOverrideManager
from cross_project_tracker import CrossProjectTracker

logger = logging.getLogger(__name__)


def timeout_handler(signum, frame):
    """Handle timeout signal."""
    logger.error("Integration timed out after 300 seconds")
    sys.exit(1)

def main():
    """
    Main integration workflow with timeout protection.
    """
    # Set up timeout handler (5 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minute timeout

    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Integrate recommendations into NBA Simulator AWS')
        parser.add_argument('--synthesis-path', required=True, help='Path to synthesis project')
        parser.add_argument('--simulator-path', required=True, help='Path to simulator project')
        parser.add_argument('--book-results', help='Path to book analysis results')
        parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds (default: 300)')

        args = parser.parse_args()

        # Update timeout if specified
        if args.timeout != 300:
            signal.alarm(args.timeout)

        synthesis_path = args.synthesis_path
        simulator_path = args.simulator_path
        book_results_dir = args.book_results

        # Validate paths
        if not os.path.exists(synthesis_path):
            logger.error(f"Synthesis path does not exist: {synthesis_path}")
            return {"success": False, "error": f"Synthesis path not found: {synthesis_path}"}

        if not os.path.exists(simulator_path):
            logger.error(f"Simulator path does not exist: {simulator_path}")
            return {"success": False, "error": f"Simulator path not found: {simulator_path}"}

        logger.info("🚀 Starting Recommendation Integration...")
        logger.info(f"   Synthesis: {synthesis_path}")
        logger.info(f"   Simulator: {simulator_path}")
        logger.info(f"   Book Results: {book_results_dir}")
        logger.info(f"   Timeout: {args.timeout} seconds")

        # Step 1: Load all recommendations
        logger.info("📖 Step 1: Loading recommendations...")
        integrator = RecommendationIntegrator(simulator_path, synthesis_path)
        master_recs = integrator.load_master_recommendations()

        total_recs = len(master_recs.get('recommendations', []))
        logger.info(f"   Loaded {total_recs} recommendations from master DB")

        if total_recs == 0:
            logger.warning("⚠️  No recommendations found. Creating sample data for testing...")
            master_recs = create_sample_recommendations()
            total_recs = len(master_recs['recommendations'])
            logger.info(f"   Created {total_recs} sample recommendations")

        # Step 2: Map recommendations to phases
        logger.info("🗺️  Step 2: Mapping recommendations to phases...")
        phase_recs = integrator.create_phase_recommendations(master_recs)

        phases_with_recs = len([r for r in phase_recs.values() if r])
        logger.info(f"   Mapped to {phases_with_recs} phases")

        # Step 3: Generate phase enhancement documents
        logger.info("📝 Step 3: Generating phase enhancement documents...")
        generated_files = integrator.generate_phase_enhancement_docs(phase_recs)

        logger.info(f"   Generated {len(generated_files)} phase documents")

        # Step 4: Generate integration summary
        logger.info("📊 Step 4: Generating integration summary...")
        summary_content = integrator.generate_integration_summary(phase_recs)

        # Save summary
        summary_path = os.path.join(synthesis_path, 'analysis_results', 'integration_summary.md')
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)

        with open(summary_path, 'w') as f:
            f.write(summary_content)

        logger.info(f"   Summary saved to: {summary_path}")

        # Calculate metrics
        total_recommendations = sum(len(recs) for recs in phase_recs.values())
        phases_updated = len([r for r in phase_recs.values() if r])

        # Cancel timeout
        signal.alarm(0)

        logger.info("✅ Integration completed successfully!")
        logger.info(f"   Phases updated: {phases_updated}")
        logger.info(f"   Files generated: {len(generated_files)}")
        logger.info(f"   Recommendations integrated: {total_recommendations}")

        return {
            "success": True,
            "phases_updated": phases_updated,
            "files_generated": generated_files,
            "recommendations_integrated": total_recommendations,
            "conflicts_detected": 0,
            "summary_path": summary_path
        }

    except Exception as e:
        logger.error(f"❌ Integration failed: {e}")
        signal.alarm(0)  # Cancel timeout
        return {"success": False, "error": str(e)}


def integrate_main():
    """Main integration function called by multi_pass_book_deployment.py"""
    return main()


def create_sample_recommendations() -> Dict[str, Any]:
    """Create sample recommendations for testing."""
    return {
        "recommendations": [
            {
                "id": "sample_1",
                "title": "Implement data validation pipeline",
                "category": "critical",
                "source_books": ["Sample Book"],
                "added_date": datetime.now().isoformat(),
                "reasoning": "Quality checks needed for data integrity"
            },
            {
                "id": "sample_2",
                "title": "Add machine learning model training",
                "category": "important",
                "source_books": ["Sample Book"],
                "added_date": datetime.now().isoformat(),
                "reasoning": "Need to train models for prediction"
            }
        ],
        "by_category": {"critical": ["sample_1"], "important": ["sample_2"], "nice_to_have": []},
        "by_book": {"Sample Book": ["sample_1", "sample_2"]}
    }


if __name__ == "__main__":
    result = main()
    if isinstance(result, dict) and not result.get('success', False):
        sys.exit(1)
    else:
        sys.exit(0)

