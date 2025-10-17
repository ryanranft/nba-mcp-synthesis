"""
Formula Dependency Graph for Sports Analytics

This module provides tools to create and visualize dependency graphs between
sports analytics formulas. It maps relationships between different metrics,
shows which formulas depend on others, and helps users understand complex
analytical frameworks.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import logging
import json
from dataclasses import dataclass, field
from enum import Enum
import re

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap

    NETWORKX_AVAILABLE = True
except ImportError:
    nx = None
    plt = None
    NETWORKX_AVAILABLE = False

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr

    SYMPY_AVAILABLE = True
except ImportError:
    sp = None
    SYMPY_AVAILABLE = False

from ..exceptions import ValidationError
from .logger_config import log_operation

logger = logging.getLogger(__name__)

# Use ValidationError for all tool errors
ToolError = ValidationError


class FormulaType(Enum):
    """Types of formulas in the dependency graph"""

    BASIC = "basic"
    ADVANCED = "advanced"
    COMPOSITE = "composite"
    DERIVED = "derived"
    CUSTOM = "custom"


class DependencyType(Enum):
    """Types of dependencies between formulas"""

    DIRECT = "direct"  # Formula A directly uses Formula B
    INDIRECT = "indirect"  # Formula A uses Formula B through another formula
    COMPONENT = "component"  # Formula A is a component of Formula B
    DERIVED = "derived"  # Formula A is derived from Formula B


@dataclass
class FormulaNode:
    """Represents a formula in the dependency graph"""

    formula_id: str
    name: str
    formula: str
    variables: List[str]
    formula_type: FormulaType
    description: Optional[str] = None
    complexity_score: int = 1
    usage_frequency: int = 0
    category: Optional[str] = None
    source: Optional[str] = None


@dataclass
class FormulaDependency:
    """Represents a dependency between two formulas"""

    source_id: str
    target_id: str
    dependency_type: DependencyType
    strength: float = 1.0  # 0.0 to 1.0, how strong the dependency is
    description: Optional[str] = None


@dataclass
class DependencyGraph:
    """Container for the complete dependency graph"""

    nodes: Dict[str, FormulaNode] = field(default_factory=dict)
    dependencies: List[FormulaDependency] = field(default_factory=list)
    categories: Dict[str, List[str]] = field(default_factory=dict)


def check_dependencies():
    """Check if required libraries are available."""
    if not SYMPY_AVAILABLE:
        raise ToolError(
            "SymPy is required for formula dependency analysis. Please install it: pip install sympy"
        )
    if not NETWORKX_AVAILABLE:
        raise ToolError(
            "NetworkX and Matplotlib are required for graph visualization. Please install them: pip install networkx matplotlib"
        )


@log_operation("formula_dependency_create_graph")
def create_formula_dependency_graph(
    formulas: Optional[Dict[str, Dict[str, Any]]] = None,
    analyze_dependencies: bool = True,
    include_custom_formulas: bool = True,
) -> DependencyGraph:
    """
    Create a dependency graph from a collection of formulas.

    Args:
        formulas: Dictionary of formula definitions (if None, will get from algebra_helper)
        analyze_dependencies: Whether to analyze dependencies between formulas
        include_custom_formulas: Whether to include custom formulas in analysis

    Returns:
        DependencyGraph object containing nodes and dependencies

    Raises:
        ValidationError: If input data is invalid or dependencies are missing
    """
    logger.info("Creating formula dependency graph...")
    check_dependencies()

    # If no formulas provided, get them from algebra_helper
    if formulas is None:
        try:
            from .algebra_helper import get_sports_formula

            # Get all available formula names by calling the function with a dummy name
            # and catching the error to see what's available
            available_formulas = [
                "per",
                "true_shooting",
                "usage_rate",
                "four_factors_shooting",
                "four_factors_turnovers",
                "pace",
                "vorp",
                "ws_per_48",
                "game_score",
                "pie",
                "bpm_offensive",
                "bpm_defensive",
                "win_shares_offensive",
                "corner_3pt_pct",
                "rim_fg_pct",
                "midrange_efficiency",
                "catch_and_shoot_pct",
                "defensive_win_shares",
                "steal_percentage",
                "block_percentage",
                "defensive_rating",
                "net_rating",
                "offensive_efficiency",
                "defensive_efficiency",
                "pace_factor",
                "clutch_performance",
                "on_off_differential",
                "plus_minus_per_100",
                "assist_percentage",
                "rebound_percentage",
                "turnover_percentage",
                "free_throw_rate",
                "effective_field_goal_percentage",
                "true_shooting_percentage",
                "player_efficiency_rating",
                "pace_adjusted_stats",
                "clutch_time_rating",
                "defensive_impact",
                "offensive_impact",
                "shooting_efficiency_differential",
                "possession_usage",
                "defensive_rebound_percentage",
                "offensive_rebound_percentage",
                "team_efficiency_differential",
                "pace_adjusted_offensive_rating",
                "pace_adjusted_defensive_rating",
            ]

            # Build formulas dictionary by calling get_sports_formula for each
            formulas = {}
            for formula_name in available_formulas:
                try:
                    # Call with minimal data to get the formula structure
                    result = get_sports_formula(
                        formula_name,
                        **{
                            var: 1.0
                            for var in [
                                "PTS",
                                "FGA",
                                "FTA",
                                "FGM",
                                "STL",
                                "3PM",
                                "FTM",
                                "BLK",
                                "OREB",
                                "AST",
                                "DREB",
                                "PF",
                                "TOV",
                                "MP",
                                "REB",
                                "USG",
                                "WS",
                                "BPM",
                                "VORP",
                                "PER",
                                "TS",
                                "EFG",
                                "USG_PCT",
                                "PACE",
                                "ORtg",
                                "DRtg",
                                "NetRtg",
                                "OBPM",
                                "DBPM",
                                "OWS",
                                "DWS",
                                "AST_PCT",
                                "REB_PCT",
                                "TOV_PCT",
                                "FTR",
                                "EFG_PCT",
                                "TS_PCT",
                                "DRB_PCT",
                                "ORB_PCT",
                                "POSS_PCT",
                                "TEAM_GAMES",
                                "TEAM_MINUTES",
                                "TEAM_FGM",
                                "TEAM_FGA",
                                "TEAM_FTM",
                                "TEAM_FTA",
                                "TEAM_TOV",
                                "TEAM_ORB",
                                "TEAM_DRB",
                                "TEAM_PACE",
                                "TEAM_ORtg",
                                "TEAM_DRtg",
                                "TEAM_NetRtg",
                                "TEAM_OBPM",
                                "TEAM_DBPM",
                                "TEAM_OWS",
                                "TEAM_DWS",
                                "TEAM_AST_PCT",
                                "TEAM_REB_PCT",
                                "TEAM_TOV_PCT",
                                "TEAM_FTR",
                                "TEAM_EFG_PCT",
                                "TEAM_TS_PCT",
                                "TEAM_DRB_PCT",
                                "TEAM_ORB_PCT",
                                "TEAM_POSS_PCT",
                            ]
                        },
                    )
                    if "formula" in result:
                        formulas[formula_name] = {
                            "formula": result["formula"],
                            "variables": result.get("variables", []),
                            "description": result.get("description", ""),
                            "name": formula_name.replace("_", " ").title(),
                        }
                except Exception as e:
                    logger.warning(f"Could not get formula {formula_name}: {e}")
                    continue
        except ImportError:
            logger.error("Could not import get_sports_formula from algebra_helper")
            raise ValidationError("Could not access sports formulas")

    graph = DependencyGraph()

    # Add formula nodes
    for formula_id, formula_data in formulas.items():
        try:
            node = FormulaNode(
                formula_id=formula_id,
                name=formula_data.get("name", formula_id),
                formula=formula_data["formula"],
                variables=formula_data.get("variables", []),
                formula_type=_determine_formula_type(formula_id, formula_data),
                description=formula_data.get("description", ""),
                complexity_score=_calculate_complexity_score(formula_data["formula"]),
                category=formula_data.get("category", "general"),
            )
            graph.nodes[formula_id] = node

            # Add to category
            category = node.category
            if category not in graph.categories:
                graph.categories[category] = []
            graph.categories[category].append(formula_id)

        except Exception as e:
            logger.warning(f"Failed to add formula {formula_id}: {e}")
            continue

    # Analyze dependencies if requested
    if analyze_dependencies:
        graph.dependencies = _analyze_formula_dependencies(graph.nodes)

    logger.info(
        f"Created dependency graph with {len(graph.nodes)} nodes and {len(graph.dependencies)} dependencies"
    )
    return graph


def _determine_formula_type(
    formula_id: str, formula_data: Dict[str, Any]
) -> FormulaType:
    """Determine the type of a formula based on its characteristics."""
    formula = formula_data.get("formula", "")
    variables = formula_data.get("variables", [])

    # Check for composite formulas (formulas that reference other formulas)
    if any(var in formula for var in ["PER", "TS%", "USG%", "WS", "BPM"]):
        return FormulaType.COMPOSITE

    # Check for advanced metrics
    advanced_keywords = ["win shares", "box plus minus", "vorp", "pace", "rating"]
    if any(keyword in formula_id.lower() for keyword in advanced_keywords):
        return FormulaType.ADVANCED

    # Check for derived formulas
    if len(variables) > 5 or "+" in formula or "-" in formula:
        return FormulaType.DERIVED

    return FormulaType.BASIC


def _calculate_complexity_score(formula: str) -> int:
    """Calculate complexity score for a formula (1-10 scale)."""
    score = 1

    # Add points for mathematical operations
    score += formula.count("+") + formula.count("-")
    score += formula.count("*") + formula.count("/")
    score += formula.count("**") * 2  # Exponents are more complex
    score += formula.count("(") + formula.count(")")

    # Add points for complex functions
    complex_functions = ["sqrt", "log", "exp", "sin", "cos", "tan"]
    for func in complex_functions:
        score += formula.count(func) * 2

    # Cap at 10
    return min(score, 10)


def _analyze_formula_dependencies(
    nodes: Dict[str, FormulaNode],
) -> List[FormulaDependency]:
    """Analyze dependencies between formulas."""
    dependencies = []

    for source_id, source_node in nodes.items():
        for target_id, target_node in nodes.items():
            if source_id == target_id:
                continue

            # Check if source formula uses variables from target formula
            source_vars = set(source_node.variables)
            target_vars = set(target_node.variables)

            # Direct dependency: source uses target's variables
            if source_vars.intersection(target_vars):
                overlap = len(source_vars.intersection(target_vars))
                strength = overlap / len(source_vars) if source_vars else 0

                if strength > 0.1:  # Only include meaningful dependencies
                    dependency = FormulaDependency(
                        source_id=source_id,
                        target_id=target_id,
                        dependency_type=DependencyType.DIRECT,
                        strength=strength,
                        description=f"{source_node.name} uses variables from {target_node.name}",
                    )
                    dependencies.append(dependency)

            # Check for formula references in the formula string
            if target_node.name.lower() in source_node.formula.lower():
                dependency = FormulaDependency(
                    source_id=source_id,
                    target_id=target_id,
                    dependency_type=DependencyType.COMPONENT,
                    strength=0.8,
                    description=f"{source_node.name} references {target_node.name}",
                )
                dependencies.append(dependency)

    return dependencies


@log_operation("formula_dependency_visualize_graph")
def visualize_dependency_graph(
    graph: DependencyGraph,
    layout: str = "spring",
    show_labels: bool = True,
    node_size: int = 1000,
    edge_width: float = 1.0,
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a visualization of the formula dependency graph.

    Args:
        graph: The dependency graph to visualize
        layout: Layout algorithm ('spring', 'circular', 'hierarchical')
        show_labels: Whether to show node labels
        node_size: Size of nodes in the visualization
        edge_width: Width of edges
        save_path: Optional path to save the visualization

    Returns:
        Dictionary with visualization metadata and statistics

    Raises:
        ValidationError: If visualization fails
    """
    logger.info("Creating dependency graph visualization...")
    check_dependencies()

    # Create NetworkX graph
    G = nx.DiGraph()

    # Add nodes
    for formula_id, node in graph.nodes.items():
        G.add_node(
            formula_id,
            **{
                "name": node.name,
                "formula_type": node.formula_type.value,
                "complexity": node.complexity_score,
                "category": node.category,
            },
        )

    # Add edges
    for dep in graph.dependencies:
        G.add_edge(
            dep.source_id,
            dep.target_id,
            weight=dep.strength,
            dependency_type=dep.dependency_type.value,
        )

    # Create visualization
    plt.figure(figsize=(16, 12))

    # Choose layout
    if layout == "spring":
        pos = nx.spring_layout(G, k=3, iterations=50)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "hierarchical":
        pos = (
            nx.nx_agraph.graphviz_layout(G, prog="dot")
            if hasattr(nx, "nx_agraph")
            else nx.spring_layout(G)
        )
    else:
        pos = nx.spring_layout(G)

    # Color nodes by formula type
    node_colors = []
    type_colors = {
        FormulaType.BASIC.value: "#FF6B6B",
        FormulaType.ADVANCED.value: "#4ECDC4",
        FormulaType.COMPOSITE.value: "#45B7D1",
        FormulaType.DERIVED.value: "#96CEB4",
        FormulaType.CUSTOM.value: "#FFEAA7",
    }

    for node in G.nodes():
        node_data = G.nodes[node]
        formula_type = node_data.get("formula_type", FormulaType.BASIC.value)
        node_colors.append(type_colors.get(formula_type, "#95A5A6"))

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, node_color=node_colors, node_size=node_size, alpha=0.8
    )

    # Draw edges with different styles for different dependency types
    edge_colors = []
    edge_styles = []

    for edge in G.edges():
        edge_data = G.edges[edge]
        dep_type = edge_data.get("dependency_type", DependencyType.DIRECT.value)

        if dep_type == DependencyType.DIRECT.value:
            edge_colors.append("#2C3E50")
            edge_styles.append("solid")
        elif dep_type == DependencyType.COMPONENT.value:
            edge_colors.append("#E74C3C")
            edge_styles.append("dashed")
        elif dep_type == DependencyType.DERIVED.value:
            edge_colors.append("#3498DB")
            edge_styles.append("dotted")
        else:
            edge_colors.append("#95A5A6")
            edge_styles.append("solid")

    # Draw edges
    for i, (edge, color, style) in enumerate(zip(G.edges(), edge_colors, edge_styles)):
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[edge],
            edge_color=color,
            style=style,
            width=edge_width,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle="->",
        )

    # Draw labels
    if show_labels:
        labels = {node: graph.nodes[node].name for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight="bold")

    # Create legend
    legend_elements = [
        mpatches.Patch(color=color, label=formula_type.replace("_", " ").title())
        for formula_type, color in type_colors.items()
    ]
    plt.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.15, 1))

    plt.title(
        "Sports Analytics Formula Dependency Graph", fontsize=16, fontweight="bold"
    )
    plt.axis("off")
    plt.tight_layout()

    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Graph visualization saved to {save_path}")

    # Calculate statistics
    stats = {
        "total_nodes": len(G.nodes()),
        "total_edges": len(G.edges()),
        "average_degree": (
            sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0
        ),
        "strongly_connected_components": len(list(nx.strongly_connected_components(G))),
        "formula_types": {
            ft.value: sum(
                1 for n in G.nodes() if G.nodes[n].get("formula_type") == ft.value
            )
            for ft in FormulaType
        },
        "dependency_types": {
            dt.value: sum(1 for d in graph.dependencies if d.dependency_type == dt)
            for dt in DependencyType
        },
    }

    plt.show()

    return {
        "status": "success",
        "visualization_created": True,
        "statistics": stats,
        "save_path": save_path,
    }


@log_operation("formula_dependency_find_paths")
def find_dependency_paths(
    graph: DependencyGraph, source_formula: str, target_formula: str, max_depth: int = 5
) -> Dict[str, Any]:
    """
    Find all dependency paths between two formulas.

    Args:
        graph: The dependency graph
        source_formula: Starting formula ID
        target_formula: Target formula ID
        max_depth: Maximum path depth to search

    Returns:
        Dictionary with found paths and analysis

    Raises:
        ValidationError: If formulas don't exist or analysis fails
    """
    logger.info(f"Finding dependency paths from {source_formula} to {target_formula}")
    check_dependencies()

    if source_formula not in graph.nodes:
        raise ValidationError(f"Source formula '{source_formula}' not found in graph")
    if target_formula not in graph.nodes:
        raise ValidationError(f"Target formula '{target_formula}' not found in graph")

    # Create NetworkX graph
    G = nx.DiGraph()
    for dep in graph.dependencies:
        G.add_edge(dep.source_id, dep.target_id, weight=dep.strength)

    # Find all simple paths
    try:
        paths = list(
            nx.all_simple_paths(G, source_formula, target_formula, cutoff=max_depth)
        )
    except nx.NetworkXNoPath:
        paths = []

    # Analyze paths
    path_analysis = []
    for i, path in enumerate(paths):
        path_strength = 1.0
        path_description = []

        for j in range(len(path) - 1):
            source = path[j]
            target = path[j + 1]

            # Find dependency strength
            for dep in graph.dependencies:
                if dep.source_id == source and dep.target_id == target:
                    path_strength *= dep.strength
                    path_description.append(
                        f"{graph.nodes[source].name} → {graph.nodes[target].name}"
                    )
                    break

        path_analysis.append(
            {
                "path_id": i + 1,
                "path": path,
                "strength": path_strength,
                "length": len(path) - 1,
                "description": " → ".join(path_description),
            }
        )

    # Sort by strength
    path_analysis.sort(key=lambda x: x["strength"], reverse=True)

    return {
        "status": "success",
        "source_formula": source_formula,
        "target_formula": target_formula,
        "total_paths": len(paths),
        "paths": path_analysis,
        "shortest_path_length": (
            min([p["length"] for p in path_analysis]) if path_analysis else None
        ),
        "strongest_path": path_analysis[0] if path_analysis else None,
    }


@log_operation("formula_dependency_analyze_complexity")
def analyze_formula_complexity(
    graph: DependencyGraph, formula_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze the complexity of formulas in the dependency graph.

    Args:
        graph: The dependency graph
        formula_id: Optional specific formula to analyze

    Returns:
        Dictionary with complexity analysis

    Raises:
        ValidationError: If analysis fails
    """
    logger.info("Analyzing formula complexity...")
    check_dependencies()

    if formula_id and formula_id not in graph.nodes:
        raise ValidationError(f"Formula '{formula_id}' not found in graph")

    # Create NetworkX graph for analysis
    G = nx.DiGraph()
    for dep in graph.dependencies:
        G.add_edge(dep.source_id, dep.target_id)

    if formula_id:
        # Analyze specific formula
        node = graph.nodes[formula_id]

        # Calculate centrality measures
        in_degree = G.in_degree(formula_id)
        out_degree = G.out_degree(formula_id)

        # Find dependencies
        dependencies = [
            dep for dep in graph.dependencies if dep.source_id == formula_id
        ]
        dependents = [dep for dep in graph.dependencies if dep.target_id == formula_id]

        analysis = {
            "formula_id": formula_id,
            "formula_name": node.name,
            "complexity_score": node.complexity_score,
            "formula_type": node.formula_type.value,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "total_dependencies": len(dependencies),
            "total_dependents": len(dependents),
            "dependencies": [
                {
                    "target": dep.target_id,
                    "strength": dep.strength,
                    "type": dep.dependency_type.value,
                }
                for dep in dependencies
            ],
            "dependents": [
                {
                    "source": dep.source_id,
                    "strength": dep.strength,
                    "type": dep.dependency_type.value,
                }
                for dep in dependents
            ],
        }
    else:
        # Analyze all formulas - only for nodes that exist in the NetworkX graph
        graph_node_ids = list(G.nodes())
        complexity_scores = [
            node.complexity_score
            for node_id, node in graph.nodes.items()
            if node_id in G
        ]
        in_degrees = [len(list(G.predecessors(node_id))) for node_id in graph_node_ids]
        out_degrees = [len(list(G.successors(node_id))) for node_id in graph_node_ids]

        # Find most complex formulas
        most_complex = sorted(
            [(node_id, node) for node_id, node in graph.nodes.items() if node_id in G],
            key=lambda x: x[1].complexity_score,
            reverse=True,
        )[:5]

        # Find most connected formulas
        most_connected = sorted(
            [(node_id, node) for node_id, node in graph.nodes.items() if node_id in G],
            key=lambda x: len(list(G.neighbors(x[0]))) if x[0] in G else 0,
            reverse=True,
        )[:5]

        analysis = {
            "total_formulas": len(graph.nodes),
            "average_complexity": (
                sum(complexity_scores) / len(complexity_scores)
                if complexity_scores
                else 0
            ),
            "max_complexity": max(complexity_scores) if complexity_scores else 0,
            "min_complexity": min(complexity_scores) if complexity_scores else 0,
            "average_in_degree": sum(in_degrees) / len(in_degrees) if in_degrees else 0,
            "average_out_degree": (
                sum(out_degrees) / len(out_degrees) if out_degrees else 0
            ),
            "most_complex_formulas": [
                {"id": fid, "name": node.name, "complexity": node.complexity_score}
                for fid, node in most_complex
            ],
            "most_connected_formulas": [
                {"id": fid, "name": node.name, "degree": G.degree(fid)}
                for fid, node in most_connected
            ],
        }

    return {"status": "success", "analysis": analysis}


@log_operation("formula_dependency_export_graph")
def export_dependency_graph(
    graph: DependencyGraph, format: str = "json", include_visualization: bool = False
) -> Dict[str, Any]:
    """
    Export the dependency graph in various formats.

    Args:
        graph: The dependency graph to export
        format: Export format ('json', 'graphml', 'gexf')
        include_visualization: Whether to include visualization data

    Returns:
        Dictionary with export information

    Raises:
        ValidationError: If export fails
    """
    logger.info(f"Exporting dependency graph in {format} format...")
    check_dependencies()

    export_data = {
        "metadata": {
            "total_nodes": len(graph.nodes),
            "total_dependencies": len(graph.dependencies),
            "categories": list(graph.categories.keys()),
            "export_format": format,
        },
        "nodes": {},
        "dependencies": [],
    }

    # Export nodes
    for formula_id, node in graph.nodes.items():
        export_data["nodes"][formula_id] = {
            "name": node.name,
            "formula": node.formula,
            "variables": node.variables,
            "formula_type": node.formula_type.value,
            "description": node.description,
            "complexity_score": node.complexity_score,
            "category": node.category,
        }

    # Export dependencies
    for dep in graph.dependencies:
        export_data["dependencies"].append(
            {
                "source_id": dep.source_id,
                "target_id": dep.target_id,
                "dependency_type": dep.dependency_type.value,
                "strength": dep.strength,
                "description": dep.description,
            }
        )

    # Add visualization data if requested
    if include_visualization:
        try:
            viz_result = visualize_dependency_graph(graph, save_path=None)
            export_data["visualization"] = viz_result["statistics"]
        except Exception as e:
            logger.warning(f"Failed to include visualization data: {e}")

    return {
        "status": "success",
        "export_format": format,
        "export_data": export_data,
        "node_count": len(graph.nodes),
        "dependency_count": len(graph.dependencies),
    }
