#!/usr/bin/env python3
"""
Phase Mapper for Recommendation Organization & Integration System

Maps book recommendations to NBA_SIMULATOR_AWS project phases (0-9).
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PhaseMapper:
    """
    Maps book recommendations to NBA_SIMULATOR_AWS project phases.
    
    Phase Mapping:
    - Phase 0: Data Collection
    - Phase 1: Data Quality & Integration
    - Phase 2: AWS Glue ETL
    - Phase 3: Database Infrastructure
    - Phase 4: Simulation Engine
    - Phase 5: Machine Learning Models
    - Phase 6: Optional Enhancements
    - Phase 7: Betting Odds Integration
    - Phase 8: Recursive Data Discovery
    - Phase 9: System Architecture
    """
    
    def __init__(self):
        self.phase_keywords = {
            0: [
                "data collection", "scraping", "ingestion", "sources", "data sources",
                "web scraping", "api integration", "data pipeline", "etl", "extract",
                "collect", "gather", "fetch", "download", "import", "acquire"
            ],
            1: [
                "data quality", "validation", "integration", "deduplication", "cleaning",
                "data cleaning", "data validation", "quality checks", "data integrity",
                "data consistency", "data standardization", "data normalization",
                "data profiling", "data monitoring", "data governance"
            ],
            2: [
                "etl", "glue", "transformation", "pipeline", "aws glue", "data transformation",
                "data processing", "batch processing", "stream processing", "data warehouse",
                "data lake", "spark", "hadoop", "preprocessing", "feature engineering"
            ],
            3: [
                "database", "postgresql", "rds", "schema", "sql", "database design",
                "data modeling", "tables", "indexes", "queries", "database optimization",
                "database performance", "database security", "backup", "replication"
            ],
            4: [
                "simulation", "temporal", "panel data", "fidelity", "simulation engine",
                "game simulation", "player simulation", "team simulation", "match simulation",
                "statistical simulation", "monte carlo", "agent-based", "discrete event"
            ],
            5: [
                "machine learning", "ml models", "training", "prediction", "model",
                "algorithm", "neural network", "deep learning", "feature engineering",
                "model training", "model evaluation", "model deployment", "mlops",
                "model versioning", "model registry", "model monitoring"
            ],
            6: [
                "enhancements", "optimization", "performance", "scalability", "improvements",
                "advanced features", "user experience", "ui", "ux", "dashboard", "visualization",
                "analytics", "reporting", "monitoring", "alerting", "logging"
            ],
            7: [
                "betting", "odds", "gambling", "lines", "sports betting", "betting odds",
                "bookmaker", "spread", "over under", "moneyline", "betting market",
                "betting analysis", "betting strategy", "risk management"
            ],
            8: [
                "discovery", "analysis", "insights", "exploration", "data discovery",
                "pattern recognition", "anomaly detection", "trend analysis", "correlation",
                "statistical analysis", "data mining", "knowledge discovery", "research"
            ],
            9: [
                "architecture", "infrastructure", "deployment", "devops", "ci/cd",
                "containerization", "kubernetes", "docker", "microservices", "api",
                "security", "scalability", "reliability", "monitoring", "observability",
                "system design", "cloud architecture", "aws", "terraform", "infrastructure as code"
            ]
        }
        
        # Phase descriptions for better mapping
        self.phase_descriptions = {
            0: "Data Collection - Scraping, ingestion, data sources",
            1: "Data Quality & Integration - Validation, cleaning, deduplication",
            2: "AWS Glue ETL - Transformation, processing, pipelines",
            3: "Database Infrastructure - PostgreSQL, RDS, schema design",
            4: "Simulation Engine - Game simulation, temporal data",
            5: "Machine Learning Models - Training, prediction, algorithms",
            6: "Optional Enhancements - Performance, UI, analytics",
            7: "Betting Odds Integration - Sports betting, odds analysis",
            8: "Recursive Data Discovery - Analysis, insights, exploration",
            9: "System Architecture - Infrastructure, deployment, DevOps"
        }
    
    def map_recommendation_to_phase(self, rec: Dict[str, Any]) -> List[int]:
        """
        Maps a recommendation to most relevant phase(s).
        
        Args:
            rec: Recommendation dictionary with 'title' and optional 'reasoning'
            
        Returns:
            list: Phase numbers [0-9] that match this recommendation
        """
        rec_text = f"{rec['title']} {rec.get('reasoning', '')}".lower()
        
        matches = []
        match_scores = {}
        
        # Score each phase based on keyword matches
        for phase, keywords in self.phase_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in rec_text:
                    score += 1
                    # Give higher weight to exact phrase matches
                    if f" {keyword} " in f" {rec_text} ":
                        score += 2
            
            if score > 0:
                match_scores[phase] = score
        
        # Sort by score and return phases with highest scores
        if match_scores:
            sorted_phases = sorted(match_scores.items(), key=lambda x: x[1], reverse=True)
            # Return phases with score >= 50% of highest score
            max_score = sorted_phases[0][1]
            threshold = max(1, max_score // 2)
            
            for phase, score in sorted_phases:
                if score >= threshold:
                    matches.append(phase)
                else:
                    break
        
        # Default to Phase 5 (ML) if no specific match
        if not matches:
            logger.warning(f"No phase match found for '{rec['title']}', defaulting to Phase 5")
            matches = [5]
        elif len(matches) > 1:
            logger.info(f"Multiple phase matches for '{rec['title']}': {matches}")
        
        return matches
    
    def get_phase_description(self, phase_num: int) -> str:
        """Get description for a specific phase."""
        return self.phase_descriptions.get(phase_num, f"Phase {phase_num}")
    
    def get_all_phase_descriptions(self) -> Dict[int, str]:
        """Get all phase descriptions."""
        return self.phase_descriptions.copy()
    
    def map_recommendations_batch(self, recommendations: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Map multiple recommendations to phases in batch.
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            dict: {phase_num: [recommendations]}
        """
        phase_recs = {i: [] for i in range(10)}
        
        for rec in recommendations:
            phases = self.map_recommendation_to_phase(rec)
            for phase in phases:
                phase_recs[phase].append(rec)
        
        return phase_recs
    
    def get_phase_statistics(self, phase_recs: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Get statistics about phase distribution.
        
        Args:
            phase_recs: Phase recommendations dictionary
            
        Returns:
            dict: Statistics about phase distribution
        """
        stats = {
            'total_recommendations': sum(len(recs) for recs in phase_recs.values()),
            'phases_with_recommendations': len([recs for recs in phase_recs.values() if recs]),
            'phase_distribution': {},
            'category_distribution': {'critical': 0, 'important': 0, 'nice_to_have': 0}
        }
        
        for phase, recs in phase_recs.items():
            if recs:
                stats['phase_distribution'][phase] = len(recs)
                
                # Count by category
                for rec in recs:
                    category = rec.get('category', 'nice_to_have')
                    if category in stats['category_distribution']:
                        stats['category_distribution'][category] += 1
        
        return stats


def test_phase_mapper():
    """Test the PhaseMapper functionality."""
    mapper = PhaseMapper()
    
    # Test cases
    test_recommendations = [
        {
            'title': 'Implement data validation pipeline',
            'reasoning': 'Quality checks needed for data integrity',
            'category': 'critical'
        },
        {
            'title': 'Add machine learning model training',
            'reasoning': 'Need to train models for prediction',
            'category': 'important'
        },
        {
            'title': 'Set up AWS Glue ETL pipeline',
            'reasoning': 'Transform data using AWS Glue',
            'category': 'critical'
        },
        {
            'title': 'Design PostgreSQL database schema',
            'reasoning': 'Need proper database structure',
            'category': 'important'
        },
        {
            'title': 'Implement betting odds integration',
            'reasoning': 'Connect to betting APIs for odds data',
            'category': 'important'
        },
        {
            'title': 'Add system monitoring and alerting',
            'reasoning': 'Monitor system health and performance',
            'category': 'nice_to_have'
        }
    ]
    
    print("🧪 Testing PhaseMapper...")
    
    for rec in test_recommendations:
        phases = mapper.map_recommendation_to_phase(rec)
        print(f"  '{rec['title']}' → Phases {phases}")
    
    # Test batch mapping
    phase_recs = mapper.map_recommendations_batch(test_recommendations)
    stats = mapper.get_phase_statistics(phase_recs)
    
    print(f"\n📊 Phase Distribution:")
    for phase, count in stats['phase_distribution'].items():
        desc = mapper.get_phase_description(phase)
        print(f"  Phase {phase}: {count} recommendations ({desc})")
    
    print(f"\n📈 Category Distribution:")
    for category, count in stats['category_distribution'].items():
        print(f"  {category}: {count} recommendations")


if __name__ == "__main__":
    test_phase_mapper()