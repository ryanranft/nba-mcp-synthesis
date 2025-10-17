"""
Feature Store Module
Centralized repository for reusable ML features with versioning.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import json
from pathlib import Path
import hashlib

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

        logger.debug(f"Saved {len(self.features)} features to store")

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
    ) -> FeatureDefinition:
        """
        Register a new feature.

        Args:
            feature_id: Unique feature identifier
            name: Feature name
            description: Feature description
            data_type: Data type
            source_table: Source table
            transformation: Transformation logic
            created_by: Creator
            tags: Custom tags

        Returns:
            FeatureDefinition object
        """
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
        self._save_store()

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

    def write_features(self, entity_id: str, features: Dict[str, Any]):
        """
        Write feature values for an entity.

        Args:
            entity_id: Entity identifier (e.g., player_id, game_id)
            features: Dictionary of {feature_id: value}
        """
        # Validate features
        for feat_id in features:
            if feat_id not in self.features:
                logger.warning(f"Feature {feat_id} not registered, skipping")
                continue

        if entity_id not in self.feature_values:
            self.feature_values[entity_id] = {}

        self.feature_values[entity_id].update(features)

        logger.debug(f"Wrote {len(features)} features for entity {entity_id}")

    def read_features(
        self, entity_ids: List[str], feature_ids: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Read features for entities.

        Args:
            entity_ids: List of entity identifiers
            feature_ids: Optional list of specific features (None for all)

        Returns:
            Dictionary of {entity_id: {feature_id: value}}
        """
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
