"""Model Registry - BOOK RECOMMENDATION 9 & IMPORTANT"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_id: str
    name: str
    version: str
    stage: str  # development, staging, production, archived
    framework: str  # sklearn, pytorch, tensorflow, etc.
    created_at: datetime
    created_by: str
    description: str
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    updated_at: Optional[datetime] = None
    promoted_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None


class ModelRegistry:
    """Central registry for all models"""

    def __init__(self):
        self.models: Dict[str, ModelMetadata] = {}
        self.version_history: Dict[str, List[ModelMetadata]] = {}

    def register(
        self,
        name: str,
        version: str,
        framework: str,
        created_by: str,
        description: str,
        stage: str = "development",
        tags: Optional[List[str]] = None,
        metrics: Optional[Dict[str, float]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        artifacts: Optional[Dict[str, str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        Register a new model

        Args:
            name: Model name
            version: Model version
            framework: ML framework used
            created_by: Creator identifier
            description: Model description
            stage: Deployment stage
            tags: Optional tags
            metrics: Model metrics
            hyperparameters: Model hyperparameters
            artifacts: Artifact locations
            dependencies: Package dependencies

        Returns:
            Model ID
        """
        model_id = f"{name}_{version}_{int(datetime.utcnow().timestamp())}"

        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version,
            stage=stage,
            framework=framework,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=description,
            tags=tags or [],
            metrics=metrics or {},
            hyperparameters=hyperparameters or {},
            artifacts=artifacts or {},
            dependencies=dependencies or []
        )

        self.models[model_id] = metadata

        # Add to version history
        if name not in self.version_history:
            self.version_history[name] = []
        self.version_history[name].append(metadata)

        logger.info(f"✅ Registered model: {name} v{version} (ID: {model_id})")

        # Persist to database
        self._persist_metadata(metadata)

        return model_id

    def get(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        return self.models.get(model_id)

    def get_by_name_version(self, name: str, version: str) -> Optional[ModelMetadata]:
        """Get model by name and version"""
        versions = self.version_history.get(name, [])
        for metadata in versions:
            if metadata.version == version:
                return metadata
        return None

    def get_latest(self, name: str, stage: Optional[str] = None) -> Optional[ModelMetadata]:
        """
        Get latest model version

        Args:
            name: Model name
            stage: Optional stage filter

        Returns:
            Latest model metadata
        """
        versions = self.version_history.get(name, [])

        if stage:
            versions = [v for v in versions if v.stage == stage]

        if not versions:
            return None

        return max(versions, key=lambda v: v.created_at)

    def list_models(
        self,
        name: Optional[str] = None,
        stage: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModelMetadata]:
        """
        List models with optional filters

        Args:
            name: Filter by name
            stage: Filter by stage
            tags: Filter by tags

        Returns:
            List of model metadata
        """
        models = list(self.models.values())

        if name:
            models = [m for m in models if m.name == name]

        if stage:
            models = [m for m in models if m.stage == stage]

        if tags:
            models = [
                m for m in models
                if all(tag in m.tags for tag in tags)
            ]

        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def update_stage(self, model_id: str, new_stage: str) -> bool:
        """
        Update model stage

        Args:
            model_id: Model ID
            new_stage: New stage

        Returns:
            Success status
        """
        if model_id not in self.models:
            logger.error(f"❌ Model {model_id} not found")
            return False

        metadata = self.models[model_id]
        old_stage = metadata.stage
        metadata.stage = new_stage
        metadata.updated_at = datetime.utcnow()

        if new_stage == "production":
            metadata.promoted_at = datetime.utcnow()

            # Demote other production models of same name
            for other_id, other_metadata in self.models.items():
                if (other_id != model_id and
                    other_metadata.name == metadata.name and
                    other_metadata.stage == "production"):
                    other_metadata.stage = "archived"
                    logger.info(f"📦 Archived previous production model: {other_id}")

        logger.info(f"✅ Updated {model_id} stage: {old_stage} → {new_stage}")

        # Persist change
        self._persist_metadata(metadata)

        # Send notification
        if new_stage == "production":
            from mcp_server.alerting import alert, AlertSeverity
            alert(
                f"Model Promoted to Production",
                f"{metadata.name} v{metadata.version} is now in production",
                AlertSeverity.INFO
            )

        return True

    def update_metrics(self, model_id: str, metrics: Dict[str, float]) -> bool:
        """Update model metrics"""
        if model_id not in self.models:
            return False

        self.models[model_id].metrics.update(metrics)
        self.models[model_id].updated_at = datetime.utcnow()

        self._persist_metadata(self.models[model_id])

        return True

    def add_tag(self, model_id: str, tag: str) -> bool:
        """Add a tag to model"""
        if model_id not in self.models:
            return False

        if tag not in self.models[model_id].tags:
            self.models[model_id].tags.append(tag)
            self.models[model_id].updated_at = datetime.utcnow()
            self._persist_metadata(self.models[model_id])

        return True

    def deprecate(self, model_id: str, reason: str = "") -> bool:
        """
        Deprecate a model

        Args:
            model_id: Model ID
            reason: Deprecation reason

        Returns:
            Success status
        """
        if model_id not in self.models:
            return False

        metadata = self.models[model_id]
        metadata.stage = "deprecated"
        metadata.deprecated_at = datetime.utcnow()
        metadata.metadata["deprecation_reason"] = reason

        logger.warning(f"⚠️  Deprecated model: {model_id} - {reason}")

        self._persist_metadata(metadata)

        return True

    def compare_models(
        self,
        model_id1: str,
        model_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two models

        Args:
            model_id1: First model ID
            model_id2: Second model ID

        Returns:
            Comparison results
        """
        if model_id1 not in self.models or model_id2 not in self.models:
            return {"error": "One or both models not found"}

        model1 = self.models[model_id1]
        model2 = self.models[model_id2]

        comparison = {
            "model1": {
                "id": model_id1,
                "name": model1.name,
                "version": model1.version,
                "stage": model1.stage,
                "metrics": model1.metrics,
                "created_at": model1.created_at.isoformat()
            },
            "model2": {
                "id": model_id2,
                "name": model2.name,
                "version": model2.version,
                "stage": model2.stage,
                "metrics": model2.metrics,
                "created_at": model2.created_at.isoformat()
            },
            "metric_differences": {}
        }

        # Calculate metric differences
        common_metrics = set(model1.metrics.keys()) & set(model2.metrics.keys())

        for metric in common_metrics:
            val1 = model1.metrics[metric]
            val2 = model2.metrics[metric]
            diff = val2 - val1
            pct_change = (diff / val1 * 100) if val1 != 0 else 0

            comparison["metric_differences"][metric] = {
                "model1_value": val1,
                "model2_value": val2,
                "absolute_diff": diff,
                "percent_change": pct_change,
                "winner": model_id2 if val2 > val1 else model_id1
            }

        return comparison

    def get_lineage(self, model_id: str) -> List[str]:
        """
        Get model lineage (parent models)

        Args:
            model_id: Model ID

        Returns:
            List of parent model IDs
        """
        if model_id not in self.models:
            return []

        metadata = self.models[model_id]

        # In production, this would track actual lineage
        # For now, return models of same name with earlier timestamps
        lineage = []

        for other_id, other_metadata in self.models.items():
            if (other_metadata.name == metadata.name and
                other_metadata.created_at < metadata.created_at):
                lineage.append(other_id)

        return sorted(lineage, key=lambda x: self.models[x].created_at)

    def _persist_metadata(self, metadata: ModelMetadata):
        """Persist metadata to database"""
        from mcp_server.database import get_database_engine
        from sqlalchemy import text

        try:
            engine = get_database_engine()

            query = text("""
                INSERT INTO model_registry (
                    model_id, name, version, stage, framework,
                    created_at, created_by, description, tags,
                    metrics, hyperparameters, artifacts, dependencies,
                    updated_at, promoted_at, deprecated_at
                ) VALUES (
                    :model_id, :name, :version, :stage, :framework,
                    :created_at, :created_by, :description, :tags,
                    :metrics, :hyperparameters, :artifacts, :dependencies,
                    :updated_at, :promoted_at, :deprecated_at
                )
                ON CONFLICT (model_id) DO UPDATE SET
                    stage = EXCLUDED.stage,
                    metrics = EXCLUDED.metrics,
                    updated_at = EXCLUDED.updated_at,
                    promoted_at = EXCLUDED.promoted_at,
                    deprecated_at = EXCLUDED.deprecated_at
            """)

            with engine.begin() as conn:
                conn.execute(query, {
                    "model_id": metadata.model_id,
                    "name": metadata.name,
                    "version": metadata.version,
                    "stage": metadata.stage,
                    "framework": metadata.framework,
                    "created_at": metadata.created_at,
                    "created_by": metadata.created_by,
                    "description": metadata.description,
                    "tags": json.dumps(metadata.tags),
                    "metrics": json.dumps(metadata.metrics),
                    "hyperparameters": json.dumps(metadata.hyperparameters),
                    "artifacts": json.dumps(metadata.artifacts),
                    "dependencies": json.dumps(metadata.dependencies),
                    "updated_at": metadata.updated_at,
                    "promoted_at": metadata.promoted_at,
                    "deprecated_at": metadata.deprecated_at
                })
        except Exception as e:
            logger.error(f"❌ Failed to persist metadata: {e}")

    def generate_catalog(self) -> str:
        """Generate human-readable model catalog"""
        catalog = f"""
📚 MODEL REGISTRY CATALOG
{'='*60}

Total Models: {len(self.models)}
Unique Names: {len(self.version_history)}

"""

        # Group by stage
        by_stage = {}
        for metadata in self.models.values():
            if metadata.stage not in by_stage:
                by_stage[metadata.stage] = []
            by_stage[metadata.stage].append(metadata)

        for stage in ["production", "staging", "development", "archived", "deprecated"]:
            if stage not in by_stage:
                continue

            models = by_stage[stage]
            catalog += f"\n{stage.upper()} ({len(models)} models):\n"
            catalog += "─" * 60 + "\n"

            for metadata in sorted(models, key=lambda m: m.created_at, reverse=True):
                catalog += f"\n📦 {metadata.name} v{metadata.version}\n"
                catalog += f"   ID: {metadata.model_id}\n"
                catalog += f"   Framework: {metadata.framework}\n"
                catalog += f"   Created: {metadata.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                catalog += f"   By: {metadata.created_by}\n"

                if metadata.metrics:
                    catalog += "   Metrics:\n"
                    for metric, value in list(metadata.metrics.items())[:3]:
                        catalog += f"   - {metric}: {value:.4f}\n"

                if metadata.tags:
                    catalog += f"   Tags: {', '.join(metadata.tags)}\n"

        catalog += "\n" + "="*60 + "\n"

        return catalog


# Global model registry
_model_registry = None


def get_model_registry() -> ModelRegistry:
    """Get global model registry"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


# Example usage
if __name__ == "__main__":
    registry = ModelRegistry()

    # Register a model
    model_id = registry.register(
        name="nba_win_predictor",
        version="1.0.0",
        framework="sklearn",
        created_by="data_scientist_1",
        description="Random Forest classifier for NBA game outcome prediction",
        tags=["classification", "nba", "games"],
        metrics={"accuracy": 0.82, "f1_score": 0.80},
        hyperparameters={"n_estimators": 100, "max_depth": 10}
    )

    # Promote to production
    registry.update_stage(model_id, "production")

    # Generate catalog
    catalog = registry.generate_catalog()
    print(catalog)

