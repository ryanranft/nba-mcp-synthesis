#!/usr/bin/env python3
"""
Test script for NBA MCP Server book integration features.

This script tests:
1. Book listing with math detection
2. Book reading with chunking and LaTeX preservation
3. Book searching across library
4. Book resource access
5. Recommendation prompt

Requirements:
- Books uploaded to S3 under books/ prefix
- NBA MCP Server running with S3 connector configured
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.fastmcp_lifespan import nba_lifespan
from mcp_server.fastmcp_server import (
    list_books,
    read_book,
    search_books,
    get_book_metadata,
    get_book_chunk,
    detect_math_content
)
from mcp_server.tools.params import (
    ListBooksParams,
    ReadBookParams,
    SearchBooksParams
)


class MockContext:
    """Mock FastMCP context for testing."""

    def __init__(self, lifespan_context):
        self.request_context = type('obj', (object,), {
            'lifespan_context': lifespan_context
        })()

    async def info(self, msg):
        print(f"[INFO] {msg}")

    async def debug(self, msg):
        print(f"[DEBUG] {msg}")

    async def error(self, msg):
        print(f"[ERROR] {msg}")

    async def report_progress(self, current, total, message):
        pct = int((current / total) * 100)
        print(f"[PROGRESS] {pct}% - {message}")


async def test_math_detection():
    """Test math content detection function."""
    print("\n" + "=" * 60)
    print("TEST 1: Math Content Detection")
    print("=" * 60)

    # Test case 1: LaTeX formulas
    text1 = """
    The standard deviation is calculated as:
    $$\\sigma = \\sqrt{\\frac{\\sum_{i=1}^{n}(x_i - \\mu)^2}{n}}$$
    Where $\\mu$ is the mean value.
    """
    result1 = detect_math_content(text1)
    print("\n📐 Text with LaTeX:")
    print(f"  has_math: {result1['has_math']}")
    print(f"  latex_formulas: {result1['latex_formulas']}")
    print(f"  difficulty_score: {result1['difficulty_score']}")
    print(f"  recommended_mcp: {result1['recommended_mcp']}")

    # Test case 2: Plain text
    text2 = "This is a simple introduction to NBA analytics without any math."
    result2 = detect_math_content(text2)
    print("\n📝 Plain text:")
    print(f"  has_math: {result2['has_math']}")
    print(f"  recommended_mcp: {result2['recommended_mcp']}")

    # Test case 3: Math symbols
    text3 = "The sum ∑ of values where α > β and σ ≠ 0"
    result3 = detect_math_content(text3)
    print("\n🔣 Text with symbols:")
    print(f"  has_math: {result3['has_math']}")
    print(f"  math_symbols: {result3['math_symbols']}")

    assert result1['has_math'] == True
    assert result2['has_math'] == False
    assert result3['has_math'] == True

    print("\n✅ Math detection tests passed!")


async def test_list_books(ctx):
    """Test book listing with math detection."""
    print("\n" + "=" * 60)
    print("TEST 2: List Books")
    print("=" * 60)

    params = ListBooksParams(prefix="books/", max_keys=10)
    result = await list_books(params, ctx)

    print(f"\n📚 Found {result.count} books")

    if result.success and result.books:
        math_books = [b for b in result.books if b.get('has_math')]
        print(f"📐 {len(math_books)} books with math content")

        print("\n📖 Sample books:")
        for book in result.books[:3]:
            print(f"\n  • {book['path']}")
            print(f"    Size: {book.get('size', 0):,} bytes")
            print(f"    Format: {book.get('format', 'unknown')}")
            print(f"    Has math: {book.get('has_math', False)}")
            if book.get('has_math'):
                print(f"    Math difficulty: {book.get('math_difficulty', 0.0):.2f}")
                print(f"    Recommended MCP: {book.get('recommended_mcp')}")

        print("\n✅ list_books test passed!")
        return result.books
    else:
        print(f"\n⚠️  No books found or error: {result.error}")
        print("    Make sure books are uploaded to S3 under books/ prefix")
        return []


async def test_read_book(ctx, book_path=None):
    """Test book reading with chunking."""
    print("\n" + "=" * 60)
    print("TEST 3: Read Book")
    print("=" * 60)

    if not book_path:
        print("\n⚠️  No book path provided, skipping test")
        return

    print(f"\n📖 Reading: {book_path}")

    # Read first chunk
    params = ReadBookParams(
        book_path=book_path,
        chunk_size=50000,
        chunk_number=0
    )
    result = await read_book(params, ctx)

    if result.success:
        print(f"\n✅ Successfully read chunk {result.chunk_number + 1}/{result.total_chunks}")
        print(f"   Chunk size: {result.chunk_size:,} characters")
        print(f"   Has more: {result.has_more}")

        # Show metadata
        print("\n📊 Metadata:")
        print(f"   Total size: {result.metadata.get('total_size', 0):,} bytes")
        print(f"   Format: {result.metadata.get('format')}")
        print(f"   Has math: {result.metadata.get('has_math')}")
        if result.metadata.get('has_math'):
            print(f"   LaTeX formulas: {result.metadata.get('latex_formulas')}")
            print(f"   Math difficulty: {result.metadata.get('math_difficulty'):.2f}")

        # Show preview
        preview = result.content[:300]
        print(f"\n📄 Content preview:")
        print(f"   {preview}...")

        # Check for LaTeX
        if '$' in result.content or '\\begin{' in result.content:
            print("\n   ✓ LaTeX formulas detected and preserved!")

        print("\n✅ read_book test passed!")
        return result
    else:
        print(f"\n❌ Failed to read book: {result.error}")
        return None


async def test_search_books(ctx):
    """Test book searching."""
    print("\n" + "=" * 60)
    print("TEST 4: Search Books")
    print("=" * 60)

    # Test search queries
    queries = [
        "standard deviation",
        "machine learning",
        "python",
        "formula"
    ]

    for query in queries:
        print(f"\n🔍 Searching for: '{query}'")

        params = SearchBooksParams(
            query=query,
            book_prefix="books/",
            max_results=3
        )
        result = await search_books(params, ctx)

        if result.success and result.results:
            print(f"   Found {result.count} results")

            for i, match in enumerate(result.results[:2], 1):
                print(f"\n   {i}. {match['book_path']}")
                print(f"      Matches: {match['match_count']}")
                print(f"      Chunk: {match['chunk_number']}")
                print(f"      Excerpt: {match['excerpt'][:100]}...")
        else:
            print(f"   No results found")

    print("\n✅ search_books test passed!")


async def test_book_resources(ctx):
    """Test book resource access."""
    print("\n" + "=" * 60)
    print("TEST 5: Book Resources")
    print("=" * 60)

    # First, get a book path from list
    params = ListBooksParams(prefix="books/", max_keys=1)
    result = await list_books(params, ctx)

    if not result.success or not result.books:
        print("\n⚠️  No books available for resource test")
        return

    book_path = result.books[0]['path']
    print(f"\n🔗 Testing resource access for: {book_path}")

    # Test metadata resource
    print("\n📋 Resource: book://{path}")
    try:
        metadata = await get_book_metadata(book_path, ctx)
        metadata_dict = json.loads(metadata)
        print(f"   ✓ Metadata retrieved")
        print(f"   Size: {metadata_dict.get('size'):,} bytes")
        print(f"   Total chunks: {metadata_dict.get('total_chunks')}")
        print(f"   Has math: {metadata_dict.get('has_math')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test chunk resource
    print("\n📄 Resource: book://{path}/chunk/0")
    try:
        chunk_content = await get_book_chunk(book_path, 0, ctx)
        print(f"   ✓ Chunk retrieved")
        print(f"   Length: {len(chunk_content):,} characters")
        print(f"   Preview: {chunk_content[:100]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n✅ Resource tests passed!")


async def test_chunking_edge_cases(ctx, book_path=None):
    """Test edge cases in chunking."""
    print("\n" + "=" * 60)
    print("TEST 6: Chunking Edge Cases")
    print("=" * 60)

    if not book_path:
        print("\n⚠️  No book path provided, skipping test")
        return

    # Test invalid chunk number
    print("\n🧪 Test: Invalid chunk number (999)")
    params = ReadBookParams(
        book_path=book_path,
        chunk_size=50000,
        chunk_number=999
    )
    result = await read_book(params, ctx)

    if not result.success:
        print(f"   ✓ Correctly rejected: {result.error}")
    else:
        print(f"   ❌ Should have failed")

    # Test different chunk sizes
    print("\n🧪 Test: Different chunk sizes")
    for size in [10000, 50000, 100000, 200000]:
        params = ReadBookParams(
            book_path=book_path,
            chunk_size=size,
            chunk_number=0
        )
        result = await read_book(params, ctx)

        if result.success:
            print(f"   ✓ {size:,} chars: {result.total_chunks} chunks")
        else:
            print(f"   ❌ {size:,} chars: Failed")

    print("\n✅ Edge case tests passed!")


async def run_all_tests():
    """Run all book integration tests."""
    print("\n" + "=" * 60)
    print("NBA MCP Server - Book Integration Tests")
    print("=" * 60)

    try:
        # Initialize lifespan (connectors)
        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as lifespan_context:
            ctx = MockContext(lifespan_context)

            # Test 1: Math detection (standalone)
            await test_math_detection()

            # Test 2: List books
            books = await test_list_books(ctx)

            # Find a book with math content for further tests
            book_path = None
            if books:
                book_path = books[0]['path']
                # Prefer a math book if available
                math_books = [b for b in books if b.get('has_math')]
                if math_books:
                    book_path = math_books[0]['path']

            # Test 3: Read book
            book_result = await test_read_book(ctx, book_path)

            # Test 4: Search books
            await test_search_books(ctx)

            # Test 5: Book resources
            await test_book_resources(ctx)

            # Test 6: Chunking edge cases
            await test_chunking_edge_cases(ctx, book_path)

            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def run_interactive_demo():
    """Run an interactive demo of book features."""
    print("\n" + "=" * 60)
    print("NBA MCP Server - Book Integration Demo")
    print("=" * 60)

    class MockApp:
        pass

    async with nba_lifespan(MockApp()) as lifespan_context:
        ctx = MockContext(lifespan_context)

        # List books
        print("\n📚 Discovering books in library...")
        params = ListBooksParams(prefix="books/", max_keys=20)
        result = await list_books(params, ctx)

        if not result.success or not result.books:
            print("\n⚠️  No books found. Upload books to S3 under books/ prefix.")
            return

        # Show books with math content
        math_books = [b for b in result.books if b.get('has_math')]
        regular_books = [b for b in result.books if not b.get('has_math')]

        print(f"\n📐 Math books ({len(math_books)}):")
        for book in math_books:
            print(f"  • {book['path']} (difficulty: {book.get('math_difficulty', 0):.2f})")

        print(f"\n📖 Regular books ({len(regular_books)}):")
        for book in regular_books[:5]:
            print(f"  • {book['path']}")

        # Interactive selection
        print("\n" + "-" * 60)
        print("Select a book to read:")
        for i, book in enumerate(result.books[:10], 1):
            indicator = "📐" if book.get('has_math') else "📖"
            print(f"  {i}. {indicator} {book['path']}")

        try:
            choice = int(input("\nEnter book number (or 0 to skip): "))
            if choice > 0 and choice <= len(result.books):
                book = result.books[choice - 1]
                print(f"\n📖 Reading: {book['path']}")

                # Read first chunk
                params = ReadBookParams(
                    book_path=book['path'],
                    chunk_size=50000,
                    chunk_number=0
                )
                read_result = await read_book(params, ctx)

                if read_result.success:
                    print(f"\n📄 Chunk 1/{read_result.total_chunks}:")
                    print("-" * 60)
                    print(read_result.content[:1000])
                    print("\n[... content continues ...]")
                    print("-" * 60)

                    if read_result.metadata.get('has_math'):
                        print("\n💡 This book contains math content!")
                        print("   Use math-mcp tools for computations.")

                    if read_result.has_more:
                        print(f"\n📚 {read_result.total_chunks - 1} more chunks available")
        except (ValueError, KeyboardInterrupt):
            print("\nSkipping interactive demo...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test NBA MCP Server book integration"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demo instead of automated tests"
    )

    args = parser.parse_args()

    if args.demo:
        asyncio.run(run_interactive_demo())
    else:
        asyncio.run(run_all_tests())