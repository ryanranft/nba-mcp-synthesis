"""
Unit Tests for Simulation Service (Agent 12, Module 2)

Tests simulation requests, results, service, and batch processing.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
from unittest.mock import Mock, MagicMock

from mcp_server.simulations.deployment.simulation_service import (
    SimulationRequest,
    SimulationResult,
    SimulationService,
    BatchSimulator
)
from mcp_server.simulations.deployment.model_persistence import (
    ModelSerializer,
    ModelRegistry
)


class TestSimulationRequest:
    """Test SimulationRequest dataclass"""

    def test_request_creation(self):
        """Test creating simulation request"""
        request = SimulationRequest(
            request_id="req_001",
            home_team_id="LAL",
            away_team_id="BOS",
            home_features={'points': 110.5, 'rebounds': 45.0},
            away_features={'points': 105.0, 'rebounds': 42.0},
            model_id="test_model",
            num_simulations=100
        )
        assert request.request_id == "req_001"
        assert request.home_team_id == "LAL"
        assert request.num_simulations == 100

    def test_to_dict(self):
        """Test converting request to dictionary"""
        request = SimulationRequest(
            request_id="req_001",
            home_team_id="LAL",
            away_team_id="BOS",
            home_features={'points': 110.5},
            away_features={'points': 105.0},
            model_id="test_model"
        )
        data = request.to_dict()
        assert isinstance(data, dict)
        assert data['request_id'] == "req_001"
        assert isinstance(data['created_at'], str)

    def test_from_dict(self):
        """Test creating request from dictionary"""
        data = {
            'request_id': 'req_001',
            'home_team_id': 'LAL',
            'away_team_id': 'BOS',
            'home_features': {'points': 110.5},
            'away_features': {'points': 105.0},
            'model_id': 'test_model',
            'model_version': None,
            'num_simulations': 1,
            'metadata': {},
            'created_at': datetime.now().isoformat()
        }
        request = SimulationRequest.from_dict(data)
        assert request.request_id == 'req_001'
        assert isinstance(request.created_at, datetime)

    def test_get_hash(self):
        """Test getting request hash"""
        request = SimulationRequest(
            request_id="req_001",
            home_team_id="LAL",
            away_team_id="BOS",
            home_features={},
            away_features={},
            model_id="test"
        )
        hash1 = request.get_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hex digest

        # Same parameters should produce same hash
        request2 = SimulationRequest(
            request_id="req_002",  # Different ID
            home_team_id="LAL",
            away_team_id="BOS",
            home_features={},
            away_features={},
            model_id="test"
        )
        hash2 = request2.get_hash()
        assert hash1 == hash2


class TestSimulationResult:
    """Test SimulationResult dataclass"""

    def test_result_creation(self):
        """Test creating simulation result"""
        result = SimulationResult(
            request_id="req_001",
            home_win_probability=0.65,
            away_win_probability=0.35,
            expected_home_score=108.5,
            expected_away_score=102.3,
            predictions=[5.2, 6.1, 5.8],
            simulation_count=3
        )
        assert result.request_id == "req_001"
        assert result.home_win_probability == 0.65
        assert len(result.predictions) == 3

    def test_to_dict(self):
        """Test converting result to dictionary"""
        result = SimulationResult(
            request_id="req_001",
            home_win_probability=0.65,
            away_win_probability=0.35,
            expected_home_score=108.5,
            expected_away_score=102.3
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data['home_win_probability'] == 0.65

    def test_from_dict(self):
        """Test creating result from dictionary"""
        data = {
            'request_id': 'req_001',
            'home_win_probability': 0.65,
            'away_win_probability': 0.35,
            'expected_home_score': 108.5,
            'expected_away_score': 102.3,
            'predictions': [],
            'simulation_count': 1,
            'confidence_interval_95': None,
            'metadata': {},
            'completed_at': datetime.now().isoformat()
        }
        result = SimulationResult.from_dict(data)
        assert result.request_id == 'req_001'
        assert isinstance(result.completed_at, datetime)


class TestSimulationService:
    """Test SimulationService class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_model(self):
        """Create sample sklearn model"""
        X = np.random.randn(100, 10)
        y = np.random.randn(100) * 10  # Point differential
        model = LinearRegression()
        model.fit(X, y)
        return model

    @pytest.fixture
    def registry(self, temp_dir, sample_model):
        """Create registry with sample model"""
        serializer = ModelSerializer(base_path=temp_dir)
        registry_path = temp_dir / "test_registry.json"
        registry = ModelRegistry(serializer=serializer, registry_path=registry_path)
        registry.register_model(sample_model, "test_model", "1.0", "linear")
        return registry

    @pytest.fixture
    def service(self, registry):
        """Create simulation service"""
        return SimulationService(registry)

    @pytest.fixture
    def sample_request(self):
        """Create sample simulation request"""
        return SimulationRequest(
            request_id="req_001",
            home_team_id="LAL",
            away_team_id="BOS",
            home_features={f'feat_{i}': float(i) for i in range(5)},
            away_features={f'feat_{i}': float(i+5) for i in range(5)},
            model_id="test_model",
            model_version="1.0",
            num_simulations=10
        )

    def test_service_initialization(self, service):
        """Test initializing service"""
        assert service.model_registry is not None
        assert service.cache_enabled is True
        assert service.requests_processed == 0

    def test_simulate_single(self, service, sample_request):
        """Test single simulation"""
        result = service.simulate(sample_request)
        assert isinstance(result, SimulationResult)
        assert result.request_id == "req_001"
        assert 0.0 <= result.home_win_probability <= 1.0
        assert len(result.predictions) == 10

    def test_simulate_with_confidence_interval(self, service, sample_request):
        """Test simulation with confidence interval"""
        result = service.simulate(sample_request)
        assert result.confidence_interval_95 is not None
        assert len(result.confidence_interval_95) == 2
        assert result.confidence_interval_95[0] <= result.confidence_interval_95[1]

    def test_cache_hit(self, service, sample_request):
        """Test cache hit on second request"""
        # First request
        result1 = service.simulate(sample_request)
        assert service.cache_hits == 0

        # Second identical request (should hit cache)
        result2 = service.simulate(sample_request)
        assert service.cache_hits == 1
        assert result1.request_id == result2.request_id

    def test_cache_disabled(self, registry, sample_request):
        """Test service with cache disabled"""
        service = SimulationService(registry, cache_enabled=False)
        service.simulate(sample_request)
        service.simulate(sample_request)
        assert service.cache_hits == 0

    def test_clear_cache(self, service, sample_request):
        """Test clearing cache"""
        service.simulate(sample_request)
        assert len(service.cache) > 0

        service.clear_cache()
        assert len(service.cache) == 0

    def test_clear_models(self, service, sample_request):
        """Test clearing loaded models"""
        service.simulate(sample_request)
        assert len(service.loaded_models) > 0

        service.clear_models()
        assert len(service.loaded_models) == 0

    def test_get_statistics(self, service, sample_request):
        """Test getting service statistics"""
        service.simulate(sample_request)
        service.simulate(sample_request)  # Cache hit

        stats = service.get_statistics()
        assert stats['requests_processed'] == 2
        assert stats['cache_hits'] == 1
        assert stats['cache_hit_rate'] == 0.5

    def test_model_caching(self, service, sample_request):
        """Test model caching"""
        # First simulation loads model
        service.simulate(sample_request)
        assert len(service.loaded_models) == 1

        # Second simulation reuses cached model
        service.simulate(sample_request)
        assert len(service.loaded_models) == 1


class TestBatchSimulator:
    """Test BatchSimulator class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_model(self):
        """Create sample sklearn model"""
        X = np.random.randn(100, 10)
        y = np.random.randn(100) * 10
        model = LinearRegression()
        model.fit(X, y)
        return model

    @pytest.fixture
    def service(self, temp_dir, sample_model):
        """Create simulation service"""
        serializer = ModelSerializer(base_path=temp_dir)
        registry_path = temp_dir / "batch_registry.json"
        registry = ModelRegistry(serializer=serializer, registry_path=registry_path)
        registry.register_model(sample_model, "test_model", "1.0", "linear")
        return SimulationService(registry)

    @pytest.fixture
    def batch_simulator(self, service):
        """Create batch simulator"""
        return BatchSimulator(service, max_workers=2)

    @pytest.fixture
    def sample_requests(self):
        """Create sample batch of requests"""
        return [
            SimulationRequest(
                request_id=f"req_{i:03d}",
                home_team_id="LAL",
                away_team_id="BOS",
                home_features={f'feat_{j}': float(j) for j in range(5)},
                away_features={f'feat_{j}': float(j+5) for j in range(5)},
                model_id="test_model",
                model_version="1.0",
                num_simulations=5
            )
            for i in range(10)
        ]

    def test_batch_simulator_initialization(self, batch_simulator):
        """Test initializing batch simulator"""
        assert batch_simulator.simulation_service is not None
        assert batch_simulator.max_workers == 2
        assert batch_simulator.batches_processed == 0

    def test_simulate_batch_sequential(self, batch_simulator, sample_requests):
        """Test batch simulation (sequential)"""
        results = batch_simulator.simulate_batch(sample_requests[:5], parallel=False)
        assert len(results) == 5
        assert all(isinstance(r, SimulationResult) for r in results)

    def test_simulate_batch_parallel(self, batch_simulator, sample_requests):
        """Test batch simulation (parallel)"""
        results = batch_simulator.simulate_batch(sample_requests, parallel=True)
        assert len(results) == 10
        assert all(isinstance(r, SimulationResult) for r in results)

    def test_aggregate_results(self, batch_simulator, sample_requests):
        """Test aggregating results"""
        results = batch_simulator.simulate_batch(sample_requests[:5], parallel=False)
        aggregated = batch_simulator.aggregate_results(results)

        assert 'total_simulations' in aggregated
        assert aggregated['total_simulations'] == 5
        assert 'avg_home_win_prob' in aggregated
        assert 0.0 <= aggregated['avg_home_win_prob'] <= 1.0

    def test_aggregate_empty_results(self, batch_simulator):
        """Test aggregating empty results"""
        aggregated = batch_simulator.aggregate_results([])
        assert aggregated == {}

    def test_get_statistics(self, batch_simulator, sample_requests):
        """Test getting batch simulator statistics"""
        batch_simulator.simulate_batch(sample_requests[:5], parallel=False)

        stats = batch_simulator.get_statistics()
        assert stats['batches_processed'] == 1
        assert stats['max_workers'] == 2
        assert 'service_stats' in stats
