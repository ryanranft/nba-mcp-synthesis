#!/usr/bin/env python3
"""
Upload Algebraic Proof Textbooks to S3

This script uploads two algebraic proof textbooks to the S3 bucket:
1. Book of Proof by Richard Hammack
2. Mathematics for Computer Science by Eric Lehman

These books will enhance the MCP server's algebraic equation manipulation capabilities.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.recursive_book_analysis import BookManager
from mcp_server.config import MCPConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Upload algebraic proof textbooks to S3."""

    # Initialize configuration and book manager
    try:
        config = MCPConfig()
        book_manager = BookManager(config.s3_bucket)
        logger.info(f"Initialized BookManager with S3 bucket: {config.s3_bucket}")
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        return False

    # Define books to upload
    books = [
        {
            "local_path": "/Users/ryanranft/Downloads/Book-of-proof-Richard-Hammack.pdf",
            "s3_path": "books/Book_of_Proof_Richard_Hammack.pdf",
            "title": "Book of Proof",
            "author": "Richard Hammack",
        },
        {
            "local_path": "/Users/ryanranft/Downloads/Mathematics for Computer Science Eric Lehman.pdf",
            "s3_path": "books/Mathematics_for_Computer_Science_Eric_Lehman.pdf",
            "title": "Mathematics for Computer Science",
            "author": "Eric Lehman",
        },
    ]

    # Check if local files exist
    logger.info("Checking local files...")
    for book in books:
        if not os.path.exists(book["local_path"]):
            logger.error(f"❌ Local file not found: {book['local_path']}")
            return False
        else:
            file_size = os.path.getsize(book["local_path"])
            logger.info(f"✅ Found: {book['title']} ({file_size / (1024*1024):.1f} MB)")

    # Upload books to S3
    logger.info("Starting upload to S3...")
    success_count = 0

    for book in books:
        logger.info(f"📤 Uploading: {book['title']}")

        try:
            success = book_manager.upload_to_s3(book["local_path"], book["s3_path"])

            if success:
                logger.info(f"✅ Successfully uploaded: {book['title']}")
                success_count += 1
            else:
                logger.error(f"❌ Failed to upload: {book['title']}")

        except Exception as e:
            logger.error(f"❌ Error uploading {book['title']}: {e}")

    # Summary
    logger.info(f"\n📊 Upload Summary:")
    logger.info(f"   Total books: {len(books)}")
    logger.info(f"   Successful uploads: {success_count}")
    logger.info(f"   Failed uploads: {len(books) - success_count}")

    if success_count == len(books):
        logger.info("🎉 All algebraic proof textbooks uploaded successfully!")
        logger.info("\n📚 These books will enhance the MCP server's capabilities for:")
        logger.info("   • Algebraic equation manipulation")
        logger.info("   • Mathematical proof techniques")
        logger.info("   • Sports analytics formula verification")
        logger.info("   • Symbolic mathematics operations")
        return True
    else:
        logger.error("❌ Some uploads failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
