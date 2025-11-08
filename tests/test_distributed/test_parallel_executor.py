"""
Tests for ParallelExecutor

Tests parallel task execution, hyperparameter search, and cross-validation.
"""

import pytest
import numpy as np
from time import sleep
from mcp_server.distributed.parallel_executor import ParallelExecutor, ParallelTaskResult


# Simple test functions
def simple_add(a, b):
    """Add two numbers"""
    return a + b


def slow_function(delay):
    """Function that sleeps"""
    sleep(delay)
    return delay


def failing_function():
    """Function that always fails"""
    raise ValueError("This function always fails")


def square_number(x):
    """Square a number"""
    return x ** 2


# Simple model class for testing
class DummyModel:
    """Simple model for testing"""

    def __init__(self, param_a=1.0, param_b=0.0):
        self.param_a = param_a
        self.param_b = param_b
        self.coef_ = None

    def fit(self, X, y):
        # Simple linear fit: y = param_a * X + param_b
        self.coef_ = self.param_a
        return self

    def predict(self, X):
        return self.param_a * X + self.param_b

    def score(self, X, y):
        predictions = self.predict(X)
        mse = np.mean((y - predictions) ** 2)
        return mse


class TestParallelExecutor:
    """Test suite for ParallelExecutor"""

    @pytest.fixture
    def executor(self):
        """Create executor instance"""
        return ParallelExecutor(max_workers=2, use_processes=False)

    def test_executor_initialization(self):
        """Test executor initializes correctly"""
        executor = ParallelExecutor(max_workers=4, use_processes=True)

        assert executor.max_workers == 4
        assert executor.use_processes is True
        assert executor.total_tasks_executed == 0
        assert executor.total_failures == 0

    def test_execute_simple_tasks(self, executor):
        """Test executing simple parallel tasks"""
        task_args = [(1, 2), (3, 4), (5, 6)]

        results = executor.execute_parallel(simple_add, task_args)

        assert len(results) == 3
        assert all(isinstance(r, ParallelTaskResult) for r in results)
        assert all(r.success for r in results)
        assert sorted([r.result for r in results]) == [3, 7, 11]

    def test_execute_with_kwargs(self, executor):
        """Test execution with keyword arguments"""
        task_args = [(1,), (2,), (3,)]
        task_kwargs = [{"b": 10}, {"b": 20}, {"b": 30}]

        results = executor.execute_parallel(
            simple_add,
            task_args,
            task_kwargs
        )

        assert len(results) == 3
        assert sorted([r.result for r in results]) == [11, 22, 33]

    def test_execution_timing(self, executor):
        """Test that execution times are tracked"""
        task_args = [(0.1,), (0.05,)]

        results = executor.execute_parallel(slow_function, task_args)

        for result in results:
            assert result.execution_time > 0.0
            assert result.execution_time < 1.0  # Should be quick

    def test_task_failure_handling(self, executor):
        """Test handling of failed tasks"""
        task_args = [(), (), ()]

        results = executor.execute_parallel(failing_function, task_args)

        assert len(results) == 3
        assert all(not r.success for r in results)
        assert all(r.error is not None for r in results)
        assert executor.total_failures == 3

    def test_mixed_success_and_failure(self, executor):
        """Test mix of successful and failed tasks"""
        # Mix of functions
        def sometimes_fail(x):
            if x < 0:
                raise ValueError("Negative not allowed")
            return x ** 2

        task_args = [(2,), (-1,), (3,), (-2,), (4,)]

        results = executor.execute_parallel(sometimes_fail, task_args)

        assert len(results) == 5
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        assert len(successful) == 3
        assert len(failed) == 2

    def test_parallel_hyperparameter_search(self, executor):
        """Test parallel hyperparameter grid search"""
        # Generate simple data
        X_train = np.array([1, 2, 3, 4, 5])
        y_train = np.array([2, 4, 6, 8, 10])  # y = 2*x

        param_grid = {
            "param_a": [1.0, 1.5, 2.0, 2.5],
            "param_b": [0.0, 0.5]
        }

        def scoring_func(model, X, y):
            return model.score(X, y)

        result = executor.parallel_hyperparameter_search(
            model_class=DummyModel,
            X_train=X_train,
            y_train=y_train,
            param_grid=param_grid,
            scoring_func=scoring_func
        )

        assert "best_params" in result
        assert "best_score" in result
        assert result["total_combinations"] == 8  # 4 * 2
        assert result["successful_combinations"] > 0

        # Best params should be close to true values (param_a=2, param_b=0)
        assert result["best_params"]["param_a"] == pytest.approx(2.0, rel=0.5)

    def test_parallel_cross_validation(self, executor):
        """Test parallel k-fold cross-validation"""
        # Generate simple data
        np.random.seed(42)
        X = np.random.randn(100)
        y = 2 * X + 1 + np.random.randn(100) * 0.1

        result = executor.parallel_cross_validation(
            model_class=DummyModel,
            X=X,
            y=y,
            n_splits=3,
            params={"param_a": 2.0, "param_b": 1.0}
        )

        assert result["n_splits"] == 3
        assert result["successful_folds"] == 3
        assert "mean_score" in result
        assert "std_score" in result
        assert len(result["fold_scores"]) == 3
        assert all(score >= 0 for score in result["fold_scores"])

    def test_get_statistics(self, executor):
        """Test getting executor statistics"""
        # Execute some tasks
        task_args = [(1, 2), (3, 4)]
        executor.execute_parallel(simple_add, task_args)

        # Execute some failing tasks
        task_args = [(), ()]
        executor.execute_parallel(failing_function, task_args)

        stats = executor.get_statistics()

        assert stats["total_tasks_executed"] == 4
        assert stats["total_failures"] == 2
        assert stats["success_rate"] == 0.5
        assert stats["backend"] == "thread"

    def test_process_vs_thread_executor(self):
        """Test both process and thread-based execution"""
        # Thread executor
        thread_executor = ParallelExecutor(use_processes=False)
        task_args = [(2,), (3,), (4,)]
        thread_results = thread_executor.execute_parallel(square_number, task_args)

        # Process executor
        process_executor = ParallelExecutor(use_processes=True)
        process_results = process_executor.execute_parallel(square_number, task_args)

        # Both should give same results
        thread_values = sorted([r.result for r in thread_results])
        process_values = sorted([r.result for r in process_results])

        assert thread_values == process_values == [4, 9, 16]

    def test_auto_worker_count(self):
        """Test that auto worker count works"""
        executor = ParallelExecutor(max_workers=None)

        task_args = [(1,), (2,), (3,)]
        results = executor.execute_parallel(square_number, task_args)

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_large_parallel_workload(self, executor):
        """Test handling large number of parallel tasks"""
        n_tasks = 100
        task_args = [(i,) for i in range(n_tasks)]

        results = executor.execute_parallel(square_number, task_args)

        assert len(results) == n_tasks
        assert all(r.success for r in results)
        expected = [i**2 for i in range(n_tasks)]
        actual = sorted([r.result for r in results])
        assert actual == expected

    def test_hyperparameter_search_with_failures(self, executor):
        """Test hyperparameter search handles model failures"""

        class FailingModel:
            def __init__(self, param_a=1.0):
                if param_a < 0:
                    raise ValueError("param_a must be positive")
                self.param_a = param_a

            def fit(self, X, y):
                return self

            def score(self, X, y):
                return self.param_a

        X_train = np.array([1, 2, 3])
        y_train = np.array([2, 4, 6])

        param_grid = {
            "param_a": [-1.0, 0.5, 1.0, 1.5]  # One invalid value
        }

        def scoring_func(model, X, y):
            return model.score(X, y)

        result = executor.parallel_hyperparameter_search(
            model_class=FailingModel,
            X_train=X_train,
            y_train=y_train,
            param_grid=param_grid,
            scoring_func=scoring_func
        )

        # Should still find best among successful combinations
        assert result["successful_combinations"] == 3
        assert result["best_params"]["param_a"] > 0

    def test_cross_validation_with_pandas(self, executor):
        """Test cross-validation with pandas DataFrame"""
        import pandas as pd

        # Create pandas DataFrame
        np.random.seed(42)
        df = pd.DataFrame({
            "X": np.random.randn(50),
            "y": np.random.randn(50)
        })

        X = df["X"].values
        y = df["y"].values

        result = executor.parallel_cross_validation(
            model_class=DummyModel,
            X=X,
            y=y,
            n_splits=5,
            params={"param_a": 1.0, "param_b": 0.0}
        )

        assert result["n_splits"] == 5
        assert result["successful_folds"] == 5
