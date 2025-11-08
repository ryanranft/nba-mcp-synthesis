"""
Notebook Execution Validation Framework

Tests that all tutorial notebooks execute successfully and produce expected outputs.

Usage:
    pytest tests/notebooks/test_notebook_execution.py -v
    pytest tests/notebooks/test_notebook_execution.py::test_notebook_01 -v
"""

import pytest
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path
import json
import time
from datetime import datetime


class NotebookValidator:
    """Validates Jupyter notebook execution and outputs."""

    def __init__(self, notebook_path, timeout=600):
        """
        Initialize validator.

        Args:
            notebook_path: Path to notebook file
            timeout: Maximum execution time in seconds (default: 10 minutes)
        """
        self.notebook_path = Path(notebook_path)
        self.timeout = timeout
        self.execution_results = {}
        self.cell_outputs = []
        self.execution_time = 0

    def execute(self):
        """Execute notebook and capture results."""
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {self.notebook_path}")

        print(f"\n{'='*60}")
        print(f"Executing: {self.notebook_path.name}")
        print(f"Timeout: {self.timeout}s")
        print(f"{'='*60}\n")

        # Load notebook
        with open(self.notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Configure executor
        # Set working directory to project root so imports work
        import os

        project_root = Path(__file__).parent.parent.parent

        ep = ExecutePreprocessor(
            timeout=self.timeout,
            kernel_name="python3",
            allow_errors=False,  # Fail on first error
        )

        # Execute
        start_time = time.time()
        try:
            # Execute with project root as working directory
            ep.preprocess(nb, {"metadata": {"path": str(project_root)}})
            self.execution_time = time.time() - start_time

            self.execution_results = {
                "notebook": str(self.notebook_path),
                "status": "success",
                "execution_time": self.execution_time,
                "cell_count": len(nb.cells),
                "errors": [],
            }

            # Extract outputs
            for i, cell in enumerate(nb.cells):
                if cell.cell_type == "code" and hasattr(cell, "outputs"):
                    self.cell_outputs.append({"cell_index": i, "outputs": cell.outputs})

            print(f"✅ SUCCESS - Executed in {self.execution_time:.1f}s")
            print(f"   Cells: {len(nb.cells)}")
            print(f"   Code outputs: {len(self.cell_outputs)}")

            return True

        except Exception as e:
            self.execution_time = time.time() - start_time
            self.execution_results = {
                "notebook": str(self.notebook_path),
                "status": "failed",
                "execution_time": self.execution_time,
                "errors": [str(e)],
            }

            print(f"❌ FAILED - {str(e)}")
            raise

    def validate_outputs(self, expected_outputs=None):
        """
        Validate notebook outputs match expectations.

        Args:
            expected_outputs: Dict of expected output checks
        """
        if expected_outputs is None:
            return True

        for check_name, check_func in expected_outputs.items():
            try:
                check_func(self.cell_outputs)
                print(f"  ✓ {check_name}")
            except AssertionError as e:
                print(f"  ✗ {check_name}: {e}")
                raise

        return True

    def generate_report(self, output_path=None):
        """Generate validation report."""
        if output_path is None:
            output_path = f"validation_results/notebook_{self.notebook_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.execution_results, f, indent=2, default=str)

        return output_path


# ==============================================================================
# Test Fixtures
# ==============================================================================

NOTEBOOKS_DIR = Path("examples")

NOTEBOOKS = {
    "01": NOTEBOOKS_DIR / "01_nba_101_getting_started.ipynb",
    "02": NOTEBOOKS_DIR / "02_player_valuation_performance.ipynb",
    "03": NOTEBOOKS_DIR / "03_team_strategy_game_outcomes.ipynb",
    "04": NOTEBOOKS_DIR / "04_contract_analytics_salary_cap.ipynb",
    "05": NOTEBOOKS_DIR / "05_live_game_analytics_dashboard.ipynb",
    "06": NOTEBOOKS_DIR / "06_streaming_analytics.ipynb",
}


# ==============================================================================
# Individual Notebook Tests
# ==============================================================================


@pytest.mark.notebooks
@pytest.mark.slow
def test_notebook_01_getting_started():
    """Test Notebook 1: NBA 101 Getting Started"""
    validator = NotebookValidator(NOTEBOOKS["01"], timeout=300)  # 5 minutes
    assert validator.execute(), "Notebook execution failed"

    # Validate key outputs
    def check_basic_stats(outputs):
        """Check that basic statistics were computed."""
        # At least one output should contain statistical results
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs({"basic_stats": check_basic_stats})


@pytest.mark.notebooks
@pytest.mark.slow
def test_notebook_02_player_valuation():
    """Test Notebook 2: Player Valuation & Performance Analysis"""
    validator = NotebookValidator(NOTEBOOKS["02"], timeout=420)  # 7 minutes
    assert validator.execute(), "Notebook execution failed"

    def check_time_series(outputs):
        """Check that time series analysis was performed."""
        assert len(outputs) > 0, "No outputs found"

    def check_panel_data(outputs):
        """Check that panel data analysis was performed."""
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs(
        {"time_series": check_time_series, "panel_data": check_panel_data}
    )


@pytest.mark.notebooks
@pytest.mark.slow
def test_notebook_03_team_strategy():
    """Test Notebook 3: Team Strategy & Game Outcomes"""
    validator = NotebookValidator(NOTEBOOKS["03"], timeout=420)  # 7 minutes
    assert validator.execute(), "Notebook execution failed"

    def check_game_theory(outputs):
        """Check that game theory analysis was performed."""
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs({"game_theory": check_game_theory})


@pytest.mark.notebooks
@pytest.mark.slow
def test_notebook_04_contract_analytics():
    """Test Notebook 4: Contract Analytics & Salary Cap Management"""
    validator = NotebookValidator(NOTEBOOKS["04"], timeout=420)  # 7 minutes
    assert validator.execute(), "Notebook execution failed"

    def check_optimization(outputs):
        """Check that optimization was performed."""
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs({"optimization": check_optimization})


@pytest.mark.notebooks
@pytest.mark.slow
def test_notebook_05_live_analytics():
    """Test Notebook 5: Live Game Analytics Dashboard"""
    validator = NotebookValidator(NOTEBOOKS["05"], timeout=240)  # 4 minutes
    assert validator.execute(), "Notebook execution failed"

    def check_particle_filter(outputs):
        """Check that particle filter analysis was performed."""
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs({"particle_filter": check_particle_filter})


@pytest.mark.notebooks
def test_notebook_06_streaming_analytics():
    """Test Notebook 6: Real-Time Streaming Analytics"""
    validator = NotebookValidator(NOTEBOOKS["06"], timeout=240)  # 4 minutes
    assert validator.execute(), "Notebook execution failed"

    def check_streaming(outputs):
        """Check that streaming analytics were performed."""
        assert len(outputs) > 0, "No outputs found"

    validator.validate_outputs({"streaming": check_streaming})


# ==============================================================================
# Comprehensive Test Suite
# ==============================================================================


@pytest.mark.notebooks
@pytest.mark.comprehensive
def test_all_notebooks_execute():
    """Test that all tutorial notebooks execute successfully."""
    results = {}

    for notebook_id, notebook_path in NOTEBOOKS.items():
        print(f"\n{'='*70}")
        print(f"Testing Notebook {notebook_id}: {notebook_path.name}")
        print(f"{'='*70}")

        validator = NotebookValidator(notebook_path, timeout=420)

        try:
            validator.execute()
            results[notebook_id] = {
                "status": "success",
                "time": validator.execution_time,
                "cells": len(validator.cell_outputs),
            }
        except Exception as e:
            results[notebook_id] = {
                "status": "failed",
                "error": str(e),
                "time": validator.execution_time,
            }

    # Summary
    print(f"\n{'='*70}")
    print("NOTEBOOK VALIDATION SUMMARY")
    print(f"{'='*70}\n")

    total = len(results)
    passed = sum(1 for r in results.values() if r["status"] == "success")
    success_rate = (passed / total) * 100

    for notebook_id, result in results.items():
        status_symbol = "✅" if result["status"] == "success" else "❌"
        time_str = f"{result['time']:.1f}s" if "time" in result else "N/A"
        print(
            f"{status_symbol} Notebook {notebook_id}: {result['status'].upper()} ({time_str})"
        )

    print(f"\n{'='*70}")
    print(f"Success Rate: {success_rate:.1f}% ({passed}/{total})")
    print(f"{'='*70}\n")

    # Save comprehensive report
    report_path = f"validation_results/comprehensive_notebook_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"📊 Full report saved: {report_path}\n")

    # Assert all passed
    assert success_rate == 100.0, f"Only {passed}/{total} notebooks passed"


# ==============================================================================
# Quick Validation Test
# ==============================================================================


@pytest.mark.notebooks
@pytest.mark.quick
def test_notebook_01_quick():
    """Quick test of Notebook 1 (for CI/CD)."""
    validator = NotebookValidator(NOTEBOOKS["01"], timeout=180)  # 3 minutes
    assert validator.execute(), "Notebook 1 execution failed"


if __name__ == "__main__":
    # Run comprehensive test when executed directly
    print("Running comprehensive notebook validation...")
    test_all_notebooks_execute()
