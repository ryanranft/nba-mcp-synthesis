#!/usr/bin/env python3
"""
Test script for High-Context Book Analyzer

Quick test with a single book to verify:
- Full-context processing (up to 1M chars)
- Both models (Gemini 1.5 Pro + Claude Sonnet 4)
- Consensus synthesis
- Cost tracking accuracy

Usage:
    python test_high_context_analyzer.py

Expected output:
- Cost: ~$0.60-0.70
- Time: 60-120 seconds
- Recommendations: 30-60
- Both models succeed
"""

import asyncio
import logging
import sys
import os
import pytest

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from scripts.high_context_book_analyzer import HighContextBookAnalyzer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_single_book():
    """Test high-context analyzer with a single book."""

    logger.info("=" * 80)
    logger.info("HIGH-CONTEXT BOOK ANALYZER TEST")
    logger.info("=" * 80)

    # Test book metadata
    test_book = {
        "title": "Machine Learning for Absolute Beginners",
        "author": "Oliver Theobald",
        "s3_key": "books/0812_Machine-Learning-for-Absolute-Beginners.pdf",
        "genre": "Machine Learning",
        "priority": "HIGH",
    }

    logger.info(f"\n📖 Test Book: {test_book['title']}")
    logger.info(f"👤 Author: {test_book['author']}")
    logger.info(f"📂 S3 Key: {test_book['s3_key']}")

    try:
        # Initialize analyzer
        logger.info("\n🚀 Initializing High-Context Book Analyzer...")
        analyzer = HighContextBookAnalyzer()

        # Analyze book
        logger.info("\n📊 Starting analysis...")
        logger.info("⏱️  This will take 60-120 seconds...")

        result = await analyzer.analyze_book(test_book)

        # Print results
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 80)

        if result.success:
            logger.info("\n✅ Analysis successful!")

            logger.info(f"\n💰 COST BREAKDOWN:")
            logger.info(f"   Total:        ${result.total_cost:.4f}")
            logger.info(f"   Gemini 1.5 Pro:  ${result.gemini_cost:.4f}")
            logger.info(f"   Claude Sonnet 4: ${result.claude_cost:.4f}")
            logger.info(f"   Pricing Tier:    {result.pricing_tier}")

            logger.info(f"\n📊 TOKEN USAGE:")
            logger.info(f"   Total:    {result.total_tokens:,}")
            logger.info(f"   Gemini:   {result.gemini_tokens:,}")
            logger.info(f"   Claude:   {result.claude_tokens:,}")

            logger.info(f"\n📄 CONTENT:")
            logger.info(f"   Characters analyzed: {result.content_chars:,}")
            logger.info(f"   Estimated tokens:    ~{result.content_chars // 4:,}")

            logger.info(f"\n⏱️  PERFORMANCE:")
            logger.info(f"   Total time:   {result.total_time:.1f}s")
            logger.info(f"   Consensus:    {result.consensus_level}")

            logger.info(f"\n📋 RECOMMENDATIONS:")
            logger.info(f"   Total: {len(result.recommendations)}")

            # Count by priority
            critical = sum(
                1 for r in result.recommendations if r.get("priority") == "CRITICAL"
            )
            important = sum(
                1 for r in result.recommendations if r.get("priority") == "IMPORTANT"
            )
            nice_to_have = sum(
                1 for r in result.recommendations if r.get("priority") == "NICE-TO-HAVE"
            )

            logger.info(f"   Critical:     {critical}")
            logger.info(f"   Important:    {important}")
            logger.info(f"   Nice-to-Have: {nice_to_have}")

            # Count by source
            gemini_count = sum(
                1 for r in result.recommendations if r.get("_source") == "gemini"
            )
            claude_count = sum(
                1 for r in result.recommendations if r.get("_source") == "claude"
            )
            both_count = sum(
                1
                for r in result.recommendations
                if r.get("_consensus", {}).get("both_agree", False)
            )

            logger.info(f"\n🎯 CONSENSUS:")
            logger.info(f"   From Gemini:  {gemini_count}")
            logger.info(f"   From Claude:  {claude_count}")
            logger.info(f"   Both agree:   {both_count}")

            # Show sample recommendations
            logger.info(f"\n📝 SAMPLE RECOMMENDATIONS (first 3):")
            for i, rec in enumerate(result.recommendations[:3], 1):
                logger.info(f"\n   {i}. {rec.get('title', 'N/A')}")
                logger.info(f"      Priority: {rec.get('priority', 'N/A')}")
                logger.info(f"      Source: {rec.get('_source', 'N/A')}")
                logger.info(f"      Category: {rec.get('category', 'N/A')}")
                desc = rec.get("description", "N/A")
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                logger.info(f"      Description: {desc}")

            logger.info("\n" + "=" * 80)
            logger.info("TEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)

            logger.info(
                f"\n💡 Cost projection for 45 books: ${result.total_cost * 45:.2f}"
            )
            logger.info(
                f"⏱️  Time projection for 45 books: {(result.total_time * 45) / 3600:.1f} hours"
            )

            return True

        else:
            logger.error(f"\n❌ Analysis failed: {result.error}")
            return False

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    logger.info("\nStarting High-Context Book Analyzer test...")
    logger.info("This will test the analyzer with a single book.\n")

    success = await test_single_book()

    if success:
        logger.info("\n✅ All tests passed!")
        logger.info("\n📖 Next steps:")
        logger.info("   1. Review the recommendations quality")
        logger.info("   2. Compare with standard analyzer output")
        logger.info("   3. Run test with 3 books for cost validation")
        logger.info("   4. Run full 45-book analysis if satisfied")
        sys.exit(0)
    else:
        logger.error("\n❌ Tests failed!")
        logger.info("\n🔍 Troubleshooting:")
        logger.info("   1. Check API keys are set correctly")
        logger.info("   2. Verify book exists in S3")
        logger.info("   3. Check network connectivity")
        logger.info("   4. Review error messages above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
