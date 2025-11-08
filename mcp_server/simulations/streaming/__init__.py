"""
Streaming Simulation Components (Agent 14)

Real-time simulation capabilities for live NBA game analysis:
- Streaming Kalman filters for state estimation
- Live game simulation with probability updates
- WebSocket/API data connectors
- In-game prediction updates

Integrates with:
- streaming_analytics: Event processing and live tracking
- event_streaming: Pub/sub and event routing
- simulations/deployment: Model loading and prediction
"""

from mcp_server.simulations.streaming.kalman_filter import (
    StreamingKalmanFilter,
    GameState,
    KalmanFilterConfig,
)
from mcp_server.simulations.streaming.live_simulator import (
    LiveGameSimulator,
    SimulationUpdate,
    LiveSimulatorConfig,
)
from mcp_server.simulations.streaming.data_connector import (
    StreamingDataConnector,
    DataSourceConfig,
    DataSourceType,
    WebSocketConnector,
    MockDataConnector,
)
from mcp_server.simulations.streaming.in_game_predictor import (
    InGamePredictor,
    PredictionUpdate,
    PredictorConfig,
)

__all__ = [
    "StreamingKalmanFilter",
    "GameState",
    "KalmanFilterConfig",
    "LiveGameSimulator",
    "SimulationUpdate",
    "LiveSimulatorConfig",
    "StreamingDataConnector",
    "DataSourceConfig",
    "DataSourceType",
    "WebSocketConnector",
    "MockDataConnector",
    "InGamePredictor",
    "PredictionUpdate",
    "PredictorConfig",
]
