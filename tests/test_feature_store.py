"""
Tests for feature_store.py module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**
Tests for feature store with CI/CD hooks, versioning, and lineage tracking.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from mcp_server.feature_store import (
    FeatureStore,
    FeatureDefinition,
    FeatureSet,
)


@pytest.fixture
def temp_store_path():
    """Create a temporary directory for feature store"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def feature_store(temp_store_path):
    """Create a feature store instance"""
    return FeatureStore(store_path=temp_store_path)


# Feature Registration Tests (5 tests)


def test_register_feature(feature_store):
    """Test basic feature registration"""
    feature = feature_store.register_feature(
        feature_id="player_ppg",
        name="Points Per Game",
        description="Average points scored per game",
        data_type="float",
        source_table="player_stats",
        transformation="AVG(points)",
    )

    assert isinstance(feature, FeatureDefinition)
    assert feature.feature_id == "player_ppg"
    assert feature.name == "Points Per Game"
    assert feature.data_type == "float"
    assert "player_ppg" in feature_store.features


def test_register_feature_with_dependencies(feature_store):
    """Test feature registration with dependencies"""
    # Register base feature
    feature_store.register_feature(
        feature_id="total_points",
        name="Total Points",
        description="Total points scored",
        data_type="int",
    )

    # Register dependent feature
    feature = feature_store.register_feature(
        feature_id="points_per_game",
        name="Points Per Game",
        description="Average points per game",
        data_type="float",
        dependencies=["total_points"],
    )

    assert "points_per_game" in feature_store.feature_lineage
    assert "total_points" in feature_store.feature_lineage["points_per_game"]


def test_register_feature_persistence(temp_store_path):
    """Test feature persistence across store instances"""
    # Create store and register feature
    store1 = FeatureStore(store_path=temp_store_path)
    store1.register_feature(
        feature_id="test_feature",
        name="Test Feature",
        description="Test",
        data_type="float",
    )

    # Create new store instance and verify feature persisted
    store2 = FeatureStore(store_path=temp_store_path)
    assert "test_feature" in store2.features
    assert store2.features["test_feature"].name == "Test Feature"


def test_create_feature_set(feature_store):
    """Test feature set creation"""
    # Register features
    feature_store.register_feature(
        feature_id="ppg", name="PPG", description="Points per game", data_type="float"
    )
    feature_store.register_feature(
        feature_id="rpg", name="RPG", description="Rebounds per game", data_type="float"
    )
    feature_store.register_feature(
        feature_id="apg", name="APG", description="Assists per game", data_type="float"
    )

    # Create feature set
    feature_set = feature_store.create_feature_set(
        feature_set_id="player_stats",
        name="Player Stats",
        description="Basic player statistics",
        feature_ids=["ppg", "rpg", "apg"],
    )

    assert isinstance(feature_set, FeatureSet)
    assert feature_set.feature_set_id == "player_stats"
    assert len(feature_set.features) == 3
    assert "player_stats" in feature_store.feature_sets


def test_create_feature_set_invalid_feature(feature_store):
    """Test feature set creation with invalid feature"""
    with pytest.raises(ValueError, match="Feature .* not found"):
        feature_store.create_feature_set(
            feature_set_id="invalid_set",
            name="Invalid Set",
            description="Test",
            feature_ids=["nonexistent_feature"],
        )


# Feature Read/Write Tests (5 tests)


def test_write_and_read_features(feature_store):
    """Test writing and reading feature values"""
    # Register feature
    feature_store.register_feature(
        feature_id="ppg", name="PPG", description="Points per game", data_type="float"
    )

    # Write features
    feature_store.write_features(entity_id="player_123", features={"ppg": 25.5})

    # Read features
    result = feature_store.read_features(entity_ids=["player_123"], feature_ids=["ppg"])

    assert "player_123" in result
    assert result["player_123"]["ppg"] == 25.5


def test_read_nonexistent_entity(feature_store):
    """Test reading features for nonexistent entity"""
    result = feature_store.read_features(
        entity_ids=["nonexistent"], feature_ids=["ppg"]
    )
    assert "nonexistent" in result
    assert result["nonexistent"] == {}


def test_read_feature_set(feature_store):
    """Test reading a feature set"""
    # Register features and create set
    feature_store.register_feature(
        feature_id="ppg", name="PPG", description="Points", data_type="float"
    )
    feature_store.register_feature(
        feature_id="rpg", name="RPG", description="Rebounds", data_type="float"
    )
    feature_store.create_feature_set(
        feature_set_id="stats",
        name="Stats",
        description="Stats",
        feature_ids=["ppg", "rpg"],
    )

    # Write features
    feature_store.write_features(
        entity_id="player_1", features={"ppg": 20.0, "rpg": 8.0}
    )

    # Read feature set
    result = feature_store.read_feature_set(
        entity_ids=["player_1"], feature_set_id="stats"
    )

    assert "player_1" in result
    assert result["player_1"]["ppg"] == 20.0
    assert result["player_1"]["rpg"] == 8.0


def test_write_unregistered_feature_warning(feature_store, caplog):
    """Test warning when writing unregistered feature"""
    feature_store.write_features(
        entity_id="player_1", features={"unknown_feature": 100}
    )

    # Check that a warning was logged
    assert "not registered" in caplog.text


def test_search_features(feature_store):
    """Test feature search functionality"""
    # Register multiple features
    feature_store.register_feature(
        feature_id="ppg",
        name="Points Per Game",
        description="Points",
        data_type="float",
        tags={"category": "scoring"},
    )
    feature_store.register_feature(
        feature_id="total_points",
        name="Total Points",
        description="Total",
        data_type="int",
        tags={"category": "scoring"},
    )
    feature_store.register_feature(
        feature_id="games_played",
        name="Games Played",
        description="Games",
        data_type="int",
        tags={"category": "metadata"},
    )

    # Search by name pattern
    results = feature_store.search_features(name_pattern="points")
    assert len(results) >= 2

    # Search by data type
    results = feature_store.search_features(data_type="float")
    assert len(results) >= 1

    # Search by tags
    results = feature_store.search_features(tags={"category": "scoring"})
    assert len(results) == 2


# CI/CD Deployment Tests (3 tests)


def test_register_deployment_hook(feature_store):
    """Test registering deployment hooks"""

    def pre_hook(info):
        pass

    def post_hook(info):
        pass

    feature_store.register_deployment_hook("pre_deployment", pre_hook)
    feature_store.register_deployment_hook("post_deployment", post_hook)

    assert len(feature_store.deployment_hooks["pre_deployment"]) == 1
    assert len(feature_store.deployment_hooks["post_deployment"]) == 1


def test_notify_deployment(feature_store):
    """Test deployment notification"""
    hook_called = {"pre": False, "post": False}

    def pre_hook(info):
        hook_called["pre"] = True
        assert "features" in info
        assert "timestamp" in info

    def post_hook(info):
        hook_called["post"] = True

    feature_store.register_deployment_hook("pre_deployment", pre_hook)
    feature_store.register_deployment_hook("post_deployment", post_hook)

    feature_store.notify_deployment("pre", features=["feature1"])
    feature_store.notify_deployment("post", features=["feature1"])

    assert hook_called["pre"] is True
    assert hook_called["post"] is True


def test_validate_deployment_compatibility(feature_store):
    """Test deployment compatibility validation"""
    # Register features
    feature_store.register_feature(
        feature_id="feature1", name="Feature 1", description="Test", data_type="float"
    )

    # Valid deployment
    is_valid, errors = feature_store.validate_deployment_compatibility(["feature1"])
    assert is_valid is True
    assert len(errors) == 0

    # Invalid deployment (missing feature)
    is_valid, errors = feature_store.validate_deployment_compatibility(
        ["feature1", "nonexistent"]
    )
    assert is_valid is False
    assert len(errors) > 0


# Versioning Tests (3 tests)


def test_compare_feature_versions(feature_store):
    """Test feature version comparison"""
    feature_store.register_feature(
        feature_id="test_feature", name="Test", description="Test", data_type="float"
    )

    comparison = feature_store.compare_feature_versions(
        "test_feature", "1.0.0", "1.1.0"
    )

    assert "feature_id" in comparison
    assert "current_version" in comparison
    assert comparison["feature_id"] == "test_feature"


def test_rollback_feature_version(feature_store):
    """Test feature version rollback"""
    feature_store.register_feature(
        feature_id="test_feature", name="Test", description="Test", data_type="float"
    )

    feature = feature_store.rollback_feature_version("test_feature", "1.0.0")

    assert isinstance(feature, FeatureDefinition)
    assert feature.feature_id == "test_feature"


def test_rollback_nonexistent_feature(feature_store):
    """Test rollback of nonexistent feature"""
    with pytest.raises(ValueError, match="not found"):
        feature_store.rollback_feature_version("nonexistent", "1.0.0")


# Lineage Tracking Tests (2 tests)


def test_track_feature_lineage(feature_store):
    """Test feature lineage tracking"""
    # Register features
    feature_store.register_feature(
        feature_id="base_feature", name="Base", description="Base", data_type="float"
    )
    feature_store.register_feature(
        feature_id="derived_feature",
        name="Derived",
        description="Derived",
        data_type="float",
        dependencies=["base_feature"],
    )

    assert "derived_feature" in feature_store.feature_lineage
    assert "base_feature" in feature_store.feature_lineage["derived_feature"]


def test_get_feature_lineage(feature_store):
    """Test retrieving feature lineage"""
    # Create lineage chain
    feature_store.register_feature(
        feature_id="f1", name="F1", description="Level 1", data_type="float"
    )
    feature_store.register_feature(
        feature_id="f2",
        name="F2",
        description="Level 2",
        data_type="float",
        dependencies=["f1"],
    )
    feature_store.register_feature(
        feature_id="f3",
        name="F3",
        description="Level 3",
        data_type="float",
        dependencies=["f2"],
    )

    lineage = feature_store.get_feature_lineage("f3", recursive=False)

    assert lineage["feature_id"] == "f3"
    assert "f2" in lineage["direct_dependencies"]
    assert "f3" in feature_store.get_feature_lineage("f2")["dependent_features"]


# Statistics Tests (2 tests)


def test_get_feature_stats(feature_store):
    """Test feature store statistics"""
    # Register features of different types
    feature_store.register_feature(
        feature_id="f1", name="F1", description="Float", data_type="float"
    )
    feature_store.register_feature(
        feature_id="f2", name="F2", description="Int", data_type="int"
    )
    feature_store.register_feature(
        feature_id="f3", name="F3", description="String", data_type="string"
    )

    stats = feature_store.get_feature_stats()

    assert stats["total_features"] == 3
    assert stats["total_feature_sets"] == 0
    assert "by_data_type" in stats
    assert stats["by_data_type"]["float"] == 1
    assert stats["by_data_type"]["int"] == 1


def test_get_feature_stats_empty_store(feature_store):
    """Test statistics for empty feature store"""
    stats = feature_store.get_feature_stats()

    assert stats["total_features"] == 0
    assert stats["total_feature_sets"] == 0
    assert stats["total_entities"] == 0
