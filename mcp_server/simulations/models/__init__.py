"""
Advanced Simulation Models (Agent 11)

Provides enhanced ML models for NBA game simulation including
ensemble methods, neural networks, and advanced feature engineering.
"""

from .ensemble import EnsembleSimulator
from .neural_networks import (
    TrainingMetrics,
    TrainingHistory,
    MLPWrapper,
    TORCH_AVAILABLE
)
from .feature_engineering import (
    FeatureSet,
    TimeBasedFeatureGenerator,
    InteractionFeatureGenerator,
    DomainFeatureGenerator,
    FeatureScaler,
    FeatureSelector
)

__all__ = [
    'EnsembleSimulator',
    'TrainingMetrics',
    'TrainingHistory',
    'MLPWrapper',
    'TORCH_AVAILABLE',
    'FeatureSet',
    'TimeBasedFeatureGenerator',
    'InteractionFeatureGenerator',
    'DomainFeatureGenerator',
    'FeatureScaler',
    'FeatureSelector'
]

# Conditionally export PyTorch models if available
if TORCH_AVAILABLE:
    from .neural_networks import FeedforwardNN, LSTMPredictor, PyTorchWrapper
    __all__.extend(['FeedforwardNN', 'LSTMPredictor', 'PyTorchWrapper'])
