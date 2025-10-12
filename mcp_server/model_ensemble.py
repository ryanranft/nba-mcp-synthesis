"""
Model Ensemble Module
Combine multiple models for improved predictions.
"""

import logging
from typing import Dict, Optional, Any, List, Callable
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """Combine multiple models"""

    def __init__(self):
        """Initialize ensemble predictor"""
        self.models: Dict[str, Dict] = {}

    def add_model(
        self,
        model_id: str,
        predict_fn: Callable,
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ):
        """
        Add model to ensemble.

        Args:
            model_id: Model identifier
            predict_fn: Prediction function
            weight: Model weight
            metadata: Model metadata
        """
        self.models[model_id] = {
            "predict_fn": predict_fn,
            "weight": weight,
            "metadata": metadata or {}
        }

        logger.info(f"Added model {model_id} with weight {weight}")

    def predict_voting(
        self,
        inputs: Any,
        voting_type: str = "hard"
    ) -> Dict[str, Any]:
        """
        Voting ensemble prediction.

        Args:
            inputs: Model inputs
            voting_type: "hard" (majority) or "soft" (weighted average)

        Returns:
            Ensemble prediction
        """
        predictions = {}

        for model_id, model_info in self.models.items():
            pred = model_info["predict_fn"](inputs)
            predictions[model_id] = {
                "prediction": pred,
                "weight": model_info["weight"]
            }

        if voting_type == "hard":
            # Majority vote
            votes = [p["prediction"] for p in predictions.values()]
            final_pred = max(set(votes), key=votes.count)
        else:
            # Weighted average
            weighted_sum = sum(
                p["prediction"] * p["weight"]
                for p in predictions.values()
            )
            total_weight = sum(p["weight"] for p in predictions.values())
            final_pred = weighted_sum / total_weight if total_weight > 0 else 0

        return {
            "ensemble_prediction": final_pred,
            "individual_predictions": {
                k: v["prediction"] for k, v in predictions.items()
            },
            "voting_type": voting_type,
            "num_models": len(self.models)
        }

    def predict_stacking(
        self,
        inputs: Any,
        meta_learner_fn: Callable
    ) -> Dict[str, Any]:
        """
        Stacking ensemble prediction.

        Args:
            inputs: Model inputs
            meta_learner_fn: Meta-learner function

        Returns:
            Stacked prediction
        """
        # Get base model predictions
        base_predictions = []
        for model_id, model_info in self.models.items():
            pred = model_info["predict_fn"](inputs)
            base_predictions.append(pred)

        # Meta-learner combines base predictions
        final_pred = meta_learner_fn(base_predictions)

        return {
            "ensemble_prediction": final_pred,
            "base_predictions": base_predictions,
            "method": "stacking",
            "num_models": len(self.models)
        }

    def predict_boosting_style(
        self,
        inputs: Any
    ) -> Dict[str, Any]:
        """
        Boosting-style sequential prediction.

        Args:
            inputs: Model inputs

        Returns:
            Boosted prediction
        """
        predictions = []
        weights = []

        for model_id, model_info in self.models.items():
            pred = model_info["predict_fn"](inputs)
            predictions.append(pred)
            weights.append(model_info["weight"])

        # Weighted combination
        final_pred = sum(p * w for p, w in zip(predictions, weights)) / sum(weights)

        return {
            "ensemble_prediction": final_pred,
            "individual_predictions": predictions,
            "weights": weights,
            "method": "boosting_style"
        }

    def get_ensemble_stats(self) -> Dict[str, Any]:
        """Get ensemble statistics"""
        return {
            "num_models": len(self.models),
            "models": list(self.models.keys()),
            "total_weight": sum(m["weight"] for m in self.models.values()),
            "avg_weight": statistics.mean(m["weight"] for m in self.models.values()) if self.models else 0
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL ENSEMBLE DEMO")
    print("=" * 80)

    # Mock models
    def model_a(inputs):
        return sum(inputs) * 0.1

    def model_b(inputs):
        return sum(inputs) * 0.12

    def model_c(inputs):
        return sum(inputs) * 0.08

    # Create ensemble
    print("\n" + "=" * 80)
    print("CREATING ENSEMBLE")
    print("=" * 80)

    ensemble = EnsemblePredictor()
    ensemble.add_model("random_forest", model_a, weight=1.0, metadata={"accuracy": 0.85})
    ensemble.add_model("gradient_boost", model_b, weight=1.2, metadata={"accuracy": 0.88})
    ensemble.add_model("neural_net", model_c, weight=0.8, metadata={"accuracy": 0.82})

    print(f"✅ Created ensemble with {len(ensemble.models)} models")

    # Test inputs
    test_inputs = [10, 5, 8, 12]

    # Voting ensemble
    print("\n" + "=" * 80)
    print("VOTING ENSEMBLE (Soft)")
    print("=" * 80)

    result_voting = ensemble.predict_voting(test_inputs, voting_type="soft")
    print(f"\nInputs: {test_inputs}")
    print(f"Ensemble Prediction: {result_voting['ensemble_prediction']:.3f}")
    print(f"Individual Predictions:")
    for model, pred in result_voting['individual_predictions'].items():
        print(f"  {model}: {pred:.3f}")

    # Boosting style
    print("\n" + "=" * 80)
    print("BOOSTING-STYLE ENSEMBLE")
    print("=" * 80)

    result_boosting = ensemble.predict_boosting_style(test_inputs)
    print(f"\nEnsemble Prediction: {result_boosting['ensemble_prediction']:.3f}")
    print(f"Weights: {result_boosting['weights']}")

    # Stacking
    print("\n" + "=" * 80)
    print("STACKING ENSEMBLE")
    print("=" * 80)

    def meta_learner(base_preds):
        # Simple average as meta-learner
        return sum(base_preds) / len(base_preds)

    result_stacking = ensemble.predict_stacking(test_inputs, meta_learner)
    print(f"\nEnsemble Prediction: {result_stacking['ensemble_prediction']:.3f}")
    print(f"Base Predictions: {[f'{p:.3f}' for p in result_stacking['base_predictions']]}")

    # Ensemble stats
    print("\n" + "=" * 80)
    print("ENSEMBLE STATISTICS")
    print("=" * 80)

    stats = ensemble.get_ensemble_stats()
    print(f"\nNumber of Models: {stats['num_models']}")
    print(f"Total Weight: {stats['total_weight']:.2f}")
    print(f"Average Weight: {stats['avg_weight']:.2f}")

    print("\n" + "=" * 80)
    print("Model Ensemble Demo Complete!")
    print("=" * 80)

