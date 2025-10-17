"""Model Explainability - BOOK RECOMMENDATION 5 & IMPORTANT"""

import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP (SHapley Additive exPlanations) for model explainability"""

    def __init__(self, model: Any, background_data: Optional[np.ndarray] = None):
        """
        Initialize SHAP explainer

        Args:
            model: Trained model
            background_data: Background dataset for SHAP
        """
        self.model = model
        self.background_data = background_data
        self.explainer = None
        self._initialize_explainer()

    def _initialize_explainer(self):
        """Initialize SHAP explainer based on model type"""
        try:
            import shap

            # Auto-detect model type and create appropriate explainer
            if hasattr(self.model, "predict_proba"):
                # Tree-based models
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("✅ Using TreeExplainer")
            elif hasattr(self.model, "coef_"):
                # Linear models
                self.explainer = shap.LinearExplainer(self.model, self.background_data)
                logger.info("✅ Using LinearExplainer")
            else:
                # Deep learning or other models
                self.explainer = shap.KernelExplainer(
                    self.model.predict, self.background_data
                )
                logger.info("✅ Using KernelExplainer")
        except ImportError:
            logger.warning("⚠️  SHAP not installed - using simplified explainer")
            self.explainer = None

    def explain_prediction(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Explain a single prediction

        Args:
            X: Input features
            feature_names: Optional feature names

        Returns:
            Explanation with feature contributions
        """
        if self.explainer is None:
            return self._simple_explanation(X, feature_names)

        import shap

        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X)

        # Get prediction
        if hasattr(self.model, "predict_proba"):
            prediction = self.model.predict_proba(X)[0]
        else:
            prediction = self.model.predict(X)[0]

        # Create explanation
        if isinstance(X, pd.DataFrame):
            feature_names = X.columns.tolist()
            X_values = X.values[0]
        else:
            X_values = X[0] if len(X.shape) > 1 else X
            feature_names = feature_names or [
                f"feature_{i}" for i in range(len(X_values))
            ]

        # Get top contributing features
        if isinstance(shap_values, list):
            shap_values = shap_values[0]  # For multi-class, take first class

        contributions = list(zip(feature_names, X_values, shap_values[0]))
        contributions.sort(key=lambda x: abs(x[2]), reverse=True)

        return {
            "prediction": (
                float(prediction) if isinstance(prediction, np.ndarray) else prediction
            ),
            "top_features": [
                {
                    "feature": name,
                    "value": float(value),
                    "contribution": float(contrib),
                    "impact": "positive" if contrib > 0 else "negative",
                }
                for name, value, contrib in contributions[:10]
            ],
            "base_value": (
                float(self.explainer.expected_value)
                if hasattr(self.explainer, "expected_value")
                else 0.0
            ),
        }

    def _simple_explanation(
        self, X: Union[np.ndarray, pd.DataFrame], feature_names: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Simplified explanation when SHAP is not available"""
        if hasattr(self.model, "feature_importances_"):
            # Tree-based models
            importances = self.model.feature_importances_

            if isinstance(X, pd.DataFrame):
                feature_names = X.columns.tolist()
                X_values = X.values[0]
            else:
                X_values = X[0] if len(X.shape) > 1 else X
                feature_names = feature_names or [
                    f"feature_{i}" for i in range(len(X_values))
                ]

            contributions = list(zip(feature_names, X_values, importances))
            contributions.sort(key=lambda x: abs(x[2]), reverse=True)

            prediction = self.model.predict(X)[0]

            return {
                "prediction": (
                    float(prediction)
                    if isinstance(prediction, np.ndarray)
                    else prediction
                ),
                "top_features": [
                    {
                        "feature": name,
                        "value": float(value),
                        "importance": float(importance),
                    }
                    for name, value, importance in contributions[:10]
                ],
                "note": "Using feature importances (SHAP not available)",
            }
        elif hasattr(self.model, "coef_"):
            # Linear models
            coefficients = (
                self.model.coef_[0]
                if len(self.model.coef_.shape) > 1
                else self.model.coef_
            )

            if isinstance(X, pd.DataFrame):
                feature_names = X.columns.tolist()
                X_values = X.values[0]
            else:
                X_values = X[0] if len(X.shape) > 1 else X
                feature_names = feature_names or [
                    f"feature_{i}" for i in range(len(X_values))
                ]

            contributions = list(zip(feature_names, X_values, coefficients))
            contributions.sort(key=lambda x: abs(x[2]), reverse=True)

            prediction = self.model.predict(X)[0]

            return {
                "prediction": (
                    float(prediction)
                    if isinstance(prediction, np.ndarray)
                    else prediction
                ),
                "top_features": [
                    {
                        "feature": name,
                        "value": float(value),
                        "coefficient": float(coef),
                        "contribution": float(value * coef),
                    }
                    for name, value, coef in contributions[:10]
                ],
                "note": "Using linear coefficients (SHAP not available)",
            }
        else:
            return {
                "prediction": "unknown",
                "error": "Model explainability not supported for this model type",
            }


class FeatureImportanceAnalyzer:
    """Analyze feature importance across the model"""

    def __init__(self, model: Any):
        self.model = model

    def get_global_importance(self, feature_names: List[str]) -> pd.DataFrame:
        """
        Get global feature importance

        Args:
            feature_names: List of feature names

        Returns:
            DataFrame with feature importances
        """
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importances = np.abs(
                self.model.coef_[0]
                if len(self.model.coef_.shape) > 1
                else self.model.coef_
            )
        else:
            logger.error("❌ Model does not support feature importance")
            return pd.DataFrame()

        df = pd.DataFrame({"feature": feature_names, "importance": importances})
        df = df.sort_values("importance", ascending=False)

        return df

    def plot_importance(self, feature_names: List[str], top_n: int = 20):
        """Plot feature importance (requires matplotlib)"""
        try:
            import matplotlib.pyplot as plt

            df = self.get_global_importance(feature_names)
            df_top = df.head(top_n)

            plt.figure(figsize=(10, 8))
            plt.barh(df_top["feature"], df_top["importance"])
            plt.xlabel("Importance")
            plt.title(f"Top {top_n} Feature Importances")
            plt.tight_layout()

            return plt
        except ImportError:
            logger.warning("⚠️  matplotlib not installed - cannot plot")
            return None


class ModelExplainer:
    """High-level interface for model explainability"""

    def __init__(self, model: Any, background_data: Optional[np.ndarray] = None):
        self.model = model
        self.shap_explainer = SHAPExplainer(model, background_data)
        self.importance_analyzer = FeatureImportanceAnalyzer(model)

    def explain(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Explain prediction with all available methods

        Args:
            X: Input features
            feature_names: Optional feature names

        Returns:
            Complete explanation
        """
        explanation = self.shap_explainer.explain_prediction(X, feature_names)

        # Add global importance
        if feature_names:
            global_importance = self.importance_analyzer.get_global_importance(
                feature_names
            )
            explanation["global_feature_importance"] = global_importance.to_dict(
                "records"
            )[:10]

        return explanation

    def generate_report(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        feature_names: Optional[List[str]] = None,
    ) -> str:
        """Generate human-readable explanation report"""
        explanation = self.explain(X, feature_names)

        report = f"""
🔍 MODEL PREDICTION EXPLANATION
{'='*60}

📊 Prediction: {explanation['prediction']}

🎯 Top Contributing Features:
"""

        for i, feature in enumerate(explanation["top_features"][:5], 1):
            impact = "📈" if feature.get("impact") == "positive" else "📉"
            report += f"\n{i}. {impact} {feature['feature']}"
            report += f"\n   Value: {feature['value']:.4f}"
            if "contribution" in feature:
                report += f"\n   Contribution: {feature['contribution']:.4f}"

        report += f"\n\n{'='*60}\n"

        return report


# Example usage
if __name__ == "__main__":
    from sklearn.ensemble import RandomForestClassifier

    # Train example model
    X_train = np.random.randn(100, 5)
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)

    model = RandomForestClassifier(n_estimators=10)
    model.fit(X_train, y_train)

    # Create explainer
    explainer = ModelExplainer(model, X_train[:50])

    # Explain a prediction
    X_test = np.random.randn(1, 5)
    feature_names = ["points", "assists", "rebounds", "steals", "blocks"]

    explanation = explainer.explain(X_test, feature_names)
    print(explanation)

    # Generate report
    report = explainer.generate_report(X_test, feature_names)
    print(report)
