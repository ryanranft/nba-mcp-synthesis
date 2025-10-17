"""
PDF Processing Helper for NBA MCP Server

Provides PDF file processing capabilities including:
- Metadata extraction
- Table of contents parsing
- Page and chapter extraction
- Markdown conversion with formatting preservation

Based on best practices from ebook-mcp implementation.
"""

import os
from typing import List, Tuple, Dict, Union, Any, Optional
from pathlib import Path

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import html2text

    HTML2TEXT_AVAILABLE = True
except ImportError:
    html2text = None
    HTML2TEXT_AVAILABLE = False

from ..exceptions import PdfProcessingError
from .logger_config import get_logger, log_operation

# Initialize logger
logger = get_logger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    if not PYMUPDF_AVAILABLE:
        missing.append("PyMuPDF")
    if not BEAUTIFULSOUP_AVAILABLE:
        missing.append("beautifulsoup4")
    if not HTML2TEXT_AVAILABLE:
        missing.append("html2text")

    if missing:
        raise ImportError(
            f"Missing required dependencies for PDF processing: {', '.join(missing)}. "
            f"Install with: pip install {' '.join(missing)}"
        )


def get_all_pdf_files(path: str) -> List[str]:
    """
    Get all PDF files in the specified directory.

    Args:
        path: Directory path to search

    Returns:
        List of PDF filenames
    """
    check_dependencies()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")

    return [f for f in os.listdir(path) if f.lower().endswith(".pdf")]


@log_operation("pdf_metadata_extraction")
def get_metadata(pdf_path: str) -> Dict[str, Union[str, int]]:
    """
    Get metadata from a PDF file.

    Extracts standard metadata fields including title, author, subject,
    creator, producer, creation date, modification date, page count, etc.

    Args:
        pdf_path: Absolute path to the PDF file

    Returns:
        Dictionary containing metadata fields

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found",
                file_path=pdf_path,
                operation="metadata_extraction",
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF metadata extraction",
            file_path=pdf_path,
            operation="metadata_extraction",
        )
        doc = fitz.open(pdf_path)
        meta = {}

        # Extract standard metadata
        pdf_meta = doc.metadata
        if pdf_meta:
            meta["title"] = pdf_meta.get("title", "")
            meta["author"] = pdf_meta.get("author", "")
            meta["subject"] = pdf_meta.get("subject", "")
            meta["creator"] = pdf_meta.get("creator", "")
            meta["producer"] = pdf_meta.get("producer", "")
            meta["creation_date"] = pdf_meta.get("creationDate", "")
            meta["modification_date"] = pdf_meta.get("modDate", "")
            meta["keywords"] = pdf_meta.get("keywords", "")

        # Add page count
        meta["page_count"] = doc.page_count

        # Check if PDF has TOC
        toc = doc.get_toc()
        meta["has_toc"] = len(toc) > 0
        meta["toc_entries"] = len(toc)

        doc.close()

        logger.info(
            "PDF metadata extraction completed",
            file_path=pdf_path,
            operation="metadata_extraction",
            page_count=meta["page_count"],
            has_toc=meta["has_toc"],
        )
        return meta

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to parse PDF file",
            file_path=pdf_path,
            operation="metadata_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to parse PDF file", pdf_path, "metadata_extraction", e
        )


@log_operation("pdf_toc_extraction")
def get_toc(pdf_path: str) -> List[Tuple[int, str, int]]:
    """
    Get the Table of Contents (TOC) from a PDF file.

    Args:
        pdf_path: Absolute path to the PDF file

    Returns:
        List of TOC entries, each entry is a tuple of (level, title, page_number)
        - level: Hierarchy level (1 for top-level, 2 for subsection, etc.)
        - title: Chapter/section title
        - page_number: Page number (1-indexed)

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found", file_path=pdf_path, operation="toc_extraction"
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF TOC extraction",
            file_path=pdf_path,
            operation="toc_extraction",
        )
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        doc.close()

        logger.info(
            "PDF TOC extraction completed",
            file_path=pdf_path,
            operation="toc_extraction",
            entry_count=len(toc),
        )
        return toc

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to parse PDF file",
            file_path=pdf_path,
            operation="toc_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to parse PDF file", pdf_path, "toc_extraction", e
        )


@log_operation("pdf_page_extraction")
def extract_page_text(pdf_path: str, page_number: int) -> str:
    """
    Extract text from a specific page.

    Args:
        pdf_path: Absolute path to the PDF file
        page_number: Page number (0-indexed)

    Returns:
        Plain text content of the page

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found", file_path=pdf_path, operation="page_extraction"
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF page extraction",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_extraction",
        )
        doc = fitz.open(pdf_path)

        # Check page number
        if page_number < 0 or page_number >= doc.page_count:
            doc.close()
            raise PdfProcessingError(
                f"Page number {page_number} out of range (0-{doc.page_count-1})",
                pdf_path,
                "page_extraction",
            )

        # Extract text
        page = doc[page_number]
        text = page.get_text()
        doc.close()

        logger.info(
            "PDF page extraction completed",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_extraction",
            text_length=len(text),
        )
        return text

    except FileNotFoundError:
        raise
    except PdfProcessingError:
        raise
    except Exception as e:
        logger.error(
            "Failed to extract page from PDF",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to extract page from PDF", pdf_path, "page_extraction", e
        )


@log_operation("pdf_page_html_extraction")
def extract_page_html(pdf_path: str, page_number: int) -> str:
    """
    Extract HTML content from a specific page.

    Args:
        pdf_path: Absolute path to the PDF file
        page_number: Page number (0-indexed)

    Returns:
        HTML content of the page with formatting

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found",
                file_path=pdf_path,
                operation="page_html_extraction",
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF page HTML extraction",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_html_extraction",
        )
        doc = fitz.open(pdf_path)

        # Check page number
        if page_number < 0 or page_number >= doc.page_count:
            doc.close()
            raise PdfProcessingError(
                f"Page number {page_number} out of range (0-{doc.page_count-1})",
                pdf_path,
                "page_html_extraction",
            )

        # Extract HTML
        page = doc[page_number]
        html = page.get_text("html")
        doc.close()

        logger.info(
            "PDF page HTML extraction completed",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_html_extraction",
            html_length=len(html),
        )
        return html

    except FileNotFoundError:
        raise
    except PdfProcessingError:
        raise
    except Exception as e:
        logger.error(
            "Failed to extract HTML from PDF page",
            file_path=pdf_path,
            page_number=page_number,
            operation="page_html_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to extract HTML from PDF page", pdf_path, "page_html_extraction", e
        )


def convert_html_to_markdown(html_str: str) -> str:
    """
    Convert HTML string to Markdown format.

    Args:
        html_str: HTML string to convert

    Returns:
        Markdown-formatted string
    """
    check_dependencies()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    return h.handle(html_str)


@log_operation("pdf_page_markdown_extraction")
def extract_page_markdown(pdf_path: str, page_number: int) -> str:
    """
    Extract page content as Markdown with formatting preservation.

    Args:
        pdf_path: Absolute path to the PDF file
        page_number: Page number (0-indexed)

    Returns:
        Markdown-formatted page content

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    html = extract_page_html(pdf_path, page_number)
    return convert_html_to_markdown(html)


@log_operation("pdf_page_range_extraction")
def extract_page_range(
    pdf_path: str, start_page: int, end_page: int, output: str = "text"
) -> str:
    """
    Extract text from a range of pages.

    Args:
        pdf_path: Absolute path to the PDF file
        start_page: Starting page number (0-indexed, inclusive)
        end_page: Ending page number (0-indexed, inclusive)
        output: Output format ('text', 'html', or 'markdown')

    Returns:
        Combined content from all pages in the range

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
        ValueError: If invalid output format specified
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found",
                file_path=pdf_path,
                operation="page_range_extraction",
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF page range extraction",
            file_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            output_format=output,
            operation="page_range_extraction",
        )
        doc = fitz.open(pdf_path)

        # Validate page range
        if start_page < 0 or end_page >= doc.page_count or start_page > end_page:
            doc.close()
            raise PdfProcessingError(
                f"Invalid page range [{start_page}, {end_page}] for document with {doc.page_count} pages",
                pdf_path,
                "page_range_extraction",
            )

        # Extract pages
        content_parts = []
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]

            if output == "text":
                content_parts.append(page.get_text())
            elif output == "html":
                content_parts.append(page.get_text("html"))
            elif output == "markdown":
                html = page.get_text("html")
                content_parts.append(convert_html_to_markdown(html))
            else:
                doc.close()
                raise ValueError(
                    f"Invalid output format: {output}. Use 'text', 'html', or 'markdown'."
                )

        doc.close()

        # Combine content
        if output == "markdown":
            result = "\n\n---\n\n".join(content_parts)  # Page breaks
        else:
            result = "\n\n".join(content_parts)

        logger.info(
            "PDF page range extraction completed",
            file_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            page_count=end_page - start_page + 1,
            operation="page_range_extraction",
            content_length=len(result),
        )
        return result

    except FileNotFoundError:
        raise
    except PdfProcessingError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Failed to extract page range from PDF",
            file_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            operation="page_range_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to extract page range from PDF",
            pdf_path,
            "page_range_extraction",
            e,
        )


@log_operation("pdf_chapter_extraction")
def extract_chapter(
    pdf_path: str, chapter_title: str, output: str = "text"
) -> Dict[str, Any]:
    """
    Extract a chapter by title from PDF TOC.

    Args:
        pdf_path: Absolute path to the PDF file
        chapter_title: Title of the chapter (partial match supported)
        output: Output format ('text', 'html', or 'markdown')

    Returns:
        Dictionary with:
        - title: Chapter title
        - level: TOC level
        - start_page: Starting page (1-indexed)
        - end_page: Ending page (1-indexed)
        - content: Chapter content

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If chapter not found or extraction fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found", file_path=pdf_path, operation="chapter_extraction"
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF chapter extraction",
            file_path=pdf_path,
            chapter_title=chapter_title,
            operation="chapter_extraction",
        )
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()

        # Find chapter in TOC
        chapter_idx = None
        for i, (level, title, page) in enumerate(toc):
            if chapter_title.lower() in title.lower():
                chapter_idx = i
                break

        if chapter_idx is None:
            doc.close()
            raise PdfProcessingError(
                f"Chapter '{chapter_title}' not found in TOC",
                pdf_path,
                "chapter_extraction",
            )

        # Get chapter info
        chapter_level, chapter_title_full, start_page = toc[chapter_idx]

        # Find end page (next chapter at same or higher level)
        end_page = doc.page_count
        for i in range(chapter_idx + 1, len(toc)):
            level, title, page = toc[i]
            if level <= chapter_level:
                end_page = page
                break

        doc.close()

        # Extract content (pages are 1-indexed in TOC, 0-indexed in extraction)
        content = extract_page_range(pdf_path, start_page - 1, end_page - 1, output)

        result = {
            "title": chapter_title_full,
            "level": chapter_level,
            "start_page": start_page,
            "end_page": end_page,
            "page_count": end_page - start_page + 1,
            "content": content,
        }

        logger.info(
            "PDF chapter extraction completed",
            file_path=pdf_path,
            chapter_title=chapter_title_full,
            start_page=start_page,
            end_page=end_page,
            operation="chapter_extraction",
        )
        return result

    except FileNotFoundError:
        raise
    except PdfProcessingError:
        raise
    except Exception as e:
        logger.error(
            "Failed to extract chapter from PDF",
            file_path=pdf_path,
            chapter_title=chapter_title,
            operation="chapter_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to extract chapter from PDF", pdf_path, "chapter_extraction", e
        )


@log_operation("pdf_full_text_extraction")
def extract_full_text(pdf_path: str, output: str = "text") -> str:
    """
    Extract all text from PDF.

    Args:
        pdf_path: Absolute path to the PDF file
        output: Output format ('text', 'html', or 'markdown')

    Returns:
        Complete PDF content in specified format

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If the file is not a valid PDF or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            logger.error(
                "PDF file not found",
                file_path=pdf_path,
                operation="full_text_extraction",
            )
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Open PDF file
        logger.debug(
            "Starting PDF full text extraction",
            file_path=pdf_path,
            output_format=output,
            operation="full_text_extraction",
        )
        doc = fitz.open(pdf_path)

        # Extract all pages
        result = extract_page_range(pdf_path, 0, doc.page_count - 1, output)

        doc.close()

        logger.info(
            "PDF full text extraction completed",
            file_path=pdf_path,
            page_count=doc.page_count,
            operation="full_text_extraction",
            content_length=len(result),
        )
        return result

    except FileNotFoundError:
        raise
    except PdfProcessingError:
        raise
    except Exception as e:
        logger.error(
            "Failed to extract full text from PDF",
            file_path=pdf_path,
            operation="full_text_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to extract full text from PDF", pdf_path, "full_text_extraction", e
        )


def search_text_in_pdf(
    pdf_path: str, query: str, context_chars: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for text in PDF and return matches with context.

    Args:
        pdf_path: Absolute path to the PDF file
        query: Search query
        context_chars: Number of characters to include before/after match

    Returns:
        List of matches with:
        - page: Page number (0-indexed)
        - match: Matching text
        - context: Surrounding text
        - position: Character position on page

    Raises:
        FileNotFoundError: If the file does not exist
        PdfProcessingError: If search fails
    """
    check_dependencies()

    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        results = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()

            # Case-insensitive search
            text_lower = text.lower()
            query_lower = query.lower()

            # Find all occurrences
            start = 0
            while True:
                pos = text_lower.find(query_lower, start)
                if pos == -1:
                    break

                # Extract context
                context_start = max(0, pos - context_chars)
                context_end = min(len(text), pos + len(query) + context_chars)
                context = text[context_start:context_end]

                results.append(
                    {
                        "page": page_num,
                        "match": text[pos : pos + len(query)],
                        "context": context,
                        "position": pos,
                    }
                )

                start = pos + 1

        doc.close()
        return results

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to search text in PDF",
            file_path=pdf_path,
            query=query,
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise PdfProcessingError(
            "Failed to search text in PDF", pdf_path, "text_search", e
        )
