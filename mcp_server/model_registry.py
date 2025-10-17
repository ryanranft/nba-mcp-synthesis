"""
Model Registry Module
Centralized catalog for all ML models with versioning and metadata.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelStage(Enum):
    """Model lifecycle stage"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    """Model version metadata"""

    model_id: str
    version: str
    stage: ModelStage
    created_at: datetime
    created_by: str
    framework: str  # "sklearn", "pytorch", "tensorflow", etc.
    algorithm: str
    metrics: Dict[str, float] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_dataset: Optional[str] = None
    artifact_path: Optional[str] = None
    description: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    parent_version: Optional[str] = None


class ModelRegistry:
    """Central registry for ML models"""

    def __init__(self, registry_path: str = "./model_registry"):
        """
        Initialize model registry.

        Args:
            registry_path: Path to registry storage
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        self.models: Dict[str, List[ModelVersion]] = {}
        self._load_registry()

    def _load_registry(self):
        """Load registry from disk"""
        registry_file = self.registry_path / "registry.json"
        if registry_file.exists():
            with open(registry_file, "r") as f:
                data = json.load(f)
                # Reconstruct ModelVersion objects
                for model_id, versions in data.items():
                    self.models[model_id] = [
                        ModelVersion(
                            model_id=v["model_id"],
                            version=v["version"],
                            stage=ModelStage(v["stage"]),
                            created_at=datetime.fromisoformat(v["created_at"]),
                            created_by=v["created_by"],
                            framework=v["framework"],
                            algorithm=v["algorithm"],
                            metrics=v.get("metrics", {}),
                            hyperparameters=v.get("hyperparameters", {}),
                            training_dataset=v.get("training_dataset"),
                            artifact_path=v.get("artifact_path"),
                            description=v.get("description"),
                            tags=v.get("tags", {}),
                            parent_version=v.get("parent_version"),
                        )
                        for v in versions
                    ]
            logger.info(f"Loaded {len(self.models)} models from registry")

    def _save_registry(self):
        """Save registry to disk"""
        registry_file = self.registry_path / "registry.json"
        data = {}
        for model_id, versions in self.models.items():
            data[model_id] = [
                {
                    "model_id": v.model_id,
                    "version": v.version,
                    "stage": v.stage.value,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "framework": v.framework,
                    "algorithm": v.algorithm,
                    "metrics": v.metrics,
                    "hyperparameters": v.hyperparameters,
                    "training_dataset": v.training_dataset,
                    "artifact_path": v.artifact_path,
                    "description": v.description,
                    "tags": v.tags,
                    "parent_version": v.parent_version,
                }
                for v in versions
            ]

        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved registry to {registry_file}")

    def register_model(
        self,
        model_id: str,
        version: str,
        framework: str,
        algorithm: str,
        created_by: str,
        metrics: Optional[Dict[str, float]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        training_dataset: Optional[str] = None,
        artifact_path: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        parent_version: Optional[str] = None,
        stage: ModelStage = ModelStage.DEVELOPMENT,
    ) -> ModelVersion:
        """
        Register a new model version.

        Args:
            model_id: Model identifier
            version: Model version
            framework: ML framework used
            algorithm: Algorithm name
            created_by: Creator identifier
            metrics: Model metrics
            hyperparameters: Model hyperparameters
            training_dataset: Training dataset reference
            artifact_path: Path to model artifact
            description: Model description
            tags: Custom tags
            parent_version: Parent version for lineage
            stage: Initial stage

        Returns:
            ModelVersion object
        """
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            stage=stage,
            created_at=datetime.utcnow(),
            created_by=created_by,
            framework=framework,
            algorithm=algorithm,
            metrics=metrics or {},
            hyperparameters=hyperparameters or {},
            training_dataset=training_dataset,
            artifact_path=artifact_path,
            description=description,
            tags=tags or {},
            parent_version=parent_version,
        )

        if model_id not in self.models:
            self.models[model_id] = []

        self.models[model_id].append(model_version)
        self._save_registry()

        logger.info(
            f"Registered {model_id} v{version} "
            f"(stage: {stage.value}, framework: {framework})"
        )

        return model_version

    def get_model_version(
        self, model_id: str, version: Optional[str] = None
    ) -> Optional[ModelVersion]:
        """
        Get specific model version or latest.

        Args:
            model_id: Model identifier
            version: Specific version (None for latest)

        Returns:
            ModelVersion or None
        """
        if model_id not in self.models:
            return None

        versions = self.models[model_id]
        if not versions:
            return None

        if version:
            for v in versions:
                if v.version == version:
                    return v
            return None
        else:
            # Return latest
            return sorted(versions, key=lambda v: v.created_at, reverse=True)[0]

    def get_production_model(self, model_id: str) -> Optional[ModelVersion]:
        """Get production version of a model"""
        if model_id not in self.models:
            return None

        prod_versions = [
            v for v in self.models[model_id] if v.stage == ModelStage.PRODUCTION
        ]

        if not prod_versions:
            return None

        # Return latest production version
        return sorted(prod_versions, key=lambda v: v.created_at, reverse=True)[0]

    def promote_model(self, model_id: str, version: str, to_stage: ModelStage):
        """
        Promote model to a new stage.

        Args:
            model_id: Model identifier
            version: Model version
            to_stage: Target stage
        """
        model_version = self.get_model_version(model_id, version)
        if not model_version:
            raise ValueError(f"Model {model_id} v{version} not found")

        old_stage = model_version.stage
        model_version.stage = to_stage

        self._save_registry()

        logger.info(
            f"Promoted {model_id} v{version} from {old_stage.value} to {to_stage.value}"
        )

    def search_models(
        self,
        framework: Optional[str] = None,
        stage: Optional[ModelStage] = None,
        tags: Optional[Dict[str, str]] = None,
        min_accuracy: Optional[float] = None,
    ) -> List[ModelVersion]:
        """
        Search for models by criteria.

        Args:
            framework: Filter by framework
            stage: Filter by stage
            tags: Filter by tags
            min_accuracy: Filter by minimum accuracy

        Returns:
            List of matching ModelVersion objects
        """
        results = []

        for model_id, versions in self.models.items():
            for version in versions:
                # Apply filters
                if framework and version.framework != framework:
                    continue
                if stage and version.stage != stage:
                    continue
                if tags:
                    if not all(version.tags.get(k) == v for k, v in tags.items()):
                        continue
                if min_accuracy:
                    if version.metrics.get("accuracy", 0) < min_accuracy:
                        continue

                results.append(version)

        return sorted(results, key=lambda v: v.created_at, reverse=True)

    def get_model_lineage(self, model_id: str, version: str) -> List[ModelVersion]:
        """
        Get model lineage (parent versions).

        Args:
            model_id: Model identifier
            version: Model version

        Returns:
            List of ModelVersion objects in lineage
        """
        lineage = []
        current_version = self.get_model_version(model_id, version)

        while current_version:
            lineage.append(current_version)
            if current_version.parent_version:
                current_version = self.get_model_version(
                    model_id, current_version.parent_version
                )
            else:
                break

        return lineage

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_models = len(self.models)
        total_versions = sum(len(versions) for versions in self.models.values())

        stage_counts = {stage.value: 0 for stage in ModelStage}
        framework_counts = {}

        for versions in self.models.values():
            for version in versions:
                stage_counts[version.stage.value] += 1
                framework_counts[version.framework] = (
                    framework_counts.get(version.framework, 0) + 1
                )

        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "by_stage": stage_counts,
            "by_framework": framework_counts,
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL REGISTRY DEMO")
    print("=" * 80)

    registry = ModelRegistry(registry_path="./demo_registry")

    # Register models
    print("\n" + "=" * 80)
    print("REGISTERING MODELS")
    print("=" * 80)

    registry.register_model(
        model_id="nba_win_predictor",
        version="1.0.0",
        framework="sklearn",
        algorithm="RandomForest",
        created_by="data_scientist_1",
        metrics={"accuracy": 0.85, "f1": 0.83},
        hyperparameters={"n_estimators": 100, "max_depth": 10},
        description="Initial win prediction model",
        stage=ModelStage.PRODUCTION,
    )

    registry.register_model(
        model_id="nba_win_predictor",
        version="1.1.0",
        framework="sklearn",
        algorithm="GradientBoosting",
        created_by="data_scientist_2",
        metrics={"accuracy": 0.88, "f1": 0.86},
        hyperparameters={"n_estimators": 200, "learning_rate": 0.1},
        description="Improved model with gradient boosting",
        parent_version="1.0.0",
        stage=ModelStage.STAGING,
    )

    print("✅ Registered 2 model versions")

    # Get production model
    print("\n" + "=" * 80)
    print("PRODUCTION MODEL")
    print("=" * 80)

    prod_model = registry.get_production_model("nba_win_predictor")
    print(f"\nModel: {prod_model.model_id} v{prod_model.version}")
    print(f"Algorithm: {prod_model.algorithm}")
    print(f"Metrics: {prod_model.metrics}")

    # Promote to production
    print("\n" + "=" * 80)
    print("PROMOTING MODEL")
    print("=" * 80)

    registry.promote_model("nba_win_predictor", "1.1.0", ModelStage.PRODUCTION)
    print("✅ Promoted v1.1.0 to production")

    # Search models
    print("\n" + "=" * 80)
    print("SEARCHING MODELS")
    print("=" * 80)

    results = registry.search_models(framework="sklearn", min_accuracy=0.85)
    print(f"\nFound {len(results)} models (sklearn, accuracy >= 0.85):")
    for model in results:
        print(
            f"  - {model.model_id} v{model.version}: "
            f"accuracy={model.metrics.get('accuracy', 0):.2f}"
        )

    # Registry stats
    print("\n" + "=" * 80)
    print("REGISTRY STATISTICS")
    print("=" * 80)

    stats = registry.get_registry_stats()
    print(f"\nTotal Models: {stats['total_models']}")
    print(f"Total Versions: {stats['total_versions']}")
    print(f"\nBy Stage:")
    for stage, count in stats["by_stage"].items():
        if count > 0:
            print(f"  - {stage}: {count}")
    print(f"\nBy Framework:")
    for framework, count in stats["by_framework"].items():
        print(f"  - {framework}: {count}")

    print("\n" + "=" * 80)
    print("Model Registry Demo Complete!")
    print("=" * 80)
