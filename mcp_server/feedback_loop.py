"""Feedback Loop - BOOK RECOMMENDATION 8 & IMPORTANT"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class Feedback:
    """User feedback on a prediction"""
    feedback_id: str
    model_name: str
    model_version: str
    prediction: Any
    actual_outcome: Any
    features: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    confidence_score: Optional[float] = None
    feedback_type: str = "correction"  # correction, rating, flag
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackCollector:
    """Collect and store user feedback"""
    
    def __init__(self):
        self.feedback_storage: List[Feedback] = []
        self.stats: Dict[str, Any] = {
            "total_feedback": 0,
            "by_model": {},
            "by_type": {}
        }
    
    def record_feedback(
        self,
        model_name: str,
        model_version: str,
        prediction: Any,
        actual_outcome: Any,
        features: Dict[str, Any],
        user_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        feedback_type: str = "correction",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Record user feedback
        
        Args:
            model_name: Model name
            model_version: Model version
            prediction: Model prediction
            actual_outcome: Actual outcome
            features: Input features
            user_id: Optional user identifier
            confidence_score: Optional confidence score
            feedback_type: Type of feedback
            metadata: Additional metadata
            
        Returns:
            Feedback ID
        """
        feedback_id = f"fb_{int(datetime.utcnow().timestamp() * 1000)}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            model_name=model_name,
            model_version=model_version,
            prediction=prediction,
            actual_outcome=actual_outcome,
            features=features,
            user_id=user_id,
            confidence_score=confidence_score,
            feedback_type=feedback_type,
            metadata=metadata or {}
        )
        
        self.feedback_storage.append(feedback)
        
        # Update stats
        self.stats["total_feedback"] += 1
        
        if model_name not in self.stats["by_model"]:
            self.stats["by_model"][model_name] = 0
        self.stats["by_model"][model_name] += 1
        
        if feedback_type not in self.stats["by_type"]:
            self.stats["by_type"][feedback_type] = 0
        self.stats["by_type"][feedback_type] += 1
        
        logger.info(f"✅ Recorded feedback {feedback_id} for {model_name}")
        
        # Store in database
        self._persist_feedback(feedback)
        
        # Trigger feedback analysis if threshold reached
        if self.stats["by_model"][model_name] >= 100:
            self._trigger_analysis(model_name)
        
        return feedback_id
    
    def _persist_feedback(self, feedback: Feedback):
        """Persist feedback to database"""
        from mcp_server.database import get_database_engine
        from sqlalchemy import text
        
        try:
            engine = get_database_engine()
            
            query = text("""
                INSERT INTO feedback_log (
                    feedback_id, model_name, model_version,
                    prediction, actual_outcome, features,
                    timestamp, user_id, confidence_score,
                    feedback_type, metadata
                ) VALUES (
                    :feedback_id, :model_name, :model_version,
                    :prediction, :actual_outcome, :features,
                    :timestamp, :user_id, :confidence_score,
                    :feedback_type, :metadata
                )
            """)
            
            with engine.begin() as conn:
                conn.execute(query, {
                    "feedback_id": feedback.feedback_id,
                    "model_name": feedback.model_name,
                    "model_version": feedback.model_version,
                    "prediction": json.dumps(feedback.prediction),
                    "actual_outcome": json.dumps(feedback.actual_outcome),
                    "features": json.dumps(feedback.features),
                    "timestamp": feedback.timestamp,
                    "user_id": feedback.user_id,
                    "confidence_score": feedback.confidence_score,
                    "feedback_type": feedback.feedback_type,
                    "metadata": json.dumps(feedback.metadata)
                })
        except Exception as e:
            logger.error(f"❌ Failed to persist feedback: {e}")
    
    def _trigger_analysis(self, model_name: str):
        """Trigger feedback analysis"""
        logger.info(f"🔍 Triggering feedback analysis for {model_name}")
        
        # This would trigger the FeedbackAnalyzer
        # For now, just log
        analyzer = get_feedback_analyzer()
        analyzer.analyze_model_feedback(model_name)
    
    def get_feedback_summary(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get feedback summary"""
        if model_name:
            feedback_list = [f for f in self.feedback_storage if f.model_name == model_name]
        else:
            feedback_list = self.feedback_storage
        
        if not feedback_list:
            return {"message": "No feedback available"}
        
        # Calculate accuracy based on feedback
        correct = sum(1 for f in feedback_list if f.prediction == f.actual_outcome)
        total = len(feedback_list)
        
        return {
            "total_feedback": total,
            "correct_predictions": correct,
            "accuracy": correct / total if total > 0 else 0,
            "feedback_by_type": {
                feedback_type: sum(1 for f in feedback_list if f.feedback_type == feedback_type)
                for feedback_type in set(f.feedback_type for f in feedback_list)
            }
        }


class FeedbackAnalyzer:
    """Analyze feedback and extract insights"""
    
    def __init__(self):
        self.collector = get_feedback_collector()
    
    def analyze_model_feedback(self, model_name: str) -> Dict[str, Any]:
        """
        Analyze feedback for a model
        
        Args:
            model_name: Model name
            
        Returns:
            Analysis results
        """
        feedback_list = [f for f in self.collector.feedback_storage if f.model_name == model_name]
        
        if not feedback_list:
            return {"error": "No feedback available"}
        
        analysis = {
            "model_name": model_name,
            "total_feedback": len(feedback_list),
            "accuracy_metrics": self._calculate_accuracy(feedback_list),
            "error_patterns": self._identify_error_patterns(feedback_list),
            "feature_importance": self._analyze_feature_importance(feedback_list),
            "recommendations": []
        }
        
        # Generate recommendations
        if analysis["accuracy_metrics"]["accuracy"] < 0.80:
            analysis["recommendations"].append({
                "priority": "high",
                "type": "retrain",
                "message": "Model accuracy below 80% - retraining recommended"
            })
        
        if len(analysis["error_patterns"]) > 0:
            analysis["recommendations"].append({
                "priority": "medium",
                "type": "investigate",
                "message": f"Found {len(analysis['error_patterns'])} error patterns to investigate"
            })
        
        logger.info(f"📊 Analyzed {len(feedback_list)} feedback items for {model_name}")
        
        return analysis
    
    def _calculate_accuracy(self, feedback_list: List[Feedback]) -> Dict[str, float]:
        """Calculate accuracy metrics from feedback"""
        total = len(feedback_list)
        correct = sum(1 for f in feedback_list if f.prediction == f.actual_outcome)
        
        # For classification
        if isinstance(feedback_list[0].prediction, (int, bool, str)):
            from sklearn.metrics import precision_score, recall_score, f1_score
            
            predictions = [f.prediction for f in feedback_list]
            actuals = [f.actual_outcome for f in feedback_list]
            
            return {
                "accuracy": correct / total if total > 0 else 0,
                "precision": float(precision_score(actuals, predictions, average='weighted', zero_division=0)),
                "recall": float(recall_score(actuals, predictions, average='weighted', zero_division=0)),
                "f1_score": float(f1_score(actuals, predictions, average='weighted', zero_division=0))
            }
        else:
            # For regression
            import numpy as np
            
            predictions = [f.prediction for f in feedback_list]
            actuals = [f.actual_outcome for f in feedback_list]
            
            mae = np.mean(np.abs(np.array(predictions) - np.array(actuals)))
            rmse = np.sqrt(np.mean((np.array(predictions) - np.array(actuals))**2))
            
            return {
                "mae": float(mae),
                "rmse": float(rmse)
            }
    
    def _identify_error_patterns(self, feedback_list: List[Feedback]) -> List[Dict]:
        """Identify common error patterns"""
        errors = [f for f in feedback_list if f.prediction != f.actual_outcome]
        
        if not errors:
            return []
        
        patterns = []
        
        # Group errors by common feature values
        feature_error_counts = {}
        
        for error in errors:
            for feature_name, feature_value in error.features.items():
                key = f"{feature_name}={feature_value}"
                if key not in feature_error_counts:
                    feature_error_counts[key] = 0
                feature_error_counts[key] += 1
        
        # Identify patterns where errors occur frequently
        total_errors = len(errors)
        
        for key, count in feature_error_counts.items():
            if count / total_errors > 0.2:  # More than 20% of errors
                patterns.append({
                    "pattern": key,
                    "error_count": count,
                    "error_rate": count / total_errors
                })
        
        patterns.sort(key=lambda x: x["error_count"], reverse=True)
        
        return patterns[:10]  # Top 10 patterns
    
    def _analyze_feature_importance(self, feedback_list: List[Feedback]) -> Dict[str, float]:
        """Analyze which features are most associated with errors"""
        errors = [f for f in feedback_list if f.prediction != f.actual_outcome]
        correct = [f for f in feedback_list if f.prediction == f.actual_outcome]
        
        if not errors or not correct:
            return {}
        
        # Calculate correlation between features and errors
        importance = {}
        
        # This is a simplified version
        # In production, would use more sophisticated analysis
        
        return importance


class FeedbackLoop:
    """Complete feedback loop system"""
    
    def __init__(self):
        self.collector = get_feedback_collector()
        self.analyzer = get_feedback_analyzer()
    
    def record_and_analyze(
        self,
        model_name: str,
        model_version: str,
        prediction: Any,
        actual_outcome: Any,
        features: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Record feedback and trigger analysis if needed"""
        # Record feedback
        feedback_id = self.collector.record_feedback(
            model_name=model_name,
            model_version=model_version,
            prediction=prediction,
            actual_outcome=actual_outcome,
            features=features,
            **kwargs
        )
        
        # Get summary
        summary = self.collector.get_feedback_summary(model_name)
        
        # Check if analysis should be triggered
        if summary["total_feedback"] % 100 == 0:
            analysis = self.analyzer.analyze_model_feedback(model_name)
            
            return {
                "feedback_id": feedback_id,
                "summary": summary,
                "analysis": analysis
            }
        
        return {
            "feedback_id": feedback_id,
            "summary": summary
        }


# Global instances
_feedback_collector = None
_feedback_analyzer = None
_feedback_loop = None


def get_feedback_collector() -> FeedbackCollector:
    """Get global feedback collector"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """Get global feedback analyzer"""
    global _feedback_analyzer
    if _feedback_analyzer is None:
        _feedback_analyzer = FeedbackAnalyzer()
    return _feedback_analyzer


def get_feedback_loop() -> FeedbackLoop:
    """Get global feedback loop"""
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = FeedbackLoop()
    return _feedback_loop


# Example usage
if __name__ == "__main__":
    feedback_loop = FeedbackLoop()
    
    # Simulate some feedback
    for i in range(50):
        prediction = 1 if i % 3 != 0 else 0
        actual = 1 if i % 4 != 0 else 0
        
        result = feedback_loop.record_and_analyze(
            model_name="nba_win_predictor",
            model_version="v1.0",
            prediction=prediction,
            actual_outcome=actual,
            features={"points_diff": i, "home_advantage": i % 2}
        )
        
        if "analysis" in result:
            print(f"\nAnalysis triggered at {i} feedback items:")
            print(json.dumps(result["analysis"], indent=2))

