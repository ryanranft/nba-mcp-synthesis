"""
Simulation Service Layer (Agent 12, Module 2)

Provides service layer for executing NBA game simulations at scale.

Integrates with:
- Agent 2 (Monitoring): Track simulation requests and performance
- Agent 10 (Validation): Validate requests and results
- Agent 11 (Models): Use deployed models for simulation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class SimulationRequest:
    """Request for game simulation"""
    request_id: str
    home_team_id: str
    away_team_id: str
    home_features: Dict[str, float]
    away_features: Dict[str, float]
    model_id: str
    model_version: Optional[str] = None
    num_simulations: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRequest':
        """Create from dictionary"""
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    def get_hash(self) -> str:
        """Get hash of request for caching"""
        key = f"{self.home_team_id}_{self.away_team_id}_{self.model_id}_{self.model_version}"
        return hashlib.md5(key.encode()).hexdigest()


@dataclass
class SimulationResult:
    """Result of game simulation"""
    request_id: str
    home_win_probability: float
    away_win_probability: float
    expected_home_score: float
    expected_away_score: float
    predictions: List[float] = field(default_factory=list)
    simulation_count: int = 1
    confidence_interval_95: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['completed_at'] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationResult':
        """Create from dictionary"""
        data = data.copy()
        if 'completed_at' in data:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        if 'confidence_interval_95' in data and data['confidence_interval_95']:
            data['confidence_interval_95'] = tuple(data['confidence_interval_95'])
        return cls(**data)


class SimulationService:
    """
    Service for executing game simulations.

    Features:
    - Model loading and caching
    - Request validation
    - Result caching
    - Performance monitoring
    """

    def __init__(
        self,
        model_registry: Any,
        cache_enabled: bool = True,
        cache_size: int = 100
    ):
        """
        Initialize simulation service.

        Args:
            model_registry: ModelRegistry instance
            cache_enabled: Whether to cache results
            cache_size: Maximum cache size
        """
        self.model_registry = model_registry
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size
        self.cache: Dict[str, SimulationResult] = {}
        self.loaded_models: Dict[str, Any] = {}
        self.requests_processed = 0
        self.cache_hits = 0

    def simulate(self, request: SimulationRequest) -> SimulationResult:
        """
        Execute simulation request.

        Args:
            request: SimulationRequest object

        Returns:
            SimulationResult object
        """
        # Check cache
        if self.cache_enabled:
            cache_key = request.get_hash()
            if cache_key in self.cache:
                self.cache_hits += 1
                self.requests_processed += 1
                logger.debug(f"Cache hit for request {request.request_id}")
                return self.cache[cache_key]

        # Load model
        model = self._get_model(request.model_id, request.model_version)

        # Prepare features
        features = self._prepare_features(
            request.home_features,
            request.away_features
        )

        # Run simulations
        predictions = []
        for _ in range(request.num_simulations):
            pred = model.predict(features.reshape(1, -1))[0]
            predictions.append(float(pred))

        # Compute statistics
        predictions_array = np.array(predictions)
        mean_pred = float(predictions_array.mean())
        std_pred = float(predictions_array.std())

        # Compute win probabilities (assuming prediction is point differential)
        home_win_prob = float(np.mean(predictions_array > 0))
        away_win_prob = 1.0 - home_win_prob

        # Compute expected scores (assuming mean of ~100 points per team)
        expected_home = 100.0 + mean_pred / 2
        expected_away = 100.0 - mean_pred / 2

        # Compute confidence interval
        if request.num_simulations > 1:
            ci_95 = (
                float(mean_pred - 1.96 * std_pred),
                float(mean_pred + 1.96 * std_pred)
            )
        else:
            ci_95 = None

        # Create result
        result = SimulationResult(
            request_id=request.request_id,
            home_win_probability=home_win_prob,
            away_win_probability=away_win_prob,
            expected_home_score=expected_home,
            expected_away_score=expected_away,
            predictions=predictions,
            simulation_count=request.num_simulations,
            confidence_interval_95=ci_95,
            metadata={
                'model_id': request.model_id,
                'model_version': request.model_version,
                'mean_prediction': mean_pred,
                'std_prediction': std_pred
            }
        )

        # Update cache
        if self.cache_enabled:
            self._update_cache(cache_key, result)

        self.requests_processed += 1
        return result

    def _get_model(self, model_id: str, version: Optional[str]) -> Any:
        """
        Get model from cache or registry.

        Args:
            model_id: Model identifier
            version: Model version

        Returns:
            Loaded model
        """
        cache_key = f"{model_id}_{version or 'latest'}"

        if cache_key not in self.loaded_models:
            model = self.model_registry.get_model(model_id, version)
            self.loaded_models[cache_key] = model
            logger.info(f"Loaded model {cache_key}")

        return self.loaded_models[cache_key]

    def _prepare_features(
        self,
        home_features: Dict[str, float],
        away_features: Dict[str, float]
    ) -> np.ndarray:
        """
        Prepare features for prediction.

        Args:
            home_features: Home team features
            away_features: Away team features

        Returns:
            Feature array
        """
        # Combine features (simple concatenation for now)
        all_features = []

        # Sort keys to ensure consistent ordering
        home_keys = sorted(home_features.keys())
        away_keys = sorted(away_features.keys())

        for key in home_keys:
            all_features.append(home_features[key])

        for key in away_keys:
            all_features.append(away_features[key])

        return np.array(all_features)

    def _update_cache(self, key: str, result: SimulationResult):
        """Update result cache with LRU eviction"""
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = result

    def clear_cache(self):
        """Clear result cache"""
        self.cache.clear()
        logger.info("Cleared simulation cache")

    def clear_models(self):
        """Clear loaded models"""
        self.loaded_models.clear()
        logger.info("Cleared loaded models")

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_hit_rate = (
            self.cache_hits / self.requests_processed
            if self.requests_processed > 0 else 0.0
        )

        return {
            'requests_processed': self.requests_processed,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.cache),
            'loaded_models': len(self.loaded_models)
        }


class BatchSimulator:
    """
    Execute simulations in batch with parallel processing.

    Features:
    - Parallel execution
    - Progress tracking
    - Error handling
    - Result aggregation
    """

    def __init__(
        self,
        simulation_service: SimulationService,
        max_workers: int = 4
    ):
        """
        Initialize batch simulator.

        Args:
            simulation_service: SimulationService instance
            max_workers: Maximum parallel workers
        """
        self.simulation_service = simulation_service
        self.max_workers = max_workers
        self.batches_processed = 0

    def simulate_batch(
        self,
        requests: List[SimulationRequest],
        parallel: bool = True
    ) -> List[SimulationResult]:
        """
        Execute batch of simulations.

        Args:
            requests: List of SimulationRequest objects
            parallel: Whether to execute in parallel

        Returns:
            List of SimulationResult objects
        """
        if not parallel or len(requests) == 1:
            # Sequential execution with error handling
            results = []
            for req in requests:
                try:
                    result = self.simulation_service.simulate(req)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Simulation failed for request {req.request_id}: {e}")
                    # Create error result
                    error_result = SimulationResult(
                        request_id=req.request_id,
                        home_win_probability=0.5,
                        away_win_probability=0.5,
                        expected_home_score=100.0,
                        expected_away_score=100.0,
                        metadata={'error': str(e)}
                    )
                    results.append(error_result)
        else:
            # Parallel execution
            results = self._simulate_parallel(requests)

        self.batches_processed += 1
        logger.info(f"Completed batch of {len(requests)} simulations")

        return results

    def _simulate_parallel(
        self,
        requests: List[SimulationRequest]
    ) -> List[SimulationResult]:
        """
        Execute simulations in parallel.

        Args:
            requests: List of requests

        Returns:
            List of results
        """
        results = [None] * len(requests)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(self.simulation_service.simulate, req): idx
                for idx, req in enumerate(requests)
            }

            # Collect results
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error(f"Simulation failed for request {idx}: {e}")
                    # Create error result
                    results[idx] = SimulationResult(
                        request_id=requests[idx].request_id,
                        home_win_probability=0.5,
                        away_win_probability=0.5,
                        expected_home_score=100.0,
                        expected_away_score=100.0,
                        metadata={'error': str(e)}
                    )

        return results

    def aggregate_results(
        self,
        results: List[SimulationResult]
    ) -> Dict[str, Any]:
        """
        Aggregate results across multiple simulations.

        Args:
            results: List of SimulationResult objects

        Returns:
            Aggregated statistics
        """
        if not results:
            return {}

        home_win_probs = [r.home_win_probability for r in results]
        expected_home = [r.expected_home_score for r in results]
        expected_away = [r.expected_away_score for r in results]

        return {
            'total_simulations': len(results),
            'avg_home_win_prob': float(np.mean(home_win_probs)),
            'std_home_win_prob': float(np.std(home_win_probs)),
            'avg_home_score': float(np.mean(expected_home)),
            'avg_away_score': float(np.mean(expected_away)),
            'home_wins': sum(1 for p in home_win_probs if p > 0.5),
            'away_wins': sum(1 for p in home_win_probs if p < 0.5)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get batch simulator statistics"""
        return {
            'batches_processed': self.batches_processed,
            'max_workers': self.max_workers,
            'service_stats': self.simulation_service.get_statistics()
        }
