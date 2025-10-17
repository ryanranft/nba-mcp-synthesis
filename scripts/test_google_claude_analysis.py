#!/usr/bin/env python3
"""
Test Google Gemini + Claude Book Analysis

This script tests the new Google + Claude approach on 2 books to validate
quality and cost before full deployment.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.google_claude_book_analyzer import GoogleClaudeBookAnalyzer
from mcp_server.env_helper import get_hierarchical_env
from scripts.cost_tracker import CostTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test books configuration
TEST_BOOKS = [
    {
        "id": "designing_ml_systems",
        "title": "Designing Machine Learning Systems",
        "author": "Chip Huyen",
        "content": """
        This book covers the fundamentals of building production-ready machine learning systems.

        Key topics include:
        - Data pipelines and ETL processes
        - Model training and validation
        - Model deployment and monitoring
        - MLOps best practices
        - Feature engineering
        - Model versioning and management
        - A/B testing frameworks
        - Data drift detection
        - Automated retraining pipelines
        - Model explainability and interpretability

        The book emphasizes the importance of:
        - Scalable data processing
        - Robust model validation
        - Continuous monitoring
        - Automated workflows
        - Security and compliance
        - Performance optimization
        """,
    },
    {
        "id": "statistics_601",
        "title": "Statistics 601 Advanced Statistical Methods",
        "author": "Various Authors",
        "content": """
        Advanced statistical methods for data analysis and research.

        Key topics include:
        - Hypothesis testing and statistical inference
        - Bayesian analysis and probability theory
        - Regression analysis and modeling
        - Time series analysis
        - Panel data analysis
        - Causal inference methods
        - Statistical power analysis
        - Experimental design
        - Multivariate analysis
        - Non-parametric methods

        The book covers:
        - Statistical validation frameworks
        - Advanced testing procedures
        - Model selection criteria
        - Robust statistical methods
        - Research methodology
        - Data quality assessment
        """,
    },
]


async def test_google_claude_analysis():
    """Test Google + Claude analysis on 2 books"""

    logger.info("🧪 Starting Google + Claude Book Analysis Test")
    logger.info("=" * 60)

    # Check API keys
    google_api_key = get_hierarchical_env(
        "GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
    )
    claude_api_key = get_hierarchical_env(
        "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
    )

    if not google_api_key:
        logger.error("❌ GOOGLE_API_KEY environment variable not set")
        return False

    if not claude_api_key:
        logger.error("❌ ANTHROPIC_API_KEY environment variable not set")
        return False

    logger.info("✅ API keys found")

    # Initialize analyzer
    try:
        analyzer = GoogleClaudeBookAnalyzer(google_api_key, claude_api_key)
        logger.info("✅ Google + Claude analyzer initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize analyzer: {str(e)}")
        return False

    # Health check
    logger.info("🔍 Running health checks...")
    health_status = await analyzer.health_check()

    if not health_status["overall"]:
        logger.error(f"❌ Health check failed: {health_status}")
        return False

    logger.info(f"✅ Health checks passed: {health_status}")

    # Test analysis on each book
    total_cost = 0.0
    total_tokens = 0
    total_time = 0.0
    all_recommendations = []

    for i, book in enumerate(TEST_BOOKS, 1):
        logger.info(f"\n📖 Testing Book {i}/{len(TEST_BOOKS)}: {book['title']}")
        logger.info("-" * 50)

        try:
            # Run analysis
            result = await analyzer.analyze_book(book)

            # Log results
            logger.info(f"✅ Analysis complete for {book['title']}")
            logger.info(f"   Recommendations: {len(result.recommendations)}")
            logger.info(f"   Cost: ${result.total_cost:.4f}")
            logger.info(f"   Tokens: {result.total_tokens:,}")
            logger.info(f"   Time: {result.total_time:.1f}s")

            # Count by priority
            critical_count = len(
                [r for r in result.recommendations if r.get("priority") == "CRITICAL"]
            )
            important_count = len(
                [r for r in result.recommendations if r.get("priority") == "IMPORTANT"]
            )
            nice_count = len(
                [
                    r
                    for r in result.recommendations
                    if r.get("priority") == "NICE-TO-HAVE"
                ]
            )

            logger.info(f"   Priority breakdown:")
            logger.info(f"     Critical: {critical_count}")
            logger.info(f"     Important: {important_count}")
            logger.info(f"     Nice-to-Have: {nice_count}")

            # Accumulate totals
            total_cost += result.total_cost
            total_tokens += result.total_tokens
            total_time += result.total_time
            all_recommendations.extend(result.recommendations)

            # Save individual results
            output_file = f"test_results_{book['id']}.json"
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "book": book,
                        "result": {
                            "recommendations": result.recommendations,
                            "google_analysis": result.google_analysis,
                            "claude_synthesis": result.claude_synthesis,
                            "total_cost": result.total_cost,
                            "total_tokens": result.total_tokens,
                            "total_time": result.total_time,
                            "google_cost": result.google_cost,
                            "claude_cost": result.claude_cost,
                            "processing_details": result.processing_details,
                        },
                    },
                    f,
                    indent=2,
                )

            logger.info(f"💾 Results saved to {output_file}")

        except Exception as e:
            logger.error(f"❌ Analysis failed for {book['title']}: {str(e)}")
            return False

    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Books analyzed: {len(TEST_BOOKS)}")
    logger.info(f"Total recommendations: {len(all_recommendations)}")
    logger.info(f"Total cost: ${total_cost:.4f}")
    logger.info(f"Total tokens: {total_tokens:,}")
    logger.info(f"Total time: {total_time:.1f}s")
    logger.info(f"Average cost per book: ${total_cost/len(TEST_BOOKS):.4f}")
    logger.info(f"Average tokens per book: {total_tokens//len(TEST_BOOKS):,}")
    logger.info(f"Average time per book: {total_time/len(TEST_BOOKS):.1f}s")

    # Cost analysis
    logger.info(f"\n💰 COST ANALYSIS")
    logger.info("-" * 30)
    logger.info(f"Estimated cost for 20 books: ${total_cost * 10:.2f}")
    logger.info(f"Estimated cost for 17 books: ${total_cost * 8.5:.2f}")

    # Quality assessment
    logger.info(f"\n🎯 QUALITY ASSESSMENT")
    logger.info("-" * 30)

    critical_count = len(
        [r for r in all_recommendations if r.get("priority") == "CRITICAL"]
    )
    important_count = len(
        [r for r in all_recommendations if r.get("priority") == "IMPORTANT"]
    )
    nice_count = len(
        [r for r in all_recommendations if r.get("priority") == "NICE-TO-HAVE"]
    )

    logger.info(f"Critical recommendations: {critical_count}")
    logger.info(f"Important recommendations: {important_count}")
    logger.info(f"Nice-to-Have recommendations: {nice_count}")

    # Check for required fields
    complete_recs = 0
    for rec in all_recommendations:
        required_fields = [
            "title",
            "description",
            "priority",
            "time_estimate",
            "mapped_phase",
        ]
        if all(field in rec for field in required_fields):
            complete_recs += 1

    logger.info(f"Complete recommendations: {complete_recs}/{len(all_recommendations)}")

    # Save summary
    summary = {
        "test_summary": {
            "books_analyzed": len(TEST_BOOKS),
            "total_recommendations": len(all_recommendations),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_time": total_time,
            "average_cost_per_book": total_cost / len(TEST_BOOKS),
            "average_tokens_per_book": total_tokens // len(TEST_BOOKS),
            "average_time_per_book": total_time / len(TEST_BOOKS),
        },
        "cost_projections": {
            "estimated_cost_20_books": total_cost * 10,
            "estimated_cost_17_books": total_cost * 8.5,
        },
        "quality_metrics": {
            "critical_recommendations": critical_count,
            "important_recommendations": important_count,
            "nice_to_have_recommendations": nice_count,
            "complete_recommendations": complete_recs,
            "completion_rate": (
                complete_recs / len(all_recommendations) if all_recommendations else 0
            ),
        },
        "recommendations": all_recommendations,
    }

    with open("google_claude_test_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("💾 Test summary saved to google_claude_test_summary.json")

    # Final assessment
    if (
        total_cost < 5.0
        and len(all_recommendations) >= 10
        and complete_recs >= len(all_recommendations) * 0.8
    ):
        logger.info("\n✅ TEST PASSED - Ready for full deployment!")
        return True
    else:
        logger.warning("\n⚠️ TEST NEEDS REVIEW - Check results before full deployment")
        return False


async def main():
    """Main test function"""
    try:
        success = await test_google_claude_analysis()
        if success:
            logger.info("\n🎉 Google + Claude analysis test completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Google + Claude analysis test failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Test crashed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
