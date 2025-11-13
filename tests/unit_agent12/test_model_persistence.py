"""
Unit Tests for Model Persistence (Agent 12, Module 1)

Tests model serialization, versioning, and registry.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

from mcp_server.simulations.deployment.model_persistence import (
    ModelVersion,
    ModelSerializer,
    ModelRegistry,
)


class TestModelVersion:
    """Test ModelVersion dataclass"""

    def test_model_version_creation(self):
        """Test creating model version"""
        version = ModelVersion(
            model_id="test_model",
            version="1.0.0",
            created_at=datetime.now(),
            model_type="linear",
            metrics={"mse": 0.5, "r2": 0.95},
            metadata={"notes": "Initial version"},
        )
        assert version.model_id == "test_model"
        assert version.version == "1.0.0"
        assert version.model_type == "linear"
        assert version.metrics["mse"] == 0.5

    def test_to_dict(self):
        """Test converting to dictionary"""
        version = ModelVersion(
            model_id="test", version="1.0", created_at=datetime.now(), model_type="test"
        )
        data = version.to_dict()
        assert isinstance(data, dict)
        assert data["model_id"] == "test"
        assert isinstance(data["created_at"], str)

    def test_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "model_id": "test",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "model_type": "test",
            "metrics": {},
            "metadata": {},
            "file_path": None,
            "checksum": None,
        }
        version = ModelVersion.from_dict(data)
        assert version.model_id == "test"
        assert isinstance(version.created_at, datetime)


class TestModelSerializer:
    """Test ModelSerializer class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def serializer(self, temp_dir):
        """Create serializer with temp directory"""
        return ModelSerializer(base_path=temp_dir)

    @pytest.fixture
    def sample_model(self):
        """Create sample sklearn model"""
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model = LinearRegression()
        model.fit(X, y)
        return model

    def test_serializer_initialization(self, temp_dir):
        """Test initializing serializer"""
        serializer = ModelSerializer(base_path=temp_dir)
        assert serializer.base_path == temp_dir
        assert serializer.base_path.exists()
        assert serializer.serializations_count == 0

    def test_serialize_model(self, serializer, sample_model):
        """Test serializing model"""
        file_path, checksum = serializer.serialize(sample_model, "test_model", "1.0")
        assert file_path.exists()
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex digest

    def test_serialize_with_metadata(self, serializer, sample_model):
        """Test serializing with metadata"""
        metadata = {"author": "test", "date": "2024-01-01"}
        file_path, checksum = serializer.serialize(
            sample_model, "test_model", "1.0", metadata=metadata
        )
        # Check metadata file exists
        metadata_path = file_path.with_suffix(".json")
        assert metadata_path.exists()

    def test_deserialize_model(self, serializer, sample_model):
        """Test deserializing model"""
        # Serialize first
        serializer.serialize(sample_model, "test_model", "1.0")

        # Deserialize
        loaded_model = serializer.deserialize(
            "test_model", "1.0", verify_checksum=False
        )
        assert loaded_model is not None
        assert isinstance(loaded_model, LinearRegression)

    def test_deserialize_with_checksum_verification(self, serializer, sample_model):
        """Test deserializing with checksum verification"""
        file_path, checksum = serializer.serialize(sample_model, "test_model", "1.0")

        # Should succeed with correct checksum
        loaded_model = serializer.deserialize(
            "test_model", "1.0", verify_checksum=True, expected_checksum=checksum
        )
        assert loaded_model is not None

    def test_deserialize_wrong_checksum_fails(self, serializer, sample_model):
        """Test deserializing fails with wrong checksum"""
        serializer.serialize(sample_model, "test_model", "1.0")

        with pytest.raises(ValueError, match="Checksum mismatch"):
            serializer.deserialize(
                "test_model",
                "1.0",
                verify_checksum=True,
                expected_checksum="wrong_checksum",
            )

    def test_deserialize_nonexistent_model(self, serializer):
        """Test deserializing nonexistent model fails"""
        with pytest.raises(FileNotFoundError):
            serializer.deserialize("nonexistent", "1.0")

    def test_list_models(self, serializer, sample_model):
        """Test listing models"""
        serializer.serialize(sample_model, "model1", "1.0")
        serializer.serialize(sample_model, "model2", "2.0")

        models = serializer.list_models()
        assert len(models) == 2
        assert ("model1", "1.0") in models
        assert ("model2", "2.0") in models

    def test_delete_model(self, serializer, sample_model):
        """Test deleting model"""
        serializer.serialize(sample_model, "test_model", "1.0")
        assert serializer.delete_model("test_model", "1.0") is True

        # Should not exist anymore
        with pytest.raises(FileNotFoundError):
            serializer.deserialize("test_model", "1.0")

    def test_delete_nonexistent_model(self, serializer):
        """Test deleting nonexistent model"""
        assert serializer.delete_model("nonexistent", "1.0") is False

    def test_get_statistics(self, serializer, sample_model):
        """Test getting statistics"""
        serializer.serialize(sample_model, "model1", "1.0")
        serializer.deserialize("model1", "1.0", verify_checksum=False)

        stats = serializer.get_statistics()
        assert stats["serializations"] == 1
        assert stats["deserializations"] == 1
        assert stats["total_models"] == 1


class TestModelRegistry:
    """Test ModelRegistry class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def registry(self, temp_dir):
        """Create registry with temp directory"""
        serializer = ModelSerializer(base_path=temp_dir)
        registry_path = temp_dir / "registry.json"
        return ModelRegistry(serializer=serializer, registry_path=registry_path)

    @pytest.fixture
    def sample_model(self):
        """Create sample sklearn model"""
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model = LinearRegression()
        model.fit(X, y)
        return model

    def test_registry_initialization(self, registry):
        """Test initializing registry"""
        assert registry.versions == {}
        assert registry.serializer is not None

    def test_register_model(self, registry, sample_model):
        """Test registering model"""
        version = registry.register_model(
            sample_model, "test_model", "1.0.0", "linear", metrics={"mse": 0.5}
        )
        assert version.model_id == "test_model"
        assert version.version == "1.0.0"
        assert version.checksum is not None

    def test_get_model_latest(self, registry, sample_model):
        """Test getting latest model version"""
        registry.register_model(sample_model, "test", "1.0", "linear")
        registry.register_model(sample_model, "test", "2.0", "linear")

        # Get latest (should be 2.0)
        loaded_model = registry.get_model("test")
        assert loaded_model is not None

    def test_get_model_specific_version(self, registry, sample_model):
        """Test getting specific model version"""
        registry.register_model(sample_model, "test", "1.0", "linear")
        registry.register_model(sample_model, "test", "2.0", "linear")

        # Get specific version
        loaded_model = registry.get_model("test", "1.0")
        assert loaded_model is not None

    def test_get_nonexistent_model(self, registry):
        """Test getting nonexistent model fails"""
        with pytest.raises(ValueError, match="not found in registry"):
            registry.get_model("nonexistent")

    def test_get_nonexistent_version(self, registry, sample_model):
        """Test getting nonexistent version fails"""
        registry.register_model(sample_model, "test", "1.0", "linear")

        with pytest.raises(ValueError, match="version .* not found"):
            registry.get_model("test", "2.0")

    def test_get_version_info(self, registry, sample_model):
        """Test getting version info"""
        registry.register_model(
            sample_model, "test", "1.0", "linear", metrics={"mse": 0.5}
        )

        info = registry.get_version_info("test", "1.0")
        assert info.model_id == "test"
        assert info.version == "1.0"
        assert info.metrics["mse"] == 0.5

    def test_list_models(self, registry, sample_model):
        """Test listing models"""
        registry.register_model(sample_model, "model1", "1.0", "linear")
        registry.register_model(sample_model, "model2", "1.0", "linear")

        models = registry.list_models()
        assert "model1" in models
        assert "model2" in models

    def test_list_versions(self, registry, sample_model):
        """Test listing versions"""
        registry.register_model(sample_model, "test", "1.0", "linear")
        registry.register_model(sample_model, "test", "2.0", "linear")

        versions = registry.list_versions("test")
        assert "1.0" in versions
        assert "2.0" in versions

    def test_compare_versions(self, registry, sample_model):
        """Test comparing versions"""
        registry.register_model(
            sample_model, "test", "1.0", "linear", metrics={"mse": 1.0}
        )
        registry.register_model(
            sample_model, "test", "2.0", "linear", metrics={"mse": 0.5}
        )

        comparison = registry.compare_versions("test", "1.0", "2.0", "mse")
        assert comparison["value1"] == 1.0
        assert comparison["value2"] == 0.5
        assert comparison["difference"] == -0.5
        assert comparison["percent_change"] == -50.0

    def test_registry_persistence(self, temp_dir, sample_model):
        """Test registry persistence across instances"""
        # Create first registry and register model
        serializer1 = ModelSerializer(base_path=temp_dir)
        registry_path = temp_dir / "registry.json"
        registry1 = ModelRegistry(serializer=serializer1, registry_path=registry_path)

        registry1.register_model(
            sample_model, "test", "1.0", "linear", metrics={"mse": 0.5}
        )

        # Create second registry (should load from disk)
        serializer2 = ModelSerializer(base_path=temp_dir)
        registry2 = ModelRegistry(serializer=serializer2, registry_path=registry_path)

        assert "test" in registry2.list_models()
        info = registry2.get_version_info("test", "1.0")
        assert info.metrics["mse"] == 0.5

    def test_get_statistics(self, registry, sample_model):
        """Test getting statistics"""
        registry.register_model(sample_model, "model1", "1.0", "linear")
        registry.register_model(sample_model, "model2", "1.0", "ensemble")

        stats = registry.get_statistics()
        assert stats["total_models"] == 2
        assert stats["total_versions"] == 2
        assert "linear" in stats["model_types"]
        assert "ensemble" in stats["model_types"]
