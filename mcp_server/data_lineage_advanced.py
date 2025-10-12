"""
Advanced Data Lineage Tracking

Complete data lineage with impact analysis:
- End-to-end lineage
- Impact analysis
- Data provenance
- Dependency mapping
- Change tracking
- Compliance reporting

Features:
- Automatic tracking
- Visual lineage graphs
- Impact predictions
- Compliance audit trails
- Version control
- Query lineage

Use Cases:
- Regulatory compliance
- Impact analysis
- Debugging pipelines
- Data quality
- Audit trails
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DataAssetType(Enum):
    """Types of data assets"""
    TABLE = "table"
    VIEW = "view"
    FILE = "file"
    API = "api"
    MODEL = "model"
    FEATURE = "feature"


class LineageOperation(Enum):
    """Types of lineage operations"""
    READ = "read"
    WRITE = "write"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    JOIN = "join"
    FILTER = "filter"


@dataclass
class DataAsset:
    """Represents a data asset"""
    asset_id: str
    name: str
    asset_type: DataAssetType
    location: str  # Database, S3 path, etc.
    schema: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LineageEdge:
    """Represents a lineage relationship"""
    source_asset_id: str
    target_asset_id: str
    operation: LineageOperation
    transformation_logic: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageEvent:
    """Single lineage event"""
    event_id: str
    asset_id: str
    operation: LineageOperation
    user: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class LineageGraph:
    """Graph representation of data lineage"""
    
    def __init__(self):
        self.assets: Dict[str, DataAsset] = {}
        self.edges: List[LineageEdge] = []
        self.events: List[LineageEvent] = []
    
    def add_asset(self, asset: DataAsset) -> None:
        """Add data asset to lineage"""
        self.assets[asset.asset_id] = asset
        logger.debug(f"Added asset: {asset.name} ({asset.asset_type.value})")
    
    def add_lineage(
        self,
        source_id: str,
        target_id: str,
        operation: LineageOperation,
        transformation: Optional[str] = None
    ) -> None:
        """Add lineage relationship"""
        
        if source_id not in self.assets or target_id not in self.assets:
            logger.warning(f"Missing asset for lineage: {source_id} -> {target_id}")
            return
        
        edge = LineageEdge(
            source_asset_id=source_id,
            target_asset_id=target_id,
            operation=operation,
            transformation_logic=transformation
        )
        
        self.edges.append(edge)
        logger.debug(f"Added lineage: {source_id} -> {target_id} ({operation.value})")
    
    def get_upstream_assets(self, asset_id: str, max_depth: int = 10) -> List[DataAsset]:
        """Get all upstream dependencies"""
        visited = set()
        upstream = []
        
        def traverse(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Find edges where current asset is the target
            for edge in self.edges:
                if edge.target_asset_id == current_id:
                    source_asset = self.assets.get(edge.source_asset_id)
                    if source_asset:
                        upstream.append(source_asset)
                        traverse(edge.source_asset_id, depth + 1)
        
        traverse(asset_id, 0)
        return upstream
    
    def get_downstream_assets(self, asset_id: str, max_depth: int = 10) -> List[DataAsset]:
        """Get all downstream dependents"""
        visited = set()
        downstream = []
        
        def traverse(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Find edges where current asset is the source
            for edge in self.edges:
                if edge.source_asset_id == current_id:
                    target_asset = self.assets.get(edge.target_asset_id)
                    if target_asset:
                        downstream.append(target_asset)
                        traverse(edge.target_asset_id, depth + 1)
        
        traverse(asset_id, 0)
        return downstream
    
    def get_lineage_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between two assets"""
        
        # BFS to find path
        from collections import deque
        
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
            
            # Find next assets
            for edge in self.edges:
                if edge.source_asset_id == current_id:
                    next_id = edge.target_asset_id
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))
        
        return None  # No path found
    
    def export_lineage(self, format: str = "json") -> str:
        """Export lineage graph"""
        
        if format == "json":
            data = {
                'assets': [
                    {
                        'id': a.asset_id,
                        'name': a.name,
                        'type': a.asset_type.value,
                        'location': a.location
                    }
                    for a in self.assets.values()
                ],
                'edges': [
                    {
                        'source': e.source_asset_id,
                        'target': e.target_asset_id,
                        'operation': e.operation.value,
                        'transformation': e.transformation_logic
                    }
                    for e in self.edges
                ]
            }
            return json.dumps(data, indent=2)
        
        elif format == "mermaid":
            lines = ["graph LR"]
            
            for edge in self.edges:
                source = self.assets[edge.source_asset_id].name
                target = self.assets[edge.target_asset_id].name
                lines.append(f"    {source}[{source}] -->|{edge.operation.value}| {target}[{target}]")
            
            return "\n".join(lines)
        
        return ""


class ImpactAnalyzer:
    """Analyze impact of changes"""
    
    def __init__(self, lineage_graph: LineageGraph):
        self.graph = lineage_graph
    
    def analyze_impact(self, asset_id: str) -> Dict[str, Any]:
        """Analyze impact of changing an asset"""
        
        if asset_id not in self.graph.assets:
            return {'error': 'Asset not found'}
        
        asset = self.graph.assets[asset_id]
        
        # Get all downstream assets
        downstream = self.graph.get_downstream_assets(asset_id)
        
        # Categorize by type
        impact_by_type = {}
        for dep in downstream:
            asset_type = dep.asset_type.value
            if asset_type not in impact_by_type:
                impact_by_type[asset_type] = []
            impact_by_type[asset_type].append(dep.name)
        
        # Calculate impact score
        impact_score = len(downstream)
        
        # Determine severity
        if impact_score > 10:
            severity = "HIGH"
        elif impact_score > 5:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        return {
            'asset': {
                'id': asset.asset_id,
                'name': asset.name,
                'type': asset.asset_type.value
            },
            'impact_score': impact_score,
            'severity': severity,
            'affected_assets': len(downstream),
            'affected_by_type': impact_by_type,
            'downstream_assets': [
                {
                    'id': d.asset_id,
                    'name': d.name,
                    'type': d.asset_type.value
                }
                for d in downstream[:10]  # Top 10
            ],
            'recommendation': self._get_recommendation(severity, impact_score)
        }
    
    def _get_recommendation(self, severity: str, impact_score: int) -> str:
        """Get recommendation based on impact"""
        if severity == "HIGH":
            return f"High impact change affecting {impact_score} assets. Schedule maintenance window and notify stakeholders."
        elif severity == "MEDIUM":
            return f"Medium impact change affecting {impact_score} assets. Test thoroughly before deployment."
        else:
            return f"Low impact change affecting {impact_score} assets. Standard deployment process."


class ComplianceReporter:
    """Generate compliance reports"""
    
    def __init__(self, lineage_graph: LineageGraph):
        self.graph = lineage_graph
    
    def generate_compliance_report(
        self,
        regulation: str = "GDPR"
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        
        # Identify sensitive data assets
        sensitive_assets = [
            asset for asset in self.graph.assets.values()
            if asset.metadata.get('contains_pii', False)
        ]
        
        # Check data flows
        sensitive_flows = []
        for asset in sensitive_assets:
            downstream = self.graph.get_downstream_assets(asset.asset_id)
            for dep in downstream:
                sensitive_flows.append({
                    'source': asset.name,
                    'target': dep.name,
                    'risk': self._assess_risk(asset, dep)
                })
        
        # Generate report
        return {
            'regulation': regulation,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_assets': len(self.graph.assets),
                'sensitive_assets': len(sensitive_assets),
                'sensitive_flows': len(sensitive_flows)
            },
            'sensitive_data_assets': [
                {
                    'id': a.asset_id,
                    'name': a.name,
                    'type': a.asset_type.value,
                    'downstream_count': len(self.graph.get_downstream_assets(a.asset_id))
                }
                for a in sensitive_assets
            ],
            'high_risk_flows': [
                flow for flow in sensitive_flows
                if flow['risk'] == 'HIGH'
            ][:10],
            'recommendations': self._get_compliance_recommendations(sensitive_flows)
        }
    
    def _assess_risk(self, source: DataAsset, target: DataAsset) -> str:
        """Assess risk of data flow"""
        # Check if flowing to external system
        if 'external' in target.location.lower():
            return "HIGH"
        elif target.asset_type == DataAssetType.API:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_compliance_recommendations(self, flows: List[Dict[str, Any]]) -> List[str]:
        """Get compliance recommendations"""
        recommendations = []
        
        high_risk_count = sum(1 for f in flows if f['risk'] == 'HIGH')
        
        if high_risk_count > 0:
            recommendations.append(
                f"Review {high_risk_count} high-risk data flows to external systems"
            )
        
        recommendations.append("Implement data encryption for sensitive data")
        recommendations.append("Enable audit logging for all data access")
        
        return recommendations


class DataLineageTracker:
    """Main data lineage tracker"""
    
    def __init__(self):
        self.lineage_graph = LineageGraph()
        self.impact_analyzer = ImpactAnalyzer(self.lineage_graph)
        self.compliance_reporter = ComplianceReporter(self.lineage_graph)
    
    def register_asset(
        self,
        asset_id: str,
        name: str,
        asset_type: DataAssetType,
        location: str,
        schema: Optional[Dict[str, str]] = None,
        contains_pii: bool = False
    ) -> None:
        """Register a data asset"""
        asset = DataAsset(
            asset_id=asset_id,
            name=name,
            asset_type=asset_type,
            location=location,
            schema=schema,
            metadata={'contains_pii': contains_pii}
        )
        self.lineage_graph.add_asset(asset)
    
    def track_operation(
        self,
        source_ids: List[str],
        target_id: str,
        operation: LineageOperation,
        transformation: Optional[str] = None
    ) -> None:
        """Track a data operation"""
        for source_id in source_ids:
            self.lineage_graph.add_lineage(
                source_id,
                target_id,
                operation,
                transformation
            )
    
    def get_lineage_report(self, asset_id: str) -> Dict[str, Any]:
        """Get comprehensive lineage report"""
        
        if asset_id not in self.lineage_graph.assets:
            return {'error': 'Asset not found'}
        
        asset = self.lineage_graph.assets[asset_id]
        upstream = self.lineage_graph.get_upstream_assets(asset_id)
        downstream = self.lineage_graph.get_downstream_assets(asset_id)
        impact = self.impact_analyzer.analyze_impact(asset_id)
        
        return {
            'asset': {
                'id': asset.asset_id,
                'name': asset.name,
                'type': asset.asset_type.value,
                'location': asset.location
            },
            'lineage': {
                'upstream_count': len(upstream),
                'downstream_count': len(downstream),
                'upstream_assets': [
                    {'id': a.asset_id, 'name': a.name, 'type': a.asset_type.value}
                    for a in upstream[:5]  # Top 5
                ],
                'downstream_assets': [
                    {'id': a.asset_id, 'name': a.name, 'type': a.asset_type.value}
                    for a in downstream[:5]
                ]
            },
            'impact_analysis': impact
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Advanced Data Lineage Demo ===\n")
    
    # Create tracker
    tracker = DataLineageTracker()
    
    # Register assets
    print("--- Registering Data Assets ---\n")
    
    tracker.register_asset(
        "raw_games",
        "Raw Games Data",
        DataAssetType.TABLE,
        "s3://nba-data/raw/games/"
    )
    
    tracker.register_asset(
        "raw_players",
        "Raw Players Data",
        DataAssetType.TABLE,
        "s3://nba-data/raw/players/",
        contains_pii=True
    )
    
    tracker.register_asset(
        "clean_games",
        "Cleaned Games",
        DataAssetType.TABLE,
        "postgres://nba/clean_games"
    )
    
    tracker.register_asset(
        "player_stats",
        "Player Statistics",
        DataAssetType.VIEW,
        "postgres://nba/player_stats"
    )
    
    tracker.register_asset(
        "ml_features",
        "ML Features",
        DataAssetType.FEATURE,
        "feature_store://nba/features"
    )
    
    print("✓ Registered 5 assets")
    
    # Track operations
    print("\n--- Tracking Operations ---\n")
    
    tracker.track_operation(
        ["raw_games"],
        "clean_games",
        LineageOperation.TRANSFORM,
        "Remove nulls, standardize dates"
    )
    
    tracker.track_operation(
        ["raw_players", "clean_games"],
        "player_stats",
        LineageOperation.JOIN,
        "JOIN players ON games.player_id"
    )
    
    tracker.track_operation(
        ["player_stats"],
        "ml_features",
        LineageOperation.AGGREGATE,
        "Calculate rolling averages"
    )
    
    print("✓ Tracked 3 operations")
    
    # Get lineage report
    print("\n--- Lineage Report: player_stats ---\n")
    report = tracker.get_lineage_report("player_stats")
    
    print(f"Asset: {report['asset']['name']}")
    print(f"Type: {report['asset']['type']}")
    print(f"\nLineage:")
    print(f"  Upstream: {report['lineage']['upstream_count']} assets")
    print(f"  Downstream: {report['lineage']['downstream_count']} assets")
    
    print(f"\nImpact Analysis:")
    print(f"  Severity: {report['impact_analysis']['severity']}")
    print(f"  Affected Assets: {report['impact_analysis']['affected_assets']}")
    print(f"  Recommendation: {report['impact_analysis']['recommendation']}")
    
    # Compliance report
    print("\n--- Compliance Report ---\n")
    compliance = tracker.compliance_reporter.generate_compliance_report("GDPR")
    
    print(f"Regulation: {compliance['regulation']}")
    print(f"Sensitive Assets: {compliance['summary']['sensitive_assets']}")
    print(f"Sensitive Flows: {compliance['summary']['sensitive_flows']}")
    
    print("\n=== Demo Complete ===")

