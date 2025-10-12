"""
Model Performance Testing Module
Comprehensive testing framework for ML model performance, accuracy, and reliability.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_time_ms: float
    throughput_qps: float
    memory_usage_mb: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "inference_time_ms": self.inference_time_ms,
            "throughput_qps": self.throughput_qps,
            "memory_usage_mb": self.memory_usage_mb
        }


@dataclass
class PerformanceTest:
    """Single performance test configuration"""
    test_name: str
    model_name: str
    test_data_size: int
    passed: bool = False
    metrics: Optional[PerformanceMetrics] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ModelPerformanceTester:
    """Tests ML model performance across multiple dimensions"""
    
    def __init__(self):
        self.test_results: List[PerformanceTest] = []
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[float, float, float, float]:
        """
        Calculate accuracy, precision, recall, F1.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Tuple of (accuracy, precision, recall, f1)
        """
        # Binary classification metrics
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return accuracy, precision, recall, f1
    
    def test_accuracy(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        min_accuracy: float = 0.80
    ) -> PerformanceTest:
        """
        Test model accuracy meets minimum threshold.
        
        Args:
            model: Model with predict() method
            X_test: Test features
            y_test: Test labels
            min_accuracy: Minimum required accuracy
            
        Returns:
            PerformanceTest result
        """
        test = PerformanceTest(
            test_name="accuracy_threshold",
            model_name=str(type(model).__name__),
            test_data_size=len(X_test)
        )
        
        try:
            y_pred = model.predict(X_test)
            accuracy, precision, recall, f1 = self.calculate_metrics(y_test, y_pred)
            
            test.metrics = PerformanceMetrics(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                inference_time_ms=0,
                throughput_qps=0,
                memory_usage_mb=0
            )
            test.passed = accuracy >= min_accuracy
            
            logger.info(
                f"Accuracy test: {accuracy:.2%} "
                f"({'PASSED' if test.passed else 'FAILED'} - min {min_accuracy:.2%})"
            )
            
        except Exception as e:
            test.error = str(e)
            logger.error(f"Accuracy test failed: {e}")
        
        self.test_results.append(test)
        return test
    
    def test_inference_latency(
        self,
        model: Any,
        X_test: np.ndarray,
        max_latency_ms: float = 100.0,
        n_iterations: int = 100
    ) -> PerformanceTest:
        """
        Test model inference latency.
        
        Args:
            model: Model with predict() method
            X_test: Test features
            max_latency_ms: Maximum allowed latency (ms)
            n_iterations: Number of iterations for average
            
        Returns:
            PerformanceTest result
        """
        test = PerformanceTest(
            test_name="inference_latency",
            model_name=str(type(model).__name__),
            test_data_size=len(X_test)
        )
        
        try:
            latencies = []
            for _ in range(n_iterations):
                start = time.time()
                _ = model.predict(X_test[:1])  # Single prediction
                end = time.time()
                latencies.append((end - start) * 1000)  # Convert to ms
            
            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)
            
            test.metrics = PerformanceMetrics(
                accuracy=0,
                precision=0,
                recall=0,
                f1_score=0,
                inference_time_ms=avg_latency,
                throughput_qps=0,
                memory_usage_mb=0
            )
            test.passed = avg_latency <= max_latency_ms
            
            logger.info(
                f"Latency test: avg={avg_latency:.2f}ms, "
                f"p95={p95_latency:.2f}ms, p99={p99_latency:.2f}ms "
                f"({'PASSED' if test.passed else 'FAILED'} - max {max_latency_ms}ms)"
            )
            
        except Exception as e:
            test.error = str(e)
            logger.error(f"Latency test failed: {e}")
        
        self.test_results.append(test)
        return test
    
    def test_throughput(
        self,
        model: Any,
        X_test: np.ndarray,
        min_qps: float = 100.0,
        duration_seconds: float = 5.0
    ) -> PerformanceTest:
        """
        Test model throughput (queries per second).
        
        Args:
            model: Model with predict() method
            X_test: Test features
            min_qps: Minimum required queries per second
            duration_seconds: Test duration
            
        Returns:
            PerformanceTest result
        """
        test = PerformanceTest(
            test_name="throughput",
            model_name=str(type(model).__name__),
            test_data_size=len(X_test)
        )
        
        try:
            start_time = time.time()
            query_count = 0
            
            while (time.time() - start_time) < duration_seconds:
                _ = model.predict(X_test[:10])  # Batch of 10
                query_count += 10
            
            elapsed = time.time() - start_time
            qps = query_count / elapsed
            
            test.metrics = PerformanceMetrics(
                accuracy=0,
                precision=0,
                recall=0,
                f1_score=0,
                inference_time_ms=0,
                throughput_qps=qps,
                memory_usage_mb=0
            )
            test.passed = qps >= min_qps
            
            logger.info(
                f"Throughput test: {qps:.1f} QPS "
                f"({'PASSED' if test.passed else 'FAILED'} - min {min_qps} QPS)"
            )
            
        except Exception as e:
            test.error = str(e)
            logger.error(f"Throughput test failed: {e}")
        
        self.test_results.append(test)
        return test
    
    def test_consistency(
        self,
        model: Any,
        X_test: np.ndarray,
        n_runs: int = 10
    ) -> PerformanceTest:
        """
        Test model prediction consistency across multiple runs.
        
        Args:
            model: Model with predict() method
            X_test: Test features
            n_runs: Number of prediction runs
            
        Returns:
            PerformanceTest result
        """
        test = PerformanceTest(
            test_name="prediction_consistency",
            model_name=str(type(model).__name__),
            test_data_size=len(X_test)
        )
        
        try:
            predictions = []
            for _ in range(n_runs):
                pred = model.predict(X_test)
                predictions.append(pred)
            
            # Check if all predictions are identical
            first_pred = predictions[0]
            all_consistent = all(np.array_equal(first_pred, p) for p in predictions)
            
            test.passed = all_consistent
            
            logger.info(
                f"Consistency test: {'PASSED' if test.passed else 'FAILED'} "
                f"({n_runs} runs)"
            )
            
        except Exception as e:
            test.error = str(e)
            logger.error(f"Consistency test failed: {e}")
        
        self.test_results.append(test)
        return test
    
    def run_comprehensive_test_suite(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Run comprehensive performance test suite.
        
        Args:
            model: Model to test
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dict with summary of all tests
        """
        logger.info("Starting comprehensive performance test suite...")
        
        # Run all tests
        self.test_accuracy(model, X_test, y_test, min_accuracy=0.75)
        self.test_inference_latency(model, X_test, max_latency_ms=50.0)
        self.test_throughput(model, X_test, min_qps=50.0)
        self.test_consistency(model, X_test, n_runs=5)
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.passed)
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "all_passed": failed_tests == 0,
            "test_results": [
                {
                    "test_name": t.test_name,
                    "passed": t.passed,
                    "metrics": t.metrics.to_dict() if t.metrics else None,
                    "error": t.error
                }
                for t in self.test_results
            ]
        }
        
        logger.info(
            f"Test suite complete: {passed_tests}/{total_tests} passed "
            f"({summary['pass_rate']:.1f}%)"
        )
        
        return summary


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL PERFORMANCE TESTING DEMO")
    print("=" * 80)
    
    # Simple mock model for demonstration
    class MockModel:
        def predict(self, X):
            return np.random.randint(0, 2, len(X))
    
    model = MockModel()
    X_test = np.random.randn(1000, 10)
    y_test = np.random.randint(0, 2, 1000)
    
    tester = ModelPerformanceTester()
    summary = tester.run_comprehensive_test_suite(model, X_test, y_test)
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✓")
    print(f"Failed: {summary['failed']} ✗")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"Overall: {'✅ ALL PASSED' if summary['all_passed'] else '❌ SOME FAILED'}")
    
    print("\n" + "=" * 80)
    print("Model Performance Testing Complete!")
    print("=" * 80)

