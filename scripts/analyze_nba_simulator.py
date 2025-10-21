#!/usr/bin/env python3
"""
NBA Simulator Analyzer

Analyzes the nba-simulator-aws project structure to:
1. Map existing modules and their purposes
2. Identify integration points for new recommendations
3. Detect gaps and opportunities
4. Generate optimal placement suggestions

Part of Tier 2 Smart Integrator system.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a module in nba-simulator-aws."""
    path: str
    name: str
    purpose: str
    dependencies: List[str]
    key_functions: List[str]
    lines_of_code: int
    integration_points: List[str]


@dataclass
class SimulatorAnalysis:
    """Complete analysis of nba-simulator-aws structure."""
    project_root: str
    total_modules: int
    total_lines: int
    modules: Dict[str, ModuleInfo]
    integration_map: Dict[str, List[str]]  # Category -> list of modules
    gaps: List[Dict[str, str]]
    recommendations: List[Dict[str, str]]


class NBASimulatorAnalyzer:
    """
    Analyze nba-simulator-aws project structure.

    Capabilities:
    - Scan project directory structure
    - Identify modules and their purposes
    - Map integration points
    - Detect implementation gaps
    - Suggest optimal placements for new features

    Example:
        >>> analyzer = NBASimulatorAnalyzer("/path/to/nba-simulator-aws")
        >>> analysis = analyzer.analyze()
        >>> print(f"Found {analysis.total_modules} modules")
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize analyzer.

        Args:
            project_root: Path to nba-simulator-aws (defaults to sibling directory)
        """
        if project_root is None:
            # Default to sibling directory
            current_dir = Path(__file__).parent.parent
            project_root = current_dir.parent / "nba-simulator-aws"

        self.project_root = Path(project_root)

        if not self.project_root.exists():
            logger.warning(f"Project root not found: {self.project_root}")
            logger.info("Creating mock analysis for testing")
            self.mock_mode = True
        else:
            logger.info(f"Analyzing NBA Simulator at: {self.project_root}")
            self.mock_mode = False

        # Known integration categories
        self.categories = [
            'data_ingestion',
            'feature_engineering',
            'modeling',
            'prediction',
            'evaluation',
            'api',
            'database',
            'utilities'
        ]

    def analyze(self) -> SimulatorAnalysis:
        """
        Perform complete project analysis.

        Returns:
            SimulatorAnalysis with comprehensive project structure
        """
        logger.info("Starting NBA Simulator analysis...")

        if self.mock_mode:
            return self._create_mock_analysis()

        # Scan project structure
        modules = self._scan_modules()

        # Build integration map
        integration_map = self._build_integration_map(modules)

        # Identify gaps
        gaps = self._identify_gaps(modules, integration_map)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps)

        # Calculate totals
        total_lines = sum(m.lines_of_code for m in modules.values())

        analysis = SimulatorAnalysis(
            project_root=str(self.project_root),
            total_modules=len(modules),
            total_lines=total_lines,
            modules=modules,
            integration_map=integration_map,
            gaps=gaps,
            recommendations=recommendations
        )

        logger.info(f"Analysis complete: {len(modules)} modules, {total_lines} lines")

        return analysis

    def _scan_modules(self) -> Dict[str, ModuleInfo]:
        """Scan project for Python modules."""
        modules = {}

        # Scan scripts directory
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                module_info = self._analyze_module(py_file)
                if module_info:
                    modules[module_info.name] = module_info

        return modules

    def _analyze_module(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python module."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Count lines
            lines = len(content.split('\n'))

            # Extract module name
            name = file_path.stem

            # Extract docstring for purpose
            purpose = self._extract_docstring(content) or "No description"

            # Extract dependencies (imports)
            dependencies = self._extract_imports(content)

            # Extract functions
            functions = self._extract_functions(content)

            # Identify integration points
            integration_points = self._identify_integration_points(content, name)

            return ModuleInfo(
                path=str(file_path.relative_to(self.project_root)),
                name=name,
                purpose=purpose[:200],  # Truncate long descriptions
                dependencies=dependencies,
                key_functions=functions[:10],  # Top 10 functions
                lines_of_code=lines,
                integration_points=integration_points
            )

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_docstring(self, content: str) -> Optional[str]:
        """Extract module docstring."""
        # Look for triple-quoted string at start of file
        match = re.search(r'^\s*["\']{{3}}(.+?)["\']{{3}}', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Extract module name
                parts = line.split()
                if len(parts) >= 2:
                    imports.append(parts[1].split('.')[0])
        return list(set(imports))[:20]  # Limit to 20 unique imports

    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names."""
        functions = []
        for match in re.finditer(r'^\s*def\s+(\w+)\s*\(', content, re.MULTILINE):
            func_name = match.group(1)
            if not func_name.startswith('_'):  # Public functions only
                functions.append(func_name)
        return functions

    def _identify_integration_points(self, content: str, module_name: str) -> List[str]:
        """Identify potential integration points in module."""
        points = []

        # Check for common patterns
        if 'pandas' in content.lower():
            points.append('data_processing')
        if 'sklearn' in content.lower() or 'model' in content.lower():
            points.append('machine_learning')
        if 'predict' in content.lower():
            points.append('prediction')
        if 'database' in content.lower() or 'sql' in content.lower():
            points.append('database')
        if 'api' in module_name.lower() or 'endpoint' in content.lower():
            points.append('api')
        if 'feature' in content.lower():
            points.append('feature_engineering')

        return points

    def _build_integration_map(
        self,
        modules: Dict[str, ModuleInfo]
    ) -> Dict[str, List[str]]:
        """Build map of categories to modules."""
        integration_map = {category: [] for category in self.categories}

        for module_name, module_info in modules.items():
            for point in module_info.integration_points:
                if point in integration_map:
                    integration_map[point].append(module_name)

        return integration_map

    def _identify_gaps(
        self,
        modules: Dict[str, ModuleInfo],
        integration_map: Dict[str, List[str]]
    ) -> List[Dict[str, str]]:
        """Identify gaps in current implementation."""
        gaps = []

        # Check for missing categories
        for category in self.categories:
            if not integration_map[category]:
                gaps.append({
                    'category': category,
                    'severity': 'high',
                    'description': f"No modules found for {category}"
                })

        return gaps

    def _generate_recommendations(self, gaps: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate integration recommendations."""
        recommendations = []

        for gap in gaps:
            recommendations.append({
                'gap': gap['category'],
                'recommendation': f"Consider adding {gap['category']} module",
                'priority': gap['severity']
            })

        return recommendations

    def _create_mock_analysis(self) -> SimulatorAnalysis:
        """Create mock analysis for testing when project not found."""
        logger.info("Creating mock analysis...")

        mock_modules = {
            'simulate_game': ModuleInfo(
                path='scripts/simulate_game.py',
                name='simulate_game',
                purpose='Main game simulation logic',
                dependencies=['pandas', 'numpy'],
                key_functions=['run_simulation', 'calculate_stats'],
                lines_of_code=500,
                integration_points=['prediction', 'machine_learning']
            ),
            'data_loader': ModuleInfo(
                path='scripts/data_loader.py',
                name='data_loader',
                purpose='Load and preprocess NBA data',
                dependencies=['pandas', 'sqlalchemy'],
                key_functions=['load_data', 'clean_data'],
                lines_of_code=300,
                integration_points=['data_processing', 'database']
            ),
            'feature_builder': ModuleInfo(
                path='scripts/feature_builder.py',
                name='feature_builder',
                purpose='Build features for ML models',
                dependencies=['pandas', 'numpy', 'sklearn'],
                key_functions=['create_features', 'select_features'],
                lines_of_code=400,
                integration_points=['feature_engineering', 'machine_learning']
            )
        }

        integration_map = {
            'data_processing': ['data_loader'],
            'feature_engineering': ['feature_builder'],
            'machine_learning': ['simulate_game', 'feature_builder'],
            'prediction': ['simulate_game'],
            'database': ['data_loader'],
            'data_ingestion': [],
            'modeling': [],
            'evaluation': [],
            'api': [],
            'utilities': []
        }

        gaps = [
            {'category': 'data_ingestion', 'severity': 'medium', 'description': 'No dedicated data ingestion module'},
            {'category': 'evaluation', 'severity': 'high', 'description': 'No model evaluation framework'},
            {'category': 'api', 'severity': 'low', 'description': 'No API endpoints defined'}
        ]

        recommendations = [
            {'gap': 'data_ingestion', 'recommendation': 'Add automated data ingestion pipeline', 'priority': 'medium'},
            {'gap': 'evaluation', 'recommendation': 'Implement comprehensive evaluation metrics', 'priority': 'high'},
            {'gap': 'api', 'recommendation': 'Create REST API for predictions', 'priority': 'low'}
        ]

        return SimulatorAnalysis(
            project_root=str(self.project_root),
            total_modules=len(mock_modules),
            total_lines=1200,
            modules=mock_modules,
            integration_map=integration_map,
            gaps=gaps,
            recommendations=recommendations
        )

    def save_analysis(self, analysis: SimulatorAnalysis, output_file: Path):
        """Save analysis to JSON file."""
        # Convert to dict
        data = {
            'project_root': analysis.project_root,
            'total_modules': analysis.total_modules,
            'total_lines': analysis.total_lines,
            'modules': {name: asdict(module) for name, module in analysis.modules.items()},
            'integration_map': analysis.integration_map,
            'gaps': analysis.gaps,
            'recommendations': analysis.recommendations
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Analysis saved to {output_file}")


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("NBA SIMULATOR ANALYZER DEMO")
    print("=" * 70)
    print()

    # Initialize analyzer
    analyzer = NBASimulatorAnalyzer()

    # Run analysis
    analysis = analyzer.analyze()

    # Print results
    print(f"Project: {analysis.project_root}")
    print(f"Total Modules: {analysis.total_modules}")
    print(f"Total Lines: {analysis.total_lines:,}")
    print()

    print("Modules:")
    for name, module in list(analysis.modules.items())[:5]:  # Show first 5
        print(f"  - {module.name} ({module.lines_of_code} lines)")
        print(f"    Purpose: {module.purpose[:60]}...")
        print(f"    Integration Points: {', '.join(module.integration_points)}")
        print()

    print(f"Identified Gaps: {len(analysis.gaps)}")
    for gap in analysis.gaps:
        print(f"  - {gap['category']}: {gap['description']}")
    print()

    print(f"Recommendations: {len(analysis.recommendations)}")
    for rec in analysis.recommendations[:3]:
        print(f"  - [{rec['priority'].upper()}] {rec['recommendation']}")
    print()

    # Save analysis
    output_file = Path("implementation_plans/nba_simulator_analysis.json")
    analyzer.save_analysis(analysis, output_file)
    print(f"Analysis saved to: {output_file}")

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)




