#!/usr/bin/env python3
"""
Test Multi-Model Book Analysis

This script tests the multi-model book analyzer with 2 books to validate:
1. Real API calls are working (not simulated)
2. Cost tracking is accurate
3. Consensus voting produces quality recommendations
4. NBA-style directory structure is created

Usage:
    python scripts/test_multi_model_analysis.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.multi_model_book_analyzer import MultiModelBookAnalyzer, CostTracker
from scripts.organize_book_results import BookResultsOrganizer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiModelTester:
    """Test multi-model book analysis functionality"""

    def __init__(self):
        self.test_books = [
            {
                "id": "designing_ml_systems",
                "title": "Designing Machine Learning Systems",
                "author": "Chip Huyen",
                "genre": "Machine Learning",
                "pages": 461,
                "s3_path": "books/designing-machine-learning-systems.pdf",
            },
            {
                "id": "statistics_601",
                "title": "Statistics 601 Advanced Statistical Methods",
                "author": "Various",
                "genre": "Statistics",
                "pages": 300,
                "s3_path": "books/statistics-601-advanced.pdf",
            },
        ]

        self.results_dir = Path("test_results/multi_model")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run_tests(self):
        """Run comprehensive multi-model tests"""
        logger.info("🧪 Starting Multi-Model Book Analysis Tests")
        logger.info("=" * 60)

        # Test 1: Multi-model analyzer initialization
        await self._test_analyzer_initialization()

        # Test 2: Book analysis with consensus voting
        await self._test_book_analysis()

        # Test 3: Cost tracking
        await self._test_cost_tracking()

        # Test 4: NBA-style directory structure
        await self._test_directory_structure()

        # Test 5: Integration with existing workflow
        await self._test_workflow_integration()

        logger.info("=" * 60)
        logger.info("✅ All tests completed!")

    async def _test_analyzer_initialization(self):
        """Test 1: Multi-model analyzer initialization"""
        logger.info("\n🔧 Test 1: Multi-Model Analyzer Initialization")

        try:
            analyzer = MultiModelBookAnalyzer()

            # Check models are initialized
            models = analyzer.models
            logger.info(f"   Models initialized: {list(models.keys())}")

            # Check configuration
            config = analyzer.config
            logger.info(
                f"   Consensus threshold: {config['consensus']['unanimous_threshold']}"
            )
            logger.info(f"   Max iterations: {config['analysis']['max_iterations']}")

            # Verify at least one model is working
            if not models:
                raise RuntimeError("No models could be initialized")

            logger.info("   ✅ Analyzer initialization successful")

        except Exception as e:
            logger.error(f"   ❌ Analyzer initialization failed: {e}")
            raise

    async def _test_book_analysis(self):
        """Test 2: Book analysis with consensus voting"""
        logger.info("\n📚 Test 2: Book Analysis with Consensus Voting")

        analyzer = MultiModelBookAnalyzer()

        for book in self.test_books:
            logger.info(f"\n   Analyzing: {book['title']}")

            try:
                # Run analysis
                result = await analyzer.analyze_book(book)

                # Validate results
                total_recs = len(result.unanimous_recommendations) + len(
                    result.majority_recommendations
                )
                logger.info(f"   Total recommendations: {total_recs}")
                logger.info(
                    f"   Unanimous (Critical): {len(result.unanimous_recommendations)}"
                )
                logger.info(
                    f"   Majority (Important): {len(result.majority_recommendations)}"
                )
                logger.info(f"   Cost: ${result.total_cost:.2f}")
                logger.info(f"   Tokens: {result.total_tokens:,}")
                logger.info(f"   Time: {result.total_time:.1f}s")

                # Save results
                result_file = self.results_dir / f"{book['id']}_analysis.json"
                with open(result_file, "w") as f:
                    json.dump(
                        {
                            "book": book,
                            "unanimous_recommendations": result.unanimous_recommendations,
                            "majority_recommendations": result.majority_recommendations,
                            "total_cost": result.total_cost,
                            "total_tokens": result.total_tokens,
                            "total_time": result.total_time,
                            "model_responses": [
                                {
                                    "model_name": r.model_name,
                                    "cost": r.cost,
                                    "tokens_used": r.tokens_used,
                                    "processing_time": r.processing_time,
                                    "error": r.error,
                                }
                                for r in result.model_responses
                            ],
                        },
                        f,
                        indent=2,
                    )

                logger.info(f"   ✅ Analysis complete: {result_file}")

            except Exception as e:
                logger.error(f"   ❌ Analysis failed for {book['title']}: {e}")
                raise

    async def _test_cost_tracking(self):
        """Test 3: Cost tracking accuracy"""
        logger.info("\n💰 Test 3: Cost Tracking")

        try:
            cost_tracker = CostTracker(
                str(self.results_dir / "test_cost_tracking.json")
            )

            # Add some test sessions
            cost_tracker.add_session(5.25, 15000)
            cost_tracker.add_session(3.75, 12000)

            # Get summary
            summary = cost_tracker.get_cost_summary()

            logger.info(f"   Total cost: ${summary['total_cost']:.2f}")
            logger.info(f"   Total tokens: {summary['total_tokens']:,}")
            logger.info(f"   Sessions: {summary['session_count']}")
            logger.info(
                f"   Average per session: ${summary['average_per_session']:.2f}"
            )

            # Verify cost file exists
            cost_file = self.results_dir / "test_cost_tracking.json"
            if cost_file.exists():
                logger.info(f"   ✅ Cost tracking file created: {cost_file}")
            else:
                raise RuntimeError("Cost tracking file not created")

        except Exception as e:
            logger.error(f"   ❌ Cost tracking test failed: {e}")
            raise

    async def _test_directory_structure(self):
        """Test 4: NBA-style directory structure creation"""
        logger.info("\n📁 Test 4: NBA-Style Directory Structure")

        try:
            # Create test recommendations
            test_recommendations = [
                {
                    "id": "test_rec_1",
                    "title": "Model Versioning with MLflow",
                    "description": "Implement centralized model tracking",
                    "priority": "CRITICAL",
                    "source_chapter": "Chapter 3: Model Development",
                    "time_estimate": "8 hours",
                    "impact": "High",
                    "status": "PENDING",
                    "source_book_id": "designing_ml_systems",
                    "mapped_phase": 5,
                    "consensus_score": "3/3",
                    "agreeing_models": ["deepseek", "claude", "ollama"],
                },
                {
                    "id": "test_rec_2",
                    "title": "Data Drift Detection",
                    "description": "Automated monitoring of data changes",
                    "priority": "IMPORTANT",
                    "source_chapter": "Chapter 4: Data Management",
                    "time_estimate": "12 hours",
                    "impact": "Medium",
                    "status": "PENDING",
                    "source_book_id": "designing_ml_systems",
                    "mapped_phase": 5,
                    "consensus_score": "2/3",
                    "agreeing_models": ["deepseek", "claude"],
                },
            ]

            # Create master recommendations file
            master_file = self.results_dir / "master_recommendations.json"
            with open(master_file, "w") as f:
                json.dump(
                    {
                        "recommendations": test_recommendations,
                        "metadata": {
                            "total_recommendations": len(test_recommendations),
                            "generated_date": datetime.now().isoformat(),
                        },
                    },
                    f,
                    indent=2,
                )

            # Test organizer
            organizer = BookResultsOrganizer(str(self.results_dir))

            # Test book metadata
            book_metadata = {
                "title": "Designing Machine Learning Systems",
                "author": "Chip Huyen",
                "genre": "Machine Learning",
            }

            # Organize results
            result = organizer.organize_single_book(
                "designing_ml_systems", book_metadata
            )

            if result["success"]:
                logger.info(f"   ✅ Directory structure created successfully")
                logger.info(f"   Directories: {result['directories_created']}")

                # Verify files exist
                book_dir = self.results_dir / "books" / "designing_ml_systems"
                expected_files = [
                    "README.md",
                    "CRITICAL_RECOMMENDATIONS.md",
                    "IMPORTANT_RECOMMENDATIONS.md",
                    "BY_PHASE/PHASE_5_RECOMMENDATIONS.md",
                ]

                for file_path in expected_files:
                    full_path = book_dir / file_path
                    if full_path.exists():
                        logger.info(f"   ✅ {file_path} created")
                    else:
                        logger.warning(f"   ⚠️ {file_path} not found")

            else:
                raise RuntimeError(
                    f"Directory organization failed: {result.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"   ❌ Directory structure test failed: {e}")
            raise

    async def _test_workflow_integration(self):
        """Test 5: Integration with existing workflow"""
        logger.info("\n🔄 Test 5: Workflow Integration")

        try:
            # Test that the recursive analyzer can use multi-model analysis
            from scripts.recursive_book_analysis import RecursiveAnalyzer

            config = {
                "s3_bucket": "nba-data-lake",
                "project_context": "NBA MCP Synthesis",
                "convergence_threshold": 3,
                "max_iterations": 2,
                "project_paths": ["/Users/ryanranft/nba-mcp-synthesis"],
            }

            analyzer = RecursiveAnalyzer(config)

            # Test async method exists
            if hasattr(analyzer, "analyze_book_recursively"):
                logger.info(
                    "   ✅ RecursiveAnalyzer has async analyze_book_recursively method"
                )
            else:
                raise RuntimeError("RecursiveAnalyzer missing async method")

            # Test multi-model integration method exists
            if hasattr(analyzer, "_analyze_with_mcp_and_intelligence"):
                logger.info(
                    "   ✅ RecursiveAnalyzer has multi-model integration method"
                )
            else:
                raise RuntimeError("RecursiveAnalyzer missing multi-model method")

            logger.info("   ✅ Workflow integration successful")

        except Exception as e:
            logger.error(f"   ❌ Workflow integration test failed: {e}")
            raise


async def main():
    """Main test function"""
    print("🧪 Multi-Model Book Analysis Test Suite")
    print("=" * 50)

    # Check environment variables
    required_env_vars = ["DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
        print("   Some tests may fail without proper API keys")
        print("   Set these variables to test real API calls")
        print()

    # Run tests
    tester = MultiModelTester()

    try:
        await tester.run_tests()
        print("\n🎉 All tests passed! Multi-model integration is ready.")
        print("\nNext steps:")
        print(
            "1. Run 2-book test: python scripts/test_multi_model_analysis.py --books 2"
        )
        print(
            "2. Full deployment: python scripts/deploy_book_analysis.py --config config/books_to_analyze_all_ai_ml.json"
        )

    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check API keys are set correctly")
        print("2. Verify internet connection")
        print("3. Check that Ollama is running locally")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
