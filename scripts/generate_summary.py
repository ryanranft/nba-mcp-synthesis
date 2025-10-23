#!/usr/bin/env python3
"""
Generate Analysis Summary

Creates a summary snapshot of current analysis state for before/after comparison.

Usage:
    python3 scripts/generate_summary.py --output analysis_results/pre_convergence_summary.json
"""

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


def generate_summary(output_path: Path) -> Dict:
    """
    Generate comprehensive summary of current state.

    Args:
        output_path: Where to save summary

    Returns:
        Summary dict
    """
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_books': 0,
        'books_converged': 0,
        'total_recommendations': 0,
        'by_priority': {
            'critical': 0,
            'important': 0,
            'nice-to-have': 0
        },
        'total_cost': 0.0,
        'books': []
    }

    # Load synthesis results
    synthesis_file = Path('synthesis_results/synthesis_output_gemini_claude.json')
    if synthesis_file.exists():
        try:
            with open(synthesis_file) as f:
                synthesis_data = json.load(f)

            recs = synthesis_data.get('consensus_recommendations', [])
            summary['total_recommendations'] = len(recs)

            for rec in recs:
                priority = rec.get('priority', 'unknown')
                if priority in summary['by_priority']:
                    summary['by_priority'][priority] += 1
        except Exception as e:
            logger.warning(f"Failed to load synthesis results: {e}")

    # Load convergence trackers
    analysis_dir = Path('analysis_results')
    if analysis_dir.exists():
        tracker_files = list(analysis_dir.glob('*_convergence_tracker.json'))
        summary['total_books'] = len(tracker_files)

        for tracker_file in tracker_files:
            try:
                with open(tracker_file) as f:
                    tracker_data = json.load(f)

                book_title = tracker_data.get('book_title', tracker_file.stem)
                converged = tracker_data.get('convergence_achieved', False)
                iterations = tracker_data.get('iterations_completed', 0)
                recommendations = tracker_data.get('final_count', 0)

                if converged:
                    summary['books_converged'] += 1

                summary['books'].append({
                    'title': book_title,
                    'converged': converged,
                    'iterations': iterations,
                    'recommendations': recommendations
                })
            except Exception as e:
                logger.warning(f"Failed to load tracker {tracker_file}: {e}")

    # Load cost data
    cost_file = Path('cost_tracker/cost_summary.json')
    if cost_file.exists():
        try:
            with open(cost_file) as f:
                cost_data = json.load(f)
            summary['total_cost'] = cost_data.get('total_cost', 0.0)
        except Exception as e:
            logger.warning(f"Failed to load cost data: {e}")

    # Save summary
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary saved to {output_path}")

    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate Analysis Summary')
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('analysis_results/summary.json'),
        help='Output JSON file'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    summary = generate_summary(args.output)

    print(f"\n{'='*60}")
    print(f"Analysis Summary")
    print(f"{'='*60}")
    print(f"\nTotal Books: {summary['total_books']}")
    print(f"Books Converged: {summary['books_converged']}/{summary['total_books']}")
    print(f"\nTotal Recommendations: {summary['total_recommendations']}")
    print(f"  Critical: {summary['by_priority']['critical']}")
    print(f"  Important: {summary['by_priority']['important']}")
    print(f"  Nice-to-have: {summary['by_priority']['nice-to-have']}")
    print(f"\nTotal Cost: ${summary['total_cost']:.2f}")
    print(f"\nSummary saved to: {args.output}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()







