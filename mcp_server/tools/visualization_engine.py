"""
Advanced Visualization Engine Module

Author: NBA MCP Server Team
Date: 2025-01-13
"""

import json
import logging
import base64
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import math
import numpy as np
import sympy as sp
from sympy import latex, simplify, expand, factor, diff, integrate, solve
from sympy.parsing.sympy_parser import parse_expr
import uuid

# Import other modules
from .formula_intelligence import FormulaIntelligence
from .formula_builder import InteractiveFormulaBuilder
from .algebra_helper import get_sports_formula

logger = logging.getLogger(__name__)

class VisualizationType(Enum):
    """Types of visualizations supported"""
    LATEX = "latex"
    TABLE = "table"
    CHART = "chart"
    GRAPH = "graph"
    PLOT_2D = "plot_2d"
    PLOT_3D = "plot_3d"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    NETWORK = "network"
    TIMELINE = "timeline"

class ChartType(Enum):
    """Specific chart types"""
    SCATTER = "scatter"
    LINE = "line"
    BAR = "bar"
    HISTOGRAM = "histogram"
    PIE = "pie"
    HEATMAP = "heatmap"
    BOX_PLOT = "box_plot"
    VIOLIN = "violin"
    RADAR = "radar"
    SANKEY = "sankey"

@dataclass
class VisualizationConfig:
    """Configuration for visualizations"""
    width: int = 800
    height: int = 600
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    z_label: str = ""
    color_scheme: str = "default"
    theme: str = "light"
    show_grid: bool = True
    show_legend: bool = True
    interactive: bool = True
    animation: bool = False
    export_format: str = "png"

@dataclass
class DataPoint:
    """Represents a single data point"""
    x: float
    y: float
    z: Optional[float] = None
    label: Optional[str] = None
    color: Optional[str] = None
    size: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Dataset:
    """Represents a dataset for visualization"""
    name: str
    data_points: List[DataPoint]
    x_column: str = "x"
    y_column: str = "y"
    z_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class VisualizationResult:
    """Result of a visualization generation"""
    success: bool
    visualization_type: VisualizationType
    data: Optional[Dict[str, Any]] = None
    image_data: Optional[str] = None  # Base64 encoded image
    svg_data: Optional[str] = None    # SVG markup
    html_data: Optional[str] = None   # HTML with embedded visualization
    latex_data: Optional[str] = None  # LaTeX representation
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AdvancedVisualizationEngine:
    """
    Advanced visualization engine with support for multiple chart types,
    3D plotting, interactive visualizations, and real-time data.
    """

    def __init__(self):
        """Initialize the visualization engine"""
        self.formula_intelligence = FormulaIntelligence()
        self.formula_builder = InteractiveFormulaBuilder()

        # Visualization templates
        self.chart_templates = self._initialize_chart_templates()

        # Color schemes
        self.color_schemes = self._initialize_color_schemes()

        # Supported export formats
        self.export_formats = ["png", "svg", "pdf", "html", "json"]

    def _initialize_chart_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined chart templates"""
        return {
            "player_comparison": {
                "type": ChartType.SCATTER,
                "title": "Player Performance Comparison",
                "x_label": "Offensive Rating",
                "y_label": "Defensive Rating",
                "color_scheme": "sports",
                "interactive": True
            },
            "team_metrics": {
                "type": ChartType.BAR,
                "title": "Team Performance Metrics",
                "x_label": "Teams",
                "y_label": "Performance Score",
                "color_scheme": "team_colors",
                "interactive": True
            },
            "formula_analysis": {
                "type": ChartType.LINE,
                "title": "Formula Analysis Over Time",
                "x_label": "Time Period",
                "y_label": "Formula Value",
                "color_scheme": "formula",
                "interactive": True
            },
            "shooting_efficiency": {
                "type": ChartType.HEATMAP,
                "title": "Shooting Efficiency Heatmap",
                "x_label": "Distance from Basket",
                "y_label": "Angle from Center",
                "color_scheme": "efficiency",
                "interactive": True
            }
        }

    def _initialize_color_schemes(self) -> Dict[str, List[str]]:
        """Initialize color schemes for visualizations"""
        return {
            "default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "sports": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "team_colors": ["#C8102E", "#1D428A", "#CE1141", "#0C2340", "#E31837"],
            "efficiency": ["#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00"],
            "formula": ["#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"],
            "heatmap": ["#000080", "#0000FF", "#00FFFF", "#FFFF00", "#FF0000"]
        }

    def generate_visualization(
        self,
        visualization_type: VisualizationType,
        data: Union[List[DataPoint], Dataset, Dict[str, Any]],
        config: Optional[VisualizationConfig] = None,
        chart_type: Optional[ChartType] = None
    ) -> VisualizationResult:
        """
        Generate a visualization based on type and data.

        Args:
            visualization_type: Type of visualization to generate
            data: Data to visualize (points, dataset, or raw data)
            config: Visualization configuration
            chart_type: Specific chart type (for chart visualizations)

        Returns:
            VisualizationResult with generated visualization
        """
        try:
            if config is None:
                config = VisualizationConfig()

            # Convert data to standardized format
            dataset = self._normalize_data(data)

            if visualization_type == VisualizationType.LATEX:
                return self._generate_latex_visualization(dataset, config)
            elif visualization_type == VisualizationType.TABLE:
                return self._generate_table_visualization(dataset, config)
            elif visualization_type == VisualizationType.CHART:
                return self._generate_chart_visualization(dataset, config, chart_type)
            elif visualization_type == VisualizationType.GRAPH:
                return self._generate_graph_visualization(dataset, config)
            elif visualization_type == VisualizationType.PLOT_2D:
                return self._generate_2d_plot(dataset, config)
            elif visualization_type == VisualizationType.PLOT_3D:
                return self._generate_3d_plot(dataset, config)
            elif visualization_type == VisualizationType.HEATMAP:
                return self._generate_heatmap(dataset, config)
            elif visualization_type == VisualizationType.SCATTER:
                return self._generate_scatter_plot(dataset, config)
            elif visualization_type == VisualizationType.HISTOGRAM:
                return self._generate_histogram(dataset, config)
            elif visualization_type == VisualizationType.BAR_CHART:
                return self._generate_bar_chart(dataset, config)
            elif visualization_type == VisualizationType.LINE_CHART:
                return self._generate_line_chart(dataset, config)
            elif visualization_type == VisualizationType.PIE_CHART:
                return self._generate_pie_chart(dataset, config)
            elif visualization_type == VisualizationType.NETWORK:
                return self._generate_network_graph(dataset, config)
            elif visualization_type == VisualizationType.TIMELINE:
                return self._generate_timeline(dataset, config)
            else:
                return VisualizationResult(
                    success=False,
                    visualization_type=visualization_type,
                    error=f"Unsupported visualization type: {visualization_type}"
                )

        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return VisualizationResult(
                success=False,
                visualization_type=visualization_type,
                error=str(e)
            )

    def _normalize_data(self, data: Union[List[DataPoint], Dataset, Dict[str, Any]]) -> Dataset:
        """Normalize different data formats to Dataset"""
        if isinstance(data, Dataset):
            return data
        elif isinstance(data, list):
            # Assume list of DataPoint objects
            return Dataset(
                name="dataset",
                data_points=data,
                x_column="x",
                y_column="y"
            )
        elif isinstance(data, dict):
            # Convert dictionary to Dataset
            if "data_points" in data:
                return Dataset(**data)
            else:
                # Assume raw data dictionary
                points = []
                if "x" in data and "y" in data:
                    x_values = data["x"] if isinstance(data["x"], list) else [data["x"]]
                    y_values = data["y"] if isinstance(data["y"], list) else [data["y"]]
                    z_values = data.get("z", [])
                    if not isinstance(z_values, list):
                        z_values = [z_values] if z_values else [None] * len(x_values)

                    for i, (x, y) in enumerate(zip(x_values, y_values)):
                        z = z_values[i] if i < len(z_values) else None
                        points.append(DataPoint(x=x, y=y, z=z))

                return Dataset(
                    name=data.get("name", "dataset"),
                    data_points=points,
                    x_column=data.get("x_column", "x"),
                    y_column=data.get("y_column", "y"),
                    z_column=data.get("z_column"),
                    metadata=data.get("metadata")
                )
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    def _generate_latex_visualization(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate LaTeX visualization"""
        try:
            latex_content = []

            # Add title if specified
            if config.title:
                latex_content.append(f"\\section{{{config.title}}}")

            # Generate LaTeX for each data point
            for point in dataset.data_points:
                if point.label:
                    latex_content.append(f"\\textbf{{{point.label}}}: ")

                if point.z is not None:
                    latex_content.append(f"({point.x}, {point.y}, {point.z})")
                else:
                    latex_content.append(f"({point.x}, {point.y})")

                if point.metadata:
                    latex_content.append(f" \\textit{{{point.metadata}}}")

                latex_content.append("\\\\")

            latex_data = "\n".join(latex_content)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.LATEX,
                latex_data=latex_data,
                metadata={
                    "point_count": len(dataset.data_points),
                    "has_3d": any(p.z is not None for p in dataset.data_points)
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.LATEX,
                error=str(e)
            )

    def _generate_table_visualization(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate table visualization"""
        try:
            table_data = []

            # Create header
            headers = [dataset.x_column, dataset.y_column]
            if dataset.z_column:
                headers.append(dataset.z_column)
            if dataset.color_column:
                headers.append("Color")
            if dataset.size_column:
                headers.append("Size")
            headers.extend(["Label", "Metadata"])
            table_data.append(headers)

            # Add data rows
            for point in dataset.data_points:
                row = [point.x, point.y]
                if dataset.z_column:
                    row.append(point.z if point.z is not None else "")
                if dataset.color_column:
                    row.append(point.color if point.color else "")
                if dataset.size_column:
                    row.append(point.size if point.size else "")
                row.append(point.label if point.label else "")
                row.append(str(point.metadata) if point.metadata else "")
                table_data.append(row)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.TABLE,
                data={"table": table_data},
                metadata={
                    "row_count": len(table_data) - 1,
                    "column_count": len(headers)
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.TABLE,
                error=str(e)
            )

    def _generate_chart_visualization(
        self,
        dataset: Dataset,
        config: VisualizationConfig,
        chart_type: Optional[ChartType]
    ) -> VisualizationResult:
        """Generate chart visualization"""
        try:
            if chart_type is None:
                chart_type = ChartType.SCATTER

            # Generate chart data structure
            chart_data = {
                "type": chart_type.value,
                "title": config.title or f"{chart_type.value.title()} Chart",
                "x_label": config.x_label or dataset.x_column,
                "y_label": config.y_label or dataset.y_column,
                "data": []
            }

            # Convert data points to chart format
            for point in dataset.data_points:
                chart_point = {
                    "x": point.x,
                    "y": point.y,
                    "label": point.label
                }
                if point.z is not None:
                    chart_point["z"] = point.z
                if point.color:
                    chart_point["color"] = point.color
                if point.size:
                    chart_point["size"] = point.size
                chart_data["data"].append(chart_point)

            # Generate HTML representation
            html_data = self._generate_chart_html(chart_data, config)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.CHART,
                data=chart_data,
                html_data=html_data,
                metadata={
                    "chart_type": chart_type.value,
                    "point_count": len(chart_data["data"]),
                    "interactive": config.interactive
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.CHART,
                error=str(e)
            )

    def _generate_chart_html(self, chart_data: Dict[str, Any], config: VisualizationConfig) -> str:
        """Generate HTML representation of chart"""
        chart_id = f"chart_{uuid.uuid4().hex[:8]}"

        html = f"""
        <div id="{chart_id}" style="width: {config.width}px; height: {config.height}px;">
            <h3>{chart_data['title']}</h3>
            <div class="chart-container">
                <svg width="{config.width}" height="{config.height}" viewBox="0 0 {config.width} {config.height}">
                    <rect width="100%" height="100%" fill="white" stroke="black" stroke-width="1"/>
                    <text x="{config.width//2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">
                        {chart_data['title']}
                    </text>
                    <text x="{config.width//2}" y="{config.height-10}" text-anchor="middle" font-size="12">
                        {chart_data['x_label']}
                    </text>
                    <text x="20" y="{config.height//2}" text-anchor="middle" font-size="12" transform="rotate(-90, 20, {config.height//2})">
                        {chart_data['y_label']}
                    </text>
        """

        # Add data points
        if chart_data["data"]:
            x_values = [p["x"] for p in chart_data["data"]]
            y_values = [p["y"] for p in chart_data["data"]]

            if x_values and y_values:
                x_min, x_max = min(x_values), max(x_values)
                y_min, y_max = min(y_values), max(y_values)

                # Add padding
                x_range = x_max - x_min if x_max != x_min else 1
                y_range = y_max - y_min if y_max != y_min else 1
                x_padding = x_range * 0.1
                y_padding = y_range * 0.1

                x_min -= x_padding
                x_max += x_padding
                y_min -= y_padding
                y_max += y_padding

                # Scale to SVG coordinates
                plot_width = config.width - 80
                plot_height = config.height - 80
                plot_x = 40
                plot_y = 40

                for point in chart_data["data"]:
                    svg_x = plot_x + (point["x"] - x_min) / (x_max - x_min) * plot_width
                    svg_y = plot_y + plot_height - (point["y"] - y_min) / (y_max - y_min) * plot_height

                    color = point.get("color", "#1f77b4")
                    size = point.get("size", 5)

                    html += f"""
                    <circle cx="{svg_x}" cy="{svg_y}" r="{size}" fill="{color}" stroke="black" stroke-width="1">
                        <title>{point.get('label', f'({point["x"]}, {point["y"]})')}</title>
                    </circle>
                    """

        html += """
                </svg>
            </div>
        </div>
        """

        return html

    def _generate_graph_visualization(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate graph visualization (network/relationship)"""
        try:
            # For now, generate a simple network graph
            graph_data = {
                "nodes": [],
                "edges": []
            }

            # Convert data points to nodes
            for i, point in enumerate(dataset.data_points):
                node = {
                    "id": f"node_{i}",
                    "label": point.label or f"Point {i}",
                    "x": point.x,
                    "y": point.y,
                    "color": point.color or "#1f77b4"
                }
                graph_data["nodes"].append(node)

            # Create edges between nearby points
            for i, point1 in enumerate(dataset.data_points):
                for j, point2 in enumerate(dataset.data_points[i+1:], i+1):
                    distance = math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
                    if distance < 10:  # Threshold for edge creation
                        edge = {
                            "source": f"node_{i}",
                            "target": f"node_{j}",
                            "weight": distance
                        }
                        graph_data["edges"].append(edge)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.GRAPH,
                data=graph_data,
                metadata={
                    "node_count": len(graph_data["nodes"]),
                    "edge_count": len(graph_data["edges"])
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.GRAPH,
                error=str(e)
            )

    def _generate_2d_plot(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate 2D plot visualization"""
        return self._generate_chart_visualization(dataset, config, ChartType.SCATTER)

    def _generate_3d_plot(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate 3D plot visualization"""
        try:
            # Check if we have 3D data
            has_3d = any(point.z is not None for point in dataset.data_points)
            if not has_3d:
                return VisualizationResult(
                    success=False,
                    visualization_type=VisualizationType.PLOT_3D,
                    error="No 3D data available (z values missing)"
                )

            # Generate 3D plot data
            plot_data = {
                "type": "3d_scatter",
                "title": config.title or "3D Plot",
                "x_label": config.x_label or dataset.x_column,
                "y_label": config.y_label or dataset.y_column,
                "z_label": config.z_label or dataset.z_column or "Z",
                "data": []
            }

            for point in dataset.data_points:
                if point.z is not None:
                    plot_data["data"].append({
                        "x": point.x,
                        "y": point.y,
                        "z": point.z,
                        "label": point.label,
                        "color": point.color
                    })

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.PLOT_3D,
                data=plot_data,
                metadata={
                    "point_count": len(plot_data["data"]),
                    "has_3d": True
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.PLOT_3D,
                error=str(e)
            )

    def _generate_heatmap(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate heatmap visualization"""
        try:
            # Create grid for heatmap
            x_values = [p.x for p in dataset.data_points]
            y_values = [p.y for p in dataset.data_points]

            if not x_values or not y_values:
                return VisualizationResult(
                    success=False,
                    visualization_type=VisualizationType.HEATMAP,
                    error="No data points available for heatmap"
                )

            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)

            # Create grid
            grid_size = 20
            x_step = (x_max - x_min) / grid_size
            y_step = (y_max - y_min) / grid_size

            heatmap_data = []
            for i in range(grid_size):
                row = []
                for j in range(grid_size):
                    cell_x = x_min + i * x_step
                    cell_y = y_min + j * y_step

                    # Count points in this cell
                    count = sum(1 for p in dataset.data_points
                              if cell_x <= p.x < cell_x + x_step and
                                 cell_y <= p.y < cell_y + y_step)

                    row.append(count)
                heatmap_data.append(row)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.HEATMAP,
                data={
                    "heatmap": heatmap_data,
                    "x_range": [x_min, x_max],
                    "y_range": [y_min, y_max],
                    "grid_size": grid_size
                },
                metadata={
                    "grid_size": grid_size,
                    "max_value": max(max(row) for row in heatmap_data)
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.HEATMAP,
                error=str(e)
            )

    def _generate_scatter_plot(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate scatter plot visualization"""
        return self._generate_chart_visualization(dataset, config, ChartType.SCATTER)

    def _generate_histogram(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate histogram visualization"""
        try:
            # Use y values for histogram
            y_values = [p.y for p in dataset.data_points]

            if not y_values:
                return VisualizationResult(
                    success=False,
                    visualization_type=VisualizationType.HISTOGRAM,
                    error="No data points available for histogram"
                )

            # Create bins
            num_bins = min(20, len(set(y_values)))
            y_min, y_max = min(y_values), max(y_values)
            bin_width = (y_max - y_min) / num_bins if y_max != y_min else 1

            bins = []
            bin_counts = []

            for i in range(num_bins):
                bin_start = y_min + i * bin_width
                bin_end = bin_start + bin_width
                count = sum(1 for y in y_values if bin_start <= y < bin_end)

                bins.append((bin_start, bin_end))
                bin_counts.append(count)

            histogram_data = {
                "bins": bins,
                "counts": bin_counts,
                "bin_width": bin_width,
                "total_points": len(y_values)
            }

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.HISTOGRAM,
                data=histogram_data,
                metadata={
                    "num_bins": num_bins,
                    "max_count": max(bin_counts)
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.HISTOGRAM,
                error=str(e)
            )

    def _generate_bar_chart(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate bar chart visualization"""
        return self._generate_chart_visualization(dataset, config, ChartType.BAR)

    def _generate_line_chart(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate line chart visualization"""
        return self._generate_chart_visualization(dataset, config, ChartType.LINE)

    def _generate_pie_chart(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate pie chart visualization"""
        try:
            # Group data by labels or create categories
            categories = {}
            for point in dataset.data_points:
                category = point.label or f"Category {point.x}"
                if category not in categories:
                    categories[category] = 0
                categories[category] += point.y

            pie_data = {
                "categories": list(categories.keys()),
                "values": list(categories.values()),
                "total": sum(categories.values())
            }

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.PIE_CHART,
                data=pie_data,
                metadata={
                    "category_count": len(categories),
                    "total_value": pie_data["total"]
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.PIE_CHART,
                error=str(e)
            )

    def _generate_network_graph(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate network graph visualization"""
        return self._generate_graph_visualization(dataset, config)

    def _generate_timeline(self, dataset: Dataset, config: VisualizationConfig) -> VisualizationResult:
        """Generate timeline visualization"""
        try:
            # Sort data points by x value (assuming x is time)
            sorted_points = sorted(dataset.data_points, key=lambda p: p.x)

            timeline_data = {
                "events": [],
                "start_time": sorted_points[0].x if sorted_points else 0,
                "end_time": sorted_points[-1].x if sorted_points else 0
            }

            for point in sorted_points:
                event = {
                    "time": point.x,
                    "label": point.label or f"Event at {point.x}",
                    "value": point.y,
                    "color": point.color,
                    "metadata": point.metadata
                }
                timeline_data["events"].append(event)

            return VisualizationResult(
                success=True,
                visualization_type=VisualizationType.TIMELINE,
                data=timeline_data,
                metadata={
                    "event_count": len(timeline_data["events"]),
                    "duration": timeline_data["end_time"] - timeline_data["start_time"]
                }
            )

        except Exception as e:
            return VisualizationResult(
                success=False,
                visualization_type=VisualizationType.TIMELINE,
                error=str(e)
            )

    def export_visualization(
        self,
        visualization: VisualizationResult,
        format: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export visualization in specified format.

        Args:
            visualization: Visualization result to export
            format: Export format (png, svg, pdf, html, json)
            filename: Optional filename for export

        Returns:
            Dictionary with export information
        """
        try:
            if format not in self.export_formats:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format}"
                }

            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"visualization_{timestamp}.{format}"

            export_data = {
                "filename": filename,
                "format": format,
                "visualization_type": visualization.visualization_type.value,
                "metadata": visualization.metadata
            }

            if format == "json":
                export_data["data"] = visualization.data
            elif format == "html":
                export_data["html_content"] = visualization.html_data
            elif format == "svg":
                export_data["svg_content"] = visualization.svg_data
            elif format == "png":
                export_data["image_data"] = visualization.image_data
            elif format == "pdf":
                # PDF export would require additional processing
                export_data["note"] = "PDF export requires additional processing"

            return {
                "success": True,
                "export": export_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_visualization_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available visualization templates"""
        return self.chart_templates

    def get_color_schemes(self) -> Dict[str, List[str]]:
        """Get available color schemes"""
        return self.color_schemes

    def get_supported_formats(self) -> List[str]:
        """Get supported export formats"""
        return self.export_formats




