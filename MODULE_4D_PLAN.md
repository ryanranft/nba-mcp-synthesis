# Module 4D: Econometric Suite - Implementation Plan

**Module**: econometric_suite.py
**Purpose**: Unified interface for all econometric methods with auto-selection
**Status**: ✅ **COMPLETED**
**Target**: ~1000 LOC + 25 tests
**Actual**: 1,000 LOC + 31 tests (exceeded target!)

---

## ✅ IMPLEMENTATION SUMMARY

**Completion Date**: October 26, 2025
**Git Commit**: 51f0d3bc
**Test Pass Rate**: 100% (31/31 tests)
**Documentation**: ECONOMETRIC_SUITE.md (comprehensive)

**Achievements**:
- ✅ All 6 econometric modules integrated
- ✅ Auto-detection working for all data structures
- ✅ Model comparison framework functional
- ✅ Model averaging with multiple weight schemes
- ✅ MLflow integration complete
- ✅ 100% test coverage
- ✅ Comprehensive documentation with examples

---

## Overview

The EconometricSuite provides a high-level interface that:
1. Auto-selects appropriate methods based on data structure
2. Provides unified API across all econometric modules
3. Enables model averaging and ensemble approaches
4. Offers integrated diagnostics and validation
5. Tracks all experiments via MLflow

## Architecture

### Core Components

1. **DataClassifier**: Analyzes data structure and recommends methods
2. **EconometricSuite**: Main unified interface
3. **SuiteResult**: Comprehensive results container
4. **ModelAverager**: Combines predictions across methods
5. **DiagnosticsDashboard**: Integrated validation metrics

### Data Type Detection

```python
class DataStructure(Enum):
    CROSS_SECTION = "cross_section"      # Single time point
    TIME_SERIES = "time_series"          # Single entity over time
    PANEL = "panel"                       # Multiple entities over time
    EVENT_HISTORY = "event_history"      # Duration/survival data
    TREATMENT_OUTCOME = "treatment_outcome"  # Causal inference
```

### Auto-Selection Logic

**Decision Tree**:

```
1. Check for duration/event columns
   → survival_analysis methods

2. Check for treatment/outcome structure
   → causal_inference methods

3. Check temporal structure:
   a. No time index → cross_section
   b. Single entity → time_series or advanced_time_series
   c. Multiple entities → panel_data

4. Check for Bayesian priors requested
   → bayesian methods
```

## Implementation Plan

### Phase 1: Core Infrastructure (300 LOC)

**Files**:
- `mcp_server/econometric_suite.py` (create)

**Components**:
1. DataClassifier
   - `detect_structure()` - Identify data type
   - `recommend_methods()` - Suggest appropriate analyses

2. SuiteResult (dataclass)
   - Stores results from multiple methods
   - Comparison metrics
   - Model rankings

### Phase 2: Unified Interface (400 LOC)

**EconometricSuite Class**:

```python
class EconometricSuite:
    def __init__(
        self,
        data: pd.DataFrame,
        target: Optional[str] = None,
        entity_col: Optional[str] = None,
        time_col: Optional[str] = None,
        mlflow_experiment: Optional[str] = None
    ):
        """Initialize suite with data."""
        pass

    # === Auto Analysis ===
    def analyze(
        self,
        method: str = 'auto',
        **kwargs
    ) -> SuiteResult:
        """
        Auto-select and run analysis.

        method='auto': Auto-detect best method
        method='all': Run all applicable methods
        method='ensemble': Model averaging
        """
        pass

    # === Method Access ===
    def time_series_analysis(self, **kwargs):
        """Access time series methods."""
        pass

    def panel_analysis(self, **kwargs):
        """Access panel data methods."""
        pass

    def causal_analysis(
        self,
        treatment_col: str,
        outcome_col: str,
        **kwargs
    ):
        """Access causal inference methods."""
        pass

    def survival_analysis(
        self,
        duration_col: str,
        event_col: str,
        **kwargs
    ):
        """Access survival methods."""
        pass

    def bayesian_analysis(self, **kwargs):
        """Access Bayesian methods."""
        pass

    def advanced_time_series_analysis(self, **kwargs):
        """Access advanced time series methods."""
        pass

    # === Model Comparison ===
    def compare_methods(
        self,
        methods: List[str],
        metric: str = 'aic'
    ) -> pd.DataFrame:
        """Compare multiple methods."""
        pass

    def ensemble_predict(
        self,
        methods: List[str],
        weights: str = 'auto'
    ):
        """Ensemble predictions."""
        pass
```

### Phase 3: Model Averaging (200 LOC)

**ModelAverager Class**:

```python
class ModelAverager:
    """
    Combine predictions from multiple econometric models.
    """

    def average(
        self,
        predictions: Dict[str, np.ndarray],
        weights: Union[str, Dict[str, float]] = 'equal'
    ) -> np.ndarray:
        """
        Average predictions with optional weighting.

        weights options:
        - 'equal': Simple average
        - 'aic': Weight by AIC
        - 'bic': Weight by BIC
        - 'performance': Weight by validation performance
        - dict: Custom weights
        """
        pass
```

### Phase 4: Integrated Diagnostics (100 LOC)

**DiagnosticsDashboard**:

```python
def diagnostic_summary(suite_result: SuiteResult) -> Dict[str, Any]:
    """
    Generate comprehensive diagnostics across methods.

    Returns:
    - Model comparison table
    - Information criteria
    - Prediction accuracy
    - Convergence status
    - Warnings and issues
    """
    pass
```

## Usage Examples

### Example 1: Auto Analysis

```python
from mcp_server.econometric_suite import EconometricSuite

# Load data
df = pd.read_csv('player_stats.csv')

# Auto-detect and analyze
suite = EconometricSuite(
    data=df,
    target='points_per_game',
    entity_col='player_id',
    time_col='season'
)

# Auto-select best method
result = suite.analyze(method='auto')

print(result.summary())
# Output:
# Data Structure: Panel (500 players, 10 seasons)
# Recommended Method: Panel Fixed Effects
# Model: FixedEffectsResult(...)
# AIC: 1234.5
# R²: 0.67
```

### Example 2: Compare Multiple Methods

```python
# Run multiple panel methods
results = suite.compare_methods(
    methods=['fixed_effects', 'random_effects', 'pooled_ols'],
    metric='bic'
)

print(results)
# Output:
#                  AIC      BIC   R²     Best
# fixed_effects   1200   1250  0.70    ✓
# random_effects  1220   1260  0.68
# pooled_ols      1350   1380  0.55
```

### Example 3: Ensemble Prediction

```python
# Ensemble across methods
prediction = suite.ensemble_predict(
    methods=['fixed_effects', 'random_effects', 'bayesian_hierarchical'],
    weights='aic'  # AIC-weighted average
)
```

### Example 4: Causal Analysis Workflow

```python
# Automatically detect treatment structure
suite = EconometricSuite(
    data=coaching_changes_df,
    target='wins'
)

result = suite.causal_analysis(
    treatment_col='new_coach',
    outcome_col='wins',
    method='auto'  # Will try IV, PSM, or synthetic control
)

print(result.treatment_effect)
print(result.diagnostic_summary())
```

### Example 5: Survival Analysis Pipeline

```python
suite = EconometricSuite(
    data=player_careers_df,
    mlflow_experiment='career_longevity'
)

result = suite.survival_analysis(
    duration_col='career_years',
    event_col='retired',
    method='all'  # Compare Cox, Weibull, log-normal
)

# Model comparison
comparison = suite.compare_methods(
    methods=['cox', 'weibull', 'lognormal'],
    metric='concordance_index'
)
```

## Test Plan (25 tests)

### Data Classification (5 tests)
- test_detect_cross_section
- test_detect_time_series
- test_detect_panel
- test_detect_survival
- test_detect_treatment_outcome

### Auto-Selection (5 tests)
- test_auto_select_time_series
- test_auto_select_panel
- test_auto_select_causal
- test_auto_select_survival
- test_auto_select_bayesian

### Method Access (6 tests)
- test_time_series_access
- test_panel_access
- test_causal_access
- test_survival_access
- test_bayesian_access
- test_advanced_time_series_access

### Model Averaging (4 tests)
- test_equal_weights
- test_aic_weights
- test_performance_weights
- test_custom_weights

### Integration (5 tests)
- test_compare_methods
- test_diagnostic_summary
- test_mlflow_tracking
- test_ensemble_predict
- test_end_to_end_workflow

## Data Structures

### SuiteResult

```python
@dataclass
class SuiteResult:
    """Comprehensive results from econometric suite."""

    data_structure: DataStructure
    method_used: str
    result: Any  # Specific result object
    model: Any   # Fitted model

    # Diagnostics
    aic: Optional[float] = None
    bic: Optional[float] = None
    log_likelihood: Optional[float] = None
    r_squared: Optional[float] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate summary report."""
        pass

    def plot(self):
        """Visualize results."""
        pass
```

## Integration with Existing Modules

### Time Series Integration

```python
def time_series_analysis(self, **kwargs):
    from mcp_server.time_series import TimeSeriesAnalyzer

    analyzer = TimeSeriesAnalyzer(self.data[self.target])

    if kwargs.get('method') == 'auto':
        # Auto-select: ARIMA, VAR, or seasonal decomposition
        pass

    return analyzer
```

### Panel Data Integration

```python
def panel_analysis(self, **kwargs):
    from mcp_server.panel_data import PanelDataAnalyzer

    analyzer = PanelDataAnalyzer(
        self.data,
        entity_col=self.entity_col,
        time_col=self.time_col
    )

    return analyzer
```

### Similar for Bayesian, Causal, Survival, Advanced Time Series

## MLflow Integration

```python
def analyze(self, method='auto', **kwargs):
    if self.mlflow_experiment:
        with mlflow.start_run():
            # Log data characteristics
            mlflow.log_params({
                'data_structure': self.data_structure,
                'n_obs': len(self.data),
                'n_entities': self._n_entities,
                'n_periods': self._n_periods,
                'method': method,
            })

            # Run analysis
            result = self._run_analysis(method, **kwargs)

            # Log results
            mlflow.log_metrics({
                'aic': result.aic,
                'bic': result.bic,
                'r_squared': result.r_squared,
            })

            return result
```

## Dependencies

All dependencies already installed from previous modules:
- statsmodels (time series, panel)
- pmdarima (auto ARIMA)
- linearmodels (panel IV)
- pymc (Bayesian)
- dowhy (causal inference)
- lifelines (survival)
- scikit-survival (ML survival)
- mlflow (experiment tracking)

No new dependencies required.

## Success Criteria

1. ✅ Auto-detection works for all data types
2. ✅ All 6 module types accessible via unified API
3. ✅ Model comparison functional
4. ✅ Ensemble predictions working
5. ✅ 25+ tests passing
6. ✅ MLflow integration complete
7. ✅ Documentation with examples

## Timeline

- **Phase 1** (Core Infrastructure): 1 hour
- **Phase 2** (Unified Interface): 2 hours
- **Phase 3** (Model Averaging): 1 hour
- **Phase 4** (Diagnostics): 1 hour
- **Testing**: 2 hours
- **Documentation**: 1 hour

**Total Estimate**: 8 hours

## Deliverables

1. `mcp_server/econometric_suite.py` (~1000 LOC)
2. `tests/test_econometric_suite.py` (~500 LOC, 25 tests)
3. `ECONOMETRIC_SUITE.md` (comprehensive documentation)
4. Integration examples across all modules
5. Git commit with all changes

---

## Post-Implementation Enhancements

With Module 4D complete, the following enhancements would extend its capabilities. See **AGENT8_FUTURE_ROADMAP.md** for comprehensive details.

### Phase 1: Expand Method Coverage (2 weeks)
**Goal**: Add more methods from each module to Suite interface

**Additions**:
- **Causal Inference**: Fuzzy RDD, kernel matching, radius matching
- **Time Series**: ARIMAX, VARMAX, STL decomposition
- **Survival**: Fine-Gray subdistribution hazards, cure models
- **Advanced TS**: Multiple factor orders, regime-specific diagnostics

**Estimate**: 400 LOC, 15 tests

### Phase 2: Smart Covariate Selection (1 week)
**Goal**: Automatic feature selection for econometric models

**Features**:
- LASSO/Ridge for covariate selection
- Instrument validity checking (weak instrument detection)
- Multicollinearity detection and resolution
- Forward/backward selection for panel data

**Estimate**: 200 LOC, 8 tests

### Phase 3: Cross-Validation Framework (1 week)
**Goal**: Model validation with appropriate CV schemes

**Features**:
- Time series cross-validation (expanding window, rolling window)
- Panel data cross-validation (entity-based folds)
- Survival analysis cross-validation (C-index optimization)
- Model selection via CV

**Estimate**: 250 LOC, 10 tests

### Phase 4: Visualization Dashboard (2 weeks)
**Goal**: Interactive visualizations for all methods

**Features**:
- Plotly-based interactive diagnostics
- Residual plots, Q-Q plots, ACF/PACF
- Survival curves, hazard plots
- Factor loadings visualization
- Regime probability tracking

**Estimate**: 500 LOC, 5 tests

### Phase 5: Pipeline Builder (1 week)
**Goal**: Chain multiple analyses into workflows

**Features**:
- Sequential analysis pipelines
- Conditional branching based on diagnostics
- Result caching and reuse
- Pipeline serialization

**Estimate**: 300 LOC, 8 tests

### Phase 6: Automated Reporting (1 week)
**Goal**: Generate professional reports automatically

**Features**:
- LaTeX report generation
- HTML report generation
- Automatic table and figure creation
- Executive summary generation

**Estimate**: 250 LOC, 5 tests

---

## Integration Success Metrics

| Criterion | Status |
|-----------|--------|
| All 6 modules accessible | ✅ Yes |
| Auto-detection working | ✅ Yes |
| Model comparison functional | ✅ Yes |
| Model averaging working | ✅ Yes |
| MLflow integration | ✅ Yes |
| 25+ tests | ✅ Yes (31 tests) |
| Documentation | ✅ Yes (comprehensive) |
| 100% test pass rate | ✅ Yes |

---

## Completed Steps

1. ✅ Implement DataClassifier and data structure detection
2. ✅ Create EconometricSuite class with method access
3. ✅ Implement ModelAverager for ensemble predictions
4. ✅ Add integrated diagnostics
5. ✅ Write comprehensive tests (31 tests, exceeded target)
6. ✅ Create documentation with real-world examples
7. ✅ Commit Module 4D (Commit 51f0d3bc)

---

**Status**: ✅ Complete - Production Ready
**Complexity**: Medium (integration layer achieved)
**Risk Level**: Low (all existing modules tested)
**Next Steps**: See AGENT8_FUTURE_ROADMAP.md for enhancement options
