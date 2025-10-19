#!/usr/bin/env python3
"""
Smart Integrator - Generate Optimal Placement Decisions

Takes book recommendations and NBA simulator analysis to generate
intelligent placement decisions for where to integrate new features.

Features:
- Match recommendations to existing modules
- Suggest new module creation when needed
- Provide detailed integration instructions
- Generate implementation priority order

Part of Tier 2 implementation for intelligent plan management.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class RecommendationMatch:
    """Match between a recommendation and existing module."""
    recommendation_id: str
    recommendation_title: str
    matched_module: Optional[str]
    match_score: float  # 0.0 to 1.0
    integration_strategy: str  # 'extend', 'new_module', 'merge'
    target_location: str
    rationale: str
    dependencies: List[str]
    estimated_effort: str  # 'low', 'medium', 'high'


@dataclass
class IntegrationPlan:
    """Complete integration plan for all recommendations."""
    total_recommendations: int
    matched_to_existing: int
    new_modules_needed: int
    placements: List[RecommendationMatch]
    implementation_order: List[str]  # Ordered list of recommendation IDs
    summary: Dict[str, any]


class SmartIntegrator:
    """
    Generate optimal placement decisions for recommendations.
    
    Capabilities:
    - Match recommendations to existing modules
    - Detect similarity between recommendations and code
    - Suggest integration strategies
    - Generate implementation order based on dependencies
    - Estimate implementation effort
    
    Example:
        >>> integrator = SmartIntegrator(simulator_analysis, recommendations)
        >>> plan = integrator.generate_integration_plan()
        >>> print(f"Match rate: {plan.matched_to_existing}/{plan.total_recommendations}")
    """
    
    def __init__(
        self,
        simulator_analysis: Dict[str, any],
        recommendations: List[Dict[str, any]],
        match_threshold: float = 0.6
    ):
        """
        Initialize smart integrator.
        
        Args:
            simulator_analysis: Analysis from analyze_nba_simulator.py
            recommendations: List of book recommendations
            match_threshold: Minimum similarity for module matching
        """
        self.analysis = simulator_analysis
        self.recommendations = recommendations
        self.match_threshold = match_threshold
        
        logger.info(f"SmartIntegrator initialized")
        logger.info(f"  Analyzing {len(recommendations)} recommendations")
        logger.info(f"  Against {self.analysis.get('total_modules', 0)} existing modules")
    
    def generate_integration_plan(self) -> IntegrationPlan:
        """
        Generate complete integration plan.
        
        Returns:
            IntegrationPlan with placement decisions for all recommendations
        """
        logger.info("Generating integration plan...")
        
        placements = []
        matched_count = 0
        new_module_count = 0
        
        # Process each recommendation
        for i, rec in enumerate(self.recommendations):
            rec_id = rec.get('id', f"rec_{i}")
            rec_title = rec.get('title', rec.get('recommendation', 'Unknown'))
            
            # Find best matching module
            match = self._find_best_match(rec_id, rec_title, rec)
            
            if match.matched_module:
                matched_count += 1
            else:
                new_module_count += 1
            
            placements.append(match)
        
        # Generate implementation order
        implementation_order = self._generate_implementation_order(placements)
        
        # Create summary
        summary = {
            'match_rate': f"{matched_count}/{len(self.recommendations)} ({matched_count/len(self.recommendations)*100:.1f}%)",
            'new_modules': new_module_count,
            'strategies': self._count_strategies(placements),
            'total_effort': self._estimate_total_effort(placements)
        }
        
        plan = IntegrationPlan(
            total_recommendations=len(self.recommendations),
            matched_to_existing=matched_count,
            new_modules_needed=new_module_count,
            placements=placements,
            implementation_order=implementation_order,
            summary=summary
        )
        
        logger.info(f"Integration plan complete: {matched_count} matched, {new_module_count} new modules")
        
        return plan
    
    def _find_best_match(
        self,
        rec_id: str,
        rec_title: str,
        rec: Dict[str, any]
    ) -> RecommendationMatch:
        """
        Find best matching module for a recommendation.
        
        Args:
            rec_id: Recommendation ID
            rec_title: Recommendation title
            rec: Full recommendation dict
        
        Returns:
            RecommendationMatch with placement decision
        """
        modules = self.analysis.get('modules', {})
        
        if not modules:
            # No modules to match against - create new
            return self._create_new_module_placement(rec_id, rec_title, rec)
        
        # Calculate similarity with each module
        best_score = 0.0
        best_module = None
        
        for module_name, module_info in modules.items():
            score = self._calculate_module_similarity(rec_title, rec, module_info)
            if score > best_score:
                best_score = score
                best_module = module_name
        
        # Decide strategy based on match score
        if best_score >= self.match_threshold:
            # Good match - extend existing module
            return self._create_extend_placement(
                rec_id, rec_title, rec, best_module, best_score
            )
        else:
            # No good match - create new module
            return self._create_new_module_placement(rec_id, rec_title, rec)
    
    def _calculate_module_similarity(
        self,
        rec_title: str,
        rec: Dict[str, any],
        module_info: Dict[str, any]
    ) -> float:
        """Calculate similarity between recommendation and module."""
        # Compare title/name
        module_name = module_info.get('name', '')
        title_similarity = SequenceMatcher(
            None,
            rec_title.lower(),
            module_name.lower()
        ).ratio()
        
        # Compare purpose/description
        rec_desc = rec.get('description', rec.get('content', ''))
        module_purpose = module_info.get('purpose', '')
        
        desc_similarity = SequenceMatcher(
            None,
            rec_desc.lower()[:200],
            module_purpose.lower()[:200]
        ).ratio()
        
        # Compare integration points
        rec_category = rec.get('category', '').lower()
        module_points = [p.lower() for p in module_info.get('integration_points', [])]
        
        category_match = 1.0 if any(rec_category in point for point in module_points) else 0.0
        
        # Weighted combination
        similarity = (
            title_similarity * 0.4 +
            desc_similarity * 0.4 +
            category_match * 0.2
        )
        
        return similarity
    
    def _create_extend_placement(
        self,
        rec_id: str,
        rec_title: str,
        rec: Dict[str, any],
        module_name: str,
        match_score: float
    ) -> RecommendationMatch:
        """Create placement to extend existing module."""
        modules = self.analysis.get('modules', {})
        module_info = modules.get(module_name, {})
        module_path = module_info.get('path', f'scripts/{module_name}.py')
        
        return RecommendationMatch(
            recommendation_id=rec_id,
            recommendation_title=rec_title,
            matched_module=module_name,
            match_score=match_score,
            integration_strategy='extend',
            target_location=module_path,
            rationale=f"Extends existing {module_name} (similarity: {match_score:.1%})",
            dependencies=module_info.get('dependencies', []),
            estimated_effort=self._estimate_effort(rec, module_info, 'extend')
        )
    
    def _create_new_module_placement(
        self,
        rec_id: str,
        rec_title: str,
        rec: Dict[str, any]
    ) -> RecommendationMatch:
        """Create placement for new module."""
        # Suggest module name based on recommendation
        module_name = self._suggest_module_name(rec_title)
        target_location = f"scripts/{module_name}.py"
        
        # Identify likely dependencies
        dependencies = self._identify_dependencies(rec)
        
        return RecommendationMatch(
            recommendation_id=rec_id,
            recommendation_title=rec_title,
            matched_module=None,
            match_score=0.0,
            integration_strategy='new_module',
            target_location=target_location,
            rationale=f"No existing module found - create new {module_name}",
            dependencies=dependencies,
            estimated_effort=self._estimate_effort(rec, None, 'new_module')
        )
    
    def _suggest_module_name(self, rec_title: str) -> str:
        """Suggest module name from recommendation title."""
        # Convert to snake_case
        name = rec_title.lower()
        name = name.replace(' ', '_')
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        name = name[:50]  # Limit length
        
        return name
    
    def _identify_dependencies(self, rec: Dict[str, any]) -> List[str]:
        """Identify likely dependencies for recommendation."""
        dependencies = ['pandas', 'numpy']  # Common dependencies
        
        # Add based on category/keywords
        rec_text = str(rec).lower()
        
        if 'machine learning' in rec_text or 'model' in rec_text:
            dependencies.append('sklearn')
        
        if 'database' in rec_text or 'sql' in rec_text:
            dependencies.append('sqlalchemy')
        
        if 'api' in rec_text:
            dependencies.append('requests')
        
        if 'visualization' in rec_text or 'plot' in rec_text:
            dependencies.extend(['matplotlib', 'seaborn'])
        
        return list(set(dependencies))
    
    def _estimate_effort(
        self,
        rec: Dict[str, any],
        module_info: Optional[Dict[str, any]],
        strategy: str
    ) -> str:
        """Estimate implementation effort."""
        # Base effort by strategy
        if strategy == 'extend' and module_info:
            # Extending existing module
            module_size = module_info.get('lines_of_code', 0)
            if module_size > 1000:
                return 'medium'  # Large module, careful integration
            else:
                return 'low'  # Small module, easy to extend
        
        elif strategy == 'new_module':
            # Creating new module
            complexity = rec.get('complexity', 'medium')
            if complexity == 'high' or 'complex' in str(rec).lower():
                return 'high'
            elif complexity == 'low' or 'simple' in str(rec).lower():
                return 'low'
            else:
                return 'medium'
        
        return 'medium'
    
    def _generate_implementation_order(
        self,
        placements: List[RecommendationMatch]
    ) -> List[str]:
        """Generate optimal implementation order based on dependencies."""
        # Sort by:
        # 1. Effort (low first)
        # 2. Dependencies (independents first)
        # 3. Match score (better matches first)
        
        effort_order = {'low': 0, 'medium': 1, 'high': 2}
        
        sorted_placements = sorted(
            placements,
            key=lambda p: (
                effort_order.get(p.estimated_effort, 1),
                len(p.dependencies),
                -p.match_score
            )
        )
        
        return [p.recommendation_id for p in sorted_placements]
    
    def _count_strategies(self, placements: List[RecommendationMatch]) -> Dict[str, int]:
        """Count how many of each strategy."""
        counts = {}
        for p in placements:
            counts[p.integration_strategy] = counts.get(p.integration_strategy, 0) + 1
        return counts
    
    def _estimate_total_effort(self, placements: List[RecommendationMatch]) -> str:
        """Estimate total implementation effort."""
        effort_points = {'low': 1, 'medium': 3, 'high': 5}
        total_points = sum(effort_points.get(p.estimated_effort, 3) for p in placements)
        
        if total_points < 10:
            return 'low (< 1 week)'
        elif total_points < 30:
            return 'medium (1-2 weeks)'
        else:
            return 'high (2+ weeks)'
    
    def save_integration_plan(
        self,
        plan: IntegrationPlan,
        output_file: Path
    ):
        """Save integration plan to JSON and markdown."""
        # Save JSON
        json_data = {
            'total_recommendations': plan.total_recommendations,
            'matched_to_existing': plan.matched_to_existing,
            'new_modules_needed': plan.new_modules_needed,
            'placements': [asdict(p) for p in plan.placements],
            'implementation_order': plan.implementation_order,
            'summary': plan.summary
        }
        
        json_file = output_file.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"Integration plan JSON saved to {json_file}")
        
        # Save markdown
        md_file = output_file.with_suffix('.md')
        md_content = self._generate_markdown_report(plan)
        with open(md_file, 'w') as f:
            f.write(md_content)
        
        logger.info(f"Integration plan markdown saved to {md_file}")
    
    def _generate_markdown_report(self, plan: IntegrationPlan) -> str:
        """Generate markdown report of integration plan."""
        lines = []
        lines.append("# Integration Plan")
        lines.append("")
        lines.append(f"**Total Recommendations**: {plan.total_recommendations}")
        lines.append(f"**Matched to Existing**: {plan.matched_to_existing}")
        lines.append(f"**New Modules Needed**: {plan.new_modules_needed}")
        lines.append("")
        
        lines.append("## Summary")
        lines.append("")
        for key, value in plan.summary.items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines.append("")
        
        lines.append("## Implementation Order")
        lines.append("")
        lines.append("Recommendations ordered by effort and dependencies:")
        lines.append("")
        for i, rec_id in enumerate(plan.implementation_order, 1):
            placement = next((p for p in plan.placements if p.recommendation_id == rec_id), None)
            if placement:
                lines.append(f"{i}. **{placement.recommendation_title}** ({placement.estimated_effort} effort)")
                lines.append(f"   - Strategy: {placement.integration_strategy}")
                lines.append(f"   - Location: `{placement.target_location}`")
                lines.append("")
        
        lines.append("## Detailed Placements")
        lines.append("")
        
        for placement in plan.placements:
            lines.append(f"### {placement.recommendation_title}")
            lines.append("")
            lines.append(f"- **ID**: {placement.recommendation_id}")
            lines.append(f"- **Strategy**: {placement.integration_strategy}")
            lines.append(f"- **Target**: `{placement.target_location}`")
            
            if placement.matched_module:
                lines.append(f"- **Matched Module**: {placement.matched_module} (score: {placement.match_score:.1%})")
            
            lines.append(f"- **Rationale**: {placement.rationale}")
            lines.append(f"- **Estimated Effort**: {placement.estimated_effort}")
            
            if placement.dependencies:
                lines.append(f"- **Dependencies**: {', '.join(placement.dependencies)}")
            
            lines.append("")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("SMART INTEGRATOR DEMO")
    print("=" * 70)
    print()
    
    # Load simulator analysis
    analysis_file = Path("implementation_plans/nba_simulator_analysis.json")
    if analysis_file.exists():
        with open(analysis_file) as f:
            simulator_analysis = json.load(f)
    else:
        # Mock analysis
        simulator_analysis = {
            'total_modules': 3,
            'modules': {
                'data_loader': {
                    'name': 'data_loader',
                    'purpose': 'Load and preprocess NBA data',
                    'path': 'scripts/data_loader.py',
                    'lines_of_code': 300,
                    'dependencies': ['pandas', 'sqlalchemy'],
                    'integration_points': ['data_processing']
                },
                'feature_builder': {
                    'name': 'feature_builder',
                    'purpose': 'Build features for ML models',
                    'path': 'scripts/feature_builder.py',
                    'lines_of_code': 400,
                    'dependencies': ['pandas', 'sklearn'],
                    'integration_points': ['feature_engineering']
                }
            }
        }
    
    # Mock recommendations
    recommendations = [
        {
            'id': 'rec_1',
            'title': 'Implement panel data methods',
            'description': 'Use fixed effects models for player analysis',
            'category': 'data_processing',
            'priority': 'high'
        },
        {
            'id': 'rec_2',
            'title': 'Add advanced feature engineering',
            'description': 'Create lag features and rolling statistics',
            'category': 'feature_engineering',
            'priority': 'high'
        },
        {
            'id': 'rec_3',
            'title': 'Implement model monitoring',
            'description': 'Track model drift and performance',
            'category': 'monitoring',
            'priority': 'medium'
        }
    ]
    
    # Initialize integrator
    integrator = SmartIntegrator(simulator_analysis, recommendations)
    
    # Generate plan
    plan = integrator.generate_integration_plan()
    
    # Print results
    print(f"Total Recommendations: {plan.total_recommendations}")
    print(f"Matched to Existing: {plan.matched_to_existing}")
    print(f"New Modules Needed: {plan.new_modules_needed}")
    print()
    
    print("Integration Placements:")
    for placement in plan.placements:
        print(f"  - {placement.recommendation_title}")
        print(f"    Strategy: {placement.integration_strategy}")
        print(f"    Target: {placement.target_location}")
        print(f"    Effort: {placement.estimated_effort}")
        print()
    
    print(f"Implementation Order: {', '.join(plan.implementation_order)}")
    print()
    
    # Save plan
    output_file = Path("implementation_plans/integration_plan")
    integrator.save_integration_plan(plan, output_file)
    print(f"Plan saved to {output_file}.json and {output_file}.md")
    
    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)

