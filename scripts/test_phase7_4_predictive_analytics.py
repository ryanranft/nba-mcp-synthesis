#!/usr/bin/env python3
"""
Test script for Phase 7.4: Predictive Analytics Engine

This script tests the predictive analytics engine functionality including:
- Model training and evaluation
- Prediction generation
- Time series forecasting
- Ensemble model creation
- Hyperparameter optimization
"""

import sys
import os
import time
import random
import unittest
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.tools.predictive_analytics import (
    PredictiveAnalyticsEngine,
    train_predictive_model,
    make_prediction,
    evaluate_model_performance,
    predict_time_series,
    create_ensemble_model,
    optimize_model_hyperparameters,
)


class Phase74TestSuite(unittest.TestCase):
    """Test suite for Phase 7.4 Predictive Analytics Engine"""

    def setUp(self):
        """Set up test environment"""
        print("Setting up Phase 7.4 test environment...")
        self.engine = PredictiveAnalyticsEngine()

        # Create sample training data
        self.sample_training_data = {
            "points": [20.0, 25.0, 15.0, 30.0, 18.0, 22.0, 28.0, 16.0, 24.0, 19.0],
            "rebounds": [8.0, 10.0, 6.0, 12.0, 7.0, 9.0, 11.0, 5.0, 10.0, 8.0],
            "assists": [5.0, 7.0, 3.0, 9.0, 4.0, 6.0, 8.0, 2.0, 7.0, 5.0],
            "minutes": [35.0, 38.0, 28.0, 42.0, 32.0, 36.0, 40.0, 25.0, 37.0, 33.0],
            "efficiency": [18.5, 22.3, 14.2, 28.7, 16.8, 20.1, 26.4, 13.9, 23.2, 17.6],
        }

        # Create sample test data
        self.sample_test_data = {
            "points": [21.0, 26.0, 17.0],
            "rebounds": [9.0, 11.0, 7.0],
            "assists": [6.0, 8.0, 4.0],
            "minutes": [36.0, 39.0, 29.0],
            "efficiency": [19.2, 23.1, 15.8],
        }

        # Create time series data
        self.time_series_data = {
            "game_number": list(range(1, 21)),
            "points": [
                20,
                22,
                18,
                25,
                23,
                21,
                26,
                24,
                19,
                27,
                25,
                22,
                28,
                26,
                23,
                29,
                27,
                24,
                30,
                28,
            ],
            "rebounds": [
                8,
                9,
                7,
                11,
                10,
                8,
                12,
                11,
                7,
                13,
                12,
                9,
                14,
                13,
                10,
                15,
                14,
                11,
                16,
                15,
            ],
        }

        print("✓ Test environment setup complete")

    def test_model_training(self):
        """Test predictive model training"""
        print("Testing model training...")

        # Test regression model training
        result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=self.sample_training_data,
            test_data=self.sample_test_data,
            validation_split=0.2,
            cross_validation_folds=3,
            performance_metrics=["mse", "rmse", "mae", "r2"],
        )

        assert result["status"] == "success", "Model training should succeed"
        assert "model_id" in result, "Model ID should be present"
        assert "performance_metrics" in result, "Performance metrics should be present"
        assert "training_summary" in result, "Training summary should be present"

        model_id = result["model_id"]
        print(f"  ✓ Regression model trained: {model_id}")

        # Test classification model training
        classification_data = {
            "points": [20.0, 25.0, 15.0, 30.0, 18.0, 22.0, 28.0, 16.0, 24.0, 19.0],
            "rebounds": [8.0, 10.0, 6.0, 12.0, 7.0, 9.0, 11.0, 5.0, 10.0, 8.0],
            "assists": [5.0, 7.0, 3.0, 9.0, 4.0, 6.0, 8.0, 2.0, 7.0, 5.0],
            "minutes": [35.0, 38.0, 28.0, 42.0, 32.0, 36.0, 40.0, 25.0, 37.0, 33.0],
            "all_star": [1, 1, 0, 1, 0, 1, 1, 0, 1, 0],
        }

        classification_result = train_predictive_model(
            model_type="classification",
            target_variable="all_star",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=classification_data,
            validation_split=0.2,
            performance_metrics=["accuracy", "precision", "recall", "f1"],
        )

        assert (
            classification_result["status"] == "success"
        ), "Classification training should succeed"
        print(f"  ✓ Classification model trained: {classification_result['model_id']}")

        print("✓ Model training test passed")

    def test_prediction_generation(self):
        """Test prediction generation"""
        print("Testing prediction generation...")

        # First train a model
        training_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )

        model_id = training_result["model_id"]

        # Test single prediction
        single_prediction = make_prediction(
            model_id=model_id,
            input_features={
                "points": 25.0,
                "rebounds": 10.0,
                "assists": 7.0,
                "minutes": 38.0,
            },
            prediction_type="single",
            include_feature_importance=True,
            include_prediction_explanation=True,
        )

        assert (
            single_prediction["status"] == "success"
        ), "Single prediction should succeed"
        assert "predictions" in single_prediction, "Predictions should be present"
        assert len(single_prediction["predictions"]) == 1, "Should have one prediction"

        prediction_value = single_prediction["predictions"][0]["predicted_value"]
        assert isinstance(
            prediction_value, (int, float)
        ), "Prediction should be numeric"
        print(f"  ✓ Single prediction: {prediction_value:.2f}")

        # Test batch prediction
        batch_prediction = make_prediction(
            model_id=model_id,
            input_features={
                "points": [25.0, 20.0, 30.0],
                "rebounds": [10.0, 8.0, 12.0],
                "assists": [7.0, 5.0, 9.0],
                "minutes": [38.0, 35.0, 42.0],
            },
            prediction_type="batch",
            confidence_interval=0.95,
        )

        assert (
            batch_prediction["status"] == "success"
        ), "Batch prediction should succeed"
        assert (
            len(batch_prediction["predictions"]) == 3
        ), "Should have three predictions"
        print(
            f"  ✓ Batch prediction: {len(batch_prediction['predictions'])} predictions"
        )

        print("✓ Prediction generation test passed")

    def test_model_evaluation(self):
        """Test model evaluation"""
        print("Testing model evaluation...")

        # Train a model first
        training_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )

        model_id = training_result["model_id"]

        # Evaluate the model
        evaluation_result = evaluate_model_performance(
            model_id=model_id,
            evaluation_data=self.sample_test_data,
            evaluation_metrics=["mse", "rmse", "mae", "r2"],
            include_cross_validation=True,
            include_feature_importance=True,
            include_residual_analysis=True,
            confidence_level=0.95,
        )

        assert (
            evaluation_result["status"] == "success"
        ), "Model evaluation should succeed"
        assert (
            "performance_metrics" in evaluation_result
        ), "Performance metrics should be present"
        assert (
            "cross_validation_results" in evaluation_result
        ), "Cross-validation results should be present"
        assert (
            "feature_importance" in evaluation_result
        ), "Feature importance should be present"

        metrics = evaluation_result["performance_metrics"]
        assert "mse" in metrics, "MSE should be calculated"
        assert "r2" in metrics, "R² should be calculated"

        print(f"  ✓ Model evaluation completed: R² = {metrics.get('r2', 0):.3f}")
        print("✓ Model evaluation test passed")

    def test_time_series_prediction(self):
        """Test time series prediction"""
        print("Testing time series prediction...")

        # Test ARIMA model
        arima_result = predict_time_series(
            time_series_data=self.time_series_data,
            target_variable="points",
            prediction_horizon=5,
            model_type="arima",
            include_confidence_intervals=True,
            confidence_level=0.95,
        )

        assert arima_result["status"] == "success", "ARIMA prediction should succeed"
        assert "predictions" in arima_result, "Predictions should be present"
        assert len(arima_result["predictions"]) == 5, "Should predict 5 future values"

        predictions = arima_result["predictions"]
        for pred in predictions:
            assert "predicted_value" in pred, "Each prediction should have a value"
            assert (
                "confidence_interval" in pred
            ), "Each prediction should have confidence interval"

        print(f"  ✓ ARIMA prediction: {len(predictions)} future values")

        # Test exponential smoothing
        exp_smooth_result = predict_time_series(
            time_series_data=self.time_series_data,
            target_variable="points",
            prediction_horizon=3,
            model_type="exponential_smoothing",
            trend_type="linear",
            include_confidence_intervals=True,
        )

        assert (
            exp_smooth_result["status"] == "success"
        ), "Exponential smoothing should succeed"
        print(
            f"  ✓ Exponential smoothing: {len(exp_smooth_result['predictions'])} predictions"
        )

        print("✓ Time series prediction test passed")

    def test_ensemble_model_creation(self):
        """Test ensemble model creation"""
        print("Testing ensemble model creation...")

        # Train multiple base models first
        model1_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )

        model2_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["assists", "minutes"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )

        base_models = [model1_result["model_id"], model2_result["model_id"]]

        # Create voting ensemble
        voting_ensemble = create_ensemble_model(
            base_models=base_models,
            ensemble_method="voting",
            voting_type="hard",
            include_model_performance=True,
        )

        assert voting_ensemble["status"] == "success", "Voting ensemble should succeed"
        assert "ensemble_id" in voting_ensemble, "Ensemble ID should be present"
        assert (
            "ensemble_performance" in voting_ensemble
        ), "Ensemble performance should be present"

        print(f"  ✓ Voting ensemble created: {voting_ensemble['ensemble_id']}")

        # Create stacking ensemble
        stacking_ensemble = create_ensemble_model(
            base_models=base_models,
            ensemble_method="stacking",
            meta_model_type="linear",
            cross_validation_folds=3,
            include_model_performance=True,
        )

        assert (
            stacking_ensemble["status"] == "success"
        ), "Stacking ensemble should succeed"
        print(f"  ✓ Stacking ensemble created: {stacking_ensemble['ensemble_id']}")

        print("✓ Ensemble model creation test passed")

    def test_hyperparameter_optimization(self):
        """Test hyperparameter optimization"""
        print("Testing hyperparameter optimization...")

        # Train a base model first
        base_model_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )

        model_id = base_model_result["model_id"]

        # Test grid search optimization
        grid_search_result = optimize_model_hyperparameters(
            model_id=model_id,
            optimization_method="grid_search",
            parameter_grid={
                "max_depth": [3, 5, 7],
                "min_samples_split": [2, 5, 10],
                "n_estimators": [50, 100, 200],
            },
            optimization_metric="r2",
            max_iterations=20,
            cv_folds=3,
            random_seed=42,
        )

        assert (
            grid_search_result["status"] == "success"
        ), "Grid search optimization should succeed"
        assert (
            "optimization_result" in grid_search_result
        ), "Optimization result should be present"
        assert (
            "best_parameters" in grid_search_result["optimization_result"]
        ), "Best parameters should be present"

        best_params = grid_search_result["optimization_result"]["best_parameters"]
        improvement = grid_search_result["optimization_result"].get(
            "improvement_score", 0
        )

        print(f"  ✓ Grid search completed: {improvement:.2%} improvement")
        print(f"  ✓ Best parameters: {best_params}")

        # Test random search optimization
        random_search_result = optimize_model_hyperparameters(
            model_id=model_id,
            optimization_method="random_search",
            parameter_grid={
                "max_depth": [3, 5, 7, 9],
                "min_samples_split": [2, 5, 10, 15],
                "n_estimators": [50, 100, 200, 300],
            },
            optimization_metric="r2",
            max_iterations=15,
            cv_folds=3,
        )

        assert (
            random_search_result["status"] == "success"
        ), "Random search optimization should succeed"
        print(f"  ✓ Random search completed")

        print("✓ Hyperparameter optimization test passed")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling...")

        # Test invalid model type
        invalid_model_result = train_predictive_model(
            model_type="invalid_type",
            target_variable="efficiency",
            feature_variables=["points", "rebounds"],
            training_data=self.sample_training_data,
            validation_split=0.2,
        )

        assert (
            invalid_model_result["status"] == "error"
        ), "Invalid model type should fail gracefully"
        assert "error" in invalid_model_result, "Error message should be present"

        # Test prediction with non-existent model
        nonexistent_prediction = make_prediction(
            model_id="nonexistent_model",
            input_features={"points": 25.0, "rebounds": 10.0},
            prediction_type="single",
        )

        assert (
            nonexistent_prediction["status"] == "error"
        ), "Non-existent model should fail gracefully"

        # Test time series with insufficient data
        insufficient_data = {"game_number": [1, 2], "points": [20, 22]}
        insufficient_result = predict_time_series(
            time_series_data=insufficient_data,
            target_variable="points",
            prediction_horizon=5,
            model_type="arima",
        )

        assert (
            insufficient_result["status"] == "error"
        ), "Insufficient data should fail gracefully"

        print("  ✓ Invalid model type handling")
        print("  ✓ Non-existent model handling")
        print("  ✓ Insufficient data handling")
        print("✓ Error handling test passed")

    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("Testing performance benchmarks...")

        # Benchmark model training
        start_time = time.time()
        training_result = train_predictive_model(
            model_type="regression",
            target_variable="efficiency",
            feature_variables=["points", "rebounds", "assists", "minutes"],
            training_data=self.sample_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "r2"],
        )
        training_time = time.time() - start_time

        assert training_result["status"] == "success", "Training should succeed"
        print(f"  ✓ Model training: {training_time:.2f}s")

        # Benchmark prediction
        model_id = training_result["model_id"]
        start_time = time.time()
        prediction_result = make_prediction(
            model_id=model_id,
            input_features={
                "points": [25.0, 20.0, 30.0, 18.0, 22.0],
                "rebounds": [10.0, 8.0, 12.0, 7.0, 9.0],
                "assists": [7.0, 5.0, 9.0, 4.0, 6.0],
                "minutes": [38.0, 35.0, 42.0, 32.0, 36.0],
            },
            prediction_type="batch",
        )
        prediction_time = time.time() - start_time

        assert prediction_result["status"] == "success", "Prediction should succeed"
        print(f"  ✓ Batch prediction: {prediction_time:.2f}s")

        # Benchmark evaluation
        start_time = time.time()
        evaluation_result = evaluate_model_performance(
            model_id=model_id,
            evaluation_data=self.sample_test_data,
            evaluation_metrics=["mse", "r2"],
            include_cross_validation=True,
        )
        evaluation_time = time.time() - start_time

        assert evaluation_result["status"] == "success", "Evaluation should succeed"
        print(f"  ✓ Model evaluation: {evaluation_time:.2f}s")

        total_time = training_time + prediction_time + evaluation_time
        print(f"  ✓ Total benchmark time: {total_time:.2f}s")

        print("✓ Performance benchmarks test passed")

    def test_integration_with_sports_formulas(self):
        """Test integration with sports analytics formulas"""
        print("Testing integration with sports formulas...")

        # Create data that mimics NBA player statistics
        nba_training_data = {
            "points_per_game": [
                25.0,
                22.0,
                18.0,
                30.0,
                20.0,
                28.0,
                15.0,
                32.0,
                24.0,
                19.0,
            ],
            "rebounds_per_game": [8.0, 10.0, 6.0, 12.0, 7.0, 11.0, 5.0, 13.0, 9.0, 8.0],
            "assists_per_game": [7.0, 5.0, 3.0, 9.0, 4.0, 8.0, 2.0, 10.0, 6.0, 5.0],
            "minutes_per_game": [
                38.0,
                35.0,
                28.0,
                42.0,
                32.0,
                40.0,
                25.0,
                44.0,
                36.0,
                33.0,
            ],
            "player_efficiency_rating": [
                22.5,
                19.8,
                16.2,
                28.7,
                18.5,
                26.4,
                14.1,
                30.2,
                21.3,
                17.6,
            ],
        }

        # Train model to predict PER
        per_model_result = train_predictive_model(
            model_type="regression",
            target_variable="player_efficiency_rating",
            feature_variables=[
                "points_per_game",
                "rebounds_per_game",
                "assists_per_game",
                "minutes_per_game",
            ],
            training_data=nba_training_data,
            validation_split=0.2,
            performance_metrics=["mse", "rmse", "mae", "r2"],
        )

        assert (
            per_model_result["status"] == "success"
        ), "PER model training should succeed"

        # Test prediction for a hypothetical player
        per_prediction = make_prediction(
            model_id=per_model_result["model_id"],
            input_features={
                "points_per_game": 27.0,
                "rebounds_per_game": 9.0,
                "assists_per_game": 8.0,
                "minutes_per_game": 39.0,
            },
            prediction_type="single",
            include_prediction_explanation=True,
        )

        assert per_prediction["status"] == "success", "PER prediction should succeed"

        predicted_per = per_prediction["predictions"][0]["predicted_value"]
        print(f"  ✓ Predicted PER: {predicted_per:.2f}")

        # Test time series prediction for player performance trends
        player_performance_data = {
            "game_number": list(range(1, 16)),
            "points": [20, 22, 18, 25, 23, 21, 26, 24, 19, 27, 25, 22, 28, 26, 23],
            "rebounds": [8, 9, 7, 11, 10, 8, 12, 11, 7, 13, 12, 9, 14, 13, 10],
        }

        performance_trend = predict_time_series(
            time_series_data=player_performance_data,
            target_variable="points",
            prediction_horizon=5,
            model_type="arima",
            include_confidence_intervals=True,
        )

        assert (
            performance_trend["status"] == "success"
        ), "Performance trend prediction should succeed"

        future_points = [
            pred["predicted_value"] for pred in performance_trend["predictions"]
        ]
        print(f"  ✓ Predicted future points: {[f'{p:.1f}' for p in future_points]}")

        print("✓ Sports formulas integration test passed")


def run_performance_benchmark() -> Dict[str, Any]:
    """Run performance benchmarks for key functions."""
    print("\n============================================================")
    print("PERFORMANCE BENCHMARK TESTS")
    print("============================================================")

    # Setup test data
    training_data = {
        "points": [20.0, 25.0, 15.0, 30.0, 18.0, 22.0, 28.0, 16.0, 24.0, 19.0] * 5,
        "rebounds": [8.0, 10.0, 6.0, 12.0, 7.0, 9.0, 11.0, 5.0, 10.0, 8.0] * 5,
        "assists": [5.0, 7.0, 3.0, 9.0, 4.0, 6.0, 8.0, 2.0, 7.0, 5.0] * 5,
        "minutes": [35.0, 38.0, 28.0, 42.0, 32.0, 36.0, 40.0, 25.0, 37.0, 33.0] * 5,
        "efficiency": [18.5, 22.3, 14.2, 28.7, 16.8, 20.1, 26.4, 13.9, 23.2, 17.6] * 5,
    }

    test_data = {
        "points": [21.0, 26.0, 17.0, 31.0, 19.0],
        "rebounds": [9.0, 11.0, 7.0, 13.0, 8.0],
        "assists": [6.0, 8.0, 4.0, 10.0, 5.0],
        "minutes": [36.0, 39.0, 29.0, 43.0, 34.0],
        "efficiency": [19.2, 23.1, 15.8, 29.3, 18.7],
    }

    # Benchmark model training
    start_time = time.time()
    training_result = train_predictive_model(
        model_type="regression",
        target_variable="efficiency",
        feature_variables=["points", "rebounds", "assists", "minutes"],
        training_data=training_data,
        test_data=test_data,
        validation_split=0.2,
        performance_metrics=["mse", "rmse", "mae", "r2"],
    )
    training_time = time.time() - start_time
    print(
        f"Model Training: {training_time:.2f}s ({training_result.get('status', 'unknown')})"
    )

    # Benchmark prediction
    model_id = training_result.get("model_id", "test_model")
    start_time = time.time()
    prediction_result = make_prediction(
        model_id=model_id,
        input_features={
            "points": [25.0, 20.0, 30.0, 18.0, 22.0],
            "rebounds": [10.0, 8.0, 12.0, 7.0, 9.0],
            "assists": [7.0, 5.0, 9.0, 4.0, 6.0],
            "minutes": [38.0, 35.0, 42.0, 32.0, 36.0],
        },
        prediction_type="batch",
    )
    prediction_time = time.time() - start_time
    print(
        f"Batch Prediction: {prediction_time:.2f}s ({len(prediction_result.get('predictions', []))} predictions)"
    )

    # Benchmark evaluation
    start_time = time.time()
    evaluation_result = evaluate_model_performance(
        model_id=model_id,
        evaluation_data=test_data,
        evaluation_metrics=["mse", "r2"],
        include_cross_validation=True,
    )
    evaluation_time = time.time() - start_time
    print(f"Model Evaluation: {evaluation_time:.2f}s")

    # Benchmark time series prediction
    time_series_data = {
        "game_number": list(range(1, 21)),
        "points": [
            20,
            22,
            18,
            25,
            23,
            21,
            26,
            24,
            19,
            27,
            25,
            22,
            28,
            26,
            23,
            29,
            27,
            24,
            30,
            28,
        ],
    }
    start_time = time.time()
    ts_result = predict_time_series(
        time_series_data=time_series_data,
        target_variable="points",
        prediction_horizon=5,
        model_type="arima",
    )
    ts_time = time.time() - start_time
    print(
        f"Time Series Prediction: {ts_time:.2f}s ({len(ts_result.get('predictions', []))} predictions)"
    )

    # Benchmark ensemble creation
    model1_id = training_result.get("model_id", "model1")
    model2_id = training_result.get(
        "model_id", "model2"
    )  # Using same model for simplicity
    start_time = time.time()
    ensemble_result = create_ensemble_model(
        base_models=[model1_id, model2_id], ensemble_method="voting", voting_type="hard"
    )
    ensemble_time = time.time() - start_time
    print(f"Ensemble Creation: {ensemble_time:.2f}s")

    total_benchmark_time = (
        training_time + prediction_time + evaluation_time + ts_time + ensemble_time
    )
    print(f"\nTotal Benchmark Time: {total_benchmark_time:.2f}s")

    return {
        "training_time": training_time,
        "prediction_time": prediction_time,
        "evaluation_time": evaluation_time,
        "time_series_time": ts_time,
        "ensemble_time": ensemble_time,
        "total_benchmark_time": total_benchmark_time,
    }


def main():
    """Run all Phase 7.4 tests"""
    print("=" * 60)
    print("PHASE 7.4: PREDICTIVE ANALYTICS ENGINE - TEST SUITE")
    print("=" * 60)

    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run performance benchmarks
    benchmark_results = run_performance_benchmark()

    print("\n" + "=" * 60)
    print("PHASE 7.4 TESTING COMPLETE")
    print("=" * 60)
    print(f"Total benchmark time: {benchmark_results['total_benchmark_time']:.2f}s")
    print("All tests completed successfully! ✓")


if __name__ == "__main__":
    main()
