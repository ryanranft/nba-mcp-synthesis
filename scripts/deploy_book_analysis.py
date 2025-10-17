#!/usr/bin/env python3
"""
Book Analysis Deployment Script

Main entry point for the multi-pass book analysis deployment.
Provides CLI interface and orchestrates the complete workflow.

Usage:
    python scripts/deploy_book_analysis.py [options]

Options:
    --config PATH          Path to books configuration file
    --pass PASS_NUM        Run specific pass only (1-4)
    --resume               Resume from last checkpoint
    --test                 Test with 2-3 books only
    --dry-run              Show what would be done without executing
    --help                 Show help message
"""

import argparse
import json
import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_pass_book_deployment import MultiPassOrchestrator

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("analysis_results/deployment.log"),
        ],
    )


def validate_config(config_path: str) -> bool:
    """Validate configuration file."""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return False

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        books = config.get("books", [])
        if not books:
            logger.error("No books found in configuration")
            return False

        logger.info(f"✅ Configuration valid: {len(books)} books found")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return False


def show_deployment_summary(config_path: str):
    """Show deployment summary without executing."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        books = config.get("books", [])
        metadata = config.get("metadata", {})

        print("\n" + "=" * 70)
        print("📚 BOOK ANALYSIS DEPLOYMENT SUMMARY")
        print("=" * 70)

        print(f"\n📖 Books to Process: {len(books)}")
        print(f"📊 Total Pages: {metadata.get('total_pages', 'Unknown')}")

        # Show book categories
        categories = metadata.get("categories", {})
        if categories:
            print(f"\n📂 Categories:")
            for category, count in categories.items():
                print(f"   - {category}: {count} books")

        # Show priorities
        priorities = metadata.get("priorities", {})
        if priorities:
            print(f"\n⭐ Priorities:")
            for priority, count in priorities.items():
                print(f"   - {priority}: {count} books")

        # Show analysis settings
        settings = config.get("analysis_settings", {})
        if settings:
            print(f"\n⚙️  Analysis Settings:")
            print(
                f"   - Convergence Threshold: {settings.get('convergence_threshold', 3)}"
            )
            print(f"   - Max Iterations: {settings.get('max_iterations', 15)}")
            print(f"   - Chunk Size: {settings.get('chunk_size', 50000)}")
            print(
                f"   - Strict Convergence: {settings.get('strict_convergence', True)}"
            )

        print(f"\n🔄 Deployment Phases:")
        print(f"   1. Pass 1: Individual book convergence analysis")
        print(f"   2. Pass 2: Context-aware re-analysis")
        print(f"   3. Pass 3: Recommendation consolidation")
        print(f"   4. Pass 4: NBA Simulator AWS integration")

        print(f"\n⏱️  Estimated Duration: 20-40 hours")
        print(f"💾 Checkpoint System: Enabled")
        print(f"📄 Progress Tracking: analysis_results/multi_pass_progress.json")

        print("\n" + "=" * 70)

    except Exception as e:
        logger.error(f"Error showing summary: {e}")


def run_specific_pass(orchestrator: MultiPassOrchestrator, pass_num: int) -> bool:
    """Run a specific pass only."""
    logger.info(f"🎯 Running Pass {pass_num} only")

    if pass_num == 1:
        return orchestrator.run_pass_1()
    elif pass_num == 2:
        return orchestrator.run_pass_2()
    elif pass_num == 3:
        return orchestrator.run_pass_3_consolidation()
    elif pass_num == 4:
        return orchestrator.run_pass_4_integration()
    else:
        logger.error(f"Invalid pass number: {pass_num}. Must be 1-4.")
        return False


def run_test_deployment(orchestrator: MultiPassOrchestrator) -> bool:
    """Run test deployment with 2-3 books only."""
    logger.info("🧪 Running test deployment with 2-3 books")

    # Modify config to only process first 3 books
    original_config = orchestrator.config.copy()
    test_books = original_config["books"][:3]
    orchestrator.config["books"] = test_books
    orchestrator.config["metadata"]["total_books"] = len(test_books)

    logger.info(f"📚 Test books: {[book['title'] for book in test_books]}")

    try:
        success = orchestrator.run_full_deployment()

        # Restore original config
        orchestrator.config = original_config

        return success

    except Exception as e:
        logger.error(f"Test deployment failed: {e}")
        # Restore original config
        orchestrator.config = original_config
        return False


def main():
    """Main deployment process."""
    parser = argparse.ArgumentParser(
        description="Deploy multi-pass book analysis workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/deploy_book_analysis.py                    # Full deployment
  python scripts/deploy_book_analysis.py --test             # Test with 2-3 books
  python scripts/deploy_book_analysis.py --pass-num 1       # Run Pass 1 only
  python scripts/deploy_book_analysis.py --resume           # Resume from checkpoint
  python scripts/deploy_book_analysis.py --dry-run          # Show summary only
        """,
    )

    parser.add_argument(
        "--config",
        default="config/books_to_analyze.json",
        help="Path to books configuration file (default: config/books_to_analyze.json)",
    )

    parser.add_argument(
        "--pass-num",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific pass only (1-4)",
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )

    parser.add_argument("--test", action="store_true", help="Test with 2-3 books only")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Validate configuration
    if not validate_config(args.config):
        return 1

    # Show dry run summary
    if args.dry_run:
        show_deployment_summary(args.config)
        return 0

    # Initialize orchestrator
    try:
        orchestrator = MultiPassOrchestrator(args.config)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        return 1

    # Execute based on arguments
    try:
        if args.pass_num:
            success = run_specific_pass(orchestrator, args.pass_num)
        elif args.test:
            success = run_test_deployment(orchestrator)
        else:
            success = orchestrator.run_full_deployment()

        if success:
            print("\n🎉 Deployment completed successfully!")
            print("📄 Check analysis_results/final_deployment_report.md for details")
            return 0
        else:
            print("\n❌ Deployment failed!")
            return 1

    except KeyboardInterrupt:
        logger.info("\n⏹️  Deployment interrupted by user")
        print("\n💾 Checkpoint saved. Use --resume to continue later.")
        return 1
    except Exception as e:
        logger.error(f"Deployment failed with exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
