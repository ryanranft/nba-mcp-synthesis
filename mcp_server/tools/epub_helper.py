"""
EPUB Processing Helper for NBA MCP Server

Provides EPUB file processing capabilities including:
- Metadata extraction
- Table of contents parsing
- Chapter extraction with subchapter support
- HTML to Markdown conversion

Based on best practices from ebook-mcp implementation.
"""

import os
from typing import List, Tuple, Dict, Union, Any, Optional

try:
    from ebooklib import epub

    EBOOKLIB_AVAILABLE = True
except ImportError:
    epub = None
    EBOOKLIB_AVAILABLE = False

try:
    from bs4 import BeautifulSoup, Comment

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    Comment = None
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import html2text

    HTML2TEXT_AVAILABLE = True
except ImportError:
    html2text = None
    HTML2TEXT_AVAILABLE = False

from ..exceptions import EpubProcessingError
from .logger_config import get_logger, log_operation

# Initialize logger
logger = get_logger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    if not EBOOKLIB_AVAILABLE:
        missing.append("ebooklib")
    if not BEAUTIFULSOUP_AVAILABLE:
        missing.append("beautifulsoup4")
    if not HTML2TEXT_AVAILABLE:
        missing.append("html2text")

    if missing:
        raise ImportError(
            f"Missing required dependencies for EPUB processing: {', '.join(missing)}. "
            f"Install with: pip install {' '.join(missing)}"
        )


def get_all_epub_files(path: str) -> List[str]:
    """
    Get all EPUB files in the specified directory.

    Args:
        path: Directory path to search

    Returns:
        List of EPUB filenames
    """
    check_dependencies()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")

    return [f for f in os.listdir(path) if f.lower().endswith(".epub")]


@log_operation("epub_toc_extraction")
def get_toc(epub_path: str) -> List[Tuple[str, str]]:
    """
    Get the Table of Contents (TOC) from an EPUB file.

    Handles nested TOC structures with chapters and subchapters.

    Args:
        epub_path: Absolute path to the EPUB file

    Returns:
        List of TOC entries, each entry is a tuple of (title, href)

    Raises:
        FileNotFoundError: If the file does not exist
        EpubProcessingError: If the file is not a valid EPUB or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(epub_path):
            logger.error(
                "EPUB file not found", file_path=epub_path, operation="toc_extraction"
            )
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        # Read EPUB file
        logger.debug(
            "Starting EPUB TOC extraction",
            file_path=epub_path,
            operation="toc_extraction",
        )
        book = epub.read_epub(epub_path)
        toc = []

        # Iterate through TOC items
        for item in book.toc:
            # Handle nested TOC structure
            if isinstance(item, tuple):
                # item format: (chapter element, list of subchapters)
                chapter = item[0]
                toc.append((chapter.title, chapter.href))
                # Add subchapters
                for sub_item in item[1]:
                    if isinstance(sub_item, tuple):
                        toc.append((sub_item[0].title, sub_item[0].href))
                    else:
                        toc.append((sub_item.title, sub_item.href))
            else:
                # Single level TOC item
                toc.append((item.title, item.href))

        logger.info(
            "EPUB TOC extraction completed",
            file_path=epub_path,
            operation="toc_extraction",
            chapter_count=len(toc),
        )
        return toc
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to parse EPUB file",
            file_path=epub_path,
            operation="toc_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise EpubProcessingError(
            "Failed to parse EPUB file", epub_path, "toc_extraction", e
        )


@log_operation("epub_metadata_extraction")
def get_metadata(epub_path: str) -> Dict[str, Union[str, List[str]]]:
    """
    Get metadata from an EPUB file.

    Extracts standard metadata fields including title, author, language,
    publisher, date, etc.

    Args:
        epub_path: Absolute path to the EPUB file

    Returns:
        Dictionary containing metadata fields

    Raises:
        FileNotFoundError: If the file does not exist
        EpubProcessingError: If the file is not a valid EPUB or parsing fails
    """
    check_dependencies()

    try:
        if not os.path.exists(epub_path):
            logger.error(
                "EPUB file not found",
                file_path=epub_path,
                operation="metadata_extraction",
            )
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        # Read EPUB file
        logger.debug(
            "Starting EPUB metadata extraction",
            file_path=epub_path,
            operation="metadata_extraction",
        )
        book = epub.read_epub(epub_path)
        meta = {}

        # Standard metadata fields
        standard_fields = {
            "title": "title",
            "language": "language",
            "identifier": "identifier",
            "date": "date",
            "publisher": "publisher",
            "description": "description",
        }

        # Fields that may have multiple values
        multi_fields = ["creator", "contributor", "subject"]

        # Extract standard fields
        for field, dc_field in standard_fields.items():
            items = book.get_metadata("DC", dc_field)
            if items and len(items) > 0 and len(items[0]) > 0:
                meta[field] = items[0][0]

        # Handle multi-value fields
        for field in multi_fields:
            items = book.get_metadata("DC", field)
            if items:
                meta[field] = [item[0] for item in items]

        logger.info(
            "EPUB metadata extraction completed",
            file_path=epub_path,
            operation="metadata_extraction",
            metadata_fields=list(meta.keys()),
        )
        return meta

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to parse EPUB file",
            file_path=epub_path,
            operation="metadata_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise EpubProcessingError(
            "Failed to parse EPUB file", epub_path, "metadata_extraction", e
        )


def read_epub(epub_path: str) -> Any:
    """
    Read an EPUB file and return the book object.

    Args:
        epub_path: Path to EPUB file

    Returns:
        EPUB book object
    """
    check_dependencies()
    return epub.read_epub(epub_path)


def flatten_toc(book: Any) -> List[str]:
    """
    Flatten nested TOC structure into a list of hrefs.

    Args:
        book: EPUB book object

    Returns:
        List of chapter hrefs
    """
    toc_list = []

    def _flatten(toc: Any) -> None:
        for item in toc:
            if isinstance(item, tuple):
                link, children = item
                toc_list.append(link.href)
                if children:
                    _flatten(children)
            else:
                # Handle single Link object
                toc_list.append(item.href)

    _flatten(book.toc)
    return toc_list


def clean_html(html_str: str) -> str:
    """
    Clean HTML content by removing unnecessary elements.

    Removes:
    - Unnecessary tags (img, script, style, svg, video, iframe, nav)
    - HTML comments
    - Empty tags

    Args:
        html_str: HTML string to clean

    Returns:
        Cleaned HTML string
    """
    check_dependencies()

    soup = BeautifulSoup(html_str, "html.parser")

    # Remove unnecessary tags
    for tag in soup(["script", "style", "img", "svg", "iframe", "video", "nav"]):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove empty tags (no text and no useful attributes)
    for tag in soup.find_all():
        if (
            not tag.get_text(strip=True)
            and not tag.find("img")
            and not tag.name == "br"
        ):
            tag.decompose()

    return str(soup)


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
    return h.handle(html_str)


@log_operation("epub_chapter_extraction")
def extract_chapter_html(book: Any, anchor_href: str) -> str:
    """
    Extract chapter HTML content with improved logic to handle subchapters correctly.

    This function fixes the issue where subchapters in the TOC cause premature truncation
    of chapter content by properly understanding the chapter hierarchy.

    Args:
        book: EPUB book object
        anchor_href: Chapter location like 'chapter1.xhtml#section1_3'

    Returns:
        HTML string with complete chapter content

    Raises:
        EpubProcessingError: If chapter not found or extraction fails
    """
    logger.debug(f"Extracting chapter with improved logic: {anchor_href}")

    href, anchor = anchor_href.split("#") if "#" in anchor_href else (anchor_href, None)

    # Build TOC entries with level information
    toc_entries = []
    for item in book.toc:
        if isinstance(item, tuple):
            chapter = item[0]
            toc_entries.append((chapter.title, chapter.href, 1))
            for sub_item in item[1]:
                if isinstance(sub_item, tuple):
                    toc_entries.append((sub_item[0].title, sub_item[0].href, 2))
                else:
                    toc_entries.append((sub_item.title, sub_item.href, 2))
        else:
            toc_entries.append((item.title, item.href, 1))

    # Find current chapter in TOC
    current_idx = None
    current_level = None
    for i, (title, toc_href, level) in enumerate(toc_entries):
        if toc_href == anchor_href or (anchor_href in toc_href and "#" in anchor_href):
            current_idx = i
            current_level = level
            break

    if current_idx is None:
        raise EpubProcessingError(
            f"Chapter {anchor_href} not found in TOC", "unknown", "toc_lookup"
        )

    # Find next chapter at same or higher level
    next_chapter_href = None
    for i in range(current_idx + 1, len(toc_entries)):
        title, toc_href, level = toc_entries[i]
        if level <= current_level:
            next_chapter_href = toc_href
            break

    # Get chapter content
    item = book.get_item_with_href(href)
    if item is None:
        raise EpubProcessingError(
            f"Chapter file not found: {href}", "unknown", "chapter_file_lookup"
        )

    soup = BeautifulSoup(item.get_content().decode("utf-8"), "html.parser")

    # Helper function to get heading level
    def heading_level(tag_name):
        if tag_name and tag_name.startswith("h") and tag_name[1:].isdigit():
            return int(tag_name[1:])
        return 7  # treat as lowest priority

    # Extract content
    elems = []
    if anchor:
        start_elem = soup.find(id=anchor)
        if not start_elem:
            raise EpubProcessingError(
                f"Anchor {anchor} not found in {href}", "unknown", "anchor_lookup"
            )

        start_level = heading_level(start_elem.name)

        for elem in start_elem.next_elements:
            if elem is start_elem:
                elems.append(str(elem))
                continue
            if (
                hasattr(elem, "name")
                and elem.name
                and elem.name.startswith("h")
                and elem.name[1:].isdigit()
            ):
                if heading_level(elem.name) <= start_level:
                    break
            elems.append(str(elem))
    else:
        chapter_elem = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if chapter_elem:
            start_level = heading_level(chapter_elem.name)
            for elem in chapter_elem.next_elements:
                if elem is chapter_elem:
                    elems.append(str(elem))
                    continue
                if (
                    hasattr(elem, "name")
                    and elem.name
                    and elem.name.startswith("h")
                    and elem.name[1:].isdigit()
                ):
                    if heading_level(elem.name) <= start_level:
                        break
                elems.append(str(elem))
        else:
            body_elem = soup.find("body")
            elems = [str(body_elem)] if body_elem else [str(soup)]

    html = "\n".join(elems)
    return clean_html(html)


def extract_chapter_markdown(book: Any, anchor_href: str) -> str:
    """
    Extract chapter content as Markdown.

    Uses improved extraction logic that handles subchapters correctly.

    Args:
        book: EPUB book object
        anchor_href: Chapter location

    Returns:
        Markdown-formatted chapter content
    """
    html = extract_chapter_html(book, anchor_href)
    return convert_html_to_markdown(html)


def extract_chapter_plain_text(book: Any, anchor_href: str) -> str:
    """
    Extract chapter content as plain text.

    Args:
        book: EPUB book object
        anchor_href: Chapter location

    Returns:
        Plain text chapter content
    """
    html = extract_chapter_html(book, anchor_href)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


def extract_multiple_chapters(
    book: Any, anchor_list: List[str], output: str = "html"
) -> List[Tuple[str, str]]:
    """
    Extract multiple chapters using improved extraction logic.

    Args:
        book: EPUB book object
        anchor_list: List of chapter hrefs
        output: Output format ('html', 'text', or 'markdown')

    Returns:
        List of tuples (href, content)

    Raises:
        ValueError: If invalid output format specified
    """
    results = []
    for href in anchor_list:
        if output == "html":
            content = extract_chapter_html(book, href)
        elif output == "text":
            content = extract_chapter_plain_text(book, href)
        elif output == "markdown":
            content = extract_chapter_markdown(book, href)
        else:
            raise ValueError(
                f"Invalid output format: {output}. Use 'html', 'text', or 'markdown'."
            )
        results.append((href, content))
    return results
