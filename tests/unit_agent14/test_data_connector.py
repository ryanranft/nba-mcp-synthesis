"""
Unit Tests for Streaming Data Connectors (Agent 14, Module 3)

Tests for WebSocket, REST API, and mock data connectors.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from mcp_server.simulations.streaming.data_connector import (
    DataConnector,
    MockDataConnector,
    WebSocketConnector,
    RESTAPIConnector,
    StreamingDataConnector,
    DataSourceConfig,
    DataSourceType,
    ConnectionStatus,
    DataMessage,
    create_mock_connector,
)


class TestDataMessage:
    """Test DataMessage dataclass"""

    def test_data_message_creation(self):
        """Test basic data message creation"""
        msg = DataMessage(
            message_id="msg_001",
            timestamp=datetime.now(),
            source="test",
            data={'score': 100},
            message_type="score_update",
            sequence_number=1
        )

        assert msg.message_id == "msg_001"
        assert msg.source == "test"
        assert msg.data['score'] == 100
        assert msg.sequence_number == 1

    def test_data_message_to_dict(self):
        """Test conversion to dictionary"""
        msg = DataMessage(
            message_id="msg_001",
            timestamp=datetime.now(),
            source="test",
            data={'score': 100}
        )

        d = msg.to_dict()
        assert 'message_id' in d
        assert 'timestamp' in d
        assert 'data' in d
        assert d['data']['score'] == 100


class TestDataSourceConfig:
    """Test DataSourceConfig"""

    def test_default_config(self):
        """Test configuration creation"""
        config = DataSourceConfig(
            source_type=DataSourceType.WEBSOCKET,
            endpoint="ws://localhost:8080"
        )

        assert config.source_type == DataSourceType.WEBSOCKET
        assert config.endpoint == "ws://localhost:8080"
        assert config.reconnect_attempts == 3

    def test_custom_config(self):
        """Test custom configuration"""
        config = DataSourceConfig(
            source_type=DataSourceType.REST_API,
            endpoint="http://api.example.com",
            auth_token="secret123",
            reconnect_attempts=5,
            timeout_seconds=60.0
        )

        assert config.auth_token == "secret123"
        assert config.reconnect_attempts == 5
        assert config.timeout_seconds == 60.0


class TestMockDataConnector:
    """Test MockDataConnector"""

    def test_mock_connector_creation(self):
        """Test mock connector creation"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)

        assert connector.event_rate_hz == 10.0
        assert connector.status == ConnectionStatus.DISCONNECTED

    def test_mock_connector_connect(self):
        """Test mock connection"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        result = connector.connect()

        assert result is True
        assert connector.status == ConnectionStatus.CONNECTED

    def test_mock_connector_disconnect(self):
        """Test mock disconnection"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        connector.connect()
        connector.disconnect()

        assert connector.status == ConnectionStatus.DISCONNECTED

    def test_mock_data_generation(self):
        """Test mock data generation"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)

        messages_received = []

        def callback(msg):
            messages_received.append(msg)

        connector.register_callback(callback)
        connector.start()

        # Wait for some messages
        time.sleep(0.5)
        connector.stop()

        assert len(messages_received) > 0
        assert all(isinstance(msg, DataMessage) for msg in messages_received)

    def test_mock_score_updates(self):
        """Test that mock connector generates score updates"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=5.0)

        connector.start()
        time.sleep(0.3)

        # Get a message
        msg = connector.get_message(timeout=1.0)
        connector.stop()

        assert msg is not None
        assert 'home_score' in msg.data
        assert 'away_score' in msg.data
        assert 'time_remaining' in msg.data

    def test_callback_registration(self):
        """Test callback registration"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        callback_called = []

        def test_callback(msg):
            callback_called.append(msg)

        connector.register_callback(test_callback)
        connector.start()

        time.sleep(0.2)
        connector.stop()

        assert len(callback_called) > 0

    def test_multiple_callbacks(self):
        """Test multiple callbacks"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)

        calls1 = []
        calls2 = []

        connector.register_callback(lambda msg: calls1.append(msg))
        connector.register_callback(lambda msg: calls2.append(msg))

        connector.start()
        time.sleep(0.2)
        connector.stop()

        assert len(calls1) > 0
        assert len(calls2) > 0
        assert len(calls1) == len(calls2)

    def test_get_message_timeout(self):
        """Test get_message with timeout"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        # Should return None immediately (no messages)
        msg = connector.get_message(timeout=0.1)
        assert msg is None

    def test_statistics(self):
        """Test statistics collection"""
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)

        connector.start()
        time.sleep(0.3)
        connector.stop()

        stats = connector.get_statistics()
        assert 'messages_received' in stats
        assert 'status' in stats
        assert stats['messages_received'] > 0

    def test_create_mock_connector_convenience(self):
        """Test convenience function for creating mock connector"""
        connector = create_mock_connector(
            endpoint="mock://convenience_test",
            event_rate_hz=5.0
        )

        assert isinstance(connector, MockDataConnector)
        assert connector.event_rate_hz == 5.0


class TestWebSocketConnector:
    """Test WebSocketConnector"""

    def test_websocket_connector_creation(self):
        """Test WebSocket connector creation"""
        config = DataSourceConfig(
            source_type=DataSourceType.WEBSOCKET,
            endpoint="ws://localhost:8080"
        )
        connector = WebSocketConnector(config)

        assert connector.ws is None
        assert connector.status == ConnectionStatus.DISCONNECTED

    def test_websocket_connect_placeholder(self):
        """Test WebSocket connect (placeholder implementation)"""
        config = DataSourceConfig(
            source_type=DataSourceType.WEBSOCKET,
            endpoint="ws://localhost:8080"
        )
        connector = WebSocketConnector(config)

        # Placeholder implementation should succeed
        result = connector.connect()
        assert result is True

    def test_websocket_disconnect(self):
        """Test WebSocket disconnect"""
        config = DataSourceConfig(
            source_type=DataSourceType.WEBSOCKET,
            endpoint="ws://localhost:8080"
        )
        connector = WebSocketConnector(config)

        connector.connect()
        connector.disconnect()

        assert connector.status == ConnectionStatus.DISCONNECTED


class TestRESTAPIConnector:
    """Test RESTAPIConnector"""

    def test_rest_api_connector_creation(self):
        """Test REST API connector creation"""
        config = DataSourceConfig(
            source_type=DataSourceType.REST_API,
            endpoint="http://api.example.com"
        )
        connector = RESTAPIConnector(config, poll_interval_seconds=5.0)

        assert connector.poll_interval_seconds == 5.0
        assert connector.status == ConnectionStatus.DISCONNECTED

    def test_rest_api_connect_placeholder(self):
        """Test REST API connect (placeholder implementation)"""
        config = DataSourceConfig(
            source_type=DataSourceType.REST_API,
            endpoint="http://api.example.com"
        )
        connector = RESTAPIConnector(config)

        # Placeholder implementation should succeed
        result = connector.connect()
        assert result is True

    def test_rest_api_disconnect(self):
        """Test REST API disconnect"""
        config = DataSourceConfig(
            source_type=DataSourceType.REST_API,
            endpoint="http://api.example.com"
        )
        connector = RESTAPIConnector(config)

        connector.connect()
        connector.disconnect()

        assert connector.status == ConnectionStatus.DISCONNECTED


class TestStreamingDataConnector:
    """Test StreamingDataConnector manager"""

    def test_streaming_connector_creation(self):
        """Test streaming connector manager creation"""
        manager = StreamingDataConnector()

        assert len(manager.connectors) == 0
        assert len(manager.message_handlers) == 0

    def test_add_connector(self):
        """Test adding a connector"""
        manager = StreamingDataConnector()

        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        manager.add_connector("test_source", connector)

        assert "test_source" in manager.connectors
        assert manager.connectors["test_source"] == connector

    def test_remove_connector(self):
        """Test removing a connector"""
        manager = StreamingDataConnector()

        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)

        manager.add_connector("test_source", connector)
        manager.remove_connector("test_source")

        assert "test_source" not in manager.connectors

    def test_register_handler(self):
        """Test registering message handler"""
        manager = StreamingDataConnector()

        def test_handler(msg):
            pass

        manager.register_handler(test_handler)

        assert len(manager.message_handlers) == 1

    def test_message_routing(self):
        """Test message routing to handlers"""
        manager = StreamingDataConnector()

        messages_received = []

        def test_handler(msg):
            messages_received.append(msg)

        manager.register_handler(test_handler)

        # Add mock connector
        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)
        manager.add_connector("mock", connector)

        # Start all
        manager.start_all()
        time.sleep(0.2)
        manager.stop_all()

        # Messages should have been routed to handler
        assert len(messages_received) > 0

    def test_start_all_connectors(self):
        """Test starting all connectors"""
        manager = StreamingDataConnector()

        # Add multiple connectors
        for i in range(3):
            config = DataSourceConfig(
                source_type=DataSourceType.MOCK,
                endpoint=f"mock://test_{i}"
            )
            connector = MockDataConnector(config)
            manager.add_connector(f"mock_{i}", connector)

        manager.start_all()

        # Give connectors time to start
        time.sleep(0.1)

        # All should be running
        for connector in manager.connectors.values():
            assert connector._running is True

        manager.stop_all()

    def test_stop_all_connectors(self):
        """Test stopping all connectors"""
        manager = StreamingDataConnector()

        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config)
        manager.add_connector("mock", connector)

        manager.start_all()
        time.sleep(0.1)
        manager.stop_all()

        # Should be stopped
        assert connector._running is False

    def test_get_statistics(self):
        """Test getting statistics from all connectors"""
        manager = StreamingDataConnector()

        config1 = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test1"
        )
        connector1 = MockDataConnector(config1)

        config2 = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test2"
        )
        connector2 = MockDataConnector(config2)

        manager.add_connector("mock1", connector1)
        manager.add_connector("mock2", connector2)

        stats = manager.get_statistics()

        assert "mock1" in stats
        assert "mock2" in stats
        assert 'status' in stats["mock1"]
        assert 'status' in stats["mock2"]

    def test_multiple_handlers(self):
        """Test multiple message handlers"""
        manager = StreamingDataConnector()

        calls1 = []
        calls2 = []

        manager.register_handler(lambda msg: calls1.append(msg))
        manager.register_handler(lambda msg: calls2.append(msg))

        config = DataSourceConfig(
            source_type=DataSourceType.MOCK,
            endpoint="mock://test"
        )
        connector = MockDataConnector(config, event_rate_hz=10.0)
        manager.add_connector("mock", connector)

        manager.start_all()
        time.sleep(0.2)
        manager.stop_all()

        # Both handlers should have received messages
        assert len(calls1) > 0
        assert len(calls2) > 0
        assert len(calls1) == len(calls2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
