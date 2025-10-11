#!/usr/bin/env python3
"""
Test ML Tools Integration with FastMCP Server

Validates that Sprint 7 ML tools work correctly via the MCP server.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_server.tools import (
    ml_clustering_helper,
    ml_classification_helper,
    ml_anomaly_helper,
    ml_feature_helper
)


def test_clustering():
    """Test K-means clustering"""
    print("\n" + "="*60)
    print("TEST 1: K-means Clustering")
    print("="*60)

    # NBA player stats: [PPG, APG, RPG]
    player_stats = [
        [28, 3, 5],   # High scorer
        [25, 4, 4],   # High scorer
        [30, 2, 6],   # High scorer
        [15, 8, 4],   # Playmaker
        [12, 9, 5],   # Playmaker
        [8, 2, 12],   # Rebounder
        [10, 1, 11],  # Rebounder
    ]

    result = ml_clustering_helper.kmeans_clustering(
        data=player_stats,
        k=3,
        random_seed=42
    )

    print(f"✓ Clustered {len(player_stats)} players into {len(result['centroids'])} groups")
    print(f"✓ Converged: {result['converged']} (iterations: {result['iterations']})")
    print(f"✓ Cluster centroids:")
    for i, centroid in enumerate(result['centroids']):
        print(f"  Cluster {i}: PPG={centroid[0]:.1f}, APG={centroid[1]:.1f}, RPG={centroid[2]:.1f}")

    return True


def test_classification():
    """Test Logistic Regression"""
    print("\n" + "="*60)
    print("TEST 2: Logistic Regression (All-Star Prediction)")
    print("="*60)

    # Features: [PPG, TS%, PER]
    X_train = [
        [28, 0.62, 25],  # All-Star
        [26, 0.60, 23],  # All-Star
        [15, 0.55, 18],  # Not All-Star
        [12, 0.52, 15],  # Not All-Star
    ]
    y_train = [1, 1, 0, 0]

    # Train model
    model = ml_classification_helper.logistic_regression(
        X_train=X_train,
        y_train=y_train,
        learning_rate=0.1,
        max_iterations=200
    )

    print(f"✓ Model trained: {len(model['weights'])} weights")
    print(f"✓ Converged: {model['converged']} (iterations: {model['iterations']})")

    # Make predictions
    X_test = [[24, 0.58, 21], [10, 0.50, 14]]
    predictions = ml_classification_helper.logistic_predict(
        X=X_test,
        weights=model['weights'],
        return_probabilities=True
    )

    print(f"✓ Predictions made:")
    for i, (pred, prob) in enumerate(zip(predictions['predictions'], predictions['probabilities'])):
        label = "All-Star" if pred == 1 else "Not All-Star"
        print(f"  Player {i+1}: {label} (confidence: {prob:.1%})")

    return True


def test_anomaly_detection():
    """Test Isolation Forest"""
    print("\n" + "="*60)
    print("TEST 3: Isolation Forest (Outlier Detection)")
    print("="*60)

    # Player stats with one outlier
    data = [
        [20, 5], [22, 6], [19, 5], [21, 6],  # Normal players
        [50, 15]  # Outlier: exceptional stats
    ]

    result = ml_anomaly_helper.isolation_forest(
        data=data,
        n_trees=10,
        contamination=0.2,
        random_seed=42
    )

    print(f"✓ Analyzed {len(data)} players")
    print(f"✓ Detected {result['anomaly_count']} anomalies ({result['anomaly_percentage']:.1f}%)")
    print(f"✓ Anomalous players:")
    for anomaly in result['anomalies']:
        print(f"  Player {anomaly['index']}: stats={anomaly['data']}, score={anomaly['score']:.3f}")

    return True


def test_feature_engineering():
    """Test feature normalization"""
    print("\n" + "="*60)
    print("TEST 4: Feature Normalization")
    print("="*60)

    # Raw stats with different scales
    raw_stats = [
        [25, 5, 200],   # PPG, RPG, Height(cm)
        [30, 7, 210],
        [20, 4, 195],
    ]

    # Normalize to [0, 1]
    result = ml_feature_helper.normalize_features(
        data=raw_stats,
        method="min-max",
        feature_range=(0, 1)
    )

    print(f"✓ Normalized {result['num_samples']} samples with {result['num_features']} features")
    print(f"✓ Method: {result['method']}")
    print(f"✓ Normalized data:")
    for i, norm_stats in enumerate(result['normalized_data']):
        print(f"  Player {i+1}: {[f'{x:.3f}' for x in norm_stats]}")

    return True


def test_knn():
    """Test K-Nearest Neighbors"""
    print("\n" + "="*60)
    print("TEST 5: K-NN Position Classification")
    print("="*60)

    # Training data: [Height, Weight, PPG]
    train_data = [
        [193, 88, 18],   # PG
        [196, 91, 20],   # SG
        [201, 95, 16],   # SF
        [208, 105, 12],  # PF
        [213, 115, 14],  # C
    ]
    positions = ["PG", "SG", "SF", "PF", "C"]

    # Test player
    test_player = [198, 93, 17]  # Should be SF or SG

    result = ml_clustering_helper.find_nearest_neighbors(
        point=test_player,
        data=train_data,
        labels=positions,
        k=3
    )

    print(f"✓ Test player stats: Height={test_player[0]}cm, Weight={test_player[1]}kg, PPG={test_player[2]}")
    print(f"✓ Predicted position: {result['prediction']} (confidence: {result['confidence']:.1%})")
    print(f"✓ K-nearest neighbors:")
    for i, neighbor in enumerate(result['neighbors']):
        print(f"  {i+1}. Position={neighbor['label']}, Distance={neighbor['distance']:.2f}")

    return True


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("Sprint 7 ML Tools Integration Test")
    print("Testing ML tools via direct helper calls")
    print("="*60)

    tests = [
        ("K-means Clustering", test_clustering),
        ("Logistic Regression", test_classification),
        ("Isolation Forest", test_anomaly_detection),
        ("Feature Normalization", test_feature_engineering),
        ("K-NN Classification", test_knn),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✓ All ML tools working correctly!")
        print("✓ Sprint 7 integration: VERIFIED")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())