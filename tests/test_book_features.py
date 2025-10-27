#!/usr/bin/env python3
"""
Test NBA MCP Server book integration features.

Tests:
1. Book listing with math detection
2. Book reading with chunking and LaTeX preservation
3. Book searching across library
4. Book resource access
5. Chunking edge cases

Requirements:
- Books uploaded to S3 under books/ prefix
- NBA MCP Server running with S3 connector configured
"""

import pytest
import pytest_asyncio
import json
from mcp_server.fastmcp_lifespan import nba_lifespan
from mcp_server.fastmcp_server import (
    list_books,
    read_book,
    search_books,
    get_book_metadata,
    get_book_chunk,
    detect_math_content,
)
from mcp_server.tools.params import ListBooksParams, ReadBookParams, SearchBooksParams


class MockContext:
    """Mock FastMCP context for testing."""

    def __init__(self, lifespan_context):
        self.request_context = type(
            "obj", (object,), {"lifespan_context": lifespan_context}
        )()

    async def info(self, msg):
        pass

    async def debug(self, msg):
        pass

    async def error(self, msg):
        pass

    async def report_progress(self, current, total, message):
        pass


@pytest_asyncio.fixture
async def nba_context():
    """Fixture to provide NBA lifespan context."""

    class MockApp:
        pass

    async with nba_lifespan(MockApp()) as lifespan_context:
        ctx = MockContext(lifespan_context)
        yield ctx


@pytest.mark.asyncio
async def test_math_detection_latex():
    """Test math content detection with LaTeX formulas."""
    text = """
    The standard deviation is calculated as:
    $$\\sigma = \\sqrt{\\frac{\\sum_{i=1}^{n}(x_i - \\mu)^2}{n}}$$
    Where $\\mu$ is the mean value.
    """
    result = detect_math_content(text)

    assert result["has_math"] is True, "Should detect LaTeX formulas"
    assert result["latex_formulas"] == 3, "Should find 3 LaTeX formulas"
    assert result["difficulty_score"] > 0, "Should have non-zero difficulty"
    assert result["recommended_mcp"] == "math-mcp", "Should recommend math-mcp"


@pytest.mark.asyncio
async def test_math_detection_plain_text():
    """Test math content detection with plain text."""
    text = "This is a simple introduction to NBA analytics without any math."
    result = detect_math_content(text)

    assert result["has_math"] is False, "Should not detect math in plain text"
    assert result["recommended_mcp"] is None, "Should not recommend any MCP"


@pytest.mark.asyncio
async def test_math_detection_unicode_symbols():
    """Test math content detection with Unicode math symbols."""
    text = "The sum ∑ of values where α > β and σ ≠ 0"
    result = detect_math_content(text)

    assert result["has_math"] is True, "Should detect Unicode math symbols"
    assert result["math_symbols"] == 5, "Should find 5 math symbols"


@pytest.mark.asyncio
async def test_list_books(nba_context):
    """Test book listing with math detection."""
    params = ListBooksParams(prefix="books/", max_keys=10)
    result = await list_books(params, nba_context)

    assert result.success is True, f"Should succeed: {result.error}"
    assert result.count > 0, "Should find at least one book"
    assert isinstance(result.books, list), "Should return list of books"

    # Check book structure
    if result.books:
        book = result.books[0]
        assert "path" in book, "Book should have path"
        assert "size" in book, "Book should have size"
        assert "format" in book, "Book should have format"
        assert "has_math" in book, "Book should have math detection"


@pytest.mark.asyncio
async def test_read_book(nba_context):
    """Test book reading with chunking."""
    # First get a book path
    list_params = ListBooksParams(prefix="books/", max_keys=1)
    list_result = await list_books(list_params, nba_context)

    if not list_result.success or not list_result.books:
        pytest.skip("No books available for testing")

    book_path = list_result.books[0]["path"]

    # Read first chunk
    params = ReadBookParams(book_path=book_path, chunk_size=50000, chunk_number=0)
    result = await read_book(params, nba_context)

    assert result.success is True, f"Should successfully read book: {result.error}"
    assert result.chunk_number == 0, "Should return first chunk"
    assert result.total_chunks > 0, "Should have at least one chunk"
    assert len(result.content) > 0, "Should have content"
    assert result.metadata is not None, "Should have metadata"
    assert "total_size" in result.metadata, "Metadata should have total_size"
    assert "format" in result.metadata, "Metadata should have format"


@pytest.mark.asyncio
async def test_search_books(nba_context):
    """Test book searching across library."""
    params = SearchBooksParams(query="basketball", book_prefix="books/", max_results=5)
    result = await search_books(params, nba_context)

    assert result.success is True, f"Search should succeed: {result.error}"
    # Note: results may be empty if no matches found, which is acceptable
    if result.results:
        match = result.results[0]
        assert "book_path" in match, "Match should have book_path"
        assert "match_count" in match, "Match should have match_count"
        assert "excerpt" in match, "Match should have excerpt"


@pytest.mark.asyncio
async def test_book_metadata_resource(nba_context):
    """Test book metadata resource access."""
    # Get a book path
    list_params = ListBooksParams(prefix="books/", max_keys=1)
    list_result = await list_books(list_params, nba_context)

    if not list_result.success or not list_result.books:
        pytest.skip("No books available for testing")

    book_path = list_result.books[0]["path"]

    # Test metadata resource
    metadata = await get_book_metadata(book_path, nba_context)
    metadata_dict = json.loads(metadata)

    assert "size" in metadata_dict, "Metadata should have size"
    assert "total_chunks" in metadata_dict, "Metadata should have total_chunks"
    assert "has_math" in metadata_dict, "Metadata should have has_math"
    assert metadata_dict["total_chunks"] > 0, "Should have at least one chunk"


@pytest.mark.asyncio
async def test_book_chunk_resource(nba_context):
    """Test book chunk resource access."""
    # Get a book path
    list_params = ListBooksParams(prefix="books/", max_keys=1)
    list_result = await list_books(list_params, nba_context)

    if not list_result.success or not list_result.books:
        pytest.skip("No books available for testing")

    book_path = list_result.books[0]["path"]

    # Test chunk resource
    chunk_content = await get_book_chunk(book_path, 0, nba_context)

    assert isinstance(chunk_content, str), "Chunk should be string"
    assert len(chunk_content) > 0, "Chunk should have content"


@pytest.mark.asyncio
async def test_invalid_chunk_number(nba_context):
    """Test that invalid chunk numbers are rejected."""
    # Get a book path
    list_params = ListBooksParams(prefix="books/", max_keys=1)
    list_result = await list_books(list_params, nba_context)

    if not list_result.success or not list_result.books:
        pytest.skip("No books available for testing")

    book_path = list_result.books[0]["path"]

    # Try to read chunk 999 (should fail)
    params = ReadBookParams(book_path=book_path, chunk_size=50000, chunk_number=999)
    result = await read_book(params, nba_context)

    assert result.success is False, "Should reject invalid chunk number"
    assert "out of range" in result.error.lower(), "Error should mention out of range"


@pytest.mark.asyncio
async def test_different_chunk_sizes(nba_context):
    """Test reading with different chunk sizes."""
    # Get a book path
    list_params = ListBooksParams(prefix="books/", max_keys=1)
    list_result = await list_books(list_params, nba_context)

    if not list_result.success or not list_result.books:
        pytest.skip("No books available for testing")

    book_path = list_result.books[0]["path"]

    # Test different chunk sizes
    chunk_sizes = [10000, 50000, 100000, 200000]
    prev_chunks = None

    for size in chunk_sizes:
        params = ReadBookParams(book_path=book_path, chunk_size=size, chunk_number=0)
        result = await read_book(params, nba_context)

        assert result.success is True, f"Should succeed with chunk size {size}"
        assert result.total_chunks > 0, f"Should have chunks with size {size}"

        # Larger chunk sizes should result in fewer chunks (or equal for small books)
        if prev_chunks is not None:
            assert (
                result.total_chunks <= prev_chunks
            ), f"Larger chunks ({size}) should not increase chunk count"

        prev_chunks = result.total_chunks
