"""
Hyperparameter Tuning Module (AutoML)
Automated hyperparameter optimization using grid search and random search.
"""

import logging
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import random
import itertools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TuningResult:
    """Result from hyperparameter tuning"""

    params: Dict[str, Any]
    score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HyperparameterTuner:
    """Automated hyperparameter tuning"""

    def __init__(self):
        """Initialize hyperparameter tuner"""
        self.results: List[TuningResult] = []

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        train_fn: Callable,
        eval_fn: Callable,
        maximize: bool = True,
    ) -> TuningResult:
        """
        Perform grid search over hyperparameters.

        Args:
            param_grid: Dictionary of parameter names to lists of values
            train_fn: Function to train model with params
            eval_fn: Function to evaluate model
            maximize: Whether to maximize score

        Returns:
            Best TuningResult
        """
        param_names = list(param_grid.keys())
        param_values = [param_grid[name] for name in param_names]

        # Generate all combinations
        combinations = list(itertools.product(*param_values))
        total = len(combinations)

        logger.info(f"Starting grid search over {total} combinations")

        best_result = None

        for i, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))

            logger.info(f"Testing combination {i}/{total}: {params}")

            try:
                # Train and evaluate
                model = train_fn(params)
                score = eval_fn(model)

                result = TuningResult(
                    params=params.copy(), score=score, metadata={"iteration": i}
                )

                self.results.append(result)

                # Track best
                if best_result is None:
                    best_result = result
                elif maximize and score > best_result.score:
                    best_result = result
                elif not maximize and score < best_result.score:
                    best_result = result

                logger.info(f"Score: {score:.4f}")

            except Exception as e:
                logger.error(f"Error testing {params}: {e}")

        logger.info(
            f"Grid search complete. Best score: {best_result.score:.4f} "
            f"with params: {best_result.params}"
        )

        return best_result

    def random_search(
        self,
        param_distributions: Dict[str, tuple],
        train_fn: Callable,
        eval_fn: Callable,
        n_iterations: int = 20,
        maximize: bool = True,
    ) -> TuningResult:
        """
        Perform random search over hyperparameters.

        Args:
            param_distributions: Dict of param names to (min, max) ranges
            train_fn: Function to train model with params
            eval_fn: Function to evaluate model
            n_iterations: Number of random samples
            maximize: Whether to maximize score

        Returns:
            Best TuningResult
        """
        logger.info(f"Starting random search with {n_iterations} iterations")

        best_result = None

        for i in range(n_iterations):
            # Sample random parameters
            params = {}
            for name, (min_val, max_val) in param_distributions.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[name] = random.randint(min_val, max_val)
                else:
                    params[name] = random.uniform(min_val, max_val)

            logger.info(f"Iteration {i+1}/{n_iterations}: {params}")

            try:
                # Train and evaluate
                model = train_fn(params)
                score = eval_fn(model)

                result = TuningResult(
                    params=params.copy(), score=score, metadata={"iteration": i + 1}
                )

                self.results.append(result)

                # Track best
                if best_result is None:
                    best_result = result
                elif maximize and score > best_result.score:
                    best_result = result
                elif not maximize and score < best_result.score:
                    best_result = result

                logger.info(f"Score: {score:.4f}")

            except Exception as e:
                logger.error(f"Error testing {params}: {e}")

        logger.info(
            f"Random search complete. Best score: {best_result.score:.4f} "
            f"with params: {best_result.params}"
        )

        return best_result

    def get_top_results(self, n: int = 10) -> List[TuningResult]:
        """Get top N results"""
        return sorted(self.results, key=lambda r: r.score, reverse=True)[:n]

    def get_tuning_summary(self) -> Dict[str, Any]:
        """Get tuning summary statistics"""
        if not self.results:
            return {"error": "No results yet"}

        scores = [r.score for r in self.results]

        return {
            "total_iterations": len(self.results),
            "best_score": max(scores),
            "worst_score": min(scores),
            "mean_score": sum(scores) / len(scores),
            "score_range": max(scores) - min(scores),
            "best_params": sorted(self.results, key=lambda r: r.score, reverse=True)[
                0
            ].params,
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("HYPERPARAMETER TUNING DEMO")
    print("=" * 80)

    tuner = HyperparameterTuner()

    # Mock training and evaluation functions
    def train_model(params):
        """Mock training function"""
        return {"params": params, "trained": True}

    def evaluate_model(model):
        """Mock evaluation function - simulates accuracy"""
        params = model["params"]
        # Simulate accuracy based on params
        # Best combo: n_estimators=200, max_depth=10, min_samples_split=5
        score = 0.7
        score += (200 - abs(params["n_estimators"] - 200)) / 1000
        score += (10 - abs(params["max_depth"] - 10)) / 100
        score += (5 - abs(params["min_samples_split"] - 5)) / 100
        score += random.uniform(-0.02, 0.02)  # Add noise
        return max(0, min(1, score))  # Clamp to [0, 1]

    # Grid Search
    print("\n" + "=" * 80)
    print("GRID SEARCH")
    print("=" * 80)

    param_grid = {
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, 15],
        "min_samples_split": [2, 5, 10],
    }

    print(f"\nSearching over {len(param_grid)} parameters...")

    best_grid = tuner.grid_search(
        param_grid=param_grid,
        train_fn=train_model,
        eval_fn=evaluate_model,
        maximize=True,
    )

    print(f"\n✅ Grid Search Complete")
    print(f"Best Score: {best_grid.score:.4f}")
    print(f"Best Params: {best_grid.params}")

    # Random Search
    print("\n" + "=" * 80)
    print("RANDOM SEARCH")
    print("=" * 80)

    tuner_random = HyperparameterTuner()

    param_distributions = {
        "n_estimators": (10, 300),
        "max_depth": (3, 20),
        "min_samples_split": (2, 20),
    }

    print(f"\nPerforming 15 random samples...")

    best_random = tuner_random.random_search(
        param_distributions=param_distributions,
        train_fn=train_model,
        eval_fn=evaluate_model,
        n_iterations=15,
        maximize=True,
    )

    print(f"\n✅ Random Search Complete")
    print(f"Best Score: {best_random.score:.4f}")
    print(f"Best Params: {best_random.params}")

    # Summary
    print("\n" + "=" * 80)
    print("TUNING SUMMARY")
    print("=" * 80)

    summary = tuner.get_tuning_summary()
    print(f"\nGrid Search:")
    print(f"  Total Iterations: {summary['total_iterations']}")
    print(f"  Best Score: {summary['best_score']:.4f}")
    print(f"  Mean Score: {summary['mean_score']:.4f}")
    print(f"  Score Range: {summary['score_range']:.4f}")

    summary_random = tuner_random.get_tuning_summary()
    print(f"\nRandom Search:")
    print(f"  Total Iterations: {summary_random['total_iterations']}")
    print(f"  Best Score: {summary_random['best_score']:.4f}")
    print(f"  Mean Score: {summary_random['mean_score']:.4f}")
    print(f"  Score Range: {summary_random['score_range']:.4f}")

    # Top results
    print("\n" + "=" * 80)
    print("TOP 5 RESULTS (All Searches)")
    print("=" * 80)

    all_results = tuner.results + tuner_random.results
    top_5 = sorted(all_results, key=lambda r: r.score, reverse=True)[:5]

    for i, result in enumerate(top_5, 1):
        print(f"\n{i}. Score: {result.score:.4f}")
        print(f"   Params: {result.params}")

    print("\n" + "=" * 80)
    print("Hyperparameter Tuning Demo Complete!")
    print("=" * 80)
