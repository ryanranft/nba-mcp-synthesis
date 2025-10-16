#!/usr/bin/env python3
"""
Upload Missing Books to S3

Uploads 22 missing books from Downloads folder to S3 bucket nba-mcp-books-20251011.
"""

import boto3
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Upload missing books to S3."""

    missing_books = [
        '0812_Machine-Learning-for-Absolute-Beginners.pdf',
        'AI Engineering.pdf',
        'Anaconda-Sponsored_Manning_Generative-AI-in-Action.pdf',
        'Applied-Machine-Learning-and-AI-for-Engineers.pdf',
        'Artificial Intelligence - A Modern Approach (3rd Edition).pdf',
        'Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf',
        'Deep Learning by Ian Goodfellow, Yoshua Bengio, Aaron Courville.pdf',
        'Designing_Machine_Learning_Systems_An_Iterative_Process_for_Production-Ready_Applications_-_Chip_Huyen.pdf',
        'Gans-in-action-deep-learning-with-generative-adversarial-networks.pdf',
        'Generative-Deep-Learning.pdf',
        'Hands-On Generative AI with Transformers and Diffusion.pdf',
        'Hands-On_Large_Language_Models.pdf',
        'Hands-On_Machine_Learning_with_Scikit-Learn_Keras_and_Tensorflow_-_Aurelien_Geron.pdf',
        'LLM Engineers Handbook.pdf',
        'ML Machine Learning-A Probabilistic Perspective.pdf',
        'ML Math.pdf',
        'NLP with Transformer models.pdf',
        'Practical MLOps_ Operationalizing Machine Learning Models.pdf',
        'Probabilistic Machine Learning Advanced Topics... (Z-Library).pdf',
        'building-machine-learning-powered-applications-going-from-idea-to-product.pdf',
        'machine_learning.pdf'
    ]

    s3 = boto3.client('s3')
    bucket = 'nba-mcp-books-20251011'
    downloads_dir = Path('/Users/ryanranft/Downloads')

    logger.info(f"Starting upload of {len(missing_books)} books to S3 bucket: {bucket}")
    logger.info("=" * 80)

    uploaded_count = 0
    failed_count = 0

    for book in missing_books:
        local_path = downloads_dir / book
        s3_key = f'books/{book}'

        try:
            if local_path.exists():
                # Check file size
                file_size = local_path.stat().st_size
                logger.info(f"📚 Uploading: {book} ({file_size:,} bytes)")

                # Upload to S3
                s3.upload_file(str(local_path), bucket, s3_key)
                logger.info(f"✅ Successfully uploaded: {book}")
                uploaded_count += 1
            else:
                logger.warning(f"❌ File not found: {book}")
                failed_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to upload {book}: {e}")
            failed_count += 1

    logger.info("=" * 80)
    logger.info(f"Upload Summary:")
    logger.info(f"  ✅ Successfully uploaded: {uploaded_count}")
    logger.info(f"  ❌ Failed: {failed_count}")
    logger.info(f"  📊 Total processed: {len(missing_books)}")

    if uploaded_count > 0:
        logger.info(f"🎉 {uploaded_count} books are now available in S3!")

    return uploaded_count, failed_count

if __name__ == '__main__':
    uploaded, failed = main()
    exit(0 if failed == 0 else 1)




