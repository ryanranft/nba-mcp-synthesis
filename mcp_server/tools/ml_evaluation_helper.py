"""
Machine Learning Evaluation Metrics

Pure Python implementations of classification and regression metrics.
No external ML libraries required (no scikit-learn, no numpy).

Sprint 8 - Model Evaluation & Validation Tools
"""

import json
import math
from typing import List, Dict, Any, Union, Optional, Tuple
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
# Classification Metrics
# ============================================================================


@log_operation("ml_accuracy_score")
def accuracy_score(y_true: List[Any], y_pred: List[Any]) -> Dict[str, Any]:
    """
    Calculate prediction accuracy.

    Accuracy = correct_predictions / total_predictions

    Args:
        y_true: True labels
        y_pred: Predicted labels

    Returns:
        {
            "accuracy": Accuracy score (0.0 to 1.0),
            "correct": Number of correct predictions,
            "total": Total number of predictions,
            "percentage": Accuracy as percentage
        }

    NBA Example:
        All-Star prediction: 87% accuracy (174/200 correct)
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(
            f"y_true and y_pred must have same length: {len(y_true)} vs {len(y_pred)}"
        )

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    total = len(y_true)
    accuracy = correct / total

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "percentage": accuracy * 100,
        "interpretation": _interpret_accuracy(accuracy),
    }


def _interpret_accuracy(acc: float) -> str:
    """Interpret accuracy score"""
    if acc >= 0.95:
        return "Excellent (≥95%)"
    elif acc >= 0.85:
        return "Very Good (85-95%)"
    elif acc >= 0.75:
        return "Good (75-85%)"
    elif acc >= 0.65:
        return "Fair (65-75%)"
    else:
        return "Poor (<65%)"


@log_operation("ml_precision_recall_f1")
def precision_recall_f1(
    y_true: List[Any], y_pred: List[Any], average: str = "binary", pos_label: Any = 1
) -> Dict[str, Any]:
    """
    Calculate precision, recall, and F1-score.

    Precision = TP / (TP + FP)  - How many selected items are relevant?
    Recall = TP / (TP + FN)     - How many relevant items are selected?
    F1 = 2 * (precision * recall) / (precision + recall)  - Harmonic mean

    Args:
        y_true: True labels
        y_pred: Predicted labels
        average: "binary" (default), "macro", "micro", "weighted"
        pos_label: Positive class label (for binary classification)

    Returns:
        {
            "precision": Precision score,
            "recall": Recall score,
            "f1_score": F1-score,
            "support": Number of true instances per class,
            "per_class": Per-class metrics (for multiclass)
        }

    NBA Examples:
        MVP prediction: precision=0.92 (few false positives), recall=0.75 (missed some MVPs)
        Position classification: macro-averaged F1=0.89 across 5 positions
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Get unique classes
    classes = sorted(list(set(y_true)))

    if average == "binary":
        # Binary classification
        if len(classes) != 2:
            raise ValueError(f"Binary average requires 2 classes, got {len(classes)}")

        # Calculate TP, FP, FN for positive class
        tp = sum(
            1 for yt, yp in zip(y_true, y_pred) if yt == pos_label and yp == pos_label
        )
        fp = sum(
            1 for yt, yp in zip(y_true, y_pred) if yt != pos_label and yp == pos_label
        )
        fn = sum(
            1 for yt, yp in zip(y_true, y_pred) if yt == pos_label and yp != pos_label
        )

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        support = sum(1 for yt in y_true if yt == pos_label)

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": support,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "interpretation": {
                "precision": _interpret_precision(precision),
                "recall": _interpret_recall(recall),
                "f1": _interpret_f1(f1),
            },
        }

    else:
        # Multiclass classification
        per_class = {}

        for cls in classes:
            # One-vs-rest for each class
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
            s = sum(1 for yt in y_true if yt == cls)

            per_class[str(cls)] = {
                "precision": p,
                "recall": r,
                "f1_score": f,
                "support": s,
            }

        # Calculate averages
        if average == "macro":
            # Unweighted mean
            precision = sum(pc["precision"] for pc in per_class.values()) / len(classes)
            recall = sum(pc["recall"] for pc in per_class.values()) / len(classes)
            f1 = sum(pc["f1_score"] for pc in per_class.values()) / len(classes)

        elif average == "weighted":
            # Weighted by support
            total_support = sum(pc["support"] for pc in per_class.values())
            precision = (
                sum(pc["precision"] * pc["support"] for pc in per_class.values())
                / total_support
            )
            recall = (
                sum(pc["recall"] * pc["support"] for pc in per_class.values())
                / total_support
            )
            f1 = (
                sum(pc["f1_score"] * pc["support"] for pc in per_class.values())
                / total_support
            )

        elif average == "micro":
            # Global TP, FP, FN
            total_tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
            total_fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != yp)
            total_fn = total_fp  # In multiclass, FP == FN

            precision = (
                total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
            )
            recall = (
                total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
            )
            f1 = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

        else:
            raise ValueError(
                f"Unknown average: {average}. Use 'binary', 'macro', 'weighted', or 'micro'"
            )

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "average": average,
            "per_class": per_class,
            "num_classes": len(classes),
            "interpretation": {
                "precision": _interpret_precision(precision),
                "recall": _interpret_recall(recall),
                "f1": _interpret_f1(f1),
            },
        }


def _interpret_precision(p: float) -> str:
    """Interpret precision score"""
    if p >= 0.9:
        return "Excellent - Very few false positives"
    elif p >= 0.8:
        return "Very Good - Few false positives"
    elif p >= 0.7:
        return "Good - Some false positives"
    else:
        return "Fair/Poor - Many false positives"


def _interpret_recall(r: float) -> str:
    """Interpret recall score"""
    if r >= 0.9:
        return "Excellent - Catches almost all positive cases"
    elif r >= 0.8:
        return "Very Good - Catches most positive cases"
    elif r >= 0.7:
        return "Good - Misses some positive cases"
    else:
        return "Fair/Poor - Misses many positive cases"


def _interpret_f1(f: float) -> str:
    """Interpret F1 score"""
    if f >= 0.9:
        return "Excellent - Well-balanced precision and recall"
    elif f >= 0.8:
        return "Very Good - Good balance"
    elif f >= 0.7:
        return "Good - Reasonable balance"
    else:
        return "Fair/Poor - Imbalanced or low scores"


@log_operation("ml_confusion_matrix")
def confusion_matrix(
    y_true: List[Any],
    y_pred: List[Any],
    labels: Optional[List[Any]] = None,
    normalize: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate confusion matrix.

    Structure (binary):
                    Predicted
                  Neg    Pos
    Actual  Neg   TN     FP
            Pos   FN     TP

    Args:
        y_true: True labels
        y_pred: Predicted labels
        labels: Class labels (optional, auto-detected if None)
        normalize: None, "true", "pred", "all"

    Returns:
        {
            "matrix": Confusion matrix (2D list),
            "labels": Class labels,
            "true_positives": TP (for binary),
            "false_positives": FP (for binary),
            "true_negatives": TN (for binary),
            "false_negatives": FN (for binary)
        }

    NBA Example:
        All-Star Prediction:
                        Predicted
                      No    Yes
        Actual   No   450   50   (90% specificity)
                Yes   30    170  (85% sensitivity)
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Get labels
    if labels is None:
        labels = sorted(list(set(y_true)))

    n_classes = len(labels)

    # Create label to index mapping
    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    # Initialize matrix
    matrix = [[0 for _ in range(n_classes)] for _ in range(n_classes)]

    # Fill matrix
    for yt, yp in zip(y_true, y_pred):
        if yt in label_to_idx and yp in label_to_idx:
            i = label_to_idx[yt]
            j = label_to_idx[yp]
            matrix[i][j] += 1

    # Normalize if requested
    if normalize == "true":
        # Normalize by true labels (rows)
        matrix = [
            [
                matrix[i][j] / sum(matrix[i]) if sum(matrix[i]) > 0 else 0.0
                for j in range(n_classes)
            ]
            for i in range(n_classes)
        ]
    elif normalize == "pred":
        # Normalize by predicted labels (columns)
        col_sums = [
            sum(matrix[i][j] for i in range(n_classes)) for j in range(n_classes)
        ]
        matrix = [
            [
                matrix[i][j] / col_sums[j] if col_sums[j] > 0 else 0.0
                for j in range(n_classes)
            ]
            for i in range(n_classes)
        ]
    elif normalize == "all":
        # Normalize by total
        total = sum(sum(row) for row in matrix)
        matrix = [
            [matrix[i][j] / total if total > 0 else 0.0 for j in range(n_classes)]
            for i in range(n_classes)
        ]

    result = {
        "matrix": matrix,
        "labels": labels,
        "num_classes": n_classes,
        "normalize": normalize,
    }

    # Add binary metrics if binary classification
    if n_classes == 2:
        # Assuming labels[0] is negative, labels[1] is positive
        tn = matrix[0][0] if not normalize else int(matrix[0][0] * len(y_true))
        fp = matrix[0][1] if not normalize else int(matrix[0][1] * len(y_true))
        fn = matrix[1][0] if not normalize else int(matrix[1][0] * len(y_true))
        tp = matrix[1][1] if not normalize else int(matrix[1][1] * len(y_true))

        result.update(
            {
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
                "sensitivity": (
                    tp / (tp + fn) if (tp + fn) > 0 else 0.0
                ),  # Same as recall
                "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0.0,
                "positive_predictive_value": (
                    tp / (tp + fp) if (tp + fp) > 0 else 0.0
                ),  # Same as precision
                "negative_predictive_value": tn / (tn + fn) if (tn + fn) > 0 else 0.0,
            }
        )

    return result


@log_operation("ml_roc_auc_score")
def roc_auc_score(
    y_true: List[int], y_scores: List[float], num_thresholds: int = 100
) -> Dict[str, Any]:
    """
    Calculate ROC-AUC (area under ROC curve).

    ROC curve plots True Positive Rate vs False Positive Rate at various thresholds.
    AUC measures classifier's ability to distinguish classes.

    Args:
        y_true: True binary labels (0/1)
        y_scores: Predicted probabilities/scores
        num_thresholds: Number of thresholds to evaluate

    Returns:
        {
            "auc": Area under curve (0.5 to 1.0),
            "roc_curve": {fpr, tpr, thresholds},
            "optimal_threshold": Threshold maximizing TPR-FPR
        }

    NBA Example:
        Playoff prediction: AUC=0.89 (good discrimination between playoff/non-playoff teams)
    """
    if not y_true or not y_scores:
        raise ValueError("y_true and y_scores cannot be empty")

    if len(y_true) != len(y_scores):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_scores)}")

    # Check binary labels
    unique_labels = set(y_true)
    if unique_labels != {0, 1}:
        raise ValueError(f"y_true must be binary (0/1), got {unique_labels}")

    # Generate thresholds
    min_score = min(y_scores)
    max_score = max(y_scores)
    thresholds = [
        min_score + (max_score - min_score) * i / num_thresholds
        for i in range(num_thresholds + 1)
    ]

    # Calculate TPR and FPR for each threshold
    fpr_list = []
    tpr_list = []

    for threshold in thresholds:
        # Predict based on threshold
        y_pred = [1 if score >= threshold else 0 for score in y_scores]

        # Calculate TP, FP, TN, FN
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

        # TPR = TP / (TP + FN), FPR = FP / (FP + TN)
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        tpr_list.append(tpr)
        fpr_list.append(fpr)

    # Calculate AUC using trapezoidal rule
    auc = 0.0
    for i in range(len(fpr_list) - 1):
        # Area of trapezoid
        auc += (fpr_list[i + 1] - fpr_list[i]) * (tpr_list[i] + tpr_list[i + 1]) / 2

    # Find optimal threshold (maximizing TPR - FPR)
    differences = [tpr - fpr for tpr, fpr in zip(tpr_list, fpr_list)]
    optimal_idx = differences.index(max(differences))
    optimal_threshold = thresholds[optimal_idx]

    return {
        "auc": abs(auc),  # Absolute value in case of negative (decreasing FPR)
        "roc_curve": {"fpr": fpr_list, "tpr": tpr_list, "thresholds": thresholds},
        "optimal_threshold": optimal_threshold,
        "optimal_tpr": tpr_list[optimal_idx],
        "optimal_fpr": fpr_list[optimal_idx],
        "interpretation": _interpret_auc(abs(auc)),
    }


def _interpret_auc(auc: float) -> str:
    """Interpret AUC score"""
    if auc >= 0.9:
        return "Excellent - Outstanding discrimination"
    elif auc >= 0.8:
        return "Very Good - Good discrimination"
    elif auc >= 0.7:
        return "Good - Acceptable discrimination"
    elif auc >= 0.6:
        return "Fair - Poor discrimination"
    else:
        return "Poor - No better than random"


@log_operation("ml_classification_report")
def classification_report(y_true: List[Any], y_pred: List[Any]) -> Dict[str, Any]:
    """
    Generate comprehensive classification report.

    Aggregates precision, recall, F1 for all classes plus averages.

    Args:
        y_true: True labels
        y_pred: Predicted labels

    Returns:
        Comprehensive report with per-class and aggregate metrics

    NBA Example:
        Position Classification Report:
                 precision  recall  f1-score  support
        PG          0.91     0.88     0.89      100
        SG          0.84     0.87     0.85      105
        SF          0.89     0.85     0.87       98
        PF          0.87     0.90     0.88      102
        C           0.93     0.94     0.94       95

        macro avg   0.89     0.89     0.89      500
        weighted    0.89     0.89     0.89      500
        accuracy    0.89     0.89     0.89      500
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Get per-class metrics
    classes = sorted(list(set(y_true)))
    per_class = {}

    for cls in classes:
        # One-vs-rest
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        support = sum(1 for yt in y_true if yt == cls)

        per_class[str(cls)] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": support,
        }

    # Calculate macro average (unweighted)
    macro_precision = sum(pc["precision"] for pc in per_class.values()) / len(classes)
    macro_recall = sum(pc["recall"] for pc in per_class.values()) / len(classes)
    macro_f1 = sum(pc["f1_score"] for pc in per_class.values()) / len(classes)

    # Calculate weighted average
    total_support = sum(pc["support"] for pc in per_class.values())
    weighted_precision = (
        sum(pc["precision"] * pc["support"] for pc in per_class.values())
        / total_support
    )
    weighted_recall = (
        sum(pc["recall"] * pc["support"] for pc in per_class.values()) / total_support
    )
    weighted_f1 = (
        sum(pc["f1_score"] * pc["support"] for pc in per_class.values()) / total_support
    )

    # Overall accuracy
    accuracy = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / len(y_true)

    return {
        "per_class": per_class,
        "macro_avg": {
            "precision": macro_precision,
            "recall": macro_recall,
            "f1_score": macro_f1,
            "support": total_support,
        },
        "weighted_avg": {
            "precision": weighted_precision,
            "recall": weighted_recall,
            "f1_score": weighted_f1,
            "support": total_support,
        },
        "accuracy": accuracy,
        "num_classes": len(classes),
        "total_samples": len(y_true),
    }


@log_operation("ml_log_loss")
def log_loss(
    y_true: List[int], y_pred_proba: List[float], eps: float = 1e-15
) -> Dict[str, Any]:
    """
    Calculate log loss (cross-entropy loss).

    Log Loss = -mean(y_true * log(y_pred) + (1-y_true) * log(1-y_pred))

    Lower is better. 0 = perfect, higher = worse.

    Args:
        y_true: True binary labels (0/1)
        y_pred_proba: Predicted probabilities
        eps: Small value to avoid log(0)

    Returns:
        {
            "log_loss": Overall log loss,
            "per_sample_loss": Loss for each sample
        }

    NBA Example:
        All-Star prediction log loss: 0.23 (confident, well-calibrated predictions)
    """
    if not y_true or not y_pred_proba:
        raise ValueError("y_true and y_pred_proba cannot be empty")

    if len(y_true) != len(y_pred_proba):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred_proba)}")

    # Clip probabilities to avoid log(0)
    y_pred_clipped = [max(min(p, 1 - eps), eps) for p in y_pred_proba]

    # Calculate per-sample loss
    per_sample_loss = []
    for yt, yp in zip(y_true, y_pred_clipped):
        if yt == 1:
            loss = -math.log(yp)
        else:
            loss = -math.log(1 - yp)
        per_sample_loss.append(loss)

    # Overall log loss
    overall_loss = sum(per_sample_loss) / len(per_sample_loss)

    return {
        "log_loss": overall_loss,
        "per_sample_loss": per_sample_loss,
        "interpretation": _interpret_log_loss(overall_loss),
    }


def _interpret_log_loss(loss: float) -> str:
    """Interpret log loss"""
    if loss < 0.1:
        return "Excellent - Very confident and accurate"
    elif loss < 0.3:
        return "Very Good - Confident predictions"
    elif loss < 0.5:
        return "Good - Reasonable confidence"
    elif loss < 0.7:
        return "Fair - Low confidence"
    else:
        return "Poor - Very uncertain or inaccurate"


# ============================================================================
# Regression Metrics
# ============================================================================


@log_operation("ml_mse_rmse_mae")
def mse_rmse_mae(
    y_true: List[Union[int, float]], y_pred: List[Union[int, float]]
) -> Dict[str, Any]:
    """
    Calculate regression error metrics.

    MSE = mean((y_true - y_pred)²)       - Mean Squared Error
    RMSE = sqrt(MSE)                     - Root Mean Squared Error
    MAE = mean(|y_true - y_pred|)        - Mean Absolute Error

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        {
            "mse": Mean Squared Error,
            "rmse": Root Mean Squared Error,
            "mae": Mean Absolute Error,
            "sample_errors": Per-sample errors
        }

    NBA Example:
        PPG prediction: RMSE=2.4 points per game, MAE=1.8 PPG
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Calculate errors
    errors = [yt - yp for yt, yp in zip(y_true, y_pred)]
    squared_errors = [e**2 for e in errors]
    absolute_errors = [abs(e) for e in errors]

    # MSE
    mse = sum(squared_errors) / len(squared_errors)

    # RMSE
    rmse = math.sqrt(mse)

    # MAE
    mae = sum(absolute_errors) / len(absolute_errors)

    return {
        "mse": mse,
        "rmse": rmse,
        "mae": mae,
        "sample_errors": errors,
        "sample_squared_errors": squared_errors,
        "sample_absolute_errors": absolute_errors,
        "num_samples": len(y_true),
    }


@log_operation("ml_r2_score")
def r2_score(
    y_true: List[Union[int, float]], y_pred: List[Union[int, float]]
) -> Dict[str, Any]:
    """
    Calculate coefficient of determination (R²).

    R² = 1 - (SS_res / SS_tot)

    Where:
    - SS_res = sum((y_true - y_pred)²)  - Residual sum of squares
    - SS_tot = sum((y_true - mean)²)    - Total sum of squares

    Range: -∞ to 1.0
    - 1.0 = perfect prediction
    - 0.0 = predicting mean
    - <0.0 = worse than predicting mean

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        {
            "r2_score": R² coefficient,
            "explained_variance": Variance explained by model
        }

    NBA Example:
        Win% prediction: R²=0.78 (explains 78% of variance in team wins)
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Calculate mean
    mean_y = sum(y_true) / len(y_true)

    # SS_res: residual sum of squares
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))

    # SS_tot: total sum of squares
    ss_tot = sum((yt - mean_y) ** 2 for yt in y_true)

    # R²
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Explained variance
    explained_var = r2 if r2 >= 0 else 0.0

    return {
        "r2_score": r2,
        "explained_variance": explained_var,
        "ss_res": ss_res,
        "ss_tot": ss_tot,
        "interpretation": _interpret_r2(r2),
    }


def _interpret_r2(r2: float) -> str:
    """Interpret R² score"""
    if r2 >= 0.9:
        return "Excellent - Explains ≥90% of variance"
    elif r2 >= 0.7:
        return "Very Good - Explains 70-90% of variance"
    elif r2 >= 0.5:
        return "Good - Explains 50-70% of variance"
    elif r2 >= 0.3:
        return "Fair - Explains 30-50% of variance"
    elif r2 >= 0:
        return "Poor - Explains <30% of variance"
    else:
        return "Very Poor - Worse than predicting mean"


@log_operation("ml_mape")
def mean_absolute_percentage_error(
    y_true: List[Union[int, float]],
    y_pred: List[Union[int, float]],
    epsilon: float = 1e-10,
) -> Dict[str, Any]:
    """
    Calculate Mean Absolute Percentage Error (MAPE).

    MAPE = mean(|y_true - y_pred| / |y_true|) * 100

    Expresses error as a percentage of true values.

    Args:
        y_true: True values
        y_pred: Predicted values
        epsilon: Small value to avoid division by zero

    Returns:
        {
            "mape": MAPE percentage,
            "per_sample_ape": Absolute percentage error per sample
        }

    NBA Example:
        Salary prediction: MAPE=8.5% (predictions off by 8.5% on average)
    """
    if not y_true or not y_pred:
        raise ValueError("y_true and y_pred cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} vs {len(y_pred)}")

    # Calculate absolute percentage errors
    per_sample_ape = []
    for yt, yp in zip(y_true, y_pred):
        # Avoid division by zero
        denominator = abs(yt) if abs(yt) > epsilon else epsilon
        ape = abs(yt - yp) / denominator * 100
        per_sample_ape.append(ape)

    # MAPE
    mape = sum(per_sample_ape) / len(per_sample_ape)

    return {
        "mape": mape,
        "per_sample_ape": per_sample_ape,
        "interpretation": _interpret_mape(mape),
    }


def _interpret_mape(mape: float) -> str:
    """Interpret MAPE"""
    if mape < 5:
        return "Excellent - <5% error"
    elif mape < 10:
        return "Very Good - 5-10% error"
    elif mape < 20:
        return "Good - 10-20% error"
    elif mape < 30:
        return "Fair - 20-30% error"
    else:
        return "Poor - >30% error"
