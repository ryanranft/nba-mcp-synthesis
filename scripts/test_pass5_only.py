#!/usr/bin/env python3
"""
Test Pass 5 Implementation Generation Only
Quick test to verify Pass 5 works without running full deployment
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_implementation_files import MCPImplementationGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pass5_with_timeout():
    """Test Pass 5 implementation generation with timeout protection."""

    logger.info("🧪 Testing Pass 5 Implementation Generation")
    logger.info("=" * 50)

    # Load recommendations
    master_recs_path = "analysis_results/master_recommendations.json"
    if not os.path.exists(master_recs_path):
        logger.error(f"❌ Master recommendations file not found: {master_recs_path}")
        return False

    with open(master_recs_path, 'r') as f:
        data = json.load(f)
        recommendations = data.get('recommendations', [])

    logger.info(f"📋 Loaded {len(recommendations)} recommendations")

    if not recommendations:
        logger.error("❌ No recommendations found")
        return False

    # Initialize generator
    try:
        generator = MCPImplementationGenerator(
            mcp_server_url="http://localhost:8000",  # Default MCP server
            output_base="/Users/ryanranft/nba-simulator-aws/docs/phases",
            templates_dir="templates"
        )
        logger.info("✅ Generator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize generator: {e}")
        return False

    # Test with first 3 recommendations only
    test_recommendations = recommendations[:3]
    logger.info(f"🔧 Testing with {len(test_recommendations)} recommendations")

    implementations_generated = 0
    files_created = 0

    # Process recommendations with timeout protection
    for i, rec in enumerate(test_recommendations):
        try:
            logger.info(f"🔧 Processing recommendation {i+1}/{len(test_recommendations)}: {rec.get('title', 'Untitled')}")

            # Get phase from recommendation
            phase = rec.get('phase', 0)

            # Set timeout for each recommendation (30 seconds)
            try:
                result = await asyncio.wait_for(
                    generator.generate_files_for_recommendation(rec, phase),
                    timeout=30.0
                )

                if result.get('generated_files'):
                    implementations_generated += 1
                    files_created += len(result.get('generated_files', []))
                    logger.info(f"✅ Generated {len(result.get('generated_files', []))} files")
                else:
                    logger.warning(f"⚠️ Failed to generate implementation: {result.get('errors', ['Unknown error'])}")

            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout processing recommendation: {rec.get('title', 'Untitled')}")
                continue
            except Exception as e:
                logger.error(f"❌ Error processing recommendation: {e}")
                continue

        except Exception as e:
            logger.error(f"❌ Error generating implementation for {rec.get('title', 'Untitled')}: {e}")
            continue

    # Results
    logger.info("\n" + "=" * 50)
    logger.info("📊 Pass 5 Test Results:")
    logger.info(f"   Implementations generated: {implementations_generated}")
    logger.info(f"   Files created: {files_created}")
    logger.info(f"   Success rate: {implementations_generated/len(test_recommendations)*100:.1f}%")

    if implementations_generated > 0:
        logger.info("✅ Pass 5 test completed successfully!")
        return True
    else:
        logger.error("❌ Pass 5 test failed - no implementations generated")
        return False


async def main():
    """Main test function."""
    try:
        success = await asyncio.wait_for(test_pass5_with_timeout(), timeout=300.0)  # 5 minute total timeout
        return 0 if success else 1
    except asyncio.TimeoutError:
        logger.error("⏰ Overall test timeout (5 minutes)")
        return 1
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

