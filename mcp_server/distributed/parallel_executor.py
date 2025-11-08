"""
Parallel Executor for Distributed Operations

Handles parallel model training, hyperparameter search, and cross-validation.
"""

import logging
import time
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ParallelTaskResult:
    """Result from a parallel task execution"""
    task_id: int
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None


class ParallelExecutor:
    """
    Executes tasks in parallel using process or thread pools.

    Features:
    - Parallel hyperparameter search
    - Distributed cross-validation
    - Parallel model training
    - Progress tracking
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = True,
        timeout: Optional[float] = None
    ):
        """
        Initialize parallel executor.

        Args:
            max_workers: Maximum parallel workers (None = CPU count)
            use_processes: Use processes (True) or threads (False)
            timeout: Timeout per task in seconds
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.timeout = timeout

        # Statistics
        self.total_tasks_executed = 0
        self.total_failures = 0

        logger.info(
            f"ParallelExecutor initialized (workers={max_workers or 'auto'}, "
            f"backend={'process' if use_processes else 'thread'})"
        )

    def execute_parallel(
        self,
        func: Callable,
        task_args: List[Tuple],
        task_kwargs: Optional[List[Dict[str, Any]]] = None
    ) -> List[ParallelTaskResult]:
        """
        Execute function in parallel with different arguments.

        Args:
            func: Function to execute
            task_args: List of argument tuples for each task
            task_kwargs: Optional list of kwargs dicts for each task

        Returns:
            List of ParallelTaskResult objects
        """
        n_tasks = len(task_args)
        logger.info(f"Executing {n_tasks} tasks in parallel")

        if task_kwargs is None:
            task_kwargs = [{}] * n_tasks

        # Choose executor type
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        results = []
        start_time = time.time()

        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task_id = {}
            for task_id, (args, kwargs) in enumerate(zip(task_args, task_kwargs)):
                future = executor.submit(self._execute_task, func, task_id, args, kwargs)
                future_to_task_id[future] = task_id

            # Collect results as they complete
            for future in as_completed(future_to_task_id, timeout=self.timeout):
                task_id = future_to_task_id[future]
                try:
                    result = future.result()
                    results.append(result)

                    if not result.success:
                        logger.warning(f"Task {task_id} failed: {result.error}")
                        self.total_failures += 1

                    self.total_tasks_executed += 1

                except Exception as e:
                    logger.error(f"Task {task_id} raised exception: {e}")
                    results.append(ParallelTaskResult(
                        task_id=task_id,
                        success=False,
                        error=str(e)
                    ))
                    self.total_failures += 1
                    self.total_tasks_executed += 1

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)

        logger.info(
            f"Parallel execution complete: {success_count}/{n_tasks} succeeded "
            f"in {total_time:.2f}s"
        )

        return results

    def _execute_task(
        self,
        func: Callable,
        task_id: int,
        args: Tuple,
        kwargs: Dict[str, Any]
    ) -> ParallelTaskResult:
        """Execute a single task and track metrics"""
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            return ParallelTaskResult(
                task_id=task_id,
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ParallelTaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def parallel_hyperparameter_search(
        self,
        model_class: type,
        X_train: Any,
        y_train: Any,
        param_grid: Dict[str, List[Any]],
        scoring_func: Callable
    ) -> Dict[str, Any]:
        """
        Perform parallel hyperparameter grid search.

        Args:
            model_class: Model class to instantiate
            X_train: Training features
            y_train: Training targets
            param_grid: Dictionary of hyperparameter lists
            scoring_func: Function to score models (lower is better)

        Returns:
            Dict with best params and results
        """
        logger.info("Starting parallel hyperparameter search")

        # Generate parameter combinations
        from itertools import product
        keys = param_grid.keys()
        values = param_grid.values()
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]

        logger.info(f"Testing {len(param_combinations)} parameter combinations")

        # Create task arguments
        task_args = [
            (model_class, X_train, y_train, params, scoring_func)
            for params in param_combinations
        ]

        # Execute in parallel
        results = self.execute_parallel(
            func=self._train_and_score,
            task_args=task_args
        )

        # Find best parameters
        successful_results = [r for r in results if r.success]
        if not successful_results:
            raise ValueError("All hyperparameter combinations failed")

        best_result = min(successful_results, key=lambda r: r.result["score"])

        return {
            "best_params": best_result.result["params"],
            "best_score": best_result.result["score"],
            "total_combinations": len(param_combinations),
            "successful_combinations": len(successful_results),
            "all_results": [
                {
                    "params": r.result["params"],
                    "score": r.result["score"],
                    "time": r.execution_time
                }
                for r in successful_results
            ]
        }

    @staticmethod
    def _train_and_score(
        model_class: type,
        X_train: Any,
        y_train: Any,
        params: Dict[str, Any],
        scoring_func: Callable
    ) -> Dict[str, Any]:
        """Train model with given params and return score"""
        # Instantiate and train model
        model = model_class(**params)
        model.fit(X_train, y_train)

        # Score model
        score = scoring_func(model, X_train, y_train)

        return {
            "params": params,
            "score": score,
            "model": model  # Note: May not be pickle-able for all models
        }

    def parallel_cross_validation(
        self,
        model_class: type,
        X: Any,
        y: Any,
        n_splits: int = 5,
        params: Optional[Dict[str, Any]] = None,
        scoring_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Perform k-fold cross-validation in parallel.

        Args:
            model_class: Model class to instantiate
            X: Features
            y: Targets
            n_splits: Number of cross-validation splits
            params: Model parameters
            scoring_func: Optional custom scoring function

        Returns:
            Dict with cross-validation results
        """
        logger.info(f"Starting {n_splits}-fold cross-validation in parallel")

        params = params or {}

        # Create train/test splits
        from sklearn.model_selection import KFold
        kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)

        task_args = []
        for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(X)):
            X_train = X[train_idx] if hasattr(X, '__getitem__') else X.iloc[train_idx]
            X_test = X[test_idx] if hasattr(X, '__getitem__') else X.iloc[test_idx]
            y_train = y[train_idx] if hasattr(y, '__getitem__') else y.iloc[train_idx]
            y_test = y[test_idx] if hasattr(y, '__getitem__') else y.iloc[test_idx]

            task_args.append((
                model_class, X_train, X_test, y_train, y_test, params, scoring_func, fold_idx
            ))

        # Execute folds in parallel
        results = self.execute_parallel(
            func=self._cv_fold,
            task_args=task_args
        )

        # Aggregate results
        successful_results = [r for r in results if r.success]
        scores = [r.result["score"] for r in successful_results]

        return {
            "n_splits": n_splits,
            "successful_folds": len(successful_results),
            "mean_score": np.mean(scores),
            "std_score": np.std(scores),
            "min_score": np.min(scores),
            "max_score": np.max(scores),
            "fold_scores": scores
        }

    @staticmethod
    def _cv_fold(
        model_class: type,
        X_train: Any,
        X_test: Any,
        y_train: Any,
        y_test: Any,
        params: Dict[str, Any],
        scoring_func: Optional[Callable],
        fold_idx: int
    ) -> Dict[str, Any]:
        """Execute a single cross-validation fold"""
        # Train model
        model = model_class(**params)
        model.fit(X_train, y_train)

        # Score on test set
        if scoring_func:
            score = scoring_func(model, X_test, y_test)
        else:
            # Default: use model's score method
            score = model.score(X_test, y_test)

        return {
            "fold": fold_idx,
            "score": score
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        success_rate = (
            (self.total_tasks_executed - self.total_failures) / self.total_tasks_executed
            if self.total_tasks_executed > 0 else 0.0
        )

        return {
            "total_tasks_executed": self.total_tasks_executed,
            "total_failures": self.total_failures,
            "success_rate": success_rate,
            "max_workers": self.max_workers,
            "backend": "process" if self.use_processes else "thread"
        }
