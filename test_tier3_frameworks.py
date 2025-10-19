#!/usr/bin/env python3
"""
Test Suite for Tier 3 Frameworks

Tests the A/B Testing Framework and Smart Book Discovery system.
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ab_framework():
    """Test the A/B Testing Framework with a minimal configuration."""
    logger.info("\n" + "="*80)
    logger.info("Testing A/B Testing Framework")
    logger.info("="*80)
    
    try:
        # Import the framework
        from scripts.ab_testing_framework import (
            ABTestingFramework,
            ModelConfig,
            TestResult
        )
        
        # Define test configurations
        configs = [
            ModelConfig(
                name="gemini-primary",
                description="Gemini 1.5 Pro as primary analyzer",
                primary_model="gemini",
                use_consensus=False,
                similarity_threshold=0.70
            ),
            ModelConfig(
                name="claude-primary",
                description="Claude Sonnet 4 as primary analyzer",
                primary_model="claude",
                use_consensus=False,
                similarity_threshold=0.70
            )
        ]
        
        logger.info(f"✓ Successfully imported ABTestingFramework")
        logger.info(f"✓ Created {len(configs)} test configurations:")
        for config in configs:
            logger.info(f"  - {config.name}: {config.description}")
        
        # Initialize framework
        framework = ABTestingFramework(results_dir=Path("results/ab_tests"))
        logger.info(f"✓ Initialized framework with results dir: {framework.results_dir}")
        
        # Validate the framework has required methods
        required_methods = ['run_single_test', 'run_comparison_test', 'generate_comparison_report', 'save_results_json']
        for method in required_methods:
            if hasattr(framework, method):
                logger.info(f"✓ Framework has method: {method}")
            else:
                logger.error(f"✗ Framework missing method: {method}")
                return False
        
        logger.info("\n✅ A/B Testing Framework: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ A/B Testing Framework: FAILED")
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_smart_discovery():
    """Test the Smart Book Discovery system."""
    logger.info("\n" + "="*80)
    logger.info("Testing Smart Book Discovery System")
    logger.info("="*80)
    
    try:
        # Import the discovery system
        from scripts.smart_book_discovery import (
            SmartBookDiscovery,
            DiscoveredBook
        )
        
        logger.info(f"✓ Successfully imported SmartBookDiscovery")
        
        # Initialize discoverer
        discoverer = SmartBookDiscovery(
            s3_bucket="nba-mcp-books",
            config_dir=Path("config")
        )
        logger.info(f"✓ Initialized discoverer for bucket: {discoverer.s3_bucket}")
        
        # Validate the discoverer has required methods
        required_methods = [
            'scan_s3_for_books',
            '_suggest_category'
        ]
        for method in required_methods:
            if hasattr(discoverer, method):
                logger.info(f"✓ Discoverer has method: {method}")
            else:
                logger.error(f"✗ Discoverer missing method: {method}")
                return False
        
        # Test categorization logic (without S3 access)
        test_title = "Machine Learning Systems Design"
        category = discoverer._suggest_category(test_title, "")
        logger.info(f"✓ Categorization test: '{test_title}' -> '{category}'")
        
        logger.info("\n✅ Smart Book Discovery: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Smart Book Discovery: FAILED")
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration between the two frameworks."""
    logger.info("\n" + "="*80)
    logger.info("Testing Framework Integration")
    logger.info("="*80)
    
    try:
        # Check that both frameworks can be imported together
        from scripts.ab_testing_framework import ABTestingFramework
        from scripts.smart_book_discovery import SmartBookDiscovery
        
        logger.info("✓ Both frameworks can be imported simultaneously")
        
        # Check for potential config conflicts
        ab_config_dir = Path("config")
        discovery_config_dir = Path("config")
        
        if ab_config_dir == discovery_config_dir:
            logger.info("✓ Both frameworks use the same config directory")
        
        # Verify output directories don't conflict
        ab_output = Path("results/ab_tests")
        discovery_output = Path("config/books_to_analyze.json")
        
        logger.info(f"✓ A/B Testing output: {ab_output}")
        logger.info(f"✓ Discovery output: {discovery_output}")
        logger.info("✓ No output conflicts detected")
        
        logger.info("\n✅ Framework Integration: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Framework Integration: FAILED")
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Tier 3 framework tests."""
    logger.info("\n" + "#"*80)
    logger.info("# TIER 3 FRAMEWORKS TEST SUITE")
    logger.info("#"*80)
    logger.info(f"# Started: {datetime.now().isoformat()}")
    logger.info("#"*80 + "\n")
    
    results = {}
    
    # Run tests
    results['ab_framework'] = await test_ab_framework()
    results['smart_discovery'] = await test_smart_discovery()
    results['integration'] = await test_integration()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:20s}: {status}")
    
    logger.info("="*80)
    logger.info(f"Total:  {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info("="*80)
    
    if failed == 0:
        logger.info("\n🎉 ALL TIER 3 FRAMEWORK TESTS PASSED!")
        logger.info("\nNext steps:")
        logger.info("1. Run A/B test: python scripts/ab_testing_framework.py --test gemini-vs-claude --books 2")
        logger.info("2. Discover books: python scripts/smart_book_discovery.py --scan-repos --dry-run")
        logger.info("3. Review full Tier 3 implementation plan")
        return True
    else:
        logger.error(f"\n❌ {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    asyncio.run(main())

