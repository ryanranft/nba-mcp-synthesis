"""
Machine Learning Classification and Prediction Tools

Pure Python implementations of classification algorithms.
No external ML libraries required (no scikit-learn, no numpy).

Sprint 7 - Phase 2: Classification & Prediction Tools
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
                print(json.dumps({
                    "operation": operation_name,
                    "status": "success",
                    "function": func.__name__
                }))
                return result
            except Exception as e:
                print(json.dumps({
                    "operation": operation_name,
                    "status": "error",
                    "function": func.__name__,
                    "error": str(e)
                }))
                raise
        return wrapper
    return decorator


# ============================================================================
# Logistic Regression
# ============================================================================

@log_operation("ml_logistic_regression")
def logistic_regression(
    X_train: List[List[Union[int, float]]],
    y_train: List[int],
    learning_rate: float = 0.01,
    max_iterations: int = 1000,
    tolerance: float = 1e-4
) -> Dict[str, Any]:
    """
    Train a logistic regression classifier using gradient descent.

    Logistic Regression uses sigmoid function: σ(z) = 1 / (1 + e^(-z))
    Where z = w₀ + w₁x₁ + w₂x₂ + ... (linear combination)

    Args:
        X_train: Training features (each row is a sample)
        y_train: Training labels (0 or 1 for binary classification)
        learning_rate: Step size for gradient descent
        max_iterations: Maximum training iterations
        tolerance: Convergence threshold

    Returns:
        {
            "weights": Learned weights [w₀, w₁, w₂, ...],
            "iterations": Number of iterations run,
            "converged": Whether algorithm converged,
            "final_loss": Final cross-entropy loss
        }

    Example NBA Use Case:
        Predict whether a player will make All-Star based on stats:
        - Features: [PPG, APG, RPG, TS%, PER]
        - Labels: [1 = All-Star, 0 = Not All-Star]
        - Model learns weights for each stat's importance
    """
    if not X_train or not y_train:
        raise ValueError("Training data cannot be empty")

    if len(X_train) != len(y_train):
        raise ValueError(f"X_train and y_train must have same length: {len(X_train)} vs {len(y_train)}")

    # Validate binary labels
    unique_labels = set(y_train)
    if unique_labels != {0, 1}:
        raise ValueError(f"y_train must contain only 0 and 1. Found: {unique_labels}")

    n_samples = len(X_train)
    n_features = len(X_train[0])

    # Initialize weights to zero (including bias term)
    weights = [0.0] * (n_features + 1)

    converged = False

    for iteration in range(max_iterations):
        # Calculate predictions and gradients
        gradients = [0.0] * (n_features + 1)
        total_loss = 0.0

        for i in range(n_samples):
            # Calculate linear combination (z = w₀ + w₁x₁ + ...)
            z = weights[0]  # Bias term
            for j in range(n_features):
                z += weights[j + 1] * X_train[i][j]

            # Apply sigmoid function
            prediction = _sigmoid(z)

            # Calculate error
            error = prediction - y_train[i]

            # Update gradients
            gradients[0] += error  # Bias gradient
            for j in range(n_features):
                gradients[j + 1] += error * X_train[i][j]

            # Calculate cross-entropy loss
            # Loss = -[y*log(p) + (1-y)*log(1-p)]
            epsilon = 1e-15  # Prevent log(0)
            p = max(min(prediction, 1 - epsilon), epsilon)
            total_loss += -(y_train[i] * math.log(p) + (1 - y_train[i]) * math.log(1 - p))

        # Average loss
        avg_loss = total_loss / n_samples

        # Update weights
        max_weight_change = 0.0
        for j in range(len(weights)):
            weight_change = learning_rate * gradients[j] / n_samples
            weights[j] -= weight_change
            max_weight_change = max(max_weight_change, abs(weight_change))

        # Check convergence
        if max_weight_change < tolerance:
            converged = True
            break

    return {
        "weights": weights,
        "iterations": iteration + 1,
        "converged": converged,
        "final_loss": avg_loss,
        "num_features": n_features,
        "training_samples": n_samples
    }


@log_operation("ml_logistic_predict")
def logistic_predict(
    X: List[List[Union[int, float]]],
    weights: List[float],
    threshold: float = 0.5,
    return_probabilities: bool = False
) -> Dict[str, Any]:
    """
    Make predictions using trained logistic regression model.

    Args:
        X: Features to predict (each row is a sample)
        weights: Trained weights from logistic_regression
        threshold: Classification threshold (default 0.5)
        return_probabilities: If True, return probabilities instead of binary predictions

    Returns:
        {
            "predictions": List of predicted classes (0 or 1),
            "probabilities": List of probabilities (if return_probabilities=True),
            "threshold": Threshold used
        }

    Example:
        # Predict All-Star probability for new player
        X = [[28.5, 6.8, 5.2, 0.615, 24.3]]  # PPG, APG, RPG, TS%, PER
        result = logistic_predict(X, trained_weights)
        # prediction: 1 (All-Star likely)
        # probability: 0.87 (87% confidence)
    """
    if not X:
        raise ValueError("X cannot be empty")

    if not weights:
        raise ValueError("Weights cannot be empty")

    n_features = len(X[0])
    if len(weights) != n_features + 1:
        raise ValueError(f"Weights length ({len(weights)}) must be n_features + 1 ({n_features + 1})")

    predictions = []
    probabilities = []

    for sample in X:
        # Calculate linear combination
        z = weights[0]  # Bias
        for j in range(n_features):
            z += weights[j + 1] * sample[j]

        # Apply sigmoid
        prob = _sigmoid(z)
        probabilities.append(prob)

        # Classify based on threshold
        prediction = 1 if prob >= threshold else 0
        predictions.append(prediction)

    result = {
        "predictions": predictions,
        "threshold": threshold,
        "num_samples": len(X)
    }

    if return_probabilities:
        result["probabilities"] = probabilities

    return result


def _sigmoid(z: float) -> float:
    """
    Sigmoid activation function: σ(z) = 1 / (1 + e^(-z))

    Args:
        z: Input value

    Returns:
        Output in range (0, 1)
    """
    # Prevent overflow
    if z > 500:
        return 1.0
    elif z < -500:
        return 0.0

    return 1.0 / (1.0 + math.exp(-z))


# ============================================================================
# Naive Bayes Classifier
# ============================================================================

@log_operation("ml_naive_bayes")
def naive_bayes_train(
    X_train: List[List[Union[int, float]]],
    y_train: List[Any]
) -> Dict[str, Any]:
    """
    Train a Gaussian Naive Bayes classifier.

    Naive Bayes assumes features are independent given the class.
    For each feature, calculates mean and std dev per class.

    Args:
        X_train: Training features
        y_train: Training labels (any hashable type)

    Returns:
        {
            "classes": List of unique classes,
            "class_priors": Prior probability of each class,
            "feature_stats": {
                class: {
                    "means": List of feature means,
                    "stds": List of feature standard deviations
                }
            }
        }

    Example NBA Use Case:
        Classify player position based on stats:
        - Features: [height_cm, weight_kg, PPG, RPG, APG]
        - Classes: ["PG", "SG", "SF", "PF", "C"]
        - Model learns typical stats for each position
    """
    if not X_train or not y_train:
        raise ValueError("Training data cannot be empty")

    if len(X_train) != len(y_train):
        raise ValueError(f"X_train and y_train must have same length")

    n_features = len(X_train[0])

    # Get unique classes
    classes = sorted(set(y_train))

    # Calculate prior probabilities
    class_counts = {cls: y_train.count(cls) for cls in classes}
    class_priors = {cls: count / len(y_train) for cls, count in class_counts.items()}

    # Calculate feature statistics for each class
    feature_stats = {}

    for cls in classes:
        # Get all samples for this class
        class_samples = [X_train[i] for i in range(len(y_train)) if y_train[i] == cls]

        # Calculate mean and std for each feature
        means = []
        stds = []

        for feature_idx in range(n_features):
            feature_values = [sample[feature_idx] for sample in class_samples]

            mean = sum(feature_values) / len(feature_values)
            means.append(mean)

            # Calculate standard deviation
            variance = sum((x - mean) ** 2 for x in feature_values) / len(feature_values)
            std = math.sqrt(variance)
            # Add small constant to prevent division by zero
            stds.append(std if std > 0 else 1e-6)

        feature_stats[cls] = {
            "means": means,
            "stds": stds,
            "count": len(class_samples)
        }

    return {
        "classes": classes,
        "class_priors": class_priors,
        "feature_stats": feature_stats,
        "num_features": n_features,
        "training_samples": len(y_train)
    }


@log_operation("ml_naive_bayes_predict")
def naive_bayes_predict(
    X: List[List[Union[int, float]]],
    model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make predictions using trained Naive Bayes model.

    Args:
        X: Features to predict
        model: Trained model from naive_bayes_train

    Returns:
        {
            "predictions": List of predicted classes,
            "probabilities": List of probability distributions,
            "confidence": List of confidence scores (max probability)
        }

    Example:
        # Classify player position
        X = [[198, 88, 18.5, 6.2, 1.8]]  # height, weight, PPG, RPG, APG
        result = naive_bayes_predict(X, model)
        # prediction: "SF" (small forward)
        # confidence: 0.78
    """
    if not X:
        raise ValueError("X cannot be empty")

    classes = model["classes"]
    class_priors = model["class_priors"]
    feature_stats = model["feature_stats"]

    predictions = []
    all_probabilities = []
    confidences = []

    for sample in X:
        # Calculate posterior probability for each class
        posteriors = {}

        for cls in classes:
            # Start with prior probability (log scale to prevent underflow)
            log_prob = math.log(class_priors[cls])

            # Multiply by likelihood of each feature (add logs)
            means = feature_stats[cls]["means"]
            stds = feature_stats[cls]["stds"]

            for feature_idx in range(len(sample)):
                # Gaussian probability density
                prob = _gaussian_pdf(
                    sample[feature_idx],
                    means[feature_idx],
                    stds[feature_idx]
                )
                # Add log probability
                log_prob += math.log(prob + 1e-10)  # Prevent log(0)

            posteriors[cls] = log_prob

        # Convert log probabilities back to probabilities
        # Normalize by subtracting max (log-sum-exp trick)
        max_log_prob = max(posteriors.values())
        probs = {
            cls: math.exp(log_prob - max_log_prob)
            for cls, log_prob in posteriors.items()
        }

        # Normalize to sum to 1
        total = sum(probs.values())
        probs = {cls: p / total for cls, p in probs.items()}

        # Prediction is class with highest probability
        prediction = max(probs, key=probs.get)
        confidence = probs[prediction]

        predictions.append(prediction)
        all_probabilities.append(probs)
        confidences.append(confidence)

    return {
        "predictions": predictions,
        "probabilities": all_probabilities,
        "confidence": confidences,
        "num_samples": len(X)
    }


def _gaussian_pdf(x: float, mean: float, std: float) -> float:
    """
    Gaussian (normal) probability density function.

    PDF = (1 / (σ√2π)) × e^(-(x-μ)²/(2σ²))

    Args:
        x: Value
        mean: Mean (μ)
        std: Standard deviation (σ)

    Returns:
        Probability density
    """
    variance = std ** 2
    coefficient = 1.0 / math.sqrt(2 * math.pi * variance)
    exponent = math.exp(-((x - mean) ** 2) / (2 * variance))
    return coefficient * exponent


# ============================================================================
# Decision Tree (Simplified CART)
# ============================================================================

@log_operation("ml_decision_tree")
def decision_tree_train(
    X_train: List[List[Union[int, float]]],
    y_train: List[Any],
    max_depth: int = 5,
    min_samples_split: int = 2
) -> Dict[str, Any]:
    """
    Train a decision tree classifier using CART algorithm.

    CART (Classification and Regression Trees) builds binary tree
    by recursively splitting on features that maximize information gain.

    Args:
        X_train: Training features
        y_train: Training labels
        max_depth: Maximum tree depth
        min_samples_split: Minimum samples required to split

    Returns:
        {
            "tree": Tree structure (nested dict),
            "max_depth": Maximum depth used,
            "num_leaves": Number of leaf nodes,
            "feature_importance": Importance score per feature
        }

    Example NBA Use Case:
        Predict playoff success based on regular season stats:
        - Features: [Win%, ORtg, DRtg, Net Rating, Four Factors]
        - Labels: ["Champion", "Finals", "Playoffs", "Missed"]
        - Tree learns decision rules (e.g., "If ORtg > 115...")
    """
    if not X_train or not y_train:
        raise ValueError("Training data cannot be empty")

    if len(X_train) != len(y_train):
        raise ValueError("X_train and y_train must have same length")

    n_features = len(X_train[0])

    # Build tree recursively
    tree = _build_tree(X_train, y_train, depth=0, max_depth=max_depth, min_samples_split=min_samples_split)

    # Count leaves
    num_leaves = _count_leaves(tree)

    # Calculate feature importance (simplified - counts splits per feature)
    feature_importance = [0] * n_features
    _calculate_feature_importance(tree, feature_importance)

    # Normalize importance
    total_importance = sum(feature_importance)
    if total_importance > 0:
        feature_importance = [imp / total_importance for imp in feature_importance]

    return {
        "tree": tree,
        "max_depth": max_depth,
        "num_leaves": num_leaves,
        "feature_importance": feature_importance,
        "num_features": n_features,
        "training_samples": len(y_train)
    }


@log_operation("ml_decision_tree_predict")
def decision_tree_predict(
    X: List[List[Union[int, float]]],
    tree: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make predictions using trained decision tree.

    Args:
        X: Features to predict
        tree: Trained tree from decision_tree_train

    Returns:
        {
            "predictions": List of predicted classes,
            "paths": List of decision paths (for interpretability)
        }

    Example:
        X = [[0.62, 115.2, 108.5, 6.7]]  # Win%, ORtg, DRtg, NetRtg
        result = decision_tree_predict(X, tree)
        # prediction: "Playoffs"
        # path: ["ORtg > 112", "DRtg < 110", "Win% > 0.55"]
    """
    if not X:
        raise ValueError("X cannot be empty")

    predictions = []
    paths = []

    for sample in X:
        prediction, path = _traverse_tree(tree, sample, [])
        predictions.append(prediction)
        paths.append(path)

    return {
        "predictions": predictions,
        "paths": paths,
        "num_samples": len(X)
    }


def _build_tree(
    X: List[List[Union[int, float]]],
    y: List[Any],
    depth: int,
    max_depth: int,
    min_samples_split: int
) -> Dict[str, Any]:
    """
    Recursively build decision tree.

    Args:
        X: Training features for this node
        y: Training labels for this node
        depth: Current depth
        max_depth: Maximum allowed depth
        min_samples_split: Minimum samples to split

    Returns:
        Tree node (dict)
    """
    # Base cases - create leaf node
    if (
        depth >= max_depth
        or len(y) < min_samples_split
        or len(set(y)) == 1  # All same class
    ):
        # Leaf node: return most common class
        class_counts = {}
        for label in y:
            class_counts[label] = class_counts.get(label, 0) + 1

        majority_class = max(class_counts, key=class_counts.get)

        return {
            "type": "leaf",
            "class": majority_class,
            "samples": len(y),
            "distribution": class_counts
        }

    # Find best split
    best_feature, best_threshold, best_gini = _find_best_split(X, y)

    if best_feature is None:
        # Couldn't find good split - make leaf
        class_counts = {}
        for label in y:
            class_counts[label] = class_counts.get(label, 0) + 1
        majority_class = max(class_counts, key=class_counts.get)

        return {
            "type": "leaf",
            "class": majority_class,
            "samples": len(y),
            "distribution": class_counts
        }

    # Split data
    left_X, left_y, right_X, right_y = _split_data(X, y, best_feature, best_threshold)

    # Recursively build subtrees
    left_subtree = _build_tree(left_X, left_y, depth + 1, max_depth, min_samples_split)
    right_subtree = _build_tree(right_X, right_y, depth + 1, max_depth, min_samples_split)

    return {
        "type": "split",
        "feature": best_feature,
        "threshold": best_threshold,
        "gini": best_gini,
        "samples": len(y),
        "left": left_subtree,
        "right": right_subtree
    }


def _find_best_split(
    X: List[List[Union[int, float]]],
    y: List[Any]
) -> Tuple[Optional[int], Optional[float], Optional[float]]:
    """
    Find best feature and threshold to split on.

    Uses Gini impurity: Gini = 1 - Σ(p_i²)

    Returns:
        (best_feature_index, best_threshold, best_gini_gain)
    """
    best_gini_gain = 0
    best_feature = None
    best_threshold = None

    parent_gini = _gini_impurity(y)
    n_features = len(X[0])

    for feature_idx in range(n_features):
        # Get unique values for this feature
        values = sorted(set(sample[feature_idx] for sample in X))

        # Try splits between consecutive values
        for i in range(len(values) - 1):
            threshold = (values[i] + values[i + 1]) / 2

            # Split data
            left_X, left_y, right_X, right_y = _split_data(X, y, feature_idx, threshold)

            if not left_y or not right_y:
                continue

            # Calculate weighted Gini after split
            n = len(y)
            left_gini = _gini_impurity(left_y)
            right_gini = _gini_impurity(right_y)

            weighted_gini = (len(left_y) / n) * left_gini + (len(right_y) / n) * right_gini

            # Gini gain
            gini_gain = parent_gini - weighted_gini

            if gini_gain > best_gini_gain:
                best_gini_gain = gini_gain
                best_feature = feature_idx
                best_threshold = threshold

    return best_feature, best_threshold, best_gini_gain


def _gini_impurity(y: List[Any]) -> float:
    """
    Calculate Gini impurity: Gini = 1 - Σ(p_i²)

    Args:
        y: Labels

    Returns:
        Gini impurity (0 = pure, 0.5 = max impurity for binary)
    """
    if not y:
        return 0

    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1

    gini = 1.0
    n = len(y)

    for count in class_counts.values():
        probability = count / n
        gini -= probability ** 2

    return gini


def _split_data(
    X: List[List[Union[int, float]]],
    y: List[Any],
    feature_idx: int,
    threshold: float
) -> Tuple[List, List, List, List]:
    """
    Split data based on feature threshold.

    Returns:
        (left_X, left_y, right_X, right_y)
    """
    left_X, left_y = [], []
    right_X, right_y = [], []

    for i in range(len(X)):
        if X[i][feature_idx] <= threshold:
            left_X.append(X[i])
            left_y.append(y[i])
        else:
            right_X.append(X[i])
            right_y.append(y[i])

    return left_X, left_y, right_X, right_y


def _traverse_tree(
    node: Dict[str, Any],
    sample: List[Union[int, float]],
    path: List[str]
) -> Tuple[Any, List[str]]:
    """
    Traverse tree to make prediction for single sample.

    Returns:
        (prediction, decision_path)
    """
    if node["type"] == "leaf":
        return node["class"], path

    # Split node - go left or right
    feature_idx = node["feature"]
    threshold = node["threshold"]

    if sample[feature_idx] <= threshold:
        path.append(f"feature_{feature_idx} <= {threshold:.2f}")
        return _traverse_tree(node["left"], sample, path)
    else:
        path.append(f"feature_{feature_idx} > {threshold:.2f}")
        return _traverse_tree(node["right"], sample, path)


def _count_leaves(node: Dict[str, Any]) -> int:
    """Count number of leaf nodes in tree."""
    if node["type"] == "leaf":
        return 1
    return _count_leaves(node["left"]) + _count_leaves(node["right"])


def _calculate_feature_importance(node: Dict[str, Any], importance: List[int]):
    """Calculate feature importance by counting splits."""
    if node["type"] == "leaf":
        return

    importance[node["feature"]] += 1
    _calculate_feature_importance(node["left"], importance)
    _calculate_feature_importance(node["right"], importance)


# ============================================================================
# Random Forest (Ensemble of Decision Trees)
# ============================================================================

@log_operation("ml_random_forest")
def random_forest_train(
    X_train: List[List[Union[int, float]]],
    y_train: List[Any],
    n_trees: int = 10,
    max_depth: int = 5,
    min_samples_split: int = 2,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Train a random forest classifier (ensemble of decision trees).

    Random Forest trains multiple decision trees on bootstrap samples
    and averages their predictions (voting for classification).

    Args:
        X_train: Training features
        y_train: Training labels
        n_trees: Number of trees in forest
        max_depth: Maximum depth per tree
        min_samples_split: Minimum samples to split
        random_seed: Random seed for reproducibility

    Returns:
        {
            "trees": List of trained trees,
            "n_trees": Number of trees,
            "feature_importance": Averaged feature importance
        }

    Example NBA Use Case:
        Ensemble prediction for MVP candidates:
        - Train 50 trees on different bootstrap samples
        - Each tree votes for MVP
        - Final prediction is majority vote
        - More robust than single decision tree
    """
    if not X_train or not y_train:
        raise ValueError("Training data cannot be empty")

    if len(X_train) != len(y_train):
        raise ValueError("X_train and y_train must have same length")

    if n_trees <= 0:
        raise ValueError(f"n_trees must be positive: {n_trees}")

    # Set random seed
    if random_seed is not None:
        import random
        random.seed(random_seed)

    import random
    n_samples = len(X_train)
    n_features = len(X_train[0])

    trees = []
    all_feature_importance = []

    for _ in range(n_trees):
        # Bootstrap sample (sample with replacement)
        bootstrap_indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
        X_bootstrap = [X_train[i] for i in bootstrap_indices]
        y_bootstrap = [y_train[i] for i in bootstrap_indices]

        # Train tree on bootstrap sample
        tree_model = decision_tree_train(
            X_bootstrap,
            y_bootstrap,
            max_depth=max_depth,
            min_samples_split=min_samples_split
        )

        trees.append(tree_model["tree"])
        all_feature_importance.append(tree_model["feature_importance"])

    # Average feature importance across trees
    avg_importance = [0.0] * n_features
    for importance in all_feature_importance:
        for i in range(n_features):
            avg_importance[i] += importance[i]

    avg_importance = [imp / n_trees for imp in avg_importance]

    return {
        "trees": trees,
        "n_trees": n_trees,
        "feature_importance": avg_importance,
        "max_depth": max_depth,
        "num_features": n_features,
        "training_samples": len(y_train)
    }


@log_operation("ml_random_forest_predict")
def random_forest_predict(
    X: List[List[Union[int, float]]],
    model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make predictions using trained random forest.

    Args:
        X: Features to predict
        model: Trained model from random_forest_train

    Returns:
        {
            "predictions": List of predicted classes (majority vote),
            "vote_counts": List of vote distributions,
            "confidence": List of confidence scores
        }

    Example:
        X = [[28.5, 8.2, 7.1, 0.625, 27.5]]  # MVP candidate stats
        result = random_forest_predict(X, model)
        # prediction: "MVP"
        # votes: {"MVP": 42, "All-Star": 8}
        # confidence: 0.84 (42/50 trees voted MVP)
    """
    if not X:
        raise ValueError("X cannot be empty")

    trees = model["trees"]
    n_trees = model["n_trees"]

    predictions = []
    all_vote_counts = []
    confidences = []

    for sample in X:
        # Get prediction from each tree
        votes = []
        for tree in trees:
            prediction, _ = _traverse_tree(tree, sample, [])
            votes.append(prediction)

        # Count votes
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        # Majority vote
        final_prediction = max(vote_counts, key=vote_counts.get)
        confidence = vote_counts[final_prediction] / n_trees

        predictions.append(final_prediction)
        all_vote_counts.append(vote_counts)
        confidences.append(confidence)

    return {
        "predictions": predictions,
        "vote_counts": all_vote_counts,
        "confidence": confidences,
        "num_samples": len(X),
        "n_trees": n_trees
    }
