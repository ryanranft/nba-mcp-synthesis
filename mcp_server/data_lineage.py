"""
Data Lineage Tracker Module
Track data flow and transformations for reproducibility and debugging.
"""

import logging
from typing import Dict, Optional, Any, List, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Type of node in lineage graph"""
    SOURCE = "source"
    TRANSFORMATION = "transformation"
    FEATURE = "feature"
    MODEL = "model"
    PREDICTION = "prediction"


@dataclass
class LineageNode:
    """Node in the lineage graph"""
    node_id: str
    node_type: NodeType
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)


class DataLineageTracker:
    """Tracks data lineage across the ML pipeline"""

    def __init__(self, storage_path: str = "./data_lineage"):
        """
        Initialize data lineage tracker.

        Args:
            storage_path: Path to lineage storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.nodes: Dict[str, LineageNode] = {}
        self._load_lineage()

    def _load_lineage(self):
        """Load lineage from disk"""
        lineage_file = self.storage_path / "lineage.json"
        if lineage_file.exists():
            with open(lineage_file, 'r') as f:
                data = json.load(f)
                for node_id, node_data in data.items():
                    self.nodes[node_id] = LineageNode(
                        node_id=node_data["node_id"],
                        node_type=NodeType(node_data["node_type"]),
                        name=node_data["name"],
                        metadata=node_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(node_data["created_at"]),
                        parents=node_data.get("parents", []),
                        children=node_data.get("children", [])
                    )
            logger.info(f"Loaded {len(self.nodes)} lineage nodes")

    def _save_lineage(self):
        """Save lineage to disk"""
        lineage_file = self.storage_path / "lineage.json"
        data = {}
        for node_id, node in self.nodes.items():
            data[node_id] = {
                "node_id": node.node_id,
                "node_type": node.node_type.value,
                "name": node.name,
                "metadata": node.metadata,
                "created_at": node.created_at.isoformat(),
                "parents": node.parents,
                "children": node.children
            }

        with open(lineage_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved {len(self.nodes)} lineage nodes")

    def track_node(
        self,
        node_id: str,
        node_type: NodeType,
        name: str,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LineageNode:
        """
        Track a new node in the lineage.

        Args:
            node_id: Unique node identifier
            node_type: Type of node
            name: Node name
            parent_ids: Parent node IDs
            metadata: Additional metadata

        Returns:
            LineageNode object
        """
        parent_ids = parent_ids or []

        node = LineageNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            metadata=metadata or {},
            parents=parent_ids.copy()
        )

        # Add as child to parents
        for parent_id in parent_ids:
            if parent_id in self.nodes:
                if node_id not in self.nodes[parent_id].children:
                    self.nodes[parent_id].children.append(node_id)

        self.nodes[node_id] = node
        self._save_lineage()

        logger.info(f"Tracked lineage node: {node_id} ({node_type.value})")

        return node

    def get_ancestors(self, node_id: str) -> List[LineageNode]:
        """
        Get all ancestor nodes (upstream dependencies).

        Args:
            node_id: Node identifier

        Returns:
            List of ancestor LineageNode objects
        """
        if node_id not in self.nodes:
            return []

        ancestors = []
        visited: Set[str] = set()
        queue = [node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            current_node = self.nodes.get(current_id)
            if not current_node:
                continue

            if current_id != node_id:  # Don't include self
                ancestors.append(current_node)

            queue.extend(current_node.parents)

        return ancestors

    def get_descendants(self, node_id: str) -> List[LineageNode]:
        """
        Get all descendant nodes (downstream dependencies).

        Args:
            node_id: Node identifier

        Returns:
            List of descendant LineageNode objects
        """
        if node_id not in self.nodes:
            return []

        descendants = []
        visited: Set[str] = set()
        queue = [node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            current_node = self.nodes.get(current_id)
            if not current_node:
                continue

            if current_id != node_id:  # Don't include self
                descendants.append(current_node)

            queue.extend(current_node.children)

        return descendants

    def get_lineage_path(self, from_node_id: str, to_node_id: str) -> List[LineageNode]:
        """
        Find lineage path between two nodes.

        Args:
            from_node_id: Starting node
            to_node_id: Target node

        Returns:
            List of nodes in path
        """
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            return []

        # BFS to find path
        queue = [(from_node_id, [from_node_id])]
        visited: Set[str] = set()

        while queue:
            current_id, path = queue.pop(0)

            if current_id == to_node_id:
                return [self.nodes[node_id] for node_id in path]

            if current_id in visited:
                continue
            visited.add(current_id)

            current_node = self.nodes.get(current_id)
            if not current_node:
                continue

            for child_id in current_node.children:
                if child_id not in visited:
                    queue.append((child_id, path + [child_id]))

        return []  # No path found

    def impact_analysis(self, node_id: str) -> Dict[str, Any]:
        """
        Analyze impact of changes to a node.

        Args:
            node_id: Node to analyze

        Returns:
            Impact analysis results
        """
        if node_id not in self.nodes:
            return {"error": "Node not found"}

        node = self.nodes[node_id]
        descendants = self.get_descendants(node_id)

        # Categorize descendants by type
        impact_by_type = {}
        for desc in descendants:
            type_name = desc.node_type.value
            if type_name not in impact_by_type:
                impact_by_type[type_name] = []
            impact_by_type[type_name].append(desc.name)

        return {
            "node": node.name,
            "node_type": node.node_type.value,
            "total_impacted": len(descendants),
            "impacted_by_type": {
                k: len(v) for k, v in impact_by_type.items()
            },
            "critical_dependencies": [
                desc.name for desc in descendants
                if desc.node_type in [NodeType.MODEL, NodeType.PREDICTION]
            ]
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("DATA LINEAGE TRACKER DEMO")
    print("=" * 80)

    tracker = DataLineageTracker(storage_path="./demo_lineage")

    # Track data pipeline
    print("\n" + "=" * 80)
    print("TRACKING DATA PIPELINE")
    print("=" * 80)

    # Source data
    tracker.track_node(
        node_id="raw_games_2024",
        node_type=NodeType.SOURCE,
        name="Raw Games 2024",
        metadata={"table": "games", "records": 1230}
    )

    # Transformations
    tracker.track_node(
        node_id="cleaned_games",
        node_type=NodeType.TRANSFORMATION,
        name="Cleaned Games",
        parent_ids=["raw_games_2024"],
        metadata={"operation": "clean_nulls", "records": 1200}
    )

    tracker.track_node(
        node_id="aggregated_stats",
        node_type=NodeType.TRANSFORMATION,
        name="Aggregated Team Stats",
        parent_ids=["cleaned_games"],
        metadata={"operation": "aggregate_by_team"}
    )

    # Features
    tracker.track_node(
        node_id="feature_win_rate",
        node_type=NodeType.FEATURE,
        name="Team Win Rate",
        parent_ids=["aggregated_stats"],
        metadata={"formula": "wins / total_games"}
    )

    tracker.track_node(
        node_id="feature_ppg",
        node_type=NodeType.FEATURE,
        name="Points Per Game",
        parent_ids=["aggregated_stats"],
        metadata={"formula": "total_points / total_games"}
    )

    # Model
    tracker.track_node(
        node_id="model_playoff_predictor_v1",
        node_type=NodeType.MODEL,
        name="Playoff Predictor v1",
        parent_ids=["feature_win_rate", "feature_ppg"],
        metadata={"algorithm": "RandomForest", "accuracy": 0.87}
    )

    print("✅ Tracked 6 pipeline nodes")

    # Get ancestors
    print("\n" + "=" * 80)
    print("UPSTREAM DEPENDENCIES (Model Ancestors)")
    print("=" * 80)

    ancestors = tracker.get_ancestors("model_playoff_predictor_v1")
    print(f"\nModel depends on {len(ancestors)} upstream nodes:")
    for node in ancestors:
        print(f"  {node.node_type.value:20} → {node.name}")

    # Impact analysis
    print("\n" + "=" * 80)
    print("IMPACT ANALYSIS (Raw Data Change)")
    print("=" * 80)

    impact = tracker.impact_analysis("raw_games_2024")
    print(f"\nChanging '{impact['node']}' would impact:")
    print(f"  Total nodes: {impact['total_impacted']}")
    print(f"  By type:")
    for node_type, count in impact['impacted_by_type'].items():
        print(f"    - {node_type}: {count}")
    print(f"  Critical dependencies: {impact['critical_dependencies']}")

    # Lineage path
    print("\n" + "=" * 80)
    print("LINEAGE PATH (Source to Model)")
    print("=" * 80)

    path = tracker.get_lineage_path("raw_games_2024", "model_playoff_predictor_v1")
    print(f"\nPath from source to model ({len(path)} steps):")
    for i, node in enumerate(path, 1):
        print(f"  {i}. {node.node_type.value:20} → {node.name}")

    print("\n" + "=" * 80)
    print("Data Lineage Demo Complete!")
    print("=" * 80)

