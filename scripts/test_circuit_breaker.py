#!/usr/bin/env python3
"""
Test script for circuit breaker implementation.
Tests the resilient workflow with known broken APIs.
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.four_model_book_analyzer import FourModelBookAnalyzer
from circuit_breaker import circuit_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_resilient_analysis():
    """Test the resilient analysis with circuit breaker."""
    logger.info("🧪 Testing resilient analysis with circuit breaker...")

    # Test book metadata
    test_book = {
        'title': 'Test Book for Circuit Breaker',
        'author': 'Test Author',
        's3_path': 'books/test.pdf',
        'content': """
        This is a test book about machine learning and basketball analytics.
        It covers topics like:
        - Statistical analysis of player performance
        - Machine learning models for game prediction
        - Data visualization techniques
        - Performance optimization strategies
        """
    }

    # Initialize analyzer
    analyzer = FourModelBookAnalyzer()

    # Show circuit breaker status
    logger.info("🛡️ Circuit breaker status:")
    status = circuit_manager.get_circuit_breaker_status()
    for api_name, info in status.items():
        logger.info(f"  {api_name}: {info['state']} (can_execute: {info['can_execute']})")

    logger.info(f"✅ Working APIs: {circuit_manager.get_working_apis()}")
    logger.info(f"🚫 Broken APIs: {list(circuit_manager.broken_apis)}")

    # Run analysis
    logger.info("🚀 Starting resilient analysis...")
    result = await analyzer.analyze_book(test_book)

    logger.info("📊 Analysis Results:")
    logger.info(f"  Success: {result.success}")
    logger.info(f"  Recommendations: {len(result.recommendations)}")
    logger.info(f"  Total Cost: ${result.total_cost:.4f}")
    logger.info(f"  Total Time: {result.total_time:.1f}s")

    if result.error:
        logger.error(f"  Error: {result.error}")

    # Show final circuit breaker status
    logger.info("🛡️ Final circuit breaker status:")
    final_status = circuit_manager.get_circuit_breaker_status()
    for api_name, info in final_status.items():
        logger.info(f"  {api_name}: {info['state']} (failures: {info['failure_count']})")

if __name__ == "__main__":
    asyncio.run(test_resilient_analysis())


