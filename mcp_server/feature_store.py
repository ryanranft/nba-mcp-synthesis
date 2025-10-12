"""Feature Store - BOOK RECOMMENDATION 4"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from mcp_server.database import get_database_engine

logger = logging.getLogger(__name__)


class FeatureStore:
    """Centralized feature storage and serving"""

    def __init__(self):
        """Initialize feature store"""
        self.engine = None
        self.feature_registry = {}

    def init_engine(self):
        """Initialize database engine"""
        if not self.engine:
            self.engine = get_database_engine()

    def register_feature(
        self,
        name: str,
        description: str,
        entity_type: str,
        value_type: str,
        tags: Optional[List[str]] = None
    ):
        """
        Register a feature in the feature store

        Args:
            name: Feature name
            description: Feature description
            entity_type: Entity type (player, team, game)
            value_type: Value type (float, int, string)
            tags: Optional tags for categorization
        """
        self.feature_registry[name] = {
            "name": name,
            "description": description,
            "entity_type": entity_type,
            "value_type": value_type,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"✅ Registered feature: {name} ({entity_type})")

    def store_features(
        self,
        entity_id: str,
        entity_type: str,
        features: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        Store features for an entity

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            features: Dictionary of feature name -> value
            timestamp: Optional timestamp (defaults to now)
        """
        self.init_engine()

        timestamp = timestamp or datetime.utcnow()

        # Store in database
        from sqlalchemy import text

        with self.engine.begin() as conn:
            for feature_name, value in features.items():
                query = text("""
                    INSERT INTO feature_store (
                        entity_id, entity_type, feature_name, feature_value, timestamp
                    ) VALUES (
                        :entity_id, :entity_type, :feature_name, :feature_value, :timestamp
                    )
                    ON CONFLICT (entity_id, entity_type, feature_name, timestamp)
                    DO UPDATE SET feature_value = EXCLUDED.feature_value
                """)

                conn.execute(query, {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "feature_name": feature_name,
                    "feature_value": str(value),
                    "timestamp": timestamp
                })

        logger.debug(f"✅ Stored {len(features)} features for {entity_type} {entity_id}")

    def get_features(
        self,
        entity_id: str,
        entity_type: str,
        feature_names: Optional[List[str]] = None,
        as_of: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Retrieve features for an entity

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            feature_names: Optional list of specific features
            as_of: Optional point-in-time lookup

        Returns:
            Dictionary of feature name -> value
        """
        self.init_engine()

        as_of = as_of or datetime.utcnow()

        from sqlalchemy import text

        query = text("""
            WITH latest_features AS (
                SELECT
                    feature_name,
                    feature_value,
                    timestamp,
                    ROW_NUMBER() OVER (
                        PARTITION BY feature_name
                        ORDER BY timestamp DESC
                    ) as rn
                FROM feature_store
                WHERE entity_id = :entity_id
                  AND entity_type = :entity_type
                  AND timestamp <= :as_of
                  AND (:feature_names IS NULL OR feature_name = ANY(:feature_names))
            )
            SELECT feature_name, feature_value
            FROM latest_features
            WHERE rn = 1
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "as_of": as_of,
                "feature_names": feature_names
            })

            features = {row["feature_name"]: row["feature_value"] for row in result}

        logger.debug(f"✅ Retrieved {len(features)} features for {entity_type} {entity_id}")
        return features

    def get_feature_history(
        self,
        entity_id: str,
        entity_type: str,
        feature_name: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get historical values for a feature

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            feature_name: Feature name
            start_date: Start date
            end_date: End date (defaults to now)

        Returns:
            DataFrame with timestamp and feature_value columns
        """
        self.init_engine()

        end_date = end_date or datetime.utcnow()

        from sqlalchemy import text

        query = text("""
            SELECT timestamp, feature_value
            FROM feature_store
            WHERE entity_id = :entity_id
              AND entity_type = :entity_type
              AND feature_name = :feature_name
              AND timestamp BETWEEN :start_date AND :end_date
            ORDER BY timestamp
        """)

        df = pd.read_sql(query, self.engine, params={
            "entity_id": entity_id,
            "entity_type": entity_type,
            "feature_name": feature_name,
            "start_date": start_date,
            "end_date": end_date
        })

        logger.debug(f"✅ Retrieved {len(df)} historical values for {feature_name}")
        return df

    def compute_and_store_feature(
        self,
        entity_id: str,
        entity_type: str,
        feature_name: str,
        compute_func: callable
    ):
        """
        Compute a feature on-demand and store it

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            feature_name: Feature name
            compute_func: Function to compute feature value
        """
        # Compute feature value
        value = compute_func(entity_id, entity_type)

        # Store in feature store
        self.store_features(entity_id, entity_type, {feature_name: value})

        logger.info(f"✅ Computed and stored {feature_name} for {entity_type} {entity_id}")
        return value

    def list_features(self, entity_type: Optional[str] = None) -> List[Dict]:
        """
        List all registered features

        Args:
            entity_type: Optional filter by entity type

        Returns:
            List of feature metadata
        """
        features = list(self.feature_registry.values())

        if entity_type:
            features = [f for f in features if f["entity_type"] == entity_type]

        return features

    def search_features(self, query: str) -> List[Dict]:
        """
        Search features by name or description

        Args:
            query: Search query

        Returns:
            Matching features
        """
        query_lower = query.lower()

        matches = []
        for feature in self.feature_registry.values():
            if (query_lower in feature["name"].lower() or
                query_lower in feature["description"].lower() or
                any(query_lower in tag.lower() for tag in feature["tags"])):
                matches.append(feature)

        return matches


# Global feature store
_feature_store = None


def get_feature_store() -> FeatureStore:
    """Get global feature store"""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store


# Register common NBA features
def register_nba_features():
    """Register common NBA features"""
    store = get_feature_store()

    # Player features
    store.register_feature(
        "points_per_game",
        "Average points per game over last 10 games",
        "player",
        "float",
        ["offense", "scoring"]
    )

    store.register_feature(
        "assists_per_game",
        "Average assists per game over last 10 games",
        "player",
        "float",
        ["offense", "playmaking"]
    )

    store.register_feature(
        "rebounds_per_game",
        "Average rebounds per game over last 10 games",
        "player",
        "float",
        ["defense", "rebounding"]
    )

    store.register_feature(
        "player_efficiency_rating",
        "PER calculated over season",
        "player",
        "float",
        ["advanced", "efficiency"]
    )

    # Team features
    store.register_feature(
        "win_percentage",
        "Team win percentage over season",
        "team",
        "float",
        ["team", "performance"]
    )

    store.register_feature(
        "offensive_rating",
        "Points per 100 possessions",
        "team",
        "float",
        ["team", "offense"]
    )

    logger.info("✅ Registered standard NBA features")


# Example usage
if __name__ == "__main__":
    # Initialize and register features
    register_nba_features()

    store = get_feature_store()

    # Store features
    store.store_features(
        entity_id="player_123",
        entity_type="player",
        features={
            "points_per_game": 25.3,
            "assists_per_game": 7.2,
            "rebounds_per_game": 8.1
        }
    )

    # Retrieve features
    features = store.get_features("player_123", "player")
    print(f"Features: {features}")

    # Search features
    results = store.search_features("points")
    print(f"Found {len(results)} features matching 'points'")

