"""
Model Persistence & Versioning (Agent 12, Module 1)

Provides model serialization, versioning, and registry for NBA simulation models.

Integrates with:
- Agent 2 (Monitoring): Track model versions and deployments
- Agent 9 (Performance): Profile serialization operations
- Agent 11 (Models): Persist trained models
"""

import logging
import pickle
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import warnings

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Version information for a deployed model"""

    model_id: str
    version: str
    created_at: datetime
    model_type: str
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        """Create from dictionary"""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class ModelSerializer:
    """
    Serialize and deserialize ML models.

    Supports:
    - Pickle serialization
    - Checksum verification
    - Compression
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize model serializer.

        Args:
            base_path: Base directory for model storage
        """
        self.base_path = base_path or Path.cwd() / "models"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.serializations_count = 0
        self.deserializations_count = 0

    def serialize(
        self,
        model: Any,
        model_id: str,
        version: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Path, str]:
        """
        Serialize model to disk.

        Args:
            model: Model to serialize
            model_id: Unique model identifier
            version: Model version
            metadata: Optional metadata to store

        Returns:
            (file_path, checksum)
        """
        # Create file path
        file_name = f"{model_id}_v{version}.pkl"
        file_path = self.base_path / file_name

        # Serialize model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with open(file_path, "wb") as f:
                pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

        # Compute checksum
        checksum = self._compute_checksum(file_path)

        # Save metadata if provided
        if metadata:
            metadata_path = file_path.with_suffix(".json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        self.serializations_count += 1
        logger.info(f"Serialized model {model_id} v{version} to {file_path}")

        return file_path, checksum

    def deserialize(
        self,
        model_id: str,
        version: str,
        verify_checksum: bool = True,
        expected_checksum: Optional[str] = None,
    ) -> Any:
        """
        Deserialize model from disk.

        Args:
            model_id: Model identifier
            version: Model version
            verify_checksum: Whether to verify checksum
            expected_checksum: Expected checksum for verification

        Returns:
            Deserialized model

        Raises:
            FileNotFoundError: If model file not found
            ValueError: If checksum verification fails
        """
        # Find file
        file_name = f"{model_id}_v{version}.pkl"
        file_path = self.base_path / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        # Verify checksum if requested
        if verify_checksum and expected_checksum:
            actual_checksum = self._compute_checksum(file_path)
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch for {model_id} v{version}. "
                    f"Expected: {expected_checksum}, Got: {actual_checksum}"
                )

        # Deserialize
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with open(file_path, "rb") as f:
                model = pickle.load(f)

        self.deserializations_count += 1
        logger.info(f"Deserialized model {model_id} v{version} from {file_path}")

        return model

    def _compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of checksum
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def list_models(self) -> List[Tuple[str, str]]:
        """
        List all serialized models.

        Returns:
            List of (model_id, version) tuples
        """
        models = []
        for file_path in self.base_path.glob("*.pkl"):
            # Parse filename: model_id_vversion.pkl
            name = file_path.stem
            if "_v" in name:
                model_id, version = name.rsplit("_v", 1)
                models.append((model_id, version))
        return sorted(models)

    def delete_model(self, model_id: str, version: str) -> bool:
        """
        Delete serialized model.

        Args:
            model_id: Model identifier
            version: Model version

        Returns:
            True if deleted, False if not found
        """
        file_name = f"{model_id}_v{version}.pkl"
        file_path = self.base_path / file_name

        if file_path.exists():
            file_path.unlink()
            # Also delete metadata if exists
            metadata_path = file_path.with_suffix(".json")
            if metadata_path.exists():
                metadata_path.unlink()
            logger.info(f"Deleted model {model_id} v{version}")
            return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get serializer statistics"""
        return {
            "base_path": str(self.base_path),
            "serializations": self.serializations_count,
            "deserializations": self.deserializations_count,
            "total_models": len(self.list_models()),
        }


class ModelRegistry:
    """
    Registry for managing model versions and metadata.

    Features:
    - Version tracking
    - Metadata storage
    - Model lifecycle management
    - Version comparison
    """

    def __init__(
        self,
        serializer: Optional[ModelSerializer] = None,
        registry_path: Optional[Path] = None,
    ):
        """
        Initialize model registry.

        Args:
            serializer: Model serializer instance
            registry_path: Path to registry metadata file
        """
        self.serializer = serializer or ModelSerializer()
        self.registry_path = registry_path or Path.cwd() / "model_registry.json"
        self.versions: Dict[str, List[ModelVersion]] = {}
        self._load_registry()

    def register_model(
        self,
        model: Any,
        model_id: str,
        version: str,
        model_type: str,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelVersion:
        """
        Register a new model version.

        Args:
            model: Model to register
            model_id: Unique model identifier
            version: Version string
            model_type: Type of model (e.g., 'ensemble', 'neural_net')
            metrics: Performance metrics
            metadata: Additional metadata

        Returns:
            ModelVersion object
        """
        # Serialize model
        file_path, checksum = self.serializer.serialize(
            model, model_id, version, metadata
        )

        # Create version object
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            created_at=datetime.now(),
            model_type=model_type,
            metrics=metrics or {},
            metadata=metadata or {},
            file_path=str(file_path),
            checksum=checksum,
        )

        # Add to registry
        if model_id not in self.versions:
            self.versions[model_id] = []
        self.versions[model_id].append(model_version)

        # Save registry
        self._save_registry()

        logger.info(f"Registered model {model_id} v{version}")
        return model_version

    def get_model(
        self,
        model_id: str,
        version: Optional[str] = None,
        verify_checksum: bool = False,
    ) -> Any:
        """
        Get model by ID and version.

        Args:
            model_id: Model identifier
            version: Version string (if None, gets latest)
            verify_checksum: Whether to verify file checksum

        Returns:
            Deserialized model

        Raises:
            ValueError: If model not found
        """
        if model_id not in self.versions:
            raise ValueError(f"Model {model_id} not found in registry")

        # Get version
        if version is None:
            # Get latest version
            model_version = self.versions[model_id][-1]
        else:
            # Find specific version
            model_version = None
            for v in self.versions[model_id]:
                if v.version == version:
                    model_version = v
                    break

            if model_version is None:
                raise ValueError(f"Model {model_id} version {version} not found")

        # Deserialize
        return self.serializer.deserialize(
            model_id,
            model_version.version,
            verify_checksum=verify_checksum,
            expected_checksum=model_version.checksum if verify_checksum else None,
        )

    def get_version_info(
        self, model_id: str, version: Optional[str] = None
    ) -> ModelVersion:
        """
        Get version information without loading model.

        Args:
            model_id: Model identifier
            version: Version string (if None, gets latest)

        Returns:
            ModelVersion object

        Raises:
            ValueError: If model not found
        """
        if model_id not in self.versions:
            raise ValueError(f"Model {model_id} not found in registry")

        if version is None:
            return self.versions[model_id][-1]

        for v in self.versions[model_id]:
            if v.version == version:
                return v

        raise ValueError(f"Model {model_id} version {version} not found")

    def list_models(self) -> List[str]:
        """List all registered model IDs"""
        return sorted(self.versions.keys())

    def list_versions(self, model_id: str) -> List[str]:
        """
        List all versions for a model.

        Args:
            model_id: Model identifier

        Returns:
            List of version strings
        """
        if model_id not in self.versions:
            return []
        return [v.version for v in self.versions[model_id]]

    def compare_versions(
        self, model_id: str, version1: str, version2: str, metric: str
    ) -> Dict[str, Any]:
        """
        Compare two model versions on a metric.

        Args:
            model_id: Model identifier
            version1: First version
            version2: Second version
            metric: Metric to compare

        Returns:
            Comparison results
        """
        v1_info = self.get_version_info(model_id, version1)
        v2_info = self.get_version_info(model_id, version2)

        v1_metric = v1_info.metrics.get(metric)
        v2_metric = v2_info.metrics.get(metric)

        if v1_metric is None or v2_metric is None:
            raise ValueError(f"Metric {metric} not found in one or both versions")

        return {
            "model_id": model_id,
            "version1": version1,
            "version2": version2,
            "metric": metric,
            "value1": v1_metric,
            "value2": v2_metric,
            "difference": v2_metric - v1_metric,
            "percent_change": (
                ((v2_metric - v1_metric) / v1_metric * 100) if v1_metric != 0 else 0
            ),
        }

    def _load_registry(self):
        """Load registry from disk"""
        if self.registry_path.exists():
            with open(self.registry_path, "r") as f:
                data = json.load(f)

            for model_id, versions in data.items():
                self.versions[model_id] = [ModelVersion.from_dict(v) for v in versions]

            logger.info(f"Loaded registry with {len(self.versions)} models")

    def _save_registry(self):
        """Save registry to disk"""
        data = {
            model_id: [v.to_dict() for v in versions]
            for model_id, versions in self.versions.items()
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_models": len(self.versions),
            "total_versions": sum(len(v) for v in self.versions.values()),
            "model_types": list(
                set(
                    v.model_type
                    for versions in self.versions.values()
                    for v in versions
                )
            ),
            "serializer_stats": self.serializer.get_statistics(),
        }
