#!/usr/bin/env python3
"""
Convert Sports Analytics Books from ACSM to PDF and Upload to S3

This script converts 3 sports analytics books from ACSM files to PDFs using Adobe Digital Editions,
then uploads them to the S3 bucket nba-mcp-books-20251011.

Books to process:
1. Sports Analytics
2. Basketball Beyond Paper
3. The Midrange Theory
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to the path so we can import from scripts
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the existing converter and book manager classes
from scripts.recursive_book_analysis import AcsmConverter, BookManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sports_books_conversion.log"),
    ],
)
logger = logging.getLogger(__name__)

# S3 bucket configuration
S3_BUCKET = "nba-mcp-books-20251011"

# Define the 3 sports analytics books to process
SPORTS_BOOKS = [
    {
        "id": "sports_analytics",
        "title": "Sports Analytics",
        "acsm_path": "/Users/ryanranft/Downloads/Sports_Analytics-pdf.acsm",
        "s3_path": "books/Sports_Analytics.pdf",
        "expected_pdf_name": "Sports_Analytics.pdf",
    },
    {
        "id": "basketball_beyond_paper",
        "title": "Basketball Beyond Paper",
        "acsm_path": "/Users/ryanranft/Downloads/Basketball_Beyond_Paper-pdf.acsm",
        "s3_path": "books/Basketball_Beyond_Paper.pdf",
        "expected_pdf_name": "Basketball_Beyond_Paper.pdf",
    },
    {
        "id": "midrange_theory",
        "title": "The Midrange Theory",
        "acsm_path": "/Users/ryanranft/Downloads/The_Midrange_Theory-pdf.acsm",
        "s3_path": "books/The_Midrange_Theory.pdf",
        "expected_pdf_name": "The_Midrange_Theory.pdf",
    },
]


def check_prerequisites() -> bool:
    """Check if Adobe Digital Editions is installed and ACSM files exist."""
    logger.info("🔍 Checking prerequisites...")

    # Check Adobe Digital Editions
    converter = AcsmConverter()
    if not converter.is_ade_installed():
        logger.error(
            "❌ Adobe Digital Editions not found at /Applications/Adobe Digital Editions.app"
        )
        logger.error("Please install Adobe Digital Editions from:")
        logger.error(
            "https://www.adobe.com/solutions/ebook/digital-editions/download.html"
        )
        return False

    logger.info("✅ Adobe Digital Editions found")

    # Check ACSM files exist
    missing_files = []
    for book in SPORTS_BOOKS:
        if not os.path.exists(book["acsm_path"]):
            missing_files.append(book["acsm_path"])

    if missing_files:
        logger.error("❌ Missing ACSM files:")
        for file_path in missing_files:
            logger.error(f"   - {file_path}")
        return False

    logger.info("✅ All ACSM files found")
    return True


def convert_and_upload_books() -> Dict[str, str]:
    """
    Convert ACSM files to PDFs and upload to S3.

    Returns:
        Dictionary mapping book IDs to their converted PDF paths
    """
    logger.info("🚀 Starting conversion and upload process...")

    converter = AcsmConverter()
    book_manager = BookManager(S3_BUCKET)

    results = {
        "successful_conversions": [],
        "failed_conversions": [],
        "successful_uploads": [],
        "failed_uploads": [],
    }

    for book in SPORTS_BOOKS:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {book['title']}")
        logger.info(f"{'='*70}")

        # Check if book already exists in S3
        if book_manager.book_exists_in_s3(book["s3_path"]):
            logger.info(f"✅ Book already exists in S3: {book['s3_path']}")
            results["successful_uploads"].append(book)
            continue

        # Convert ACSM to PDF
        logger.info(f"🔄 Converting ACSM file: {book['acsm_path']}")
        converted_pdf = converter.convert_acsm_with_ade(book["acsm_path"], timeout=90)

        if not converted_pdf:
            logger.error(f"❌ Failed to convert: {book['title']}")
            results["failed_conversions"].append(book)

            # Show manual conversion instructions
            show_manual_instructions(book)
            continue

        logger.info(f"✅ Successfully converted to: {converted_pdf}")
        results["successful_conversions"].append(book)

        # Upload to S3
        logger.info(f"📤 Uploading to S3: {book['s3_path']}")
        upload_success = book_manager.upload_to_s3(converted_pdf, book["s3_path"])

        if upload_success:
            logger.info(f"✅ Successfully uploaded: {book['title']}")
            results["successful_uploads"].append(book)
        else:
            logger.error(f"❌ Failed to upload: {book['title']}")
            results["failed_uploads"].append(book)

    return results


def show_manual_instructions(book: Dict) -> None:
    """Display manual conversion instructions for a failed book."""
    logger.info(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║           ⚠️  MANUAL CONVERSION REQUIRED                         ║
╚══════════════════════════════════════════════════════════════════╝

Book: {book['title']}
ACSM File: {book['acsm_path']}

Follow these steps:

1. Open Adobe Digital Editions
2. Double-click: {book['acsm_path']}
3. Wait for the PDF to download
4. Find the PDF in: ~/Documents/Digital Editions/
5. Copy it to Downloads folder as: {book['expected_pdf_name']}
6. Re-run this script

═══════════════════════════════════════════════════════════════════
"""
    )


def verify_uploads(results: Dict) -> None:
    """Verify that all books were successfully uploaded to S3."""
    logger.info("\n🔍 Verifying S3 uploads...")

    book_manager = BookManager(S3_BUCKET)

    for book in SPORTS_BOOKS:
        if book_manager.book_exists_in_s3(book["s3_path"]):
            logger.info(f"✅ Verified in S3: {book['title']}")
        else:
            logger.error(f"❌ Not found in S3: {book['title']}")


def print_summary(results: Dict) -> None:
    """Print a summary of the conversion and upload process."""
    logger.info(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 CONVERSION SUMMARY                        ║
╚══════════════════════════════════════════════════════════════════╝

Successful Conversions: {len(results['successful_conversions'])}/3
Successful Uploads: {len(results['successful_uploads'])}/3

✅ Successfully Processed:
"""
    )

    for book in results["successful_uploads"]:
        logger.info(f"   - {book['title']}")

    if results["failed_conversions"]:
        logger.info(
            f"""
❌ Failed Conversions:
"""
        )
        for book in results["failed_conversions"]:
            logger.info(f"   - {book['title']}")

    if results["failed_uploads"]:
        logger.info(
            f"""
❌ Failed Uploads:
"""
        )
        for book in results["failed_uploads"]:
            logger.info(f"   - {book['title']}")

    logger.info(
        f"""
═══════════════════════════════════════════════════════════════════
"""
    )


def main():
    """Main function to orchestrate the conversion and upload process."""
    logger.info("🏀 Sports Analytics Books Converter")
    logger.info("=" * 50)

    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites not met. Exiting.")
        sys.exit(1)

    # Convert and upload books
    results = convert_and_upload_books()

    # Verify uploads
    verify_uploads(results)

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    if len(results["successful_uploads"]) == 3:
        logger.info("🎉 All books successfully processed!")
        sys.exit(0)
    else:
        logger.error("⚠️  Some books failed to process. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
