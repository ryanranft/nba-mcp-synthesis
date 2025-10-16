#!/usr/bin/env python3
"""
Interactive Formula Playground

This module provides a web-based interactive playground for experimenting with
sports analytics formulas, featuring real-time validation, visualization, and
collaborative features.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import sympy as sp
from sympy import latex, simplify, expand, factor, diff, integrate, solve
from sympy.parsing.sympy_parser import parse_expr

# Import other modules
from .formula_intelligence import FormulaIntelligence
from .formula_builder import InteractiveFormulaBuilder
from .algebra_helper import get_sports_formula

logger = logging.getLogger(__name__)

class PlaygroundMode(Enum):
    """Playground interaction modes"""
    EXPLORE = "explore"
    LEARN = "learn"
    BUILD = "build"
    COMPARE = "compare"
    COLLABORATE = "collaborate"

class VisualizationType(Enum):
    """Types of formula visualizations"""
    LATEX = "latex"
    GRAPH = "graph"
    TABLE = "table"
    CHART = "chart"
    ANIMATION = "animation"

@dataclass
class PlaygroundSession:
    """Represents a playground session"""
    session_id: str
    user_id: str
    mode: PlaygroundMode
    formulas: List[Dict[str, Any]]
    variables: Dict[str, float]
    history: List[Dict[str, Any]]
    created_at: str
    last_modified: str
    is_shared: bool = False
    share_token: Optional[str] = None

@dataclass
class FormulaExperiment:
    """Represents a formula experiment"""
    experiment_id: str
    formula: str
    description: str
    variables: Dict[str, float]
    results: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    notes: str
    tags: List[str]
    created_at: str

@dataclass
class PlaygroundRecommendation:
    """Represents a playground recommendation"""
    type: str
    title: str
    description: str
    action: str
    priority: int
    context: Dict[str, Any]

class InteractiveFormulaPlayground:
    """
    Interactive Formula Playground with real-time experimentation capabilities.
    """

    _instance = None
    _sessions: Dict[str, PlaygroundSession] = {}
    _experiments: Dict[str, FormulaExperiment] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InteractiveFormulaPlayground, cls).__new__(cls)
            cls._instance.formula_intelligence = FormulaIntelligence()
            cls._instance.formula_builder = InteractiveFormulaBuilder()
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'formula_intelligence'):
            self.formula_intelligence = FormulaIntelligence()
            self.formula_builder = InteractiveFormulaBuilder()
        self.sessions = InteractiveFormulaPlayground._sessions
        self.experiments = InteractiveFormulaPlayground._experiments

        # Playground templates
        self.playground_templates = self._initialize_templates()

        # Visualization tools
        self.visualization_tools = {
            VisualizationType.LATEX: self._render_latex,
            VisualizationType.GRAPH: self._render_graph,
            VisualizationType.TABLE: self._render_table,
            VisualizationType.CHART: self._render_chart,
            VisualizationType.ANIMATION: self._render_animation,
        }

    def _initialize_templates(self) -> List[Dict[str, Any]]:
        """Initialize playground templates"""
        return [
            {
                "name": "Shooting Efficiency Lab",
                "description": "Explore shooting efficiency metrics and their relationships",
                "mode": PlaygroundMode.EXPLORE,
                "formulas": [
                    "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
                    "(FGM + 0.5 * 3PM) / FGA",  # eFG%
                    "FGM / FGA",  # FG%
                    "3PM / 3PA",  # 3P%
                    "FTM / FTA"   # FT%
                ],
                "variables": {
                    "PTS": 25.0, "FGM": 10.0, "FGA": 20.0, "3PM": 3.0, "3PA": 8.0,
                    "FTM": 2.0, "FTA": 3.0
                },
                "visualizations": [VisualizationType.CHART, VisualizationType.TABLE],
                "learning_objectives": [
                    "Understand the relationship between different shooting metrics",
                    "Compare efficiency across different shot types",
                    "Analyze the impact of 3-pointers on overall efficiency"
                ]
            },
            {
                "name": "Advanced Metrics Workshop",
                "description": "Deep dive into advanced basketball analytics",
                "mode": PlaygroundMode.LEARN,
                "formulas": [
                    "(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) / MP",  # PER
                    "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
                    "ORtg - DRtg",  # Net Rating
                    "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100"  # Assist %
                ],
                "variables": {
                    "FGM": 10.0, "STL": 2.0, "3PM": 3.0, "FTM": 5.0, "BLK": 1.0,
                    "OREB": 2.0, "AST": 8.0, "DREB": 6.0, "PF": 3.0, "FTA": 6.0,
                    "FGA": 18.0, "TOV": 3.0, "MP": 35.0, "TM_MP": 240.0, "TM_FGA": 90.0,
                    "TM_FTA": 25.0, "TM_TOV": 12.0, "TM_FGM": 35.0, "ORtg": 115.0, "DRtg": 108.0
                },
                "visualizations": [VisualizationType.GRAPH, VisualizationType.TABLE],
                "learning_objectives": [
                    "Master advanced basketball metrics",
                    "Understand player efficiency calculations",
                    "Analyze team impact metrics"
                ]
            },
            {
                "name": "Formula Builder Studio",
                "description": "Create and test custom formulas",
                "mode": PlaygroundMode.BUILD,
                "formulas": [],
                "variables": {},
                "visualizations": [VisualizationType.LATEX, VisualizationType.GRAPH],
                "learning_objectives": [
                    "Learn to construct custom formulas",
                    "Understand mathematical relationships",
                    "Validate formula correctness"
                ]
            },
            {
                "name": "Player Comparison Lab",
                "description": "Compare players using different metrics",
                "mode": PlaygroundMode.COMPARE,
                "formulas": [
                    "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
                    "(FGM + 0.5 * 3PM) / FGA",  # eFG%
                    "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100"  # Usage Rate
                ],
                "variables": {
                    "Player1_PTS": 25.0, "Player1_FGA": 20.0, "Player1_FTA": 5.0,
                    "Player1_FGM": 10.0, "Player1_3PM": 3.0, "Player1_FGM": 10.0,
                    "Player1_FGA": 20.0, "Player1_FTA": 5.0, "Player1_TOV": 3.0,
                    "Player1_MP": 35.0, "Player1_TM_MP": 240.0, "Player1_TM_FGA": 90.0,
                    "Player1_TM_FTA": 25.0, "Player1_TM_TOV": 12.0,
                    "Player2_PTS": 22.0, "Player2_FGA": 18.0, "Player2_FTA": 4.0,
                    "Player2_FGM": 9.0, "Player2_3PM": 2.0, "Player2_FGM": 9.0,
                    "Player2_FGA": 18.0, "Player2_FTA": 4.0, "Player2_TOV": 2.0,
                    "Player2_MP": 32.0, "Player2_TM_MP": 240.0, "Player2_TM_FGA": 90.0,
                    "Player2_TM_FTA": 25.0, "Player2_TM_TOV": 12.0
                },
                "visualizations": [VisualizationType.CHART, VisualizationType.TABLE],
                "learning_objectives": [
                    "Compare players across multiple metrics",
                    "Identify strengths and weaknesses",
                    "Understand relative performance"
                ]
            }
        ]

    def create_session(self, user_id: str, mode: PlaygroundMode, template_name: str = None) -> PlaygroundSession:
        """Create a new playground session"""
        import uuid
        from datetime import datetime

        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Use template if specified
        if template_name:
            template = next((t for t in self.playground_templates if t["name"] == template_name), None)
            if template:
                formulas = template["formulas"]
                variables = template["variables"]
            else:
                formulas = []
                variables = {}
        else:
            formulas = []
            variables = {}

        session = PlaygroundSession(
            session_id=session_id,
            user_id=user_id,
            mode=mode,
            formulas=formulas,
            variables=variables,
            history=[],
            created_at=now,
            last_modified=now
        )

        self.sessions[session_id] = session
        return session

    def add_formula_to_session(self, session_id: str, formula: str, description: str = "") -> Dict[str, Any]:
        """Add a formula to a playground session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Validate formula
        validation_result = self.formula_builder.validate_formula(formula)

        if not validation_result.is_valid:
            return {
                "success": False,
                "error": f"Invalid formula: {', '.join(validation_result.errors)}",
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions
            }

        # Analyze formula
        analysis = self.formula_intelligence.analyze_formula(formula)

        # Create formula entry
        formula_entry = {
            "id": str(len(session.formulas)),
            "formula": formula,
            "description": description,
            "analysis": analysis,
            "validation": asdict(validation_result),
            "created_at": session.last_modified
        }

        session.formulas.append(formula_entry)
        session.last_modified = datetime.now().isoformat()

        # Add to history
        session.history.append({
            "action": "add_formula",
            "formula": formula,
            "timestamp": session.last_modified
        })

        return {
            "success": True,
            "formula_entry": formula_entry,
            "session_updated": True
        }

    def update_variables(self, session_id: str, variables: Dict[str, float]) -> Dict[str, Any]:
        """Update variables for a session"""
        if session_id not in self.sessions:
            return {
                "success": False,
                "errors": {"session_id": f"Session {session_id} not found"},
                "message": f"Session {session_id} not found"
            }

        session = self.sessions[session_id]

        # Validate variables
        validation_results = {}
        for var, value in variables.items():
            if var in self.formula_builder.sports_variables:
                var_info = self.formula_builder.sports_variables[var]
                min_val, max_val = var_info['range']
                if not (min_val <= value <= max_val):
                    validation_results[var] = f"Value {value} out of range [{min_val}, {max_val}]"

        if validation_results:
            return {
                "success": False,
                "errors": validation_results,
                "message": "Some variables have invalid values"
            }

        # Update variables
        session.variables.update(variables)
        session.last_modified = datetime.now().isoformat()

        # Add to history
        session.history.append({
            "action": "update_variables",
            "variables": variables,
            "timestamp": session.last_modified
        })

        return {
            "success": True,
            "updated_variables": variables,
            "session_updated": True
        }

    def calculate_formula_results(self, session_id: str) -> Dict[str, Any]:
        """Calculate results for all formulas in a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        results = {}

        for i, formula_entry in enumerate(session.formulas):
            # Handle both string formulas and dictionary formulas
            if isinstance(formula_entry, str):
                formula = formula_entry
                formula_id = str(i)
            else:
                formula = formula_entry["formula"]
                formula_id = formula_entry["id"]

            try:
                # Try as sports formula first
                if formula in [f["template"] for f in self.formula_builder.formula_templates]:
                    template = next(f for f in self.formula_builder.formula_templates if f["template"] == formula)
                    result = self.formula_builder.create_formula_from_template(template["name"], session.variables)
                else:
                    # Use general formula calculation
                    result = self.formula_builder.get_formula_preview(formula, session.variables)

                results[formula_id] = {
                    "formula": formula,
                    "result": result,
                    "success": True
                }

            except Exception as e:
                results[formula_id] = {
                    "formula": formula,
                    "error": str(e),
                    "success": False
                }

        return {
            "success": True,
            "results": results,
            "variables_used": session.variables
        }

    def generate_visualizations(self, session_id: str, visualization_types: List[VisualizationType]) -> Dict[str, Any]:
        """Generate visualizations for session formulas"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        visualizations = {}

        for viz_type in visualization_types:
            if viz_type in self.visualization_tools:
                try:
                    viz_result = self.visualization_tools[viz_type](session)
                    visualizations[viz_type.value] = viz_result
                except Exception as e:
                    visualizations[viz_type.value] = {
                        "error": str(e),
                        "success": False
                    }

        return {
            "success": True,
            "visualizations": visualizations,
            "session_id": session_id
        }

    def get_recommendations(self, session_id: str) -> List[PlaygroundRecommendation]:
        """Get recommendations for improving the session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        recommendations = []

        # Analyze session content
        if len(session.formulas) == 0:
            recommendations.append(PlaygroundRecommendation(
                type="formula",
                title="Add Your First Formula",
                description="Start by adding a formula to explore",
                action="add_formula",
                priority=1,
                context={"suggestion": "PTS / (2 * (FGA + 0.44 * FTA))"}
            ))

        if len(session.variables) == 0:
            recommendations.append(PlaygroundRecommendation(
                type="variables",
                title="Set Variable Values",
                description="Add variable values to see calculated results",
                action="set_variables",
                priority=2,
                context={"suggested_variables": ["PTS", "FGA", "FTA"]}
            ))

        # Check for related formulas
        if session.formulas:
            for formula_entry in session.formulas:
                # Handle both string formulas and dictionary formulas
                if isinstance(formula_entry, str):
                    formula = formula_entry
                else:
                    formula = formula_entry["formula"]

                related_formulas = self._get_related_formulas(formula)

                for related in related_formulas:
                    if not any((f if isinstance(f, str) else f["formula"]) == related for f in session.formulas):
                        recommendations.append(PlaygroundRecommendation(
                            type="formula",
                            title=f"Try Related Formula: {related}",
                            description="This formula is related to your current formulas",
                            action="add_formula",
                            priority=3,
                            context={"suggestion": related}
                        ))

        return recommendations

    def share_session(self, session_id: str) -> Dict[str, Any]:
        """Share a session with others"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        if not session.share_token:
            import uuid
            session.share_token = str(uuid.uuid4())
            session.is_shared = True

        return {
            "success": True,
            "share_token": session.share_token,
            "share_url": f"/playground/shared/{session.share_token}",
            "session_id": session_id
        }

    def get_shared_session(self, share_token: str) -> Dict[str, Any]:
        """Get a shared session by token"""
        session = next((s for s in self.sessions.values() if s.share_token == share_token), None)

        if not session:
            return {
                "success": False,
                "error": "Shared session not found"
            }

        return {
            "success": True,
            "session": asdict(session)
        }

    def create_experiment(self, session_id: str, experiment_name: str, description: str = "") -> Dict[str, Any]:
        """Create an experiment from a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Calculate results
        results = self.calculate_formula_results(session_id)

        # Generate visualizations
        visualizations = self.generate_visualizations(session_id, [VisualizationType.LATEX, VisualizationType.CHART])

        # Create experiment
        import uuid
        from datetime import datetime

        # Get first formula, handling both string and dictionary formats
        first_formula = ""
        if session.formulas:
            first_formula = session.formulas[0] if isinstance(session.formulas[0], str) else session.formulas[0]["formula"]

        experiment = FormulaExperiment(
            experiment_id=str(uuid.uuid4()),
            formula=first_formula,
            description=description,
            variables=session.variables,
            results=results,
            visualizations=visualizations.get("visualizations", {}),
            notes="",
            tags=[],
            created_at=datetime.now().isoformat()
        )

        self.experiments[experiment.experiment_id] = experiment

        return {
            "success": True,
            "experiment": asdict(experiment)
        }

    def _render_latex(self, session: PlaygroundSession) -> Dict[str, Any]:
        """Render LaTeX visualizations"""
        latex_formulas = []

        for formula_entry in session.formulas:
            formula = formula_entry["formula"]
            try:
                expr = parse_expr(formula, evaluate=False)
                latex_formulas.append({
                    "formula": formula,
                    "latex": latex(expr),
                    "simplified": latex(simplify(expr))
                })
            except Exception as e:
                latex_formulas.append({
                    "formula": formula,
                    "error": str(e)
                })

        return {
            "success": True,
            "type": "latex",
            "formulas": latex_formulas
        }

    def _render_graph(self, session: PlaygroundSession) -> Dict[str, Any]:
        """Render graph visualizations"""
        # This would integrate with plotting libraries like matplotlib or plotly
        return {
            "success": True,
            "type": "graph",
            "message": "Graph visualization not yet implemented",
            "data": {
                "formulas": [f["formula"] for f in session.formulas],
                "variables": session.variables
            }
        }

    def _render_table(self, session: PlaygroundSession) -> Dict[str, Any]:
        """Render table visualizations"""
        results = self.calculate_formula_results(session.session_id)

        table_data = []
        for formula_entry in session.formulas:
            formula_id = formula_entry["id"]
            if formula_id in results["results"]:
                result = results["results"][formula_id]
                table_data.append({
                    "formula": formula_entry["formula"],
                    "description": formula_entry.get("description", ""),
                    "result": result.get("result", {}).get("calculated_value") if result.get("success") else None,
                    "error": result.get("error") if not result.get("success") else None
                })

        return {
            "success": True,
            "type": "table",
            "data": table_data,
            "columns": ["Formula", "Description", "Result", "Error"]
        }

    def _render_chart(self, session: PlaygroundSession) -> Dict[str, Any]:
        """Render chart visualizations"""
        # This would integrate with charting libraries
        return {
            "success": True,
            "type": "chart",
            "message": "Chart visualization not yet implemented",
            "data": {
                "formulas": [f["formula"] for f in session.formulas],
                "variables": session.variables
            }
        }

    def _render_animation(self, session: PlaygroundSession) -> Dict[str, Any]:
        """Render animation visualizations"""
        # This would integrate with animation libraries
        return {
            "success": True,
            "type": "animation",
            "message": "Animation visualization not yet implemented",
            "data": {
                "formulas": [f["formula"] for f in session.formulas],
                "variables": session.variables
            }
        }

    def _get_related_formulas(self, formula: str) -> List[str]:
        """Get formulas related to the given formula"""
        # Simple implementation - in practice, this would use more sophisticated analysis
        related = []

        if "PTS" in formula and "FGA" in formula:
            related.extend([
                "(FGM + 0.5 * 3PM) / FGA",  # eFG%
                "FGM / FGA"  # FG%
            ])

        if "FGM" in formula and "FGA" in formula:
            related.extend([
                "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
                "3PM / 3PA"  # 3P%
            ])

        return related[:3]  # Limit to 3 related formulas
