"""
ML-Econometric Bridge Module (Agent 17)

Bridges machine learning and econometric methods for NBA analytics:
- Hybrid models (two-stage, stacking, residual learning)
- Prophet time series forecasting
- Model selection and cross-validation
- Feature engineering (lags, interactions, NBA features)
- Model registry and versioning

Key Modules:
- hybrid_models: Combine ML and econometric approaches
- prophet_integration: Time series forecasting with Prophet
- model_selection: Cross-validation and hyperparameter tuning
- feature_engineering: Advanced feature creation
- model_registry: Model persistence and versioning

Integrates with:
- econometric methods: Panel data, fixed effects
- time_series: ARIMA and state space models
- simulations: Prediction evaluation
- All other modules: Feature enrichment

Requires sklearn for ML features (optional dependency)
Requires Prophet for time series forecasting (optional dependency)
"""

from mcp_server.ml_bridge.hybrid_models import (
    HybridModelConfig,
    PredictionResult,
    TwoStageModel,
    ResidualLearningModel,
    StackedEnsemble,
    ConstrainedML,
    create_hybrid_model,
    check_ml_available,
)
from mcp_server.ml_bridge.prophet_integration import (
    ProphetConfig,
    ForecastResult,
    NBAProphetForecaster,
    PlayerPerformanceForecaster,
    SeasonMode,
    create_nba_holidays,
    check_prophet_available,
)
from mcp_server.ml_bridge.model_selection import (
    CVStrategy,
    CVConfig,
    ModelPerformance,
    CrossValidator,
    HyperparameterTuner,
    ModelComparator,
    calculate_metrics,
)
from mcp_server.ml_bridge.feature_engineering import (
    FeatureConfig,
    TimeSeriesFeatureCreator,
    InteractionFeatureCreator,
    NBAFeatureCreator,
    FeatureSelector,
    FeaturePipeline,
)
from mcp_server.ml_bridge.model_registry import (
    ModelStatus,
    ModelMetadata,
    ModelArtifact,
    ModelRegistry,
    create_metadata_from_results,
)

__all__ = [
    # Hybrid models
    "HybridModelConfig",
    "PredictionResult",
    "TwoStageModel",
    "ResidualLearningModel",
    "StackedEnsemble",
    "ConstrainedML",
    "create_hybrid_model",
    "check_ml_available",
    # Prophet integration
    "ProphetConfig",
    "ForecastResult",
    "NBAProphetForecaster",
    "PlayerPerformanceForecaster",
    "SeasonMode",
    "create_nba_holidays",
    "check_prophet_available",
    # Model selection
    "CVStrategy",
    "CVConfig",
    "ModelPerformance",
    "CrossValidator",
    "HyperparameterTuner",
    "ModelComparator",
    "calculate_metrics",
    # Feature engineering
    "FeatureConfig",
    "TimeSeriesFeatureCreator",
    "InteractionFeatureCreator",
    "NBAFeatureCreator",
    "FeatureSelector",
    "FeaturePipeline",
    # Model registry
    "ModelStatus",
    "ModelMetadata",
    "ModelArtifact",
    "ModelRegistry",
    "create_metadata_from_results",
]
