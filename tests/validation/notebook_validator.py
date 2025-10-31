"""
Notebook Validation Framework for Option 2 Notebooks

This module provides comprehensive validation for Jupyter notebooks including:
- Automated execution
- Error detection
- Output validation
- Performance tracking
- Quality reporting

Author: Option 4 Week 3
Date: October 2025
"""

import logging
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

logger = logging.getLogger(__name__)


@dataclass
class NotebookValidationResult:
    """Results from notebook validation."""

    notebook_path: str
    success: bool
    execution_time_seconds: float
    total_cells: int
    executed_cells: int
    failed_cells: int
    error_cells: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    output_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notebook_path": self.notebook_path,
            "success": self.success,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "total_cells": self.total_cells,
            "executed_cells": self.executed_cells,
            "failed_cells": self.failed_cells,
            "error_cells": self.error_cells,
            "errors": self.errors,
            "warnings": self.warnings,
            "output_summary": self.output_summary,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationConfig:
    """Configuration for notebook validation."""

    timeout: int = 600  # 10 minutes per cell
    kernel_name: str = "python3"
    allow_errors: bool = False  # Continue on cell errors
    store_outputs: bool = True  # Store cell outputs
    execute_path: Optional[str] = None  # Working directory for execution


class NotebookValidator:
    """
    Validator for Jupyter notebooks.

    Executes notebooks and validates outputs, errors, and quality metrics.
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize validator with configuration."""
        self.config = config or ValidationConfig()
        self.results: List[NotebookValidationResult] = []
        self.logger = logger

    def validate_notebook(
        self, notebook_path: str, save_executed: bool = False
    ) -> NotebookValidationResult:
        """
        Validate a single Jupyter notebook.

        Args:
            notebook_path: Path to notebook file
            save_executed: If True, save executed notebook to disk

        Returns:
            NotebookValidationResult with validation details
        """
        self.logger.info(f"Validating notebook: {notebook_path}")

        # Read notebook
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
        except Exception as e:
            return NotebookValidationResult(
                notebook_path=notebook_path,
                success=False,
                execution_time_seconds=0.0,
                total_cells=0,
                executed_cells=0,
                failed_cells=0,
                errors=[f"Failed to read notebook: {str(e)}"],
            )

        # Count cells
        total_cells = len(nb.cells)
        code_cells = sum(1 for cell in nb.cells if cell.cell_type == "code")

        self.logger.info(f"  Total cells: {total_cells} ({code_cells} code cells)")

        # Execute notebook
        start_time = time.time()
        executed_cells = 0
        failed_cells = 0
        error_cells = []
        errors = []
        warnings = []

        ep = ExecutePreprocessor(
            timeout=self.config.timeout,
            kernel_name=self.config.kernel_name,
            allow_errors=self.config.allow_errors,
            store_widget_state=self.config.store_outputs,
        )

        try:
            # Execute with working directory
            resources = {}
            if self.config.execute_path:
                resources["metadata"] = {"path": self.config.execute_path}

            executed_nb, resources = ep.preprocess(nb, resources)

            # Count successful executions
            for idx, cell in enumerate(executed_nb.cells):
                if cell.cell_type != "code":
                    continue

                executed_cells += 1

                # Check for errors in outputs
                if hasattr(cell, "outputs"):
                    for output in cell.outputs:
                        if output.output_type == "error":
                            failed_cells += 1
                            error_cells.append(idx)
                            error_msg = f"Cell {idx}: {output.ename}: {output.evalue}"
                            errors.append(error_msg)
                            self.logger.warning(f"  {error_msg}")
                            break

                        # Check for warnings
                        if output.output_type == "stream" and output.name == "stderr":
                            warning_text = output.text
                            if "warning" in warning_text.lower():
                                warnings.append(f"Cell {idx}: {warning_text[:200]}")

            # Save executed notebook if requested
            if save_executed and executed_nb:
                output_path = notebook_path.replace(".ipynb", "_executed.ipynb")
                with open(output_path, "w", encoding="utf-8") as f:
                    nbformat.write(executed_nb, f)
                self.logger.info(f"  Saved executed notebook to: {output_path}")

            success = failed_cells == 0

        except CellExecutionError as e:
            failed_cells += 1
            error_cells.append(e.cell_index if hasattr(e, "cell_index") else -1)
            errors.append(f"Cell execution error: {str(e)}")
            self.logger.error(f"  Execution error: {str(e)}")
            success = False

        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            self.logger.error(f"  Unexpected error: {str(e)}")
            self.logger.error(traceback.format_exc())
            success = False

        execution_time = time.time() - start_time

        # Generate output summary
        output_summary = {
            "code_cells": code_cells,
            "markdown_cells": total_cells - code_cells,
            "execution_time_seconds": round(execution_time, 2),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        }

        result = NotebookValidationResult(
            notebook_path=notebook_path,
            success=success,
            execution_time_seconds=execution_time,
            total_cells=total_cells,
            executed_cells=executed_cells,
            failed_cells=failed_cells,
            error_cells=error_cells,
            errors=errors,
            warnings=warnings,
            output_summary=output_summary,
        )

        self.results.append(result)
        return result

    def validate_multiple(
        self, notebook_paths: List[str], save_executed: bool = False
    ) -> List[NotebookValidationResult]:
        """
        Validate multiple notebooks.

        Args:
            notebook_paths: List of notebook file paths
            save_executed: If True, save executed notebooks

        Returns:
            List of NotebookValidationResult objects
        """
        results = []

        for path in notebook_paths:
            self.logger.info(f"\n{'=' * 70}")
            result = self.validate_notebook(path, save_executed=save_executed)
            results.append(result)

            # Log summary
            status = "✅ PASSED" if result.success else "❌ FAILED"
            self.logger.info(f"  Status: {status}")
            self.logger.info(
                f"  Execution time: {result.execution_time_seconds:.2f}s"
            )
            self.logger.info(
                f"  Cells: {result.executed_cells}/{result.total_cells} executed"
            )
            if result.failed_cells > 0:
                self.logger.info(f"  Failed cells: {result.failed_cells}")

        return results

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics across all validated notebooks.

        Returns:
            Dictionary with aggregate validation metrics
        """
        if not self.results:
            return {"error": "No validation results available"}

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        summary = {
            "total_notebooks": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "total_execution_time_seconds": sum(
                r.execution_time_seconds for r in self.results
            ),
            "total_cells_executed": sum(r.executed_cells for r in self.results),
            "total_errors": sum(r.failed_cells for r in self.results),
            "notebooks": {},
        }

        # Per-notebook summary
        for result in self.results:
            notebook_name = Path(result.notebook_path).name
            summary["notebooks"][notebook_name] = {
                "success": result.success,
                "execution_time_seconds": result.execution_time_seconds,
                "cells_executed": result.executed_cells,
                "failed_cells": result.failed_cells,
                "errors_count": len(result.errors),
                "warnings_count": len(result.warnings),
            }

        return summary

    def save_results(
        self, output_dir: str = "validation_results", filename: str = "validation_results.json"
    ) -> str:
        """
        Save validation results to JSON file.

        Args:
            output_dir: Directory for output file
            filename: Name of output file

        Returns:
            Path to saved file
        """
        import os

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        output = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_notebooks": len(self.results),
                "validation_config": {
                    "timeout": self.config.timeout,
                    "kernel_name": self.config.kernel_name,
                    "allow_errors": self.config.allow_errors,
                },
            },
            "results": [r.to_dict() for r in self.results],
            "summary": self.generate_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        return filepath

    def print_summary(self):
        """Print formatted summary to console."""
        summary = self.generate_summary()

        print("\n" + "=" * 70)
        print("NOTEBOOK VALIDATION SUMMARY")
        print("=" * 70)

        print(f"\nTotal Notebooks: {summary['total_notebooks']}")
        print(
            f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)"
        )
        print(f"Failed: {summary['failed']}")
        print(
            f"Total Execution Time: {summary['total_execution_time_seconds']:.2f}s"
        )
        print(f"Total Cells Executed: {summary['total_cells_executed']}")
        print(f"Total Errors: {summary['total_errors']}")

        if summary.get("notebooks"):
            print("\n" + "-" * 70)
            print("Per-Notebook Results:")
            for notebook, metrics in summary["notebooks"].items():
                status = "✅" if metrics["success"] else "❌"
                print(f"\n  {status} {notebook}")
                print(f"      Time: {metrics['execution_time_seconds']:.2f}s")
                print(f"      Cells: {metrics['cells_executed']}")
                if metrics["failed_cells"] > 0:
                    print(f"      Failed: {metrics['failed_cells']} cells")
                if metrics["warnings_count"] > 0:
                    print(f"      Warnings: {metrics['warnings_count']}")

        # Show errors if any
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print("\n" + "-" * 70)
            print("Failed Notebooks Details:")
            for result in failed_results:
                print(f"\n  ❌ {Path(result.notebook_path).name}")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"      {error}")
                if len(result.errors) > 3:
                    print(f"      ... and {len(result.errors) - 3} more errors")

        print("\n" + "=" * 70 + "\n")
