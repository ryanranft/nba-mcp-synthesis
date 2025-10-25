#!/usr/bin/env python3
"""
Test EPUB and PDF Features

Tests EPUB and PDF processing tools for metadata extraction,
TOC parsing, chapter extraction, and search.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_dir():
    """Path to sample books directory"""
    return Path(__file__).parent.parent.parent / "sample_books"


@pytest.fixture
def sample_epub(sample_dir):
    """Find a sample EPUB file"""
    if not sample_dir.exists():
        pytest.skip("sample_books directory not found")

    epub_files = list(sample_dir.glob("*.epub"))
    if not epub_files:
        pytest.skip("No EPUB sample files found in sample_books/")

    return str(epub_files[0])


@pytest.fixture
def sample_pdf(sample_dir):
    """Find a sample PDF file"""
    if not sample_dir.exists():
        pytest.skip("sample_books directory not found")

    pdf_files = list(sample_dir.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("No PDF sample files found in sample_books/")

    return str(pdf_files[0])


# EPUB Tests


@pytest.mark.integration
def test_epub_dependencies():
    """Test that EPUB dependencies are available"""
    try:
        from mcp_server.tools import epub_helper

        epub_helper.check_dependencies()
    except ImportError as e:
        pytest.skip(f"EPUB dependencies not available: {e}")


@pytest.mark.integration
def test_epub_metadata(sample_epub):
    """Test EPUB metadata extraction"""
    try:
        from mcp_server.tools import epub_helper
    except ImportError:
        pytest.skip("epub_helper not available")

    metadata = epub_helper.get_metadata(sample_epub)

    assert isinstance(metadata, dict), "Metadata should be a dictionary"
    assert (
        "title" in metadata or "creator" in metadata
    ), "Metadata should contain at least title or creator"


@pytest.mark.integration
def test_epub_toc(sample_epub):
    """Test EPUB table of contents extraction"""
    try:
        from mcp_server.tools import epub_helper
    except ImportError:
        pytest.skip("epub_helper not available")

    toc = epub_helper.get_toc(sample_epub)

    assert isinstance(toc, list), "TOC should be a list"
    # TOC may be empty for some EPUBs, so just check structure
    for item in toc:
        assert len(item) == 2, "Each TOC entry should have (title, href)"


@pytest.mark.integration
def test_epub_chapter_extraction(sample_epub):
    """Test EPUB chapter content extraction"""
    try:
        from mcp_server.tools import epub_helper
    except ImportError:
        pytest.skip("epub_helper not available")

    # Get TOC to find first chapter
    toc = epub_helper.get_toc(sample_epub)

    if not toc:
        pytest.skip("No chapters found in TOC")

    # Get first chapter
    first_chapter_title, first_chapter_href = toc[0]

    # Open EPUB
    book = epub_helper.read_epub(sample_epub)

    # Test different formats
    html_content = epub_helper.extract_chapter_html(book, first_chapter_href)
    assert isinstance(html_content, str), "HTML content should be a string"
    assert len(html_content) > 0, "HTML content should not be empty"

    markdown_content = epub_helper.extract_chapter_markdown(book, first_chapter_href)
    assert isinstance(markdown_content, str), "Markdown content should be a string"

    text_content = epub_helper.extract_chapter_plain_text(book, first_chapter_href)
    assert isinstance(text_content, str), "Plain text content should be a string"


# PDF Tests


@pytest.mark.integration
def test_pdf_dependencies():
    """Test that PDF dependencies are available"""
    try:
        from mcp_server.tools import pdf_helper

        pdf_helper.check_dependencies()
    except ImportError as e:
        pytest.skip(f"PDF dependencies not available: {e}")


@pytest.mark.integration
def test_pdf_metadata(sample_pdf):
    """Test PDF metadata extraction"""
    try:
        from mcp_server.tools import pdf_helper
    except ImportError:
        pytest.skip("pdf_helper not available")

    metadata = pdf_helper.get_metadata(sample_pdf)

    assert isinstance(metadata, dict), "Metadata should be a dictionary"
    assert "page_count" in metadata, "Metadata should contain page_count"
    assert metadata["page_count"] > 0, "PDF should have at least one page"


@pytest.mark.integration
def test_pdf_toc(sample_pdf):
    """Test PDF table of contents extraction"""
    try:
        from mcp_server.tools import pdf_helper
    except ImportError:
        pytest.skip("pdf_helper not available")

    toc = pdf_helper.get_toc(sample_pdf)

    # TOC may be None or empty for PDFs without TOC
    if toc:
        assert isinstance(toc, list), "TOC should be a list"
        for entry in toc:
            assert len(entry) == 3, "Each TOC entry should have (level, title, page)"


@pytest.mark.integration
def test_pdf_page_extraction(sample_pdf):
    """Test PDF page content extraction"""
    try:
        from mcp_server.tools import pdf_helper
    except ImportError:
        pytest.skip("pdf_helper not available")

    # Test different formats for first page
    text_content = pdf_helper.extract_page_text(sample_pdf, 0)
    assert isinstance(text_content, str), "Text content should be a string"
    assert len(text_content) > 0, "Text content should not be empty"

    html_content = pdf_helper.extract_page_html(sample_pdf, 0)
    assert isinstance(html_content, str), "HTML content should be a string"

    markdown_content = pdf_helper.extract_page_markdown(sample_pdf, 0)
    assert isinstance(markdown_content, str), "Markdown content should be a string"


@pytest.mark.integration
def test_pdf_page_range(sample_pdf):
    """Test PDF page range extraction"""
    try:
        from mcp_server.tools import pdf_helper
    except ImportError:
        pytest.skip("pdf_helper not available")

    # Get metadata to check page count
    metadata = pdf_helper.get_metadata(sample_pdf)
    page_count = metadata.get("page_count", 0)

    if page_count < 3:
        pytest.skip("PDF has fewer than 3 pages")

    # Extract first 3 pages
    content = pdf_helper.extract_page_range(sample_pdf, 0, 2, "text")

    assert isinstance(content, str), "Content should be a string"
    assert len(content) > 0, "Content should not be empty"


@pytest.mark.integration
def test_pdf_search(sample_pdf):
    """Test text search in PDF"""
    try:
        from mcp_server.tools import pdf_helper
    except ImportError:
        pytest.skip("pdf_helper not available")

    # Search for common word "the"
    results = pdf_helper.search_text_in_pdf(sample_pdf, "the", context_chars=50)

    assert isinstance(results, list), "Search results should be a list"

    # If results found, check structure
    if results:
        for result in results:
            assert "page" in result, "Result should have 'page' field"
            assert "context" in result, "Result should have 'context' field"
            assert isinstance(result["page"], int), "Page should be an integer"
            assert isinstance(result["context"], str), "Context should be a string"
