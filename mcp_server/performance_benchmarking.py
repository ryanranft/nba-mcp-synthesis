"""
Performance Benchmarking Module
Benchmark and compare model performance across metrics.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import time
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Benchmark model performance"""
    
    def __init__(self):
        """Initialize performance benchmark"""
        self.results: List[Dict] = []
    
    def benchmark_model(
        self,
        model_id: str,
        predict_fn: callable,
        test_data: List[Any],
        true_labels: Optional[List[Any]] = None,
        num_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Benchmark a model.
        
        Args:
            model_id: Model identifier
            predict_fn: Prediction function
            test_data: Test dataset
            true_labels: True labels (for accuracy)
            num_iterations: Iterations for timing
            
        Returns:
            Benchmark results
        """
        logger.info(f"Benchmarking {model_id}...")
        
        # Latency benchmark
        latencies = []
        for _ in range(num_iterations):
            start = time.time()
            predictions = [predict_fn(sample) for sample in test_data]
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
        
        # Throughput
        total_time = sum(latencies) / 1000  # seconds
        throughput = (len(test_data) * num_iterations) / total_time
        
        # Accuracy (if labels provided)
        accuracy = None
        if true_labels:
            predictions = [predict_fn(sample) for sample in test_data]
            correct = sum(1 for p, t in zip(predictions, true_labels) if p == t)
            accuracy = correct / len(true_labels) * 100
        
        result = {
            "model_id": model_id,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "std": statistics.stdev(latencies) if len(latencies) > 1 else 0
            },
            "throughput_samples_per_sec": throughput,
            "accuracy_percent": accuracy,
            "test_size": len(test_data),
            "iterations": num_iterations
        }
        
        self.results.append(result)
        
        logger.info(
            f"✅ {model_id}: {result['latency_ms']['mean']:.2f}ms, "
            f"{throughput:.1f} samples/sec"
        )
        
        return result
    
    def compare_benchmarks(
        self,
        model_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare benchmark results.
        
        Args:
            model_ids: Models to compare (None for all)
            
        Returns:
            Comparison results
        """
        if not self.results:
            return {"error": "No benchmarks available"}
        
        results_to_compare = self.results
        if model_ids:
            results_to_compare = [
                r for r in self.results if r["model_id"] in model_ids
            ]
        
        # Find best by each metric
        best_latency = min(results_to_compare, key=lambda r: r["latency_ms"]["mean"])
        best_throughput = max(results_to_compare, key=lambda r: r["throughput_samples_per_sec"])
        best_accuracy = max(
            [r for r in results_to_compare if r["accuracy_percent"] is not None],
            key=lambda r: r["accuracy_percent"]
        ) if any(r["accuracy_percent"] is not None for r in results_to_compare) else None
        
        return {
            "models_compared": len(results_to_compare),
            "best_latency": {
                "model_id": best_latency["model_id"],
                "latency_ms": best_latency["latency_ms"]["mean"]
            },
            "best_throughput": {
                "model_id": best_throughput["model_id"],
                "throughput": best_throughput["throughput_samples_per_sec"]
            },
            "best_accuracy": {
                "model_id": best_accuracy["model_id"],
                "accuracy": best_accuracy["accuracy_percent"]
            } if best_accuracy else None,
            "all_results": results_to_compare
        }
    
    def generate_report(self) -> str:
        """Generate benchmark report"""
        if not self.results:
            return "No benchmark results available"
        
        report = "PERFORMANCE BENCHMARK REPORT\n"
        report += "=" * 80 + "\n\n"
        
        for result in self.results:
            report += f"Model: {result['model_id']}\n"
            report += f"  Latency (mean): {result['latency_ms']['mean']:.2f}ms\n"
            report += f"  Throughput: {result['throughput_samples_per_sec']:.1f} samples/sec\n"
            if result['accuracy_percent']:
                report += f"  Accuracy: {result['accuracy_percent']:.2f}%\n"
            report += "\n"
        
        return report


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("PERFORMANCE BENCHMARKING DEMO")
    print("=" * 80)
    
    # Mock models
    def fast_model(x):
        time.sleep(0.001)  # 1ms
        return sum(x) > 50
    
    def slow_model(x):
        time.sleep(0.005)  # 5ms
        return sum(x) > 50
    
    def accurate_model(x):
        time.sleep(0.003)  # 3ms
        return sum(x) > 45  # More accurate
    
    # Test data
    import random
    test_data = [[random.randint(0, 20) for _ in range(5)] for _ in range(50)]
    true_labels = [sum(x) > 50 for x in test_data]
    
    # Benchmark
    print("\n" + "=" * 80)
    print("RUNNING BENCHMARKS")
    print("=" * 80)
    
    benchmark = PerformanceBenchmark()
    
    benchmark.benchmark_model(
        "fast_model",
        fast_model,
        test_data,
        true_labels,
        num_iterations=5
    )
    
    benchmark.benchmark_model(
        "slow_model",
        slow_model,
        test_data,
        true_labels,
        num_iterations=5
    )
    
    benchmark.benchmark_model(
        "accurate_model",
        accurate_model,
        test_data,
        true_labels,
        num_iterations=5
    )
    
    print(f"\n✅ Benchmarked 3 models")
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    comparison = benchmark.compare_benchmarks()
    
    print(f"\nBest Latency: {comparison['best_latency']['model_id']} "
          f"({comparison['best_latency']['latency_ms']:.2f}ms)")
    print(f"Best Throughput: {comparison['best_throughput']['model_id']} "
          f"({comparison['best_throughput']['throughput']:.1f} samples/sec)")
    if comparison['best_accuracy']:
        print(f"Best Accuracy: {comparison['best_accuracy']['model_id']} "
              f"({comparison['best_accuracy']['accuracy']:.2f}%)")
    
    # Report
    print("\n" + "=" * 80)
    print(benchmark.generate_report())
    print("=" * 80)

