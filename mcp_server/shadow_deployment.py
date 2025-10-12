"""Shadow Deployment - BOOK RECOMMENDATION 10 & IMPORTANT"""
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
import time

logger = logging.getLogger(__name__)


@dataclass
class ShadowModel:
    """Shadow model configuration"""
    name: str
    version: str
    model: Any
    predict_func: Callable
    sample_rate: float = 1.0  # Fraction of requests to send to shadow
    metrics: Dict[str, List[float]] = field(default_factory=lambda: {
        "latency": [],
        "predictions": [],
        "errors": []
    })
    start_time: datetime = field(default_factory=datetime.utcnow)


class ShadowDeployment:
    """Shadow deployment manager"""

    def __init__(self):
        self.production_model: Optional[Any] = None
        self.shadow_models: Dict[str, ShadowModel] = {}
        self.comparison_results: List[Dict] = []

    def register_production_model(self, model: Any, predict_func: Callable):
        """
        Register the production model

        Args:
            model: Production model
            predict_func: Prediction function
        """
        self.production_model = {
            "model": model,
            "predict_func": predict_func
        }

        logger.info("✅ Registered production model")

    def register_shadow_model(
        self,
        name: str,
        version: str,
        model: Any,
        predict_func: Callable,
        sample_rate: float = 1.0
    ):
        """
        Register a shadow model

        Args:
            name: Model name
            version: Model version
            model: Shadow model
            predict_func: Prediction function
            sample_rate: Fraction of requests to shadow (0-1)
        """
        shadow = ShadowModel(
            name=name,
            version=version,
            model=model,
            predict_func=predict_func,
            sample_rate=sample_rate
        )

        self.shadow_models[name] = shadow

        logger.info(f"✅ Registered shadow model: {name} v{version} (sample_rate={sample_rate})")

    def predict(self, X: Any, **kwargs) -> Dict[str, Any]:
        """
        Make prediction (production + shadow)

        Args:
            X: Input features
            **kwargs: Additional arguments

        Returns:
            Prediction results
        """
        if not self.production_model:
            raise ValueError("Production model not registered")

        # Production prediction
        prod_start = time.time()
        try:
            production_pred = self.production_model["predict_func"](
                self.production_model["model"],
                X,
                **kwargs
            )
            prod_latency = time.time() - prod_start

            result = {
                "prediction": production_pred,
                "model": "production",
                "latency": prod_latency
            }
        except Exception as e:
            logger.error(f"❌ Production model error: {e}")
            raise

        # Shadow predictions (async, don't block)
        for shadow_name, shadow in self.shadow_models.items():
            # Sample check
            import random
            if random.random() > shadow.sample_rate:
                continue

            # Run shadow prediction in background
            asyncio.create_task(
                self._run_shadow_prediction(shadow, X, production_pred, **kwargs)
            )

        return result

    async def _run_shadow_prediction(
        self,
        shadow: ShadowModel,
        X: Any,
        production_pred: Any,
        **kwargs
    ):
        """Run shadow prediction asynchronously"""
        shadow_start = time.time()

        try:
            shadow_pred = shadow.predict_func(shadow.model, X, **kwargs)
            shadow_latency = time.time() - shadow_start

            # Record metrics
            shadow.metrics["latency"].append(shadow_latency)
            shadow.metrics["predictions"].append(shadow_pred)

            # Compare with production
            comparison = {
                "timestamp": datetime.utcnow(),
                "shadow_name": shadow.name,
                "shadow_version": shadow.version,
                "production_pred": production_pred,
                "shadow_pred": shadow_pred,
                "prod_latency": 0,  # Would be passed in
                "shadow_latency": shadow_latency,
                "match": production_pred == shadow_pred
            }

            self.comparison_results.append(comparison)

            # Log disagreements
            if production_pred != shadow_pred:
                logger.warning(
                    f"⚠️  Shadow disagreement: "
                    f"prod={production_pred}, shadow={shadow_pred} ({shadow.name})"
                )

        except Exception as e:
            logger.error(f"❌ Shadow model error ({shadow.name}): {e}")
            shadow.metrics["errors"].append(str(e))

    def get_shadow_report(self, shadow_name: str) -> Dict[str, Any]:
        """
        Get shadow model performance report

        Args:
            shadow_name: Shadow model name

        Returns:
            Performance report
        """
        if shadow_name not in self.shadow_models:
            return {"error": f"Shadow model {shadow_name} not found"}

        shadow = self.shadow_models[shadow_name]

        # Get comparison results for this shadow
        shadow_comparisons = [
            c for c in self.comparison_results
            if c["shadow_name"] == shadow_name
        ]

        if not shadow_comparisons:
            return {
                "shadow_name": shadow_name,
                "status": "no_data",
                "message": "No predictions made yet"
            }

        # Calculate metrics
        total_predictions = len(shadow_comparisons)
        matches = sum(1 for c in shadow_comparisons if c["match"])
        agreement_rate = matches / total_predictions if total_predictions > 0 else 0

        avg_latency = (
            sum(shadow.metrics["latency"]) / len(shadow.metrics["latency"])
            if shadow.metrics["latency"] else 0
        )

        error_rate = (
            len(shadow.metrics["errors"]) / total_predictions
            if total_predictions > 0 else 0
        )

        # Duration
        duration = datetime.utcnow() - shadow.start_time

        report = {
            "shadow_name": shadow_name,
            "version": shadow.version,
            "status": "running",
            "duration_hours": duration.total_seconds() / 3600,
            "total_predictions": total_predictions,
            "agreement_rate": agreement_rate,
            "disagreement_rate": 1 - agreement_rate,
            "avg_latency_ms": avg_latency * 1000,
            "error_rate": error_rate,
            "sample_rate": shadow.sample_rate,
            "recommendation": self._get_recommendation(
                agreement_rate,
                error_rate,
                avg_latency
            )
        }

        return report

    def _get_recommendation(
        self,
        agreement_rate: float,
        error_rate: float,
        avg_latency: float
    ) -> Dict[str, str]:
        """Generate deployment recommendation"""
        if error_rate > 0.05:
            return {
                "action": "do_not_deploy",
                "reason": f"High error rate: {error_rate:.2%}"
            }

        if agreement_rate < 0.90:
            return {
                "action": "investigate",
                "reason": f"Low agreement rate: {agreement_rate:.2%}"
            }

        if avg_latency > 1.0:  # More than 1 second
            return {
                "action": "optimize",
                "reason": f"High latency: {avg_latency:.2f}s"
            }

        return {
            "action": "ready_to_deploy",
            "reason": "All metrics look good! ✅"
        }

    def promote_shadow_to_production(self, shadow_name: str):
        """
        Promote shadow model to production

        Args:
            shadow_name: Shadow model name
        """
        if shadow_name not in self.shadow_models:
            raise ValueError(f"Shadow model {shadow_name} not found")

        shadow = self.shadow_models[shadow_name]

        # Get report
        report = self.get_shadow_report(shadow_name)

        if report["recommendation"]["action"] != "ready_to_deploy":
            logger.warning(
                f"⚠️  Shadow model not ready: {report['recommendation']['reason']}"
            )
            raise ValueError(f"Shadow model not ready: {report['recommendation']['reason']}")

        # Promote
        old_production = self.production_model
        self.production_model = {
            "model": shadow.model,
            "predict_func": shadow.predict_func
        }

        # Remove from shadows
        del self.shadow_models[shadow_name]

        logger.info(f"🚀 Promoted shadow model {shadow_name} to production")

        # Send notification
        from mcp_server.alerting import alert, AlertSeverity
        alert(
            f"Shadow Model Promoted: {shadow_name}",
            f"Version {shadow.version} is now in production",
            AlertSeverity.INFO
        )

        return {
            "status": "promoted",
            "shadow_name": shadow_name,
            "version": shadow.version,
            "report": report
        }

    def generate_comparison_report(self) -> str:
        """Generate human-readable comparison report"""
        if not self.shadow_models:
            return "No shadow models registered"

        report = f"""
🔬 SHADOW DEPLOYMENT REPORT
{'='*60}

Production Model: Active
Shadow Models: {len(self.shadow_models)}

"""

        for shadow_name, shadow in self.shadow_models.items():
            shadow_report = self.get_shadow_report(shadow_name)

            report += f"""
📊 {shadow_name} v{shadow.version}
{'─'*60}
Duration: {shadow_report.get('duration_hours', 0):.1f} hours
Predictions: {shadow_report.get('total_predictions', 0)}
Agreement: {shadow_report.get('agreement_rate', 0):.1%}
Avg Latency: {shadow_report.get('avg_latency_ms', 0):.1f}ms
Error Rate: {shadow_report.get('error_rate', 0):.2%}

Recommendation: {shadow_report.get('recommendation', {}).get('action', 'unknown')}
Reason: {shadow_report.get('recommendation', {}).get('reason', 'N/A')}

"""

        report += f"{'='*60}\n"

        return report


# Global shadow deployment
_shadow_deployment = None


def get_shadow_deployment() -> ShadowDeployment:
    """Get global shadow deployment"""
    global _shadow_deployment
    if _shadow_deployment is None:
        _shadow_deployment = ShadowDeployment()
    return _shadow_deployment


# Example usage
if __name__ == "__main__":
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np

    # Create models
    X_train = np.random.randn(100, 5)
    y_train = (X_train[:, 0] > 0).astype(int)

    prod_model = RandomForestClassifier(n_estimators=10)
    prod_model.fit(X_train, y_train)

    shadow_model = RandomForestClassifier(n_estimators=20)
    shadow_model.fit(X_train, y_train)

    # Setup shadow deployment
    deployment = ShadowDeployment()

    deployment.register_production_model(
        prod_model,
        lambda model, X: model.predict(X)[0]
    )

    deployment.register_shadow_model(
        "improved_model",
        "v2.0",
        shadow_model,
        lambda model, X: model.predict(X)[0],
        sample_rate=1.0
    )

    # Make predictions
    for i in range(50):
        X_test = np.random.randn(1, 5)
        result = deployment.predict(X_test)
        time.sleep(0.01)  # Simulate some delay

    # Get report
    report = deployment.generate_comparison_report()
    print(report)

