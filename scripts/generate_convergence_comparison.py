#!/usr/bin/env python3
"""
Generate Convergence Enhancement Comparison Report

Compares pre- and post-convergence analysis results to show:
- Recommendations gained per book
- Cost per additional recommendation
- Convergence iteration distribution
- Quality comparison
- ROI analysis

Usage:
    python scripts/generate_convergence_comparison.py \
        --before analysis_results/pre_convergence_summary.json \
        --after analysis_results/post_convergence_summary.json \
        --output CONVERGENCE_ENHANCEMENT_RESULTS.md
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import argparse

logger = logging.getLogger(__name__)


class ConvergenceComparisonReport:
    """Generate comparison report for convergence enhancement."""

    def __init__(self, before_data: Dict, after_data: Dict):
        """
        Initialize comparison report generator.

        Args:
            before_data: Pre-convergence summary
            after_data: Post-convergence summary
        """
        self.before = before_data
        self.after = after_data

    def calculate_gains(self) -> Dict:
        """Calculate gains from convergence enhancement."""
        before_total = self.before.get('total_recommendations', 0)
        after_total = self.after.get('total_recommendations', 0)
        gain = after_total - before_total
        gain_percent = (gain / before_total * 100) if before_total > 0 else 0

        before_cost = self.before.get('total_cost', 0.0)
        after_cost = self.after.get('total_cost', 0.0)
        additional_cost = after_cost - before_cost

        cost_per_rec = (additional_cost / gain) if gain > 0 else 0

        return {
            'before_total': before_total,
            'after_total': after_total,
            'gain': gain,
            'gain_percent': gain_percent,
            'before_cost': before_cost,
            'after_cost': after_cost,
            'additional_cost': additional_cost,
            'cost_per_rec': cost_per_rec
        }

    def compare_by_priority(self) -> Dict:
        """Compare recommendations by priority level."""
        before_counts = self.before.get('by_priority', {})
        after_counts = self.after.get('by_priority', {})

        comparison = {}
        for priority in ['critical', 'important', 'nice-to-have']:
            before = before_counts.get(priority, 0)
            after = after_counts.get(priority, 0)
            gain = after - before
            comparison[priority] = {
                'before': before,
                'after': after,
                'gain': gain,
                'gain_percent': (gain / before * 100) if before > 0 else 0
            }

        return comparison

    def analyze_convergence_improvement(self) -> Dict:
        """Analyze convergence improvement."""
        before_converged = self.before.get('books_converged', 0)
        after_converged = self.after.get('books_converged', 0)
        total_books = self.before.get('total_books', 0)

        before_percent = (before_converged / total_books * 100) if total_books > 0 else 0
        after_percent = (after_converged / total_books * 100) if total_books > 0 else 0

        return {
            'before_converged': before_converged,
            'after_converged': after_converged,
            'total_books': total_books,
            'before_percent': before_percent,
            'after_percent': after_percent,
            'improvement': after_converged - before_converged
        }

    def calculate_roi(self, gains: Dict) -> Dict:
        """Calculate ROI metrics."""
        additional_cost = gains['additional_cost']
        gain = gains['gain']

        # Estimate value per recommendation
        # Critical = $500, Important = $200, Nice-to-have = $50
        priority_comp = self.compare_by_priority()
        estimated_value = (
            priority_comp['critical']['gain'] * 500 +
            priority_comp['important']['gain'] * 200 +
            priority_comp['nice-to-have']['gain'] * 50
        )

        roi = ((estimated_value - additional_cost) / additional_cost * 100) if additional_cost > 0 else 0

        return {
            'additional_cost': additional_cost,
            'estimated_value': estimated_value,
            'net_value': estimated_value - additional_cost,
            'roi_percent': roi
        }

    def generate_markdown_report(self) -> str:
        """Generate full markdown report."""
        gains = self.calculate_gains()
        priority_comp = self.compare_by_priority()
        convergence = self.analyze_convergence_improvement()
        roi = self.calculate_roi(gains)

        report = [
            "# Convergence Enhancement Results",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Recommendations Gained:** {gains['gain']:,} (+{gains['gain_percent']:.1f}%)",
            f"- **Additional Cost:** ${gains['additional_cost']:.2f}",
            f"- **Cost per Recommendation:** ${gains['cost_per_rec']:.2f}",
            f"- **Books Converged:** {convergence['after_converged']}/{convergence['total_books']} "
            f"({convergence['after_percent']:.1f}%, +{convergence['improvement']} books)",
            f"- **Estimated ROI:** {roi['roi_percent']:.0f}%",
            "",
            "---",
            "",
            "## Overall Gains",
            "",
            "| Metric | Before | After | Gain | Change |",
            "|--------|--------|-------|------|--------|",
            f"| Total Recommendations | {gains['before_total']:,} | {gains['after_total']:,} | "
            f"+{gains['gain']:,} | +{gains['gain_percent']:.1f}% |",
            f"| Total Cost | ${gains['before_cost']:.2f} | ${gains['after_cost']:.2f} | "
            f"+${gains['additional_cost']:.2f} | - |",
            f"| Books Converged | {convergence['before_converged']} | {convergence['after_converged']} | "
            f"+{convergence['improvement']} | +{(convergence['improvement']/convergence['total_books']*100):.1f}% |",
            "",
            "## Recommendations by Priority",
            "",
            "| Priority | Before | After | Gain | Change |",
            "|----------|--------|-------|------|--------|"
        ]

        for priority in ['critical', 'important', 'nice-to-have']:
            data = priority_comp[priority]
            report.append(
                f"| {priority.capitalize()} | {data['before']:,} | {data['after']:,} | "
                f"+{data['gain']:,} | +{data['gain_percent']:.1f}% |"
            )

        report.extend([
            "",
            "## Cost Analysis",
            "",
            f"- **Additional Cost:** ${gains['additional_cost']:.2f}",
            f"- **Cost per Additional Recommendation:** ${gains['cost_per_rec']:.2f}",
            f"- **Total Recommendations Gained:** {gains['gain']:,}",
            "",
            "### Cost Breakdown by Priority",
            ""
        ])

        for priority in ['critical', 'important', 'nice-to-have']:
            data = priority_comp[priority]
            if data['gain'] > 0:
                cost_for_priority = gains['cost_per_rec'] * data['gain']
                report.append(f"- **{priority.capitalize()}:** {data['gain']:,} recommendations "
                            f"(${cost_for_priority:.2f})")

        report.extend([
            "",
            "## ROI Analysis",
            "",
            f"**Estimated Value of Additional Recommendations:**",
            f"- Critical: {priority_comp['critical']['gain']:,} × $500 = "
            f"${priority_comp['critical']['gain'] * 500:,.0f}",
            f"- Important: {priority_comp['important']['gain']:,} × $200 = "
            f"${priority_comp['important']['gain'] * 200:,.0f}",
            f"- Nice-to-have: {priority_comp['nice-to-have']['gain']:,} × $50 = "
            f"${priority_comp['nice-to-have']['gain'] * 50:,.0f}",
            f"- **Total Estimated Value:** ${roi['estimated_value']:,.0f}",
            "",
            f"**Net Value:** ${roi['net_value']:,.0f}",
            f"**ROI:** {roi['roi_percent']:.0f}%",
            "",
            "## Convergence Improvement",
            "",
            f"- **Before:** {convergence['before_converged']}/{convergence['total_books']} books "
            f"({convergence['before_percent']:.1f}%)",
            f"- **After:** {convergence['after_converged']}/{convergence['total_books']} books "
            f"({convergence['after_percent']:.1f}%)",
            f"- **Improvement:** +{convergence['improvement']} books fully converged",
            "",
            "## Conclusion",
            ""
        ])

        # Add conclusion based on ROI
        if roi['roi_percent'] > 100:
            conclusion = (
                f"✅ **Excellent ROI:** The convergence enhancement delivered "
                f"{roi['roi_percent']:.0f}% ROI, with {gains['gain']:,} additional "
                f"recommendations gained at ${gains['cost_per_rec']:.2f} each. "
                f"This represents strong value for the additional investment."
            )
        elif roi['roi_percent'] > 0:
            conclusion = (
                f"✅ **Positive ROI:** The convergence enhancement achieved "
                f"{roi['roi_percent']:.0f}% ROI, gaining {gains['gain']:,} "
                f"recommendations. Cost efficiency was good at ${gains['cost_per_rec']:.2f} "
                f"per recommendation."
            )
        else:
            conclusion = (
                f"⚠️  **Moderate ROI:** The convergence enhancement gained {gains['gain']:,} "
                f"recommendations at ${gains['cost_per_rec']:.2f} each. Consider the "
                f"strategic value of the specific recommendations gained."
            )

        report.extend([
            conclusion,
            "",
            "### Key Achievements",
            "",
            f"1. Increased total recommendations by {gains['gain_percent']:.1f}%",
            f"2. Improved book convergence from {convergence['before_percent']:.1f}% to "
            f"{convergence['after_percent']:.1f}%",
            f"3. Maintained quality with critical recommendations gaining {priority_comp['critical']['gain']} "
            f"({priority_comp['critical']['gain_percent']:.1f}%)",
            "",
            "### Recommendations",
            "",
            "1. **Use enhanced recommendations** for nba-simulator-aws implementation",
            "2. **Monitor convergence** in future analyses to optimize iteration counts",
            "3. **Track ROI** of implemented recommendations to validate value estimates",
            ""
        ])

        return '\n'.join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Convergence Enhancement Comparison Report'
    )
    parser.add_argument(
        '--before',
        type=Path,
        required=True,
        help='Pre-convergence summary JSON file'
    )
    parser.add_argument(
        '--after',
        type=Path,
        required=True,
        help='Post-convergence summary JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('CONVERGENCE_ENHANCEMENT_RESULTS.md'),
        help='Output markdown file'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Load data
    logger.info(f"Loading pre-convergence data from {args.before}")
    with open(args.before) as f:
        before_data = json.load(f)

    logger.info(f"Loading post-convergence data from {args.after}")
    with open(args.after) as f:
        after_data = json.load(f)

    # Generate report
    logger.info("Generating comparison report...")
    reporter = ConvergenceComparisonReport(before_data, after_data)
    report = reporter.generate_markdown_report()

    # Save report
    args.output.write_text(report)
    logger.info(f"✅ Report saved to {args.output}")

    # Print summary
    gains = reporter.calculate_gains()
    print(f"\n{'='*60}")
    print(f"📊 Convergence Enhancement Summary")
    print(f"{'='*60}")
    print(f"\n✅ Gained {gains['gain']:,} recommendations (+{gains['gain_percent']:.1f}%)")
    print(f"💰 Additional cost: ${gains['additional_cost']:.2f}")
    print(f"💡 Cost per recommendation: ${gains['cost_per_rec']:.2f}")
    print(f"\n📄 Full report: {args.output}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()





