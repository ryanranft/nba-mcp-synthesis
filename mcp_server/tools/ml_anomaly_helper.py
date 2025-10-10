"""
Machine Learning Anomaly Detection Tools

Pure Python implementations of anomaly/outlier detection algorithms.
No external ML libraries required (no scikit-learn, no numpy).

Sprint 7 - Phase 3: Anomaly Detection Tools
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
# Z-Score Outlier Detection
# ============================================================================

@log_operation("ml_zscore_outliers")
def detect_outliers_zscore(
    data: List[List[Union[int, float]]],
    threshold: float = 3.0,
    labels: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Detect outliers using Z-score method.

    Z-score = (x - μ) / σ
    Points with |z-score| > threshold are considered outliers.

    Args:
        data: Data points (each row is a sample)
        threshold: Z-score threshold (default 3.0 = 3 standard deviations)
        labels: Optional labels for data points

    Returns:
        {
            "outliers": Indices of outlier points,
            "z_scores": Z-scores for each point,
            "outlier_count": Number of outliers,
            "outlier_percentage": Percentage of outliers,
            "threshold": Threshold used
        }

    Example NBA Use Case:
        Detect outlier performances:
        - Data: [[PPG, RPG, APG]] for all players
        - Outliers: Players with exceptional stats (e.g., Wilt's 50 PPG)
        - Z-score > 3: More than 3 std deviations above mean
    """
    if not data:
        raise ValueError("Data cannot be empty")

    if threshold <= 0:
        raise ValueError(f"Threshold must be positive: {threshold}")

    n_samples = len(data)
    n_features = len(data[0])

    # Calculate mean and std for each feature
    means = []
    stds = []

    for feature_idx in range(n_features):
        feature_values = [sample[feature_idx] for sample in data]

        mean = sum(feature_values) / n_samples
        variance = sum((x - mean) ** 2 for x in feature_values) / n_samples
        std = math.sqrt(variance)

        means.append(mean)
        stds.append(std if std > 0 else 1e-10)  # Prevent division by zero

    # Calculate z-scores for each point
    z_scores = []
    outliers = []

    for i, sample in enumerate(data):
        # Calculate z-score for each feature
        sample_z_scores = []

        for feature_idx in range(n_features):
            z = (sample[feature_idx] - means[feature_idx]) / stds[feature_idx]
            sample_z_scores.append(z)

        # Max absolute z-score across all features
        max_z = max(abs(z) for z in sample_z_scores)
        z_scores.append({
            "index": i,
            "z_scores": sample_z_scores,
            "max_z_score": max_z,
            "is_outlier": max_z > threshold
        })

        if max_z > threshold:
            outlier_info = {
                "index": i,
                "z_scores": sample_z_scores,
                "max_z_score": max_z,
                "data": sample
            }

            if labels is not None:
                outlier_info["label"] = labels[i]

            outliers.append(outlier_info)

    return {
        "outliers": outliers,
        "z_scores": z_scores,
        "outlier_count": len(outliers),
        "outlier_percentage": (len(outliers) / n_samples) * 100,
        "threshold": threshold,
        "total_samples": n_samples,
        "feature_means": means,
        "feature_stds": stds
    }


# ============================================================================
# Isolation Forest
# ============================================================================

@log_operation("ml_isolation_forest")
def isolation_forest(
    data: List[List[Union[int, float]]],
    n_trees: int = 100,
    sample_size: Optional[int] = None,
    contamination: float = 0.1,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Detect anomalies using Isolation Forest algorithm.

    Isolation Forest isolates anomalies by randomly partitioning data.
    Anomalies are easier to isolate (shorter path in tree).

    Args:
        data: Data points
        n_trees: Number of isolation trees
        sample_size: Samples per tree (default: min(256, len(data)))
        contamination: Expected proportion of outliers (0.0 to 0.5)
        random_seed: Random seed for reproducibility

    Returns:
        {
            "anomalies": Indices of anomalous points,
            "anomaly_scores": Anomaly score for each point (higher = more anomalous),
            "threshold": Anomaly score threshold used,
            "anomaly_count": Number of anomalies detected
        }

    Example NBA Use Case:
        Detect unusual player stat combinations:
        - Most players cluster in similar stat patterns
        - Anomalies: Unique players (e.g., Jokic's triple-double averages)
        - Isolation Forest finds players hard to categorize
    """
    if not data:
        raise ValueError("Data cannot be empty")

    if n_trees <= 0:
        raise ValueError(f"n_trees must be positive: {n_trees}")

    if not (0 < contamination < 0.5):
        raise ValueError(f"contamination must be between 0 and 0.5: {contamination}")

    # Set defaults
    if sample_size is None:
        sample_size = min(256, len(data))

    # Set random seed
    if random_seed is not None:
        import random
        random.seed(random_seed)

    import random

    # Build isolation trees
    trees = []
    for _ in range(n_trees):
        # Random sample
        sample_indices = random.sample(range(len(data)), min(sample_size, len(data)))
        sample_data = [data[i] for i in sample_indices]

        # Build isolation tree
        tree = _build_isolation_tree(sample_data, height_limit=math.ceil(math.log2(sample_size)))
        trees.append(tree)

    # Calculate anomaly scores
    anomaly_scores = []

    for i, point in enumerate(data):
        # Average path length across all trees
        path_lengths = []

        for tree in trees:
            path_length = _isolation_tree_path_length(tree, point, current_height=0)
            path_lengths.append(path_length)

        avg_path_length = sum(path_lengths) / len(path_lengths)

        # Normalize by expected path length
        c = _average_path_length(sample_size)
        anomaly_score = 2 ** (-avg_path_length / c)

        anomaly_scores.append({
            "index": i,
            "score": anomaly_score,
            "avg_path_length": avg_path_length
        })

    # Sort by score (descending)
    sorted_scores = sorted(anomaly_scores, key=lambda x: x["score"], reverse=True)

    # Determine threshold based on contamination
    threshold_index = int(len(data) * contamination)
    threshold = sorted_scores[threshold_index]["score"] if threshold_index < len(sorted_scores) else 0.5

    # Identify anomalies
    anomalies = [
        {
            "index": item["index"],
            "score": item["score"],
            "data": data[item["index"]]
        }
        for item in anomaly_scores
        if item["score"] >= threshold
    ]

    return {
        "anomalies": anomalies,
        "anomaly_scores": [item["score"] for item in anomaly_scores],
        "threshold": threshold,
        "anomaly_count": len(anomalies),
        "anomaly_percentage": (len(anomalies) / len(data)) * 100,
        "n_trees": n_trees,
        "sample_size": sample_size,
        "contamination": contamination
    }


def _build_isolation_tree(
    data: List[List[Union[int, float]]],
    height_limit: int,
    current_height: int = 0
) -> Dict[str, Any]:
    """
    Recursively build isolation tree.

    Args:
        data: Data points for this node
        height_limit: Maximum tree height
        current_height: Current height

    Returns:
        Tree node
    """
    import random

    # Terminal node conditions
    if current_height >= height_limit or len(data) <= 1:
        return {
            "type": "leaf",
            "size": len(data)
        }

    # Randomly select feature to split on
    n_features = len(data[0])
    split_feature = random.randint(0, n_features - 1)

    # Get feature values
    feature_values = [sample[split_feature] for sample in data]
    min_val = min(feature_values)
    max_val = max(feature_values)

    if min_val == max_val:
        # Can't split - all values same
        return {
            "type": "leaf",
            "size": len(data)
        }

    # Random split value
    split_value = random.uniform(min_val, max_val)

    # Split data
    left_data = [sample for sample in data if sample[split_feature] < split_value]
    right_data = [sample for sample in data if sample[split_feature] >= split_value]

    if not left_data or not right_data:
        # Split failed
        return {
            "type": "leaf",
            "size": len(data)
        }

    # Recursively build subtrees
    return {
        "type": "split",
        "split_feature": split_feature,
        "split_value": split_value,
        "left": _build_isolation_tree(left_data, height_limit, current_height + 1),
        "right": _build_isolation_tree(right_data, height_limit, current_height + 1)
    }


def _isolation_tree_path_length(
    node: Dict[str, Any],
    point: List[Union[int, float]],
    current_height: int
) -> float:
    """
    Calculate path length for point in isolation tree.

    Args:
        node: Current tree node
        point: Point to evaluate
        current_height: Current depth

    Returns:
        Path length
    """
    if node["type"] == "leaf":
        # Adjust for unsplit nodes
        size = node["size"]
        if size <= 1:
            return current_height
        else:
            # Add expected path length for remaining points
            return current_height + _average_path_length(size)

    # Internal node - traverse
    if point[node["split_feature"]] < node["split_value"]:
        return _isolation_tree_path_length(node["left"], point, current_height + 1)
    else:
        return _isolation_tree_path_length(node["right"], point, current_height + 1)


def _average_path_length(n: int) -> float:
    """
    Calculate average path length for unsuccessful search in BST.

    Args:
        n: Number of data points

    Returns:
        Average path length
    """
    if n <= 1:
        return 0

    # c(n) = 2H(n-1) - 2(n-1)/n
    # where H(i) is harmonic number ≈ ln(i) + 0.5772 (Euler-Mascheroni constant)
    harmonic = math.log(n - 1) + 0.5772156649

    return 2 * harmonic - (2 * (n - 1) / n)


# ============================================================================
# Local Outlier Factor (LOF)
# ============================================================================

@log_operation("ml_local_outlier_factor")
def local_outlier_factor(
    data: List[List[Union[int, float]]],
    k: int = 20,
    contamination: float = 0.1
) -> Dict[str, Any]:
    """
    Detect anomalies using Local Outlier Factor (LOF).

    LOF measures local density deviation of a point w.r.t. its neighbors.
    Points with substantially lower density than neighbors are outliers.

    Args:
        data: Data points
        k: Number of neighbors to consider
        contamination: Expected proportion of outliers

    Returns:
        {
            "anomalies": Indices of anomalous points,
            "lof_scores": LOF score for each point (>1 = outlier),
            "threshold": LOF threshold used,
            "anomaly_count": Number of anomalies
        }

    Example NBA Use Case:
        Detect context-dependent outliers:
        - Player stats look normal compared to league
        - But unusual compared to similar players
        - Example: Good 3PT shooter on team of poor shooters
        - LOF catches local anomalies global methods miss
    """
    if not data:
        raise ValueError("Data cannot be empty")

    if k <= 0:
        raise ValueError(f"k must be positive: {k}")

    if k >= len(data):
        raise ValueError(f"k ({k}) must be less than number of points ({len(data)})")

    if not (0 < contamination < 0.5):
        raise ValueError(f"contamination must be between 0 and 0.5: {contamination}")

    # Calculate distances between all points
    distances = []

    for i in range(len(data)):
        point_distances = []
        for j in range(len(data)):
            if i == j:
                point_distances.append((j, 0.0))
            else:
                dist = _euclidean_distance(data[i], data[j])
                point_distances.append((j, dist))

        # Sort by distance
        point_distances.sort(key=lambda x: x[1])
        distances.append(point_distances)

    # Calculate k-distance for all points first
    k_distances = []
    for i in range(len(data)):
        # k-distance: distance to k-th nearest neighbor
        k_dist = distances[i][k][1]
        k_distances.append(k_dist)

    # Calculate Local Reachability Density (LRD) for all points
    lrd_scores = []
    for i in range(len(data)):
        # Get k-nearest neighbors
        k_neighbors = [idx for idx, _ in distances[i][1:k+1]]

        # Calculate reachability distances
        reachability_dists = []
        for neighbor_idx in k_neighbors:
            # Find actual distance to this neighbor
            actual_dist = None
            for idx, dist in distances[i]:
                if idx == neighbor_idx:
                    actual_dist = dist
                    break

            # Reachability distance = max(k-distance(neighbor), actual distance)
            reachability_dist = max(k_distances[neighbor_idx], actual_dist)
            reachability_dists.append(reachability_dist)

        # Local Reachability Density (LRD)
        avg_reachability = sum(reachability_dists) / len(reachability_dists)
        lrd = 1 / avg_reachability if avg_reachability > 0 else float('inf')
        lrd_scores.append(lrd)

    # Calculate LOF scores
    lof_scores = []

    for i in range(len(data)):
        k_neighbors = [idx for idx, _ in distances[i][1:k+1]]

        # Average LRD of neighbors
        neighbor_lrd_sum = sum(lrd_scores[neighbor_idx] for neighbor_idx in k_neighbors)
        avg_neighbor_lrd = neighbor_lrd_sum / len(k_neighbors)

        # LOF = (avg neighbor LRD) / (point LRD)
        if lrd_scores[i] == 0:
            lof = float('inf')
        elif lrd_scores[i] == float('inf'):
            lof = 0
        else:
            lof = avg_neighbor_lrd / lrd_scores[i]

        lof_scores.append({
            "index": i,
            "lof_score": lof
        })

    # Sort by LOF score (descending)
    sorted_lof = sorted(lof_scores, key=lambda x: x["lof_score"], reverse=True)

    # Determine threshold: top contamination% are anomalies
    # We want to include the top N items, so threshold should be at index N-1
    n_anomalies = max(1, int(len(data) * contamination))  # At least 1
    threshold_index = min(n_anomalies - 1, len(sorted_lof) - 1)
    threshold = sorted_lof[threshold_index]["lof_score"]

    # Identify anomalies (LOF >= threshold, includes the threshold point)
    anomalies = [
        {
            "index": item["index"],
            "lof_score": item["lof_score"],
            "data": data[item["index"]]
        }
        for item in lof_scores
        if item["lof_score"] >= threshold
    ]

    return {
        "anomalies": anomalies,
        "lof_scores": [item["lof_score"] for item in lof_scores],
        "threshold": threshold,
        "anomaly_count": len(anomalies),
        "anomaly_percentage": (len(anomalies) / len(data)) * 100,
        "k": k,
        "contamination": contamination,
        "interpretation": {
            "lof_near_1": "Normal point (similar density to neighbors)",
            "lof_greater_1": "Outlier (lower density than neighbors)",
            "lof_much_greater_1": "Strong outlier"
        }
    }


def _euclidean_distance(point1: List[Union[int, float]], point2: List[Union[int, float]]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(point1, point2)))
