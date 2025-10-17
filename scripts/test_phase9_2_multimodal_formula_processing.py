#!/usr/bin/env python3
"""
Test script for Phase 9.2: Multi-Modal Formula Processing

This script tests the multi-modal formula processing capabilities including:
- Text-based formula processing
- Image-based formula extraction
- Data-driven formula generation
- Cross-modal formula validation
- Multi-modal capabilities

Author: NBA MCP Server Development Team
Date: October 13, 2025
"""

import sys
import os
import unittest
import json
import base64
import io
from typing import Dict, Any, List
import numpy as np
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.tools.multimodal_formula_processing import (
    MultiModalFormulaProcessor,
    process_text_formula,
    process_image_formula,
    process_data_formula,
    validate_cross_modal_formula,
    get_multimodal_capabilities,
    TextProcessingResult,
    ImageProcessingResult,
    DataProcessingResult,
    CrossModalValidationResult,
    ProcessingMode,
    FormulaSource,
    ValidationStatus,
)


class Phase92TestSuite(unittest.TestCase):
    """Test suite for Phase 9.2 Multi-Modal Formula Processing"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = MultiModalFormulaProcessor()

        # Test data for various tests
        self.test_texts = [
            "PER = (FGM * 2 + 3PM * 3 + FTM) / MP * 100",
            "True Shooting Percentage is calculated as PTS / (2 * (FGA + 0.44 * FTA))",
            "Usage Rate equals (FGA + 0.44 * FTA + TOV) * (Team Minutes / 5) / (Player Minutes * (Team FGA + 0.44 * Team FTA + Team TOV)) * 100",
            "The effective field goal percentage formula is: eFG% = (FGM + 0.5 * 3PM) / FGA",
            "Player Efficiency Rating = (Points + Rebounds + Assists + Steals + Blocks - Missed Shots - Turnovers) / Minutes",
        ]

        self.test_data = {
            "points": [25.0, 30.0, 20.0, 35.0, 28.0, 22.0, 40.0, 18.0, 32.0, 26.0],
            "rebounds": [8.0, 10.0, 6.0, 12.0, 9.0, 7.0, 15.0, 5.0, 11.0, 8.0],
            "assists": [5.0, 7.0, 4.0, 8.0, 6.0, 3.0, 10.0, 2.0, 9.0, 5.0],
            "minutes": [35.0, 38.0, 30.0, 42.0, 36.0, 28.0, 45.0, 25.0, 40.0, 33.0],
        }

        # Create a simple test image (1x1 pixel PNG)
        self.test_image_data = self._create_test_image()

    def _create_test_image(self) -> str:
        """Create a simple test image for testing"""
        try:
            from PIL import Image
            import base64

            # Create a simple 1x1 pixel image
            img = Image.new("RGB", (1, 1), color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()

            return base64.b64encode(img_bytes).decode("utf-8")
        except ImportError:
            # Return a minimal base64 string if PIL is not available
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def test_processor_initialization(self):
        """Test that the processor initializes correctly"""
        self.assertIsInstance(self.processor, MultiModalFormulaProcessor)
        self.assertIsNotNone(self.processor.text_patterns)
        self.assertIsInstance(self.processor.text_patterns, dict)

        # Test capabilities
        capabilities = self.processor.get_processing_capabilities()
        self.assertIsInstance(capabilities, dict)
        self.assertIn("text_processing", capabilities)
        self.assertIn("image_processing", capabilities)
        self.assertIn("data_processing", capabilities)
        self.assertIn("cross_modal_validation", capabilities)

    def test_text_formula_processing(self):
        """Test text-based formula processing"""
        print("\n=== Testing Text Formula Processing ===")

        for i, text in enumerate(self.test_texts):
            with self.subTest(text=text[:50] + "..."):
                result = self.processor.process_text_formula(
                    text=text, context="basketball", confidence_threshold=0.5
                )

                self.assertIsInstance(result, TextProcessingResult)
                self.assertIsNotNone(result.formula_id)
                self.assertEqual(result.source_text, text)
                self.assertIsInstance(result.extracted_formula, str)
                self.assertIsInstance(result.variables, list)
                self.assertIsInstance(result.confidence, float)
                self.assertIsInstance(result.processing_method, str)
                self.assertIsInstance(result.validation_status, ValidationStatus)
                self.assertIsInstance(result.metadata, dict)

                print(
                    f"✓ Text {i+1}: {result.processing_method} - Confidence: {result.confidence:.2f}"
                )
                if result.extracted_formula:
                    print(f"  Formula: {result.extracted_formula}")
                    print(f"  Variables: {result.variables}")

    def test_image_formula_processing(self):
        """Test image-based formula processing"""
        print("\n=== Testing Image Formula Processing ===")

        result = self.processor.process_image_formula(
            image_data=self.test_image_data,
            image_format="base64",
            confidence_threshold=0.5,
        )

        self.assertIsInstance(result, ImageProcessingResult)
        self.assertIsNotNone(result.formula_id)
        self.assertIsInstance(result.image_source, str)
        self.assertIsInstance(result.extracted_text, str)
        self.assertIsInstance(result.extracted_formula, str)
        self.assertIsInstance(result.variables, list)
        self.assertIsInstance(result.confidence, float)
        self.assertIsInstance(result.processing_method, str)
        self.assertIsInstance(result.validation_status, ValidationStatus)
        self.assertIsInstance(result.metadata, dict)

        print(
            f"✓ Image Processing: {result.processing_method} - Confidence: {result.confidence:.2f}"
        )
        print(f"  Extracted Text: {result.extracted_text}")
        print(f"  Formula: {result.extracted_formula}")

    def test_data_formula_processing(self):
        """Test data-driven formula generation"""
        print("\n=== Testing Data Formula Processing ===")

        methods = ["regression", "correlation", "pattern"]

        for method in methods:
            with self.subTest(method=method):
                result = self.processor.process_data_formula(
                    data=self.test_data,
                    target_variable="points",
                    method=method,
                    confidence_threshold=0.5,
                )

                self.assertIsInstance(result, DataProcessingResult)
                self.assertIsNotNone(result.formula_id)
                self.assertIsInstance(result.data_source, str)
                self.assertIsInstance(result.generated_formula, str)
                self.assertIsInstance(result.variables, list)
                self.assertIsInstance(result.accuracy, float)
                self.assertIsInstance(result.processing_method, str)
                self.assertIsInstance(result.validation_status, ValidationStatus)
                self.assertIsInstance(result.metadata, dict)

                print(f"✓ Data Processing ({method}): Accuracy: {result.accuracy:.2f}")
                print(f"  Formula: {result.generated_formula}")
                print(f"  Variables: {result.variables}")

    def test_cross_modal_validation(self):
        """Test cross-modal formula validation"""
        print("\n=== Testing Cross-Modal Validation ===")

        # First process a text formula to get a formula ID
        text_result = self.processor.process_text_formula(
            text=self.test_texts[0], context="basketball"
        )

        validation_methods = ["syntax", "semantics", "mathematical", "domain"]

        result = self.processor.validate_cross_modal(
            formula_id=text_result.formula_id,
            validation_methods=validation_methods,
            confidence_threshold=0.5,
        )

        self.assertIsInstance(result, CrossModalValidationResult)
        self.assertEqual(result.formula_id, text_result.formula_id)
        self.assertIsInstance(result.validation_methods, list)
        self.assertIsInstance(result.consistency_score, float)
        self.assertIsInstance(result.confidence, float)
        self.assertIsInstance(result.validation_status, ValidationStatus)
        self.assertIsInstance(result.discrepancies, list)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.metadata, dict)

        print(f"✓ Cross-Modal Validation: Consistency: {result.consistency_score:.2f}")
        print(f"  Status: {result.validation_status.value}")
        print(f"  Discrepancies: {len(result.discrepancies)}")
        print(f"  Recommendations: {len(result.recommendations)}")

    def test_standalone_functions(self):
        """Test standalone functions"""
        print("\n=== Testing Standalone Functions ===")

        # Test text processing
        text_result = process_text_formula(
            text=self.test_texts[0], context="basketball"
        )
        self.assertIsInstance(text_result, dict)
        self.assertIn("formula_id", text_result)

        # Test image processing
        image_result = process_image_formula(
            image_data=self.test_image_data, image_format="base64"
        )
        self.assertIsInstance(image_result, dict)
        self.assertIn("formula_id", image_result)

        # Test data processing
        data_result = process_data_formula(
            data=self.test_data, target_variable="points", method="regression"
        )
        self.assertIsInstance(data_result, dict)
        self.assertIn("formula_id", data_result)

        # Test cross-modal validation
        validation_result = validate_cross_modal_formula(
            formula_id=text_result["formula_id"],
            validation_methods=["syntax", "semantics"],
        )
        self.assertIsInstance(validation_result, dict)
        self.assertIn("formula_id", validation_result)

        # Test capabilities
        capabilities = get_multimodal_capabilities()
        self.assertIsInstance(capabilities, dict)
        self.assertIn("text_processing", capabilities)

        print("✓ All standalone functions working correctly")

    def test_error_handling(self):
        """Test error handling"""
        print("\n=== Testing Error Handling ===")

        # Test with invalid text
        result = self.processor.process_text_formula(text="", context="basketball")
        self.assertIsInstance(result, TextProcessingResult)
        self.assertEqual(result.validation_status, ValidationStatus.INVALID)

        # Test with invalid data
        result = self.processor.process_data_formula(
            data={}, target_variable="nonexistent", method="regression"
        )
        self.assertIsInstance(result, DataProcessingResult)
        self.assertEqual(result.validation_status, ValidationStatus.INVALID)

        # Test with invalid image data
        result = self.processor.process_image_formula(
            image_data="invalid_base64", image_format="base64"
        )
        self.assertIsInstance(result, ImageProcessingResult)
        self.assertEqual(result.validation_status, ValidationStatus.INVALID)

        print("✓ Error handling working correctly")

    def test_integration_with_sports_formulas(self):
        """Test integration with sports formulas"""
        print("\n=== Testing Integration with Sports Formulas ===")

        # Test with basketball-specific formulas
        basketball_texts = [
            "PER = (FGM * 2 + 3PM * 3 + FTM) / MP * 100",
            "True Shooting Percentage = PTS / (2 * (FGA + 0.44 * FTA))",
            "Usage Rate = (FGA + 0.44 * FTA + TOV) * (Team Minutes / 5) / (Player Minutes * (Team FGA + 0.44 * Team FTA + Team TOV)) * 100",
        ]

        for text in basketball_texts:
            result = self.processor.process_text_formula(
                text=text, context="basketball"
            )

            self.assertIsInstance(result, TextProcessingResult)
            self.assertGreater(result.confidence, 0.0)

            print(
                f"✓ Basketball Formula: {result.processing_method} - Confidence: {result.confidence:.2f}"
            )

    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n=== Testing Performance Benchmarks ===")

        import time

        # Text processing benchmark
        start_time = time.time()
        for text in self.test_texts:
            self.processor.process_text_formula(text, context="basketball")
        text_time = time.time() - start_time

        # Data processing benchmark
        start_time = time.time()
        for method in ["regression", "correlation", "pattern"]:
            self.processor.process_data_formula(
                data=self.test_data, target_variable="points", method=method
            )
        data_time = time.time() - start_time

        # Image processing benchmark
        start_time = time.time()
        self.processor.process_image_formula(
            image_data=self.test_image_data, image_format="base64"
        )
        image_time = time.time() - start_time

        print(f"✓ Text Processing: {text_time:.2f}s for {len(self.test_texts)} texts")
        print(f"✓ Data Processing: {data_time:.2f}s for 3 methods")
        print(f"✓ Image Processing: {image_time:.2f}s")

        # Performance assertions
        self.assertLess(text_time, 10.0, "Text processing should be fast")
        self.assertLess(data_time, 5.0, "Data processing should be fast")
        self.assertLess(image_time, 5.0, "Image processing should be fast")

    def test_formula_validation(self):
        """Test formula validation functionality"""
        print("\n=== Testing Formula Validation ===")

        # Test valid formula
        valid_formula = "x = a + b * c"
        validation_result = self.processor._validate_formula(valid_formula)

        self.assertIsInstance(validation_result, dict)
        self.assertIn("status", validation_result)
        self.assertIn("parsed", validation_result)
        self.assertIn("variables", validation_result)

        print(f"✓ Formula Validation: {validation_result['status'].value}")
        print(f"  Variables: {validation_result['variables']}")

    def test_pattern_extraction(self):
        """Test pattern extraction methods"""
        print("\n=== Testing Pattern Extraction ===")

        # Test direct extraction
        direct_result = self.processor._extract_direct_formula(
            "PER = (FGM * 2 + 3PM * 3 + FTM) / MP * 100"
        )
        if direct_result:
            self.assertIsInstance(direct_result, dict)
            self.assertIn("formula", direct_result)
            self.assertIn("variables", direct_result)
            self.assertIn("confidence", direct_result)
            print(f"✓ Direct Extraction: {direct_result['confidence']:.2f}")

        # Test pattern-based extraction
        pattern_result = self.processor._extract_pattern_based_formula(
            "Player Efficiency Rating is calculated as..."
        )
        if pattern_result:
            self.assertIsInstance(pattern_result, dict)
            self.assertIn("formula", pattern_result)
            self.assertIn("variables", pattern_result)
            self.assertIn("confidence", pattern_result)
            print(f"✓ Pattern Extraction: {pattern_result['confidence']:.2f}")

        # Test context-aware extraction
        context_result = self.processor._extract_context_aware_formula(
            "PER calculation", "basketball"
        )
        if context_result:
            self.assertIsInstance(context_result, dict)
            self.assertIn("formula", context_result)
            self.assertIn("variables", context_result)
            self.assertIn("confidence", context_result)
            print(f"✓ Context Extraction: {context_result['confidence']:.2f}")


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("PHASE 9.2: MULTI-MODAL FORMULA PROCESSING TESTS")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase92TestSuite)

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

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
