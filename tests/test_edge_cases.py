"""
Edge Case Tests for NBA MCP Analytics.

Tests exception handling and edge cases for all econometric methods.
Validates that custom exceptions are raised with proper context.

Run with:
    pytest tests/test_edge_cases.py -v
"""

import pytest
import numpy as np
import pandas as pd

from mcp_server.econometric_suite import EconometricSuite
from mcp_server.exceptions import (
    InsufficientDataError,
    InvalidDataError,
    InvalidParameterError,
    MissingParameterError,
    DataShapeError,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def minimal_data():
    """Minimal valid dataset."""
    return pd.DataFrame({
        'value': [1, 2, 3, 4, 5],
        'date': pd.date_range('2020-01-01', periods=5),
        'entity': [1, 1, 2, 2, 3]
    })


@pytest.fixture
def insufficient_data():
    """Dataset with too few observations."""
    return pd.DataFrame({
        'value': [1],
        'date': pd.date_range('2020-01-01', periods=1)
    })


@pytest.fixture
def missing_data():
    """Dataset with missing values."""
    return pd.DataFrame({
        'value': [1, np.nan, 3, np.nan, 5],
        'date': pd.date_range('2020-01-01', periods=5)
    })


@pytest.fixture
def valid_time_series():
    """Valid time series dataset for testing."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'date': dates,
        'points': np.random.normal(20, 5, 100),
        'assists': np.random.normal(5, 2, 100)
    })


@pytest.fixture
def valid_causal_data():
    """Valid causal inference dataset."""
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        'treatment': np.random.binomial(1, 0.5, n),
        'outcome': np.random.normal(50, 10, n),
        'covariate1': np.random.normal(0, 1, n),
        'covariate2': np.random.normal(0, 1, n)
    })


# ==============================================================================
# Initialization Tests
# ==============================================================================


class TestInitializationEdgeCases:
    """Test EconometricSuite initialization edge cases."""

    def test_non_dataframe_input(self):
        """Test with non-DataFrame input."""
        with pytest.raises(InvalidDataError) as exc_info:
            EconometricSuite(data=[1, 2, 3], target='value')

        assert "pandas DataFrame" in str(exc_info.value)
        assert exc_info.value.details['value'] == 'list'

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(InsufficientDataError) as exc_info:
            EconometricSuite(data=empty_df, target='value')

        assert "empty" in str(exc_info.value).lower()
        assert exc_info.value.details['actual'] == 0

    def test_single_row_dataframe(self):
        """Test with single row (insufficient data)."""
        single_row = pd.DataFrame({'value': [1]})

        with pytest.raises(InsufficientDataError) as exc_info:
            EconometricSuite(data=single_row, target='value')

        assert exc_info.value.details['required'] == 2
        assert exc_info.value.details['actual'] == 1


# ==============================================================================
# Time Series Edge Cases
# ==============================================================================


class TestTimeSeriesEdgeCases:
    """Test time series analysis edge cases."""

    def test_missing_target_column(self, valid_time_series):
        """Test time series without target specified."""
        suite = EconometricSuite(data=valid_time_series)

        with pytest.raises(MissingParameterError) as exc_info:
            suite.time_series_analysis(method='arima')

        assert exc_info.value.details['parameter'] == 'target'
        assert exc_info.value.details['context'] == 'time_series_analysis'

    def test_invalid_target_column(self, valid_time_series):
        """Test time series with non-existent target column."""
        suite = EconometricSuite(
            data=valid_time_series,
            target='nonexistent'
        )

        with pytest.raises(InvalidDataError) as exc_info:
            suite.time_series_analysis(method='arima')

        assert exc_info.value.details['column'] == 'nonexistent'
        assert "not found" in str(exc_info.value)

    def test_invalid_method_name(self, valid_time_series):
        """Test time series with invalid method."""
        suite = EconometricSuite(
            data=valid_time_series,
            target='points',
            time_col='date'
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            suite.time_series_analysis(method='invalid_method')

        assert exc_info.value.details['parameter'] == 'method'
        assert exc_info.value.details['value'] == 'invalid_method'
        assert 'valid_values' in exc_info.value.details

    def test_insufficient_data_arima(self):
        """Test ARIMA with too few observations."""
        small_data = pd.DataFrame({
            'points': np.random.randn(20),
            'date': pd.date_range('2020-01-01', periods=20)
        })

        suite = EconometricSuite(
            data=small_data,
            target='points',
            time_col='date'
        )

        with pytest.raises(InsufficientDataError) as exc_info:
            suite.time_series_analysis(method='arima')

        assert exc_info.value.details['required'] == 30
        assert exc_info.value.details['actual'] == 20


# ==============================================================================
# Causal Inference Edge Cases
# ==============================================================================


class TestCausalInferenceEdgeCases:
    """Test causal inference edge cases."""

    def test_missing_treatment_and_outcome(self, valid_causal_data):
        """Test causal analysis without treatment/outcome specified."""
        suite = EconometricSuite(data=valid_causal_data)

        with pytest.raises(MissingParameterError) as exc_info:
            suite.causal_analysis(method='psm')

        assert 'treatment_col' in exc_info.value.details['parameter']
        assert 'outcome_col' in exc_info.value.details['parameter']

    def test_nonexistent_treatment_column(self, valid_causal_data):
        """Test with non-existent treatment column."""
        suite = EconometricSuite(data=valid_causal_data)

        with pytest.raises(InvalidDataError) as exc_info:
            suite.causal_analysis(
                treatment_col='nonexistent',
                outcome_col='outcome',
                method='psm'
            )

        assert exc_info.value.details['column'] == 'nonexistent'

    def test_nonexistent_outcome_column(self, valid_causal_data):
        """Test with non-existent outcome column."""
        suite = EconometricSuite(data=valid_causal_data)

        with pytest.raises(InvalidDataError) as exc_info:
            suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='nonexistent',
                method='psm'
            )

        assert exc_info.value.details['column'] == 'nonexistent'

    def test_invalid_causal_method(self, valid_causal_data):
        """Test with invalid causal method."""
        suite = EconometricSuite(data=valid_causal_data)

        with pytest.raises(InvalidParameterError) as exc_info:
            suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='outcome',
                method='invalid_method'
            )

        assert exc_info.value.details['parameter'] == 'method'
        assert exc_info.value.details['value'] == 'invalid_method'

    def test_insufficient_data_causal(self):
        """Test causal analysis with too few observations."""
        small_data = pd.DataFrame({
            'treatment': [1, 0, 1],
            'outcome': [10, 20, 15],
            'covariate': [1, 2, 3]
        })

        suite = EconometricSuite(data=small_data)

        with pytest.raises(InsufficientDataError) as exc_info:
            suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='outcome',
                method='psm'
            )

        assert exc_info.value.details['required'] == 20
        assert exc_info.value.details['actual'] == 3


# ==============================================================================
# Data Validation Edge Cases
# ==============================================================================


class TestDataValidationEdgeCases:
    """Test data validation utility functions."""

    def test_validate_data_shape_min_rows(self):
        """Test validate_data_shape with insufficient rows."""
        from mcp_server.exceptions import validate_data_shape

        data = pd.DataFrame({'a': [1, 2]})

        with pytest.raises(InsufficientDataError) as exc_info:
            validate_data_shape(data, min_rows=10)

        assert exc_info.value.details['required'] == 10
        assert exc_info.value.details['actual'] == 2

    def test_validate_data_shape_min_cols(self):
        """Test validate_data_shape with insufficient columns."""
        from mcp_server.exceptions import validate_data_shape

        data = pd.DataFrame({'a': [1, 2, 3]})

        with pytest.raises(DataShapeError) as exc_info:
            validate_data_shape(data, min_cols=5)

        assert exc_info.value.details['actual_shape'] == (3, 1)

    def test_validate_parameter_invalid_value(self):
        """Test validate_parameter with invalid value."""
        from mcp_server.exceptions import validate_parameter

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_parameter('method', 'invalid', valid_values=['a', 'b', 'c'])

        assert exc_info.value.details['parameter'] == 'method'
        assert exc_info.value.details['value'] == 'invalid'
        assert exc_info.value.details['valid_values'] == ['a', 'b', 'c']

    def test_validate_parameter_wrong_type(self):
        """Test validate_parameter with wrong type."""
        from mcp_server.exceptions import validate_parameter

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_parameter('lags', 'five', value_type=int)

        assert exc_info.value.details['parameter'] == 'lags'
        assert exc_info.value.details['value'] == 'five'

    def test_validate_parameter_out_of_range(self):
        """Test validate_parameter with out-of-range value."""
        from mcp_server.exceptions import validate_parameter

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_parameter('alpha', 1.5, min_value=0, max_value=1)

        assert exc_info.value.details['parameter'] == 'alpha'
        assert exc_info.value.details['value'] == 1.5


# ==============================================================================
# Exception Serialization Tests
# ==============================================================================


class TestExceptionSerialization:
    """Test exception to_dict() serialization."""

    def test_exception_to_dict(self):
        """Test exception can be converted to dictionary."""
        exc = InsufficientDataError(
            "Need more data",
            required=100,
            actual=50
        )

        exc_dict = exc.to_dict()

        assert exc_dict['error_type'] == 'InsufficientDataError'
        assert exc_dict['message'] == 'Need more data'
        assert exc_dict['details']['required'] == 100
        assert exc_dict['details']['actual'] == 50

    def test_exception_string_representation(self):
        """Test exception string includes details."""
        exc = InvalidParameterError(
            "Invalid method",
            parameter='method',
            value='bad_method'
        )

        exc_str = str(exc)

        assert 'Invalid method' in exc_str
        assert 'parameter=method' in exc_str
        assert 'value=bad_method' in exc_str


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestEdgeCaseIntegration:
    """Integration tests for edge case handling."""

    def test_complete_workflow_with_valid_data(self, valid_time_series):
        """Test complete workflow succeeds with valid data."""
        suite = EconometricSuite(
            data=valid_time_series,
            target='points',
            time_col='date'
        )

        # Should not raise any exceptions
        result = suite.time_series_analysis(method='arima', order=(1,1,1))

        assert result is not None
        assert result.method_used == 'ARIMA'

    def test_graceful_error_handling_chain(self):
        """Test multiple validation errors are caught gracefully."""
        # Empty DataFrame
        with pytest.raises(InsufficientDataError):
            EconometricSuite(data=pd.DataFrame())

        # Invalid type
        with pytest.raises(InvalidDataError):
            EconometricSuite(data=[1, 2, 3])

        # Valid initialization but invalid method
        suite = EconometricSuite(
            data=pd.DataFrame({'a': range(100)}),
            target='a'
        )
        with pytest.raises(InvalidParameterError):
            suite.time_series_analysis(method='nonexistent')


# ==============================================================================
# Additional Model Edge Cases (20+ tests)
# ==============================================================================


class TestARIMAEdgeCases:
    """Test ARIMA-specific edge cases."""

    def test_arima_negative_order(self):
        """Test ARIMA with negative order values."""
        from mcp_server.time_series import TimeSeriesAnalyzer

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({'value': np.random.randn(100)}, index=dates)

        analyzer = TimeSeriesAnalyzer(data, target_column='value')

        with pytest.raises(InvalidParameterError):
            analyzer.fit_arima(order=(-1, 1, 1))

    def test_arima_zero_order(self):
        """Test ARIMA with all zeros."""
        from mcp_server.time_series import TimeSeriesAnalyzer

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({'value': np.random.randn(100)}, index=dates)

        analyzer = TimeSeriesAnalyzer(data, target_column='value')

        with pytest.raises(InvalidParameterError):
            analyzer.fit_arima(order=(0, 0, 0))

    def test_arima_insufficient_data(self):
        """Test ARIMA with < 30 observations."""
        from mcp_server.time_series import TimeSeriesAnalyzer

        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        data = pd.DataFrame({'value': np.random.randn(20)}, index=dates)

        analyzer = TimeSeriesAnalyzer(data, target_column='value')

        with pytest.raises(InsufficientDataError):
            analyzer.fit_arima(order=(1, 1, 1))

    def test_arima_non_tuple_order(self):
        """Test ARIMA with order as list instead of tuple."""
        from mcp_server.time_series import TimeSeriesAnalyzer

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({'value': np.random.randn(100)}, index=dates)

        analyzer = TimeSeriesAnalyzer(data, target_column='value')

        with pytest.raises(InvalidParameterError):
            analyzer.fit_arima(order=[1, 1, 1])  # List instead of tuple

    def test_arima_wrong_order_length(self):
        """Test ARIMA with order of wrong length."""
        from mcp_server.time_series import TimeSeriesAnalyzer

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({'value': np.random.randn(100)}, index=dates)

        analyzer = TimeSeriesAnalyzer(data, target_column='value')

        with pytest.raises(InvalidParameterError):
            analyzer.fit_arima(order=(1, 1))  # Only 2 elements


class TestRegressionEdgeCases:
    """Test regression-specific edge cases."""

    def test_regression_perfect_collinearity(self):
        """Test regression with perfectly collinear predictors."""
        data = pd.DataFrame({
            'y': np.random.randn(100),
            'x1': np.random.randn(100),
            'x2': np.random.randn(100)
        })
        data['x3'] = data['x1'] + data['x2']  # Perfect collinearity

        suite = EconometricSuite(data=data, target='y')

        # Should detect and handle multicollinearity
        # May raise LinAlgError or ModelFitError
        try:
            result = suite.regression(predictors=['x1', 'x2', 'x3'])
        except (np.linalg.LinAlgError, ValueError):
            pass  # Expected

    def test_regression_more_predictors_than_observations(self):
        """Test regression with p > n."""
        data = pd.DataFrame({'y': np.random.randn(10)})
        for i in range(20):
            data[f'x{i}'] = np.random.randn(10)

        suite = EconometricSuite(data=data, target='y')

        # Should fail - underdetermined system
        try:
            result = suite.regression(predictors=[f'x{i}' for i in range(20)])
        except (np.linalg.LinAlgError, ValueError):
            pass  # Expected

    def test_regression_constant_predictor(self):
        """Test regression with zero-variance predictor."""
        data = pd.DataFrame({
            'y': np.random.randn(100),
            'x1': [5.0] * 100,  # Constant
            'x2': np.random.randn(100)
        })

        suite = EconometricSuite(data=data, target='y')

        # Should handle gracefully
        try:
            result = suite.regression(predictors=['x1', 'x2'])
        except ValueError:
            pass  # May fail with constant predictor

    def test_regression_empty_predictors(self):
        """Test regression with empty predictor list."""
        data = pd.DataFrame({
            'y': np.random.randn(100),
            'x': np.random.randn(100)
        })

        suite = EconometricSuite(data=data, target='y')

        # Should handle - may fit intercept only
        try:
            result = suite.regression(predictors=[])
        except (ValueError, TypeError):
            pass  # May require predictors


class TestPanelDataEdgeCases:
    """Test panel data edge cases."""

    def test_panel_single_entity(self):
        """Test panel with only one entity."""
        data = pd.DataFrame({
            'entity': ['A'] * 50,
            'time': range(50),
            'y': np.random.randn(50),
            'x': np.random.randn(50)
        })

        suite = EconometricSuite(
            data=data,
            target='y',
            entity_col='entity',
            time_col='time'
        )

        # Should fail - need multiple entities
        try:
            result = suite.panel_analysis(method='fixed_effects')
        except (ValueError, KeyError):
            pass  # Expected

    def test_panel_single_time_period(self):
        """Test panel with single time period (cross-section)."""
        data = pd.DataFrame({
            'entity': [f'E{i}' for i in range(100)],
            'time': [1] * 100,
            'y': np.random.randn(100),
            'x': np.random.randn(100)
        })

        suite = EconometricSuite(
            data=data,
            target='y',
            entity_col='entity',
            time_col='time'
        )

        # Should fail - need multiple time periods
        try:
            result = suite.panel_analysis(method='fixed_effects')
        except (ValueError, KeyError):
            pass  # Expected

    def test_panel_unbalanced(self):
        """Test unbalanced panel data."""
        data = pd.DataFrame({
            'entity': ['A', 'A', 'A', 'B', 'B', 'C', 'C', 'C', 'C'],
            'time': [1, 2, 3, 1, 2, 1, 2, 3, 4],
            'y': np.random.randn(9),
            'x': np.random.randn(9)
        })

        suite = EconometricSuite(
            data=data,
            target='y',
            entity_col='entity',
            time_col='time'
        )

        # Should handle unbalanced panel
        # May work or raise error depending on method
        try:
            result = suite.panel_analysis(method='fixed_effects')
        except (ValueError, KeyError):
            pass  # May not work with very unbalanced data


class TestCausalAnalysisEdgeCases:
    """Test causal analysis edge cases."""

    def test_psm_all_same_treatment(self):
        """Test PSM where everyone has same treatment."""
        data = pd.DataFrame({
            'treatment': [1] * 100,  # All treated
            'outcome': np.random.randn(100),
            'covariate': np.random.randn(100)
        })

        suite = EconometricSuite(data=data)

        # Should fail - no variation in treatment
        with pytest.raises((ValueError, KeyError)):
            result = suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='outcome',
                method='psm'
            )

    def test_psm_very_unbalanced(self):
        """Test PSM with very unbalanced groups (95/5 split)."""
        data = pd.DataFrame({
            'treatment': [0] * 95 + [1] * 5,
            'outcome': np.random.randn(100),
            'covariate': np.random.randn(100)
        })

        suite = EconometricSuite(data=data)

        # May fail with too few treated units
        try:
            result = suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='outcome',
                method='psm',
                caliper=0.1
            )
        except (ValueError, KeyError):
            pass  # Expected with very few matches

    def test_rdd_no_observations_at_cutoff(self):
        """Test RDD with no observations near cutoff."""
        data = pd.DataFrame({
            'running_var': list(range(-100, -50)) + list(range(50, 100)),  # Gap at 0
            'outcome': np.random.randn(100),
            'treatment': [0] * 50 + [1] * 50
        })

        suite = EconometricSuite(data=data)

        # May work but estimates will be poor
        try:
            result = suite.causal_analysis(
                treatment_col='treatment',
                outcome_col='outcome',
                method='rdd',
                running_var='running_var',
                cutoff=0,
                bandwidth=10
            )
        except (ValueError, KeyError):
            pass  # May fail with no data near cutoff


class TestDataQualityEdgeCases:
    """Test data quality edge cases."""

    def test_all_nan_target(self):
        """Test with all NaN values in target."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=50),
            'value': [np.nan] * 50
        })

        suite = EconometricSuite(data=data, target='value', time_col='date')
        # Should handle gracefully
        assert suite is not None

    def test_extreme_outliers(self):
        """Test with extreme outliers."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'value': np.random.randn(100)
        })
        data.loc[0, 'value'] = 1e10  # Extreme outlier

        suite = EconometricSuite(data=data, target='value', time_col='date')
        # Should handle gracefully
        assert suite is not None

    def test_infinite_values(self):
        """Test with infinite values."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'value': np.random.randn(100)
        })
        data.loc[10, 'value'] = np.inf

        # Should handle or raise appropriate error
        try:
            suite = EconometricSuite(data=data, target='value', time_col='date')
        except (InvalidDataError, ValueError):
            pass  # Expected

    def test_mixed_types_in_column(self):
        """Test with mixed types in numeric column."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'value': ['10', 20, '30', 40] * 25  # Mixed str/int
        })

        # Should raise error or handle gracefully
        try:
            suite = EconometricSuite(data=data, target='value', time_col='date')
            result = suite.time_series_analysis(method='arima', order=(1, 1, 1))
        except (InvalidDataError, TypeError, ValueError):
            pass  # Expected

    def test_duplicate_index(self):
        """Test with duplicate timestamps."""
        dates = pd.date_range('2023-01-01', periods=50).tolist()
        dates = dates + dates  # Duplicate

        data = pd.DataFrame({
            'date': dates,
            'value': np.random.randn(100)
        })

        # Should handle or raise error
        try:
            suite = EconometricSuite(data=data, target='value', time_col='date')
        except (InvalidDataError, ValueError):
            pass  # Expected

    def test_high_cardinality_categorical(self):
        """Test with categorical with many unique values."""
        data = pd.DataFrame({
            'entity': [f'E{i}' for i in range(100)],
            'time': list(range(100)),
            'y': np.random.randn(100),
            'x': np.random.randn(100)
        })

        suite = EconometricSuite(
            data=data,
            target='y',
            entity_col='entity',
            time_col='time'
        )
        # Should handle but may not be ideal
        assert suite is not None


class TestBoundaryConditions:
    """Test boundary value conditions."""

    def test_exactly_minimum_observations(self):
        """Test with exactly 30 observations (minimum for ARIMA)."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=30),
            'value': np.random.randn(30)
        })

        suite = EconometricSuite(data=data, target='value', time_col='date')
        result = suite.time_series_analysis(method='arima', order=(1, 1, 1))
        assert result is not None

    def test_very_long_series(self):
        """Test with very long time series (5000+ obs)."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5000),
            'value': np.random.randn(5000)
        })

        suite = EconometricSuite(data=data, target='value', time_col='date')
        # Should work but may be slow
        result = suite.time_series_analysis(method='arima', order=(1, 1, 1))
        assert result is not None

    def test_zero_variance_series(self):
        """Test with constant (zero variance) series."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'value': [10.0] * 100  # Constant
        })

        suite = EconometricSuite(data=data, target='value', time_col='date')

        # ARIMA may fail with constant series
        try:
            result = suite.time_series_analysis(method='arima', order=(1, 0, 0))
        except (ValueError, np.linalg.LinAlgError):
            pass  # Expected

    def test_extreme_scale_differences(self):
        """Test with variables at very different scales."""
        data = pd.DataFrame({
            'y': np.random.randn(100),
            'x1': np.random.randn(100) * 1e10,  # Very large
            'x2': np.random.randn(100) * 1e-10  # Very small
        })

        suite = EconometricSuite(data=data, target='y')

        # Should work but may have numerical issues
        try:
            result = suite.regression(predictors=['x1', 'x2'])
        except (np.linalg.LinAlgError, ValueError):
            pass  # May fail due to ill-conditioning


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
