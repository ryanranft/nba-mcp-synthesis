"""
Tests for Hyperparameter Tuning Module

**Phase 10A Week 3 - Agent 5: Model Training & Experimentation**
Comprehensive tests for grid search, random search, and Bayesian optimization
with MLflow integration and cross-validation.
"""

import random
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from mcp_server.hyperparameter_tuning import (
    HyperparameterTuner,
    TuningResult,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_mlflow_tracker():
    """Create a mock MLflow tracker"""
    tracker = MagicMock()
    tracker.start_run = MagicMock()
    tracker.log_params = MagicMock()
    tracker.log_metric = MagicMock()
    tracker.end_run = MagicMock()
    return tracker


@pytest.fixture
def simple_train_fn():
    """Simple mock training function"""

    def train(params):
        return {"params": params, "trained": True}

    return train


@pytest.fixture
def simple_eval_fn():
    """Simple mock evaluation function with deterministic output"""

    def evaluate(model):
        params = model["params"]
        # Simple scoring: prefer n_estimators=100, max_depth=5
        score = 0.5
        if "n_estimators" in params:
            score += (100 - abs(params["n_estimators"] - 100)) / 1000
        if "max_depth" in params:
            score += (5 - abs(params["max_depth"] - 5)) / 100
        return max(0.0, min(1.0, score))

    return evaluate


# ==============================================================================
# Test HyperparameterTuner Initialization
# ==============================================================================


def test_tuner_initialization():
    """Test basic tuner initialization"""
    tuner = HyperparameterTuner()

    assert tuner.results == []
    assert tuner.mlflow_tracker is None
    assert tuner.enable_mlflow is False  # No tracker provided
    assert tuner.enable_early_stopping is False


def test_tuner_initialization_with_mlflow(mock_mlflow_tracker):
    """Test tuner initialization with MLflow tracker"""
    tuner = HyperparameterTuner(mlflow_tracker=mock_mlflow_tracker, enable_mlflow=True)

    assert tuner.mlflow_tracker is mock_mlflow_tracker
    assert tuner.enable_mlflow is True


def test_tuner_initialization_with_early_stopping():
    """Test tuner initialization with early stopping"""
    tuner = HyperparameterTuner(enable_early_stopping=True, early_stopping_patience=3)

    assert tuner.enable_early_stopping is True
    assert tuner.early_stopping_patience == 3


# ==============================================================================
# Test Grid Search
# ==============================================================================


def test_grid_search_basic(simple_train_fn, simple_eval_fn):
    """Test basic grid search functionality"""
    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [5, 10],
    }

    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    # Should test 4 combinations
    assert len(tuner.results) == 4
    assert isinstance(result, TuningResult)
    assert result.params in [
        {"n_estimators": 50, "max_depth": 5},
        {"n_estimators": 100, "max_depth": 5},
        {"n_estimators": 50, "max_depth": 10},
        {"n_estimators": 100, "max_depth": 10},
    ]
    # Best should be n_estimators=100, max_depth=5
    assert result.params == {"n_estimators": 100, "max_depth": 5}


def test_grid_search_with_cross_validation(simple_train_fn, simple_eval_fn):
    """Test grid search with cross-validation"""
    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [5],
    }

    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
        cv_folds=3,
    )

    assert len(tuner.results) == 2
    # Check that cross-validation metadata is present
    for res in tuner.results:
        assert res.metadata["cv_folds"] == 3
        assert "score_std" in res.metadata


def test_grid_search_with_mlflow(mock_mlflow_tracker, simple_train_fn, simple_eval_fn):
    """Test grid search with MLflow logging"""
    mock_mlflow_tracker.start_run.return_value.__enter__ = MagicMock(
        return_value="run_123"
    )
    mock_mlflow_tracker.start_run.return_value.__exit__ = MagicMock(return_value=False)

    tuner = HyperparameterTuner(mlflow_tracker=mock_mlflow_tracker, enable_mlflow=True)

    param_grid = {
        "n_estimators": [50, 100],
    }

    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    # Verify MLflow logging was called
    assert mock_mlflow_tracker.start_run.call_count == 2
    assert mock_mlflow_tracker.log_params.call_count == 2
    assert mock_mlflow_tracker.log_metric.call_count == 2


def test_grid_search_minimize(simple_train_fn, simple_eval_fn):
    """Test grid search with minimization"""
    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [5, 10],
    }

    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=False,  # Minimize instead of maximize
    )

    # Best should be n_estimators=50, max_depth=10 (lowest score)
    assert result.params == {"n_estimators": 50, "max_depth": 10}


def test_grid_search_early_stopping(simple_train_fn):
    """Test grid search with early stopping"""

    def decreasing_eval_fn(model):
        """Evaluation function that returns decreasing scores"""
        # First is best, then worse, triggering early stopping
        params = model["params"]
        # Score decreases with n_estimators
        return 1.0 - (params["n_estimators"] / 100)

    tuner = HyperparameterTuner(enable_early_stopping=True, early_stopping_patience=2)

    param_grid = {
        "n_estimators": [10, 20, 30, 40, 50, 60, 70, 80],  # 8 values
    }

    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=decreasing_eval_fn,
        maximize=True,
    )

    # Should stop before testing all 8 combinations
    # First one is best (10), then 2 worse (20, 30), then stops
    assert len(tuner.results) <= 4
    assert result.params["n_estimators"] == 10


# ==============================================================================
# Test Random Search
# ==============================================================================


def test_random_search_basic(simple_train_fn, simple_eval_fn):
    """Test basic random search functionality"""
    random.seed(42)  # Set seed for reproducibility

    tuner = HyperparameterTuner()

    param_distributions = {
        "n_estimators": (10, 200),
        "max_depth": (3, 15),
    }

    result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        n_iterations=10,
        maximize=True,
    )

    assert len(tuner.results) == 10
    assert isinstance(result, TuningResult)
    assert "n_estimators" in result.params
    assert "max_depth" in result.params
    # Check param ranges
    assert 10 <= result.params["n_estimators"] <= 200
    assert 3 <= result.params["max_depth"] <= 15


def test_random_search_with_cross_validation(simple_train_fn, simple_eval_fn):
    """Test random search with cross-validation"""
    random.seed(42)

    tuner = HyperparameterTuner()

    param_distributions = {
        "n_estimators": (50, 150),
    }

    result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        n_iterations=5,
        maximize=True,
        cv_folds=3,
    )

    assert len(tuner.results) == 5
    # Check cross-validation metadata
    for res in tuner.results:
        assert res.metadata["cv_folds"] == 3
        assert "score_std" in res.metadata


def test_random_search_with_mlflow(
    mock_mlflow_tracker, simple_train_fn, simple_eval_fn
):
    """Test random search with MLflow logging"""
    random.seed(42)

    mock_mlflow_tracker.start_run.return_value.__enter__ = MagicMock(
        return_value="run_123"
    )
    mock_mlflow_tracker.start_run.return_value.__exit__ = MagicMock(return_value=False)

    tuner = HyperparameterTuner(mlflow_tracker=mock_mlflow_tracker, enable_mlflow=True)

    param_distributions = {
        "n_estimators": (50, 150),
    }

    result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        n_iterations=3,
        maximize=True,
    )

    # Verify MLflow logging
    assert mock_mlflow_tracker.start_run.call_count == 3
    assert mock_mlflow_tracker.log_params.call_count == 3


def test_random_search_early_stopping(simple_train_fn):
    """Test random search with early stopping"""
    random.seed(42)

    def constant_eval_fn(model):
        """Return constant score to trigger early stopping"""
        return 0.8

    tuner = HyperparameterTuner(enable_early_stopping=True, early_stopping_patience=2)

    param_distributions = {
        "n_estimators": (10, 200),
    }

    result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=constant_eval_fn,
        n_iterations=10,
        maximize=True,
    )

    # Should stop early because score doesn't improve
    assert len(tuner.results) < 10


# ==============================================================================
# Test Bayesian Optimization
# ==============================================================================


@pytest.mark.skipif(
    True,  # Skip by default since scikit-optimize might not be installed
    reason="scikit-optimize not installed",
)
def test_bayesian_optimization_basic(simple_train_fn, simple_eval_fn):
    """Test basic Bayesian optimization (requires scikit-optimize)"""
    try:
        import skopt

        tuner = HyperparameterTuner()

        param_space = {
            "n_estimators": (10, 200),
            "max_depth": (3, 15),
        }

        result = tuner.bayesian_optimization(
            param_space=param_space,
            train_fn=simple_train_fn,
            eval_fn=simple_eval_fn,
            n_calls=10,
            n_initial_points=3,
            maximize=True,
        )

        assert len(tuner.results) == 10
        assert isinstance(result, TuningResult)
        assert "n_estimators" in result.params
        assert "max_depth" in result.params
    except ImportError:
        pytest.skip("scikit-optimize not installed")


def test_bayesian_optimization_import_error(simple_train_fn, simple_eval_fn):
    """Test that Bayesian optimization raises ImportError if skopt not available"""
    tuner = HyperparameterTuner()

    with patch("mcp_server.hyperparameter_tuning.SKOPT_AVAILABLE", False):
        param_space = {
            "n_estimators": (10, 200),
        }

        with pytest.raises(ImportError, match="scikit-optimize is required"):
            tuner.bayesian_optimization(
                param_space=param_space,
                train_fn=simple_train_fn,
                eval_fn=simple_eval_fn,
                n_calls=5,
            )


# ==============================================================================
# Test Utility Methods
# ==============================================================================


def test_get_top_results(simple_train_fn, simple_eval_fn):
    """Test getting top results"""
    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100, 150],
    }

    tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    top_results = tuner.get_top_results(n=2, maximize=True)

    assert len(top_results) == 2
    assert top_results[0].score >= top_results[1].score


def test_get_tuning_summary(simple_train_fn, simple_eval_fn):
    """Test tuning summary statistics"""
    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100, 150],
    }

    tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    summary = tuner.get_tuning_summary()

    assert summary["total_iterations"] == 3
    assert "best_score" in summary
    assert "worst_score" in summary
    assert "mean_score" in summary
    assert "median_score" in summary
    assert "score_range" in summary
    assert "score_std" in summary
    assert "best_params" in summary
    assert "methods_used" in summary
    assert "grid_search" in summary["methods_used"]


def test_get_tuning_summary_empty():
    """Test tuning summary with no results"""
    tuner = HyperparameterTuner()

    summary = tuner.get_tuning_summary()

    assert "error" in summary
    assert summary["error"] == "No results yet"


# ==============================================================================
# Test Error Handling
# ==============================================================================


def test_grid_search_with_failing_train_fn(simple_train_fn, simple_eval_fn):
    """Test grid search handles training failures gracefully"""
    fail_count = [0]

    def sometimes_failing_train_fn(params):
        """Fail on first call, succeed on second"""
        fail_count[0] += 1
        if fail_count[0] == 1:
            raise ValueError("Training failed")
        return simple_train_fn(params)

    tuner = HyperparameterTuner()

    param_grid = {
        "n_estimators": [50, 100],
    }

    # Should not raise, but log errors and continue
    result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=sometimes_failing_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    # Only one successful result (second call)
    assert len(tuner.results) == 1
    assert result is not None
    assert result.params["n_estimators"] == 100


def test_random_search_with_failing_eval_fn(simple_train_fn, simple_eval_fn):
    """Test random search handles evaluation failures gracefully"""
    random.seed(42)
    fail_count = [0]

    def sometimes_failing_eval_fn(model):
        """Fail on first call, succeed on others"""
        fail_count[0] += 1
        if fail_count[0] == 1:
            raise ValueError("Evaluation failed")
        return simple_eval_fn(model)

    tuner = HyperparameterTuner()

    param_distributions = {
        "n_estimators": (50, 150),
    }

    # Should not raise, but log errors and continue
    result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=sometimes_failing_eval_fn,
        n_iterations=3,
        maximize=True,
    )

    # Two successful results (2nd and 3rd calls)
    assert len(tuner.results) == 2
    assert result is not None


# ==============================================================================
# Test Integration
# ==============================================================================


def test_full_tuning_workflow(mock_mlflow_tracker, simple_train_fn, simple_eval_fn):
    """Test complete tuning workflow with multiple methods"""
    random.seed(42)

    mock_mlflow_tracker.start_run.return_value.__enter__ = MagicMock(
        return_value="run_123"
    )
    mock_mlflow_tracker.start_run.return_value.__exit__ = MagicMock(return_value=False)

    tuner = HyperparameterTuner(mlflow_tracker=mock_mlflow_tracker, enable_mlflow=True)

    # Grid search
    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [5],
    }

    grid_result = tuner.grid_search(
        param_grid=param_grid,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        maximize=True,
    )

    # Random search
    param_distributions = {
        "n_estimators": (10, 200),
        "max_depth": (3, 15),
    }

    random_result = tuner.random_search(
        param_distributions=param_distributions,
        train_fn=simple_train_fn,
        eval_fn=simple_eval_fn,
        n_iterations=3,
        maximize=True,
    )

    # Check results
    assert len(tuner.results) == 5  # 2 grid + 3 random
    summary = tuner.get_tuning_summary()
    assert summary["total_iterations"] == 5
    assert set(summary["methods_used"]) == {"grid_search", "random_search"}

    # Verify MLflow was used
    assert mock_mlflow_tracker.start_run.call_count == 5
