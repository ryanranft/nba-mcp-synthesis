#!/usr/bin/env python3
"""
Run Pass 5 Only - Implementation Generation

This script runs only Pass 5 of the multi-pass deployment to generate
implementation files for existing recommendations.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_pass_book_deployment import MultiPassOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_pass5_only():
    """Run only Pass 5: Implementation Generation"""

    print("🚀 Starting Pass 5 Only - Implementation Generation")
    print("="*60)

    # Create orchestrator
    orchestrator = MultiPassOrchestrator()

    # Check if prerequisites are met
    print("📋 Checking prerequisites...")

    # Check if master recommendations exist
    master_recs_path = "analysis_results/master_recommendations.json"
    if not os.path.exists(master_recs_path):
        print(f"❌ Master recommendations not found: {master_recs_path}")
        print("   Please run Passes 1-4 first to generate recommendations")
        return False

    # Check if consolidated recommendations exist (optional)
    consolidated_recs_path = "analysis_results/consolidated_recommendations.json"
    if not os.path.exists(consolidated_recs_path):
        print(f"⚠️  Consolidated recommendations not found: {consolidated_recs_path}")
        print("   Will use master recommendations directly")

    # Check if target directory exists
    target_dir = "/Users/ryanranft/nba-simulator-aws/docs/phases"
    if not os.path.exists(target_dir):
        print(f"❌ Target directory not found: {target_dir}")
        print("   Please ensure NBA Simulator AWS project exists")
        return False

    print("✅ Prerequisites met")
    print()

    # Run Pass 5
    print("⚙️  Running Pass 5: Implementation Generation...")
    success = await orchestrator.run_pass_5_implementation()

    if success:
        print("\n🎉 Pass 5 completed successfully!")

        # Show summary
        progress = orchestrator._load_progress()
        pass5_data = progress.get('pass_5', {})

        print(f"   Implementations Generated: {pass5_data.get('implementations_generated', 0)}")
        print(f"   Files Created: {pass5_data.get('files_created', 0)}")

        # Count actual files
        total_files = 0
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(('.py', '.sql', '.yaml', '.yml', '.md')):
                    total_files += 1

        print(f"   Total Implementation Files: {total_files}")

    else:
        print("\n❌ Pass 5 failed")
        return False

    return True

def main():
    """Main function"""
    try:
        # Run Pass 5
        success = asyncio.run(run_pass5_only())

        if success:
            print("\n✅ Pass 5 Only execution completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Pass 5 Only execution failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Pass 5 Only execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pass 5 Only execution failed: {e}")
        logger.error(f"Pass 5 execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
