"""
Prediction Caching Module
Caches model predictions to reduce latency and computational costs.
"""

import logging
import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionCache:
    """In-memory prediction cache (use Redis in production)"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        """
        Initialize prediction cache.
        
        Args:
            ttl_seconds: Time-to-live for cached predictions
            max_size: Maximum number of cached predictions
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_cache_key(self, model_id: str, inputs: Any) -> str:
        """Generate cache key from model_id and inputs"""
        # Convert inputs to JSON string for hashing
        try:
            inputs_str = json.dumps(inputs, sort_keys=True)
        except (TypeError, ValueError):
            # If inputs not JSON-serializable, use str representation
            inputs_str = str(inputs)
        
        # Create hash of model_id + inputs
        key_string = f"{model_id}:{inputs_str}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, model_id: str, inputs: Any) -> Optional[Any]:
        """
        Get cached prediction.
        
        Args:
            model_id: Model identifier
            inputs: Prediction inputs
            
        Returns:
            Cached prediction or None if not found/expired
        """
        cache_key = self._generate_cache_key(model_id, inputs)
        
        with self.lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                
                # Check if expired
                created_at = datetime.fromisoformat(entry["created_at"])
                if datetime.utcnow() - created_at > timedelta(seconds=self.ttl_seconds):
                    # Expired, remove from cache
                    del self.cache[cache_key]
                    self.stats["misses"] += 1
                    return None
                
                # Valid cache hit
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT for model {model_id}")
                return entry["prediction"]
            
            # Cache miss
            self.stats["misses"] += 1
            logger.debug(f"Cache MISS for model {model_id}")
            return None
    
    def set(self, model_id: str, inputs: Any, prediction: Any, metadata: Optional[Dict] = None):
        """
        Cache a prediction.
        
        Args:
            model_id: Model identifier
            inputs: Prediction inputs
            prediction: Model prediction result
            metadata: Optional metadata (confidence, latency, etc.)
        """
        cache_key = self._generate_cache_key(model_id, inputs)
        
        with self.lock:
            # Check if cache is full
            if len(self.cache) >= self.max_size and cache_key not in self.cache:
                # Evict oldest entry (simple FIFO eviction)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats["evictions"] += 1
                logger.debug(f"Evicted cache entry (cache full)")
            
            # Store prediction
            self.cache[cache_key] = {
                "prediction": prediction,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            logger.debug(f"Cached prediction for model {model_id}")
    
    def invalidate(self, model_id: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            model_id: If provided, only invalidate entries for this model
                     If None, clear entire cache
        """
        with self.lock:
            if model_id is None:
                # Clear entire cache
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cleared entire cache ({count} entries)")
            else:
                # Clear entries for specific model
                # Note: In practice, would need to track model_id -> keys mapping
                # For now, clear entire cache when model_id specified
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cleared cache for model {model_id} ({count} entries)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "hit_rate": hit_rate
            }


class CachedModelPredictor:
    """Wrapper that adds caching to model predictions"""
    
    def __init__(self, model_id: str, model: Any, cache: PredictionCache):
        """
        Initialize cached model predictor.
        
        Args:
            model_id: Unique model identifier
            model: Model with predict() method
            cache: Prediction cache instance
        """
        self.model_id = model_id
        self.model = model
        self.cache = cache
    
    def predict(self, inputs: Any) -> Any:
        """
        Make prediction with caching.
        
        Args:
            inputs: Model inputs
            
        Returns:
            Prediction result (from cache or fresh prediction)
        """
        # Try to get from cache
        cached_prediction = self.cache.get(self.model_id, inputs)
        if cached_prediction is not None:
            return cached_prediction
        
        # Cache miss - compute prediction
        prediction = self.model.predict(inputs)
        
        # Cache the result
        self.cache.set(self.model_id, inputs, prediction)
        
        return prediction
    
    def predict_with_metadata(self, inputs: Any) -> Dict[str, Any]:
        """
        Make prediction and return with metadata (cached vs fresh).
        
        Args:
            inputs: Model inputs
            
        Returns:
            Dict with prediction and metadata
        """
        # Try to get from cache
        cached_prediction = self.cache.get(self.model_id, inputs)
        if cached_prediction is not None:
            return {
                "prediction": cached_prediction,
                "cached": True,
                "model_id": self.model_id
            }
        
        # Cache miss - compute prediction
        import time
        start_time = time.time()
        prediction = self.model.predict(inputs)
        latency_ms = (time.time() - start_time) * 1000
        
        # Cache the result
        self.cache.set(self.model_id, inputs, prediction, {"latency_ms": latency_ms})
        
        return {
            "prediction": prediction,
            "cached": False,
            "model_id": self.model_id,
            "latency_ms": latency_ms
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("PREDICTION CACHING DEMO")
    print("=" * 80)
    
    # Mock model
    class MockModel:
        def predict(self, inputs):
            import time
            time.sleep(0.1)  # Simulate model inference
            return sum(inputs) > 50  # Simple prediction
    
    model = MockModel()
    cache = PredictionCache(ttl_seconds=60, max_size=100)
    cached_predictor = CachedModelPredictor("nba_win_predictor", model, cache)
    
    # Test inputs
    test_inputs = [
        [10, 20, 30],
        [40, 50, 60],
        [10, 20, 30],  # Duplicate - should hit cache
        [40, 50, 60],  # Duplicate - should hit cache
        [70, 80, 90]
    ]
    
    print("\n" + "=" * 80)
    print("MAKING PREDICTIONS")
    print("=" * 80)
    
    for i, inputs in enumerate(test_inputs, 1):
        import time
        start = time.time()
        result = cached_predictor.predict_with_metadata(inputs)
        latency = (time.time() - start) * 1000
        
        cache_status = "🟢 CACHED" if result["cached"] else "🔴 FRESH"
        print(f"\nPrediction {i}: {inputs}")
        print(f"   Result: {result['prediction']}")
        print(f"   Status: {cache_status}")
        print(f"   Total Latency: {latency:.2f}ms")
    
    # Show cache statistics
    print("\n" + "=" * 80)
    print("CACHE STATISTICS")
    print("=" * 80)
    
    stats = cache.get_stats()
    print(f"\nCache Size: {stats['cache_size']}/{stats['max_size']}")
    print(f"TTL: {stats['ttl_seconds']}s")
    print(f"Hits: {stats['hits']}")
    print(f"Misses: {stats['misses']}")
    print(f"Evictions: {stats['evictions']}")
    print(f"Hit Rate: {stats['hit_rate']:.1f}%")
    
    # Test cache invalidation
    print("\n" + "=" * 80)
    print("CACHE INVALIDATION")
    print("=" * 80)
    
    print(f"\nBefore invalidation: {len(cache.cache)} entries")
    cache.invalidate()
    print(f"After invalidation: {len(cache.cache)} entries")
    
    print("\n" + "=" * 80)
    print("Prediction Caching Demo Complete!")
    print("=" * 80)

