#!/usr/bin/env python3
"""
Simplified Resilient Recursive Book Analysis
Uses only working APIs (Google + DeepSeek) with aggressive timeouts.
"""

import os
import sys
import asyncio
import logging
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.resilient_book_analyzer import ResilientBookAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedRecursiveAnalyzer:
    """Simplified recursive analyzer using only working APIs."""

    def __init__(self, config_file: str, output_dir: str):
        self.config_file = config_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.books = self.config.get('books', [])
        logger.info(f"📚 Loaded {len(self.books)} books from config")

        # Initialize analyzer
        self.analyzer = ResilientBookAnalyzer()

        # Load existing recommendations
        self.master_recs_file = self.output_dir / "master_recommendations.json"
        self.master_recommendations = self._load_master_recommendations()

    def _load_master_recommendations(self) -> Dict[str, Any]:
        """Load existing master recommendations."""
        if self.master_recs_file.exists():
            with open(self.master_recs_file, 'r') as f:
                data = json.load(f)
                # Ensure required keys exist
                if 'total_cost' not in data:
                    data['total_cost'] = 0.0
                if 'total_books' not in data:
                    data['total_books'] = 0
                return data
        else:
            return {
                'recommendations': [],
                'total_cost': 0.0,
                'total_books': 0,
                'last_updated': None
            }

    def _save_master_recommendations(self):
        """Save master recommendations to file."""
        self.master_recommendations['last_updated'] = datetime.now().isoformat()
        with open(self.master_recs_file, 'w') as f:
            json.dump(self.master_recommendations, f, indent=2)

    async def analyze_book(self, book: Dict[str, Any]) -> bool:
        """Analyze a single book."""
        book_title = book.get('title', 'Unknown')
        logger.info(f"📖 Analyzing: {book_title}")

        try:
            # Run analysis with timeout
            result = await asyncio.wait_for(
                self.analyzer.analyze_book(book),
                timeout=300  # 5 minute timeout per book
            )

            if result.success:
                # Add recommendations to master list
                for rec in result.recommendations:
                    rec['book_title'] = book_title
                    rec['analysis_date'] = datetime.now().isoformat()
                    self.master_recommendations['recommendations'].append(rec)

                # Update totals
                self.master_recommendations['total_cost'] += result.total_cost
                self.master_recommendations['total_books'] += 1

                logger.info(f"✅ {book_title}: {len(result.recommendations)} recommendations, ${result.total_cost:.4f}")
                return True
            else:
                logger.error(f"❌ {book_title}: Analysis failed - {result.error}")
                return False

        except asyncio.TimeoutError:
            logger.error(f"❌ {book_title}: Analysis timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ {book_title}: Analysis failed - {str(e)}")
            return False

    async def _run_multi_pass_deployment(self):
        """Run multi-pass deployment after all books analyzed."""
        logger.info("\n" + "="*60)
        logger.info("🔄 Starting Multi-Pass Deployment")
        logger.info("="*60)

        try:
            from multi_pass_book_deployment import MultiPassOrchestrator

            orchestrator = MultiPassOrchestrator()

            # Run full deployment (Passes 1-5)
            success = await orchestrator.run_full_deployment()

            if success:
                logger.info("✅ Multi-pass deployment completed successfully")
                return True
            else:
                logger.error("❌ Multi-pass deployment failed")
                return False

        except Exception as e:
            logger.error(f"❌ Multi-pass deployment error: {e}")
            return False

    async def analyze_all_books(self):
        """Analyze all books in the configuration."""
        logger.info(f"🚀 Starting analysis of {len(self.books)} books...")

        successful = 0
        failed = 0

        for i, book in enumerate(self.books, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Book {i}/{len(self.books)}: {book.get('title', 'Unknown')}")
            logger.info(f"{'='*60}")

            success = await self.analyze_book(book)

            if success:
                successful += 1
            else:
                failed += 1

            # Save progress after each book
            self._save_master_recommendations()

            logger.info(f"📊 Progress: {successful} successful, {failed} failed")

        logger.info(f"\n🎉 Analysis complete!")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"💰 Total cost: ${self.master_recommendations['total_cost']:.4f}")
        logger.info(f"📋 Total recommendations: {len(self.master_recommendations['recommendations'])}")

        # NEW: Trigger multi-pass deployment
        if successful > 0:
            logger.info("\n🚀 Triggering multi-pass deployment...")
            deployment_success = await self._run_multi_pass_deployment()
            if deployment_success:
                logger.info("✅ Complete workflow finished: Books analyzed → Recommendations integrated → Implementation files generated")
            else:
                logger.warning("⚠️ Multi-pass deployment had issues, but book analysis completed")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Simplified Resilient Book Analysis')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--book', help='Analyze specific book by title')

    args = parser.parse_args()

    analyzer = SimplifiedRecursiveAnalyzer(args.config, args.output_dir)

    if args.book:
        # Analyze specific book
        book = next((b for b in analyzer.books if b.get('title') == args.book), None)
        if book:
            await analyzer.analyze_book(book)
            analyzer._save_master_recommendations()
        else:
            logger.error(f"Book '{args.book}' not found in configuration")
    else:
        # Analyze all books
        await analyzer.analyze_all_books()

if __name__ == "__main__":
    asyncio.run(main())
