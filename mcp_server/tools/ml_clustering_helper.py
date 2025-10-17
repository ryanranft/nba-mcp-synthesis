"""
Machine Learning Clustering and Similarity Tools

Pure Python implementations of clustering algorithms and similarity measures.
No external ML libraries required (no scikit-learn, no numpy).

Sprint 7 - Phase 1: Clustering & Similarity Tools
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
# Distance and Similarity Measures
# ============================================================================


@log_operation("ml_euclidean_distance")
def calculate_euclidean_distance(
    point1: List[Union[int, float]], point2: List[Union[int, float]]
) -> float:
    """
    Calculate Euclidean distance between two points.

    Formula: d = √(Σ(x₁ - x₂)²)

    Args:
        point1: First point coordinates
        point2: Second point coordinates

    Returns:
        Euclidean distance (0 = identical, larger = more different)

    Example:
        >>> calculate_euclidean_distance([1, 2, 3], [4, 5, 6])
        5.196152422706632

    NBA Use Case:
        Distance between player stat profiles:
        - Point 1: [25 PPG, 7 APG, 5 RPG]
        - Point 2: [22 PPG, 8 APG, 4 RPG]
        - Distance shows how similar players are
    """
    if len(point1) != len(point2):
        raise ValueError(
            f"Points must have same dimensions: {len(point1)} vs {len(point2)}"
        )

    if len(point1) == 0:
        raise ValueError("Points cannot be empty")

    # Calculate squared differences
    squared_diff = sum((x - y) ** 2 for x, y in zip(point1, point2))

    # Return square root
    return math.sqrt(squared_diff)


@log_operation("ml_cosine_similarity")
def calculate_cosine_similarity(
    vector1: List[Union[int, float]], vector2: List[Union[int, float]]
) -> float:
    """
    Calculate cosine similarity between two vectors.

    Formula: cos(θ) = (A · B) / (||A|| × ||B||)

    Args:
        vector1: First vector
        vector2: Second vector

    Returns:
        Cosine similarity (-1 to 1)
        - 1.0 = identical direction
        - 0.0 = orthogonal (no similarity)
        - -1.0 = opposite direction

    Example:
        >>> calculate_cosine_similarity([1, 2, 3], [2, 4, 6])
        1.0  # Perfect similarity (same direction)

    NBA Use Case:
        Compare player performance profiles:
        - Similar players have cosine similarity near 1.0
        - Different playstyles have similarity near 0.0
        - Better than Euclidean for normalized comparisons
    """
    if len(vector1) != len(vector2):
        raise ValueError(
            f"Vectors must have same dimensions: {len(vector1)} vs {len(vector2)}"
        )

    if len(vector1) == 0:
        raise ValueError("Vectors cannot be empty")

    # Calculate dot product
    dot_product = sum(x * y for x, y in zip(vector1, vector2))

    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(x**2 for x in vector1))
    magnitude2 = math.sqrt(sum(x**2 for x in vector2))

    # Handle zero vectors
    if magnitude1 == 0 or magnitude2 == 0:
        raise ValueError("Cannot calculate cosine similarity with zero vector")

    # Return cosine similarity
    return dot_product / (magnitude1 * magnitude2)


# ============================================================================
# K-Means Clustering
# ============================================================================


@log_operation("ml_kmeans_clustering")
def kmeans_clustering(
    data: List[List[Union[int, float]]],
    k: int = 3,
    max_iterations: int = 100,
    tolerance: float = 1e-4,
    random_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform K-means clustering using Lloyd's algorithm.

    Args:
        data: List of data points (each point is a list of features)
        k: Number of clusters
        max_iterations: Maximum iterations before stopping
        tolerance: Convergence threshold (centroid movement)
        random_seed: Random seed for reproducibility

    Returns:
        {
            "clusters": List of cluster assignments (0 to k-1),
            "centroids": List of cluster centroids,
            "iterations": Number of iterations run,
            "inertia": Sum of squared distances to centroids,
            "converged": Whether algorithm converged
        }

    Example NBA Use Case:
        Group players into 3 clusters based on stats:
        - Cluster 0: High scorers (guards)
        - Cluster 1: Rebounders (forwards)
        - Cluster 2: All-around (versatile)

        Input: [[25, 3, 5], [22, 4, 4], [15, 2, 12], [14, 3, 11], [8, 1, 8]]
        (PPG, APG, RPG for 5 players)
    """
    if not data:
        raise ValueError("Data cannot be empty")

    if k <= 0:
        raise ValueError(f"k must be positive: {k}")

    if k > len(data):
        raise ValueError(f"k ({k}) cannot exceed number of data points ({len(data)})")

    # Validate all points have same dimensions
    dimensions = len(data[0])
    for i, point in enumerate(data):
        if len(point) != dimensions:
            raise ValueError(
                f"All points must have same dimensions. Point {i} has {len(point)}, expected {dimensions}"
            )

    # Set random seed if provided
    if random_seed is not None:
        import random

        random.seed(random_seed)

    # Initialize centroids (k-means++ would be better, but using simple random for now)
    import random

    centroids = [list(point) for point in random.sample(data, k)]

    clusters = [0] * len(data)
    converged = False

    for iteration in range(max_iterations):
        # Assignment step: assign each point to nearest centroid
        for i, point in enumerate(data):
            min_distance = float("inf")
            closest_centroid = 0

            for j, centroid in enumerate(centroids):
                distance = calculate_euclidean_distance(point, centroid)
                if distance < min_distance:
                    min_distance = distance
                    closest_centroid = j

            clusters[i] = closest_centroid

        # Update step: recalculate centroids
        new_centroids = []
        max_centroid_movement = 0.0

        for j in range(k):
            # Get all points assigned to this cluster
            cluster_points = [data[i] for i in range(len(data)) if clusters[i] == j]

            if not cluster_points:
                # Empty cluster - keep old centroid
                new_centroids.append(centroids[j])
                continue

            # Calculate mean of all points in cluster
            new_centroid = [
                sum(point[dim] for point in cluster_points) / len(cluster_points)
                for dim in range(dimensions)
            ]
            new_centroids.append(new_centroid)

            # Track centroid movement
            movement = calculate_euclidean_distance(centroids[j], new_centroid)
            max_centroid_movement = max(max_centroid_movement, movement)

        # Check for convergence
        if max_centroid_movement < tolerance:
            converged = True
            break

        centroids = new_centroids

    # Calculate inertia (sum of squared distances to centroids)
    inertia = 0.0
    for i, point in enumerate(data):
        centroid = centroids[clusters[i]]
        distance = calculate_euclidean_distance(point, centroid)
        inertia += distance**2

    return {
        "clusters": clusters,
        "centroids": centroids,
        "iterations": iteration + 1,
        "inertia": inertia,
        "converged": converged,
        "summary": {
            "num_clusters": k,
            "cluster_sizes": [clusters.count(i) for i in range(k)],
            "avg_distance_to_centroid": inertia / len(data),
        },
    }


# ============================================================================
# K-Nearest Neighbors
# ============================================================================


@log_operation("ml_knn_classify")
def find_nearest_neighbors(
    point: List[Union[int, float]],
    data: List[List[Union[int, float]]],
    labels: List[Any],
    k: int = 5,
    distance_metric: str = "euclidean",
) -> Dict[str, Any]:
    """
    Find K-nearest neighbors and classify a point.

    Args:
        point: Point to classify
        data: Training data points
        labels: Labels for training data
        k: Number of neighbors to consider
        distance_metric: "euclidean" or "cosine"

    Returns:
        {
            "prediction": Most common label among k neighbors,
            "neighbors": List of (index, distance, label) tuples,
            "confidence": Ratio of votes for predicted class,
            "vote_counts": Count of votes per class
        }

    Example NBA Use Case:
        Classify a player's position based on stats:
        - Point: [15 PPG, 8 APG, 3 RPG]
        - Training data: Stats from known players
        - Labels: ["PG", "SG", "SF", "PF", "C"]
        - Prediction: "PG" (point guard)
    """
    if not data:
        raise ValueError("Training data cannot be empty")

    if len(data) != len(labels):
        raise ValueError(
            f"Data and labels must have same length: {len(data)} vs {len(labels)}"
        )

    if k <= 0:
        raise ValueError(f"k must be positive: {k}")

    if k > len(data):
        raise ValueError(
            f"k ({k}) cannot exceed number of training points ({len(data)})"
        )

    # Calculate distances to all training points
    distances = []

    for i, train_point in enumerate(data):
        if distance_metric == "euclidean":
            distance = calculate_euclidean_distance(point, train_point)
        elif distance_metric == "cosine":
            # Convert cosine similarity to distance (1 - similarity)
            similarity = calculate_cosine_similarity(point, train_point)
            distance = 1 - similarity
        else:
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        distances.append((i, distance, labels[i]))

    # Sort by distance and take k nearest
    distances.sort(key=lambda x: x[1])
    neighbors = distances[:k]

    # Count votes for each label
    vote_counts = {}
    for _, _, label in neighbors:
        vote_counts[label] = vote_counts.get(label, 0) + 1

    # Prediction is most common label
    prediction = max(vote_counts, key=vote_counts.get)
    confidence = vote_counts[prediction] / k

    return {
        "prediction": prediction,
        "neighbors": [
            {"index": idx, "distance": dist, "label": label}
            for idx, dist, label in neighbors
        ],
        "confidence": confidence,
        "vote_counts": vote_counts,
        "k": k,
        "distance_metric": distance_metric,
    }


# ============================================================================
# Hierarchical Clustering
# ============================================================================


@log_operation("ml_hierarchical_clustering")
def hierarchical_clustering(
    data: List[List[Union[int, float]]], n_clusters: int = 3, linkage: str = "average"
) -> Dict[str, Any]:
    """
    Perform agglomerative hierarchical clustering.

    Args:
        data: List of data points
        n_clusters: Number of clusters to form
        linkage: Linkage criterion ("single", "complete", "average")
            - single: minimum distance between clusters
            - complete: maximum distance between clusters
            - average: average distance between clusters

    Returns:
        {
            "clusters": List of cluster assignments,
            "dendrogram": List of merge steps [(cluster1, cluster2, distance)],
            "final_clusters": Number of final clusters,
            "linkage_used": Linkage method used
        }

    Example NBA Use Case:
        Build hierarchy of player similarities:
        - Start with each player as own cluster
        - Merge most similar players/clusters
        - Continue until desired number of clusters
        - Useful for discovering natural groupings
    """
    if not data:
        raise ValueError("Data cannot be empty")

    if n_clusters <= 0:
        raise ValueError(f"n_clusters must be positive: {n_clusters}")

    if n_clusters > len(data):
        raise ValueError(
            f"n_clusters ({n_clusters}) cannot exceed number of points ({len(data)})"
        )

    if linkage not in ["single", "complete", "average"]:
        raise ValueError(
            f"Unknown linkage: {linkage}. Use 'single', 'complete', or 'average'"
        )

    # Initialize: each point is its own cluster
    clusters = [[i] for i in range(len(data))]
    dendrogram = []

    # Merge until we have desired number of clusters
    while len(clusters) > n_clusters:
        # Find pair of clusters with minimum distance
        min_distance = float("inf")
        merge_i, merge_j = 0, 1

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                distance = _cluster_distance(clusters[i], clusters[j], data, linkage)

                if distance < min_distance:
                    min_distance = distance
                    merge_i, merge_j = i, j

        # Merge the two closest clusters
        merged = clusters[merge_i] + clusters[merge_j]
        dendrogram.append((merge_i, merge_j, min_distance))

        # Remove old clusters and add merged one
        # Remove in reverse order to preserve indices
        if merge_i < merge_j:
            clusters.pop(merge_j)
            clusters.pop(merge_i)
        else:
            clusters.pop(merge_i)
            clusters.pop(merge_j)

        clusters.append(merged)

    # Create cluster assignments
    cluster_assignments = [0] * len(data)
    for cluster_id, cluster_points in enumerate(clusters):
        for point_idx in cluster_points:
            cluster_assignments[point_idx] = cluster_id

    return {
        "clusters": cluster_assignments,
        "dendrogram": [
            {"cluster1": i, "cluster2": j, "distance": d} for i, j, d in dendrogram
        ],
        "final_clusters": len(clusters),
        "linkage_used": linkage,
        "cluster_sizes": [len(cluster) for cluster in clusters],
    }


def _cluster_distance(
    cluster1: List[int],
    cluster2: List[int],
    data: List[List[Union[int, float]]],
    linkage: str,
) -> float:
    """
    Calculate distance between two clusters based on linkage criterion.

    Args:
        cluster1: Indices of points in first cluster
        cluster2: Indices of points in second cluster
        data: All data points
        linkage: Linkage criterion

    Returns:
        Distance between clusters
    """
    distances = []

    for i in cluster1:
        for j in cluster2:
            distance = calculate_euclidean_distance(data[i], data[j])
            distances.append(distance)

    if linkage == "single":
        # Minimum distance
        return min(distances)
    elif linkage == "complete":
        # Maximum distance
        return max(distances)
    elif linkage == "average":
        # Average distance
        return sum(distances) / len(distances)
    else:
        raise ValueError(f"Unknown linkage: {linkage}")


# ============================================================================
# Utility Functions
# ============================================================================


def normalize_features(
    data: List[List[Union[int, float]]], method: str = "min-max"
) -> List[List[float]]:
    """
    Normalize features to [0, 1] range (min-max) or standardize (z-score).

    This is a utility function - not exposed as MCP tool yet.
    Will be in ml_feature_helper.py as a full MCP tool.

    Args:
        data: Data to normalize
        method: "min-max" or "z-score"

    Returns:
        Normalized data
    """
    if not data:
        return []

    dimensions = len(data[0])

    if method == "min-max":
        # Find min and max for each dimension
        mins = [min(point[dim] for point in data) for dim in range(dimensions)]
        maxs = [max(point[dim] for point in data) for dim in range(dimensions)]

        # Normalize: (x - min) / (max - min)
        normalized = []
        for point in data:
            normalized_point = [
                (
                    (point[dim] - mins[dim]) / (maxs[dim] - mins[dim])
                    if maxs[dim] != mins[dim]
                    else 0.0
                )
                for dim in range(dimensions)
            ]
            normalized.append(normalized_point)

        return normalized

    elif method == "z-score":
        # Calculate mean and std for each dimension
        means = [
            sum(point[dim] for point in data) / len(data) for dim in range(dimensions)
        ]

        stds = [
            math.sqrt(sum((point[dim] - means[dim]) ** 2 for point in data) / len(data))
            for dim in range(dimensions)
        ]

        # Standardize: (x - mean) / std
        normalized = []
        for point in data:
            normalized_point = [
                (point[dim] - means[dim]) / stds[dim] if stds[dim] != 0 else 0.0
                for dim in range(dimensions)
            ]
            normalized.append(normalized_point)

        return normalized

    else:
        raise ValueError(f"Unknown normalization method: {method}")
