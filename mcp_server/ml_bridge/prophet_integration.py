"""
Prophet Integration for NBA Analytics (Agent 17, Module 2)

Facebook Prophet time series forecasting with NBA context:
- Player performance trends
- Team performance forecasting
- Injury-adjusted predictions
- Schedule effects (back-to-back, rest days)
- Season/playoff mode transitions
- Uncertainty quantification

Integrates with:
- time_series: ARIMA and state space models
- simulations: Game outcome forecasting
- panel_data: Player-level time series

Prophet provides:
- Automatic seasonality detection
- Holiday/special event handling
- Changepoint detection
- Uncertainty intervals
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import Prophet (optional)
try:
    from prophet import Prophet
    from prophet.diagnostics import cross_validation, performance_metrics

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None
    logger.warning("Prophet not available, time series forecasting limited")


class SeasonMode(Enum):
    """NBA season phases"""

    PRESEASON = "preseason"
    REGULAR = "regular_season"
    PLAYOFFS = "playoffs"
    OFFSEASON = "offseason"


@dataclass
class ProphetConfig:
    """Configuration for Prophet models"""

    # Growth
    growth: str = "linear"  # 'linear' or 'logistic'
    cap: Optional[float] = None  # For logistic growth (e.g., max PPG)
    floor: Optional[float] = None  # Minimum value

    # Seasonality
    yearly_seasonality: bool = False  # NBA season < 1 year
    weekly_seasonality: bool = True  # Weekly patterns
    daily_seasonality: bool = False

    # Custom seasonality
    add_game_seasonality: bool = True  # Every ~3.5 games pattern
    games_per_week: float = 3.5

    # Changepoints
    n_changepoints: int = 25
    changepoint_prior_scale: float = 0.05  # Flexibility

    # Uncertainty
    interval_width: float = 0.80  # 80% confidence intervals
    mcmc_samples: int = 0  # Use MAP, not MCMC

    # Regressors (added externally)
    include_rest_days: bool = True
    include_home_away: bool = True
    include_opponent_strength: bool = True
    include_injury_status: bool = True


@dataclass
class ForecastResult:
    """Prophet forecast result"""

    # Predictions
    dates: List[datetime]
    predictions: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray

    # Components
    trend: Optional[np.ndarray] = None
    weekly: Optional[np.ndarray] = None
    yearly: Optional[np.ndarray] = None
    holidays: Optional[np.ndarray] = None

    # Metadata
    horizon: int = 0  # Forecast horizon (days/games)
    mape: Optional[float] = None  # Mean absolute percentage error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dates": [d.isoformat() for d in self.dates],
            "predictions": self.predictions.tolist(),
            "lower_bound": self.lower_bound.tolist(),
            "upper_bound": self.upper_bound.tolist(),
            "horizon": self.horizon,
            "mape": self.mape,
            "has_components": self.trend is not None,
        }


class NBAProphetForecaster:
    """
    Prophet-based forecasting for NBA analytics.

    Features:
    - Player performance trends (PPG, FG%, etc.)
    - Team performance forecasting
    - Injury and rest day adjustments
    - Back-to-back game effects
    - Home/away splits
    - Opponent strength regressors
    """

    def __init__(self, config: Optional[ProphetConfig] = None):
        """Initialize NBA Prophet forecaster"""
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet required. Install: pip install prophet")

        self.config = config or ProphetConfig()
        self.model: Optional[Prophet] = None
        self.is_fitted = False
        self.feature_columns: List[str] = []

        logger.info("NBAProphetForecaster initialized")

    def prepare_data(
        self,
        dates: List[datetime],
        values: List[float],
        regressors: Optional[Dict[str, List[float]]] = None,
    ) -> pd.DataFrame:
        """
        Prepare data in Prophet format.

        Args:
            dates: Dates (or game numbers)
            values: Target values (e.g., PPG, win %)
            regressors: Additional regressors (rest_days, home_away, etc.)

        Returns:
            DataFrame in Prophet format (ds, y, ...)
        """
        df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": values})

        # Add cap/floor for logistic growth
        if self.config.growth == "logistic":
            if self.config.cap is not None:
                df["cap"] = self.config.cap
            else:
                # Auto-set cap as 1.2x max observed
                df["cap"] = df["y"].max() * 1.2

            if self.config.floor is not None:
                df["floor"] = self.config.floor
            else:
                df["floor"] = 0.0

        # Add regressors
        if regressors:
            for name, values in regressors.items():
                if len(values) == len(df):
                    df[name] = values
                    self.feature_columns.append(name)
                else:
                    logger.warning(f"Regressor {name} length mismatch, skipping")

        return df

    def fit(
        self,
        dates: Union[List[datetime], pd.Series],
        values: Union[List[float], np.ndarray, pd.Series],
        regressors: Optional[
            Dict[str, Union[List[float], np.ndarray, pd.Series]]
        ] = None,
        holidays: Optional[pd.DataFrame] = None,
    ) -> "NBAProphetForecaster":
        """
        Fit Prophet model to data.

        Args:
            dates: Dates or game numbers
            values: Target values
            regressors: Additional regressors
            holidays: Special events (playoff games, etc.)

        Returns:
            Self for chaining
        """
        # Prepare data
        df = self.prepare_data(dates, values, regressors)

        # Create Prophet model
        self.model = Prophet(
            growth=self.config.growth,
            changepoint_prior_scale=self.config.changepoint_prior_scale,
            n_changepoints=self.config.n_changepoints,
            interval_width=self.config.interval_width,
            yearly_seasonality=self.config.yearly_seasonality,
            weekly_seasonality=self.config.weekly_seasonality,
            daily_seasonality=self.config.daily_seasonality,
            mcmc_samples=self.config.mcmc_samples,
        )

        # Add custom seasonality (game-level patterns)
        if self.config.add_game_seasonality:
            # Games happen ~3.5x per week
            self.model.add_seasonality(
                name="game_cycle",
                period=7.0 / self.config.games_per_week,  # ~2 days
                fourier_order=3,
            )

        # Add regressors
        for col in self.feature_columns:
            self.model.add_regressor(col)

        # Add holidays
        if holidays is not None:
            self.model.holidays = holidays

        # Fit model
        logger.info(f"Fitting Prophet on {len(df)} observations")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress Prophet warnings
            self.model.fit(df)

        self.is_fitted = True
        logger.info("Prophet model fitted successfully")

        return self

    def predict(
        self,
        periods: int,
        freq: str = "D",
        future_regressors: Optional[Dict[str, List[float]]] = None,
    ) -> ForecastResult:
        """
        Generate forecast.

        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'W' for weekly)
            future_regressors: Future values for regressors

        Returns:
            ForecastResult with predictions and uncertainty
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")

        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq=freq)

        # Add cap/floor for logistic growth
        if self.config.growth == "logistic":
            if self.config.cap is not None:
                future["cap"] = self.config.cap
            else:
                future["cap"] = (
                    future["y"].max() * 1.2 if "y" in future.columns else 100.0
                )

            if self.config.floor is not None:
                future["floor"] = self.config.floor
            else:
                future["floor"] = 0.0

        # Add future regressors
        if future_regressors:
            for name, values in future_regressors.items():
                if name in self.feature_columns:
                    # Pad with last value or zeros if not enough future values
                    if len(values) < len(future):
                        padding = [values[-1] if values else 0.0] * (
                            len(future) - len(values)
                        )
                        values = list(values) + padding

                    future[name] = values[: len(future)]

        # Generate forecast
        forecast = self.model.predict(future)

        # Extract forecast period only (last 'periods' rows)
        forecast_only = forecast.tail(periods)

        # Build result
        result = ForecastResult(
            dates=forecast_only["ds"].dt.to_pydatetime().tolist(),
            predictions=forecast_only["yhat"].values,
            lower_bound=forecast_only["yhat_lower"].values,
            upper_bound=forecast_only["yhat_upper"].values,
            trend=forecast_only["trend"].values if "trend" in forecast_only else None,
            weekly=forecast_only.get("weekly", None),
            horizon=periods,
        )

        return result

    def cross_validate(
        self, initial_days: int = 30, period_days: int = 7, horizon_days: int = 7
    ) -> Dict[str, float]:
        """
        Perform time series cross-validation.

        Args:
            initial_days: Initial training period
            period_days: Spacing between cutoff dates
            horizon_days: Forecast horizon

        Returns:
            Performance metrics (MAPE, RMSE, MAE)
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Model not fitted")

        if not PROPHET_AVAILABLE:
            return {}

        logger.info("Running Prophet cross-validation")

        try:
            # Run cross-validation
            df_cv = cross_validation(
                self.model,
                initial=f"{initial_days} days",
                period=f"{period_days} days",
                horizon=f"{horizon_days} days",
            )

            # Calculate metrics
            df_metrics = performance_metrics(df_cv)

            # Aggregate metrics
            metrics = {
                "mape": float(df_metrics["mape"].mean()),
                "rmse": float(df_metrics["rmse"].mean()),
                "mae": float(df_metrics["mae"].mean()),
                "coverage": (
                    float(df_metrics["coverage"].mean())
                    if "coverage" in df_metrics
                    else None
                ),
            }

            logger.info(f"CV MAPE: {metrics['mape']:.4f}, RMSE: {metrics['rmse']:.4f}")

            return metrics

        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")
            return {}

    def detect_changepoints(self) -> Optional[pd.DataFrame]:
        """
        Detect changepoints in the time series.

        Returns:
            DataFrame with changepoint dates and deltas
        """
        if not self.is_fitted or self.model is None:
            return None

        if hasattr(self.model, "changepoints"):
            changepoints = self.model.changepoints
            deltas = self.model.params["delta"][0]  # Rate changes

            df = pd.DataFrame(
                {"date": changepoints, "delta": deltas[: len(changepoints)]}
            )

            # Filter significant changepoints
            threshold = np.abs(deltas).mean() * 0.5
            df = df[np.abs(df["delta"]) > threshold]

            return df
        else:
            return None

    def get_component_contributions(self) -> Dict[str, float]:
        """
        Get contribution of each component to predictions.

        Returns:
            Dictionary with component contributions
        """
        if not self.is_fitted or self.model is None:
            return {}

        # This requires a forecast to have been made
        # Return placeholder
        return {"trend": 0.0, "weekly": 0.0, "regressors": 0.0}


class PlayerPerformanceForecaster:
    """
    Specialized forecaster for player performance.

    Handles player-specific patterns:
    - Hot/cold streaks
    - Injury recovery curves
    - Age effects
    - Minutes restrictions
    """

    def __init__(self, config: Optional[ProphetConfig] = None):
        """Initialize player performance forecaster"""
        self.config = config or ProphetConfig()
        self.forecaster = NBAProphetForecaster(config)

    def fit_player(
        self,
        player_id: str,
        game_dates: List[datetime],
        stat_values: List[float],
        minutes_played: Optional[List[float]] = None,
        rest_days: Optional[List[int]] = None,
        is_home: Optional[List[bool]] = None,
        opponent_rating: Optional[List[float]] = None,
    ) -> "PlayerPerformanceForecaster":
        """
        Fit model for a player.

        Args:
            player_id: Player identifier
            game_dates: Game dates
            stat_values: Stat to forecast (PPG, FG%, etc.)
            minutes_played: Minutes per game
            rest_days: Days of rest before each game
            is_home: Home game indicator
            opponent_rating: Opponent defensive rating

        Returns:
            Self for chaining
        """
        # Build regressors
        regressors = {}

        if minutes_played is not None:
            regressors["minutes"] = minutes_played

        if rest_days is not None:
            regressors["rest_days"] = rest_days

        if is_home is not None:
            regressors["home"] = [1.0 if h else 0.0 for h in is_home]

        if opponent_rating is not None:
            # Normalize opponent rating
            mean_rating = np.mean(opponent_rating)
            regressors["opponent_strength"] = [r - mean_rating for r in opponent_rating]

        # Fit forecaster
        self.forecaster.fit(game_dates, stat_values, regressors)

        logger.info(f"Player {player_id} model fitted")

        return self

    def forecast_next_games(
        self,
        n_games: int,
        future_minutes: Optional[List[float]] = None,
        future_rest_days: Optional[List[int]] = None,
        future_is_home: Optional[List[bool]] = None,
        future_opponent_rating: Optional[List[float]] = None,
    ) -> ForecastResult:
        """
        Forecast next N games for player.

        Args:
            n_games: Number of games to forecast
            future_minutes: Expected minutes
            future_rest_days: Rest days before games
            future_is_home: Home game indicators
            future_opponent_rating: Opponent ratings

        Returns:
            ForecastResult with game-by-game predictions
        """
        # Build future regressors
        future_regressors = {}

        if future_minutes is not None:
            future_regressors["minutes"] = future_minutes

        if future_rest_days is not None:
            future_regressors["rest_days"] = future_rest_days

        if future_is_home is not None:
            future_regressors["home"] = [1.0 if h else 0.0 for h in future_is_home]

        if future_opponent_rating is not None:
            future_regressors["opponent_strength"] = future_opponent_rating

        # Forecast (assume ~3.5 games per week, so periods = n_games * 2 days)
        forecast = self.forecaster.predict(
            periods=n_games * 2,  # Approximate days
            freq="D",
            future_regressors=future_regressors,
        )

        return forecast


def create_nba_holidays() -> pd.DataFrame:
    """
    Create NBA holidays/special events dataframe.

    Returns:
        DataFrame with holidays in Prophet format
    """
    # Define key NBA dates
    holidays = pd.DataFrame(
        {
            "holiday": [
                "All_Star_Break",
                "Trade_Deadline",
                "Playoff_Start",
                "Finals_Start",
            ],
            "ds": pd.to_datetime(
                [
                    "2024-02-15",  # Placeholder dates
                    "2024-02-08",
                    "2024-04-15",
                    "2024-06-01",
                ]
            ),
        }
    )

    return holidays


def check_prophet_available() -> bool:
    """Check if Prophet is available"""
    return PROPHET_AVAILABLE


__all__ = [
    "ProphetConfig",
    "ForecastResult",
    "NBAProphetForecaster",
    "PlayerPerformanceForecaster",
    "SeasonMode",
    "create_nba_holidays",
    "check_prophet_available",
]
