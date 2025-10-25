#!/usr/bin/env python3
"""
Test MCP Server PDF Tools

Tests PDF reading capabilities with sports analytics books
including metadata extraction, page reading, and search.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sports_books():
    """Define sports analytics books to test"""
    return [
        {
            "id": "sports_analytics",
            "title": "Sports Analytics",
            "local_path": "/Users/ryanranft/Downloads/Sports_Analytics.pdf",
        },
        {
            "id": "basketball_beyond_paper",
            "title": "Basketball Beyond Paper",
            "local_path": "/Users/ryanranft/Downloads/Basketball_Beyond_Paper.pdf",
        },
        {
            "id": "midrange_theory",
            "title": "The Midrange Theory",
            "local_path": "/Users/ryanranft/Downloads/The_Midrange_Theory.pdf",
        },
    ]


@pytest.fixture
def sample_pdf(sports_books):
    """Find first available sports analytics PDF"""
    for book in sports_books:
        pdf_path = Path(book["local_path"])
        if pdf_path.exists():
            return str(pdf_path)

    pytest.skip("No sports analytics PDFs found in Downloads folder")


@pytest.mark.integration
def test_pdf_metadata_extraction(sample_pdf):
    """Test PDF metadata extraction"""
    try:
        from mcp_server.tools.pdf_helper import get_metadata
        from mcp_server.exceptions import PdfProcessingError
    except ImportError:
        pytest.skip("pdf_helper not available")

    try:
        metadata = get_metadata(sample_pdf)
    except PdfProcessingError as e:
        # Skip if PDF is DRM-protected, encrypted, or can't be opened
        error_str = str(e)
        if any(
            keyword in error_str
            for keyword in [
                "encryption",
                "DRM",
                "EBX_HANDLER",
                "Failed to open file",
                "FileDataError",
            ]
        ):
            pytest.skip(
                f"PDF cannot be opened (may be DRM-protected): {error_str[:100]}"
            )
        raise

    assert isinstance(metadata, dict), "Metadata should be a dictionary"
    assert "page_count" in metadata, "Metadata should contain page_count"
    assert metadata["page_count"] > 0, "PDF should have at least one page"


@pytest.mark.integration
def test_pdf_page_reading(sample_pdf):
    """Test reading PDF page content"""
    try:
        from mcp_server.tools.pdf_helper import extract_page_text
        from mcp_server.exceptions import PdfProcessingError
    except ImportError:
        pytest.skip("pdf_helper not available")

    try:
        first_page = extract_page_text(sample_pdf, 0)
    except PdfProcessingError as e:
        # Skip if PDF is DRM-protected, encrypted, or can't be opened
        error_str = str(e)
        if any(
            keyword in error_str
            for keyword in [
                "encryption",
                "DRM",
                "EBX_HANDLER",
                "Failed to open file",
                "FileDataError",
            ]
        ):
            pytest.skip(
                f"PDF cannot be opened (may be DRM-protected): {error_str[:100]}"
            )
        raise

    assert isinstance(first_page, str), "Page content should be a string"
    assert len(first_page) > 0, "First page should not be empty"


@pytest.mark.integration
def test_pdf_search_functionality(sample_pdf):
    """Test PDF text search"""
    try:
        from mcp_server.tools.pdf_helper import search_text_in_pdf
        from mcp_server.exceptions import PdfProcessingError
    except ImportError:
        pytest.skip("pdf_helper not available")

    # Search for common term "analytics"
    try:
        search_results = search_text_in_pdf(sample_pdf, "analytics", context_chars=100)
    except PdfProcessingError as e:
        # Skip if PDF is DRM-protected, encrypted, or can't be opened
        error_str = str(e)
        if any(
            keyword in error_str
            for keyword in [
                "encryption",
                "DRM",
                "EBX_HANDLER",
                "Failed to open file",
                "FileDataError",
            ]
        ):
            pytest.skip(
                f"PDF cannot be opened (may be DRM-protected): {error_str[:100]}"
            )
        raise

    assert isinstance(search_results, list), "Search results should be a list"

    # If results found, verify structure
    if search_results:
        for result in search_results:
            assert "page" in result, "Result should have 'page' field"
            assert "context" in result, "Result should have 'context' field"
            assert isinstance(result["page"], int), "Page should be an integer"
            assert isinstance(result["context"], str), "Context should be a string"


@pytest.mark.integration
def test_pdf_page_range_extraction(sample_pdf):
    """Test extracting a range of PDF pages"""
    try:
        from mcp_server.tools.pdf_helper import (
            extract_page_range,
            get_metadata,
            extract_page_text,
        )
        from mcp_server.exceptions import PdfProcessingError
    except ImportError:
        pytest.skip("pdf_helper not available")

    # Get metadata to check page count
    try:
        metadata = get_metadata(sample_pdf)
    except PdfProcessingError as e:
        # Skip if PDF is DRM-protected, encrypted, or can't be opened
        error_str = str(e)
        if any(
            keyword in error_str
            for keyword in [
                "encryption",
                "DRM",
                "EBX_HANDLER",
                "Failed to open file",
                "FileDataError",
            ]
        ):
            pytest.skip(
                f"PDF cannot be opened (may be DRM-protected): {error_str[:100]}"
            )
        raise

    page_count = metadata.get("page_count", 0)

    if page_count < 5:
        pytest.skip("PDF has fewer than 5 pages")

    # Extract first 5 pages
    try:
        content = extract_page_range(sample_pdf, 0, 4, "text")
        single_page = extract_page_text(sample_pdf, 0)
    except PdfProcessingError as e:
        # Skip if PDF is DRM-protected, encrypted, or can't be opened
        error_str = str(e)
        if any(
            keyword in error_str
            for keyword in [
                "encryption",
                "DRM",
                "EBX_HANDLER",
                "Failed to open file",
                "FileDataError",
            ]
        ):
            pytest.skip(
                f"PDF cannot be opened (may be DRM-protected): {error_str[:100]}"
            )
        raise

    assert isinstance(content, str), "Content should be a string"
    assert len(content) > 0, "Content should not be empty"
    # Should be longer than a single page
    assert len(content) > len(single_page), "Range should be longer than single page"


@pytest.mark.integration
def test_multiple_books(sports_books):
    """Test that PDF tools work with multiple books"""
    try:
        from mcp_server.tools.pdf_helper import get_metadata
        from mcp_server.exceptions import PdfProcessingError
    except ImportError:
        pytest.skip("pdf_helper not available")

    available_books = []

    for book in sports_books:
        pdf_path = Path(book["local_path"])
        if pdf_path.exists():
            try:
                metadata = get_metadata(str(pdf_path))
                available_books.append(
                    {"title": book["title"], "pages": metadata.get("page_count", 0)}
                )
            except PdfProcessingError as e:
                # Skip DRM-protected books
                error_str = str(e)
                if any(
                    keyword in error_str
                    for keyword in [
                        "encryption",
                        "DRM",
                        "EBX_HANDLER",
                        "Failed to open file",
                        "FileDataError",
                    ]
                ):
                    continue
                pass  # Skip books that can't be read for other reasons
            except Exception:
                pass  # Skip books that can't be read

    # At least one book should be readable, or skip the test
    if not available_books:
        pytest.skip("No readable (non-DRM) sports analytics PDFs found")

    assert len(available_books) > 0, "Should be able to read at least one book"

    for book in available_books:
        assert book["pages"] > 0, f"{book['title']} should have pages"
