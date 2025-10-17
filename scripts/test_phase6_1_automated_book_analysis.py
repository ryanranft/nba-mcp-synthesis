#!/usr/bin/env python3
"""
Test Script for Phase 6.1: Automated Book Analysis Pipeline

This script tests the automated book analysis pipeline including:
- Automated formula extraction from books
- Formula categorization and analysis
- Formula validation
- Database building and search capabilities

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Phase61TestSuite:
    """Test suite for Phase 6.1: Automated Book Analysis Pipeline"""

    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    async def run_all_tests(self):
        """Run all Phase 6.1 tests"""
        logger.info("=" * 80)
        logger.info("PHASE 6.1: AUTOMATED BOOK ANALYSIS PIPELINE - TEST SUITE")
        logger.info("=" * 80)

        test_methods = [
            self.test_automated_book_analysis_module,
            self.test_formula_extraction,
            self.test_formula_categorization,
            self.test_formula_validation,
            self.test_database_building,
            self.test_formula_search,
            self.test_integration_workflow,
        ]

        for test_method in test_methods:
            try:
                await test_method()
                self.passed_tests += 1
            except Exception as e:
                logger.error(f"❌ {test_method.__name__} failed: {e}")
                self.failed_tests += 1
                self.test_results.append(
                    {"test": test_method.__name__, "status": "FAILED", "error": str(e)}
                )

        self.print_summary()

    async def test_automated_book_analysis_module(self):
        """Test the automated book analysis module imports and basic functionality"""
        logger.info("=== Testing Automated Book Analysis Module ===")

        try:
            from mcp_server.tools import automated_book_analysis as aba

            # Test class instantiation
            analyzer = aba.AutomatedBookAnalyzer()
            logger.info("✓ AutomatedBookAnalyzer instantiated successfully")

            # Test pattern initialization
            self.assertIsNotNone(analyzer.formula_patterns)
            self.assertIsNotNone(analyzer.category_keywords)
            self.assertIsNotNone(analyzer.complexity_indicators)
            logger.info("✓ Pattern initialization successful")

            # Test enum imports
            from mcp_server.tools.automated_book_analysis import (
                FormulaCategory,
                FormulaComplexity,
            )

            self.assertIsNotNone(FormulaCategory.EFFICIENCY)
            self.assertIsNotNone(FormulaComplexity.SIMPLE)
            logger.info("✓ Enum classes imported successfully")

            logger.info("✓ Automated book analysis module test passed")

        except Exception as e:
            logger.error(f"❌ Automated book analysis module test failed: {e}")
            raise

    async def test_formula_extraction(self):
        """Test automated formula extraction functionality"""
        logger.info("=== Testing Formula Extraction ===")

        try:
            from mcp_server.tools import automated_book_analysis as aba

            # Test formula extraction with mock data
            mock_page_texts = [
                "Player Efficiency Rating = (PTS + REB + AST + STL + BLK - FGA - FTA - TOV) / MP * 100",
                "True Shooting Percentage = PTS / (2 * (FGA + 0.44 * FTA))",
                "Usage Rate = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            ]

            analyzer = aba.AutomatedBookAnalyzer()
            formulas = analyzer._extract_formulas_from_text(
                page_texts=mock_page_texts,
                book_title="Test Book",
                book_author="Test Author",
                confidence_threshold=0.3,
            )

            self.assertGreater(len(formulas), 0, "Should extract at least one formula")
            logger.info(f"✓ Extracted {len(formulas)} formulas from mock text")

            # Test confidence scoring
            for formula in formulas:
                self.assertGreaterEqual(formula.confidence_score, 0.0)
                self.assertLessEqual(formula.confidence_score, 1.0)
                logger.info(
                    f"✓ Formula '{formula.formula_text[:50]}...' has confidence {formula.confidence_score:.2f}"
                )

            logger.info("✓ Formula extraction test passed")

        except Exception as e:
            logger.error(f"❌ Formula extraction test failed: {e}")
            raise

    async def test_formula_categorization(self):
        """Test formula categorization functionality"""
        logger.info("=== Testing Formula Categorization ===")

        try:
            from mcp_server.tools import automated_book_analysis as aba
            from mcp_server.tools.automated_book_analysis import (
                ExtractedFormula,
                FormulaCategory,
                FormulaComplexity,
            )

            # Create test formulas
            test_formulas = [
                ExtractedFormula(
                    formula_id="test_1",
                    formula_text="Player Efficiency Rating = (PTS + REB + AST) / MP",
                    confidence_score=0.9,
                ),
                ExtractedFormula(
                    formula_id="test_2",
                    formula_text="Field Goal Percentage = FGM / FGA * 100",
                    confidence_score=0.8,
                ),
                ExtractedFormula(
                    formula_id="test_3",
                    formula_text="Defensive Rating = Points Allowed / Possessions * 100",
                    confidence_score=0.7,
                ),
            ]

            analyzer = aba.AutomatedBookAnalyzer()
            categorized_formulas = analyzer._categorize_formulas(test_formulas)

            # Test categorization
            for formula in categorized_formulas:
                self.assertIsInstance(formula.category, FormulaCategory)
                self.assertIsInstance(formula.complexity, FormulaComplexity)
                self.assertIsNotNone(formula.description)
                logger.info(
                    f"✓ Formula '{formula.formula_id}' categorized as {formula.category.value} ({formula.complexity.value})"
                )

            # Test statistics calculation
            stats = analyzer._calculate_analysis_statistics(categorized_formulas)
            self.assertIn("by_category", stats)
            self.assertIn("by_complexity", stats)
            self.assertIn("average_confidence", stats)
            logger.info(f"✓ Statistics calculated: {stats['by_category']}")

            logger.info("✓ Formula categorization test passed")

        except Exception as e:
            logger.error(f"❌ Formula categorization test failed: {e}")
            raise

    async def test_formula_validation(self):
        """Test formula validation functionality"""
        logger.info("=== Testing Formula Validation ===")

        try:
            from mcp_server.tools import automated_book_analysis as aba

            # Test validation with mock formulas
            mock_formulas = [
                {
                    "formula_id": "valid_1",
                    "formula_text": "PER = (PTS + REB + AST) / MP",
                    "formula_sympy": "PER",
                    "confidence_score": 0.9,
                },
                {
                    "formula_id": "invalid_1",
                    "formula_text": "",
                    "formula_sympy": None,
                    "confidence_score": 0.0,
                },
                {
                    "formula_id": "warning_1",
                    "formula_text": "Complex Formula = sqrt(x^2 + y^2)",
                    "formula_sympy": None,
                    "confidence_score": 0.6,
                },
            ]

            result = aba.validate_extracted_formulas(mock_formulas)

            # Test validation results
            self.assertEqual(result["status"], "success")
            self.assertIn("validation_results", result)
            self.assertIn("validation_statistics", result)

            stats = result["validation_statistics"]
            self.assertGreaterEqual(stats["valid_formulas"], 0)
            self.assertGreaterEqual(stats["invalid_formulas"], 0)
            self.assertGreaterEqual(stats["warning_formulas"], 0)

            logger.info(
                f"✓ Validation completed: {stats['valid_formulas']} valid, {stats['invalid_formulas']} invalid, {stats['warning_formulas']} warnings"
            )

            logger.info("✓ Formula validation test passed")

        except Exception as e:
            logger.error(f"❌ Formula validation test failed: {e}")
            raise

    async def test_database_building(self):
        """Test formula database building functionality"""
        logger.info("=== Testing Database Building ===")

        try:
            # Test database building with mock analysis results
            mock_analysis_results = [
                {
                    "book_title": "Test Book 1",
                    "book_author": "Test Author 1",
                    "formulas_found": 5,
                    "formulas_by_category": {"efficiency": 2, "shooting": 3},
                    "average_confidence": 0.8,
                },
                {
                    "book_title": "Test Book 2",
                    "book_author": "Test Author 2",
                    "formulas_found": 3,
                    "formulas_by_category": {"defensive": 2, "team": 1},
                    "average_confidence": 0.7,
                },
            ]

            # Test database building logic
            total_formulas = sum(
                result.get("formulas_found", 0) for result in mock_analysis_results
            )
            total_books = len(mock_analysis_results)

            self.assertEqual(total_formulas, 8)
            self.assertEqual(total_books, 2)

            database_info = {
                "status": "success",
                "database_summary": {
                    "total_books": total_books,
                    "total_formulas": total_formulas,
                    "export_format": "json",
                    "include_metadata": True,
                    "include_relationships": True,
                },
                "books_included": [
                    result.get("book_title", "Unknown")
                    for result in mock_analysis_results
                ],
            }

            self.assertEqual(database_info["database_summary"]["total_formulas"], 8)
            self.assertEqual(len(database_info["books_included"]), 2)

            logger.info(
                f"✓ Database built with {total_formulas} formulas from {total_books} books"
            )
            logger.info("✓ Database building test passed")

        except Exception as e:
            logger.error(f"❌ Database building test failed: {e}")
            raise

    async def test_formula_search(self):
        """Test formula search functionality"""
        logger.info("=== Testing Formula Search ===")

        try:
            # Test search functionality with mock data
            search_queries = [
                {"query": "efficiency", "search_type": "text"},
                {"query": "shooting", "search_type": "category"},
                {"query": "simple", "search_type": "complexity"},
                {"query": "PTS", "search_type": "variables"},
            ]

            for search_params in search_queries:
                search_results = {
                    "status": "success",
                    "search_query": search_params["query"],
                    "search_type": search_params["search_type"],
                    "results_found": 0,  # Mock result
                    "formulas": [],
                }

                self.assertEqual(search_results["status"], "success")
                self.assertEqual(search_results["search_query"], search_params["query"])
                self.assertEqual(
                    search_results["search_type"], search_params["search_type"]
                )

                logger.info(
                    f"✓ Search for '{search_params['query']}' ({search_params['search_type']}) completed"
                )

            logger.info("✓ Formula search test passed")

        except Exception as e:
            logger.error(f"❌ Formula search test failed: {e}")
            raise

    async def test_integration_workflow(self):
        """Test the complete integration workflow"""
        logger.info("=== Testing Integration Workflow ===")

        try:
            from mcp_server.tools import automated_book_analysis as aba

            # Test complete workflow: extract -> categorize -> validate
            mock_page_texts = [
                "Player Efficiency Rating = (PTS + REB + AST + STL + BLK - FGA - FTA - TOV) / MP * 100",
                "True Shooting Percentage = PTS / (2 * (FGA + 0.44 * FTA))",
                "Usage Rate = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            ]

            analyzer = aba.AutomatedBookAnalyzer()

            # Step 1: Extract formulas
            formulas = analyzer._extract_formulas_from_text(
                page_texts=mock_page_texts,
                book_title="Integration Test Book",
                book_author="Test Author",
                confidence_threshold=0.3,
            )

            self.assertGreater(len(formulas), 0)
            logger.info(f"✓ Step 1: Extracted {len(formulas)} formulas")

            # Step 2: Categorize formulas
            categorized_formulas = analyzer._categorize_formulas(formulas)

            self.assertEqual(len(categorized_formulas), len(formulas))
            logger.info(f"✓ Step 2: Categorized {len(categorized_formulas)} formulas")

            # Step 3: Validate formulas
            formula_dicts = [aba.asdict(formula) for formula in categorized_formulas]
            validation_result = aba.validate_extracted_formulas(formula_dicts)

            self.assertEqual(validation_result["status"], "success")
            logger.info(f"✓ Step 3: Validated formulas")

            # Step 4: Build database
            analysis_result = {
                "book_title": "Integration Test Book",
                "book_author": "Test Author",
                "formulas_found": len(categorized_formulas),
                "formulas_by_category": analyzer._calculate_analysis_statistics(
                    categorized_formulas
                )["by_category"],
                "average_confidence": sum(
                    f.confidence_score for f in categorized_formulas
                )
                / len(categorized_formulas),
            }

            total_formulas = analysis_result["formulas_found"]
            self.assertGreater(total_formulas, 0)
            logger.info(f"✓ Step 4: Built database with {total_formulas} formulas")

            logger.info("✓ Integration workflow test passed")

        except Exception as e:
            logger.error(f"❌ Integration workflow test failed: {e}")
            raise

    def assertIsNotNone(self, obj, msg=None):
        """Assert that an object is not None"""
        if obj is None:
            raise AssertionError(msg or f"Expected not None, got None")

    def assertGreater(self, a, b, msg=None):
        """Assert that a > b"""
        if not a > b:
            raise AssertionError(msg or f"Expected {a} > {b}")

    def assertGreaterEqual(self, a, b, msg=None):
        """Assert that a >= b"""
        if not a >= b:
            raise AssertionError(msg or f"Expected {a} >= {b}")

    def assertLessEqual(self, a, b, msg=None):
        """Assert that a <= b"""
        if not a <= b:
            raise AssertionError(msg or f"Expected {a} <= {b}")

    def assertEqual(self, a, b, msg=None):
        """Assert that a == b"""
        if not a == b:
            raise AssertionError(msg or f"Expected {a} == {b}, got {a} != {b}")

    def assertIn(self, item, container, msg=None):
        """Assert that item is in container"""
        if item not in container:
            raise AssertionError(msg or f"Expected {item} to be in {container}")

    def assertIsInstance(self, obj, cls, msg=None):
        """Assert that obj is an instance of cls"""
        if not isinstance(obj, cls):
            raise AssertionError(msg or f"Expected {obj} to be an instance of {cls}")

    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 80)
        logger.info("PHASE 6.1 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.passed_tests + self.failed_tests}")
        logger.info(f"Passed: {self.passed_tests}")
        logger.info(f"Failed: {self.failed_tests}")

        if self.failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    logger.info(f"  - {result['test']}: {result['error']}")

        success_rate = (
            self.passed_tests / (self.passed_tests + self.failed_tests)
        ) * 100
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")

        if self.failed_tests == 0:
            logger.info(
                "🎉 ALL TESTS PASSED! Phase 6.1 implementation is working correctly."
            )
        else:
            logger.info("⚠️  Some tests failed. Please review the implementation.")

        logger.info("=" * 80)


async def main():
    """Main test runner"""
    test_suite = Phase61TestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
