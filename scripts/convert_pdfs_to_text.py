#!/usr/bin/env python3
"""
Convert Sports Analytics PDFs to Text Format

This script converts the 3 sports analytics PDFs from S3 to text format
and uploads them back to S3 for better readability and mathematical notation processing.

Books to convert:
1. Sports Analytics
2. Basketball Beyond Paper
3. The Midrange Theory
"""

import os
import sys
import logging
import io
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to the path so we can import from scripts
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the existing classes
from scripts.recursive_book_analysis import BookManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pdf_to_text_conversion.log"),
    ],
)
logger = logging.getLogger(__name__)

# S3 bucket configuration
S3_BUCKET = "nba-mcp-books-20251011"

# Define the books to convert
BOOKS_TO_CONVERT = [
    {
        "id": "sports_analytics",
        "title": "Sports Analytics",
        "pdf_s3_path": "books/Sports_Analytics.pdf",
        "text_s3_path": "books/Sports_Analytics.txt",
    },
    {
        "id": "basketball_beyond_paper",
        "title": "Basketball Beyond Paper",
        "pdf_s3_path": "books/Basketball_Beyond_Paper.pdf",
        "text_s3_path": "books/Basketball_Beyond_Paper.txt",
    },
    {
        "id": "midrange_theory",
        "title": "The Midrange Theory",
        "pdf_s3_path": "books/The_Midrange_Theory.pdf",
        "text_s3_path": "books/The_Midrange_Theory.txt",
    },
]


def check_pdf_dependencies() -> bool:
    """Check if PDF processing libraries are available."""
    try:
        import PyPDF2

        logger.info("✅ PyPDF2 available")
        return True
    except ImportError:
        logger.error("❌ PyPDF2 not available. Installing...")
        try:
            import subprocess

            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
            logger.info("✅ PyPDF2 installed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to install PyPDF2: {e}")
            return False


def extract_pdf_text_from_s3(
    book_manager: BookManager, pdf_s3_path: str
) -> Optional[str]:
    """
    Download PDF from S3 and extract text content.

    Args:
        book_manager: BookManager instance for S3 operations
        pdf_s3_path: S3 path to the PDF file

    Returns:
        Extracted text content or None if failed
    """
    try:
        import PyPDF2

        logger.info(f"📥 Downloading PDF from S3: {pdf_s3_path}")

        # Download PDF from S3
        response = book_manager.s3_client.get_object(Bucket=S3_BUCKET, Key=pdf_s3_path)
        pdf_content = response["Body"].read()

        logger.info(f"📄 PDF downloaded ({len(pdf_content)} bytes)")

        # Extract text using PyPDF2
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_content = ""
        total_pages = len(pdf_reader.pages)

        logger.info(f"📖 Extracting text from {total_pages} pages...")

        for page_num in range(total_pages):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text_content += page_text + "\n\n"

                if (page_num + 1) % 10 == 0:
                    logger.info(f"   Processed {page_num + 1}/{total_pages} pages...")

            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to extract text from page {page_num + 1}: {e}"
                )
                continue

        logger.info(f"✅ Text extraction completed ({len(text_content)} characters)")
        return text_content.strip()

    except Exception as e:
        logger.error(f"❌ Failed to extract text from PDF: {e}")
        return None


def upload_text_to_s3(
    book_manager: BookManager, text_content: str, text_s3_path: str
) -> bool:
    """
    Upload extracted text to S3.

    Args:
        book_manager: BookManager instance for S3 operations
        text_content: Text content to upload
        text_s3_path: S3 path for the text file

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"📤 Uploading text to S3: {text_s3_path}")

        # Upload text content to S3
        book_manager.s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=text_s3_path,
            Body=text_content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )

        logger.info(f"✅ Text uploaded successfully ({len(text_content)} characters)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to upload text to S3: {e}")
        return False


def convert_book_to_text(book_manager: BookManager, book: Dict) -> bool:
    """
    Convert a single book from PDF to text format.

    Args:
        book_manager: BookManager instance for S3 operations
        book: Book dictionary with metadata

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Converting: {book['title']}")
    logger.info(f"{'='*70}")

    # Check if text version already exists
    if book_manager.book_exists_in_s3(book["text_s3_path"]):
        logger.info(f"✅ Text version already exists: {book['title']}")
        return True

    # Extract text from PDF
    text_content = extract_pdf_text_from_s3(book_manager, book["pdf_s3_path"])
    if not text_content:
        logger.error(f"❌ Failed to extract text from: {book['title']}")
        return False

    # Upload text to S3
    success = upload_text_to_s3(book_manager, text_content, book["text_s3_path"])
    if success:
        logger.info(f"✅ Successfully converted: {book['title']}")
        return True
    else:
        logger.error(f"❌ Failed to upload text for: {book['title']}")
        return False


def verify_text_uploads(book_manager: BookManager) -> None:
    """Verify that all text files were successfully uploaded to S3."""
    logger.info("\n🔍 Verifying text uploads...")

    for book in BOOKS_TO_CONVERT:
        if book_manager.book_exists_in_s3(book["text_s3_path"]):
            logger.info(f"✅ Text version verified: {book['title']}")
        else:
            logger.error(f"❌ Text version not found: {book['title']}")


def print_summary(results: Dict) -> None:
    """Print a summary of the conversion process."""
    logger.info(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 CONVERSION SUMMARY                        ║
╚══════════════════════════════════════════════════════════════════╝

Successful Conversions: {len(results['successful'])}/3
Failed Conversions: {len(results['failed'])}/3

✅ Successfully Converted:
"""
    )

    for book in results["successful"]:
        logger.info(f"   - {book['title']}")

    if results["failed"]:
        logger.info(
            f"""
❌ Failed Conversions:
"""
        )
        for book in results["failed"]:
            logger.info(f"   - {book['title']}")

    logger.info(
        f"""
📝 Benefits of Text Format:
   - Better mathematical notation readability
   - Faster text processing
   - Improved search capabilities
   - Easier content analysis

═══════════════════════════════════════════════════════════════════
"""
    )


def main():
    """Main function to orchestrate the PDF to text conversion process."""
    logger.info("📚 Sports Analytics PDF to Text Converter")
    logger.info("=" * 50)

    # Check dependencies
    if not check_pdf_dependencies():
        logger.error("❌ Required dependencies not available. Exiting.")
        sys.exit(1)

    # Initialize book manager
    book_manager = BookManager(S3_BUCKET)

    results = {"successful": [], "failed": []}

    # Convert each book
    for book in BOOKS_TO_CONVERT:
        success = convert_book_to_text(book_manager, book)
        if success:
            results["successful"].append(book)
        else:
            results["failed"].append(book)

    # Verify uploads
    verify_text_uploads(book_manager)

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    if len(results["successful"]) == 3:
        logger.info("🎉 All books successfully converted to text format!")
        sys.exit(0)
    else:
        logger.error("⚠️ Some books failed to convert. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
