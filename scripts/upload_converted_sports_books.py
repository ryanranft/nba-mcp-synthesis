#!/usr/bin/env python3
"""
Upload Converted Sports Analytics Books to S3

This script copies already converted PDFs from Digital Editions to Downloads
and uploads them to S3 bucket nba-mcp-books-20251011.

Books to process:
1. Sports Analytics ✅ (converted)
2. Basketball Beyond Paper ✅ (converted)
3. The Midrange Theory ❌ (needs conversion)
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# Add the project root to the path so we can import from scripts
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the existing book manager class
from scripts.recursive_book_analysis import BookManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("sports_books_upload.log")],
)
logger = logging.getLogger(__name__)

# S3 bucket configuration
S3_BUCKET = "nba-mcp-books-20251011"

# Define the books and their status
BOOKS = [
    {
        "id": "sports_analytics",
        "title": "Sports Analytics",
        "digital_editions_path": "~/Documents/Digital Editions/Sports Analytics.pdf",
        "downloads_path": "~/Downloads/Sports_Analytics.pdf",
        "s3_path": "books/Sports_Analytics.pdf",
        "converted": True,
    },
    {
        "id": "basketball_beyond_paper",
        "title": "Basketball Beyond Paper",
        "digital_editions_path": "~/Documents/Digital Editions/Basketball Beyond Paper.pdf",
        "downloads_path": "~/Downloads/Basketball_Beyond_Paper.pdf",
        "s3_path": "books/Basketball_Beyond_Paper.pdf",
        "converted": True,
    },
    {
        "id": "midrange_theory",
        "title": "The Midrange Theory",
        "digital_editions_path": "~/Documents/Digital Editions/The Midrange Theory.pdf",
        "downloads_path": "~/Downloads/The_Midrange_Theory.pdf",
        "s3_path": "books/The_Midrange_Theory.pdf",
        "converted": False,
    },
]


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in path."""
    return os.path.expanduser(os.path.expandvars(path))


def copy_pdf_to_downloads(book: dict) -> bool:
    """Copy PDF from Digital Editions to Downloads folder."""
    source_path = expand_path(book["digital_editions_path"])
    dest_path = expand_path(book["downloads_path"])

    if not os.path.exists(source_path):
        logger.error(f"❌ Source PDF not found: {source_path}")
        return False

    try:
        logger.info(f"📋 Copying {book['title']} to Downloads...")
        shutil.copy2(source_path, dest_path)
        logger.info(f"✅ Copied to: {dest_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to copy {book['title']}: {e}")
        return False


def upload_to_s3(book: dict) -> bool:
    """Upload PDF to S3 bucket."""
    downloads_path = expand_path(book["downloads_path"])

    if not os.path.exists(downloads_path):
        logger.error(f"❌ PDF not found in Downloads: {downloads_path}")
        return False

    try:
        book_manager = BookManager(S3_BUCKET)

        # Check if already exists in S3
        if book_manager.book_exists_in_s3(book["s3_path"]):
            logger.info(f"✅ Already exists in S3: {book['title']}")
            return True

        # Upload to S3
        logger.info(f"📤 Uploading {book['title']} to S3...")
        success = book_manager.upload_to_s3(downloads_path, book["s3_path"])

        if success:
            logger.info(f"✅ Successfully uploaded: {book['title']}")
            return True
        else:
            logger.error(f"❌ Failed to upload: {book['title']}")
            return False

    except Exception as e:
        logger.error(f"❌ Upload error for {book['title']}: {e}")
        return False


def handle_missing_book(book: dict) -> None:
    """Provide instructions for the missing book."""
    logger.info(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║           ⚠️  MANUAL CONVERSION REQUIRED                         ║
╚══════════════════════════════════════════════════════════════════╝

Book: {book['title']}
ACSM File: /Users/ryanranft/Downloads/The_Midrange_Theory-pdf.acsm

Follow these steps:

1. Open Adobe Digital Editions
2. Double-click: /Users/ryanranft/Downloads/The_Midrange_Theory-pdf.acsm
3. Wait for the PDF to download
4. Find the PDF in: ~/Documents/Digital Editions/
5. Copy it to Downloads folder as: The_Midrange_Theory.pdf
6. Re-run this script

═══════════════════════════════════════════════════════════════════
"""
    )


def main():
    """Main function to orchestrate the upload process."""
    logger.info("🏀 Sports Analytics Books Uploader")
    logger.info("=" * 50)

    results = {
        "successful_uploads": [],
        "failed_uploads": [],
        "missing_conversions": [],
    }

    for book in BOOKS:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {book['title']}")
        logger.info(f"{'='*70}")

        if not book["converted"]:
            logger.warning(f"⚠️  {book['title']} not yet converted")
            results["missing_conversions"].append(book)
            handle_missing_book(book)
            continue

        # Copy PDF to Downloads
        if not copy_pdf_to_downloads(book):
            results["failed_uploads"].append(book)
            continue

        # Upload to S3
        if upload_to_s3(book):
            results["successful_uploads"].append(book)
        else:
            results["failed_uploads"].append(book)

    # Print summary
    logger.info(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 UPLOAD SUMMARY                             ║
╚══════════════════════════════════════════════════════════════════╝

Successful Uploads: {len(results['successful_uploads'])}/3
Failed Uploads: {len(results['failed_uploads'])}/3
Missing Conversions: {len(results['missing_conversions'])}/3

✅ Successfully Uploaded:
"""
    )

    for book in results["successful_uploads"]:
        logger.info(f"   - {book['title']}")

    if results["failed_uploads"]:
        logger.info(
            f"""
❌ Failed Uploads:
"""
        )
        for book in results["failed_uploads"]:
            logger.info(f"   - {book['title']}")

    if results["missing_conversions"]:
        logger.info(
            f"""
⚠️  Needs Manual Conversion:
"""
        )
        for book in results["missing_conversions"]:
            logger.info(f"   - {book['title']}")

    logger.info(
        f"""
═══════════════════════════════════════════════════════════════════
"""
    )

    # Exit with appropriate code
    if len(results["successful_uploads"]) >= 2:
        logger.info("🎉 Most books successfully uploaded!")
        if results["missing_conversions"]:
            logger.info(
                "📝 Please convert the remaining book manually and re-run this script."
            )
        sys.exit(0)
    else:
        logger.error("⚠️  Some books failed to upload. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
