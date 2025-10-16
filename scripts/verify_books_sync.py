#!/usr/bin/env python3
"""
Verify Books Sync

Verifies that all books in the configuration file exist in S3 bucket.
"""

import boto3
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Verify S3 and config are in sync."""

    config_file = Path('config/books_to_analyze_all_ai_ml.json')
    bucket = 'nba-mcp-books-20251011'

    logger.info("Verifying S3 and configuration sync...")
    logger.info("=" * 80)

    # Load config
    try:
        with open(config_file) as f:
            config = json.load(f)
        logger.info(f"✅ Loaded config: {config_file}")
    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}")
        return False

    # List S3 books
    try:
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(Bucket=bucket, Prefix='books/')
        s3_books = {obj['Key'] for obj in response.get('Contents', [])}
        logger.info(f"✅ Found {len(s3_books)} books in S3 bucket: {bucket}")
    except Exception as e:
        logger.error(f"❌ Failed to list S3 books: {e}")
        return False

    # Verify each config entry
    logger.info("\nVerifying configuration entries...")
    logger.info("-" * 80)

    config_books = config.get('books', [])
    verified_count = 0
    missing_count = 0

    for book in config_books:
        s3_path = book['s3_path']
        title = book['title']

        if s3_path in s3_books:
            logger.info(f"✅ {title}")
            verified_count += 1
        else:
            logger.warning(f"❌ MISSING: {title} ({s3_path})")
            missing_count += 1

    # Summary
    logger.info("=" * 80)
    logger.info("Verification Summary:")
    logger.info(f"  📚 Config books: {len(config_books)}")
    logger.info(f"  📦 S3 books: {len(s3_books)}")
    logger.info(f"  ✅ Verified: {verified_count}")
    logger.info(f"  ❌ Missing: {missing_count}")

    if missing_count == 0:
        logger.info("🎉 All books are properly synced!")
        return True
    else:
        logger.warning(f"⚠️  {missing_count} books need to be uploaded to S3")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)




