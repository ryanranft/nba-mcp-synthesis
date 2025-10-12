"""
GraphQL API Support

Modern API alternative to REST with:
- Schema definition
- Query optimization
- Nested queries
- Type safety
- Introspection
- Subscription support

Features:
- NBA data queries
- Player/team/game resolvers
- Pagination (cursor-based)
- Filtering and sorting
- Real-time subscriptions
- DataLoader for N+1 prevention
- Schema stitching
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Player:
    """Player model"""
    id: int
    name: str
    team: str
    position: str
    jersey_number: int
    height_cm: int
    weight_kg: int
    birth_date: datetime
    ppg: float
    rpg: float
    apg: float


@dataclass
class Team:
    """Team model"""
    id: int
    name: str
    city: str
    conference: str
    division: str
    wins: int
    losses: int
    win_percentage: float


@dataclass
class Game:
    """Game model"""
    id: int
    date: datetime
    home_team: Team
    away_team: Team
    home_score: int
    away_score: int
    status: str


# GraphQL Schema Definition
SCHEMA = """
scalar DateTime

type Player {
    id: ID!
    name: String!
    team: Team!
    position: String!
    jerseyNumber: Int!
    heightCm: Int!
    weightKg: Int!
    birthDate: DateTime!
    ppg: Float!
    rpg: Float!
    apg: Float!
    stats(season: Int): PlayerStats
    games(first: Int, after: String): GameConnection!
}

type Team {
    id: ID!
    name: String!
    city: String!
    conference: String!
    division: String!
    wins: Int!
    losses: Int!
    winPercentage: Float!
    players(position: String): [Player!]!
    games(first: Int, after: String): GameConnection!
    stats(season: Int): TeamStats
}

type Game {
    id: ID!
    date: DateTime!
    homeTeam: Team!
    awayTeam: Team!
    homeScore: Int!
    awayScore: Int!
    status: String!
    playByPlay: [PlayByPlayEvent!]!
}

type PlayerStats {
    season: Int!
    gamesPlayed: Int!
    points: Int!
    rebounds: Int!
    assists: Int!
    steals: Int!
    blocks: Int!
    turnovers: Int!
    ppg: Float!
    rpg: Float!
    apg: Float!
}

type TeamStats {
    season: Int!
    gamesPlayed: Int!
    wins: Int!
    losses: Int!
    pointsFor: Int!
    pointsAgainst: Int!
    offensiveRating: Float!
    defensiveRating: Float!
}

type PlayByPlayEvent {
    timestamp: String!
    quarter: Int!
    timeRemaining: String!
    event: String!
    player: Player
    team: Team!
}

type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}

type GameEdge {
    cursor: String!
    node: Game!
}

type GameConnection {
    edges: [GameEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type Query {
    # Player queries
    player(id: ID!): Player
    players(
        first: Int
        after: String
        team: String
        position: String
        orderBy: PlayerOrderBy
    ): PlayerConnection!
    
    # Team queries
    team(id: ID!): Team
    teams(
        conference: String
        division: String
    ): [Team!]!
    
    # Game queries
    game(id: ID!): Game
    games(
        first: Int
        after: String
        date: DateTime
        team: String
        season: Int
    ): GameConnection!
    
    # Search
    search(query: String!): SearchResult!
}

type Mutation {
    updatePlayerStats(playerId: ID!, stats: PlayerStatsInput!): Player!
    updateGameScore(gameId: ID!, homeScore: Int!, awayScore: Int!): Game!
}

type Subscription {
    gameUpdated(gameId: ID!): Game!
    playerStatsUpdated(playerId: ID!): PlayerStats!
}

enum PlayerOrderBy {
    PPG_DESC
    PPG_ASC
    RPG_DESC
    RPG_ASC
    APG_DESC
    APG_ASC
    NAME_ASC
    NAME_DESC
}

input PlayerStatsInput {
    points: Int!
    rebounds: Int!
    assists: Int!
}

union SearchResult = Player | Team | Game

type PlayerConnection {
    edges: [PlayerEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type PlayerEdge {
    cursor: String!
    node: Player!
}
"""


class GraphQLResolvers:
    """GraphQL resolvers for NBA data"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.data_loaders = {}
    
    # Query Resolvers
    
    async def resolve_player(self, info, id: str) -> Optional[Player]:
        """Resolve single player by ID"""
        # Use DataLoader to batch queries
        player_loader = self._get_player_loader()
        return await player_loader.load(int(id))
    
    async def resolve_players(
        self,
        info,
        first: int = 10,
        after: Optional[str] = None,
        team: Optional[str] = None,
        position: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resolve players with pagination and filtering"""
        # Build query
        query = "SELECT * FROM players WHERE 1=1"
        params = []
        
        if team:
            query += " AND team = ?"
            params.append(team)
        
        if position:
            query += " AND position = ?"
            params.append(position)
        
        # Ordering
        order_map = {
            'PPG_DESC': 'ppg DESC',
            'PPG_ASC': 'ppg ASC',
            'NAME_ASC': 'name ASC',
            'NAME_DESC': 'name DESC'
        }
        if order_by and order_by in order_map:
            query += f" ORDER BY {order_map[order_by]}"
        
        # Cursor-based pagination
        if after:
            query += " AND id > ?"
            params.append(after)
        
        query += f" LIMIT {first + 1}"  # +1 to check hasNextPage
        
        # Execute query (mock implementation)
        players = await self._execute_query(query, params)
        
        has_next_page = len(players) > first
        if has_next_page:
            players = players[:first]
        
        edges = [
            {
                'cursor': str(player.id),
                'node': player
            }
            for player in players
        ]
        
        return {
            'edges': edges,
            'pageInfo': {
                'hasNextPage': has_next_page,
                'hasPreviousPage': after is not None,
                'startCursor': edges[0]['cursor'] if edges else None,
                'endCursor': edges[-1]['cursor'] if edges else None
            },
            'totalCount': await self._count_players(team, position)
        }
    
    async def resolve_team(self, info, id: str) -> Optional[Team]:
        """Resolve single team by ID"""
        team_loader = self._get_team_loader()
        return await team_loader.load(int(id))
    
    async def resolve_teams(
        self,
        info,
        conference: Optional[str] = None,
        division: Optional[str] = None
    ) -> List[Team]:
        """Resolve teams with filtering"""
        query = "SELECT * FROM teams WHERE 1=1"
        params = []
        
        if conference:
            query += " AND conference = ?"
            params.append(conference)
        
        if division:
            query += " AND division = ?"
            params.append(division)
        
        return await self._execute_query(query, params)
    
    async def resolve_game(self, info, id: str) -> Optional[Game]:
        """Resolve single game by ID"""
        game_loader = self._get_game_loader()
        return await game_loader.load(int(id))
    
    async def resolve_search(self, info, query: str) -> Dict[str, Any]:
        """Search across players, teams, and games"""
        results = {
            'players': await self._search_players(query),
            'teams': await self._search_teams(query),
            'games': await self._search_games(query)
        }
        return results
    
    # Field Resolvers
    
    async def resolve_player_team(self, player: Player, info) -> Team:
        """Resolve team for a player"""
        team_loader = self._get_team_loader()
        return await team_loader.load_by_name(player.team)
    
    async def resolve_player_stats(
        self,
        player: Player,
        info,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """Resolve player stats for a season"""
        if not season:
            season = datetime.now().year
        
        return await self._get_player_stats(player.id, season)
    
    async def resolve_team_players(
        self,
        team: Team,
        info,
        position: Optional[str] = None
    ) -> List[Player]:
        """Resolve players for a team"""
        query = "SELECT * FROM players WHERE team = ?"
        params = [team.name]
        
        if position:
            query += " AND position = ?"
            params.append(position)
        
        return await self._execute_query(query, params)
    
    # Mutation Resolvers
    
    async def resolve_update_player_stats(
        self,
        info,
        player_id: str,
        stats: Dict[str, int]
    ) -> Player:
        """Update player stats"""
        await self._update_player_stats(int(player_id), stats)
        player_loader = self._get_player_loader()
        player_loader.clear(int(player_id))  # Clear cache
        return await player_loader.load(int(player_id))
    
    async def resolve_update_game_score(
        self,
        info,
        game_id: str,
        home_score: int,
        away_score: int
    ) -> Game:
        """Update game score"""
        await self._update_game_score(
            int(game_id),
            home_score,
            away_score
        )
        
        # Notify subscribers
        await self._publish_game_update(int(game_id))
        
        game_loader = self._get_game_loader()
        game_loader.clear(int(game_id))
        return await game_loader.load(int(game_id))
    
    # DataLoader implementations
    
    def _get_player_loader(self):
        """Get or create player DataLoader"""
        if 'player' not in self.data_loaders:
            from dataloader import DataLoader
            self.data_loaders['player'] = DataLoader(self._batch_load_players)
        return self.data_loaders['player']
    
    def _get_team_loader(self):
        """Get or create team DataLoader"""
        if 'team' not in self.data_loaders:
            from dataloader import DataLoader
            self.data_loaders['team'] = DataLoader(self._batch_load_teams)
        return self.data_loaders['team']
    
    def _get_game_loader(self):
        """Get or create game DataLoader"""
        if 'game' not in self.data_loaders:
            from dataloader import DataLoader
            self.data_loaders['game'] = DataLoader(self._batch_load_games)
        return self.data_loaders['game']
    
    async def _batch_load_players(self, ids: List[int]) -> List[Optional[Player]]:
        """Batch load players by IDs"""
        query = f"SELECT * FROM players WHERE id IN ({','.join('?' * len(ids))})"
        players = await self._execute_query(query, ids)
        player_map = {p.id: p for p in players}
        return [player_map.get(id) for id in ids]
    
    async def _batch_load_teams(self, ids: List[int]) -> List[Optional[Team]]:
        """Batch load teams by IDs"""
        query = f"SELECT * FROM teams WHERE id IN ({','.join('?' * len(ids))})"
        teams = await self._execute_query(query, ids)
        team_map = {t.id: t for t in teams}
        return [team_map.get(id) for id in ids]
    
    async def _batch_load_games(self, ids: List[int]) -> List[Optional[Game]]:
        """Batch load games by IDs"""
        query = f"SELECT * FROM games WHERE id IN ({','.join('?' * len(ids))})"
        games = await self._execute_query(query, ids)
        game_map = {g.id: g for g in games}
        return [game_map.get(id) for id in ids]
    
    # Mock database operations
    
    async def _execute_query(self, query: str, params: List[Any]) -> List[Any]:
        """Execute database query (mock)"""
        logger.info(f"Executing query: {query} with params: {params}")
        # In real implementation, use actual database
        return []
    
    async def _count_players(
        self,
        team: Optional[str] = None,
        position: Optional[str] = None
    ) -> int:
        """Count players with filters"""
        # Mock implementation
        return 450
    
    async def _get_player_stats(self, player_id: int, season: int) -> Dict[str, Any]:
        """Get player stats for season"""
        # Mock implementation
        return {
            'season': season,
            'gamesPlayed': 82,
            'points': 2100,
            'rebounds': 650,
            'assists': 450
        }
    
    async def _update_player_stats(self, player_id: int, stats: Dict[str, int]) -> None:
        """Update player stats"""
        logger.info(f"Updating stats for player {player_id}: {stats}")
    
    async def _update_game_score(
        self,
        game_id: int,
        home_score: int,
        away_score: int
    ) -> None:
        """Update game score"""
        logger.info(f"Updating game {game_id}: {home_score}-{away_score}")
    
    async def _publish_game_update(self, game_id: int) -> None:
        """Publish game update to subscribers"""
        logger.info(f"Publishing update for game {game_id}")
    
    async def _search_players(self, query: str) -> List[Player]:
        """Search players"""
        return []
    
    async def _search_teams(self, query: str) -> List[Team]:
        """Search teams"""
        return []
    
    async def _search_games(self, query: str) -> List[Game]:
        """Search games"""
        return []


class GraphQLServer:
    """GraphQL server setup"""
    
    def __init__(self, resolvers: GraphQLResolvers):
        self.resolvers = resolvers
        self.schema = SCHEMA
    
    def create_app(self):
        """Create GraphQL application"""
        try:
            from graphene import Schema
            from flask import Flask
            from flask_graphql import GraphQLView
            
            app = Flask(__name__)
            
            # Create GraphQL endpoint
            app.add_url_rule(
                '/graphql',
                view_func=GraphQLView.as_view(
                    'graphql',
                    schema=self.schema,
                    graphiql=True  # Enable GraphiQL interface
                )
            )
            
            return app
        except ImportError:
            logger.error("graphene or flask-graphql not installed")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example GraphQL queries
    print("=== GraphQL Schema ===\n")
    print(SCHEMA[:500] + "...\n")
    
    print("=== Example Query ===\n")
    example_query = """
    query {
      player(id: "1") {
        name
        team {
          name
          city
        }
        ppg
        rpg
        apg
        stats(season: 2024) {
          gamesPlayed
          points
        }
      }
    }
    """
    print(example_query)
    
    print("\n=== Example Mutation ===\n")
    example_mutation = """
    mutation {
      updatePlayerStats(
        playerId: "1"
        stats: {
          points: 35
          rebounds: 10
          assists: 8
        }
      ) {
        name
        ppg
      }
    }
    """
    print(example_mutation)

