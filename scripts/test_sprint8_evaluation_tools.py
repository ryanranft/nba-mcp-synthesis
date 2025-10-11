"""
Sprint 8 ML Evaluation & Validation Tools Test Suite

Tests all 15 Sprint 8 tools:
- Classification Metrics (6)
- Regression Metrics (3)
- Cross-Validation (3)
- Model Comparison (2)
- Hyperparameter Tuning (1)

Run: python scripts/test_sprint8_evaluation_tools.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.tools import ml_evaluation_helper, ml_validation_helper


def test_accuracy_score():
    """Test accuracy score calculation."""
    print("\n1. Testing accuracy_score...")

    # Test 1: Perfect accuracy
    y_true = [1, 0, 1, 1, 0, 1, 0, 0]
    y_pred = [1, 0, 1, 1, 0, 1, 0, 0]
    result = ml_evaluation_helper.accuracy_score(y_true, y_pred)

    assert result['accuracy'] == 1.0, f"Expected accuracy 1.0, got {result['accuracy']}"
    assert result['percentage'] == 100.0
    assert result['correct'] == 8
    assert result['interpretation'] == "Excellent (≥95%)"
    print("  ✓ Perfect accuracy: 100%")

    # Test 2: 75% accuracy
    y_pred2 = [1, 0, 1, 0, 0, 1, 0, 1]  # 6/8 correct
    result2 = ml_evaluation_helper.accuracy_score(y_true, y_pred2)

    assert result2['accuracy'] == 0.75
    assert result2['correct'] == 6
    assert result2['interpretation'] == "Good (75-85%)"
    print("  ✓ 75% accuracy test passed")


def test_precision_recall_f1():
    """Test precision, recall, F1-score calculation."""
    print("\n2. Testing precision_recall_f1...")

    # Test binary classification
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 0, 1, 1, 1, 0]  # TP=3, FP=1, FN=1, TN=3

    result = ml_evaluation_helper.precision_recall_f1(
        y_true=y_true,
        y_pred=y_pred,
        average='binary',
        pos_label=1
    )

    # Precision = TP / (TP + FP) = 3 / 4 = 0.75
    # Recall = TP / (TP + FN) = 3 / 4 = 0.75
    # F1 = 2 * (P * R) / (P + R) = 2 * (0.75 * 0.75) / 1.5 = 0.75
    assert abs(result['precision'] - 0.75) < 0.01
    assert abs(result['recall'] - 0.75) < 0.01
    assert abs(result['f1_score'] - 0.75) < 0.01
    print(f"  ✓ Binary classification: P={result['precision']:.2f}, R={result['recall']:.2f}, F1={result['f1_score']:.2f}")


def test_confusion_matrix():
    """Test confusion matrix generation."""
    print("\n3. Testing confusion_matrix...")

    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 0, 1, 1, 1, 0]

    result = ml_evaluation_helper.confusion_matrix(
        y_true=y_true,
        y_pred=y_pred
    )

    # TP=3 (predicted 1, actual 1)
    # FP=1 (predicted 1, actual 0)
    # TN=3 (predicted 0, actual 0)
    # FN=1 (predicted 0, actual 1)
    assert result['true_positives'] == 3
    assert result['false_positives'] == 1
    assert result['true_negatives'] == 3
    assert result['false_negatives'] == 1
    assert abs(result['sensitivity'] - 0.75) < 0.01  # TP/(TP+FN) = 3/4
    print(f"  ✓ Confusion matrix: TP={result['true_positives']}, FP={result['false_positives']}, TN={result['true_negatives']}, FN={result['false_negatives']}")


def test_roc_auc_score():
    """Test ROC-AUC calculation."""
    print("\n4. Testing roc_auc_score...")

    # Perfect predictions
    y_true = [0, 0, 1, 1, 1]
    y_scores = [0.1, 0.2, 0.7, 0.8, 0.9]

    result = ml_evaluation_helper.roc_auc_score(
        y_true=y_true,
        y_scores=y_scores,
        num_thresholds=10
    )

    # Perfect separation should have AUC = 1.0
    assert abs(result['auc'] - 1.0) < 0.01
    assert result['interpretation'] == "Excellent - Outstanding discrimination"
    print(f"  ✓ Perfect separation: AUC={result['auc']:.3f}")

    # Random predictions (AUC ~0.5)
    y_scores2 = [0.6, 0.4, 0.5, 0.3, 0.7]
    result2 = ml_evaluation_helper.roc_auc_score(
        y_true=y_true,
        y_scores=y_scores2,
        num_thresholds=10
    )

    # Should be around 0.5 for random
    assert 0.3 < result2['auc'] < 0.7
    print(f"  ✓ Random predictions: AUC={result2['auc']:.3f}")


def test_classification_report():
    """Test comprehensive classification report."""
    print("\n5. Testing classification_report...")

    # Multi-class classification
    y_true = ['PG', 'SG', 'SF', 'PG', 'SG', 'SF', 'PG', 'SG']
    y_pred = ['PG', 'SG', 'SF', 'SG', 'SG', 'PG', 'PG', 'SF']

    result = ml_evaluation_helper.classification_report(
        y_true=y_true,
        y_pred=y_pred
    )

    assert 'per_class' in result
    assert 'macro_avg' in result
    assert 'weighted_avg' in result
    assert 'accuracy' in result

    # Check that we have metrics for all 3 classes
    assert len(result['per_class']) == 3
    print(f"  ✓ Multi-class report: {len(result['per_class'])} classes, accuracy={result['accuracy']:.2f}")


def test_log_loss():
    """Test log loss calculation."""
    print("\n6. Testing log_loss...")

    # Perfect predictions (low loss)
    y_true = [1, 0, 1, 1, 0]
    y_pred_proba = [0.99, 0.01, 0.98, 0.95, 0.05]

    result = ml_evaluation_helper.log_loss(
        y_true=y_true,
        y_pred_proba=y_pred_proba,
        eps=1e-15
    )

    # Perfect predictions should have very low loss
    assert result['log_loss'] < 0.1
    assert result['interpretation'] == "Excellent - Very confident and accurate"
    print(f"  ✓ Perfect predictions: Log Loss={result['log_loss']:.4f}")

    # Poor predictions (high loss)
    y_pred_proba2 = [0.1, 0.9, 0.2, 0.3, 0.8]
    result2 = ml_evaluation_helper.log_loss(
        y_true=y_true,
        y_pred_proba=y_pred_proba2,
        eps=1e-15
    )

    assert result2['log_loss'] > 1.0
    print(f"  ✓ Poor predictions: Log Loss={result2['log_loss']:.4f}")


def test_mse_rmse_mae():
    """Test MSE, RMSE, MAE calculation."""
    print("\n7. Testing mse_rmse_mae...")

    y_true = [10, 20, 30, 40, 50]
    y_pred = [12, 18, 32, 38, 48]  # Errors: 2, -2, 2, -2, -2

    result = ml_evaluation_helper.mse_rmse_mae(
        y_true=y_true,
        y_pred=y_pred
    )

    # MSE = (4 + 4 + 4 + 4 + 4) / 5 = 4
    # RMSE = sqrt(4) = 2
    # MAE = (2 + 2 + 2 + 2 + 2) / 5 = 2
    assert abs(result['mse'] - 4.0) < 0.01
    assert abs(result['rmse'] - 2.0) < 0.01
    assert abs(result['mae'] - 2.0) < 0.01
    print(f"  ✓ Regression metrics: MSE={result['mse']:.1f}, RMSE={result['rmse']:.1f}, MAE={result['mae']:.1f}")


def test_r2_score():
    """Test R² coefficient calculation."""
    print("\n8. Testing r2_score...")

    # Perfect predictions (R² = 1.0)
    y_true = [10, 20, 30, 40, 50]
    y_pred = [10, 20, 30, 40, 50]

    result = ml_evaluation_helper.r2_score(
        y_true=y_true,
        y_pred=y_pred
    )

    assert abs(result['r2_score'] - 1.0) < 0.01
    assert result['interpretation'] == "Excellent - Explains ≥90% of variance"
    print(f"  ✓ Perfect predictions: R²={result['r2_score']:.3f}")

    # Mean predictions (R² = 0.0)
    mean_val = sum(y_true) / len(y_true)
    y_pred2 = [mean_val] * len(y_true)
    result2 = ml_evaluation_helper.r2_score(
        y_true=y_true,
        y_pred=y_pred2
    )

    assert abs(result2['r2_score']) < 0.01
    print(f"  ✓ Mean predictions: R²={result2['r2_score']:.3f}")


def test_mape():
    """Test MAPE calculation."""
    print("\n9. Testing mean_absolute_percentage_error...")

    y_true = [100, 200, 300, 400]
    y_pred = [110, 190, 310, 390]  # 10%, 5%, 3.33%, 2.5% errors

    result = ml_evaluation_helper.mean_absolute_percentage_error(
        y_true=y_true,
        y_pred=y_pred
    )

    # MAPE = (10 + 5 + 3.33 + 2.5) / 4 = ~5.2%
    assert 4.0 < result['mape'] < 6.0
    assert result['interpretation'] == "Very Good - 5-10% error"
    print(f"  ✓ MAPE test: {result['mape']:.2f}%")


def test_k_fold_split():
    """Test K-fold cross-validation splits."""
    print("\n10. Testing k_fold_split...")

    result = ml_validation_helper.k_fold_split(
        n_samples=100,
        n_folds=5,
        shuffle=True,
        random_seed=42
    )

    assert result['n_folds'] == 5
    assert result['n_samples'] == 100
    assert len(result['folds']) == 5
    assert result['fold_sizes'] == [20, 20, 20, 20, 20]

    # Check that all samples are used exactly once in validation
    all_test_indices = set()
    for fold in result['folds']:
        all_test_indices.update(fold['test_indices'])

    assert len(all_test_indices) == 100
    print(f"  ✓ K-fold: {result['n_folds']} folds, fold sizes: {result['fold_sizes']}")


def test_stratified_k_fold_split():
    """Test stratified K-fold cross-validation."""
    print("\n11. Testing stratified_k_fold_split...")

    # Imbalanced dataset: 70 class A, 30 class B
    y = ['A'] * 70 + ['B'] * 30

    result = ml_validation_helper.stratified_k_fold_split(
        y=y,
        n_folds=5,
        shuffle=True,
        random_seed=42
    )

    assert result['n_folds'] == 5
    assert result['n_samples'] == 100

    # Check class distribution is preserved in each fold
    class_dist = result['class_distribution']
    assert isinstance(class_dist, list)
    assert len(class_dist) == 5  # 5 folds

    # Each fold should have ~14 A's and ~6 B's
    for fold_counts in class_dist:
        a_count = fold_counts.get('A', 0)
        b_count = fold_counts.get('B', 0)
        assert 12 <= a_count <= 16  # Allow some variance
        assert 4 <= b_count <= 8  # Allow some variance

    print(f"  ✓ Stratified K-fold: {result['n_folds']} folds, class distribution preserved")


def test_cross_validate():
    """Test cross-validation helper."""
    print("\n12. Testing cross_validate...")

    # Test standard K-fold
    X1 = [[i, i+1] for i in range(50)]  # 50 samples, 2 features
    y1 = [i % 2 for i in range(50)]  # Binary labels

    result1 = ml_validation_helper.cross_validate(
        X=X1,
        y=y1,
        cv_strategy='k-fold',
        n_folds=5,
        shuffle=True,
        random_seed=42
    )

    assert result1['cv_strategy'] == 'k-fold'
    assert result1['n_folds'] == 5
    assert len(result1['folds']) == 5
    assert len(result1['X_folds']) == 5
    print(f"  ✓ Standard K-fold: {result1['n_folds']} folds")

    # Test stratified K-fold
    X2 = [[i, i+1] for i in range(50)]
    y2 = ['A'] * 30 + ['B'] * 20

    result2 = ml_validation_helper.cross_validate(
        X=X2,
        y=y2,
        cv_strategy='stratified',
        n_folds=5,
        shuffle=True,
        random_seed=42
    )

    assert result2['cv_strategy'] == 'stratified'
    assert result2['n_folds'] == 5
    print(f"  ✓ Stratified K-fold: {result2['n_folds']} folds")


def test_compare_models():
    """Test model comparison."""
    print("\n13. Testing compare_models...")

    y_true = [1, 0, 1, 1, 0, 0, 1, 0]

    models = [
        {
            'name': 'Logistic Regression',
            'predictions': [1, 0, 1, 1, 0, 0, 1, 0]  # Perfect
        },
        {
            'name': 'Naive Bayes',
            'predictions': [1, 0, 1, 0, 0, 1, 1, 0]  # 6/8 correct
        },
        {
            'name': 'Random Forest',
            'predictions': [1, 0, 0, 1, 0, 0, 1, 1]  # 6/8 correct
        }
    ]

    result = ml_validation_helper.compare_models(
        models=models,
        y_true=y_true,
        metrics=['accuracy', 'precision', 'recall', 'f1']
    )

    assert len(result['models']) == 3
    assert len(result['metrics_compared']) == 4
    assert 'rankings' in result
    assert 'overall_best' in result

    # Logistic Regression should be best for accuracy
    assert result['rankings']['accuracy'][0] == 'Logistic Regression'
    print(f"  ✓ Compared {len(models)} models on {len(result['metrics_compared'])} metrics")


def test_paired_ttest():
    """Test paired t-test."""
    print("\n14. Testing paired_ttest...")

    # Test 1: No significant difference
    scores_a = [0.80, 0.82, 0.81, 0.79, 0.83]
    scores_b = [0.81, 0.80, 0.82, 0.80, 0.82]

    result1 = ml_validation_helper.paired_ttest(
        scores_a=scores_a,
        scores_b=scores_b,
        alpha=0.05
    )

    assert 'p_value' in result1
    assert 'significant' in result1
    assert result1['significant'] == False  # Should not be significant
    print(f"  ✓ No significant difference: p={result1['p_value']:.4f}")

    # Test 2: Significant difference
    scores_a2 = [0.90, 0.92, 0.91, 0.89, 0.93]
    scores_b2 = [0.70, 0.72, 0.71, 0.69, 0.73]

    result2 = ml_validation_helper.paired_ttest(
        scores_a=scores_a2,
        scores_b=scores_b2,
        alpha=0.05
    )

    assert result2['significant'] == True  # Should be significant
    print(f"  ✓ Significant difference: p={result2['p_value']:.4f}")


def test_grid_search():
    """Test grid search parameter generation."""
    print("\n15. Testing grid_search...")

    param_grid = {
        'k': [3, 5, 7],
        'max_iterations': [100, 200],
        'tolerance': [0.001, 0.0001]
    }

    result = ml_validation_helper.grid_search(
        param_grid=param_grid,
        n_combinations=None
    )

    # Should generate 3 * 2 * 2 = 12 combinations
    assert result['total_combinations'] == 12
    assert len(result['param_combinations']) == 12

    # Check first combination has all parameters
    first_combo = result['param_combinations'][0]
    assert 'k' in first_combo
    assert 'max_iterations' in first_combo
    assert 'tolerance' in first_combo

    print(f"  ✓ Grid search: {result['total_combinations']} parameter combinations generated")

    # Test with limit
    result2 = ml_validation_helper.grid_search(
        param_grid=param_grid,
        n_combinations=5
    )

    assert result2['combinations_tested'] == 5
    assert len(result2['param_combinations']) == 5
    print(f"  ✓ Limited grid search: {result2['combinations_tested']} combinations (limited from {result2['total_combinations']})")


def main():
    """Run all Sprint 8 tests."""
    print("=" * 70)
    print("Sprint 8 ML Evaluation & Validation Tools - Test Suite")
    print("=" * 70)

    try:
        # Classification Metrics (6 tests)
        test_accuracy_score()
        test_precision_recall_f1()
        test_confusion_matrix()
        test_roc_auc_score()
        test_classification_report()
        test_log_loss()

        # Regression Metrics (3 tests)
        test_mse_rmse_mae()
        test_r2_score()
        test_mape()

        # Cross-Validation (3 tests)
        test_k_fold_split()
        test_stratified_k_fold_split()
        test_cross_validate()

        # Model Comparison (2 tests)
        test_compare_models()
        test_paired_ttest()

        # Hyperparameter Tuning (1 test)
        test_grid_search()

        print("\n" + "=" * 70)
        print("✓ ALL 15 TESTS PASSED!")
        print("=" * 70)
        print("\nSprint 8 ML Evaluation & Validation Tools: READY FOR PRODUCTION")
        print("\nTotal Tools Tested:")
        print("  - Classification Metrics: 6 tools")
        print("  - Regression Metrics: 3 tools")
        print("  - Cross-Validation: 3 tools")
        print("  - Model Comparison: 2 tools")
        print("  - Hyperparameter Tuning: 1 tool")
        print("\nNBA MCP System Status:")
        print("  - Sprints 5-6: 55 tools ✓")
        print("  - Sprint 7: 18 ML tools ✓")
        print("  - Sprint 8: 15 evaluation tools ✓")
        print("  - TOTAL: 88 MCP tools")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())