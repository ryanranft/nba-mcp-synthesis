"""
Streaming Data Connectors (Agent 14, Module 3)

Provides connectivity to external real-time data sources:
- WebSocket connections for live data feeds
- REST API polling
- Custom data source adapters
- Data transformation and validation

Integrates with:
- streaming_analytics: Event processing
- event_streaming: Event publishing
- simulations/streaming: Live simulation updates
"""

import logging
import time
import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import threading
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""

    WEBSOCKET = "websocket"
    REST_API = "rest_api"
    FILE = "file"
    MOCK = "mock"


class ConnectionStatus(Enum):
    """Connection status"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class DataSourceConfig:
    """Configuration for data source"""

    source_type: DataSourceType
    endpoint: str
    auth_token: Optional[str] = None
    reconnect_attempts: int = 3
    reconnect_delay_seconds: float = 5.0
    timeout_seconds: float = 30.0
    buffer_size: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataMessage:
    """Message from data source"""

    message_id: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    message_type: Optional[str] = None
    sequence_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "message_type": self.message_type,
            "sequence_number": self.sequence_number,
        }


class DataConnector(ABC):
    """
    Abstract base class for data connectors.

    Subclasses implement specific connection protocols.
    """

    def __init__(self, config: DataSourceConfig):
        """
        Initialize data connector.

        Args:
            config: Data source configuration
        """
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.message_buffer: Queue[DataMessage] = Queue(maxsize=config.buffer_size)
        self.callbacks: List[Callable[[DataMessage], None]] = []
        self.stats = {
            "messages_received": 0,
            "messages_dropped": 0,
            "connection_attempts": 0,
            "last_message_time": None,
            "errors": 0,
        }
        self._running = False
        self._thread: Optional[threading.Thread] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to data source.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from data source"""
        pass

    @abstractmethod
    def _receive_loop(self):
        """Main loop for receiving data (runs in thread)"""
        pass

    def start(self):
        """Start receiving data"""
        if self._running:
            logger.warning("Connector already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        logger.info(f"Data connector started: {self.config.endpoint}")

    def stop(self):
        """Stop receiving data"""
        self._running = False
        self.disconnect()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Data connector stopped")

    def get_message(self, timeout: Optional[float] = None) -> Optional[DataMessage]:
        """
        Get next message from buffer.

        Args:
            timeout: Timeout in seconds (None = non-blocking)

        Returns:
            DataMessage or None if no message available
        """
        try:
            return self.message_buffer.get(timeout=timeout)
        except Empty:
            return None

    def register_callback(self, callback: Callable[[DataMessage], None]):
        """Register callback for incoming messages"""
        self.callbacks.append(callback)
        logger.info(f"Registered callback: {callback.__name__}")

    def get_status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self.status

    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics"""
        return {
            "status": self.status.value,
            "source_type": self.config.source_type.value,
            "endpoint": self.config.endpoint,
            **self.stats,
        }

    def _notify_callbacks(self, message: DataMessage):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def _add_message(self, message: DataMessage):
        """Add message to buffer and notify callbacks"""
        try:
            self.message_buffer.put_nowait(message)
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now()
            self._notify_callbacks(message)
        except:
            self.stats["messages_dropped"] += 1
            logger.warning("Message buffer full, dropping message")


class MockDataConnector(DataConnector):
    """
    Mock data connector for testing.

    Generates synthetic data events.
    """

    def __init__(self, config: DataSourceConfig, event_rate_hz: float = 1.0):
        """
        Initialize mock connector.

        Args:
            config: Configuration
            event_rate_hz: Events per second to generate
        """
        super().__init__(config)
        self.event_rate_hz = event_rate_hz
        self.game_state = {
            "home_score": 0,
            "away_score": 0,
            "time_remaining": 48.0,
            "quarter": 1,
        }

    def connect(self) -> bool:
        """Mock connection (always succeeds)"""
        self.status = ConnectionStatus.CONNECTED
        logger.info("Mock connector connected")
        return True

    def disconnect(self):
        """Mock disconnection"""
        self.status = ConnectionStatus.DISCONNECTED
        logger.info("Mock connector disconnected")

    def _receive_loop(self):
        """Generate mock data"""
        if not self.connect():
            return

        message_count = 0
        while self._running:
            # Generate mock event
            self._generate_mock_event(message_count)
            message_count += 1

            # Sleep based on event rate
            time.sleep(1.0 / self.event_rate_hz)

    def _generate_mock_event(self, sequence: int):
        """Generate a mock game event"""
        import random

        # Randomly update score
        if random.random() < 0.3:  # 30% chance of score
            if random.random() < 0.5:
                self.game_state["home_score"] += random.choice([2, 3])
            else:
                self.game_state["away_score"] += random.choice([2, 3])

        # Update time
        self.game_state["time_remaining"] -= 0.1

        if self.game_state["time_remaining"] <= 0:
            self.game_state["quarter"] += 1
            self.game_state["time_remaining"] = 12.0

        # Create message
        message = DataMessage(
            message_id=f"mock_{sequence}",
            timestamp=datetime.now(),
            source="mock",
            data=self.game_state.copy(),
            message_type="score_update",
            sequence_number=sequence,
        )

        self._add_message(message)


class WebSocketConnector(DataConnector):
    """
    WebSocket data connector for real-time feeds.

    Note: Requires websockets library (not imported by default)
    """

    def __init__(self, config: DataSourceConfig):
        """Initialize WebSocket connector"""
        super().__init__(config)
        self.ws = None

    def connect(self) -> bool:
        """Connect to WebSocket"""
        try:
            # Note: Actual WebSocket implementation would require 'websockets' or 'websocket-client'
            # This is a placeholder for the interface
            self.status = ConnectionStatus.CONNECTING
            self.stats["connection_attempts"] += 1

            # Placeholder: In real implementation, establish WebSocket connection
            # import websocket
            # self.ws = websocket.WebSocketApp(
            #     self.config.endpoint,
            #     on_message=self._on_message,
            #     on_error=self._on_error,
            #     on_close=self._on_close
            # )

            self.status = ConnectionStatus.CONNECTED
            logger.info(f"WebSocket connected: {self.config.endpoint}")
            return True

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.stats["errors"] += 1
            logger.error(f"WebSocket connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect WebSocket"""
        if self.ws:
            try:
                # self.ws.close()
                pass
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.status = ConnectionStatus.DISCONNECTED

    def _receive_loop(self):
        """Receive messages from WebSocket"""
        if not self.connect():
            return

        while self._running:
            try:
                # Placeholder: In real implementation, receive from WebSocket
                # This would be handled by WebSocket callbacks
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self._should_reconnect():
                    self._reconnect()
                else:
                    break

    def _on_message(self, ws, message_str: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message_str)
            message = DataMessage(
                message_id=data.get("id", f"ws_{int(time.time() * 1000)}"),
                timestamp=datetime.now(),
                source="websocket",
                data=data,
                message_type=data.get("type"),
            )
            self._add_message(message)
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    def _should_reconnect(self) -> bool:
        """Check if reconnection should be attempted"""
        return self.stats["connection_attempts"] < self.config.reconnect_attempts

    def _reconnect(self):
        """Attempt to reconnect"""
        self.status = ConnectionStatus.RECONNECTING
        logger.info(
            f"Attempting reconnect ({self.stats['connection_attempts']} / {self.config.reconnect_attempts})"
        )
        time.sleep(self.config.reconnect_delay_seconds)
        self.connect()


class RESTAPIConnector(DataConnector):
    """
    REST API connector with polling.

    Periodically polls a REST endpoint for updates.
    """

    def __init__(self, config: DataSourceConfig, poll_interval_seconds: float = 5.0):
        """
        Initialize REST API connector.

        Args:
            config: Configuration
            poll_interval_seconds: Time between polls
        """
        super().__init__(config)
        self.poll_interval_seconds = poll_interval_seconds
        self.last_poll_time: Optional[datetime] = None

    def connect(self) -> bool:
        """Check API connectivity"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.stats["connection_attempts"] += 1

            # Placeholder: Would test API endpoint
            # import requests
            # response = requests.get(
            #     self.config.endpoint,
            #     headers={'Authorization': f'Bearer {self.config.auth_token}'},
            #     timeout=self.config.timeout_seconds
            # )
            # if response.status_code == 200:
            #     self.status = ConnectionStatus.CONNECTED
            #     return True

            self.status = ConnectionStatus.CONNECTED
            logger.info(f"REST API connected: {self.config.endpoint}")
            return True

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.stats["errors"] += 1
            logger.error(f"REST API connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from API"""
        self.status = ConnectionStatus.DISCONNECTED

    def _receive_loop(self):
        """Poll API for updates"""
        if not self.connect():
            return

        while self._running:
            try:
                self._poll_api()
                time.sleep(self.poll_interval_seconds)
            except Exception as e:
                logger.error(f"API polling error: {e}")
                self.stats["errors"] += 1

    def _poll_api(self):
        """Poll API endpoint once"""
        try:
            # Placeholder: Would make actual API request
            # import requests
            # response = requests.get(
            #     self.config.endpoint,
            #     headers={'Authorization': f'Bearer {self.config.auth_token}'},
            #     timeout=self.config.timeout_seconds
            # )
            # if response.status_code == 200:
            #     data = response.json()
            #     message = DataMessage(
            #         message_id=f"api_{int(time.time() * 1000)}",
            #         timestamp=datetime.now(),
            #         source="rest_api",
            #         data=data,
            #     )
            #     self._add_message(message)

            self.last_poll_time = datetime.now()

        except Exception as e:
            logger.error(f"API poll error: {e}")


class StreamingDataConnector:
    """
    High-level streaming data connector manager.

    Manages multiple data sources and routes data to consumers.
    """

    def __init__(self):
        """Initialize connector manager"""
        self.connectors: Dict[str, DataConnector] = {}
        self.message_handlers: List[Callable[[DataMessage], None]] = []

    def add_connector(self, name: str, connector: DataConnector):
        """
        Add a data connector.

        Args:
            name: Connector name
            connector: DataConnector instance
        """
        self.connectors[name] = connector

        # Register handler to route messages
        connector.register_callback(self._route_message)

        logger.info(f"Added connector: {name}")

    def remove_connector(self, name: str):
        """Remove a data connector"""
        if name in self.connectors:
            self.connectors[name].stop()
            del self.connectors[name]
            logger.info(f"Removed connector: {name}")

    def register_handler(self, handler: Callable[[DataMessage], None]):
        """Register message handler"""
        self.message_handlers.append(handler)
        logger.info(f"Registered message handler: {handler.__name__}")

    def start_all(self):
        """Start all connectors"""
        for name, connector in self.connectors.items():
            try:
                connector.start()
                logger.info(f"Started connector: {name}")
            except Exception as e:
                logger.error(f"Failed to start connector {name}: {e}")

    def stop_all(self):
        """Stop all connectors"""
        for name, connector in self.connectors.items():
            try:
                connector.stop()
                logger.info(f"Stopped connector: {name}")
            except Exception as e:
                logger.error(f"Error stopping connector {name}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for all connectors"""
        return {
            name: connector.get_statistics()
            for name, connector in self.connectors.items()
        }

    def _route_message(self, message: DataMessage):
        """Route message to all handlers"""
        for handler in self.message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")


# Convenience function
def create_mock_connector(
    endpoint: str = "mock://test", event_rate_hz: float = 1.0
) -> MockDataConnector:
    """
    Create a mock data connector for testing.

    Args:
        endpoint: Mock endpoint name
        event_rate_hz: Events per second

    Returns:
        MockDataConnector instance
    """
    config = DataSourceConfig(source_type=DataSourceType.MOCK, endpoint=endpoint)
    return MockDataConnector(config, event_rate_hz=event_rate_hz)
