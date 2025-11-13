"""
Integration Test Framework (Agent 13)

Provides utilities and fixtures for end-to-end integration testing.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from dataclasses import dataclass, field

from mcp_server.simulations.models.ensemble import EnsembleSimulator
from mcp_server.simulations.models.feature_engineering import (
    TimeBasedFeatureGenerator,
    InteractionFeatureGenerator,
    FeatureScaler,
)
from mcp_server.simulations.validation.sim_validator import (
    SimulationValidator,
    TeamRoster,
    PlayerStats,
    GameParameters,
)
from mcp_server.simulations.validation.quality_framework import SimulationQualityChecker
from mcp_server.simulations.deployment.model_persistence import (
    ModelSerializer,
    ModelRegistry,
)
from mcp_server.simulations.deployment.simulation_service import (
    SimulationService,
    SimulationRequest,
    BatchSimulator,
)


@dataclass
class IntegrationTestContext:
    """Context for integration tests with all components"""

    temp_dir: Path
    model_registry: ModelRegistry
    simulation_service: SimulationService
    validator: SimulationValidator
    quality_checker: Optional[SimulationQualityChecker] = None
    feature_generators: Dict[str, Any] = field(default_factory=dict)

    def cleanup(self):
        """Clean up test resources"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class IntegrationTestBuilder:
    """Builder for setting up integration test environments"""

    @staticmethod
    def create_test_context(
        include_historical_data: bool = True,
    ) -> IntegrationTestContext:
        """
        Create a complete test context with all components.

        Args:
            include_historical_data: Whether to include historical data

        Returns:
            IntegrationTestContext
        """
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())

        # Create model registry
        serializer = ModelSerializer(base_path=temp_dir / "models")
        registry_path = temp_dir / "registry.json"
        model_registry = ModelRegistry(
            serializer=serializer, registry_path=registry_path
        )

        # Create simulation service
        simulation_service = SimulationService(model_registry)

        # Create validator
        validator = SimulationValidator()

        # Create quality checker
        quality_checker = None
        if include_historical_data:
            historical_data = IntegrationTestBuilder.create_historical_data()
            quality_checker = SimulationQualityChecker(historical_data)

        # Create feature generators
        feature_generators = {
            "time_based": TimeBasedFeatureGenerator(windows=[3, 5]),
            "interaction": InteractionFeatureGenerator(),
            "scaler": FeatureScaler(method="standard"),
        }

        return IntegrationTestContext(
            temp_dir=temp_dir,
            model_registry=model_registry,
            simulation_service=simulation_service,
            validator=validator,
            quality_checker=quality_checker,
            feature_generators=feature_generators,
        )

    @staticmethod
    def create_historical_data(n_games: int = 100) -> pd.DataFrame:
        """
        Create synthetic historical game data.

        Args:
            n_games: Number of games to generate

        Returns:
            DataFrame with historical game data
        """
        np.random.seed(42)
        return pd.DataFrame(
            {
                "points": np.random.normal(105, 10, n_games),
                "rebounds": np.random.normal(45, 5, n_games),
                "assists": np.random.normal(25, 4, n_games),
                "field_goal_pct": np.random.uniform(0.40, 0.55, n_games),
                "three_point_pct": np.random.uniform(0.30, 0.40, n_games),
                "turnovers": np.random.normal(15, 3, n_games),
            }
        )

    @staticmethod
    def create_sample_roster(team_id: str = "TEST", n_players: int = 12) -> TeamRoster:
        """
        Create a sample team roster.

        Args:
            team_id: Team identifier
            n_players: Number of players

        Returns:
            TeamRoster object
        """
        players = []
        for i in range(n_players):
            player = PlayerStats(
                player_id=f"player_{i:02d}",
                points=np.random.uniform(5, 25),
                assists=np.random.uniform(1, 8),
                rebounds=np.random.uniform(2, 10),
                steals=np.random.uniform(0.5, 2),
                blocks=np.random.uniform(0.2, 2),
                turnovers=np.random.uniform(1, 3),
                minutes=np.random.uniform(15, 35),
                field_goal_pct=np.random.uniform(0.40, 0.55),
                three_point_pct=np.random.uniform(0.30, 0.40),
                free_throw_pct=np.random.uniform(0.70, 0.90),
            )
            players.append(player)

        return TeamRoster(
            team_id=team_id,
            team_name=f"Team {team_id}",
            players=players,
            season="2024-25",
        )

    @staticmethod
    def train_and_register_model(
        context: IntegrationTestContext,
        model_id: str = "test_model",
        version: str = "1.0.0",
        n_features: int = 10,
        n_samples: int = 100,
    ) -> Any:
        """
        Train and register a model in the context.

        Args:
            context: Integration test context
            model_id: Model identifier
            version: Model version
            n_features: Number of features
            n_samples: Number of training samples

        Returns:
            Trained model
        """
        # Generate training data
        np.random.seed(42)
        X = np.random.randn(n_samples, n_features)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(n_samples) * 0.5

        # Train model
        model = LinearRegression()
        model.fit(X, y)

        # Register model
        context.model_registry.register_model(
            model,
            model_id,
            version,
            "linear_regression",
            metrics={"mse": 0.25, "r2": 0.95},
            metadata={"n_features": n_features, "n_samples": n_samples},
        )

        return model

    @staticmethod
    def create_simulation_request(
        model_id: str = "test_model",
        model_version: str = "1.0.0",
        num_simulations: int = 10,
    ) -> SimulationRequest:
        """
        Create a simulation request.

        Args:
            model_id: Model identifier
            model_version: Model version
            num_simulations: Number of simulations

        Returns:
            SimulationRequest object
        """
        return SimulationRequest(
            request_id="test_request",
            home_team_id="HOME",
            away_team_id="AWAY",
            home_features={f"feat_{i}": float(i) for i in range(5)},
            away_features={f"feat_{i}": float(i + 5) for i in range(5)},
            model_id=model_id,
            model_version=model_version,
            num_simulations=num_simulations,
        )


class SystemValidator:
    """
    Validate entire system integrity and correctness.

    Performs comprehensive checks across all components.
    """

    @staticmethod
    def validate_end_to_end_pipeline(context: IntegrationTestContext) -> Dict[str, Any]:
        """
        Validate complete end-to-end pipeline.

        Args:
            context: Integration test context

        Returns:
            Validation results
        """
        results = {"passed": True, "checks": {}, "errors": []}

        # Check 1: Model registry is functional
        try:
            models = context.model_registry.list_models()
            results["checks"]["model_registry"] = {
                "passed": True,
                "models_count": len(models),
            }
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Model registry check failed: {e}")
            results["checks"]["model_registry"] = {"passed": False}

        # Check 2: Simulation service is functional
        try:
            stats = context.simulation_service.get_statistics()
            results["checks"]["simulation_service"] = {"passed": True, "stats": stats}
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Simulation service check failed: {e}")
            results["checks"]["simulation_service"] = {"passed": False}

        # Check 3: Validator is functional
        try:
            roster = IntegrationTestBuilder.create_sample_roster()
            validation_result = context.validator.validate_roster(roster)
            results["checks"]["validator"] = {
                "passed": validation_result.is_valid,
                "errors": validation_result.errors,
            }
            if not validation_result.is_valid:
                results["passed"] = False
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Validator check failed: {e}")
            results["checks"]["validator"] = {"passed": False}

        # Check 4: Feature generators are functional
        try:
            data = pd.DataFrame({"points": [100, 105, 110], "rebounds": [45, 47, 46]})
            time_gen = context.feature_generators["time_based"]
            features = time_gen.create_rolling_features(data, ["points"])
            results["checks"]["feature_generators"] = {
                "passed": len(features.columns) > 0,
                "features_count": len(features.columns),
            }
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Feature generator check failed: {e}")
            results["checks"]["feature_generators"] = {"passed": False}

        return results

    @staticmethod
    def validate_data_flow(context: IntegrationTestContext) -> Dict[str, Any]:
        """
        Validate data flow through the system.

        Args:
            context: Integration test context

        Returns:
            Validation results
        """
        results = {"passed": True, "steps": [], "errors": []}

        try:
            # Step 1: Train and register model
            model = IntegrationTestBuilder.train_and_register_model(context)
            results["steps"].append(
                {"step": "train_model", "passed": model is not None}
            )

            # Step 2: Create simulation request
            request = IntegrationTestBuilder.create_simulation_request()
            results["steps"].append(
                {"step": "create_request", "passed": request is not None}
            )

            # Step 3: Execute simulation
            result = context.simulation_service.simulate(request)
            results["steps"].append(
                {
                    "step": "execute_simulation",
                    "passed": result is not None,
                    "home_win_prob": result.home_win_probability,
                }
            )

            # Step 4: Validate results
            if context.quality_checker:
                simulated_data = {
                    "points": result.expected_home_score,
                    "rebounds": 45.0,
                }
                quality = context.quality_checker.compute_realism_score(simulated_data)
                results["steps"].append(
                    {
                        "step": "quality_check",
                        "passed": 0.0 <= quality <= 1.0,
                        "quality_score": quality,
                    }
                )

        except Exception as e:
            results["passed"] = False
            results["errors"].append(str(e))

        # Check if all steps passed
        if not all(step["passed"] for step in results["steps"]):
            results["passed"] = False

        return results
