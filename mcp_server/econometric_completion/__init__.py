"""
Econometric Completion Module (Agent 18)

Advanced econometric methods to complete the toolkit:
- Cointegration analysis (Engle-Granger, Johansen, VECM)
- Matching methods (PSM, kernel, Mahalanobis)
- Quantile regression
- GMM for dynamic panels (Arellano-Bond)
- Structural breaks detection (Chow, sup-F, CUSUM, Bai-Perron)

Key Modules:
- cointegration: Long-run relationships and error correction
- matching: Treatment effect estimation via matching
- quantile_regression: Effects across distribution
- gmm_panel: Dynamic panel GMM estimators
- structural_breaks: Change point detection

Integrates with:
- panel_data: Panel cointegration and GMM
- time_series: VECM and structural breaks
- causal_inference: Matching for causal effects
- ml_bridge: Hybrid approaches

Requires statsmodels for full functionality (optional dependency)
"""

from mcp_server.econometric_completion.cointegration import (
    CointegrationTest,
    CointegrationResult,
    VECMResult,
    EngleGrangerTest,
    JohansenTest,
    VectorErrorCorrectionModel,
    test_cointegration,
    check_statsmodels_available,
)
from mcp_server.econometric_completion.matching import (
    MatchingMethod,
    KernelType,
    MatchingConfig,
    MatchingResult,
    PropensityScoreMatcher,
    MahalanobisDistanceMatcher,
    estimate_treatment_effect,
)
from mcp_server.econometric_completion.quantile_regression import (
    QuantileRegressionResult,
    QuantileProcessResult,
    QuantileRegression,
    QuantileProcess,
    QuantileTreatmentEffect,
    estimate_quantile_regression,
)
from mcp_server.econometric_completion.gmm_panel import (
    GMMResult,
    DifferenceGMM,
)
from mcp_server.econometric_completion.structural_breaks import (
    BreakPoint,
    StructuralBreakResult,
    ChowTest,
    SupFTest,
    CUSUMTest,
    BaiPerronTest,
    detect_structural_breaks,
)

__all__ = [
    # Cointegration
    "CointegrationTest",
    "CointegrationResult",
    "VECMResult",
    "EngleGrangerTest",
    "JohansenTest",
    "VectorErrorCorrectionModel",
    "test_cointegration",
    "check_statsmodels_available",
    # Matching
    "MatchingMethod",
    "KernelType",
    "MatchingConfig",
    "MatchingResult",
    "PropensityScoreMatcher",
    "MahalanobisDistanceMatcher",
    "estimate_treatment_effect",
    # Quantile regression
    "QuantileRegressionResult",
    "QuantileProcessResult",
    "QuantileRegression",
    "QuantileProcess",
    "QuantileTreatmentEffect",
    "estimate_quantile_regression",
    # GMM
    "GMMResult",
    "DifferenceGMM",
    # Structural breaks
    "BreakPoint",
    "StructuralBreakResult",
    "ChowTest",
    "SupFTest",
    "CUSUMTest",
    "BaiPerronTest",
    "detect_structural_breaks",
]
