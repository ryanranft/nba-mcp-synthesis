"""
ML Prediction Integration for Daily Betting Automation

This module integrates the existing production ML prediction system with the
daily betting automation workflow. It wraps:
- Trained ensemble model (Logistic + RF + XGBoost)
- Feature extraction from live database
- Probability calibration
- Confidence scoring

Purpose:
    Replace mock predictions in daily_betting_analysis.py with real ML predictions
    from the production-ready ensemble model.

Usage:
    from mcp_server.betting.ml_predictions import MLPredictionGenerator

    generator = MLPredictionGenerator()
    predictions = generator.generate_predictions_for_today()

    # Returns list of dicts:
    # [{
    #     'game_id': '0022400123',
    #     'game_date': '2025-01-06',
    #     'home_team': 'Los Angeles Lakers',
    #     'away_team': 'Golden State Warriors',
    #     'prob_home': 0.58,
    #     'prob_away': 0.42,
    #     'confidence': 0.85,
    #     'commence_time': '7:00 PM ET'
    # }, ...]

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import sys
import os
import pickle
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path

import psycopg2
import numpy as np

from mcp_server.unified_secrets_manager import load_secrets_hierarchical

# Import GameOutcomeEnsemble for unpickling
# The class definition is needed before loading the pickled model
try:
    # Add scripts directory to path so we can import from train_game_outcome_model
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from train_game_outcome_model import GameOutcomeEnsemble

    HAS_ENSEMBLE_CLASS = True
except ImportError as e:
    HAS_ENSEMBLE_CLASS = False
    logger.warning(f"Could not import GameOutcomeEnsemble: {e}")

logger = logging.getLogger(__name__)


class MLPredictionGenerator:
    """
    Generate ML predictions for today's NBA games

    Integrates with existing production infrastructure:
    - Ensemble model from models/ensemble_game_outcome_model.pkl
    - Feature extraction via FeatureExtractor
    - Database connection for game data
    """

    def __init__(
        self,
        model_path: str = "models/ensemble_game_outcome_model.pkl",
        min_confidence: float = 0.5,
        use_calibration: bool = True,
    ):
        """
        Initialize ML prediction generator

        Args:
            model_path: Path to trained ensemble model
            min_confidence: Minimum confidence threshold (0-1)
            use_calibration: Use calibrated probabilities if available
        """
        self.model_path = model_path
        self.min_confidence = min_confidence
        self.use_calibration = use_calibration

        # Will be loaded lazily
        self.model = None
        self.feature_extractor = None
        self.db_conn = None

        logger.info(f"MLPredictionGenerator initialized (model: {model_path})")

    def _load_model(self):
        """Load trained ensemble model"""
        if self.model is not None:
            return  # Already loaded

        if not HAS_ENSEMBLE_CLASS:
            raise ImportError(
                "GameOutcomeEnsemble class not available. "
                "Cannot unpickle model without class definition."
            )

        model_path = Path(self.model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Please run: python scripts/train_game_outcome_model.py"
            )

        try:
            import dill as pickle_lib
        except ImportError:
            import pickle as pickle_lib

        try:
            # Custom unpickler to handle GameOutcomeEnsemble from different module
            import io
            import sys

            # Read the file
            with open(model_path, "rb") as f:
                model_bytes = f.read()

            # Create a custom unpickler that remaps __main__.GameOutcomeEnsemble
            class CustomUnpickler(pickle_lib.Unpickler):
                def find_class(self, module, name):
                    # Remap __main__.GameOutcomeEnsemble to our imported class
                    if module == "__main__" and name == "GameOutcomeEnsemble":
                        if HAS_ENSEMBLE_CLASS:
                            return GameOutcomeEnsemble
                    return super().find_class(module, name)

            # Unpickle with custom handler
            self.model = CustomUnpickler(io.BytesIO(model_bytes)).load()

        except Exception as e:
            logger.error(f"Failed to load model with custom unpickler: {e}")
            # Fallback to standard unpickling
            with open(model_path, "rb") as f:
                self.model = pickle_lib.load(f)

        logger.info(f"✅ Loaded ensemble model from {model_path}")

        # Get model metadata if available
        if hasattr(self.model, "metadata"):
            metadata = self.model.metadata
            logger.info(f"   Model trained: {metadata.get('training_date', 'unknown')}")
            logger.info(f"   Test accuracy: {metadata.get('test_accuracy', 'unknown')}")
            logger.info(f"   Test AUC: {metadata.get('test_auc', 'unknown')}")

    def _connect_database(self):
        """Establish database connection"""
        if self.db_conn is not None:
            return  # Already connected

        # Get credentials from environment (loaded by secrets manager)
        db_host = os.getenv("RDS_HOST")
        db_port = os.getenv("RDS_PORT", "5432")
        db_name = os.getenv("RDS_DATABASE")
        db_user = os.getenv("RDS_USERNAME")
        db_pass = os.getenv("RDS_PASSWORD")

        if not all([db_host, db_name, db_user, db_pass]):
            raise ValueError(
                "Database credentials not found. "
                "Ensure secrets are loaded via load_secrets_hierarchical()"
            )

        self.db_conn = psycopg2.connect(
            host=db_host, port=db_port, database=db_name, user=db_user, password=db_pass
        )

        logger.info(f"✅ Connected to database: {db_name}")

    def _initialize_feature_extractor(self):
        """Initialize feature extractor"""
        if self.feature_extractor is not None:
            return  # Already initialized

        from mcp_server.betting.feature_extractor import FeatureExtractor

        self.feature_extractor = FeatureExtractor(db_conn=self.db_conn)
        logger.info("✅ Feature extractor initialized")

    def _fetch_todays_games(self) -> List[Dict[str, Any]]:
        """
        Fetch today's NBA games from database

        Returns:
            List of game dicts with game_id, home_team, away_team, etc.
        """
        cursor = self.db_conn.cursor()
        today = date.today().strftime("%Y-%m-%d")

        query = """
            SELECT
                g.game_id,
                g.home_team_id,
                g.away_team_id,
                ht.team_name as home_team_name,
                vt.team_name as away_team_name,
                g.game_date,
                g.game_time
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams vt ON g.away_team_id = vt.team_id
            WHERE g.game_date = %s
            AND g.home_score IS NULL  -- Game not played yet
            ORDER BY g.game_date
        """

        cursor.execute(query, (today,))
        games = cursor.fetchall()

        return [
            {
                "game_id": g[0],
                "home_team_id": g[1],
                "away_team_id": g[2],
                "home_team": g[3],
                "away_team": g[4],
                "game_date": str(g[5]),
                "game_time": str(g[6]) if g[6] else None,
            }
            for g in games
        ]

    def _predict_game(
        self,
        game_id: str,
        home_team_id: int,
        away_team_id: int,
        home_team: str,
        away_team: str,
    ) -> Dict[str, Any]:
        """
        Generate prediction for a single game

        Args:
            game_id: Game identifier
            home_team_id: Home team ID
            away_team_id: Away team ID
            home_team: Home team name
            away_team: Away team name

        Returns:
            Prediction dict with probabilities and confidence
        """
        try:
            # Extract features for this game
            features = self.feature_extractor.extract_game_features(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                game_date=date.today(),
            )

            if features is None or len(features) == 0:
                logger.warning(f"No features extracted for {away_team} @ {home_team}")
                return None

            # Reshape for prediction (model expects 2D array)
            features_array = np.array(features).reshape(1, -1)

            # Get probability predictions
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(features_array)[0]
                prob_home = float(proba[1])  # Index 1 is typically "home win"
            else:
                # Fallback to binary prediction
                prediction = self.model.predict(features_array)[0]
                prob_home = 0.7 if prediction == 1 else 0.3
                logger.warning(f"Model doesn't support predict_proba, using fallback")

            prob_away = 1.0 - prob_home

            # Calculate confidence (how far from 50/50)
            confidence = abs(prob_home - 0.5) * 2.0  # Maps 0.5-1.0 to 0.0-1.0

            # Use calibrated probability if available
            if self.use_calibration and hasattr(self.model, "calibrate"):
                try:
                    prob_home = self.model.calibrate(prob_home)
                    prob_away = 1.0 - prob_home
                except Exception as e:
                    logger.debug(f"Calibration not available: {e}")

            return {
                "prob_home": prob_home,
                "prob_away": prob_away,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error predicting {away_team} @ {home_team}: {e}")
            return None

    def generate_predictions_for_today(self) -> List[Dict[str, Any]]:
        """
        Generate predictions for all of today's NBA games

        Returns:
            List of prediction dicts matching the format expected by
            daily_betting_analysis.py:
            [{
                'game_id': str,
                'game_date': str (YYYY-MM-DD),
                'home_team': str,
                'away_team': str,
                'prob_home': float (0-1),
                'prob_away': float (0-1),
                'confidence': float (0-1),
                'commence_time': str (e.g., "7:00 PM ET")
            }, ...]
        """
        predictions = []

        try:
            # Lazy initialization
            self._load_model()
            self._connect_database()
            self._initialize_feature_extractor()

            # Fetch today's games
            games = self._fetch_todays_games()

            if not games:
                logger.info("No games scheduled for today")
                return []

            logger.info(f"Generating predictions for {len(games)} games...")

            # Generate prediction for each game
            for game in games:
                prediction = self._predict_game(
                    game_id=game["game_id"],
                    home_team_id=game["home_team_id"],
                    away_team_id=game["away_team_id"],
                    home_team=game["home_team"],
                    away_team=game["away_team"],
                )

                if prediction is None:
                    continue  # Skip games with errors

                # Check confidence threshold
                if prediction["confidence"] < self.min_confidence:
                    logger.info(
                        f"Skipping {game['away_team']} @ {game['home_team']}: "
                        f"Low confidence ({prediction['confidence']:.2f})"
                    )
                    continue

                # Format game time
                game_time = game.get("game_time")
                if game_time:
                    try:
                        # Convert to readable format (e.g., "7:00 PM ET")
                        time_obj = datetime.strptime(str(game_time), "%H:%M:%S")
                        commence_time = time_obj.strftime("%-I:%M %p ET")
                    except:
                        commence_time = str(game_time)
                else:
                    commence_time = "TBD"

                # Build prediction dict
                predictions.append(
                    {
                        "game_id": game["game_id"],
                        "game_date": game["game_date"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "prob_home": prediction["prob_home"],
                        "prob_away": prediction["prob_away"],
                        "confidence": prediction["confidence"],
                        "commence_time": commence_time,
                    }
                )

            logger.info(f"✅ Generated {len(predictions)} predictions")

            return predictions

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.db_conn is not None:
            self.db_conn.close()
            logger.info("Database connection closed")


def generate_ml_predictions() -> List[Dict[str, Any]]:
    """
    Convenience function to generate ML predictions for today

    This is the main entry point for daily_betting_analysis.py

    Returns:
        List of prediction dicts
    """
    generator = MLPredictionGenerator()

    try:
        predictions = generator.generate_predictions_for_today()
        return predictions
    finally:
        generator.close()


if __name__ == "__main__":
    # Test ML predictions
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative paths (models/)
    os.chdir(project_root)

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical

    print("=" * 70)
    print("ML Prediction Generator - Test")
    print("=" * 70)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    print("✅ Secrets loaded")
    print()

    # Generate predictions
    print("🎯 Generating predictions...")
    try:
        predictions = generate_ml_predictions()

        print(f"✅ Generated {len(predictions)} predictions")
        print()

        if predictions:
            print("Predictions:")
            print("-" * 70)
            for i, pred in enumerate(predictions, 1):
                print(f"{i}. {pred['away_team']} @ {pred['home_team']}")
                print(f"   Date: {pred['game_date']} at {pred['commence_time']}")
                print(f"   Home win probability: {pred['prob_home']:.1%}")
                print(f"   Away win probability: {pred['prob_away']:.1%}")
                print(f"   Confidence: {pred['confidence']:.1%}")
                print()
        else:
            print("ℹ️  No games scheduled for today")

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print()
        print("To train the model, run:")
        print("  python scripts/prepare_game_features.py")
        print("  python scripts/train_game_outcome_model.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
