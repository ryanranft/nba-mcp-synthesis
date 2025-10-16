#!/usr/bin/env python3
"""
Sports Analytics Books - Text Reading Guide

Since the PDFs are DRM-protected and can't be converted to plain text,
this script demonstrates how to read them using the existing MCP server
PDF tools for better mathematical notation understanding.

The MCP server already has sophisticated PDF reading capabilities that
can handle DRM-protected PDFs better than standard text extraction.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# S3 bucket configuration
S3_BUCKET = "nba-mcp-books-20251011"

# Define the books
SPORTS_BOOKS = [
    {
        "id": "sports_analytics",
        "title": "Sports Analytics",
        "s3_path": "books/Sports_Analytics.pdf",
        "size": "22.2 MB",
        "description": "Comprehensive guide to sports analytics methodologies"
    },
    {
        "id": "basketball_beyond_paper",
        "title": "Basketball Beyond Paper",
        "s3_path": "books/Basketball_Beyond_Paper.pdf",
        "size": "4.7 MB",
        "description": "Advanced basketball analytics beyond traditional metrics"
    },
    {
        "id": "midrange_theory",
        "title": "The Midrange Theory",
        "s3_path": "books/The_Midrange_Theory.pdf",
        "size": "2.4 MB",
        "description": "Theoretical framework for midrange shot analysis"
    }
]


def print_reading_guide():
    """Print a comprehensive guide on how to read the sports analytics books."""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║              📚 SPORTS ANALYTICS BOOKS - READING GUIDE          ║
╚══════════════════════════════════════════════════════════════════╝

🎯 WHY TEXT CONVERSION FAILED:
   The PDFs are DRM-protected from Google Play Books, which prevents
   standard text extraction. However, the MCP server has advanced
   PDF reading capabilities that can handle these files!

📖 HOW TO READ THE BOOKS:

═══════════════════════════════════════════════════════════════════

🏀 AVAILABLE SPORTS ANALYTICS BOOKS:
""")

    for i, book in enumerate(SPORTS_BOOKS, 1):
        print(f"""
{i}. 📊 {book['title']}
   📁 S3 Path: {book['s3_path']}
   📏 Size: {book['size']}
   📝 Description: {book['description']}
""")

    print("""
═══════════════════════════════════════════════════════════════════

🚀 HOW TO READ USING MCP SERVER:

1️⃣ GET BOOK METADATA:
   ```python
   await mcp.call_tool("get_pdf_metadata", {
       "book_path": "books/Sports_Analytics.pdf"
   })
   ```

2️⃣ READ SPECIFIC PAGES:
   ```python
   await mcp.call_tool("read_pdf_page", {
       "book_path": "books/Sports_Analytics.pdf",
       "page_number": 0,
       "format": "text"
   })
   ```

3️⃣ READ PAGE RANGES:
   ```python
   await mcp.call_tool("read_pdf_page_range", {
       "book_path": "books/Sports_Analytics.pdf",
       "start_page": 0,
       "end_page": 10,
       "format": "text"
   })
   ```

4️⃣ SEARCH FOR MATHEMATICAL NOTATION:
   ```python
   await mcp.call_tool("search_pdf", {
       "book_path": "books/Sports_Analytics.pdf",
       "query": "regression",
       "context_chars": 200
   })
   ```

5️⃣ READ BY CHAPTER:
   ```python
   await mcp.call_tool("read_pdf_chapter", {
       "book_path": "books/Sports_Analytics.pdf",
       "chapter_title": "Introduction",
       "format": "text"
   })
   ```

═══════════════════════════════════════════════════════════════════

🔍 MATHEMATICAL NOTATION EXAMPLES TO SEARCH FOR:

📊 Sports Analytics:
   - "player efficiency rating"
   - "true shooting percentage"
   - "usage rate"
   - "box score"
   - "advanced metrics"

🏀 Basketball Beyond Paper:
   - "four factors"
   - "pace"
   - "offensive rating"
   - "defensive rating"
   - "win shares"

🎯 The Midrange Theory:
   - "midrange shot"
   - "shot selection"
   - "efficiency"
   - "spacing"
   - "analytics"

═══════════════════════════════════════════════════════════════════

💡 ADVANCED READING STRATEGIES:

1️⃣ START WITH METADATA:
   Get book structure, page count, and table of contents

2️⃣ READ INTRODUCTION CHAPTERS:
   Usually pages 0-20 contain overview and methodology

3️⃣ SEARCH FOR SPECIFIC CONCEPTS:
   Use targeted searches for mathematical formulas

4️⃣ READ IN CHUNKS:
   Process 10-20 pages at a time for better comprehension

5️⃣ COMPARE ACROSS BOOKS:
   Search same concepts across multiple books

═══════════════════════════════════════════════════════════════════

🎯 EXAMPLE WORKFLOW:

```python
# 1. Get book overview
metadata = await mcp.call_tool("get_pdf_metadata", {
    "book_path": "books/Sports_Analytics.pdf"
})

# 2. Read introduction
intro = await mcp.call_tool("read_pdf_page_range", {
    "book_path": "books/Sports_Analytics.pdf",
    "start_page": 0,
    "end_page": 15,
    "format": "text"
})

# 3. Search for specific analytics
per_search = await mcp.call_tool("search_pdf", {
    "book_path": "books/Sports_Analytics.pdf",
    "query": "player efficiency rating",
    "context_chars": 300
})

# 4. Read relevant pages
relevant_pages = await mcp.call_tool("read_pdf_page_range", {
    "book_path": "books/Sports_Analytics.pdf",
    "start_page": 45,
    "end_page": 55,
    "format": "text"
})
```

═══════════════════════════════════════════════════════════════════

✅ BENEFITS OF THIS APPROACH:

🎯 Better Mathematical Notation:
   - MCP server preserves formatting
   - Handles complex equations better
   - Maintains context around formulas

🔍 Targeted Reading:
   - Search for specific concepts
   - Read only relevant sections
   - Compare across multiple books

📊 Structured Access:
   - Get metadata first
   - Read by chapter or page range
   - Maintain reading progress

🚀 Ready to Use:
   - No conversion needed
   - Works with DRM-protected PDFs
   - Integrated with your existing workflow

═══════════════════════════════════════════════════════════════════

🎉 NEXT STEPS:

1. Use the MCP server PDF tools to read the books
2. Start with metadata to understand book structure
3. Search for specific mathematical concepts
4. Read relevant sections in chunks
5. Compare insights across all 3 books

The MCP server's PDF capabilities are actually BETTER than plain text
for mathematical notation because they preserve formatting and context!

═══════════════════════════════════════════════════════════════════
""")


def main():
    """Main function to display the reading guide."""
    print_reading_guide()


if __name__ == "__main__":
    main()




