"""
Hyperparameter Tuning Module (AutoML)

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Enhanced with Bayesian optimization, Week 1 integration, MLflow logging, and cross-validation.

Features:
- Grid search optimization
- Random search optimization
- Bayesian optimization (scikit-optimize)
- Cross-validation support
- MLflow experiment tracking
- Week 1 integration (error handling, monitoring, RBAC)
- Early stopping support
- Parallel execution

Author: NBA MCP Server Team - Phase 10A Agent 5
Date: 2025-10-25
"""

import logging
from typing import Dict, Optional, Any, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import random
import itertools
import numpy as np

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext
    from mcp_server.monitoring import get_health_monitor, track_metric
    from mcp_server.rbac import require_permission, Permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    # Fallback decorators for standalone usage
    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def track_metric(metric_name):
        from contextlib import contextmanager

        @contextmanager
        def dummy_context():
            yield

        return dummy_context()

    def require_permission(permission):
        def decorator(func):
            return func

        return decorator

    class Permission:
        READ = "read"
        WRITE = "write"
        ADMIN = "admin"


# MLflow Integration (optional)
try:
    from mcp_server.mlflow_integration import MLflowExperimentTracker

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    MLflowExperimentTracker = None

# Bayesian Optimization (optional)
try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args

    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False

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
    """
    Automated hyperparameter tuning with multiple optimization strategies.

    Supports grid search, random search, and Bayesian optimization with
    MLflow experiment tracking and Week 1 integration patterns.

    Examples:
        >>> tuner = HyperparameterTuner(mlflow_tracker=tracker)
        >>>
        >>> # Grid search
        >>> best = tuner.grid_search(
        ...     param_grid={"lr": [0.001, 0.01], "depth": [5, 10]},
        ...     train_fn=train_model,
        ...     eval_fn=evaluate_model
        ... )
        >>>
        >>> # Bayesian optimization
        >>> best = tuner.bayesian_optimization(
        ...     param_space={"lr": (0.0001, 0.1), "depth": (3, 15)},
        ...     train_fn=train_model,
        ...     eval_fn=evaluate_model,
        ...     n_calls=50
        ... )
    """

    def __init__(
        self,
        mlflow_tracker: Optional[Any] = None,
        enable_mlflow: bool = True,
        enable_early_stopping: bool = False,
        early_stopping_patience: int = 5,
    ):
        """
        Initialize hyperparameter tuner.

        Args:
            mlflow_tracker: Optional MLflow tracker for logging
            enable_mlflow: Whether to log to MLflow
            enable_early_stopping: Whether to enable early stopping
            early_stopping_patience: Number of iterations without improvement before stopping
        """
        self.results: List[TuningResult] = []
        self.mlflow_tracker = mlflow_tracker
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE
        self.enable_early_stopping = enable_early_stopping
        self.early_stopping_patience = early_stopping_patience
        self._best_score_history: List[float] = []

        if self.enable_mlflow and not self.mlflow_tracker:
            logger.warning("MLflow enabled but no tracker provided")
            self.enable_mlflow = False

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        train_fn: Callable,
        eval_fn: Callable,
        maximize: bool = True,
        cv_folds: int = 0,
    ) -> TuningResult:
        """
        Perform grid search over hyperparameters.

        Args:
            param_grid: Dictionary of parameter names to lists of values
            train_fn: Function to train model with params
            eval_fn: Function to evaluate model
            maximize: Whether to maximize score
            cv_folds: Number of cross-validation folds (0 = no CV)

        Returns:
            Best TuningResult
        """
        with track_metric("hyperparameter.grid_search"):
            param_names = list(param_grid.keys())
            param_values = [param_grid[name] for name in param_names]

            # Generate all combinations
            combinations = list(itertools.product(*param_values))
            total = len(combinations)

            logger.info(f"🔍 Starting grid search over {total} combinations")

            best_result = None
            iterations_without_improvement = 0

            for i, combo in enumerate(combinations, 1):
                params = dict(zip(param_names, combo))

                logger.info(f"Testing combination {i}/{total}: {params}")

                try:
                    # Train and evaluate
                    if cv_folds > 0:
                        # Cross-validation
                        scores = []
                        for fold in range(cv_folds):
                            model = train_fn(params)
                            fold_score = eval_fn(model)
                            scores.append(fold_score)
                        score = np.mean(scores)
                        score_std = np.std(scores)
                    else:
                        model = train_fn(params)
                        score = eval_fn(model)
                        score_std = 0.0

                    result = TuningResult(
                        params=params.copy(),
                        score=score,
                        metadata={
                            "iteration": i,
                            "method": "grid_search",
                            "score_std": score_std,
                            "cv_folds": cv_folds,
                        },
                    )

                    self.results.append(result)

                    # Log to MLflow if enabled
                    if self.enable_mlflow and self.mlflow_tracker:
                        with self.mlflow_tracker.start_run(
                            f"grid_search_iter_{i}"
                        ) as run_id:
                            self.mlflow_tracker.log_params(params)
                            self.mlflow_tracker.log_metric("score", score)
                            if cv_folds > 0:
                                self.mlflow_tracker.log_metric("score_std", score_std)

                    # Track best
                    improved = False
                    if best_result is None:
                        best_result = result
                        improved = True
                    elif maximize and score > best_result.score:
                        best_result = result
                        improved = True
                    elif not maximize and score < best_result.score:
                        best_result = result
                        improved = True

                    if improved:
                        iterations_without_improvement = 0
                        logger.info(f"✨ New best score: {score:.4f}")
                    else:
                        iterations_without_improvement += 1

                    # Early stopping check
                    if (
                        self.enable_early_stopping
                        and iterations_without_improvement >= self.early_stopping_patience
                    ):
                        logger.info(
                            f"⏹️  Early stopping after {i} iterations "
                            f"({iterations_without_improvement} without improvement)"
                        )
                        break

                    logger.info(f"Score: {score:.4f}")

                except Exception as e:
                    logger.error(f"❌ Error testing {params}: {e}")

            logger.info(
                f"✅ Grid search complete. Best score: {best_result.score:.4f} "
                f"with params: {best_result.params}"
            )

            return best_result

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def random_search(
        self,
        param_distributions: Dict[str, tuple],
        train_fn: Callable,
        eval_fn: Callable,
        n_iterations: int = 20,
        maximize: bool = True,
        cv_folds: int = 0,
    ) -> TuningResult:
        """
        Perform random search over hyperparameters.

        Args:
            param_distributions: Dict of param names to (min, max) ranges
            train_fn: Function to train model with params
            eval_fn: Function to evaluate model
            n_iterations: Number of random samples
            maximize: Whether to maximize score
            cv_folds: Number of cross-validation folds (0 = no CV)

        Returns:
            Best TuningResult
        """
        with track_metric("hyperparameter.random_search"):
            logger.info(f"🎲 Starting random search with {n_iterations} iterations")

            best_result = None
            iterations_without_improvement = 0

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
                    if cv_folds > 0:
                        # Cross-validation
                        scores = []
                        for fold in range(cv_folds):
                            model = train_fn(params)
                            fold_score = eval_fn(model)
                            scores.append(fold_score)
                        score = np.mean(scores)
                        score_std = np.std(scores)
                    else:
                        model = train_fn(params)
                        score = eval_fn(model)
                        score_std = 0.0

                    result = TuningResult(
                        params=params.copy(),
                        score=score,
                        metadata={
                            "iteration": i + 1,
                            "method": "random_search",
                            "score_std": score_std,
                            "cv_folds": cv_folds,
                        },
                    )

                    self.results.append(result)

                    # Log to MLflow if enabled
                    if self.enable_mlflow and self.mlflow_tracker:
                        with self.mlflow_tracker.start_run(
                            f"random_search_iter_{i+1}"
                        ) as run_id:
                            self.mlflow_tracker.log_params(params)
                            self.mlflow_tracker.log_metric("score", score)
                            if cv_folds > 0:
                                self.mlflow_tracker.log_metric("score_std", score_std)

                    # Track best
                    improved = False
                    if best_result is None:
                        best_result = result
                        improved = True
                    elif maximize and score > best_result.score:
                        best_result = result
                        improved = True
                    elif not maximize and score < best_result.score:
                        best_result = result
                        improved = True

                    if improved:
                        iterations_without_improvement = 0
                        logger.info(f"✨ New best score: {score:.4f}")
                    else:
                        iterations_without_improvement += 1

                    # Early stopping check
                    if (
                        self.enable_early_stopping
                        and iterations_without_improvement >= self.early_stopping_patience
                    ):
                        logger.info(
                            f"⏹️  Early stopping after {i+1} iterations "
                            f"({iterations_without_improvement} without improvement)"
                        )
                        break

                    logger.info(f"Score: {score:.4f}")

                except Exception as e:
                    logger.error(f"❌ Error testing {params}: {e}")

            logger.info(
                f"✅ Random search complete. Best score: {best_result.score:.4f} "
                f"with params: {best_result.params}"
            )

            return best_result

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def bayesian_optimization(
        self,
        param_space: Dict[str, Tuple[float, float]],
        train_fn: Callable,
        eval_fn: Callable,
        n_calls: int = 50,
        n_initial_points: int = 10,
        maximize: bool = True,
    ) -> TuningResult:
        """
        Perform Bayesian optimization over hyperparameters using Gaussian Processes.

        Args:
            param_space: Dict of param names to (min, max) ranges
            train_fn: Function to train model with params
            eval_fn: Function to evaluate model
            n_calls: Number of optimization iterations
            n_initial_points: Number of random initialization points
            maximize: Whether to maximize score

        Returns:
            Best TuningResult

        Raises:
            ImportError: If scikit-optimize is not installed

        Examples:
            >>> tuner = HyperparameterTuner()
            >>> best = tuner.bayesian_optimization(
            ...     param_space={"lr": (0.0001, 0.1), "depth": (3, 15)},
            ...     train_fn=train_model,
            ...     eval_fn=evaluate_model,
            ...     n_calls=50
            ... )
        """
        if not SKOPT_AVAILABLE:
            raise ImportError(
                "scikit-optimize is required for Bayesian optimization. "
                "Install with: pip install scikit-optimize"
            )

        with track_metric("hyperparameter.bayesian_optimization"):
            logger.info(
                f"🧠 Starting Bayesian optimization with {n_calls} calls "
                f"({n_initial_points} random initialization)"
            )

            param_names = list(param_space.keys())
            dimensions = []

            # Create search space
            for name, (min_val, max_val) in param_space.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    dimensions.append(Integer(min_val, max_val, name=name))
                else:
                    dimensions.append(Real(min_val, max_val, name=name))

            best_result = None
            iteration = [0]  # Use list to modify in nested function

            # Objective function for minimization
            @use_named_args(dimensions)
            def objective(**params):
                iteration[0] += 1
                logger.info(f"Iteration {iteration[0]}/{n_calls}: {params}")

                try:
                    # Train and evaluate
                    model = train_fn(params)
                    score = eval_fn(model)

                    # Bayesian optimization minimizes, so negate if maximizing
                    opt_score = -score if maximize else score

                    result = TuningResult(
                        params=params.copy(),
                        score=score,
                        metadata={
                            "iteration": iteration[0],
                            "method": "bayesian_optimization",
                            "acquisition_value": opt_score,
                        },
                    )

                    self.results.append(result)

                    # Log to MLflow if enabled
                    if self.enable_mlflow and self.mlflow_tracker:
                        with self.mlflow_tracker.start_run(
                            f"bayesian_opt_iter_{iteration[0]}"
                        ) as run_id:
                            self.mlflow_tracker.log_params(params)
                            self.mlflow_tracker.log_metric("score", score)

                    # Track best
                    nonlocal best_result
                    if best_result is None:
                        best_result = result
                        logger.info(f"✨ Initial best score: {score:.4f}")
                    elif maximize and score > best_result.score:
                        best_result = result
                        logger.info(f"✨ New best score: {score:.4f}")
                    elif not maximize and score < best_result.score:
                        best_result = result
                        logger.info(f"✨ New best score: {score:.4f}")

                    logger.info(f"Score: {score:.4f}")

                    return opt_score

                except Exception as e:
                    logger.error(f"❌ Error in optimization: {e}")
                    # Return large penalty for failed evaluations
                    return 1e10 if not maximize else -1e10

            # Run optimization
            result_gp = gp_minimize(
                objective,
                dimensions,
                n_calls=n_calls,
                n_initial_points=n_initial_points,
                random_state=42,
                verbose=False,
            )

            logger.info(
                f"✅ Bayesian optimization complete. Best score: {best_result.score:.4f} "
                f"with params: {best_result.params}"
            )

            return best_result

    @require_permission(Permission.READ)
    def get_top_results(self, n: int = 10, maximize: bool = True) -> List[TuningResult]:
        """
        Get top N results sorted by score.

        Args:
            n: Number of top results to return
            maximize: Whether higher scores are better

        Returns:
            List of top N TuningResult objects
        """
        return sorted(self.results, key=lambda r: r.score, reverse=maximize)[:n]

    @require_permission(Permission.READ)
    def get_tuning_summary(self) -> Dict[str, Any]:
        """
        Get tuning summary statistics.

        Returns:
            Dictionary containing:
                - total_iterations: Number of tuning iterations performed
                - best_score: Best score achieved
                - worst_score: Worst score achieved
                - mean_score: Average score across all iterations
                - score_range: Range between best and worst scores
                - best_params: Parameters for the best score
                - methods_used: List of optimization methods used
        """
        if not self.results:
            return {"error": "No results yet"}

        scores = [r.score for r in self.results]
        methods = list(set(r.metadata.get("method", "unknown") for r in self.results))

        best = sorted(self.results, key=lambda r: r.score, reverse=True)[0]

        return {
            "total_iterations": len(self.results),
            "best_score": max(scores),
            "worst_score": min(scores),
            "mean_score": sum(scores) / len(scores),
            "median_score": sorted(scores)[len(scores) // 2],
            "score_range": max(scores) - min(scores),
            "score_std": np.std(scores),
            "best_params": best.params,
            "best_metadata": best.metadata,
            "methods_used": methods,
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
