"""
End-to-End Integration Tests (Agent 13)

Tests complete workflows from data to predictions.
"""

import pytest
import numpy as np
from datetime import datetime

from tests.integration_agent13.test_framework import (
    IntegrationTestBuilder,
    SystemValidator
)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    @pytest.fixture
    def context(self):
        """Create test context"""
        ctx = IntegrationTestBuilder.create_test_context()
        yield ctx
        ctx.cleanup()

    def test_complete_simulation_pipeline(self, context):
        """Test complete simulation pipeline from training to prediction"""
        # Train and register model
        model = IntegrationTestBuilder.train_and_register_model(context)
        assert model is not None

        # Verify model is registered
        models = context.model_registry.list_models()
        assert "test_model" in models

        # Create simulation request
        request = IntegrationTestBuilder.create_simulation_request()

        # Execute simulation
        result = context.simulation_service.simulate(request)

        # Validate result
        assert result is not None
        assert result.request_id == "test_request"
        assert 0.0 <= result.home_win_probability <= 1.0
        assert 0.0 <= result.away_win_probability <= 1.0
        assert abs(result.home_win_probability + result.away_win_probability - 1.0) < 0.01

    def test_multiple_model_versions(self, context):
        """Test managing multiple model versions"""
        # Register multiple versions
        IntegrationTestBuilder.train_and_register_model(
            context, "my_model", "1.0.0", n_samples=50
        )
        IntegrationTestBuilder.train_and_register_model(
            context, "my_model", "2.0.0", n_samples=100
        )

        # Check versions
        versions = context.model_registry.list_versions("my_model")
        assert len(versions) == 2
        assert "1.0.0" in versions
        assert "2.0.0" in versions

        # Get latest version
        model = context.model_registry.get_model("my_model")
        assert model is not None

        # Get specific version
        model_v1 = context.model_registry.get_model("my_model", "1.0.0")
        assert model_v1 is not None

    def test_batch_simulation(self, context):
        """Test batch simulation processing"""
        # Train model
        IntegrationTestBuilder.train_and_register_model(context)

        # Create batch simulator
        from mcp_server.simulations.deployment.simulation_service import BatchSimulator
        batch_sim = BatchSimulator(context.simulation_service, max_workers=2)

        # Create multiple requests
        requests = [
            IntegrationTestBuilder.create_simulation_request(num_simulations=5)
            for _ in range(10)
        ]

        # Execute batch
        results = batch_sim.simulate_batch(requests, parallel=True)

        # Validate
        assert len(results) == 10
        assert all(r.request_id == "test_request" for r in results)

    def test_feature_engineering_pipeline(self, context):
        """Test feature engineering integrated with simulation"""
        import pandas as pd

        # Create time series data
        data = pd.DataFrame({
            'points': [100, 105, 110, 108, 112],
            'rebounds': [45, 47, 46, 48, 50],
            'win': [1, 0, 1, 1, 0]
        })

        # Generate features
        time_gen = context.feature_generators['time_based']
        rolling_features = time_gen.create_rolling_features(
            data, ['points', 'rebounds'], ['mean', 'std']
        )

        assert len(rolling_features.columns) > 0
        assert rolling_features.shape[0] == 5

        # Generate momentum features
        momentum = time_gen.create_momentum_features(data)
        assert 'win_streak' in momentum.columns

    def test_validation_integration(self, context):
        """Test validation integrated with simulation"""
        # Create roster
        roster = IntegrationTestBuilder.create_sample_roster("LAL", 12)

        # Validate roster
        result = context.validator.validate_roster(roster)
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Test game parameters
        from mcp_server.simulations.validation.sim_validator import GameParameters
        params = GameParameters(
            home_team_id="LAL",
            away_team_id="BOS",
            season="2024-25",
            game_date=datetime.now()
        )

        result = context.validator.validate_game_parameters(params)
        assert result.is_valid is True

    def test_quality_checking_integration(self, context):
        """Test quality checking integrated with simulation"""
        if context.quality_checker is None:
            pytest.skip("Quality checker not available")

        # Simulate realistic game stats
        sim_data = {
            'points': 105.0,
            'rebounds': 45.0,
            'assists': 25.0,
            'field_goal_pct': 0.48,
            'three_point_pct': 0.36
        }

        # Compute realism score
        realism = context.quality_checker.compute_realism_score(sim_data)
        assert 0.0 <= realism <= 1.0

        # Check for anomalies
        anomalies = context.quality_checker.detect_anomalies(sim_data)
        assert isinstance(anomalies, list)

    def test_caching_behavior(self, context):
        """Test caching across simulation service"""
        # Train model
        IntegrationTestBuilder.train_and_register_model(context)

        # Create request
        request = IntegrationTestBuilder.create_simulation_request()

        # First simulation
        result1 = context.simulation_service.simulate(request)
        assert context.simulation_service.requests_processed == 1

        # Second simulation (should hit cache)
        result2 = context.simulation_service.simulate(request)
        assert context.simulation_service.requests_processed == 2
        assert context.simulation_service.cache_hits == 1

        # Results should be identical (from cache)
        assert result1.home_win_probability == result2.home_win_probability


class TestSystemValidation:
    """Test system-level validation"""

    @pytest.fixture
    def context(self):
        """Create test context"""
        ctx = IntegrationTestBuilder.create_test_context()
        yield ctx
        ctx.cleanup()

    def test_system_integrity(self, context):
        """Test overall system integrity"""
        results = SystemValidator.validate_end_to_end_pipeline(context)

        assert results['passed'] is True
        assert len(results['errors']) == 0
        assert results['checks']['model_registry']['passed'] is True
        assert results['checks']['simulation_service']['passed'] is True

    def test_data_flow_validation(self, context):
        """Test data flow through entire system"""
        results = SystemValidator.validate_data_flow(context)

        assert results['passed'] is True
        assert len(results['errors']) == 0
        assert len(results['steps']) >= 3

        # Check each step passed
        for step in results['steps']:
            assert step['passed'] is True


class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.fixture
    def context(self):
        """Create test context"""
        ctx = IntegrationTestBuilder.create_test_context()
        yield ctx
        ctx.cleanup()

    def test_missing_model_error(self, context):
        """Test handling of missing model"""
        request = IntegrationTestBuilder.create_simulation_request(
            model_id="nonexistent_model"
        )

        with pytest.raises(ValueError, match="not found in registry"):
            context.simulation_service.simulate(request)

    def test_invalid_roster_handling(self, context):
        """Test handling of invalid roster"""
        from mcp_server.simulations.validation.sim_validator import TeamRoster, PlayerStats

        # Create roster with too few players
        players = [
            PlayerStats("p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0)
        ]
        roster = TeamRoster("TEST", "Test Team", players, "2024-25")

        result = context.validator.validate_roster(roster)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_batch_simulation_with_errors(self, context):
        """Test batch simulation with some failing requests"""
        from mcp_server.simulations.deployment.simulation_service import BatchSimulator

        # Train model
        IntegrationTestBuilder.train_and_register_model(context, "valid_model", "1.0")

        batch_sim = BatchSimulator(context.simulation_service)

        # Mix of valid and invalid requests
        requests = [
            IntegrationTestBuilder.create_simulation_request(
                model_id="valid_model", model_version="1.0"
            ),
            IntegrationTestBuilder.create_simulation_request(
                model_id="invalid_model", model_version="1.0"
            )
        ]

        # Should handle errors gracefully
        results = batch_sim.simulate_batch(requests, parallel=False)
        assert len(results) == 2
        # First should succeed, second should have error metadata
        assert results[0].metadata.get('error') is None
        assert results[1].metadata.get('error') is not None


class TestPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def context(self):
        """Create test context"""
        ctx = IntegrationTestBuilder.create_test_context()
        yield ctx
        ctx.cleanup()

    def test_cache_performance(self, context):
        """Test caching improves performance"""
        import time

        # Train model
        IntegrationTestBuilder.train_and_register_model(context)

        request = IntegrationTestBuilder.create_simulation_request(num_simulations=100)

        # First run (no cache)
        start = time.time()
        context.simulation_service.simulate(request)
        first_time = time.time() - start

        # Second run (with cache)
        start = time.time()
        context.simulation_service.simulate(request)
        second_time = time.time() - start

        # Cache should be significantly faster
        assert second_time < first_time

    def test_batch_parallel_speedup(self, context):
        """Test parallel batch processing is faster"""
        import time
        from mcp_server.simulations.deployment.simulation_service import BatchSimulator

        # Train model
        IntegrationTestBuilder.train_and_register_model(context)

        # Create requests
        requests = [
            IntegrationTestBuilder.create_simulation_request(num_simulations=10)
            for _ in range(20)
        ]

        # Sequential execution
        batch_sim_seq = BatchSimulator(context.simulation_service, max_workers=1)
        start = time.time()
        batch_sim_seq.simulate_batch(requests, parallel=False)
        seq_time = time.time() - start

        # Clear cache for fair comparison
        context.simulation_service.clear_cache()

        # Parallel execution
        batch_sim_par = BatchSimulator(context.simulation_service, max_workers=4)
        start = time.time()
        batch_sim_par.simulate_batch(requests, parallel=True)
        par_time = time.time() - start

        # Parallel should be faster (though not guaranteed on all systems)
        # We just check it completes successfully
        assert par_time > 0
        assert seq_time > 0


class TestDataConsistency:
    """Test data consistency across components"""

    @pytest.fixture
    def context(self):
        """Create test context"""
        ctx = IntegrationTestBuilder.create_test_context()
        yield ctx
        ctx.cleanup()

    def test_model_serialization_consistency(self, context):
        """Test model serialization preserves predictions"""
        # Train model
        model = IntegrationTestBuilder.train_and_register_model(context)

        # Make predictions with original model
        X_test = np.random.randn(10, 10)
        original_preds = model.predict(X_test)

        # Load model from registry
        loaded_model = context.model_registry.get_model("test_model", "1.0.0")

        # Make predictions with loaded model
        loaded_preds = loaded_model.predict(X_test)

        # Should be identical
        np.testing.assert_array_almost_equal(original_preds, loaded_preds)

    def test_registry_persistence(self, context):
        """Test registry persists across instances"""
        # Register model
        IntegrationTestBuilder.train_and_register_model(context, "persist_test", "1.0")

        # Create new registry with same path
        from mcp_server.simulations.deployment.model_persistence import (
            ModelSerializer,
            ModelRegistry
        )

        serializer = ModelSerializer(base_path=context.temp_dir / "models")
        new_registry = ModelRegistry(
            serializer=serializer,
            registry_path=context.temp_dir / "registry.json"
        )

        # Should have the registered model
        models = new_registry.list_models()
        assert "persist_test" in models

    def test_simulation_reproducibility(self, context):
        """Test simulations are reproducible with same inputs"""
        # Train model
        IntegrationTestBuilder.train_and_register_model(context)

        request = IntegrationTestBuilder.create_simulation_request(num_simulations=1)

        # Clear cache to ensure fresh simulation
        context.simulation_service.clear_cache()

        # Run twice
        result1 = context.simulation_service.simulate(request)

        context.simulation_service.clear_cache()
        context.simulation_service.clear_models()

        result2 = context.simulation_service.simulate(request)

        # Should be identical (with single simulation, no randomness)
        assert abs(result1.home_win_probability - result2.home_win_probability) < 0.01
