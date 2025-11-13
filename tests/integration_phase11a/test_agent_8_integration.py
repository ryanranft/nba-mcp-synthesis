"""
Integration Tests for Agent 8

Tests econometric analysis integration with data validation and monitoring.

Agent Covered:
- Agent 8: Advanced Analytics (Econometric Methods)
"""

import pytest
import pandas as pd
import numpy as np


@pytest.mark.agent_8
class TestEconometricDataValidationIntegration:
    """Test econometric methods integrate with data validation"""

    def test_time_series_with_validation(self, time_series_data, test_helper):
        """Test time series analysis with data validation"""
        from mcp_server.time_series import TimeSeriesAnalyzer

        # Validate data before analysis
        test_helper.assert_data_quality(
            pd.DataFrame({"points": time_series_data}), min_rows=100
        )

        # Run time series analysis
        analyzer = TimeSeriesAnalyzer(
            data=pd.DataFrame({"points": time_series_data.head(200)}),
            target_column="points",
        )

        # Verify analyzer initialized
        assert analyzer.data is not None
        assert analyzer.target_column == "points"

    def test_panel_data_with_validation(self, panel_data, test_helper):
        """Test panel data analysis with validation"""
        from mcp_server.panel_data import PanelDataAnalyzer

        # Validate required columns
        required_cols = ["player_id", "period", "points"]
        test_helper.assert_no_nulls(panel_data, required_cols)

        # Run panel data analysis
        analyzer = PanelDataAnalyzer(
            data=panel_data.head(500),
            entity_col="player_id",
            time_col="period",
            target_col="points",
        )

        # Verify analyzer initialized
        assert analyzer.data is not None
        assert analyzer.entity_col == "player_id"


@pytest.mark.agent_8
class TestEconometricMonitoringIntegration:
    """Test econometric methods integrate with monitoring"""

    def test_time_series_with_profiling(self, time_series_data):
        """Test time series analysis is profiled"""
        from mcp_server.time_series import TimeSeriesAnalyzer
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        @profile
        def run_time_series_analysis():
            analyzer = TimeSeriesAnalyzer(
                data=pd.DataFrame({"points": time_series_data.head(100)}),
                target_column="points",
            )
            return analyzer

        # Execute
        result = run_time_series_analysis()

        # Verify profiling worked
        stats = profiler.get_summary()
        assert stats["total_calls"] >= 1
        assert result is not None

    def test_panel_data_with_profiling(self, panel_data):
        """Test panel data analysis is profiled"""
        from mcp_server.panel_data import PanelDataAnalyzer
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        @profile
        def run_panel_analysis():
            analyzer = PanelDataAnalyzer(
                data=panel_data.head(200),
                entity_col="player_id",
                time_col="period",
                target_col="points",
            )
            return analyzer

        # Execute
        result = run_panel_analysis()

        # Verify profiling worked
        stats = profiler.get_summary()
        assert stats["total_calls"] >= 1
        assert result is not None


@pytest.mark.agent_8
@pytest.mark.performance
class TestEconometricPerformance:
    """Test econometric methods performance"""

    def test_time_series_initialization_performance(
        self, time_series_data, test_helper
    ):
        """Test time series analyzer initialization performance"""
        from mcp_server.time_series import TimeSeriesAnalyzer

        # Measure performance
        def init_analyzer():
            return TimeSeriesAnalyzer(
                data=pd.DataFrame({"points": time_series_data.head(500)}),
                target_column="points",
            )

        analyzer, exec_time = test_helper.measure_execution_time(init_analyzer)

        # Should initialize quickly (<1 second)
        test_helper.assert_performance_acceptable(exec_time, threshold_ms=1000)
        assert analyzer is not None

    def test_panel_data_initialization_performance(self, panel_data, test_helper):
        """Test panel data analyzer initialization performance"""
        from mcp_server.panel_data import PanelDataAnalyzer

        # Measure performance
        def init_analyzer():
            return PanelDataAnalyzer(
                data=panel_data.head(1000),
                entity_col="player_id",
                time_col="period",
                target_col="points",
            )

        analyzer, exec_time = test_helper.measure_execution_time(init_analyzer)

        # Should initialize quickly (<2 seconds)
        test_helper.assert_performance_acceptable(exec_time, threshold_ms=2000)
        assert analyzer is not None


@pytest.mark.agent_8
class TestEconometricDataPipeline:
    """Test econometric methods in data pipelines"""

    def test_econometric_pipeline_with_preprocessing(self, sample_player_data):
        """Test econometric analysis after data preprocessing"""
        from mcp_server.time_series import TimeSeriesAnalyzer

        # Step 1: Preprocess data
        processed = sample_player_data.copy()
        processed = processed.dropna(subset=["points", "game_date"])
        processed = processed.sort_values("game_date")

        # Step 2: Create time series
        ts_data = processed.groupby("game_date")["points"].mean().head(200)

        # Step 3: Run analysis
        analyzer = TimeSeriesAnalyzer(
            data=pd.DataFrame({"points": ts_data}), target_column="points"
        )

        # Verify pipeline completed
        assert analyzer.data is not None
        assert len(analyzer.data) > 0

    def test_panel_data_pipeline(self, sample_player_data):
        """Test panel data analysis pipeline"""
        from mcp_server.panel_data import PanelDataAnalyzer

        # Step 1: Prepare panel structure
        panel = sample_player_data.copy()
        panel["period"] = (panel.index // 100) + 1
        panel = panel[["player_id", "period", "points", "minutes"]].head(500)

        # Step 2: Validate
        assert "player_id" in panel.columns
        assert "period" in panel.columns
        assert "points" in panel.columns

        # Step 3: Run analysis
        analyzer = PanelDataAnalyzer(
            data=panel, entity_col="player_id", time_col="period", target_col="points"
        )

        # Verify pipeline completed
        assert analyzer.data is not None
        assert analyzer.entity_col == "player_id"


@pytest.mark.agent_8
def test_comprehensive_agent_8_integration(
    sample_player_data, time_series_data, panel_data, test_helper
):
    """
    Comprehensive test of Agent 8 integration with other agents

    Tests: Data validation + Econometric analysis + Performance monitoring
    """
    from mcp_server.time_series import TimeSeriesAnalyzer
    from mcp_server.panel_data import PanelDataAnalyzer
    from mcp_server.profiling.performance import profile, get_profiler

    profiler = get_profiler()
    profiler.reset()

    workflow_state = {
        "data_validated": False,
        "ts_analysis_initialized": False,
        "panel_analysis_initialized": False,
        "performance_monitored": False,
        "errors": [],
    }

    # Step 1: Data Validation
    try:
        test_helper.assert_data_quality(sample_player_data, min_rows=100)
        test_helper.assert_no_nulls(sample_player_data, ["player_id", "points"])
        workflow_state["data_validated"] = True
    except Exception as e:
        workflow_state["errors"].append(f"Validation: {str(e)}")

    # Step 2: Time Series Analysis (with profiling)
    @profile
    def init_time_series():
        try:
            analyzer = TimeSeriesAnalyzer(
                data=pd.DataFrame({"points": time_series_data.head(100)}),
                target_column="points",
            )
            workflow_state["ts_analysis_initialized"] = analyzer is not None
            return analyzer
        except Exception as e:
            workflow_state["errors"].append(f"Time series: {str(e)}")
            return None

    ts_result = init_time_series()

    # Step 3: Panel Data Analysis (with profiling)
    @profile
    def init_panel():
        try:
            analyzer = PanelDataAnalyzer(
                data=panel_data.head(200),
                entity_col="player_id",
                time_col="period",
                target_col="points",
            )
            workflow_state["panel_analysis_initialized"] = analyzer is not None
            return analyzer
        except Exception as e:
            workflow_state["errors"].append(f"Panel data: {str(e)}")
            return None

    panel_result = init_panel()

    # Step 4: Verify Performance Monitoring
    stats = profiler.get_summary()
    workflow_state["performance_monitored"] = stats["total_calls"] >= 2

    # Verify workflow success
    assert workflow_state["data_validated"], "Data validation should complete"
    assert workflow_state[
        "ts_analysis_initialized"
    ], f"Time series init should work: {workflow_state['errors']}"
    assert workflow_state[
        "panel_analysis_initialized"
    ], f"Panel data init should work: {workflow_state['errors']}"
    assert workflow_state[
        "performance_monitored"
    ], "Performance monitoring should track both analyses"

    # Verify no critical errors
    assert (
        len(workflow_state["errors"]) == 0
    ), f"Workflow should complete without errors: {workflow_state['errors']}"

    # Verify results
    assert ts_result is not None
    assert panel_result is not None
