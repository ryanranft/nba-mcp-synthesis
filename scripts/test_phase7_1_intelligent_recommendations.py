#!/usr/bin/env python3
"""
Phase 7.1: Intelligent Formula Recommendations - Test Suite

This script tests the intelligent formula recommendations system including:
- Context-aware recommendations
- Data pattern-based suggestions
- User context analysis
- Predictive analytics recommendations
- Error detection and correction
"""

import sys
import os
import unittest
import time
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_server.tools.intelligent_recommendations import (
    IntelligentRecommendationEngine,
    get_intelligent_recommendations,
    suggest_formulas_from_data_patterns,
    analyze_user_context_for_recommendations,
    get_predictive_analytics_recommendations,
    detect_and_correct_formula_errors,
    RecommendationContext,
    UserContext,
    UserExpertiseLevel,
    RecommendationType,
)


class Phase71TestSuite(unittest.TestCase):
    """Test suite for Phase 7.1: Intelligent Formula Recommendations"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = IntelligentRecommendationEngine()
        print(
            f"✓ Test suite initialized with {len(self.engine.formula_database)} formulas"
        )

    def test_intelligent_recommendations_basic(self):
        """Test basic intelligent recommendations"""
        print("Testing basic intelligent recommendations...")

        # Test context-aware recommendations
        context = RecommendationContext(
            user_query="I want to analyze player shooting efficiency",
            analysis_type="shooting",
        )

        recommendations = self.engine.get_intelligent_recommendations(
            context, max_recommendations=3, confidence_threshold=0.5
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Check recommendation structure
        for rec in recommendations:
            self.assertIsInstance(rec.formula_id, str)
            self.assertIsInstance(rec.formula_name, str)
            self.assertIsInstance(rec.confidence_score, float)
            self.assertGreaterEqual(rec.confidence_score, 0.5)
            self.assertIsInstance(rec.explanation, str)

        print(f"✓ Generated {len(recommendations)} recommendations")
        print("✓ Basic intelligent recommendations test passed")

    def test_data_pattern_suggestions(self):
        """Test data pattern-based suggestions"""
        print("Testing data pattern-based suggestions...")

        # Test with shooting data
        suggestions = self.engine.suggest_formulas_from_data(
            data_description="Player shooting statistics including field goals, 3-pointers, and free throws",
            available_variables=["FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "PTS"],
            target_metric="shooting_efficiency",
            formula_complexity="moderate",
            max_suggestions=3,
        )

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

        # Check that suggestions use available variables
        for suggestion in suggestions:
            self.assertIsInstance(suggestion.formula_id, str)
            self.assertIsInstance(suggestion.confidence_score, float)
            self.assertGreater(suggestion.confidence_score, 0.0)

        print(f"✓ Generated {len(suggestions)} data-based suggestions")
        print("✓ Data pattern suggestions test passed")

    def test_user_context_analysis(self):
        """Test user context analysis"""
        print("Testing user context analysis...")

        # Test context analysis
        analysis = self.engine.analyze_user_context(
            user_query="I need to compare defensive performance between teams",
            session_history=[
                {"formula_id": "defensive_rating", "timestamp": "2024-01-01"},
                {"formula_id": "steal_pct", "timestamp": "2024-01-01"},
            ],
            current_analysis="team comparison",
            user_expertise_level="intermediate",
        )

        self.assertIsInstance(analysis, dict)
        self.assertIn("keywords", analysis)
        self.assertIn("analysis_type", analysis)
        self.assertIn("complexity_preference", analysis)
        self.assertIn("preferred_categories", analysis)

        # Check that defensive analysis is detected
        self.assertIn("defensive", analysis["preferred_categories"])
        self.assertEqual(analysis["analysis_type"], "defensive")

        print("✓ User context analysis test passed")

    def test_predictive_recommendations(self):
        """Test predictive analytics recommendations"""
        print("Testing predictive analytics recommendations...")

        # Test predictive recommendations
        recommendations = self.engine.get_predictive_recommendations(
            prediction_target="team_wins",
            historical_data_description="Team performance data including offensive and defensive ratings",
            prediction_horizon="medium_term",
            confidence_level=0.95,
        )

        self.assertIsInstance(recommendations, list)

        # Check that recommendations are suitable for prediction
        for rec in recommendations:
            self.assertIsInstance(rec.formula_id, str)
            self.assertIsInstance(rec.confidence_score, float)
            self.assertIn("predict", rec.explanation.lower())

        print(f"✓ Generated {len(recommendations)} predictive recommendations")
        print("✓ Predictive recommendations test passed")

    def test_error_detection(self):
        """Test error detection and correction"""
        print("Testing error detection and correction...")

        # Test with valid formula
        valid_analysis = self.engine.detect_and_correct_errors(
            formula_expression="FGM / FGA",
            expected_result=0.5,
            input_values={"FGM": 10, "FGA": 20},
            error_tolerance=0.01,
        )

        self.assertIsInstance(valid_analysis, dict)
        self.assertIn("has_errors", valid_analysis)
        self.assertIn("confidence", valid_analysis)
        self.assertFalse(valid_analysis["has_errors"])
        self.assertGreater(valid_analysis["confidence"], 0.5)

        # Test with invalid formula
        invalid_analysis = self.engine.detect_and_correct_errors(
            formula_expression="FGM // FGA",  # Invalid integer division
            expected_result=0.5,
            input_values={"FGM": 10, "FGA": 20},
            error_tolerance=0.01,
        )

        self.assertTrue(invalid_analysis["has_errors"])
        self.assertIn("integer_division", invalid_analysis["error_types"])
        self.assertGreater(len(invalid_analysis["correction_suggestions"]), 0)

        print("✓ Error detection test passed")

    def test_standalone_functions(self):
        """Test standalone functions for MCP tools"""
        print("Testing standalone functions...")

        # Test get_intelligent_recommendations
        result = get_intelligent_recommendations(
            context="Analyze player efficiency",
            analysis_type="efficiency",
            max_recommendations=3,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIn("recommendations", result)
        self.assertGreater(result["total_recommendations"], 0)

        # Test suggest_formulas_from_data_patterns
        suggestions = suggest_formulas_from_data_patterns(
            data_description="Player statistics",
            available_variables=["PTS", "REB", "AST"],
            max_suggestions=2,
        )

        self.assertIsInstance(suggestions, dict)
        self.assertEqual(suggestions["status"], "success")
        self.assertIn("suggestions", suggestions)

        # Test analyze_user_context_for_recommendations
        context_analysis = analyze_user_context_for_recommendations(
            user_query="Compare team performance", user_expertise_level="advanced"
        )

        self.assertIsInstance(context_analysis, dict)
        self.assertEqual(context_analysis["status"], "success")
        self.assertIn("context_analysis", context_analysis)

        # Test get_predictive_analytics_recommendations
        predictive_recs = get_predictive_analytics_recommendations(
            prediction_target="player_performance",
            historical_data_description="Player stats over multiple seasons",
        )

        self.assertIsInstance(predictive_recs, dict)
        self.assertEqual(predictive_recs["status"], "success")
        self.assertIn("recommendations", predictive_recs)

        # Test detect_and_correct_formula_errors
        error_analysis = detect_and_correct_formula_errors(
            formula_expression="PTS / GAMES", input_values={"PTS": 100, "GAMES": 10}
        )

        self.assertIsInstance(error_analysis, dict)
        self.assertEqual(error_analysis["status"], "success")
        self.assertIn("error_analysis", error_analysis)

        print("✓ Standalone functions test passed")

    def test_recommendation_quality(self):
        """Test recommendation quality and relevance"""
        print("Testing recommendation quality...")

        # Test shooting analysis recommendations
        shooting_context = RecommendationContext(
            user_query="I want to analyze 3-point shooting performance",
            analysis_type="shooting",
        )

        shooting_recs = self.engine.get_intelligent_recommendations(
            shooting_context, max_recommendations=5
        )

        # Check that shooting-related formulas are recommended
        shooting_formulas = [
            rec
            for rec in shooting_recs
            if "shooting" in rec.recommendation_type.value
            or "3pt" in rec.formula_id.lower()
        ]
        self.assertGreater(len(shooting_formulas), 0)

        # Test defensive analysis recommendations
        defensive_context = RecommendationContext(
            user_query="Analyze team defensive performance", analysis_type="defensive"
        )

        defensive_recs = self.engine.get_intelligent_recommendations(
            defensive_context, max_recommendations=5
        )

        # Check that defensive formulas are recommended
        defensive_formulas = [
            rec
            for rec in defensive_recs
            if "defensive" in rec.recommendation_type.value
        ]
        self.assertGreater(len(defensive_formulas), 0)

        print("✓ Recommendation quality test passed")

    def test_expertise_level_adaptation(self):
        """Test adaptation to user expertise level"""
        print("Testing expertise level adaptation...")

        # Test beginner recommendations
        beginner_context = RecommendationContext(
            user_query="Simple player analysis",
            user_context=UserContext(expertise_level=UserExpertiseLevel.BEGINNER),
        )

        beginner_recs = self.engine.get_intelligent_recommendations(
            beginner_context, max_recommendations=3
        )

        # Check that simple formulas are recommended for beginners
        simple_recs = [rec for rec in beginner_recs if rec.complexity_level == "simple"]
        self.assertGreater(len(simple_recs), 0)

        # Test expert recommendations
        expert_context = RecommendationContext(
            user_query="Advanced analytics analysis",
            user_context=UserContext(expertise_level=UserExpertiseLevel.EXPERT),
        )

        expert_recs = self.engine.get_intelligent_recommendations(
            expert_context, max_recommendations=3
        )

        # Check that complex formulas are recommended for experts
        complex_recs = [rec for rec in expert_recs if rec.complexity_level == "complex"]
        self.assertGreater(len(complex_recs), 0)

        print("✓ Expertise level adaptation test passed")

    def test_performance_metrics(self):
        """Test performance and scalability"""
        print("Testing performance metrics...")

        start_time = time.time()

        # Test bulk recommendations
        contexts = [
            RecommendationContext(
                user_query=f"Analysis {i}", analysis_type="efficiency"
            )
            for i in range(10)
        ]

        all_recommendations = []
        for context in contexts:
            recs = self.engine.get_intelligent_recommendations(
                context, max_recommendations=3
            )
            all_recommendations.extend(recs)

        bulk_time = time.time() - start_time

        # Test search performance
        search_start = time.time()
        search_result = suggest_formulas_from_data_patterns(
            data_description="Comprehensive player statistics",
            available_variables=[
                "PTS",
                "REB",
                "AST",
                "STL",
                "BLK",
                "TOV",
                "FGM",
                "FGA",
                "FTM",
                "FTA",
            ],
            max_suggestions=5,
        )
        search_time = time.time() - search_start

        self.assertLess(bulk_time, 5.0)  # Should complete within 5 seconds
        self.assertLess(search_time, 2.0)  # Search should complete within 2 seconds
        self.assertGreater(len(all_recommendations), 0)

        print(
            f"✓ Performance test passed (bulk: {bulk_time:.2f}s, search: {search_time:.2f}s)"
        )

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling...")

        # Test with empty context
        empty_result = get_intelligent_recommendations(context="", analysis_type="all")

        self.assertEqual(empty_result["status"], "error")

        # Test with invalid analysis type
        invalid_result = get_intelligent_recommendations(
            context="Test analysis", analysis_type="invalid_type"
        )

        # Should still work but with default behavior
        self.assertIsInstance(invalid_result, dict)

        # Test with no available variables
        no_vars_result = suggest_formulas_from_data_patterns(
            data_description="Test data", available_variables=[], max_suggestions=3
        )

        self.assertEqual(no_vars_result["status"], "error")

        print("✓ Error handling test passed")

    def test_formula_database_integration(self):
        """Test integration with formula database"""
        print("Testing formula database integration...")

        # Check that formula database is loaded
        self.assertGreater(len(self.engine.formula_database), 0)

        # Check that embeddings are built
        self.assertIsNotNone(self.engine.formula_embeddings)

        # Test that recommendations use actual formulas
        context = RecommendationContext(
            user_query="Player efficiency analysis", analysis_type="efficiency"
        )

        recommendations = self.engine.get_intelligent_recommendations(
            context, max_recommendations=5
        )

        for rec in recommendations:
            self.assertIn(rec.formula_id, self.engine.formula_database)
            formula_info = self.engine.formula_database[rec.formula_id]
            self.assertEqual(rec.formula_name, formula_info["name"])
            self.assertEqual(rec.formula_expression, formula_info["expression"])

        print("✓ Formula database integration test passed")


def run_tests():
    """Run all tests and display results"""
    print("=" * 60)
    print("PHASE 7.1: INTELLIGENT FORMULA RECOMMENDATIONS - TEST SUITE")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase71TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    if result.wasSuccessful():
        print(
            "\n🎉 ALL TESTS PASSED! Phase 7.1 Intelligent Formula Recommendations is working correctly."
        )
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed.")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
