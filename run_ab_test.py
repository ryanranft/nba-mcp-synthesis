#!/usr/bin/env python3
"""
Run A/B Test for Model Configuration Optimization

Tests different model combinations to find the optimal configuration for:
- Quality of recommendations
- Cost efficiency
- Processing speed
"""

import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run A/B test with 3 representative books."""

    logger.info("=" * 80)
    logger.info("A/B TESTING: MODEL CONFIGURATION OPTIMIZATION")
    logger.info("=" * 80)

    # Import frameworks
    from scripts.ab_testing_framework import ABTestingFramework, ModelConfig
    from scripts.high_context_book_analyzer import HighContextBookAnalyzer

    # Define test books (representative sample)
    test_books = [
        {
            "title": "Designing Machine Learning Systems",
            "s3_key": "books/Designing_Machine_Learning_Systems.pdf",
            "category": "ml_systems"
        },
        {
            "title": "Applied Predictive Modeling",
            "s3_key": "books/applied_predictive_modeling_max_kuhn_kjell_johnson_1518.pdf",
            "category": "statistics"
        },
        {
            "title": "Basketball on Paper",
            "s3_key": "books/Basketball_on_Paper.pdf",
            "category": "sports_analytics"
        }
    ]

    # Use predefined model configurations from framework
    config_names = [
        "gemini_only",
        "claude_only",
        "gemini_claude_consensus",
        "gemini_claude_high_consensus"
    ]

    logger.info(f"📚 Testing {len(test_books)} books")
    logger.info(f"🔬 Testing {len(config_names)} configurations")
    logger.info(f"📊 Total tests: {len(test_books) * len(config_names)}")

    # Initialize A/B testing framework
    framework = ABTestingFramework(results_dir=Path("results/ab_tests"))

    logger.info("\n" + "=" * 80)
    logger.info("STARTING A/B TEST")
    logger.info("=" * 80)

    # Prepare book paths and titles
    book_paths = [book["s3_key"] for book in test_books]
    book_titles = [book["title"] for book in test_books]

    # Run comparison test
    try:
        comparison = await framework.run_comparison_test(
            config_names=config_names,
            book_paths=book_paths,
            book_titles=book_titles
        )

        logger.info("\n" + "=" * 80)
        logger.info("A/B TEST COMPLETE")
        logger.info("=" * 80)

        # Calculate summary metrics
        total_tests = sum(len(results) for results in comparison.values())
        total_cost = sum(
            sum(r.total_cost_usd for r in results)
            for results in comparison.values()
        )

        # Display results summary
        logger.info(f"\n📊 RESULTS SUMMARY:")
        logger.info(f"   Tests run: {total_tests}")
        logger.info(f"   Configurations: {len(comparison)}")
        logger.info(f"   Books: {len(test_books)}")
        logger.info(f"   Total cost: ${total_cost:.2f}")

        # Calculate and show rankings
        logger.info(f"\n📈 CONFIGURATION RANKINGS:")

        # Calculate quality score for each config
        rankings = []
        for config_name, results in comparison.items():
            avg_quality = sum(
                r.critical_count * 3 + r.important_count * 2 + r.nice_to_have_count
                for r in results
            ) / len(results)
            avg_cost = sum(r.total_cost_usd for r in results) / len(results)
            avg_speed = sum(r.processing_time_seconds for r in results) / len(results)
            avg_recs = sum(r.recommendations_found for r in results) / len(results)

            # Calculate overall score (quality + cost-efficiency + speed)
            score = avg_quality * 0.5 + (1/avg_cost if avg_cost > 0 else 0) * 0.3 + (100/avg_speed if avg_speed > 0 else 0) * 0.2

            rankings.append({
                'config_name': config_name,
                'score': score,
                'avg_quality': avg_quality,
                'avg_cost': avg_cost,
                'avg_speed': avg_speed,
                'avg_recs': avg_recs
            })

        # Sort by score
        rankings.sort(key=lambda x: x['score'], reverse=True)

        # Show winner
        winner = rankings[0]
        logger.info(f"\n🏆 WINNER: {winner['config_name']}")
        logger.info(f"   Score: {winner['score']:.3f}")
        logger.info(f"   Avg recommendations: {winner['avg_recs']:.1f}")
        logger.info(f"   Avg quality: {winner['avg_quality']:.2f}")
        logger.info(f"   Avg cost: ${winner['avg_cost']:.4f}")
        logger.info(f"   Avg speed: {winner['avg_speed']:.2f}s")

        # Show all rankings
        logger.info(f"\n📊 ALL RANKINGS:")
        for i, result in enumerate(rankings, 1):
            logger.info(f"   {i}. {result['config_name']}: {result['score']:.3f}")
            logger.info(f"      Quality: {result['avg_quality']:.2f}, "
                       f"Cost: ${result['avg_cost']:.4f}, "
                       f"Speed: {result['avg_speed']:.2f}s")

        # Generate reports
        logger.info(f"\n📄 Generating reports...")
        framework.generate_comparison_report(comparison)

        # Save JSON results
        results_file = framework.results_dir / f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        framework.save_results_json(comparison, results_file)

        logger.info(f"\n✅ Reports saved to: {framework.results_dir}")
        logger.info(f"   - comparison_report.md")
        logger.info(f"   - {results_file.name}")

        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        config_name = winner['config_name']
        if config_name == "gemini_only":
            logger.info(f"   ✓ Use Gemini 1.5 Pro only (no consensus)")
            logger.info(f"   ✓ Best for cost optimization and reasonable quality")
        elif config_name == "claude_only":
            logger.info(f"   ✓ Use Claude Sonnet 4 only (no consensus)")
            logger.info(f"   ✓ Best for highest quality output")
        elif config_name == "gemini_claude_consensus":
            logger.info(f"   ✓ Use Gemini + Claude with 70% consensus threshold")
            logger.info(f"   ✓ Best for balanced quality/cost trade-off")
        elif config_name == "gemini_claude_high_consensus":
            logger.info(f"   ✓ Use Gemini + Claude with 85% consensus threshold")
            logger.info(f"   ✓ Best for highest quality with stricter agreement")

        logger.info(f"   ✓ Update config/workflow_config.yaml with winning configuration")

        return comparison

    except Exception as e:
        logger.error(f"❌ A/B test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        print("\n" + "=" * 80)
        print("✅ A/B TEST SUCCESSFUL")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ A/B TEST FAILED: {e}")
        print("=" * 80)
        exit(1)

