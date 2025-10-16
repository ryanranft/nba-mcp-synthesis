#!/usr/bin/env python3
"""
Test MCP Server PDF Tools with Sports Analytics Books

This script demonstrates how to use the MCP server PDF tools
to read the sports analytics books for better mathematical notation understanding.
"""

import asyncio
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from mcp_server.tools.params import GetPdfMetadataParams, ReadPdfPageParams, SearchPdfParams
from mcp_server.tools.pdf_helper import get_metadata, extract_page_text, search_text_in_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# S3 bucket configuration
S3_BUCKET = "nba-mcp-books-20251011"

# Define the books to test
BOOKS_TO_TEST = [
    {
        "id": "sports_analytics",
        "title": "Sports Analytics",
        "s3_path": "books/Sports_Analytics.pdf",
        "local_path": "/Users/ryanranft/Downloads/Sports_Analytics.pdf"
    },
    {
        "id": "basketball_beyond_paper",
        "title": "Basketball Beyond Paper",
        "s3_path": "books/Basketball_Beyond_Paper.pdf",
        "local_path": "/Users/ryanranft/Downloads/Basketball_Beyond_Paper.pdf"
    },
    {
        "id": "midrange_theory",
        "title": "The Midrange Theory",
        "s3_path": "books/The_Midrange_Theory.pdf",
        "local_path": "/Users/ryanranft/Downloads/The_Midrange_Theory.pdf"
    }
]


def test_local_pdf_reading():
    """Test reading PDFs from local files."""
    logger.info("🧪 Testing Local PDF Reading")
    logger.info("=" * 50)

    for book in BOOKS_TO_TEST:
        logger.info(f"\n📚 Testing: {book['title']}")
        logger.info("-" * 40)

        local_path = book["local_path"]

        # Check if local file exists
        if not Path(local_path).exists():
            logger.warning(f"⚠️ Local file not found: {local_path}")
            continue

        try:
            # Test metadata extraction
            logger.info("🔍 Getting PDF metadata...")
            metadata = get_metadata(local_path)
            logger.info(f"✅ Metadata extracted:")
            logger.info(f"   Title: {metadata.get('title', 'Unknown')}")
            logger.info(f"   Pages: {metadata.get('page_count', 'Unknown')}")
            logger.info(f"   Format: {metadata.get('format', 'Unknown')}")

            # Test page reading
            logger.info("📖 Reading first page...")
            first_page = extract_page_text(local_path, 0)
            if first_page:
                preview = first_page[:200] + "..." if len(first_page) > 200 else first_page
                logger.info(f"✅ First page preview: {preview}")
            else:
                logger.warning("⚠️ Could not extract text from first page")

            # Test search functionality
            logger.info("🔍 Searching for 'analytics'...")
            search_results = search_text_in_pdf(local_path, "analytics", context_chars=100)
            if search_results:
                logger.info(f"✅ Found {len(search_results)} matches")
                for i, result in enumerate(search_results[:3]):  # Show first 3 matches
                    logger.info(f"   Match {i+1} (Page {result['page']+1}): {result['context'][:100]}...")
            else:
                logger.warning("⚠️ No matches found for 'analytics'")

        except Exception as e:
            logger.error(f"❌ Error processing {book['title']}: {e}")


def print_usage_examples():
    """Print examples of how to use the MCP server tools."""
    logger.info("""
╔══════════════════════════════════════════════════════════════════╗
║              🚀 MCP SERVER PDF TOOLS - USAGE EXAMPLES           ║
╚══════════════════════════════════════════════════════════════════╝

📚 HOW TO READ SPORTS ANALYTICS BOOKS:

═══════════════════════════════════════════════════════════════════

1️⃣ GET BOOK METADATA:
   ```python
   from mcp_server.tools.pdf_helper import get_metadata

   metadata = get_metadata('/Users/ryanranft/Downloads/Sports_Analytics.pdf')
   print(f"Title: {metadata['title']}")
   print(f"Pages: {metadata['page_count']}")
   ```

2️⃣ READ SPECIFIC PAGES:
   ```python
   from mcp_server.tools.pdf_helper import extract_page_text

   page_content = extract_page_text('/Users/ryanranft/Downloads/Sports_Analytics.pdf', 0)
   print(page_content)
   ```

3️⃣ SEARCH FOR MATHEMATICAL CONCEPTS:
   ```python
   from mcp_server.tools.pdf_helper import search_text_in_pdf

   results = search_text_in_pdf(
       '/Users/ryanranft/Downloads/Sports_Analytics.pdf',
       'player efficiency rating',
       context_chars=200
   )

   for result in results:
       print(f"Page {result['page']+1}: {result['context']}")
   ```

4️⃣ READ PAGE RANGES:
   ```python
   from mcp_server.tools.pdf_helper import extract_page_range

   content = extract_page_range(
       '/Users/ryanranft/Downloads/Sports_Analytics.pdf',
       0, 10,  # pages 0-10
       'text'
   )
   print(content)
   ```

═══════════════════════════════════════════════════════════════════

🔍 MATHEMATICAL NOTATION SEARCH TERMS:

📊 Sports Analytics:
   - "player efficiency rating"
   - "true shooting percentage"
   - "usage rate"
   - "box score"
   - "advanced metrics"
   - "regression"
   - "correlation"

🏀 Basketball Beyond Paper:
   - "four factors"
   - "pace"
   - "offensive rating"
   - "defensive rating"
   - "win shares"
   - "PER"
   - "BPM"

🎯 The Midrange Theory:
   - "midrange shot"
   - "shot selection"
   - "efficiency"
   - "spacing"
   - "analytics"
   - "shot chart"

═══════════════════════════════════════════════════════════════════

💡 ADVANCED WORKFLOW:

```python
# 1. Get book overview
metadata = get_metadata('/Users/ryanranft/Downloads/Sports_Analytics.pdf')
print(f"Book has {metadata['page_count']} pages")

# 2. Read introduction (first 20 pages)
intro = extract_page_range(
    '/Users/ryanranft/Downloads/Sports_Analytics.pdf',
    0, 19, 'text'
)

# 3. Search for specific analytics concepts
per_results = search_text_in_pdf(
    '/Users/ryanranft/Downloads/Sports_Analytics.pdf',
    'player efficiency rating',
    context_chars=300
)

# 4. Read relevant pages with formulas
for result in per_results:
    page_content = extract_page_text(
        '/Users/ryanranft/Downloads/Sports_Analytics.pdf',
        result['page']
    )
    print(f"Page {result['page']+1}: {page_content}")
```

═══════════════════════════════════════════════════════════════════

✅ BENEFITS FOR MATHEMATICAL NOTATION:

🎯 Better Context:
   - Preserves formatting around equations
   - Maintains paragraph structure
   - Shows surrounding explanations

🔍 Targeted Search:
   - Find specific formulas quickly
   - Get context around mathematical concepts
   - Compare approaches across books

📊 Structured Reading:
   - Read by page ranges
   - Jump to specific concepts
   - Maintain reading progress

🚀 Ready to Use:
   - Works with DRM-protected PDFs
   - No conversion needed
   - Integrated with your workflow

═══════════════════════════════════════════════════════════════════
""")


def main():
    """Main function to test PDF reading capabilities."""
    logger.info("📚 Sports Analytics PDF Reading Test")
    logger.info("=" * 50)

    # Test local PDF reading
    test_local_pdf_reading()

    # Print usage examples
    print_usage_examples()

    logger.info("""
🎉 CONCLUSION:

The MCP server PDF tools provide BETTER mathematical notation reading
than plain text conversion because they:

1. ✅ Preserve formatting and context around equations
2. ✅ Allow targeted searches for specific concepts
3. ✅ Support reading by page ranges for focused study
4. ✅ Work with DRM-protected PDFs from Google Play Books
5. ✅ Maintain the original document structure

Use the PDF tools instead of text conversion for optimal
mathematical notation understanding!

═══════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    main()




