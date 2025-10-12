"""
Prediction Logging & Storage Module
Logs all predictions for auditing, debugging, and model improvement.
"""

import logging
import json
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PredictionLog:
    """Single prediction log entry"""
    prediction_id: str
    model_id: str
    model_version: str
    inputs: Any
    prediction: Any
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class PredictionLogger:
    """Logs predictions to storage for analysis and debugging"""
    
    def __init__(self, storage_path: str = "./prediction_logs"):
        """
        Initialize prediction logger.
        
        Args:
            storage_path: Directory path for storing prediction logs
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer (flush periodically)
        self.buffer: List[PredictionLog] = []
        self.buffer_size = 100
        
        # Statistics
        self.stats = {
            "total_predictions": 0,
            "predictions_by_model": {},
            "predictions_by_hour": {}
        }
    
    def log_prediction(
        self,
        prediction_id: str,
        model_id: str,
        model_version: str,
        inputs: Any,
        prediction: Any,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> PredictionLog:
        """
        Log a prediction.
        
        Args:
            prediction_id: Unique prediction identifier
            model_id: Model identifier
            model_version: Model version
            inputs: Model inputs
            prediction: Prediction result
            confidence: Prediction confidence score
            latency_ms: Prediction latency
            user_id: User who requested prediction
            session_id: Session identifier
            metadata: Additional metadata
            
        Returns:
            PredictionLog entry
        """
        log_entry = PredictionLog(
            prediction_id=prediction_id,
            model_id=model_id,
            model_version=model_version,
            inputs=inputs,
            prediction=prediction,
            confidence=confidence,
            latency_ms=latency_ms,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.buffer.append(log_entry)
        
        # Update statistics
        self.stats["total_predictions"] += 1
        self.stats["predictions_by_model"][model_id] = \
            self.stats["predictions_by_model"].get(model_id, 0) + 1
        
        hour = datetime.utcnow().strftime("%Y-%m-%d %H:00")
        self.stats["predictions_by_hour"][hour] = \
            self.stats["predictions_by_hour"].get(hour, 0) + 1
        
        # Flush buffer if full
        if len(self.buffer) >= self.buffer_size:
            self.flush()
        
        logger.debug(f"Logged prediction {prediction_id} for model {model_id}")
        return log_entry
    
    def flush(self):
        """Flush buffered predictions to storage"""
        if not self.buffer:
            return
        
        # Create filename based on current date
        date_str = datetime.utcnow().strftime("%Y%m%d")
        log_file = self.storage_path / f"predictions_{date_str}.jsonl"
        
        # Append to JSONL file
        with open(log_file, 'a') as f:
            for log_entry in self.buffer:
                json_line = json.dumps(asdict(log_entry))
                f.write(json_line + '\n')
        
        logger.info(f"Flushed {len(self.buffer)} predictions to {log_file}")
        self.buffer.clear()
    
    def query_predictions(
        self,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[PredictionLog]:
        """
        Query prediction logs.
        
        Args:
            model_id: Filter by model ID
            user_id: Filter by user ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum number of results
            
        Returns:
            List of matching PredictionLog entries
        """
        results = []
        
        # Iterate through log files
        for log_file in sorted(self.storage_path.glob("predictions_*.jsonl")):
            with open(log_file, 'r') as f:
                for line in f:
                    if len(results) >= limit:
                        break
                    
                    entry_dict = json.loads(line)
                    entry = PredictionLog(**entry_dict)
                    
                    # Apply filters
                    if model_id and entry.model_id != model_id:
                        continue
                    if user_id and entry.user_id != user_id:
                        continue
                    if start_date and entry.timestamp < start_date:
                        continue
                    if end_date and entry.timestamp > end_date:
                        continue
                    
                    results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get prediction logging statistics"""
        return {
            "total_predictions": self.stats["total_predictions"],
            "predictions_by_model": self.stats["predictions_by_model"],
            "predictions_by_hour": dict(sorted(
                self.stats["predictions_by_hour"].items(),
                reverse=True
            )[:24]),  # Last 24 hours
            "buffer_size": len(self.buffer),
            "storage_path": str(self.storage_path)
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("PREDICTION LOGGING & STORAGE DEMO")
    print("=" * 80)
    
    pred_logger = PredictionLogger(storage_path="./demo_prediction_logs")
    
    # Simulate logging predictions
    print("\n" + "=" * 80)
    print("LOGGING PREDICTIONS")
    print("=" * 80)
    
    import random
    
    for i in range(150):  # Log 150 predictions (will trigger flush)
        pred_logger.log_prediction(
            prediction_id=f"pred_{i:04d}",
            model_id=random.choice(["model_v1", "model_v2"]),
            model_version="1.0.0",
            inputs=[random.randint(0, 100) for _ in range(5)],
            prediction=random.choice([True, False]),
            confidence=random.uniform(0.6, 0.99),
            latency_ms=random.uniform(10, 100),
            user_id=f"user_{random.randint(1, 10)}",
            session_id=f"session_{random.randint(1, 20)}",
            metadata={"source": "api", "region": "us-east-1"}
        )
    
    print(f"\n✅ Logged {pred_logger.stats['total_predictions']} predictions")
    
    # Show statistics
    print("\n" + "=" * 80)
    print("LOGGING STATISTICS")
    print("=" * 80)
    
    stats = pred_logger.get_statistics()
    print(f"\nTotal Predictions: {stats['total_predictions']}")
    print(f"Storage Path: {stats['storage_path']}")
    print(f"Buffer Size: {stats['buffer_size']}")
    
    print("\nPredictions by Model:")
    for model, count in stats['predictions_by_model'].items():
        print(f"  - {model}: {count}")
    
    print("\nPredictions by Hour (last 24h):")
    for hour, count in list(stats['predictions_by_hour'].items())[:5]:
        print(f"  - {hour}: {count}")
    
    # Flush remaining
    pred_logger.flush()
    
    # Query predictions
    print("\n" + "=" * 80)
    print("QUERYING PREDICTIONS")
    print("=" * 80)
    
    results = pred_logger.query_predictions(model_id="model_v1", limit=5)
    print(f"\nFound {len(results)} predictions for model_v1 (showing 5):")
    for result in results:
        print(f"  - {result.prediction_id}: prediction={result.prediction}, "
              f"confidence={result.confidence:.2f}, latency={result.latency_ms:.1f}ms")
    
    print("\n" + "=" * 80)
    print("Prediction Logging Demo Complete!")
    print("=" * 80)

