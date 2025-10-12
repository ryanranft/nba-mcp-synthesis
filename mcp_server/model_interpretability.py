"""
Model Interpretability Module (LIME-style)
Explain individual predictions using local approximations.
"""

import logging
from typing import Dict, Optional, Any, List, Callable
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalInterpreter:
    """Local interpretable model-agnostic explanations (LIME-style)"""

    def __init__(self):
        """Initialize local interpreter"""
        pass

    def explain_prediction(
        self,
        instance: List[float],
        predict_fn: Callable,
        feature_names: List[str],
        num_samples: int = 1000,
        num_features: int = 5
    ) -> Dict[str, Any]:
        """
        Explain a prediction using local linear approximation.

        Args:
            instance: Instance to explain
            predict_fn: Prediction function
            feature_names: Feature names
            num_samples: Number of samples for approximation
            num_features: Top features to show

        Returns:
            Explanation dictionary
        """
        logger.info(f"Generating explanation for instance with {len(instance)} features")

        # Get original prediction
        original_pred = predict_fn([instance])[0]

        # Generate perturbed samples
        samples = []
        predictions = []

        for _ in range(num_samples):
            # Perturb instance
            perturbed = [
                feat + random.gauss(0, abs(feat) * 0.1)
                for feat in instance
            ]
            samples.append(perturbed)
            predictions.append(predict_fn([perturbed])[0])

        # Fit local linear model
        feature_importance = self._fit_local_model(
            instance, samples, predictions, feature_names
        )

        # Get top features
        top_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:num_features]

        explanation = {
            "instance": instance,
            "prediction": original_pred,
            "feature_importance": dict(top_features),
            "num_samples": num_samples,
            "interpretation": self._generate_interpretation(top_features, original_pred)
        }

        logger.info(f"Generated explanation with {len(top_features)} top features")

        return explanation

    def _fit_local_model(
        self,
        instance: List[float],
        samples: List[List[float]],
        predictions: List[float],
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Fit local linear model"""
        # Simplified linear regression using correlations
        feature_importance = {}

        for i, name in enumerate(feature_names):
            # Calculate feature variation vs prediction variation
            feature_values = [sample[i] - instance[i] for sample in samples]
            pred_values = [pred - predictions[0] for pred in predictions]

            # Simple correlation as importance
            if len(feature_values) > 1:
                correlation = self._correlation(feature_values, pred_values)
                feature_importance[name] = correlation
            else:
                feature_importance[name] = 0.0

        return feature_importance

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) == 0:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _generate_interpretation(
        self,
        top_features: List[tuple],
        prediction: float
    ) -> str:
        """Generate human-readable interpretation"""
        positive = [f for f, imp in top_features if imp > 0]
        negative = [f for f, imp in top_features if imp < 0]

        interpretation = f"Prediction: {prediction:.3f}\n\n"

        if positive:
            interpretation += f"Positive contributions: {', '.join(positive)}\n"
        if negative:
            interpretation += f"Negative contributions: {', '.join(negative)}\n"

        return interpretation


class CounterfactualGenerator:
    """Generate counterfactual explanations"""

    def generate_counterfactual(
        self,
        instance: List[float],
        predict_fn: Callable,
        target_class: Any,
        feature_names: List[str],
        max_changes: int = 3,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Generate counterfactual explanation.

        Args:
            instance: Original instance
            predict_fn: Prediction function
            target_class: Desired prediction
            feature_names: Feature names
            max_changes: Maximum features to change
            max_iterations: Maximum iterations

        Returns:
            Counterfactual explanation
        """
        logger.info(f"Generating counterfactual for target class: {target_class}")

        best_counterfactual = None
        best_distance = float('inf')

        for _ in range(max_iterations):
            # Random feature changes
            counterfactual = instance.copy()
            changed_features = random.sample(range(len(instance)), min(max_changes, len(instance)))

            for idx in changed_features:
                # Perturb feature
                counterfactual[idx] = instance[idx] * random.uniform(0.8, 1.2)

            # Check prediction
            pred = predict_fn([counterfactual])[0]

            if abs(pred - target_class) < 0.1:  # Close enough
                # Calculate distance
                distance = sum((a - b) ** 2 for a, b in zip(instance, counterfactual)) ** 0.5

                if distance < best_distance:
                    best_distance = distance
                    best_counterfactual = counterfactual

        if best_counterfactual:
            changes = [
                {
                    "feature": feature_names[i],
                    "original": instance[i],
                    "counterfactual": best_counterfactual[i],
                    "change": best_counterfactual[i] - instance[i]
                }
                for i in range(len(instance))
                if abs(best_counterfactual[i] - instance[i]) > 0.01
            ]

            return {
                "found": True,
                "counterfactual": best_counterfactual,
                "changes": changes,
                "distance": best_distance,
                "interpretation": f"To achieve {target_class}, change: " +
                                ", ".join(f"{c['feature']} by {c['change']:.2f}" for c in changes[:3])
            }
        else:
            return {
                "found": False,
                "message": f"Could not find counterfactual for target {target_class}"
            }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL INTERPRETABILITY DEMO")
    print("=" * 80)

    # Mock prediction function
    def mock_predict(instances):
        """Mock model: predict based on weighted sum"""
        predictions = []
        for inst in instances:
            # Weighted sum of features
            score = sum(v * w for v, w in zip(inst, [0.5, 0.3, -0.2, 0.4]))
            predictions.append(score)
        return predictions

    # Test instance
    instance = [10.0, 5.0, 3.0, 8.0]
    feature_names = ["Points", "Assists", "Turnovers", "Rebounds"]

    # Local Interpretation
    print("\n" + "=" * 80)
    print("LOCAL INTERPRETATION (LIME-style)")
    print("=" * 80)

    interpreter = LocalInterpreter()
    explanation = interpreter.explain_prediction(
        instance=instance,
        predict_fn=mock_predict,
        feature_names=feature_names,
        num_samples=500,
        num_features=4
    )

    print(f"\nOriginal Instance: {dict(zip(feature_names, instance))}")
    print(f"Prediction: {explanation['prediction']:.3f}")
    print(f"\nFeature Importance:")
    for feat, imp in explanation['feature_importance'].items():
        sign = "+" if imp > 0 else ""
        print(f"  {feat:15} {sign}{imp:.3f}")

    print(f"\n{explanation['interpretation']}")

    # Counterfactual
    print("\n" + "=" * 80)
    print("COUNTERFACTUAL EXPLANATION")
    print("=" * 80)

    cf_gen = CounterfactualGenerator()
    cf = cf_gen.generate_counterfactual(
        instance=instance,
        predict_fn=mock_predict,
        target_class=10.0,
        feature_names=feature_names,
        max_changes=2,
        max_iterations=200
    )

    if cf['found']:
        print(f"\n✅ Found counterfactual!")
        print(f"Distance: {cf['distance']:.2f}")
        print(f"\nChanges needed:")
        for change in cf['changes']:
            print(f"  {change['feature']:15} {change['original']:.2f} → "
                  f"{change['counterfactual']:.2f} ({change['change']:+.2f})")
        print(f"\n{cf['interpretation']}")
    else:
        print(f"\n❌ {cf['message']}")

    print("\n" + "=" * 80)
    print("Model Interpretability Demo Complete!")
    print("=" * 80)

