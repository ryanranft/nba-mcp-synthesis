"""
Automated Testing Framework Module
Comprehensive testing utilities for ML models and APIs.
"""

import logging
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCase:
    """Individual test case"""
    
    def __init__(
        self,
        name: str,
        test_fn: Callable,
        expected: Any,
        description: Optional[str] = None
    ):
        """
        Initialize test case.
        
        Args:
            name: Test name
            test_fn: Test function
            expected: Expected result
            description: Test description
        """
        self.name = name
        self.test_fn = test_fn
        self.expected = expected
        self.description = description


class TestSuite:
    """Test suite with multiple test cases"""
    
    def __init__(self, name: str):
        """
        Initialize test suite.
        
        Args:
            name: Suite name
        """
        self.name = name
        self.tests: List[TestCase] = []
        self.results: List[Dict] = []
    
    def add_test(
        self,
        name: str,
        test_fn: Callable,
        expected: Any,
        description: Optional[str] = None
    ):
        """Add test case to suite"""
        test = TestCase(name, test_fn, expected, description)
        self.tests.append(test)
        logger.debug(f"Added test: {name}")
    
    def run(self) -> Dict[str, Any]:
        """Run all tests in suite"""
        logger.info(f"Running test suite: {self.name}")
        
        start_time = datetime.utcnow()
        passed = 0
        failed = 0
        errors = 0
        
        for test in self.tests:
            try:
                result = test.test_fn()
                
                if result == test.expected:
                    passed += 1
                    self.results.append({
                        "test": test.name,
                        "status": "PASSED",
                        "expected": test.expected,
                        "actual": result
                    })
                    logger.debug(f"✅ {test.name}: PASSED")
                else:
                    failed += 1
                    self.results.append({
                        "test": test.name,
                        "status": "FAILED",
                        "expected": test.expected,
                        "actual": result
                    })
                    logger.warning(f"❌ {test.name}: FAILED (expected {test.expected}, got {result})")
            
            except Exception as e:
                errors += 1
                self.results.append({
                    "test": test.name,
                    "status": "ERROR",
                    "error": str(e)
                })
                logger.error(f"💥 {test.name}: ERROR - {e}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "suite": self.name,
            "total_tests": len(self.tests),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "duration_seconds": duration,
            "pass_rate": (passed / len(self.tests) * 100) if self.tests else 0,
            "results": self.results
        }
        
        logger.info(
            f"Test suite complete: {passed}/{len(self.tests)} passed "
            f"({summary['pass_rate']:.1f}%) in {duration:.2f}s"
        )
        
        return summary


class ModelTester:
    """Specialized testing for ML models"""
    
    @staticmethod
    def test_prediction_shape(
        predict_fn: Callable,
        test_input: Any,
        expected_shape: tuple
    ) -> bool:
        """Test prediction output shape"""
        result = predict_fn(test_input)
        if hasattr(result, 'shape'):
            return result.shape == expected_shape
        return len(result) == expected_shape[0] if expected_shape else True
    
    @staticmethod
    def test_prediction_range(
        predict_fn: Callable,
        test_input: Any,
        min_val: float,
        max_val: float
    ) -> bool:
        """Test prediction is in expected range"""
        result = predict_fn(test_input)
        return min_val <= result <= max_val
    
    @staticmethod
    def test_reproducibility(
        predict_fn: Callable,
        test_input: Any,
        num_runs: int = 3
    ) -> bool:
        """Test model produces consistent results"""
        results = [predict_fn(test_input) for _ in range(num_runs)]
        return all(r == results[0] for r in results)
    
    @staticmethod
    def test_inference_time(
        predict_fn: Callable,
        test_input: Any,
        max_time_ms: float
    ) -> bool:
        """Test inference completes within time limit"""
        import time
        start = time.time()
        predict_fn(test_input)
        duration_ms = (time.time() - start) * 1000
        return duration_ms <= max_time_ms


class APITester:
    """Specialized testing for APIs"""
    
    @staticmethod
    def test_response_status(
        response: Dict,
        expected_status: int
    ) -> bool:
        """Test API response status code"""
        return response.get("status_code") == expected_status
    
    @staticmethod
    def test_response_schema(
        response: Dict,
        required_fields: List[str]
    ) -> bool:
        """Test API response has required fields"""
        return all(field in response for field in required_fields)
    
    @staticmethod
    def test_response_time(
        response_time_ms: float,
        max_time_ms: float
    ) -> bool:
        """Test API response time"""
        return response_time_ms <= max_time_ms


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("AUTOMATED TESTING FRAMEWORK DEMO")
    print("=" * 80)
    
    # Create test suite
    suite = TestSuite("NBA Model Tests")
    
    # Mock model
    def mock_predict(inputs):
        return sum(inputs) * 0.1
    
    # Add tests
    print("\n" + "=" * 80)
    print("ADDING TESTS")
    print("=" * 80)
    
    suite.add_test(
        "prediction_in_range",
        lambda: ModelTester.test_prediction_range(mock_predict, [10, 20, 30], 0, 10),
        True,
        "Check prediction is in valid range"
    )
    
    suite.add_test(
        "inference_time",
        lambda: ModelTester.test_inference_time(mock_predict, [10, 20, 30], 100),
        True,
        "Check inference completes in < 100ms"
    )
    
    suite.add_test(
        "reproducibility",
        lambda: ModelTester.test_reproducibility(mock_predict, [10, 20, 30]),
        True,
        "Check model is deterministic"
    )
    
    # Add a failing test
    suite.add_test(
        "intentional_fail",
        lambda: False,
        True,
        "This test should fail"
    )
    
    print(f"✅ Added {len(suite.tests)} tests")
    
    # Run tests
    print("\n" + "=" * 80)
    print("RUNNING TESTS")
    print("=" * 80 + "\n")
    
    results = suite.run()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\nSuite: {results['suite']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Errors: {results['errors']} 💥")
    print(f"Pass Rate: {results['pass_rate']:.1f}%")
    print(f"Duration: {results['duration_seconds']:.3f}s")
    
    # Detailed results
    print("\nDetailed Results:")
    for result in results['results']:
        status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}
        icon = status_icon.get(result['status'], "❓")
        print(f"  {icon} {result['test']}: {result['status']}")
    
    print("\n" + "=" * 80)
    print("Automated Testing Demo Complete!")
    print("=" * 80)

