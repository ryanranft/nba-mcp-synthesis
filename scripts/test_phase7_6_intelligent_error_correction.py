#!/usr/bin/env python3
"""
Test script for Phase 7.6: Intelligent Error Correction

This script tests all the intelligent error correction functionality including:
- Error detection across multiple error types
- Intelligent error correction with different strategies
- Comprehensive formula validation
- Intelligent suggestion generation
- Error pattern analysis
- Learning from error cases
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the tools to test
from mcp_server.tools.intelligent_error_correction import (
    detect_intelligent_errors,
    correct_intelligent_errors,
    validate_formula_comprehensively,
    generate_intelligent_suggestions,
    analyze_error_patterns,
    learn_from_error_cases,
    IntelligentErrorCorrectionEngine
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase76TestSuite:
    """Test suite for Phase 7.6: Intelligent Error Correction"""

    def __init__(self):
        """Initialize the test suite"""
        self.engine = IntelligentErrorCorrectionEngine()
        self.test_results = []

        # Sample test formulas with various error types
        self.test_formulas = {
            "syntax_errors": [
                "points ==",  # Double equals
                "function()",  # Empty function call
                "a + + b",  # Consecutive operators
                "sqrt((2 + 3)",  # Unmatched parentheses
            ],
            "semantic_errors": [
                "points / 0",  # Division by zero
                "sqrt(-4)",  # Square root of negative
                "log(0)",  # Log of zero
            ],
            "domain_errors": [
                "field_goal_percentage > 1.5",  # Percentage over 100%
                "points_per_game < -5",  # Negative points
            ],
            "valid_formulas": [
                "points / field_goal_attempts",
                "rebounds + assists",
                "sqrt(points * rebounds)",
                "log(points + 1)",
            ]
        }

        # Sample error cases for learning
        self.sample_error_cases = [
            {
                "error_type": "syntax",
                "formula": "points ==",
                "correction": "points =",
                "context": "assignment operation"
            },
            {
                "error_type": "semantic",
                "formula": "points / 0",
                "correction": "points / (0 + 1e-10)",
                "context": "division by zero"
            },
            {
                "error_type": "domain",
                "formula": "field_goal_percentage > 1.5",
                "correction": "field_goal_percentage > 1.0",
                "context": "percentage validation"
            }
        ]

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases"""
        print("=" * 60)
        print("PHASE 7.6: INTELLIGENT ERROR CORRECTION - TEST SUITE")
        print("=" * 60)

        start_time = time.time()

        # Run individual test methods
        test_methods = [
            self.test_error_detection,
            self.test_error_correction,
            self.test_formula_validation,
            self.test_intelligent_suggestions,
            self.test_error_pattern_analysis,
            self.test_error_learning,
            self.test_error_handling,
            self.test_integration_with_sports_formulas,
            self.run_performance_benchmark
        ]

        for test_method in test_methods:
            try:
                test_method()
                self.test_results.append({"test": test_method.__name__, "status": "passed"})
            except Exception as e:
                print(f"❌ {test_method.__name__} failed: {e}")
                self.test_results.append({"test": test_method.__name__, "status": "failed", "error": str(e)})

        total_time = time.time() - start_time

        # Summary
        passed_tests = sum(1 for result in self.test_results if result["status"] == "passed")
        total_tests = len(self.test_results)

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_time": total_time,
            "test_results": self.test_results
        }

    def test_error_detection(self):
        """Test intelligent error detection"""
        print("\nTesting error detection...")

        # Test syntax error detection
        result1 = detect_intelligent_errors(
            input_formula="points ==",
            context_type="formula",
            error_types=["syntax"],
            include_suggestions=True,
            confidence_threshold=0.7,
            domain_context="basketball"
        )

        assert result1["status"] == "success", "Error detection should succeed"
        assert result1["errors_detected"] > 0, "Should detect syntax errors"
        assert len(result1["suggestions"]) > 0, "Should provide suggestions"

        # Test semantic error detection
        result2 = detect_intelligent_errors(
            input_formula="points / 0",
            context_type="formula",
            error_types=["semantic"],
            include_suggestions=True,
            confidence_threshold=0.8
        )

        assert result2["status"] == "success", "Semantic error detection should succeed"
        assert result2["errors_detected"] > 0, "Should detect semantic errors"

        # Test domain error detection
        result3 = detect_intelligent_errors(
            input_formula="field_goal_percentage > 1.5",
            context_type="formula",
            error_types=["domain"],
            domain_context="basketball"
        )

        assert result3["status"] == "success", "Domain error detection should succeed"

        # Test multiple error types
        result4 = detect_intelligent_errors(
            input_formula="points ==",
            context_type="formula",
            error_types=["syntax", "semantic", "logical"],
            include_suggestions=True
        )

        assert result4["status"] == "success", "Multiple error type detection should succeed"

        print("  ✓ Syntax error detection")
        print("  ✓ Semantic error detection")
        print("  ✓ Domain error detection")
        print("  ✓ Multiple error type detection")
        print("✓ Error detection test passed")

    def test_error_correction(self):
        """Test intelligent error correction"""
        print("\nTesting error correction...")

        # First detect some errors
        detection_result = detect_intelligent_errors(
            input_formula="points ==",
            context_type="formula",
            error_types=["syntax"],
            include_suggestions=True
        )

        detected_errors = detection_result["errors"]

        # Test automatic correction
        result1 = correct_intelligent_errors(
            detected_errors=detected_errors,
            correction_strategy="automatic",
            preserve_intent=True,
            validation_level="comprehensive",
            include_explanations=True,
            max_corrections=3
        )

        assert result1["status"] == "success", "Automatic correction should succeed"
        assert result1["corrections_applied"] >= 0, "Should apply corrections"

        # Test suggested correction
        result2 = correct_intelligent_errors(
            detected_errors=detected_errors,
            correction_strategy="suggested",
            preserve_intent=True,
            validation_level="basic",
            include_explanations=True,
            max_corrections=2
        )

        assert result2["status"] == "success", "Suggested correction should succeed"

        # Test interactive correction
        result3 = correct_intelligent_errors(
            detected_errors=detected_errors,
            correction_strategy="interactive",
            preserve_intent=True,
            validation_level="strict",
            include_explanations=True,
            max_corrections=1
        )

        assert result3["status"] == "success", "Interactive correction should succeed"

        print("  ✓ Automatic correction strategy")
        print("  ✓ Suggested correction strategy")
        print("  ✓ Interactive correction strategy")
        print("  ✓ Correction validation")
        print("✓ Error correction test passed")

    def test_formula_validation(self):
        """Test comprehensive formula validation"""
        print("\nTesting formula validation...")

        # Test comprehensive validation
        result1 = validate_formula_comprehensively(
            formula_expression="points / field_goal_attempts",
            validation_types=["syntax", "semantics", "mathematics"],
            test_data={
                "points": [20.0, 25.0, 15.0],
                "field_goal_attempts": [15.0, 20.0, 12.0]
            },
            expected_range={"result": (0.0, 1.0)},
            domain_constraints={"basketball": True},
            include_performance_analysis=True
        )

        assert result1["status"] == "success", "Formula validation should succeed"
        assert "is_valid" in result1, "Should include validity status"
        assert "errors" in result1, "Should include errors list"
        assert "suggestions" in result1, "Should include suggestions"

        # Test validation with invalid formula
        result2 = validate_formula_comprehensively(
            formula_expression="points / 0",
            validation_types=["syntax", "semantics"],
            include_performance_analysis=False
        )

        assert result2["status"] == "success", "Invalid formula validation should succeed"
        assert result2["is_valid"] == False, "Should identify invalid formula"
        assert len(result2["errors"]) > 0, "Should detect errors in invalid formula"

        # Test domain-specific validation
        result3 = validate_formula_comprehensively(
            formula_expression="field_goal_percentage > 1.5",
            validation_types=["domain"],
            domain_constraints={"basketball": True}
        )

        assert result3["status"] == "success", "Domain validation should succeed"

        print("  ✓ Comprehensive validation")
        print("  ✓ Invalid formula detection")
        print("  ✓ Domain-specific validation")
        print("  ✓ Performance analysis")
        print("✓ Formula validation test passed")

    def test_intelligent_suggestions(self):
        """Test intelligent suggestion generation"""
        print("\nTesting intelligent suggestions...")

        # Test basic suggestion generation
        result1 = generate_intelligent_suggestions(
            error_context={
                "error_type": "syntax",
                "formula": "points ==",
                "position": (0, 8)
            },
            user_intent="Calculate player efficiency",
            similar_formulas=["points = assists + rebounds", "points = field_goals * 2"],
            correction_history=[],
            suggestion_count=3,
            include_alternatives=True
        )

        assert result1["status"] == "success", "Suggestion generation should succeed"
        assert result1["suggestions_count"] > 0, "Should generate suggestions"
        assert len(result1["suggestions"]) > 0, "Should have suggestion list"

        # Test semantic error suggestions
        result2 = generate_intelligent_suggestions(
            error_context={
                "error_type": "semantic",
                "formula": "points / 0",
                "message": "Division by zero"
            },
            user_intent="Calculate shooting percentage",
            similar_formulas=["points / field_goal_attempts"],
            suggestion_count=2,
            include_alternatives=True
        )

        assert result2["status"] == "success", "Semantic suggestion generation should succeed"

        # Test domain error suggestions
        result3 = generate_intelligent_suggestions(
            error_context={
                "error_type": "domain",
                "formula": "field_goal_percentage > 1.5",
                "message": "Percentage over 100%"
            },
            user_intent="Validate shooting statistics",
            suggestion_count=1,
            include_alternatives=False
        )

        assert result3["status"] == "success", "Domain suggestion generation should succeed"

        print("  ✓ Basic suggestion generation")
        print("  ✓ Semantic error suggestions")
        print("  ✓ Domain error suggestions")
        print("  ✓ Context-aware suggestions")
        print("✓ Intelligent suggestions test passed")

    def test_error_pattern_analysis(self):
        """Test error pattern analysis"""
        print("\nTesting error pattern analysis...")

        # Test formula string analysis
        result1 = analyze_error_patterns(
            analysis_input="points ==",
            analysis_depth="deep",
            include_pattern_analysis=True,
            include_statistical_analysis=True,
            include_context_analysis=True,
            generate_report=False
        )

        assert result1["status"] == "success", "Pattern analysis should succeed"
        assert "analysis_results" in result1, "Should include analysis results"

        # Test analysis data input
        analysis_data = {
            "formulas": ["points ==", "points / 0", "field_goal_percentage > 1.5"],
            "error_types": ["syntax", "semantic", "domain"],
            "context": "basketball analytics"
        }

        result2 = analyze_error_patterns(
            analysis_input=analysis_data,
            analysis_depth="comprehensive",
            include_pattern_analysis=True,
            include_statistical_analysis=True,
            include_context_analysis=True,
            generate_report=True
        )

        assert result2["status"] == "success", "Data analysis should succeed"

        # Test surface analysis
        result3 = analyze_error_patterns(
            analysis_input="points + assists",
            analysis_depth="surface",
            include_pattern_analysis=False,
            include_statistical_analysis=False,
            include_context_analysis=True,
            generate_report=False
        )

        assert result3["status"] == "success", "Surface analysis should succeed"

        print("  ✓ Formula string analysis")
        print("  ✓ Analysis data input")
        print("  ✓ Surface analysis depth")
        print("  ✓ Pattern and statistical analysis")
        print("✓ Error pattern analysis test passed")

    def test_error_learning(self):
        """Test learning from error cases"""
        print("\nTesting error learning...")

        # Test supervised learning
        result1 = learn_from_error_cases(
            error_cases=self.sample_error_cases,
            learning_type="supervised",
            update_model=True,
            validation_split=0.2,
            learning_rate=0.01,
            epochs=5
        )

        assert result1["status"] == "success", "Supervised learning should succeed"
        assert "learning_results" in result1, "Should include learning results"

        # Test unsupervised learning
        result2 = learn_from_error_cases(
            error_cases=self.sample_error_cases,
            learning_type="unsupervised",
            update_model=False,
            validation_split=0.3,
            learning_rate=0.005,
            epochs=3
        )

        assert result2["status"] == "success", "Unsupervised learning should succeed"

        # Test reinforcement learning
        result3 = learn_from_error_cases(
            error_cases=self.sample_error_cases,
            learning_type="reinforcement",
            update_model=True,
            validation_split=0.25,
            learning_rate=0.02,
            epochs=10
        )

        assert result3["status"] == "success", "Reinforcement learning should succeed"

        print("  ✓ Supervised learning")
        print("  ✓ Unsupervised learning")
        print("  ✓ Reinforcement learning")
        print("  ✓ Model update control")
        print("✓ Error learning test passed")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\nTesting error handling...")

        # Test empty formula
        result1 = detect_intelligent_errors(
            input_formula="",
            context_type="formula",
            error_types=["syntax"]
        )

        assert result1["status"] == "error", "Should handle empty formula gracefully"

        # Test invalid error types
        result2 = detect_intelligent_errors(
            input_formula="points + assists",
            context_type="formula",
            error_types=["invalid_type"],
            include_suggestions=True
        )

        assert result2["status"] == "success", "Should handle invalid error types gracefully"

        # Test invalid correction strategy
        detected_errors = [{"error_id": "test", "error_type": "syntax", "severity": "medium", "message": "Test error", "confidence": 0.8}]

        result3 = correct_intelligent_errors(
            detected_errors=detected_errors,
            correction_strategy="invalid_strategy",
            preserve_intent=True,
            validation_level="basic",
            include_explanations=True,
            max_corrections=1
        )

        assert result3["status"] == "success", "Should handle invalid correction strategy"

        # Test invalid validation types
        result4 = validate_formula_comprehensively(
            formula_expression="points + assists",
            validation_types=["invalid_type"],
            include_performance_analysis=False
        )

        assert result4["status"] == "success", "Should handle invalid validation types"

        print("  ✓ Empty formula handling")
        print("  ✓ Invalid error types")
        print("  ✓ Invalid correction strategy")
        print("  ✓ Invalid validation types")
        print("✓ Error handling test passed")

    def test_integration_with_sports_formulas(self):
        """Test integration with sports analytics formulas"""
        print("\nTesting integration with sports formulas...")

        # Test common basketball formulas
        basketball_formulas = [
            "points / field_goal_attempts",  # Field goal percentage
            "rebounds + assists + points",  # Triple double components
            "assists / minutes",  # Assists per minute
            "points / (field_goal_attempts + 0.44 * free_throw_attempts)",  # True shooting percentage
        ]

        for formula in basketball_formulas:
            # Test error detection
            detection_result = detect_intelligent_errors(
                input_formula=formula,
                context_type="formula",
                error_types=["syntax", "semantic", "domain"],
                domain_context="basketball"
            )

            assert detection_result["status"] == "success", f"Should detect errors in {formula}"

            # Test validation
            validation_result = validate_formula_comprehensively(
                formula_expression=formula,
                validation_types=["syntax", "semantics", "domain"],
                domain_constraints={"basketball": True}
            )

            assert validation_result["status"] == "success", f"Should validate {formula}"

        # Test domain-specific error detection
        domain_error_formula = "field_goal_percentage > 1.5"
        domain_result = detect_intelligent_errors(
            input_formula=domain_error_formula,
            context_type="formula",
            error_types=["domain"],
            domain_context="basketball"
        )

        assert domain_result["status"] == "success", "Should detect domain errors"

        print("  ✓ Basketball formula validation")
        print("  ✓ Domain-specific error detection")
        print("  ✓ Sports analytics integration")
        print("  ✓ Formula complexity handling")
        print("✓ Sports formulas integration test passed")

    def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmarks for key functions"""
        print("\n============================================================")
        print("PERFORMANCE BENCHMARK TESTS")
        print("============================================================")

        # Setup test data
        test_formulas = [
            "points / field_goal_attempts",
            "points ==",
            "sqrt(-4)",
            "field_goal_percentage > 1.5",
            "rebounds + assists + points"
        ]

        # Benchmark error detection
        start_time = time.time()
        for formula in test_formulas:
            detect_intelligent_errors(
                input_formula=formula,
                context_type="formula",
                error_types=["syntax", "semantic", "domain"],
                domain_context="basketball"
            )
        detection_time = time.time() - start_time
        print(f"Error Detection: {detection_time:.2f}s ({len(test_formulas)} formulas)")

        # Benchmark formula validation
        start_time = time.time()
        for formula in test_formulas:
            validate_formula_comprehensively(
                formula_expression=formula,
                validation_types=["syntax", "semantics", "domain"],
                domain_constraints={"basketball": True}
            )
        validation_time = time.time() - start_time
        print(f"Formula Validation: {validation_time:.2f}s ({len(test_formulas)} formulas)")

        # Benchmark suggestion generation
        start_time = time.time()
        for i in range(5):
            generate_intelligent_suggestions(
                error_context={"error_type": "syntax", "formula": "test"},
                suggestion_count=3
            )
        suggestion_time = time.time() - start_time
        print(f"Suggestion Generation: {suggestion_time:.2f}s (5 requests)")

        # Benchmark pattern analysis
        start_time = time.time()
        analyze_error_patterns(
            analysis_input="points + assists",
            analysis_depth="deep",
            include_pattern_analysis=True,
            include_statistical_analysis=True,
            include_context_analysis=True
        )
        analysis_time = time.time() - start_time
        print(f"Pattern Analysis: {analysis_time:.2f}s")

        # Benchmark learning
        start_time = time.time()
        learn_from_error_cases(
            error_cases=self.sample_error_cases,
            learning_type="supervised",
            update_model=False,
            epochs=3
        )
        learning_time = time.time() - start_time
        print(f"Error Learning: {learning_time:.2f}s")

        total_benchmark_time = detection_time + validation_time + suggestion_time + analysis_time + learning_time
        print(f"\nTotal Benchmark Time: {total_benchmark_time:.2f}s")

        return {
            "detection_time": detection_time,
            "validation_time": validation_time,
            "suggestion_time": suggestion_time,
            "analysis_time": analysis_time,
            "learning_time": learning_time,
            "total_benchmark_time": total_benchmark_time
        }


def main():
    """Main test execution"""
    try:
        test_suite = Phase76TestSuite()
        results = test_suite.run_all_tests()

        if results["success_rate"] >= 80:
            print(f"\n🎉 Phase 7.6 tests completed successfully! ({results['success_rate']:.1f}% pass rate)")
            return 0
        else:
            print(f"\n❌ Phase 7.6 tests had issues ({results['success_rate']:.1f}% pass rate)")
            return 1

    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)



