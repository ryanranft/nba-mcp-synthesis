#!/usr/bin/env python3
"""
Pass 5 Implementation Generation with Circuit Breaker
Runs Pass 5 with timeout protection and circuit breaker patterns
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


class CircuitBreaker:
    """Circuit breaker pattern for handling failures."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self):
        """Check if execution is allowed."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if datetime.now().timestamp() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = 'CLOSED'

    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"🔴 Circuit breaker OPENED after {self.failure_count} failures")


async def run_pass5_with_circuit_breaker():
    """Run Pass 5 implementation generation with circuit breaker protection."""

    logger.info("🚀 Starting Pass 5 Implementation Generation with Circuit Breaker")
    logger.info("=" * 70)

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
            mcp_server_url="http://localhost:8000",
            output_base="/Users/ryanranft/nba-simulator-aws/docs/phases",
            templates_dir="templates"
        )
        logger.info("✅ Generator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize generator: {e}")
        return False

    # Initialize circuit breaker
    circuit_breaker = CircuitBreaker(failure_threshold=10, timeout=120)  # 10 failures, 2 min timeout

    implementations_generated = 0
    files_created = 0
    skipped_due_to_circuit_breaker = 0

    # Process recommendations with circuit breaker protection
    for i, rec in enumerate(recommendations):
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"🔴 Circuit breaker OPEN - skipping recommendation {i+1}/{len(recommendations)}")
            skipped_due_to_circuit_breaker += 1
            continue

        try:
            logger.info(f"🔧 Processing recommendation {i+1}/{len(recommendations)}: {rec.get('title', 'Untitled')}")

            # Get phase from recommendation
            phase = rec.get('phase', 0)

            # Set timeout for each recommendation (60 seconds)
            try:
                result = await asyncio.wait_for(
                    generator.generate_files_for_recommendation(rec, phase),
                    timeout=60.0
                )

                if result.get('generated_files'):
                    implementations_generated += 1
                    files_created += len(result.get('generated_files', []))
                    circuit_breaker.on_success()
                    logger.info(f"✅ Generated {len(result.get('generated_files', []))} files")
                else:
                    circuit_breaker.on_failure()
                    logger.warning(f"⚠️ Failed to generate implementation: {result.get('errors', ['Unknown error'])}")

            except asyncio.TimeoutError:
                circuit_breaker.on_failure()
                logger.error(f"⏰ Timeout processing recommendation: {rec.get('title', 'Untitled')}")
                continue
            except Exception as e:
                circuit_breaker.on_failure()
                logger.error(f"❌ Error processing recommendation: {e}")
                continue

        except Exception as e:
            circuit_breaker.on_failure()
            logger.error(f"❌ Error generating implementation for {rec.get('title', 'Untitled')}: {e}")
            continue

        # Progress update every 20 recommendations
        if (i + 1) % 20 == 0:
            logger.info(f"📊 Progress: {i+1}/{len(recommendations)} processed, {implementations_generated} successful")

    # Final results
    logger.info("\n" + "=" * 70)
    logger.info("📊 Pass 5 Implementation Generation Results:")
    logger.info(f"   Total recommendations: {len(recommendations)}")
    logger.info(f"   Implementations generated: {implementations_generated}")
    logger.info(f"   Files created: {files_created}")
    logger.info(f"   Skipped (circuit breaker): {skipped_due_to_circuit_breaker}")
    logger.info(f"   Success rate: {implementations_generated/len(recommendations)*100:.1f}%")
    logger.info(f"   Circuit breaker state: {circuit_breaker.state}")

    # Update progress file
    progress_path = "analysis_results/multi_pass_progress.json"
    if os.path.exists(progress_path):
        with open(progress_path, 'r') as f:
            progress = json.load(f)

        progress['pass_5']['status'] = 'completed'
        progress['pass_5']['implementations_generated'] = implementations_generated
        progress['pass_5']['files_created'] = files_created
        progress['pass_5']['end_time'] = datetime.now().isoformat()

        with open(progress_path, 'w') as f:
            json.dump(progress, f, indent=2)

        logger.info("💾 Progress file updated")

    if implementations_generated > 0:
        logger.info("✅ Pass 5 implementation generation completed successfully!")
        return True
    else:
        logger.error("❌ Pass 5 implementation generation failed - no implementations generated")
        return False


async def main():
    """Main function with overall timeout."""
    try:
        success = await asyncio.wait_for(run_pass5_with_circuit_breaker(), timeout=1800.0)  # 30 minute total timeout
        return 0 if success else 1
    except asyncio.TimeoutError:
        logger.error("⏰ Overall timeout (30 minutes)")
        return 1
    except Exception as e:
        logger.error(f"❌ Pass 5 failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

