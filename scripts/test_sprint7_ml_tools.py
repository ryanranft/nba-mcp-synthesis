#!/usr/bin/env python3
"""
Test Suite for Sprint 7 ML Tools

Tests all 18 machine learning tools:
- 5 Clustering tools
- 8 Classification tools (4 train/predict pairs)
- 3 Anomaly detection tools
- 2 Feature engineering tools

Run: python scripts/test_sprint7_ml_tools.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_server.tools import (
    ml_clustering_helper,
    ml_classification_helper,
    ml_anomaly_helper,
    ml_feature_helper,
)


class TestRunner:
    """Simple test runner with pass/fail tracking"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name, actual, expected=None, check_type=None):
        """Run a test"""
        try:
            if expected is not None:
                # Check equality
                if isinstance(expected, float):
                    success = abs(actual - expected) < 0.01
                else:
                    success = actual == expected
            elif check_type is not None:
                # Check type
                success = isinstance(actual, check_type)
            else:
                # Just check truthy
                success = bool(actual)

            if success:
                print(f"✓ {name}")
                self.passed += 1
            else:
                print(f"✗ {name}")
                print(f"  Expected: {expected}, Got: {actual}")
                self.failed += 1

            self.tests.append((name, success))

        except Exception as e:
            print(f"✗ {name} - Exception: {e}")
            self.failed += 1
            self.tests.append((name, False))

    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Tests: {total} total, {self.passed} passed, {self.failed} failed")
        print(f"Success Rate: {(self.passed/total*100):.1f}%")
        print(f"{'='*60}")
        return self.failed == 0


def test_clustering_tools():
    """Test clustering and similarity tools"""
    print("\n" + "=" * 60)
    print("Testing Clustering Tools (5 tests)")
    print("=" * 60)

    runner = TestRunner()

    # Test 1: Euclidean distance
    dist = ml_clustering_helper.calculate_euclidean_distance([0, 0], [3, 4])
    runner.test("Euclidean distance (3-4-5 triangle)", dist, 5.0)

    # Test 2: Cosine similarity (identical vectors)
    sim = ml_clustering_helper.calculate_cosine_similarity([1, 2, 3], [2, 4, 6])
    runner.test("Cosine similarity (same direction)", sim, 1.0)

    # Test 3: K-means clustering
    data = [[25, 5], [22, 6], [28, 4], [10, 15], [12, 14], [11, 16]]
    result = ml_clustering_helper.kmeans_clustering(data, k=2, random_seed=42)
    runner.test("K-means converged", result["converged"], True)
    runner.test("K-means created 2 clusters", len(result["centroids"]), 2)

    # Test 4: K-NN classification
    train_data = [[20, 5], [22, 6], [10, 15], [12, 14]]
    train_labels = ["scorer", "scorer", "rebounder", "rebounder"]
    test_point = [21, 5]

    knn_result = ml_clustering_helper.find_nearest_neighbors(
        test_point, train_data, train_labels, k=3
    )
    runner.test("K-NN prediction", knn_result["prediction"], "scorer")

    # Test 5: Hierarchical clustering
    small_data = [[1, 1], [2, 2], [10, 10]]
    hier_result = ml_clustering_helper.hierarchical_clustering(
        small_data, n_clusters=2, linkage="average"
    )
    runner.test(
        "Hierarchical clustering created 2 clusters", hier_result["final_clusters"], 2
    )

    return runner.summary()


def test_classification_tools():
    """Test classification tools"""
    print("\n" + "=" * 60)
    print("Testing Classification Tools (12 tests)")
    print("=" * 60)

    runner = TestRunner()

    # Prepare training data (linearly separable)
    X_train = [[1, 1], [2, 2], [3, 3], [8, 8], [9, 9], [10, 10]]  # Class 0  # Class 1
    y_train_binary = [0, 0, 0, 1, 1, 1]
    y_train_multi = ["A", "A", "A", "B", "B", "B"]

    # Test 1-3: Logistic Regression
    print("\nLogistic Regression:")
    lr_model = ml_classification_helper.logistic_regression(
        X_train, y_train_binary, learning_rate=0.1, max_iterations=100
    )
    runner.test("Logistic regression trained", "weights" in lr_model, True)
    runner.test(
        "Logistic regression has correct weight count", len(lr_model["weights"]), 3
    )  # 2 features + 1 bias

    # Make predictions
    X_test = [[2, 2], [9, 9]]
    lr_pred = ml_classification_helper.logistic_predict(
        X_test, lr_model["weights"], return_probabilities=True
    )
    runner.test("Logistic predictions", len(lr_pred["predictions"]), 2)
    runner.test("Logistic probabilities returned", "probabilities" in lr_pred, True)

    # Test 4-6: Naive Bayes
    print("\nNaive Bayes:")
    nb_model = ml_classification_helper.naive_bayes_train(X_train, y_train_multi)
    runner.test("Naive Bayes trained", "classes" in nb_model, True)
    runner.test("Naive Bayes found 2 classes", len(nb_model["classes"]), 2)

    nb_pred = ml_classification_helper.naive_bayes_predict(X_test, nb_model)
    runner.test("Naive Bayes predictions", len(nb_pred["predictions"]), 2)
    runner.test("Naive Bayes confidence scores", len(nb_pred["confidence"]), 2)

    # Test 7-9: Decision Tree
    print("\nDecision Tree:")
    dt_model = ml_classification_helper.decision_tree_train(
        X_train, y_train_multi, max_depth=3
    )
    runner.test("Decision tree trained", "tree" in dt_model, True)
    runner.test("Decision tree has leaves", dt_model["num_leaves"] > 0, True)

    dt_pred = ml_classification_helper.decision_tree_predict(X_test, dt_model["tree"])
    runner.test("Decision tree predictions", len(dt_pred["predictions"]), 2)
    runner.test("Decision tree paths", "paths" in dt_pred, True)

    # Test 10-12: Random Forest
    print("\nRandom Forest:")
    rf_model = ml_classification_helper.random_forest_train(
        X_train, y_train_multi, n_trees=5, max_depth=3, random_seed=42
    )
    runner.test("Random forest trained", "trees" in rf_model, True)
    runner.test("Random forest has 5 trees", len(rf_model["trees"]), 5)

    rf_pred = ml_classification_helper.random_forest_predict(X_test, rf_model)
    runner.test("Random forest predictions", len(rf_pred["predictions"]), 2)

    return runner.summary()


def test_anomaly_detection_tools():
    """Test anomaly detection tools"""
    print("\n" + "=" * 60)
    print("Testing Anomaly Detection Tools (9 tests)")
    print("=" * 60)

    runner = TestRunner()

    # Create data with outliers
    # Normal points around [5, 5], outlier at [50, 50]
    data = [
        [5, 5],
        [6, 5],
        [5, 6],
        [6, 6],
        [4, 5],
        [5, 4],
        [7, 5],
        [5, 7],
        [50, 50],  # Outlier
    ]

    # Test 1-3: Z-score outlier detection
    print("\nZ-score Outlier Detection:")
    zscore_result = ml_anomaly_helper.detect_outliers_zscore(data, threshold=2.0)
    runner.test("Z-score detected outliers", zscore_result["outlier_count"] > 0, True)
    runner.test("Z-score found the outlier", zscore_result["outlier_count"], 1)
    runner.test("Z-score returned statistics", "feature_means" in zscore_result, True)

    # Test 4-6: Isolation Forest
    print("\nIsolation Forest:")
    iforest_result = ml_anomaly_helper.isolation_forest(
        data, n_trees=10, contamination=0.1, random_seed=42
    )
    runner.test(
        "Isolation forest detected anomalies", iforest_result["anomaly_count"] > 0, True
    )
    runner.test(
        "Isolation forest returned scores",
        len(iforest_result["anomaly_scores"]) == len(data),
        True,
    )
    runner.test("Isolation forest has threshold", "threshold" in iforest_result, True)

    # Test 7-9: Local Outlier Factor
    print("\nLocal Outlier Factor:")
    lof_result = ml_anomaly_helper.local_outlier_factor(data, k=3, contamination=0.1)
    runner.test("LOF detected anomalies", lof_result["anomaly_count"] > 0, True)
    runner.test("LOF returned scores", len(lof_result["lof_scores"]) == len(data), True)
    runner.test("LOF interpretation included", "interpretation" in lof_result, True)

    return runner.summary()


def test_feature_engineering_tools():
    """Test feature engineering tools"""
    print("\n" + "=" * 60)
    print("Testing Feature Engineering Tools (8 tests)")
    print("=" * 60)

    runner = TestRunner()

    # Test data
    data = [[10, 100], [20, 200], [30, 300]]

    # Test 1-4: Feature normalization (different methods)
    print("\nFeature Normalization:")

    # Min-max normalization
    minmax_result = ml_feature_helper.normalize_features(
        data, method="min-max", feature_range=(0, 1)
    )
    runner.test("Min-max normalization", "normalized_data" in minmax_result, True)
    runner.test(
        "Min-max values in range", minmax_result["normalized_data"][0][0], 0.0
    )  # Min should be 0
    runner.test(
        "Min-max max value", minmax_result["normalized_data"][2][0], 1.0
    )  # Max should be 1

    # Z-score normalization
    zscore_norm = ml_feature_helper.normalize_features(data, method="z-score")
    runner.test("Z-score normalization", "normalized_data" in zscore_norm, True)

    # Robust normalization
    robust_norm = ml_feature_helper.normalize_features(data, method="robust")
    runner.test("Robust normalization", "normalized_data" in robust_norm, True)

    # Max-abs normalization
    maxabs_norm = ml_feature_helper.normalize_features(data, method="max-abs")
    runner.test("Max-abs normalization", "normalized_data" in maxabs_norm, True)

    # Test 7-8: Feature importance
    print("\nFeature Importance:")
    X = [[1, 10], [2, 20], [3, 30], [4, 40]]
    y = [0, 0, 1, 1]
    predictions = [0, 0, 1, 1]  # Perfect predictions

    importance_result = ml_feature_helper.calculate_feature_importance(
        X, y, predictions, n_repeats=5, random_seed=42
    )
    runner.test(
        "Feature importance calculated", "importance_scores" in importance_result, True
    )
    runner.test(
        "Feature ranking provided", "feature_ranking" in importance_result, True
    )

    return runner.summary()


def test_nba_use_cases():
    """Test realistic NBA use cases"""
    print("\n" + "=" * 60)
    print("Testing NBA Use Cases (5 tests)")
    print("=" * 60)

    runner = TestRunner()

    # Use case 1: Cluster players by stats
    print("\nUse Case 1: Player Clustering")
    player_stats = [
        [28, 3, 5],  # High scorer (PPG, APG, RPG)
        [25, 4, 4],  # High scorer
        [30, 2, 6],  # High scorer
        [15, 8, 4],  # Playmaker
        [12, 9, 5],  # Playmaker
        [14, 7, 3],  # Playmaker
        [8, 2, 12],  # Rebounder
        [10, 1, 11],  # Rebounder
    ]

    clusters = ml_clustering_helper.kmeans_clustering(player_stats, k=3, random_seed=42)
    runner.test("Clustered players into 3 archetypes", len(clusters["centroids"]), 3)

    # Use case 2: Predict All-Star (binary classification)
    print("\nUse Case 2: All-Star Prediction")
    player_features = [
        [28, 0.62, 25],  # PPG, TS%, PER - All-Star
        [26, 0.60, 23],  # All-Star
        [15, 0.55, 18],  # Not All-Star
        [12, 0.52, 15],  # Not All-Star
    ]
    is_allstar = [1, 1, 0, 0]

    allstar_model = ml_classification_helper.logistic_regression(
        player_features, is_allstar, learning_rate=0.1, max_iterations=200
    )
    runner.test("All-Star model trained", "weights" in allstar_model, True)

    # Use case 3: Detect outlier performances
    print("\nUse Case 3: Outlier Performance Detection")
    game_scores = [[20], [22], [19], [21], [50]]  # 50 is outlier

    outliers = ml_anomaly_helper.detect_outliers_zscore(
        game_scores, threshold=1.9  # Lower threshold to catch the outlier
    )
    runner.test(
        "Detected outlier game (50 points)", outliers["outlier_count"] > 0, True
    )

    # Use case 4: Normalize stats for comparison
    print("\nUse Case 4: Stat Normalization")
    raw_stats = [
        [25, 5, 5],  # Player 1
        [30, 7, 8],  # Player 2
        [20, 4, 3],  # Player 3
    ]

    normalized = ml_feature_helper.normalize_features(raw_stats, method="min-max")
    runner.test(
        "Normalized stats for comparison", len(normalized["normalized_data"]), 3
    )

    # Use case 5: Position classification with KNN
    print("\nUse Case 5: Position Classification")
    # Training: [Height cm, Weight kg, PPG]
    train_players = [
        [193, 88, 18],  # PG
        [196, 91, 20],  # SG
        [201, 95, 16],  # SF
        [208, 105, 12],  # PF
        [213, 115, 14],  # C
    ]
    positions = ["PG", "SG", "SF", "PF", "C"]

    # Test player
    test_player = [198, 93, 17]  # Should be SF or SG

    position_pred = ml_clustering_helper.find_nearest_neighbors(
        test_player, train_players, positions, k=3
    )
    runner.test(
        "Predicted player position", position_pred["prediction"] in ["SG", "SF"], True
    )

    return runner.summary()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Sprint 7 ML Tools Test Suite")
    print("Testing 18 ML tools with 39 test cases")
    print("=" * 60)

    results = []

    # Run test suites
    results.append(test_clustering_tools())
    results.append(test_classification_tools())
    results.append(test_anomaly_detection_tools())
    results.append(test_feature_engineering_tools())
    results.append(test_nba_use_cases())

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    if all(results):
        print("✓ All test suites passed!")
        print("\nSprint 7 ML Tools: READY FOR PRODUCTION")
        return 0
    else:
        print("✗ Some tests failed")
        print("\nPlease review failed tests above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
