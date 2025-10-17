"""
Machine Learning Validation and Model Comparison Tools

Pure Python implementations of cross-validation, model comparison, and hyperparameter tuning.
No external ML libraries required (no scikit-learn, no numpy).

Sprint 8 - Model Validation & Comparison Tools
"""

import json
import math
import random
from typing import List, Dict, Any, Union, Optional, Callable
from functools import wraps


def log_operation(operation_name: str):
    """Decorator for structured logging of operations"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                print(
                    json.dumps(
                        {
                            "operation": operation_name,
                            "status": "success",
                            "function": func.__name__,
                        }
                    )
                )
                return result
            except Exception as e:
                print(
                    json.dumps(
                        {
                            "operation": operation_name,
                            "status": "error",
                            "function": func.__name__,
                            "error": str(e),
                        }
                    )
                )
                raise

        return wrapper

    return decorator


# ============================================================================
# Cross-Validation Tools
# ============================================================================


@log_operation("ml_k_fold_split")
def k_fold_split(
    n_samples: int,
    n_folds: int = 5,
    shuffle: bool = True,
    random_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate K-fold cross-validation splits.

    Divides data into K equal folds. Each fold is used once as test set
    while the remaining K-1 folds form the training set.

    Args:
        n_samples: Number of samples in dataset
        n_folds: Number of folds (default 5)
        shuffle: Shuffle data before splitting (default True)
        random_seed: Random seed for reproducibility

    Returns:
        {
            "folds": List of {train_indices, test_indices} for each fold,
            "n_folds": Number of folds,
            "fold_sizes": Size of each fold
        }

    NBA Example:
        5-fold CV on 500 players: each fold has 100 test, 400 train
    """
    if n_samples <= 0:
        raise ValueError(f"n_samples must be positive: {n_samples}")

    if n_folds <= 1:
        raise ValueError(f"n_folds must be > 1: {n_folds}")

    if n_folds > n_samples:
        raise ValueError(f"n_folds ({n_folds}) cannot exceed n_samples ({n_samples})")

    # Set random seed if provided
    if random_seed is not None:
        random.seed(random_seed)

    # Create indices
    indices = list(range(n_samples))

    # Shuffle if requested
    if shuffle:
        random.shuffle(indices)

    # Calculate fold size
    fold_size = n_samples // n_folds
    remainder = n_samples % n_folds

    # Create folds
    folds = []
    start_idx = 0

    for fold_idx in range(n_folds):
        # Add 1 extra sample to first 'remainder' folds
        current_fold_size = fold_size + (1 if fold_idx < remainder else 0)
        end_idx = start_idx + current_fold_size

        # Test indices for this fold
        test_indices = indices[start_idx:end_idx]

        # Train indices (all other folds)
        train_indices = indices[:start_idx] + indices[end_idx:]

        folds.append(
            {
                "fold": fold_idx,
                "train_indices": train_indices,
                "test_indices": test_indices,
                "train_size": len(train_indices),
                "test_size": len(test_indices),
            }
        )

        start_idx = end_idx

    # Calculate fold sizes
    fold_sizes = [fold["test_size"] for fold in folds]

    return {
        "folds": folds,
        "n_folds": n_folds,
        "n_samples": n_samples,
        "fold_sizes": fold_sizes,
        "shuffled": shuffle,
    }


@log_operation("ml_stratified_k_fold_split")
def stratified_k_fold_split(
    y: List[Any],
    n_folds: int = 5,
    shuffle: bool = True,
    random_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate stratified K-fold cross-validation splits.

    Maintains class distribution in each fold - important for imbalanced datasets.

    Args:
        y: Target labels
        n_folds: Number of folds (default 5)
        shuffle: Shuffle data before splitting (default True)
        random_seed: Random seed for reproducibility

    Returns:
        {
            "folds": List of {train_indices, test_indices} for each fold,
            "n_folds": Number of folds,
            "class_distribution": Distribution of classes per fold
        }

    NBA Example:
        MVP prediction (1% positive class): each fold maintains 1% MVP candidates
    """
    if not y:
        raise ValueError("y cannot be empty")

    if n_folds <= 1:
        raise ValueError(f"n_folds must be > 1: {n_folds}")

    if n_folds > len(y):
        raise ValueError(f"n_folds ({n_folds}) cannot exceed n_samples ({len(y)})")

    # Set random seed if provided
    if random_seed is not None:
        random.seed(random_seed)

    # Group indices by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)

    # Shuffle each class if requested
    if shuffle:
        for indices in class_indices.values():
            random.shuffle(indices)

    # Verify each class has enough samples
    for label, indices in class_indices.items():
        if len(indices) < n_folds:
            raise ValueError(
                f"Class '{label}' has only {len(indices)} samples, need at least {n_folds}"
            )

    # Create folds by distributing each class
    folds = [[] for _ in range(n_folds)]

    for label, indices in class_indices.items():
        # Distribute this class across folds
        for fold_idx, idx in enumerate(indices):
            folds[fold_idx % n_folds].append(idx)

    # Create train/test splits
    result_folds = []
    class_distribution = []

    for fold_idx in range(n_folds):
        test_indices = folds[fold_idx]
        train_indices = []
        for other_fold_idx in range(n_folds):
            if other_fold_idx != fold_idx:
                train_indices.extend(folds[other_fold_idx])

        # Calculate class distribution in this fold
        test_labels = [y[idx] for idx in test_indices]
        test_class_counts = {
            label: test_labels.count(label) for label in set(test_labels)
        }

        result_folds.append(
            {
                "fold": fold_idx,
                "train_indices": train_indices,
                "test_indices": test_indices,
                "train_size": len(train_indices),
                "test_size": len(test_indices),
                "test_class_distribution": test_class_counts,
            }
        )

        class_distribution.append(test_class_counts)

    return {
        "folds": result_folds,
        "n_folds": n_folds,
        "n_samples": len(y),
        "class_distribution": class_distribution,
        "classes": list(class_indices.keys()),
        "shuffled": shuffle,
    }


@log_operation("ml_cross_validate")
def cross_validate(
    X: List[List[Union[int, float]]],
    y: List[Any],
    cv_strategy: str = "k-fold",
    n_folds: int = 5,
    shuffle: bool = True,
    random_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform cross-validation (simplified version for scoring only).

    This version returns fold splits for use with external train/predict functions.
    Full integration with ML models happens in the MCP tool layer.

    Args:
        X: Feature data
        y: Target labels
        cv_strategy: "k-fold" or "stratified"
        n_folds: Number of folds (default 5)
        shuffle: Shuffle before splitting (default True)
        random_seed: Random seed for reproducibility

    Returns:
        {
            "folds": Fold splits with train/test indices,
            "X_folds": X data split into folds,
            "y_folds": y data split into folds,
            "cv_strategy": Strategy used
        }

    NBA Example:
        5-fold CV for All-Star prediction
    """
    if not X or not y:
        raise ValueError("X and y cannot be empty")

    if len(X) != len(y):
        raise ValueError(f"X and y must have same length: {len(X)} vs {len(y)}")

    # Generate fold splits
    if cv_strategy == "k-fold":
        fold_result = k_fold_split(
            n_samples=len(X), n_folds=n_folds, shuffle=shuffle, random_seed=random_seed
        )
    elif cv_strategy == "stratified":
        fold_result = stratified_k_fold_split(
            y=y, n_folds=n_folds, shuffle=shuffle, random_seed=random_seed
        )
    else:
        raise ValueError(
            f"Unknown cv_strategy: {cv_strategy}. Use 'k-fold' or 'stratified'"
        )

    # Create X and y splits for each fold
    X_folds = []
    y_folds = []

    for fold in fold_result["folds"]:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]

        X_train = [X[i] for i in train_idx]
        X_test = [X[i] for i in test_idx]
        y_train = [y[i] for i in train_idx]
        y_test = [y[i] for i in test_idx]

        X_folds.append(
            {
                "fold": fold["fold"],
                "X_train": X_train,
                "X_test": X_test,
                "y_train": y_train,
                "y_test": y_test,
            }
        )

    return {
        "folds": fold_result["folds"],
        "X_folds": X_folds,
        "cv_strategy": cv_strategy,
        "n_folds": n_folds,
        "n_samples": len(X),
    }


# ============================================================================
# Model Comparison Tools
# ============================================================================


@log_operation("ml_compare_models")
def compare_models(
    models: List[Dict[str, Any]], y_true: List[Any], metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare multiple models side-by-side.

    Args:
        models: List of {
            "name": Model name,
            "predictions": Predicted labels,
            "probabilities": Predicted probabilities (optional),
            "training_time": Training time in seconds (optional)
        }
        y_true: True labels
        metrics: Metrics to compute (default: ["accuracy", "precision", "recall", "f1"])

    Returns:
        Comparison table with rankings

    NBA Example:
        Compare Logistic Regression vs Random Forest vs Naive Bayes for All-Star prediction
    """
    if not models:
        raise ValueError("models cannot be empty")

    if not y_true:
        raise ValueError("y_true cannot be empty")

    if metrics is None:
        metrics = ["accuracy"]

    # Import evaluation functions
    from . import ml_evaluation_helper

    # Calculate metrics for each model
    results = []

    for model in models:
        name = model.get("name", "Unnamed")
        predictions = model.get("predictions")
        probabilities = model.get("probabilities")
        training_time = model.get("training_time", 0.0)

        if predictions is None:
            raise ValueError(f"Model '{name}' missing 'predictions'")

        if len(predictions) != len(y_true):
            raise ValueError(f"Model '{name}': predictions length mismatch")

        model_metrics = {"name": name, "training_time": training_time}

        # Calculate requested metrics
        for metric in metrics:
            if metric == "accuracy":
                acc = ml_evaluation_helper.accuracy_score(y_true, predictions)
                model_metrics["accuracy"] = acc["accuracy"]

            elif metric == "precision" or metric == "recall" or metric == "f1":
                # Try binary first, fall back to macro
                try:
                    prf = ml_evaluation_helper.precision_recall_f1(
                        y_true, predictions, average="binary"
                    )
                except:
                    prf = ml_evaluation_helper.precision_recall_f1(
                        y_true, predictions, average="macro"
                    )

                if metric == "precision":
                    model_metrics["precision"] = prf["precision"]
                elif metric == "recall":
                    model_metrics["recall"] = prf["recall"]
                elif metric == "f1":
                    model_metrics["f1"] = prf["f1_score"]

            elif metric == "roc_auc" and probabilities:
                try:
                    auc = ml_evaluation_helper.roc_auc_score(y_true, probabilities)
                    model_metrics["roc_auc"] = auc["auc"]
                except:
                    model_metrics["roc_auc"] = None

        results.append(model_metrics)

    # Rank models by each metric
    rankings = {}
    for metric in metrics:
        if metric == "training_time":
            # Lower is better
            sorted_results = sorted(results, key=lambda x: x.get(metric, float("inf")))
        else:
            # Higher is better
            sorted_results = sorted(
                results, key=lambda x: x.get(metric, 0), reverse=True
            )

        rankings[metric] = [r["name"] for r in sorted_results]

    # Find overall best model (most #1 rankings)
    best_counts = {}
    for metric, ranking in rankings.items():
        if metric != "training_time" and ranking:
            best_model = ranking[0]
            best_counts[best_model] = best_counts.get(best_model, 0) + 1

    overall_best = (
        max(best_counts.items(), key=lambda x: x[1])[0]
        if best_counts
        else results[0]["name"]
    )

    return {
        "models": results,
        "rankings": rankings,
        "overall_best": overall_best,
        "num_models": len(models),
        "metrics_compared": metrics,
    }


@log_operation("ml_paired_ttest")
def paired_ttest(
    scores_a: List[float], scores_b: List[float], alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Statistical comparison of two models using paired t-test.

    Tests if model A is significantly different from model B based on
    cross-validation scores.

    H0: Mean difference = 0 (models perform equally)
    H1: Mean difference ≠ 0 (models perform differently)

    Args:
        scores_a: CV scores for model A
        scores_b: CV scores for model B
        alpha: Significance level (default 0.05)

    Returns:
        {
            "t_statistic": t-statistic,
            "p_value": p-value,
            "significant": True if p < alpha,
            "mean_diff": Mean difference,
            "confidence_interval": 95% CI for mean difference
        }

    NBA Example:
        Random Forest vs Logistic Regression: p=0.03 (significantly different at α=0.05)
    """
    if not scores_a or not scores_b:
        raise ValueError("scores_a and scores_b cannot be empty")

    if len(scores_a) != len(scores_b):
        raise ValueError(
            f"scores must have same length: {len(scores_a)} vs {len(scores_b)}"
        )

    n = len(scores_a)

    if n < 2:
        raise ValueError(f"Need at least 2 scores, got {n}")

    # Calculate differences
    differences = [a - b for a, b in zip(scores_a, scores_b)]

    # Mean difference
    mean_diff = sum(differences) / n

    # Standard deviation of differences
    variance = sum((d - mean_diff) ** 2 for d in differences) / (n - 1)
    std_diff = math.sqrt(variance)

    # Standard error
    se = std_diff / math.sqrt(n)

    # t-statistic
    t_stat = mean_diff / se if se > 0 else 0.0

    # Degrees of freedom
    df = n - 1

    # Approximate p-value using t-distribution
    # For simplicity, use normal approximation for df > 30
    # For df <= 30, use Student's t critical values
    if df > 30:
        # Normal approximation
        z = abs(t_stat)
        # P(Z > z) for two-tailed test
        # Using approximation: P(Z > z) ≈ 0.5 * erfc(z/sqrt(2))
        from math import erfc

        p_value = erfc(z / math.sqrt(2))
    else:
        # Use simplified t-distribution approximation
        # Critical values for common alpha levels
        # This is a rough approximation - for production use scipy.stats
        t_abs = abs(t_stat)
        if df == 1:
            t_critical_05 = 12.706
        elif df <= 5:
            t_critical_05 = 2.571
        elif df <= 10:
            t_critical_05 = 2.228
        elif df <= 20:
            t_critical_05 = 2.086
        else:
            t_critical_05 = 2.042

        p_value = (
            0.001
            if t_abs > t_critical_05 * 2
            else (
                0.01
                if t_abs > t_critical_05 * 1.5
                else (
                    0.05
                    if t_abs > t_critical_05
                    else 0.10 if t_abs > t_critical_05 * 0.7 else 0.20
                )
            )
        )

    # Confidence interval (95%)
    t_critical = 1.96 if df > 30 else 2.042  # Approximate
    margin = t_critical * se
    ci_lower = mean_diff - margin
    ci_upper = mean_diff + margin

    # Determine significance
    significant = p_value < alpha

    return {
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": significant,
        "alpha": alpha,
        "mean_diff": mean_diff,
        "std_diff": std_diff,
        "degrees_of_freedom": df,
        "confidence_interval": {
            "lower": ci_lower,
            "upper": ci_upper,
            "confidence_level": 0.95,
        },
        "interpretation": _interpret_ttest(p_value, alpha, mean_diff),
    }


def _interpret_ttest(p_value: float, alpha: float, mean_diff: float) -> str:
    """Interpret t-test results"""
    if p_value >= alpha:
        return (
            f"Not significant (p={p_value:.3f} >= α={alpha}): No evidence of difference"
        )
    else:
        direction = (
            "Model A performs better" if mean_diff > 0 else "Model B performs better"
        )
        return f"Significant (p={p_value:.3f} < α={alpha}): {direction}"


# ============================================================================
# Hyperparameter Tuning
# ============================================================================


@log_operation("ml_grid_search")
def grid_search(
    param_grid: Dict[str, List[Any]], n_combinations: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate parameter combinations for grid search.

    This version generates the parameter grid. Actual training happens
    in the MCP tool layer with user-provided train/predict functions.

    Args:
        param_grid: Dict of parameter names to lists of values
        n_combinations: Limit number of combinations (optional, for large grids)

    Returns:
        {
            "param_combinations": List of parameter dicts,
            "total_combinations": Total number of combinations,
            "param_grid": Original parameter grid
        }

    NBA Example:
        Grid search for Logistic Regression:
        param_grid = {
            "learning_rate": [0.001, 0.01, 0.1],
            "max_iterations": [100, 500, 1000]
        }
        → 9 combinations to test
    """
    if not param_grid:
        raise ValueError("param_grid cannot be empty")

    # Generate all combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]

    # Calculate total combinations
    total_combinations = 1
    for values in param_values:
        total_combinations *= len(values)

    # Generate combinations recursively
    def generate_combinations(names, values, current=None):
        if current is None:
            current = {}

        if not names:
            return [current.copy()]

        combinations = []
        name = names[0]
        remaining_names = names[1:]

        for value in values[0]:
            current[name] = value
            combinations.extend(
                generate_combinations(remaining_names, values[1:], current)
            )

        return combinations

    param_combinations = generate_combinations(param_names, param_values)

    # Limit combinations if requested
    if n_combinations and n_combinations < len(param_combinations):
        random.shuffle(param_combinations)
        param_combinations = param_combinations[:n_combinations]

    return {
        "param_combinations": param_combinations,
        "total_combinations": total_combinations,
        "combinations_tested": len(param_combinations),
        "param_grid": param_grid,
        "param_names": param_names,
    }
