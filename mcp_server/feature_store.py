"""
Feature Store Module
Centralized repository for reusable ML features with versioning.

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**
Enhanced with CI/CD hooks, Week 1 integration, and advanced feature management.
"""

import logging
from typing import Dict, Optional, Any, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
import hashlib

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext
    from mcp_server.monitoring import get_health_monitor
    from mcp_server.auth_enhanced import require_permission, Permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def require_permission(permission):
        def decorator(func):
            return func

        return decorator

    class Permission:
        READ = "read"
        WRITE = "write"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureDefinition:
    """Definition of a feature"""

    feature_id: str
    name: str
    description: str
    data_type: str  # "int", "float", "string", "boolean", "array"
    source_table: Optional[str] = None
    transformation: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    version: str = "1.0.0"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class FeatureSet:
    """Collection of related features"""

    feature_set_id: str
    name: str
    description: str
    features: List[str]  # Feature IDs
    created_at: datetime
    created_by: str
    version: str
    tags: Dict[str, str] = field(default_factory=dict)


class FeatureStore:
    """Centralized feature store"""

    def __init__(self, store_path: str = "./feature_store"):
        """
        Initialize feature store.

        Args:
            store_path: Path to feature store storage
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.features: Dict[str, FeatureDefinition] = {}
        self.feature_sets: Dict[str, FeatureSet] = {}
        self.feature_values: Dict[str, Dict[str, Any]] = (
            {}
        )  # {entity_id: {feature_id: value}}
        self.deployment_hooks: Dict[str, List[Callable]] = {
            "pre_deployment": [],
            "post_deployment": [],
        }
        self.feature_lineage: Dict[str, List[str]] = (
            {}
        )  # {feature_id: [dependency_ids]}

        self._load_store()

    def _load_store(self):
        """Load feature store from disk"""
        features_file = self.store_path / "features.json"
        if features_file.exists():
            with open(features_file, "r") as f:
                data = json.load(f)
                for feat_id, feat_data in data.items():
                    self.features[feat_id] = FeatureDefinition(
                        feature_id=feat_data["feature_id"],
                        name=feat_data["name"],
                        description=feat_data["description"],
                        data_type=feat_data["data_type"],
                        source_table=feat_data.get("source_table"),
                        transformation=feat_data.get("transformation"),
                        created_at=datetime.fromisoformat(feat_data["created_at"]),
                        created_by=feat_data["created_by"],
                        version=feat_data["version"],
                        tags=feat_data.get("tags", {}),
                    )
            logger.info(f"Loaded {len(self.features)} features from store")

    def _save_store(self):
        """Save feature store to disk"""
        features_file = self.store_path / "features.json"
        data = {}
        for feat_id, feat in self.features.items():
            data[feat_id] = {
                "feature_id": feat.feature_id,
                "name": feat.name,
                "description": feat.description,
                "data_type": feat.data_type,
                "source_table": feat.source_table,
                "transformation": feat.transformation,
                "created_at": feat.created_at.isoformat(),
                "created_by": feat.created_by,
                "version": feat.version,
                "tags": feat.tags,
            }

        with open(features_file, "w") as f:
            json.dump(data, f, indent=2)

        # Save lineage if available
        if self.feature_lineage:
            lineage_file = self.store_path / "lineage.json"
            with open(lineage_file, "w") as f:
                json.dump(self.feature_lineage, f, indent=2)

        logger.debug(f"Saved {len(self.features)} features to store")

    @handle_errors(reraise=True, notify=False) if WEEK1_AVAILABLE else lambda f: f
    @require_permission(Permission.WRITE) if WEEK1_AVAILABLE else lambda f: f
    def register_feature(
        self,
        feature_id: str,
        name: str,
        description: str,
        data_type: str,
        source_table: Optional[str] = None,
        transformation: Optional[str] = None,
        created_by: str = "system",
        tags: Optional[Dict[str, str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> FeatureDefinition:
        """
        Register a new feature.

        **Week 1 Integration:** Uses error handling, monitoring, and RBAC from Phase 10A Week 1.

        Args:
            feature_id: Unique feature identifier
            name: Feature name
            description: Feature description
            data_type: Data type
            source_table: Source table
            transformation: Transformation logic
            created_by: Creator
            tags: Custom tags
            dependencies: List of feature IDs this feature depends on

        Returns:
            FeatureDefinition object
        """
        import time

        start_time = time.time()

        feature = FeatureDefinition(
            feature_id=feature_id,
            name=name,
            description=description,
            data_type=data_type,
            source_table=source_table,
            transformation=transformation,
            created_by=created_by,
            tags=tags or {},
        )

        self.features[feature_id] = feature

        # Track lineage if dependencies provided
        if dependencies:
            self.track_feature_lineage(feature_id, dependencies)

        self._save_store()

        # Week 1 Monitoring Integration
        if WEEK1_AVAILABLE:
            try:
                monitor = get_health_monitor()
                registration_time_ms = (time.time() - start_time) * 1000
                monitor.track_metric("feature_store.registrations", 1)
                monitor.track_metric(
                    "feature_store.registration_time_ms", registration_time_ms
                )
            except Exception as e:
                logger.debug(f"Could not track monitoring metrics: {e}")

        logger.info(f"Registered feature: {feature_id} ({name})")

        return feature

    def create_feature_set(
        self,
        feature_set_id: str,
        name: str,
        description: str,
        feature_ids: List[str],
        created_by: str = "system",
        tags: Optional[Dict[str, str]] = None,
    ) -> FeatureSet:
        """
        Create a feature set.

        Args:
            feature_set_id: Feature set identifier
            name: Feature set name
            description: Description
            feature_ids: List of feature IDs
            created_by: Creator
            tags: Custom tags

        Returns:
            FeatureSet object
        """
        # Validate features exist
        for feat_id in feature_ids:
            if feat_id not in self.features:
                raise ValueError(f"Feature {feat_id} not found")

        feature_set = FeatureSet(
            feature_set_id=feature_set_id,
            name=name,
            description=description,
            features=feature_ids,
            created_at=datetime.utcnow(),
            created_by=created_by,
            version="1.0.0",
            tags=tags or {},
        )

        self.feature_sets[feature_set_id] = feature_set

        logger.info(
            f"Created feature set: {feature_set_id} with {len(feature_ids)} features"
        )

        return feature_set

    @handle_errors(reraise=True, notify=False) if WEEK1_AVAILABLE else lambda f: f
    def write_features(self, entity_id: str, features: Dict[str, Any]):
        """
        Write feature values for an entity.

        **Week 1 Integration:** Uses error handling and monitoring from Phase 10A Week 1.

        Args:
            entity_id: Entity identifier (e.g., player_id, game_id)
            features: Dictionary of {feature_id: value}
        """
        import time

        start_time = time.time()

        # Validate features
        valid_features = {}
        for feat_id, value in features.items():
            if feat_id not in self.features:
                logger.warning(f"Feature {feat_id} not registered, skipping")
                continue
            valid_features[feat_id] = value

        if entity_id not in self.feature_values:
            self.feature_values[entity_id] = {}

        self.feature_values[entity_id].update(valid_features)

        # Week 1 Monitoring Integration
        if WEEK1_AVAILABLE:
            try:
                monitor = get_health_monitor()
                write_time_ms = (time.time() - start_time) * 1000
                monitor.track_metric("feature_store.writes", 1)
                monitor.track_metric("feature_store.write_time_ms", write_time_ms)
                monitor.track_metric(
                    "feature_store.features_written", len(valid_features)
                )
            except Exception as e:
                logger.debug(f"Could not track monitoring metrics: {e}")

        logger.debug(f"Wrote {len(valid_features)} features for entity {entity_id}")

    @handle_errors(reraise=True, notify=False) if WEEK1_AVAILABLE else lambda f: f
    @require_permission(Permission.READ) if WEEK1_AVAILABLE else lambda f: f
    def read_features(
        self, entity_ids: List[str], feature_ids: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Read features for entities.

        **Week 1 Integration:** Uses error handling, monitoring, and RBAC from Phase 10A Week 1.

        Args:
            entity_ids: List of entity identifiers
            feature_ids: Optional list of specific features (None for all)

        Returns:
            Dictionary of {entity_id: {feature_id: value}}
        """
        import time

        start_time = time.time()

        result = {}

        for entity_id in entity_ids:
            if entity_id not in self.feature_values:
                result[entity_id] = {}
                continue

            entity_features = self.feature_values[entity_id]

            if feature_ids:
                # Filter to requested features
                result[entity_id] = {
                    feat_id: entity_features.get(feat_id)
                    for feat_id in feature_ids
                    if feat_id in entity_features
                }
            else:
                # Return all features
                result[entity_id] = entity_features.copy()

        # Week 1 Monitoring Integration
        if WEEK1_AVAILABLE:
            try:
                monitor = get_health_monitor()
                read_time_ms = (time.time() - start_time) * 1000
                monitor.track_metric("feature_store.reads", 1)
                monitor.track_metric("feature_store.read_time_ms", read_time_ms)
                total_features = sum(len(feats) for feats in result.values())
                monitor.track_metric("feature_store.features_read", total_features)
            except Exception as e:
                logger.debug(f"Could not track monitoring metrics: {e}")

        return result

    def read_feature_set(
        self, entity_ids: List[str], feature_set_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Read a feature set for entities.

        Args:
            entity_ids: List of entity identifiers
            feature_set_id: Feature set identifier

        Returns:
            Dictionary of {entity_id: {feature_id: value}}
        """
        feature_set = self.feature_sets.get(feature_set_id)
        if not feature_set:
            raise ValueError(f"Feature set {feature_set_id} not found")

        return self.read_features(entity_ids, feature_set.features)

    def search_features(
        self,
        name_pattern: Optional[str] = None,
        data_type: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[FeatureDefinition]:
        """
        Search for features.

        Args:
            name_pattern: Name pattern to match
            data_type: Filter by data type
            tags: Filter by tags

        Returns:
            List of matching FeatureDefinition objects
        """
        results = []

        for feat in self.features.values():
            # Apply filters
            if name_pattern and name_pattern.lower() not in feat.name.lower():
                continue
            if data_type and feat.data_type != data_type:
                continue
            if tags:
                if not all(feat.tags.get(k) == v for k, v in tags.items()):
                    continue

            results.append(feat)

        return results

    def get_feature_stats(self) -> Dict[str, Any]:
        """Get feature store statistics"""
        type_counts = {}
        for feat in self.features.values():
            type_counts[feat.data_type] = type_counts.get(feat.data_type, 0) + 1

        return {
            "total_features": len(self.features),
            "total_feature_sets": len(self.feature_sets),
            "total_entities": len(self.feature_values),
            "by_data_type": type_counts,
        }

    # CI/CD and Deployment Methods

    def register_deployment_hook(
        self, hook_type: str, callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Register a deployment hook callback.

        **Phase 10A Week 2 - Agent 4:** CI/CD integration for feature deployments.

        Args:
            hook_type: Type of hook ('pre_deployment' or 'post_deployment')
            callback: Function to call during deployment

        Raises:
            ValueError: If hook_type is not recognized
        """
        if hook_type not in self.deployment_hooks:
            raise ValueError(
                f"Invalid hook type '{hook_type}'. Must be 'pre_deployment' or 'post_deployment'"
            )

        self.deployment_hooks[hook_type].append(callback)
        logger.info(f"Registered {hook_type} hook: {callback.__name__}")

    def notify_deployment(
        self,
        deployment_type: str,
        features: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Trigger deployment notifications and hooks.

        **Phase 10A Week 2 - Agent 4:** Execute CI/CD deployment pipeline.

        Args:
            deployment_type: Type of deployment ('pre' or 'post')
            features: List of feature IDs being deployed
            metadata: Additional deployment metadata
        """
        hook_key = f"{deployment_type}_deployment"
        if hook_key not in self.deployment_hooks:
            logger.warning(f"Unknown deployment type: {deployment_type}")
            return

        deployment_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "features": features,
            "metadata": metadata or {},
        }

        # Execute all registered hooks
        for hook in self.deployment_hooks[hook_key]:
            try:
                hook(deployment_info)
                logger.debug(f"Executed {deployment_type} hook: {hook.__name__}")
            except Exception as e:
                logger.error(
                    f"Error executing {deployment_type} hook {hook.__name__}: {e}"
                )

    def validate_deployment_compatibility(
        self, feature_ids: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate feature compatibility before deployment.

        **Phase 10A Week 2 - Agent 4:** Pre-deployment validation.

        Args:
            feature_ids: List of feature IDs to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check all features exist
        for feat_id in feature_ids:
            if feat_id not in self.features:
                errors.append(f"Feature '{feat_id}' not found in store")

        # Check dependencies
        for feat_id in feature_ids:
            if feat_id in self.feature_lineage:
                deps = self.feature_lineage[feat_id]
                for dep_id in deps:
                    if dep_id not in feature_ids and dep_id not in self.features:
                        errors.append(
                            f"Feature '{feat_id}' depends on '{dep_id}' which is not available"
                        )

        is_valid = len(errors) == 0
        return is_valid, errors

    # Feature Versioning Methods

    def compare_feature_versions(
        self, feature_id: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a feature.

        **Phase 10A Week 2 - Agent 4:** Feature version comparison.

        Args:
            feature_id: Feature identifier
            version1: First version
            version2: Second version

        Returns:
            Dictionary with comparison details

        Note:
            This is a basic implementation. For full version control,
            integrate with DVC or MLflow Model Registry.
        """
        if feature_id not in self.features:
            raise ValueError(f"Feature '{feature_id}' not found")

        feature = self.features[feature_id]

        # Basic comparison based on stored version
        # In production, would load from version history
        comparison = {
            "feature_id": feature_id,
            "current_version": feature.version,
            "versions_compared": [version1, version2],
            "differences": [],  # Would contain actual diffs
            "note": "Full version comparison requires version history storage",
        }

        # Check if current version matches either requested version
        if feature.version == version1:
            comparison["status"] = "version1 is current"
        elif feature.version == version2:
            comparison["status"] = "version2 is current"
        else:
            comparison["status"] = "neither version matches current"

        return comparison

    def rollback_feature_version(
        self, feature_id: str, target_version: str
    ) -> FeatureDefinition:
        """
        Rollback a feature to a previous version.

        **Phase 10A Week 2 - Agent 4:** Feature version rollback.

        Args:
            feature_id: Feature identifier
            target_version: Version to rollback to

        Returns:
            Updated FeatureDefinition

        Note:
            This is a placeholder. Full implementation requires version history storage.
        """
        if feature_id not in self.features:
            raise ValueError(f"Feature '{feature_id}' not found")

        feature = self.features[feature_id]

        logger.warning(
            f"Rollback feature '{feature_id}' to version {target_version} "
            f"(current: {feature.version}). Full versioning requires DVC/MLflow integration."
        )

        # In production, would load from version history and restore
        # For now, just log the intent
        return feature

    # Feature Lineage Methods

    def track_feature_lineage(self, feature_id: str, dependencies: List[str]):
        """
        Track feature lineage and dependencies.

        **Phase 10A Week 2 - Agent 4:** Feature lineage tracking for data governance.

        Args:
            feature_id: Feature identifier
            dependencies: List of feature IDs this feature depends on
        """
        # Validate dependencies exist
        for dep_id in dependencies:
            if dep_id not in self.features:
                logger.warning(
                    f"Dependency '{dep_id}' for feature '{feature_id}' not found in store"
                )

        self.feature_lineage[feature_id] = dependencies
        logger.info(
            f"Tracked lineage for '{feature_id}': {len(dependencies)} dependencies"
        )

    def get_feature_lineage(
        self, feature_id: str, recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Get feature lineage and dependency graph.

        **Phase 10A Week 2 - Agent 4:** Retrieve feature lineage for impact analysis.

        Args:
            feature_id: Feature identifier
            recursive: If True, get full dependency tree

        Returns:
            Dictionary with lineage information
        """
        if feature_id not in self.features:
            raise ValueError(f"Feature '{feature_id}' not found")

        lineage = {
            "feature_id": feature_id,
            "direct_dependencies": self.feature_lineage.get(feature_id, []),
            "dependent_features": [],  # Features that depend on this one
        }

        # Find features that depend on this one
        for feat_id, deps in self.feature_lineage.items():
            if feature_id in deps:
                lineage["dependent_features"].append(feat_id)

        # Recursive dependency resolution
        if recursive and lineage["direct_dependencies"]:
            lineage["full_dependency_tree"] = self._build_dependency_tree(feature_id)

        return lineage

    def _build_dependency_tree(
        self, feature_id: str, visited: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Recursively build dependency tree.

        Args:
            feature_id: Feature identifier
            visited: Set of already visited features (for cycle detection)

        Returns:
            Nested dependency tree
        """
        if visited is None:
            visited = set()

        if feature_id in visited:
            return {"feature_id": feature_id, "cycle_detected": True}

        visited.add(feature_id)

        tree = {
            "feature_id": feature_id,
            "dependencies": [],
        }

        direct_deps = self.feature_lineage.get(feature_id, [])
        for dep_id in direct_deps:
            if dep_id in self.features:
                tree["dependencies"].append(
                    self._build_dependency_tree(dep_id, visited.copy())
                )

        return tree


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("FEATURE STORE DEMO")
    print("=" * 80)

    store = FeatureStore(store_path="./demo_feature_store")

    # Register features
    print("\n" + "=" * 80)
    print("REGISTERING FEATURES")
    print("=" * 80)

    store.register_feature(
        feature_id="player_ppg",
        name="Points Per Game",
        description="Average points scored per game",
        data_type="float",
        source_table="player_stats",
        transformation="AVG(points)",
        tags={"category": "scoring"},
    )

    store.register_feature(
        feature_id="player_apg",
        name="Assists Per Game",
        description="Average assists per game",
        data_type="float",
        source_table="player_stats",
        transformation="AVG(assists)",
        tags={"category": "playmaking"},
    )

    store.register_feature(
        feature_id="player_rpg",
        name="Rebounds Per Game",
        description="Average rebounds per game",
        data_type="float",
        source_table="player_stats",
        transformation="AVG(rebounds)",
        tags={"category": "rebounding"},
    )

    print("✅ Registered 3 features")

    # Create feature set
    print("\n" + "=" * 80)
    print("CREATING FEATURE SET")
    print("=" * 80)

    store.create_feature_set(
        feature_set_id="player_basic_stats",
        name="Player Basic Stats",
        description="Basic player performance statistics",
        feature_ids=["player_ppg", "player_apg", "player_rpg"],
        tags={"category": "basic_stats"},
    )

    print("✅ Created feature set with 3 features")

    # Write feature values
    print("\n" + "=" * 80)
    print("WRITING FEATURE VALUES")
    print("=" * 80)

    store.write_features(
        entity_id="player_123",
        features={"player_ppg": 25.3, "player_apg": 8.1, "player_rpg": 7.4},
    )

    store.write_features(
        entity_id="player_456",
        features={"player_ppg": 18.7, "player_apg": 3.2, "player_rpg": 9.5},
    )

    print("✅ Wrote features for 2 players")

    # Read features
    print("\n" + "=" * 80)
    print("READING FEATURES")
    print("=" * 80)

    features = store.read_feature_set(
        entity_ids=["player_123", "player_456"], feature_set_id="player_basic_stats"
    )

    for entity_id, feats in features.items():
        print(f"\n{entity_id}:")
        for feat_id, value in feats.items():
            feat_def = store.features[feat_id]
            print(f"  - {feat_def.name}: {value}")

    # Search features
    print("\n" + "=" * 80)
    print("SEARCHING FEATURES")
    print("=" * 80)

    results = store.search_features(name_pattern="per game", data_type="float")
    print(f"\nFound {len(results)} features (name contains 'per game', type=float):")
    for feat in results:
        print(f"  - {feat.name} ({feat.feature_id})")

    # Feature stats
    print("\n" + "=" * 80)
    print("FEATURE STORE STATISTICS")
    print("=" * 80)

    stats = store.get_feature_stats()
    print(f"\nTotal Features: {stats['total_features']}")
    print(f"Total Feature Sets: {stats['total_feature_sets']}")
    print(f"Total Entities: {stats['total_entities']}")
    print(f"\nBy Data Type:")
    for dtype, count in stats["by_data_type"].items():
        print(f"  - {dtype}: {count}")

    print("\n" + "=" * 80)
    print("Feature Store Demo Complete!")
    print("=" * 80)
