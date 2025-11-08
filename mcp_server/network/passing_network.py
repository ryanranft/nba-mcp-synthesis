"""
Passing Network Analysis (Agent 16, Module 1)

Analyzes passing patterns and network structure:
- Pass frequency and efficiency
- Network centrality metrics
- Ball movement patterns
- Assist networks
- Pass clustering

Integrates with:
- spatial: Pass locations and court positioning
- player_interaction: Player relationships
- play_types: Pass context (pick and roll, etc.)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import math

import numpy as np

logger = logging.getLogger(__name__)

# Try to import NetworkX (optional)
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available, some network features disabled")


class PassType(Enum):
    """Types of passes"""

    DIRECT = "direct"  # Direct pass
    ASSIST = "assist"  # Pass leading to score
    TURNOVER = "turnover"  # Pass resulting in turnover
    SKIP = "skip"  # Skip pass (across court)
    ENTRY = "entry"  # Entry pass to post
    OUTLET = "outlet"  # Outlet pass (fast break)


@dataclass
class Pass:
    """Individual pass event"""

    passer_id: str
    receiver_id: str
    timestamp: float
    game_id: str

    # Pass characteristics
    pass_type: PassType = PassType.DIRECT
    resulted_in_assist: bool = False
    resulted_in_turnover: bool = False

    # Spatial information
    passer_x: Optional[float] = None
    passer_y: Optional[float] = None
    receiver_x: Optional[float] = None
    receiver_y: Optional[float] = None

    # Computed metrics
    distance: Optional[float] = None

    def __post_init__(self):
        """Compute derived metrics"""
        if self.distance is None and all([
            self.passer_x, self.passer_y,
            self.receiver_x, self.receiver_y
        ]):
            self.distance = self._compute_distance()

    def _compute_distance(self) -> float:
        """Compute pass distance"""
        dx = self.receiver_x - self.passer_x
        dy = self.receiver_y - self.passer_y
        return math.sqrt(dx * dx + dy * dy)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'passer_id': self.passer_id,
            'receiver_id': self.receiver_id,
            'timestamp': self.timestamp,
            'game_id': self.game_id,
            'pass_type': self.pass_type.value,
            'assist': self.resulted_in_assist,
            'turnover': self.resulted_in_turnover,
            'distance': self.distance,
        }


@dataclass
class PassingMetrics:
    """Passing metrics between two players"""

    passer_id: str
    receiver_id: str

    # Volume metrics
    total_passes: int
    assists: int
    turnovers: int

    # Efficiency metrics
    assist_rate: float  # Assists / total passes
    turnover_rate: float  # Turnovers / total passes
    completion_rate: float  # (total - turnovers) / total

    # Distance metrics
    avg_pass_distance: float
    max_pass_distance: float

    # Temporal
    passes_per_game: float = 0.0

    def effectiveness_score(self) -> float:
        """
        Combined effectiveness score (0-1).

        Higher score = more effective passing connection
        """
        # Weight: 40% completion, 30% assists, 30% volume (normalized)
        completion_component = self.completion_rate * 0.4
        assist_component = min(self.assist_rate * 2, 1.0) * 0.3  # Cap at 50%
        volume_component = min(self.total_passes / 50.0, 1.0) * 0.3  # Normalize to 50 passes

        return completion_component + assist_component + volume_component

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'passer_id': self.passer_id,
            'receiver_id': self.receiver_id,
            'total_passes': self.total_passes,
            'assists': self.assists,
            'turnovers': self.turnovers,
            'assist_rate': self.assist_rate,
            'turnover_rate': self.turnover_rate,
            'completion_rate': self.completion_rate,
            'avg_distance': self.avg_pass_distance,
            'effectiveness': self.effectiveness_score(),
        }


class PassingNetwork:
    """
    Represents passing network as a graph.

    Nodes = players
    Edges = passing connections (weighted by frequency/effectiveness)
    """

    def __init__(self):
        """Initialize passing network"""
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available, limited functionality")
            self.graph = None
        else:
            self.graph = nx.DiGraph()  # Directed graph (A -> B)

        self.passes: List[Pass] = []
        self.pass_counts: Dict[Tuple[str, str], int] = {}

    def add_pass(self, pass_event: Pass):
        """Add a pass to the network"""
        self.passes.append(pass_event)

        # Update pass count
        edge = (pass_event.passer_id, pass_event.receiver_id)
        self.pass_counts[edge] = self.pass_counts.get(edge, 0) + 1

        if NETWORKX_AVAILABLE and self.graph is not None:
            # Add nodes
            self.graph.add_node(pass_event.passer_id)
            self.graph.add_node(pass_event.receiver_id)

            # Add/update edge
            if self.graph.has_edge(*edge):
                self.graph[edge[0]][edge[1]]['weight'] += 1
            else:
                self.graph.add_edge(*edge, weight=1)

    def add_passes(self, passes: List[Pass]):
        """Add multiple passes"""
        for pass_event in passes:
            self.add_pass(pass_event)

    def get_pass_metrics(
        self,
        passer_id: str,
        receiver_id: str
    ) -> Optional[PassingMetrics]:
        """Get passing metrics between two players"""
        # Filter passes
        passes = [
            p for p in self.passes
            if p.passer_id == passer_id and p.receiver_id == receiver_id
        ]

        if not passes:
            return None

        total_passes = len(passes)
        assists = sum(1 for p in passes if p.resulted_in_assist)
        turnovers = sum(1 for p in passes if p.resulted_in_turnover)

        assist_rate = assists / total_passes if total_passes > 0 else 0.0
        turnover_rate = turnovers / total_passes if total_passes > 0 else 0.0
        completion_rate = (total_passes - turnovers) / total_passes if total_passes > 0 else 0.0

        # Distance metrics
        distances = [p.distance for p in passes if p.distance is not None]
        avg_distance = float(np.mean(distances)) if distances else 0.0
        max_distance = float(np.max(distances)) if distances else 0.0

        return PassingMetrics(
            passer_id=passer_id,
            receiver_id=receiver_id,
            total_passes=total_passes,
            assists=assists,
            turnovers=turnovers,
            assist_rate=assist_rate,
            turnover_rate=turnover_rate,
            completion_rate=completion_rate,
            avg_pass_distance=avg_distance,
            max_pass_distance=max_distance
        )

    def get_top_connections(
        self,
        n: int = 10,
        metric: str = 'frequency'
    ) -> List[Tuple[str, str, float]]:
        """
        Get top N passing connections.

        Args:
            n: Number of connections to return
            metric: Metric to sort by ('frequency', 'effectiveness', 'assists')

        Returns:
            List of (passer, receiver, score) tuples
        """
        connections = []

        for (passer, receiver), count in self.pass_counts.items():
            metrics = self.get_pass_metrics(passer, receiver)

            if metrics:
                if metric == 'frequency':
                    score = float(metrics.total_passes)
                elif metric == 'effectiveness':
                    score = metrics.effectiveness_score()
                elif metric == 'assists':
                    score = float(metrics.assists)
                else:
                    score = float(count)

                connections.append((passer, receiver, score))

        # Sort by score descending
        connections.sort(key=lambda x: x[2], reverse=True)

        return connections[:n]

    def get_player_centrality(
        self,
        player_id: str,
        centrality_type: str = 'degree'
    ) -> float:
        """
        Get centrality score for a player.

        Args:
            player_id: Player identifier
            centrality_type: Type ('degree', 'betweenness', 'closeness', 'pagerank')

        Returns:
            Centrality score
        """
        if not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("NetworkX required for centrality metrics")
            return 0.0

        if player_id not in self.graph:
            return 0.0

        try:
            if centrality_type == 'degree':
                return self.graph.degree(player_id, weight='weight')
            elif centrality_type == 'betweenness':
                centrality = nx.betweenness_centrality(self.graph, weight='weight')
                return centrality.get(player_id, 0.0)
            elif centrality_type == 'closeness':
                centrality = nx.closeness_centrality(self.graph, distance='weight')
                return centrality.get(player_id, 0.0)
            elif centrality_type == 'pagerank':
                centrality = nx.pagerank(self.graph, weight='weight')
                return centrality.get(player_id, 0.0)
            else:
                return 0.0
        except:
            return 0.0

    def get_all_player_centralities(
        self,
        centrality_type: str = 'degree'
    ) -> Dict[str, float]:
        """Get centrality scores for all players"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {}

        players = list(self.graph.nodes())
        return {
            player: self.get_player_centrality(player, centrality_type)
            for player in players
        }

    def identify_passing_clusters(
        self,
        min_cluster_size: int = 3
    ) -> List[Set[str]]:
        """
        Identify clusters of players with strong passing connections.

        Args:
            min_cluster_size: Minimum players in a cluster

        Returns:
            List of player sets (clusters)
        """
        if not NETWORKX_AVAILABLE or self.graph is None:
            return []

        try:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()

            # Use Louvain community detection if available
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(undirected, weight='weight')

                # Group by community
                clusters_dict: Dict[int, Set[str]] = {}
                for player, comm in communities.items():
                    if comm not in clusters_dict:
                        clusters_dict[comm] = set()
                    clusters_dict[comm].add(player)

                # Filter by size
                clusters = [
                    cluster for cluster in clusters_dict.values()
                    if len(cluster) >= min_cluster_size
                ]

                return clusters
            except ImportError:
                # Fallback to connected components
                components = nx.connected_components(undirected)
                return [
                    set(comp) for comp in components
                    if len(comp) >= min_cluster_size
                ]
        except:
            return []


class NetworkAnalyzer:
    """
    Analyze passing networks and extract insights.

    Features:
    - Network construction from pass data
    - Centrality analysis (hub players)
    - Passing efficiency metrics
    - Network topology analysis
    - Temporal network evolution
    """

    def __init__(self):
        """Initialize network analyzer"""
        self.network = PassingNetwork()
        self.networks_by_game: Dict[str, PassingNetwork] = {}
        self.networks_by_team: Dict[str, PassingNetwork] = {}

        logger.info("NetworkAnalyzer initialized")

    def add_pass(self, pass_event: Pass):
        """Add a pass to analyzer"""
        self.network.add_pass(pass_event)

        # Index by game
        if pass_event.game_id not in self.networks_by_game:
            self.networks_by_game[pass_event.game_id] = PassingNetwork()
        self.networks_by_game[pass_event.game_id].add_pass(pass_event)

    def add_passes(self, passes: List[Pass]):
        """Add multiple passes"""
        for pass_event in passes:
            self.add_pass(pass_event)

    def analyze_player_role(
        self,
        player_id: str
    ) -> Dict[str, Any]:
        """
        Analyze player's role in passing network.

        Args:
            player_id: Player identifier

        Returns:
            Dictionary with role analysis
        """
        # Get passes involving player
        passes_from = [p for p in self.network.passes if p.passer_id == player_id]
        passes_to = [p for p in self.network.passes if p.receiver_id == player_id]

        total_passes_from = len(passes_from)
        total_passes_to = len(passes_to)
        total_passes = total_passes_from + total_passes_to

        if total_passes == 0:
            return {
                'role': 'isolated',
                'pass_ratio': 0.0,
                'centrality': 0.0
            }

        # Pass ratio (outgoing / total)
        pass_ratio = total_passes_from / total_passes if total_passes > 0 else 0.0

        # Classify role
        if pass_ratio > 0.7:
            role = 'playmaker'  # Primarily passes
        elif pass_ratio > 0.4:
            role = 'balanced'  # Both passes and receives
        else:
            role = 'finisher'  # Primarily receives

        # Get centrality
        centrality = self.network.get_player_centrality(player_id, 'degree')

        return {
            'role': role,
            'passes_from': total_passes_from,
            'passes_to': total_passes_to,
            'pass_ratio': pass_ratio,
            'centrality': centrality,
            'assists_given': sum(1 for p in passes_from if p.resulted_in_assist),
            'assists_received': sum(1 for p in passes_to if p.resulted_in_assist)
        }

    def get_ball_movement_metrics(
        self,
        game_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ball movement metrics.

        Args:
            game_id: Specific game (None = overall)

        Returns:
            Dictionary with ball movement metrics
        """
        if game_id:
            network = self.networks_by_game.get(game_id)
            if not network:
                return {}
            passes = network.passes
        else:
            passes = self.network.passes

        if not passes:
            return {}

        total_passes = len(passes)
        assists = sum(1 for p in passes if p.resulted_in_assist)
        turnovers = sum(1 for p in passes if p.resulted_in_turnover)

        # Distance metrics
        distances = [p.distance for p in passes if p.distance is not None]
        avg_distance = float(np.mean(distances)) if distances else 0.0

        # Unique passers/receivers
        unique_passers = len(set(p.passer_id for p in passes))
        unique_receivers = len(set(p.receiver_id for p in passes))

        return {
            'total_passes': total_passes,
            'assists': assists,
            'turnovers': turnovers,
            'assist_rate': assists / total_passes if total_passes > 0 else 0.0,
            'turnover_rate': turnovers / total_passes if total_passes > 0 else 0.0,
            'avg_pass_distance': avg_distance,
            'unique_passers': unique_passers,
            'unique_receivers': unique_receivers,
            'ball_movement_score': self._calculate_ball_movement_score(
                total_passes, unique_passers, avg_distance
            )
        }

    def _calculate_ball_movement_score(
        self,
        total_passes: int,
        unique_passers: int,
        avg_distance: float
    ) -> float:
        """
        Calculate overall ball movement quality score (0-100).

        Higher score = better ball movement
        """
        # Normalize components
        pass_volume_score = min(total_passes / 300.0, 1.0) * 40  # Max 40 points
        passer_diversity_score = min(unique_passers / 10.0, 1.0) * 30  # Max 30 points
        pass_distance_score = min(avg_distance / 20.0, 1.0) * 30  # Max 30 points

        return pass_volume_score + passer_diversity_score + pass_distance_score

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'total_passes': len(self.network.passes),
            'games_analyzed': len(self.networks_by_game),
            'unique_players': len(set(
                [p.passer_id for p in self.network.passes] +
                [p.receiver_id for p in self.network.passes]
            )),
            'top_connections': self.network.get_top_connections(5, 'frequency')
        }

    def clear(self):
        """Clear all stored data"""
        self.network = PassingNetwork()
        self.networks_by_game.clear()
        self.networks_by_team.clear()
        logger.info("Cleared all passing network data")
