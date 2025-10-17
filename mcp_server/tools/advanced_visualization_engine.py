"""
Phase 9.3: Advanced Visualization Engine

This module provides advanced visualization capabilities for formulas and data including:
- Interactive formula visualization
- Real-time data visualization
- 3D formula representation
- Advanced charting and graphing
- Formula relationship visualization
- Dynamic data plotting

Author: NBA MCP Server Development Team
Date: October 13, 2025
"""

import logging
import json
import base64
import io
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import math

import numpy as np
import pandas as pd
from sympy import symbols, sympify, latex, simplify, expand, factor
from sympy import Symbol, Expr, lambdify

# Visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.figure import Figure
    import seaborn as sns

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning(
        "Matplotlib not available. Install matplotlib and seaborn for visualization."
    )

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning(
        "Plotly not available. Install plotly for interactive visualizations."
    )

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available. Install Pillow for image processing.")

logger = logging.getLogger(__name__)

# ============================================================================
# Data Structures
# ============================================================================


class VisualizationType(Enum):
    """Types of visualizations"""

    FORMULA_GRAPH = "formula_graph"
    DATA_PLOT = "data_plot"
    FORMULA_RELATIONSHIP = "formula_relationship"
    INTERACTIVE_CHART = "interactive_chart"
    THREE_DIMENSIONAL = "three_dimensional"
    REAL_TIME = "real_time"
    STATIC_CHART = "static_chart"


class ChartType(Enum):
    """Types of charts"""

    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    SURFACE = "surface"
    CONTOUR = "contour"
    NETWORK = "network"
    TREE = "tree"
    SANKEY = "sankey"


class ExportFormat(Enum):
    """Export formats for visualizations"""

    PNG = "png"
    JPG = "jpg"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    BASE64 = "base64"


@dataclass
class VisualizationConfig:
    """Configuration for visualizations"""

    width: int = 800
    height: int = 600
    dpi: int = 100
    style: str = "default"
    color_scheme: str = "viridis"
    background_color: str = "white"
    grid: bool = True
    legend: bool = True
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    z_label: Optional[str] = None


@dataclass
class FormulaVisualizationResult:
    """Result from formula visualization"""

    visualization_id: str
    formula_id: str
    visualization_type: VisualizationType
    chart_type: ChartType
    image_data: Optional[str] = None
    html_data: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class DataVisualizationResult:
    """Result from data visualization"""

    visualization_id: str
    data_source: str
    visualization_type: VisualizationType
    chart_type: ChartType
    image_data: Optional[str] = None
    html_data: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class InteractiveVisualizationResult:
    """Result from interactive visualization"""

    visualization_id: str
    visualization_type: VisualizationType
    interactive_data: Dict[str, Any]
    controls: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None


# ============================================================================
# Advanced Visualization Engine
# ============================================================================


class AdvancedVisualizationEngine:
    """
    Advanced visualization engine for formulas and data
    """

    def __init__(self):
        """Initialize the advanced visualization engine"""
        self.logger = logging.getLogger(__name__)
        self.visualization_cache = {}
        self.default_config = VisualizationConfig()

        # Initialize visualization libraries
        self.matplotlib_available = MATPLOTLIB_AVAILABLE
        self.plotly_available = PLOTLY_AVAILABLE
        self.pil_available = PIL_AVAILABLE

        # Set up matplotlib style
        if self.matplotlib_available:
            plt.style.use("default")
            sns.set_palette("husl")

        self.logger.info("Advanced visualization engine initialized")

    def visualize_formula(
        self,
        formula: str,
        visualization_type: VisualizationType = VisualizationType.FORMULA_GRAPH,
        chart_type: ChartType = ChartType.LINE,
        config: Optional[VisualizationConfig] = None,
        variables: Optional[Dict[str, List[float]]] = None,
        export_format: ExportFormat = ExportFormat.PNG,
    ) -> FormulaVisualizationResult:
        """
        Visualize a mathematical formula

        Args:
            formula: Mathematical formula string
            visualization_type: Type of visualization
            chart_type: Type of chart
            config: Visualization configuration
            variables: Variable values for plotting
            export_format: Export format

        Returns:
            FormulaVisualizationResult with visualization data
        """
        visualization_id = str(uuid.uuid4())
        formula_id = str(uuid.uuid4())

        self.logger.info(f"Visualizing formula: {formula_id}")

        try:
            if config is None:
                config = self.default_config

            # Parse the formula
            expr = sympify(formula)

            # Generate visualization based on type
            if visualization_type == VisualizationType.FORMULA_GRAPH:
                result = self._create_formula_graph(
                    expr, config, variables, export_format
                )
            elif visualization_type == VisualizationType.THREE_DIMENSIONAL:
                result = self._create_3d_visualization(
                    expr, config, variables, export_format
                )
            elif visualization_type == VisualizationType.INTERACTIVE_CHART:
                result = self._create_interactive_chart(
                    expr, config, variables, export_format
                )
            else:
                result = self._create_basic_plot(expr, config, variables, export_format)

            return FormulaVisualizationResult(
                visualization_id=visualization_id,
                formula_id=formula_id,
                visualization_type=visualization_type,
                chart_type=chart_type,
                image_data=result.get("image_data"),
                html_data=result.get("html_data"),
                json_data=result.get("json_data"),
                metadata={
                    "formula": formula,
                    "variables": list(expr.free_symbols),
                    "config": asdict(config),
                    "export_format": export_format.value,
                },
            )

        except Exception as e:
            self.logger.error(f"Formula visualization failed: {e}")
            return FormulaVisualizationResult(
                visualization_id=visualization_id,
                formula_id=formula_id,
                visualization_type=visualization_type,
                chart_type=chart_type,
                success=False,
                error_message=str(e),
                metadata={"formula": formula},
            )

    def visualize_data(
        self,
        data: Dict[str, List[float]],
        visualization_type: VisualizationType = VisualizationType.DATA_PLOT,
        chart_type: ChartType = ChartType.LINE,
        config: Optional[VisualizationConfig] = None,
        export_format: ExportFormat = ExportFormat.PNG,
    ) -> DataVisualizationResult:
        """
        Visualize data using various chart types

        Args:
            data: Data dictionary with variable names and values
            visualization_type: Type of visualization
            chart_type: Type of chart
            config: Visualization configuration
            export_format: Export format

        Returns:
            DataVisualizationResult with visualization data
        """
        visualization_id = str(uuid.uuid4())
        data_source = "data_dict"

        self.logger.info(f"Visualizing data: {visualization_id}")

        try:
            if config is None:
                config = self.default_config

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Generate visualization based on chart type
            if chart_type == ChartType.LINE:
                result = self._create_line_chart(df, config, export_format)
            elif chart_type == ChartType.SCATTER:
                result = self._create_scatter_chart(df, config, export_format)
            elif chart_type == ChartType.BAR:
                result = self._create_bar_chart(df, config, export_format)
            elif chart_type == ChartType.HEATMAP:
                result = self._create_heatmap(df, config, export_format)
            elif chart_type == ChartType.HISTOGRAM:
                result = self._create_histogram(df, config, export_format)
            else:
                result = self._create_line_chart(df, config, export_format)

            return DataVisualizationResult(
                visualization_id=visualization_id,
                data_source=data_source,
                visualization_type=visualization_type,
                chart_type=chart_type,
                image_data=result.get("image_data"),
                html_data=result.get("html_data"),
                json_data=result.get("json_data"),
                metadata={
                    "data_shape": df.shape,
                    "columns": list(df.columns),
                    "config": asdict(config),
                    "export_format": export_format.value,
                },
            )

        except Exception as e:
            self.logger.error(f"Data visualization failed: {e}")
            return DataVisualizationResult(
                visualization_id=visualization_id,
                data_source=data_source,
                visualization_type=visualization_type,
                chart_type=chart_type,
                success=False,
                error_message=str(e),
                metadata={"data_keys": list(data.keys())},
            )

    def create_interactive_visualization(
        self,
        data: Dict[str, Any],
        visualization_type: VisualizationType = VisualizationType.INTERACTIVE_CHART,
        config: Optional[VisualizationConfig] = None,
    ) -> InteractiveVisualizationResult:
        """
        Create interactive visualization

        Args:
            data: Data for visualization
            visualization_type: Type of visualization
            config: Visualization configuration

        Returns:
            InteractiveVisualizationResult with interactive data
        """
        visualization_id = str(uuid.uuid4())

        self.logger.info(f"Creating interactive visualization: {visualization_id}")

        try:
            if config is None:
                config = self.default_config

            if not self.plotly_available:
                raise ValueError("Plotly not available for interactive visualizations")

            # Create interactive visualization
            interactive_data = self._create_interactive_plotly(data, config)
            controls = self._generate_interactive_controls(data)

            return InteractiveVisualizationResult(
                visualization_id=visualization_id,
                visualization_type=visualization_type,
                interactive_data=interactive_data,
                controls=controls,
                metadata={"data_type": type(data).__name__, "config": asdict(config)},
            )

        except Exception as e:
            self.logger.error(f"Interactive visualization failed: {e}")
            return InteractiveVisualizationResult(
                visualization_id=visualization_id,
                visualization_type=visualization_type,
                interactive_data={},
                controls=[],
                success=False,
                error_message=str(e),
            )

    def visualize_formula_relationships(
        self,
        formulas: List[str],
        relationships: List[Tuple[str, str, str]],
        config: Optional[VisualizationConfig] = None,
        export_format: ExportFormat = ExportFormat.PNG,
    ) -> FormulaVisualizationResult:
        """
        Visualize relationships between formulas

        Args:
            formulas: List of formula strings
            relationships: List of (formula1, formula2, relationship_type) tuples
            config: Visualization configuration
            export_format: Export format

        Returns:
            FormulaVisualizationResult with relationship visualization
        """
        visualization_id = str(uuid.uuid4())
        formula_id = "relationships"

        self.logger.info(f"Visualizing formula relationships: {visualization_id}")

        try:
            if config is None:
                config = self.default_config

            # Create relationship network
            result = self._create_relationship_network(
                formulas, relationships, config, export_format
            )

            return FormulaVisualizationResult(
                visualization_id=visualization_id,
                formula_id=formula_id,
                visualization_type=VisualizationType.FORMULA_RELATIONSHIP,
                chart_type=ChartType.NETWORK,
                image_data=result.get("image_data"),
                html_data=result.get("html_data"),
                json_data=result.get("json_data"),
                metadata={
                    "formulas": formulas,
                    "relationships": relationships,
                    "config": asdict(config),
                    "export_format": export_format.value,
                },
            )

        except Exception as e:
            self.logger.error(f"Formula relationship visualization failed: {e}")
            return FormulaVisualizationResult(
                visualization_id=visualization_id,
                formula_id=formula_id,
                visualization_type=VisualizationType.FORMULA_RELATIONSHIP,
                chart_type=ChartType.NETWORK,
                success=False,
                error_message=str(e),
                metadata={"formulas": formulas, "relationships": relationships},
            )

    # ========================================================================
    # Private Methods for Visualization Creation
    # ========================================================================

    def _create_formula_graph(
        self,
        expr: Expr,
        config: VisualizationConfig,
        variables: Optional[Dict[str, List[float]]],
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """Create a graph visualization of a formula"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            # Get free symbols from expression
            free_symbols = list(expr.free_symbols)

            if len(free_symbols) == 1:
                # Single variable function
                x = free_symbols[0]
                x_vals = np.linspace(-10, 10, 1000)

                # Create lambda function
                f = lambdify(x, expr, "numpy")
                y_vals = f(x_vals)

                # Create plot
                fig, ax = plt.subplots(
                    figsize=(config.width / 100, config.height / 100), dpi=config.dpi
                )
                ax.plot(x_vals, y_vals, linewidth=2, color="blue")
                ax.set_xlabel(config.x_label or str(x))
                ax.set_ylabel(config.y_label or "f(x)")
                ax.set_title(config.title or f"Graph of {expr}")
                ax.grid(config.grid)

                if config.legend:
                    ax.legend([f"{expr}"])

            elif len(free_symbols) == 2:
                # Two variable function
                x, y = free_symbols[:2]
                x_vals = np.linspace(-5, 5, 50)
                y_vals = np.linspace(-5, 5, 50)
                X, Y = np.meshgrid(x_vals, y_vals)

                # Create lambda function
                f = lambdify([x, y], expr, "numpy")
                Z = f(X, Y)

                # Create contour plot
                fig, ax = plt.subplots(
                    figsize=(config.width / 100, config.height / 100), dpi=config.dpi
                )
                contour = ax.contour(X, Y, Z, levels=20)
                ax.clabel(contour, inline=True, fontsize=8)
                ax.set_xlabel(config.x_label or str(x))
                ax.set_ylabel(config.y_label or str(y))
                ax.set_title(config.title or f"Contour plot of {expr}")
                ax.grid(config.grid)

            else:
                # Multi-variable function - create parameter plot
                fig, ax = plt.subplots(
                    figsize=(config.width / 100, config.height / 100), dpi=config.dpi
                )
                ax.text(
                    0.5,
                    0.5,
                    f"Formula: {expr}\nVariables: {free_symbols}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    transform=ax.transAxes,
                )
                ax.set_title(config.title or "Formula Display")
                ax.axis("off")

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Formula graph creation failed: {e}")
            return {"error": str(e)}

    def _create_3d_visualization(
        self,
        expr: Expr,
        config: VisualizationConfig,
        variables: Optional[Dict[str, List[float]]],
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """Create a 3D visualization of a formula"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            from mpl_toolkits.mplot3d import Axes3D

            # Get free symbols from expression
            free_symbols = list(expr.free_symbols)

            if len(free_symbols) >= 2:
                x, y = free_symbols[:2]
                x_vals = np.linspace(-5, 5, 30)
                y_vals = np.linspace(-5, 5, 30)
                X, Y = np.meshgrid(x_vals, y_vals)

                # Create lambda function
                f = lambdify([x, y], expr, "numpy")
                Z = f(X, Y)

                # Create 3D plot
                fig = plt.figure(
                    figsize=(config.width / 100, config.height / 100), dpi=config.dpi
                )
                ax = fig.add_subplot(111, projection="3d")
                surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)
                ax.set_xlabel(config.x_label or str(x))
                ax.set_ylabel(config.y_label or str(y))
                ax.set_zlabel(config.z_label or "f(x,y)")
                ax.set_title(config.title or f"3D plot of {expr}")

                if config.legend:
                    fig.colorbar(surf, shrink=0.5, aspect=5)

            else:
                # Single variable - create 2D plot
                return self._create_formula_graph(
                    expr, config, variables, export_format
                )

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"3D visualization creation failed: {e}")
            return {"error": str(e)}

    def _create_interactive_chart(
        self,
        expr: Expr,
        config: VisualizationConfig,
        variables: Optional[Dict[str, List[float]]],
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """Create an interactive chart"""
        try:
            if not self.plotly_available:
                return {"error": "Plotly not available"}

            # Get free symbols from expression
            free_symbols = list(expr.free_symbols)

            if len(free_symbols) == 1:
                # Single variable function
                x = free_symbols[0]
                x_vals = np.linspace(-10, 10, 1000)

                # Create lambda function
                f = lambdify(x, expr, "numpy")
                y_vals = f(x_vals)

                # Create interactive plot
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(x=x_vals, y=y_vals, mode="lines", name=str(expr))
                )
                fig.update_layout(
                    title=config.title or f"Interactive plot of {expr}",
                    xaxis_title=config.x_label or str(x),
                    yaxis_title=config.y_label or "f(x)",
                    width=config.width,
                    height=config.height,
                )

            elif len(free_symbols) == 2:
                # Two variable function
                x, y = free_symbols[:2]
                x_vals = np.linspace(-5, 5, 50)
                y_vals = np.linspace(-5, 5, 50)
                X, Y = np.meshgrid(x_vals, y_vals)

                # Create lambda function
                f = lambdify([x, y], expr, "numpy")
                Z = f(X, Y)

                # Create 3D surface plot
                fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y)])
                fig.update_layout(
                    title=config.title or f"3D surface of {expr}",
                    scene=dict(
                        xaxis_title=config.x_label or str(x),
                        yaxis_title=config.y_label or str(y),
                        zaxis_title=config.z_label or "f(x,y)",
                    ),
                    width=config.width,
                    height=config.height,
                )

            else:
                # Multi-variable function
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Formula: {expr}<br>Variables: {free_symbols}",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16),
                )
                fig.update_layout(
                    title=config.title or "Formula Display",
                    width=config.width,
                    height=config.height,
                )

            # Convert to HTML
            html_data = fig.to_html(include_plotlyjs="cdn")

            return {"html_data": html_data, "json_data": fig.to_dict()}

        except Exception as e:
            self.logger.error(f"Interactive chart creation failed: {e}")
            return {"error": str(e)}

    def _create_basic_plot(
        self,
        expr: Expr,
        config: VisualizationConfig,
        variables: Optional[Dict[str, List[float]]],
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """Create a basic plot"""
        return self._create_formula_graph(expr, config, variables, export_format)

    def _create_line_chart(
        self, df: pd.DataFrame, config: VisualizationConfig, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Create a line chart"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            for column in df.columns:
                ax.plot(df.index, df[column], label=column, linewidth=2)

            ax.set_xlabel(config.x_label or "Index")
            ax.set_ylabel(config.y_label or "Value")
            ax.set_title(config.title or "Line Chart")
            ax.grid(config.grid)

            if config.legend:
                ax.legend()

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Line chart creation failed: {e}")
            return {"error": str(e)}

    def _create_scatter_chart(
        self, df: pd.DataFrame, config: VisualizationConfig, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Create a scatter chart"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            if len(df.columns) >= 2:
                ax.scatter(df.iloc[:, 0], df.iloc[:, 1], alpha=0.6)
                ax.set_xlabel(config.x_label or df.columns[0])
                ax.set_ylabel(config.y_label or df.columns[1])
            else:
                ax.scatter(df.index, df.iloc[:, 0], alpha=0.6)
                ax.set_xlabel(config.x_label or "Index")
                ax.set_ylabel(config.y_label or df.columns[0])

            ax.set_title(config.title or "Scatter Chart")
            ax.grid(config.grid)

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Scatter chart creation failed: {e}")
            return {"error": str(e)}

    def _create_bar_chart(
        self, df: pd.DataFrame, config: VisualizationConfig, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Create a bar chart"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            # Use first column for bars
            column = df.columns[0]
            ax.bar(range(len(df)), df[column])
            ax.set_xlabel(config.x_label or "Index")
            ax.set_ylabel(config.y_label or column)
            ax.set_title(config.title or f"Bar Chart - {column}")
            ax.grid(config.grid, axis="y")

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Bar chart creation failed: {e}")
            return {"error": str(e)}

    def _create_heatmap(
        self, df: pd.DataFrame, config: VisualizationConfig, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Create a heatmap"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            # Create correlation heatmap if multiple columns
            if len(df.columns) > 1:
                corr_matrix = df.corr()
                im = ax.imshow(corr_matrix, cmap="coolwarm", aspect="auto")
                ax.set_xticks(range(len(corr_matrix.columns)))
                ax.set_yticks(range(len(corr_matrix.columns)))
                ax.set_xticklabels(corr_matrix.columns, rotation=45)
                ax.set_yticklabels(corr_matrix.columns)

                # Add colorbar
                plt.colorbar(im, ax=ax)
            else:
                # Single column heatmap
                data = df.values.reshape(-1, 1)
                im = ax.imshow(data.T, cmap="viridis", aspect="auto")
                ax.set_xlabel(config.x_label or "Index")
                ax.set_ylabel(config.y_label or df.columns[0])
                plt.colorbar(im, ax=ax)

            ax.set_title(config.title or "Heatmap")

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Heatmap creation failed: {e}")
            return {"error": str(e)}

    def _create_histogram(
        self, df: pd.DataFrame, config: VisualizationConfig, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Create a histogram"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            # Create histogram for first column
            column = df.columns[0]
            ax.hist(df[column], bins=30, alpha=0.7, edgecolor="black")
            ax.set_xlabel(config.x_label or column)
            ax.set_ylabel(config.y_label or "Frequency")
            ax.set_title(config.title or f"Histogram - {column}")
            ax.grid(config.grid, axis="y")

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Histogram creation failed: {e}")
            return {"error": str(e)}

    def _create_interactive_plotly(
        self, data: Dict[str, Any], config: VisualizationConfig
    ) -> Dict[str, Any]:
        """Create interactive Plotly visualization"""
        try:
            if not self.plotly_available:
                return {"error": "Plotly not available"}

            # Create a simple interactive plot
            fig = go.Figure()

            if isinstance(data, dict) and "x" in data and "y" in data:
                fig.add_trace(
                    go.Scatter(
                        x=data["x"], y=data["y"], mode="lines+markers", name="Data"
                    )
                )
            else:
                # Create sample data
                x = np.linspace(0, 10, 100)
                y = np.sin(x)
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="sin(x)"))

            fig.update_layout(
                title=config.title or "Interactive Visualization",
                width=config.width,
                height=config.height,
            )

            return fig.to_dict()

        except Exception as e:
            self.logger.error(f"Interactive Plotly creation failed: {e}")
            return {"error": str(e)}

    def _generate_interactive_controls(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate interactive controls for visualization"""
        controls = []

        # Add basic controls
        controls.append(
            {
                "type": "slider",
                "name": "range",
                "min": 0,
                "max": 100,
                "value": 50,
                "step": 1,
            }
        )

        controls.append(
            {
                "type": "dropdown",
                "name": "chart_type",
                "options": ["line", "scatter", "bar"],
                "value": "line",
            }
        )

        return controls

    def _create_relationship_network(
        self,
        formulas: List[str],
        relationships: List[Tuple[str, str, str]],
        config: VisualizationConfig,
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """Create a network visualization of formula relationships"""
        try:
            if not self.matplotlib_available:
                return {"error": "Matplotlib not available"}

            fig, ax = plt.subplots(
                figsize=(config.width / 100, config.height / 100), dpi=config.dpi
            )

            # Create simple network visualization
            n_formulas = len(formulas)
            if n_formulas == 0:
                ax.text(
                    0.5,
                    0.5,
                    "No formulas to visualize",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
            else:
                # Position formulas in a circle
                angles = np.linspace(0, 2 * np.pi, n_formulas, endpoint=False)
                x_pos = np.cos(angles)
                y_pos = np.sin(angles)

                # Plot formulas as nodes
                for i, formula in enumerate(formulas):
                    ax.scatter(x_pos[i], y_pos[i], s=200, c="blue", alpha=0.7)
                    ax.annotate(
                        f"F{i+1}", (x_pos[i], y_pos[i]), ha="center", va="center"
                    )

                # Plot relationships as edges
                for rel in relationships:
                    formula1, formula2, rel_type = rel
                    try:
                        idx1 = formulas.index(formula1)
                        idx2 = formulas.index(formula2)
                        ax.plot(
                            [x_pos[idx1], x_pos[idx2]],
                            [y_pos[idx1], y_pos[idx2]],
                            "k-",
                            alpha=0.5,
                            linewidth=1,
                        )
                    except ValueError:
                        continue

                ax.set_xlim(-1.5, 1.5)
                ax.set_ylim(-1.5, 1.5)
                ax.set_aspect("equal")
                ax.axis("off")

            ax.set_title(config.title or "Formula Relationship Network")

            # Export visualization
            result = self._export_visualization(fig, export_format)
            plt.close(fig)

            return result

        except Exception as e:
            self.logger.error(f"Relationship network creation failed: {e}")
            return {"error": str(e)}

    def _export_visualization(
        self, fig: Figure, export_format: ExportFormat
    ) -> Dict[str, Any]:
        """Export visualization in specified format"""
        try:
            result = {}

            if export_format == ExportFormat.BASE64:
                # Export as base64
                buffer = io.BytesIO()
                fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
                buffer.seek(0)
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
                result["image_data"] = image_data

            elif export_format == ExportFormat.PNG:
                # Export as PNG
                buffer = io.BytesIO()
                fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
                buffer.seek(0)
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
                result["image_data"] = image_data

            elif export_format == ExportFormat.SVG:
                # Export as SVG
                buffer = io.BytesIO()
                fig.savefig(buffer, format="svg", bbox_inches="tight")
                buffer.seek(0)
                svg_data = buffer.getvalue().decode("utf-8")
                result["json_data"] = {"svg": svg_data}

            else:
                # Default to PNG
                buffer = io.BytesIO()
                fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
                buffer.seek(0)
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
                result["image_data"] = image_data

            return result

        except Exception as e:
            self.logger.error(f"Visualization export failed: {e}")
            return {"error": str(e)}

    def get_visualization_capabilities(self) -> Dict[str, Any]:
        """Get information about visualization capabilities"""
        return {
            "matplotlib_available": self.matplotlib_available,
            "plotly_available": self.plotly_available,
            "pil_available": self.pil_available,
            "supported_formats": [fmt.value for fmt in ExportFormat],
            "supported_chart_types": [chart.value for chart in ChartType],
            "supported_visualization_types": [viz.value for viz in VisualizationType],
            "default_config": asdict(self.default_config),
        }


# ============================================================================
# Standalone Functions for MCP Tools
# ============================================================================


def visualize_formula(
    formula: str,
    visualization_type: str = "formula_graph",
    chart_type: str = "line",
    config: Optional[Dict[str, Any]] = None,
    variables: Optional[Dict[str, List[float]]] = None,
    export_format: str = "png",
) -> Dict[str, Any]:
    """
    Visualize a mathematical formula

    Args:
        formula: Mathematical formula string
        visualization_type: Type of visualization
        chart_type: Type of chart
        config: Visualization configuration
        variables: Variable values for plotting
        export_format: Export format

    Returns:
        Dictionary with visualization results
    """
    engine = AdvancedVisualizationEngine()

    viz_type = VisualizationType(visualization_type)
    chart_type_enum = ChartType(chart_type)
    export_format_enum = ExportFormat(export_format)

    viz_config = None
    if config:
        viz_config = VisualizationConfig(**config)

    result = engine.visualize_formula(
        formula=formula,
        visualization_type=viz_type,
        chart_type=chart_type_enum,
        config=viz_config,
        variables=variables,
        export_format=export_format_enum,
    )

    return asdict(result)


def visualize_data(
    data: Dict[str, List[float]],
    visualization_type: str = "data_plot",
    chart_type: str = "line",
    config: Optional[Dict[str, Any]] = None,
    export_format: str = "png",
) -> Dict[str, Any]:
    """
    Visualize data using various chart types

    Args:
        data: Data dictionary with variable names and values
        visualization_type: Type of visualization
        chart_type: Type of chart
        config: Visualization configuration
        export_format: Export format

    Returns:
        Dictionary with visualization results
    """
    engine = AdvancedVisualizationEngine()

    viz_type = VisualizationType(visualization_type)
    chart_type_enum = ChartType(chart_type)
    export_format_enum = ExportFormat(export_format)

    viz_config = None
    if config:
        viz_config = VisualizationConfig(**config)

    result = engine.visualize_data(
        data=data,
        visualization_type=viz_type,
        chart_type=chart_type_enum,
        config=viz_config,
        export_format=export_format_enum,
    )

    return asdict(result)


def create_interactive_visualization(
    data: Dict[str, Any],
    visualization_type: str = "interactive_chart",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create interactive visualization

    Args:
        data: Data for visualization
        visualization_type: Type of visualization
        config: Visualization configuration

    Returns:
        Dictionary with interactive visualization results
    """
    engine = AdvancedVisualizationEngine()

    viz_type = VisualizationType(visualization_type)

    viz_config = None
    if config:
        viz_config = VisualizationConfig(**config)

    result = engine.create_interactive_visualization(
        data=data, visualization_type=viz_type, config=viz_config
    )

    return asdict(result)


def visualize_formula_relationships(
    formulas: List[str],
    relationships: List[Tuple[str, str, str]],
    config: Optional[Dict[str, Any]] = None,
    export_format: str = "png",
) -> Dict[str, Any]:
    """
    Visualize relationships between formulas

    Args:
        formulas: List of formula strings
        relationships: List of (formula1, formula2, relationship_type) tuples
        config: Visualization configuration
        export_format: Export format

    Returns:
        Dictionary with visualization results
    """
    engine = AdvancedVisualizationEngine()

    export_format_enum = ExportFormat(export_format)

    viz_config = None
    if config:
        viz_config = VisualizationConfig(**config)

    result = engine.visualize_formula_relationships(
        formulas=formulas,
        relationships=relationships,
        config=viz_config,
        export_format=export_format_enum,
    )

    return asdict(result)


def get_visualization_capabilities() -> Dict[str, Any]:
    """
    Get information about visualization capabilities

    Returns:
        Dictionary with capability information
    """
    engine = AdvancedVisualizationEngine()
    return engine.get_visualization_capabilities()


# ============================================================================
# Logging Configuration
# ============================================================================


def log_operation(operation_name: str):
    """Decorator for logging operations"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation_name}")
                return result
            except Exception as e:
                logger.error(f"Failed {operation_name}: {e}")
                raise

        return wrapper

    return decorator
