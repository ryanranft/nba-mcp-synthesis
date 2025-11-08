"""
Model Registry and Versioning (Agent 17, Module 5)

Model management system:
- Save and load trained models
- Model versioning and metadata tracking
- Performance history
- Model comparison and selection
- Production model management
- Experiment tracking

Integrates with:
- hybrid_models: Save/load hybrid models
- model_selection: Track performance metrics
- All model types: Universal persistence
"""

import logging
import pickle
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model lifecycle status"""
    TRAINING = "training"
    VALIDATION = "validation"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass
class ModelMetadata:
    """Metadata for a trained model"""

    # Identification
    model_id: str
    model_name: str
    model_type: str  # "random_forest", "two_stage", "prophet", etc.
    version: str

    # Training info
    training_date: str  # ISO format
    training_data_hash: Optional[str] = None
    n_training_samples: int = 0

    # Performance metrics
    train_score: float = 0.0
    test_score: float = 0.0
    cv_scores: List[float] = field(default_factory=list)
    rmse: float = 0.0
    mae: float = 0.0

    # Configuration
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    n_features: int = 0

    # Status
    status: ModelStatus = ModelStatus.TRAINING
    tags: List[str] = field(default_factory=list)

    # Comments
    description: str = ""
    created_by: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['status'] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ModelMetadata':
        """Create from dictionary"""
        if 'status' in d and isinstance(d['status'], str):
            d['status'] = ModelStatus(d['status'])
        return cls(**d)


@dataclass
class ModelArtifact:
    """Complete model artifact"""

    metadata: ModelMetadata
    model: Any  # The actual model object
    scaler: Optional[Any] = None  # Fitted scaler
    feature_selector: Optional[Any] = None  # Fitted selector
    additional_data: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    Central registry for model management.

    Features:
    - Save/load models to disk
    - Version tracking
    - Metadata storage
    - Performance comparison
    - Production model management
    """

    def __init__(self, registry_path: Optional[Union[str, Path]] = None):
        """
        Initialize model registry.

        Args:
            registry_path: Path to registry directory
        """
        if registry_path is None:
            registry_path = Path.cwd() / "model_registry"
        else:
            registry_path = Path(registry_path)

        self.registry_path = registry_path
        self.registry_path.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.registry_path / "metadata.json"
        self.models_dir = self.registry_path / "models"
        self.models_dir.mkdir(exist_ok=True)

        # Load existing metadata
        self.metadata_db: Dict[str, ModelMetadata] = {}
        self._load_metadata()

        logger.info(f"ModelRegistry initialized at {self.registry_path}")

    def _load_metadata(self):
        """Load metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)

                for model_id, meta_dict in data.items():
                    self.metadata_db[model_id] = ModelMetadata.from_dict(meta_dict)

                logger.info(f"Loaded {len(self.metadata_db)} model records")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")

    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            data = {
                model_id: meta.to_dict()
                for model_id, meta in self.metadata_db.items()
            }

            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Metadata saved")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _generate_model_id(
        self,
        model_name: str,
        model_type: str
    ) -> str:
        """Generate unique model ID"""
        timestamp = datetime.now().isoformat()
        raw_id = f"{model_name}_{model_type}_{timestamp}"

        # Hash for shorter ID
        model_id = hashlib.md5(raw_id.encode()).hexdigest()[:12]

        return model_id

    def _compute_data_hash(self, X: np.ndarray, y: np.ndarray) -> str:
        """Compute hash of training data"""
        # Sample hash (full data hash can be expensive)
        sample_data = np.concatenate([
            X.flatten()[:1000],
            y.flatten()[:1000]
        ])

        return hashlib.md5(sample_data.tobytes()).hexdigest()[:12]

    def save_model(
        self,
        model: Any,
        model_name: str,
        model_type: str,
        metadata: Optional[ModelMetadata] = None,
        scaler: Optional[Any] = None,
        feature_selector: Optional[Any] = None,
        **kwargs
    ) -> str:
        """
        Save model to registry.

        Args:
            model: Trained model
            model_name: Human-readable name
            model_type: Model type identifier
            metadata: Optional pre-filled metadata
            scaler: Optional fitted scaler
            feature_selector: Optional fitted selector
            **kwargs: Additional metadata fields

        Returns:
            Model ID
        """
        # Generate ID
        model_id = self._generate_model_id(model_name, model_type)

        # Create or update metadata
        if metadata is None:
            metadata = ModelMetadata(
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
                version="1.0.0",
                training_date=datetime.now().isoformat()
            )

        # Update with kwargs
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        # Create artifact
        artifact = ModelArtifact(
            metadata=metadata,
            model=model,
            scaler=scaler,
            feature_selector=feature_selector
        )

        # Save to disk
        model_path = self.models_dir / f"{model_id}.pkl"

        try:
            with open(model_path, 'wb') as f:
                pickle.dump(artifact, f)

            logger.info(f"Saved model {model_id} to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

        # Update metadata database
        self.metadata_db[model_id] = metadata
        self._save_metadata()

        return model_id

    def load_model(self, model_id: str) -> Optional[ModelArtifact]:
        """
        Load model from registry.

        Args:
            model_id: Model identifier

        Returns:
            ModelArtifact or None if not found
        """
        model_path = self.models_dir / f"{model_id}.pkl"

        if not model_path.exists():
            logger.error(f"Model {model_id} not found")
            return None

        try:
            with open(model_path, 'rb') as f:
                artifact = pickle.load(f)

            logger.info(f"Loaded model {model_id}")
            return artifact

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    def get_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get metadata for a model"""
        return self.metadata_db.get(model_id)

    def list_models(
        self,
        model_type: Optional[str] = None,
        status: Optional[ModelStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModelMetadata]:
        """
        List models with optional filtering.

        Args:
            model_type: Filter by model type
            status: Filter by status
            tags: Filter by tags (any match)

        Returns:
            List of matching model metadata
        """
        models = list(self.metadata_db.values())

        # Filter by type
        if model_type:
            models = [m for m in models if m.model_type == model_type]

        # Filter by status
        if status:
            models = [m for m in models if m.status == status]

        # Filter by tags
        if tags:
            models = [
                m for m in models
                if any(tag in m.tags for tag in tags)
            ]

        return models

    def update_status(
        self,
        model_id: str,
        status: ModelStatus
    ) -> bool:
        """
        Update model status.

        Args:
            model_id: Model identifier
            status: New status

        Returns:
            True if successful
        """
        if model_id not in self.metadata_db:
            return False

        self.metadata_db[model_id].status = status
        self._save_metadata()

        logger.info(f"Updated model {model_id} status to {status.value}")

        return True

    def promote_to_production(
        self,
        model_id: str,
        demote_existing: bool = True
    ) -> bool:
        """
        Promote model to production.

        Args:
            model_id: Model to promote
            demote_existing: Demote current production models

        Returns:
            True if successful
        """
        if model_id not in self.metadata_db:
            return False

        # Demote existing production models
        if demote_existing:
            for meta in self.metadata_db.values():
                if meta.status == ModelStatus.PRODUCTION:
                    meta.status = ModelStatus.ARCHIVED

        # Promote new model
        self.metadata_db[model_id].status = ModelStatus.PRODUCTION
        self._save_metadata()

        logger.info(f"Promoted model {model_id} to production")

        return True

    def get_production_model(
        self,
        model_type: Optional[str] = None
    ) -> Optional[ModelArtifact]:
        """
        Get current production model.

        Args:
            model_type: Filter by model type

        Returns:
            Production model artifact or None
        """
        production_models = self.list_models(
            model_type=model_type,
            status=ModelStatus.PRODUCTION
        )

        if not production_models:
            logger.warning(f"No production model found for type: {model_type}")
            return None

        # Return most recent
        production_models.sort(key=lambda m: m.training_date, reverse=True)
        model_id = production_models[0].model_id

        return self.load_model(model_id)

    def compare_models(
        self,
        model_ids: List[str],
        metric: str = 'test_score'
    ) -> List[Tuple[str, float]]:
        """
        Compare models by a metric.

        Args:
            model_ids: Models to compare
            metric: Metric to compare

        Returns:
            List of (model_id, score) sorted by score
        """
        comparisons = []

        for model_id in model_ids:
            meta = self.get_metadata(model_id)
            if meta:
                score = getattr(meta, metric, 0.0)
                comparisons.append((model_id, score))

        comparisons.sort(key=lambda x: x[1], reverse=True)

        return comparisons

    def delete_model(self, model_id: str) -> bool:
        """
        Delete model from registry.

        Args:
            model_id: Model to delete

        Returns:
            True if successful
        """
        if model_id not in self.metadata_db:
            return False

        # Delete file
        model_path = self.models_dir / f"{model_id}.pkl"
        if model_path.exists():
            model_path.unlink()

        # Remove from metadata
        del self.metadata_db[model_id]
        self._save_metadata()

        logger.info(f"Deleted model {model_id}")

        return True

    def get_best_model(
        self,
        model_type: Optional[str] = None,
        metric: str = 'test_score'
    ) -> Optional[Tuple[str, ModelMetadata]]:
        """
        Get best model by metric.

        Args:
            model_type: Filter by type
            metric: Metric to compare

        Returns:
            (model_id, metadata) or None
        """
        models = self.list_models(model_type=model_type)

        if not models:
            return None

        best_model = max(models, key=lambda m: getattr(m, metric, 0.0))

        return (best_model.model_id, best_model)

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        models = list(self.metadata_db.values())

        # Count by type
        type_counts = {}
        for model in models:
            type_counts[model.model_type] = type_counts.get(model.model_type, 0) + 1

        # Count by status
        status_counts = {}
        for model in models:
            status_counts[model.status.value] = status_counts.get(model.status.value, 0) + 1

        return {
            'total_models': len(models),
            'models_by_type': type_counts,
            'models_by_status': status_counts,
            'registry_path': str(self.registry_path)
        }


def create_metadata_from_results(
    model_name: str,
    model_type: str,
    train_score: float,
    test_score: float,
    hyperparameters: Dict[str, Any],
    feature_names: List[str],
    **kwargs
) -> ModelMetadata:
    """
    Helper to create metadata from training results.

    Args:
        model_name: Model name
        model_type: Model type
        train_score: Training score
        test_score: Test score
        hyperparameters: Model hyperparameters
        feature_names: Feature names
        **kwargs: Additional fields

    Returns:
        ModelMetadata object
    """
    model_id = hashlib.md5(
        f"{model_name}_{model_type}_{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    metadata = ModelMetadata(
        model_id=model_id,
        model_name=model_name,
        model_type=model_type,
        version="1.0.0",
        training_date=datetime.now().isoformat(),
        train_score=train_score,
        test_score=test_score,
        hyperparameters=hyperparameters,
        feature_names=feature_names,
        n_features=len(feature_names)
    )

    # Update with additional fields
    for key, value in kwargs.items():
        if hasattr(metadata, key):
            setattr(metadata, key, value)

    return metadata


__all__ = [
    'ModelStatus',
    'ModelMetadata',
    'ModelArtifact',
    'ModelRegistry',
    'create_metadata_from_results',
]
