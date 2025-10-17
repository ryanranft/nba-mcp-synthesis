#!/usr/bin/env python3
"""
Test Script for EPUB and PDF Features

Tests the new EPUB and PDF processing tools added to the NBA MCP server.
Validates metadata extraction, TOC parsing, chapter extraction, and search.

Usage:
    python scripts/test_epub_pdf_features.py
    python scripts/test_epub_pdf_features.py --demo  # Interactive demo
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.tools import epub_helper, pdf_helper
from mcp_server.tools.logger_config import get_logger

# Initialize logger
logger = get_logger(__name__)


class TestColors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message: str):
    """Print a styled header"""
    print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'=' * 70}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{message}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{'=' * 70}{TestColors.ENDC}\n")


def print_success(message: str):
    """Print a success message"""
    print(f"{TestColors.OKGREEN}✓ {message}{TestColors.ENDC}")


def print_error(message: str):
    """Print an error message"""
    print(f"{TestColors.FAIL}✗ {message}{TestColors.ENDC}")


def print_info(message: str):
    """Print an info message"""
    print(f"{TestColors.OKCYAN}ℹ {message}{TestColors.ENDC}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{TestColors.WARNING}⚠ {message}{TestColors.ENDC}")


# =============================================================================
# EPUB Tests
# =============================================================================


async def test_epub_dependencies():
    """Test 1: Check EPUB dependencies"""
    print_header("Test 1: EPUB Dependencies Check")

    try:
        epub_helper.check_dependencies()
        print_success(
            "All EPUB dependencies available (ebooklib, beautifulsoup4, html2text)"
        )
        return True
    except ImportError as e:
        print_error(f"Missing dependencies: {e}")
        print_info("Install with: pip install ebooklib beautifulsoup4 html2text")
        return False


async def test_epub_metadata(epub_path: str):
    """Test 2: Extract EPUB metadata"""
    print_header("Test 2: EPUB Metadata Extraction")

    if not os.path.exists(epub_path):
        print_warning(f"EPUB file not found: {epub_path}")
        print_info("Skipping EPUB metadata test")
        return False

    try:
        metadata = epub_helper.get_metadata(epub_path)

        print_success("Metadata extracted successfully")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(
            f"  Author(s): {', '.join(metadata.get('creator', [])) if metadata.get('creator') else 'N/A'}"
        )
        print(f"  Publisher: {metadata.get('publisher', 'N/A')}")
        print(f"  Language: {metadata.get('language', 'N/A')}")
        print(f"  Date: {metadata.get('date', 'N/A')}")

        if metadata.get("subject"):
            print(f"  Subjects: {', '.join(metadata.get('subject', []))}")

        return True
    except Exception as e:
        print_error(f"Failed to extract metadata: {e}")
        return False


async def test_epub_toc(epub_path: str):
    """Test 3: Extract EPUB table of contents"""
    print_header("Test 3: EPUB Table of Contents")

    if not os.path.exists(epub_path):
        print_warning(f"EPUB file not found: {epub_path}")
        print_info("Skipping EPUB TOC test")
        return False

    try:
        toc = epub_helper.get_toc(epub_path)

        print_success(f"TOC extracted: {len(toc)} chapters")

        # Show first 5 chapters
        for i, (title, href) in enumerate(toc[:5]):
            print(f"  {i+1}. {title}")
            print(f"     → {href}")

        if len(toc) > 5:
            print(f"  ... and {len(toc) - 5} more chapters")

        return True
    except Exception as e:
        print_error(f"Failed to extract TOC: {e}")
        return False


async def test_epub_chapter_extraction(epub_path: str):
    """Test 4: Extract EPUB chapter content"""
    print_header("Test 4: EPUB Chapter Extraction")

    if not os.path.exists(epub_path):
        print_warning(f"EPUB file not found: {epub_path}")
        print_info("Skipping EPUB chapter test")
        return False

    try:
        # Get TOC to find first chapter
        toc = epub_helper.get_toc(epub_path)

        if not toc:
            print_warning("No chapters found in TOC")
            return False

        # Get first chapter
        first_chapter_title, first_chapter_href = toc[0]

        print_info(f"Extracting first chapter: {first_chapter_title}")

        # Open EPUB
        book = epub_helper.read_epub(epub_path)

        # Test different formats
        formats = {
            "html": epub_helper.extract_chapter_html,
            "markdown": epub_helper.extract_chapter_markdown,
            "text": epub_helper.extract_chapter_plain_text,
        }

        for format_name, extract_func in formats.items():
            content = extract_func(book, first_chapter_href)
            print_success(f"{format_name.upper()}: {len(content)} characters")

            # Show preview (first 200 chars)
            preview = content[:200].replace("\n", " ")
            print(f"  Preview: {preview}...")

        return True
    except Exception as e:
        print_error(f"Failed to extract chapter: {e}")
        return False


# =============================================================================
# PDF Tests
# =============================================================================


async def test_pdf_dependencies():
    """Test 5: Check PDF dependencies"""
    print_header("Test 5: PDF Dependencies Check")

    try:
        pdf_helper.check_dependencies()
        print_success(
            "All PDF dependencies available (PyMuPDF, beautifulsoup4, html2text)"
        )
        return True
    except ImportError as e:
        print_error(f"Missing dependencies: {e}")
        print_info("Install with: pip install PyMuPDF beautifulsoup4 html2text")
        return False


async def test_pdf_metadata(pdf_path: str):
    """Test 6: Extract PDF metadata"""
    print_header("Test 6: PDF Metadata Extraction")

    if not os.path.exists(pdf_path):
        print_warning(f"PDF file not found: {pdf_path}")
        print_info("Skipping PDF metadata test")
        return False

    try:
        metadata = pdf_helper.get_metadata(pdf_path)

        print_success("Metadata extracted successfully")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Author: {metadata.get('author', 'N/A')}")
        print(f"  Creator: {metadata.get('creator', 'N/A')}")
        print(f"  Producer: {metadata.get('producer', 'N/A')}")
        print(f"  Pages: {metadata.get('page_count', 0)}")
        print(f"  Has TOC: {'Yes' if metadata.get('has_toc') else 'No'}")

        if metadata.get("has_toc"):
            print(f"  TOC Entries: {metadata.get('toc_entries', 0)}")

        return True
    except Exception as e:
        print_error(f"Failed to extract metadata: {e}")
        return False


async def test_pdf_toc(pdf_path: str):
    """Test 7: Extract PDF table of contents"""
    print_header("Test 7: PDF Table of Contents")

    if not os.path.exists(pdf_path):
        print_warning(f"PDF file not found: {pdf_path}")
        print_info("Skipping PDF TOC test")
        return False

    try:
        toc = pdf_helper.get_toc(pdf_path)

        if not toc:
            print_warning("No TOC found in PDF")
            return True  # Not an error, just no TOC

        print_success(f"TOC extracted: {len(toc)} entries")

        # Show first 5 entries
        for level, title, page in toc[:5]:
            indent = "  " * level
            print(f"  {indent}{title} (page {page})")

        if len(toc) > 5:
            print(f"  ... and {len(toc) - 5} more entries")

        return True
    except Exception as e:
        print_error(f"Failed to extract TOC: {e}")
        return False


async def test_pdf_page_extraction(pdf_path: str):
    """Test 8: Extract PDF page content"""
    print_header("Test 8: PDF Page Extraction")

    if not os.path.exists(pdf_path):
        print_warning(f"PDF file not found: {pdf_path}")
        print_info("Skipping PDF page test")
        return False

    try:
        # Test different formats for first page
        formats = {
            "text": pdf_helper.extract_page_text,
            "html": pdf_helper.extract_page_html,
            "markdown": pdf_helper.extract_page_markdown,
        }

        print_info("Extracting first page (page 0)")

        for format_name, extract_func in formats.items():
            content = extract_func(pdf_path, 0)
            print_success(f"{format_name.upper()}: {len(content)} characters")

            # Show preview (first 200 chars)
            preview = content[:200].replace("\n", " ")
            print(f"  Preview: {preview}...")

        return True
    except Exception as e:
        print_error(f"Failed to extract page: {e}")
        return False


async def test_pdf_page_range(pdf_path: str):
    """Test 9: Extract PDF page range"""
    print_header("Test 9: PDF Page Range Extraction")

    if not os.path.exists(pdf_path):
        print_warning(f"PDF file not found: {pdf_path}")
        print_info("Skipping PDF page range test")
        return False

    try:
        print_info("Extracting pages 0-2")

        content = pdf_helper.extract_page_range(pdf_path, 0, 2, "text")
        print_success(f"Extracted 3 pages: {len(content)} characters")

        # Test page break detection
        if "---" in content or "\n\n\n" in content:
            print_info("Page breaks detected in content")

        return True
    except Exception as e:
        print_error(f"Failed to extract page range: {e}")
        return False


async def test_pdf_search(pdf_path: str, query: str = "the"):
    """Test 10: Search text in PDF"""
    print_header("Test 10: PDF Text Search")

    if not os.path.exists(pdf_path):
        print_warning(f"PDF file not found: {pdf_path}")
        print_info("Skipping PDF search test")
        return False

    try:
        print_info(f"Searching for: '{query}'")

        results = pdf_helper.search_text_in_pdf(pdf_path, query, context_chars=50)

        print_success(f"Found {len(results)} matches")

        # Show first 3 matches
        for i, result in enumerate(results[:3]):
            page = result["page"]
            context = result["context"].replace("\n", " ")
            print(f"  Match {i+1} (page {page}): ...{context}...")

        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more matches")

        return True
    except Exception as e:
        print_error(f"Failed to search PDF: {e}")
        return False


# =============================================================================
# Main Test Runner
# =============================================================================


async def run_all_tests():
    """Run all EPUB and PDF tests"""
    print_header("EPUB & PDF Features Test Suite")
    print(f"Testing EPUB and PDF processing capabilities\n")

    # Find sample files
    sample_dir = Path(__file__).parent.parent / "sample_books"
    epub_path = None
    pdf_path = None

    # Look for sample files
    if sample_dir.exists():
        epub_files = list(sample_dir.glob("*.epub"))
        pdf_files = list(sample_dir.glob("*.pdf"))

        if epub_files:
            epub_path = str(epub_files[0])
            print_info(f"Using EPUB sample: {epub_path}")

        if pdf_files:
            pdf_path = str(pdf_files[0])
            print_info(f"Using PDF sample: {pdf_path}")

    if not epub_path:
        print_warning("No EPUB sample file found in sample_books/")
        print_info("Please add a .epub file to sample_books/ directory for testing")

    if not pdf_path:
        print_warning("No PDF sample file found in sample_books/")
        print_info("Please add a .pdf file to sample_books/ directory for testing")

    print()

    # Run tests
    results = []

    # EPUB Tests
    results.append(await test_epub_dependencies())
    if epub_path:
        results.append(await test_epub_metadata(epub_path))
        results.append(await test_epub_toc(epub_path))
        results.append(await test_epub_chapter_extraction(epub_path))
    else:
        print_warning("Skipping EPUB tests (no sample file)")
        results.extend([None, None, None])

    # PDF Tests
    results.append(await test_pdf_dependencies())
    if pdf_path:
        results.append(await test_pdf_metadata(pdf_path))
        results.append(await test_pdf_toc(pdf_path))
        results.append(await test_pdf_page_extraction(pdf_path))
        results.append(await test_pdf_page_range(pdf_path))
        results.append(await test_pdf_search(pdf_path))
    else:
        print_warning("Skipping PDF tests (no sample file)")
        results.extend([None, None, None, None, None])

    # Summary
    print_header("Test Summary")

    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    total = len(results)

    print(f"Total Tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    if skipped > 0:
        print_warning(f"Skipped: {skipped}")

    pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")

    return passed, failed, skipped


async def interactive_demo():
    """Interactive demo mode"""
    print_header("EPUB & PDF Interactive Demo")
    print("This demo will help you test EPUB and PDF processing interactively.\n")

    while True:
        print("\nOptions:")
        print("  1. Test EPUB file")
        print("  2. Test PDF file")
        print("  3. Run all tests")
        print("  4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            epub_path = input("Enter path to EPUB file: ").strip()
            if os.path.exists(epub_path):
                await test_epub_metadata(epub_path)
                await test_epub_toc(epub_path)
                await test_epub_chapter_extraction(epub_path)
            else:
                print_error(f"File not found: {epub_path}")

        elif choice == "2":
            pdf_path = input("Enter path to PDF file: ").strip()
            if os.path.exists(pdf_path):
                await test_pdf_metadata(pdf_path)
                await test_pdf_toc(pdf_path)
                await test_pdf_page_extraction(pdf_path)

                search_query = input(
                    "Enter search query (or press Enter to skip): "
                ).strip()
                if search_query:
                    await test_pdf_search(pdf_path, search_query)
            else:
                print_error(f"File not found: {pdf_path}")

        elif choice == "3":
            await run_all_tests()

        elif choice == "4":
            print("\nExiting demo. Goodbye!")
            break

        else:
            print_error("Invalid choice. Please enter 1-4.")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test EPUB and PDF features")
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    args = parser.parse_args()

    if args.demo:
        asyncio.run(interactive_demo())
    else:
        asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
