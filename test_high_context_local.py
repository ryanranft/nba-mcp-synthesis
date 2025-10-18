#!/usr/bin/env python3
"""
Test script for High-Context Book Analyzer with local file

Tests the analyzer with a local PDF file instead of S3.
"""

import asyncio
import logging
import sys
import os
import pymupdf  # PyMuPDF

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.high_context_book_analyzer import HighContextBookAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_with_local_file():
    """Test high-context analyzer with a local PDF file."""

    logger.info("=" * 80)
    logger.info("HIGH-CONTEXT BOOK ANALYZER TEST (LOCAL FILE)")
    logger.info("=" * 80)

    # Local book file
    local_book_path = "/Users/ryanranft/nba-mcp-synthesis/books/Designing Machine Learning Systems.pdf"

    logger.info(f"\n📖 Reading local file: {local_book_path}")

    # Extract text from PDF
    try:
        logger.info("📚 Extracting text from PDF...")
        doc = pymupdf.open(local_book_path)

        text_parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())

        full_text = "\n\n".join(text_parts)
        logger.info(f"✅ Extracted {len(full_text):,} characters from {len(doc)} pages")
        doc.close()

    except Exception as e:
        logger.error(f"❌ Failed to read PDF: {e}")
        return False

    # Create test book metadata with content
    test_book = {
        "title": "Designing Machine Learning Systems",
        "author": "Chip Huyen",
        "genre": "Machine Learning",
        "priority": "HIGH",
        "content": full_text  # Provide content directly
    }

    logger.info(f"\n📖 Test Book: {test_book['title']}")
    logger.info(f"👤 Author: {test_book['author']}")
    logger.info(f"📄 Content: {len(full_text):,} characters")

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
            critical = sum(1 for r in result.recommendations if r.get("priority") == "CRITICAL")
            important = sum(1 for r in result.recommendations if r.get("priority") == "IMPORTANT")
            nice_to_have = sum(1 for r in result.recommendations if r.get("priority") == "NICE-TO-HAVE")

            logger.info(f"   Critical:     {critical}")
            logger.info(f"   Important:    {important}")
            logger.info(f"   Nice-to-Have: {nice_to_have}")

            # Count by source
            gemini_count = sum(1 for r in result.recommendations if r.get("_source") == "gemini")
            claude_count = sum(1 for r in result.recommendations if r.get("_source") == "claude")
            both_count = sum(1 for r in result.recommendations
                           if r.get("_consensus", {}).get("both_agree", False))

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
                desc = rec.get('description', 'N/A')
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                logger.info(f"      Description: {desc}")

            logger.info("\n" + "=" * 80)
            logger.info("TEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)

            logger.info(f"\n💡 Cost projection for 45 books: ${result.total_cost * 45:.2f}")
            logger.info(f"⏱️  Time projection for 45 books: {(result.total_time * 45) / 3600:.1f} hours")

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
    logger.info("\nStarting High-Context Book Analyzer test with local file...")
    logger.info("This will test the analyzer with a local PDF book.\n")

    success = await test_with_local_file()

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
        logger.info("   2. Verify local PDF file exists")
        logger.info("   3. Check network connectivity")
        logger.info("   4. Review error messages above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

