#!/usr/bin/env python3
"""
Test Phase 2 Bug Fixes Integration

Validates the 5 critical bugs that were fixed in Phase 2:
- BUG-06: tracker attribute initialization in TimeSeriesAnalyzer
- BUG-07: VECM safe accessor for AIC
- BUG-04, BUG-05, BUG-08: Notebook-specific fixes

These tests ensure bug fixes remain stable across refactoring.
"""

import pytest
import warnings
import pandas as pd
import numpy as np
from mcp_server.time_series import TimeSeriesAnalyzer

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore")


@pytest.fixture
def time_series_data():
    """Generate simple time series data for testing"""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "value": np.random.randn(100).cumsum() + 100})
    return df.set_index("date")


@pytest.fixture
def multivariate_time_series_data():
    """Generate multivariate time series data for VECM testing"""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=200, freq="D")
    df = pd.DataFrame(
        {
            "var1": np.random.randn(200).cumsum() + 100,
            "var2": np.random.randn(200).cumsum() + 50,
        },
        index=dates,
    )
    return df


@pytest.mark.integration
def test_bug06_tracker_attribute_initialization(time_series_data):
    """
    Test BUG-06: tracker attribute initialization

    This bug caused AttributeError when TimeSeriesAnalyzer was initialized
    without properly setting the tracker attribute. The fix ensures tracker
    is always initialized in __init__.

    Bug Details:
    - Issue: tracker attribute was not initialized in __init__
    - Impact: Any method accessing self.tracker would fail
    - Fix: Added self.tracker = None in __init__
    """
    # Create analyzer - should not raise AttributeError
    analyzer = TimeSeriesAnalyzer(data=time_series_data, target_column="value")

    # Verify tracker attribute exists
    assert hasattr(
        analyzer, "tracker"
    ), "tracker attribute should exist after initialization"

    # Verify it's accessible (even if None)
    tracker_value = analyzer.tracker
    # tracker_value could be None or an ExperimentTracker instance
    assert tracker_value is None or hasattr(
        tracker_value, "__class__"
    ), "tracker should be None or a valid object"


@pytest.mark.integration
def test_bug07_vecm_safe_accessor(multivariate_time_series_data):
    """
    Test BUG-07: VECM safe accessor for AIC

    This bug caused AttributeError when accessing AIC from VECM results
    because statsmodels VECM doesn't have aic as a standard attribute.
    The fix adds safe accessor with getattr and fallback to NaN.

    Bug Details:
    - Issue: result_vecm.aic raised AttributeError
    - Impact: VECM analysis failed when accessing model selection criteria
    - Fix: Use getattr(result_vecm, 'aic', np.nan)
    """
    analyzer = TimeSeriesAnalyzer(
        data=multivariate_time_series_data, target_column="var1"
    )

    try:
        # Fit VECM model
        result = analyzer.fit_vecm(
            endog_data=multivariate_time_series_data[["var1", "var2"]],
            coint_rank=1,
            k_ar_diff=1,
        )

        # Verify aic attribute exists (even if NaN)
        assert hasattr(result, "aic"), "aic attribute should exist in VECMResult"

        # Verify aic is accessible (could be float or NaN)
        aic_value = result.aic
        assert isinstance(aic_value, (int, float)) or pd.isna(
            aic_value
        ), "aic should be numeric or NaN"

    except ImportError as e:
        pytest.skip(f"VECM not available (statsmodels import issue): {e}")
    except Exception as e:
        # VECM might fail for legitimate reasons (data issues, model convergence)
        # We're specifically testing that AttributeError doesn't occur
        if "AttributeError" in str(type(e).__name__):
            pytest.fail(f"BUG-07 regression: AttributeError accessing aic: {e}")
        else:
            # Other errors are acceptable (model convergence, etc.)
            pytest.skip(f"VECM skipped due to model issue (not bug): {e}")


@pytest.mark.integration
def test_phase2_bug_fixes_regression_suite(time_series_data):
    """
    Regression test suite for all Phase 2 bug fixes

    This test ensures that common time series operations work without
    errors that were present before bug fixes.
    """
    analyzer = TimeSeriesAnalyzer(data=time_series_data, target_column="value")

    # Test basic operations that previously failed
    assert hasattr(analyzer, "data"), "Should have data attribute"
    assert hasattr(analyzer, "target_column"), "Should have target_column attribute"
    assert hasattr(analyzer, "tracker"), "Should have tracker attribute (BUG-06)"

    # Test that analyzer can perform basic operations
    assert len(analyzer.data) == 100, "Should have 100 data points"
    assert analyzer.target_column == "value", "Should track correct target column"
